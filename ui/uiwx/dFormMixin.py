""" dFormMixin.py """
import os
import wx, dabo
import dPemMixin as pm
import dBaseMenuBar as mnb
import dMenu, dMessageBox, dabo.icons
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dFormMixin(pm.dPemMixin):
	def __init__(self, preClass, parent=None, properties=None, *args, **kwargs):
		if False and parent:
			## pkm 3/10/05: I like it better now without the float on parent option
			##              and think it is a better default to stick with the wx
			##              default frame style. You can still override the style
			##              by passing it to the constructor.
			style = wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT
		else:
			style = wx.DEFAULT_FRAME_STYLE
		
		kwargs["style"] = style
		
		super(dFormMixin, self).__init__(preClass, parent, properties, *args, **kwargs)
		

	def _afterInit(self):
		if self.Application and self.MenuBarClass:
			try:
	 			self.MenuBar = self.MenuBarClass()
				self.afterSetMenuBar()
			except AttributeError:
				# perhaps we are a dDialog
				pass

		if not self.Icon:
			self.Icon = wx.Icon(dabo.icons.getIconFileName('daboIcon048'), wx.BITMAP_TYPE_PNG)

		self.debugText = ""
		self.useOldDebugDialog = False
		self.restoredSP = False
		self._holdStatusText = ""
		if self.Application is not None:
			self.Application.uiForms.add(self)
		
		super(dFormMixin, self)._afterInit()
	
				
	def _initEvents(self):
		super(dFormMixin, self)._initEvents()
		self.Bind(wx.EVT_ACTIVATE, self.__onWxActivate)
		self.Bind(wx.EVT_CLOSE, self.__onWxClose)
		self.bindEvent(dEvents.Activate, self.__onActivate)
		self.bindEvent(dEvents.Deactivate, self.__onDeactivate)
		self.bindEvent(dEvents.Close, self.__onClose)
	
		
	def __onWxClose(self, evt):
		self.raiseEvent(dEvents.Close, evt)
		if evt.CanVeto():
			evt.Veto()
		
		
	def __onWxActivate(self, evt):
		""" Raise the Dabo Activate or Deactivate appropriately.
		"""
		if bool(evt.GetActive()):
			self.raiseEvent(dEvents.Activate, evt)
		else:
			self.raiseEvent(dEvents.Deactivate, evt)
			
			
	def __onActivate(self, evt): 
		# Restore the saved size and position, which can't happen 
		# in __init__ because we may not have our name yet.
		try:
			restSP = self.restoredSP
		except:
			restSP = False
		if not restSP:
			self.restoreSizeAndPosition()
		if hasattr(self, "GetStatusBar"):
			if self.GetStatusBar() is None and not isinstance(self, wx.MDIChildFrame) and self.ShowStatusBar:
				self.CreateStatusBar()

		if self.Application is not None:
			self.Application._setActiveForm(self)
	
	def __onDeactivate(self, evt):
		if self.Application is not None and self.Application.ActiveForm == self:
			self.Application._setActiveForm(None)
	
	
	def __onClose(self, evt):
		force = evt.EventData["force"]
		if not force:
			if self._beforeClose(evt) == False:
				evt.stop()
				return
			# Run the cleanup code.
			self.closing()
		if self.Application is not None:
			self.Application.uiForms.remove(self)
		self.saveSizeAndPosition()
	

	def close(self, force=False):
		""" This method will close the form. If force = False (default)
		the beforeClose methods will be called, and these will have
		an opportunity to conditionally block the form from closing.
		If force=True, the form is closed without any chance of 
		preventing it.
		"""
		if not force:
			if self._beforeClose() == False:
				return False
		# Run any cleanup code
		self.closing()
		# Kill the form
		self.Close(force=True)
		
		
	def _beforeClose(self, evt=None):
		""" See if there are any pending changes in the form, if the
		form is set for checking for this. If everything's OK, call the 
		hook method.
		"""
		ret = self.beforeClose(evt)
		return ret
		
		
	def beforeClose(self, evt):
		""" Hook method. Returning False will prevent the form from 
		closing. Gives you a chance to determine the status of the form
		to see if changes need to be saved, etc.
		"""
		return True
		
		
	def closing(self):
		""" Stub method to be customized in subclasses. At this point,
		the form is going to close. If you need to do something that might
		prevent the form from closing, code it in the beforeClose() 
		method instead.
		"""
		pass
		

	def afterSetMenuBar(self):
		""" Subclasses can extend the menu bar here.
		"""
		pass

	def onCmdWin(self, evt):
		dlg = dabo.ui.dShell.dShell(self)
		dlg.Show()

	
	def lockScreen(self):
		"""Locks the visual updates to the screen to improve performance
		when many items are being updated at once.
		IMPORTANT: you must call unlockScreen() when you are done,
		or your form will look like it isn't responding.
		"""
		self.Freeze()
	
	
	def unlockScreen(self):
		"""Unlocks the screen so that visual updates can be made. Must
		be called after a call to lockScreen().
		"""
		self.Thaw()
	
	
	def refresh(self):
		"""Refreshed the values of the controls, and also calls the
		wxPython Refresh to update the form.
		"""
		self.refreshControls()
		self.Refresh()
		
		
	def refreshControls(self):
		""" Refresh the value of all contained dControls.

		Raises EVT_VALUEREFRESH which will be caught by all dControls, who will
		in turn refresh themselves with the current value of the field in the
		bizobj. 
		"""
		self.raiseEvent(dEvents.ValueRefresh)
		try:
			self.setStatusText(self.getCurrentRecordText())
		except: pass


	def onDebugDlg(self, evt):
		# Handy hook for getting info.
		if self.useOldDebugDialog:
			dlg = wx.TextEntryDialog(self, "Command to Execute", "Debug", self.debugText)
			if dlg.ShowModal() == wx.ID_OK:
				self.debugText = dlg.GetValue()
				try:
					# Handy shortcuts for common references
					try: bo = self.getBizobj()
					except: pass
					exec(self.debugText)
				except StandardError, e: 
					dabo.infoLog.write(_("Could not execute: %s") % self.debugText)
					dabo.errorLog.write(e)

			dlg.Destroy()	
			
		else:
			self.onCmdWin(evt)


	def getMenu(self):
		""" Get the navigation menu for this form.

		Every form maintains an internal menu of actions appropriate to itself.
		For instance, a dForm with a primary bizobj will maintain a menu with 
		'requery', 'save', 'next', etc. choices. 

		This function sets up the internal menu, which can optionally be 
		inserted into the mainForm's menu bar during SetFocus.
		"""
		menu = dMenu.dMenu()
		return menu

		
	def restoreSizeAndPosition(self):
		""" Restore the saved window geometry for this form.

		Ask dApp for the last saved setting of height, width, left, and top, 
		and set those properties on this form.
		"""
		if self.Application and self.SaveUserGeometry:
			name = self.getAbsoluteName()

			left = self.Application.getUserSetting("%s.left" % name)
			top = self.Application.getUserSetting("%s.top" % name)
			width = self.Application.getUserSetting("%s.width" % name)
			height = self.Application.getUserSetting("%s.height" % name)

			if (type(left), type(top)) == (type(int()), type(int())):
				self.Position = (left,top)
			if (type(width), type(height)) == (type(int()), type(int())):
				self.Size = (width,height)

			self.restoredSP = True


	def saveSizeAndPosition(self):
		""" Save the current size and position of this form.
		"""
		if self.Application:
			if self == self.Application.MainForm:
				for form in self.Application.uiForms:
					try:
						form.saveSizeAndPosition()
					except wx.PyDeadObjectError:
						pass

			if self.SaveUserGeometry:
				name = self.getAbsoluteName()

				pos = self.Position
				size = self.Size

				self.Application.setUserSetting("%s.left" % name, pos[0])
				self.Application.setUserSetting("%s.top" % name, pos[1])
				self.Application.setUserSetting("%s.width" % name, size[0])
				self.Application.setUserSetting("%s.height" % name, size[1])


	def setStatusText(self, *args):
		""" Set the text of the status bar.

		Call this instead of SetStatusText() and dabo will decide whether to 
		send the text to the main frame or this frame. This matters with MDI
		versus non-MDI forms.
		"""
		if isinstance(self, wx.MDIChildFrame):
			controllingFrame = self.Application.MainForm
		else:
			controllingFrame = self
		if controllingFrame.GetStatusBar():
			if self._holdStatusText:
				controllingFrame.SetStatusText(self._holdStatusText)
				self._holdStatusText = ""
			else:
				controllingFrame.SetStatusText(*args)
			controllingFrame.GetStatusBar().Update()
		
	
	def layout(self):
		""" Wrap the wx sizer layout call. """
		self.Layout()
		try:
			# Call the Dabo version, if present
			self.Sizer.layout()
		except: pass
	
	
	def bringToFront(self):
		"""Makes this window topmost"""
		self.Raise()
	
	
	def sendToBack(self):
		"""Places this window behind all others."""
		self.Lower()
		
		
	def _appendToMenu(self, menu, caption, function, bitmap=wx.NullBitmap, menuId=-1):
		if isinstance(self, wx.MDIChildFrame):
			bindObj = self.Application.MainForm
		else:
			if wx.Platform == '__WXMAC__':
				# Trial and error reveals that this works on Mac, while calling
				# controllingFrame.Bind does not. I've posted an inquiry about 
				# this to wxPython-mac@wxwidgets.org, but in the meantime we have
				# this platform-specific code to tide us over.
				bindObj = menu
			else:
				bindObj = self
		menu.append(caption, bindObj, func=function, bmp=bitmap)

			
	def _appendToToolBar(self, toolBar, caption, bitmap, function, statusText=""):
		toolId = wx.NewId()
		toolBar.AddSimpleTool(toolId, bitmap, caption, statusText)

		if isinstance(self, wx.MDIChildFrame):
			controllingFrame = self.Application.MainForm
		else:
			controllingFrame = self
		wx.EVT_MENU(controllingFrame, toolId, function)


	# property get/set/del functions follow:

	def _getActiveControl(self):
		return self.FindFocus()

	def _getIcon(self):
		try:
			return self._Icon
		except AttributeError:
			return None
	def _setIcon(self, val):
		if self._constructed():
			self._Icon = val       # wx doesn't provide GetIcon()
			if not isinstance(val, wx.Icon):
				if os.path.exists(val):
					# It's a file path
					bmp = wx.Bitmap(val)
					val = wx.EmptyIcon()
					val.CopyFromBitmap(bmp)
			self.SetIcon(val)

	def _getIconBundle(self):
		try:
			return self._Icons
		except:
			return None
	def _setIconBundle(self, val):
		if self._constructed():
			self.SetIcons(val)
			self._Icons = val       # wx doesn't provide GetIcons()
		else:
			self._properties["Icons"] = val

	def _getBorderResizable(self):
		return self.hasWindowStyleFlag(wx.RESIZE_BORDER)
	def _setBorderResizable(self, value):
		self.delWindowStyleFlag(wx.RESIZE_BORDER)
		if value:
			self.addWindowStyleFlag(wx.RESIZE_BORDER)

	def _getShowMaxButton(self):
		return self.hasWindowStyleFlag(wx.MAXIMIZE_BOX)
	def _setShowMaxButton(self, value):
		self.delWindowStyleFlag(wx.MAXIMIZE_BOX)
		if value:
			self.addWindowStyleFlag(wx.MAXIMIZE_BOX)

	def _getShowMinButton(self):
		return self.hasWindowStyleFlag(wx.MINIMIZE_BOX)
	def _setShowMinButton(self, value):
		self.delWindowStyleFlag(wx.MINIMIZE_BOX)
		if value:
			self.addWindowStyleFlag(wx.MINIMIZE_BOX)


	def _getMenuBar(self):
		try:
			return self.GetMenuBar()
		except AttributeError:
			# dDialogs don't have menu bars
			return None

	def _setMenuBar(self, val):
		if self._constructed():
			try:
				self.SetMenuBar(val)
			except AttributeError:
				# dDialogs don't have menu bars
				pass
		else:
			self._properties["MenuBar"] = val

	def _getMenuBarClass(self):
		try:
			mb = self._menuBarClass
		except AttributeError:
			mb = self._menuBarClass = mnb.dBaseMenuBar
		return mb

	def _setMenuBarClass(self, val):
		self._menuBarClass = val
		

	def _getSaveUserGeometry(self):
		try:
			val = self._saveUserGeometry
		except AttributeError:
			val = self._saveUserGeometry = not isinstance(self, dabo.ui.dDialog)
		return val
	
	def _setSaveUserGeometry(self, val):
		self._saveUserGeometry = val


	def _getShowCloseButton(self):
		return self.hasWindowStyleFlag(wx.CLOSE_BOX)
	def _setShowCloseButton(self, value):
		self.delWindowStyleFlag(wx.CLOSE_BOX)
		if value:
			self.addWindowStyleFlag(wx.CLOSE_BOX)

	def _getShowCaption(self):
		return self.hasWindowStyleFlag(wx.CAPTION)
	def _setShowCaption(self, value):
		self.delWindowStyleFlag(wx.CAPTION)
		if value:
			self.addWindowStyleFlag(wx.CAPTION)

	def _getShowStatusBar(self):
		try:
			ssb = self._showStatusBar
		except AttributeError:
			ssb = self._showStatusBar = True
		return ssb
		
	def _setShowStatusBar(self, val):
		self._showStatusBar = bool(val)
		
	def _getShowSystemMenu(self):
		return self.hasWindowStyleFlag(wx.SYSTEM_MENU)
	def _setShowSystemMenu(self, value):
		self.delWindowStyleFlag(wx.SYSTEM_MENU)
		if value:
			self.addWindowStyleFlag(wx.SYSTEM_MENU)

	def _getTinyTitleBar(self):
		return self.hasWindowStyleFlag(wx.FRAME_TOOL_WINDOW)
	def _setTinyTitleBar(self, value):
		self.delWindowStyleFlag(wx.FRAME_TOOL_WINDOW)
		if value:
			self.addWindowStyleFlag(wx.FRAME_TOOL_WINDOW)

	def _getWindowState(self):
		try:
			if self.IsFullScreen():
				return 'FullScreen'
			elif self.IsMaximized():
				return 'Maximized'
			elif self.IsMinimized():
				return 'Minimized'
			else:
				return 'Normal'
		except AttributeError:
			# These only work on Windows, I fear
			return 'Normal'

	def _getWindowStateEditorInfo(self):
		return {'editor': 'list', 'values': ['Normal', 'Minimized', 'Maximized', 'FullScreen']}

	def _setWindowState(self, value):
		if self._constructed():
			value = str(value)
			if value == 'Normal':
				if self.IsFullScreen():
					self.ShowFullScreen(False)
				elif self.IsMaximized():
					self.Maximize(False)
				elif self.IsIconized:
					self.Iconize(False)
				else:
					# window already normal, but just in case:
					self.Maximize(False)
			elif value == 'Minimized':
				self.Iconize()
			elif value == 'Maximized':
				self.Maximize()
			elif value == 'FullScreen':
				self.ShowFullScreen()
			else:
				raise ValueError, ("The only possible values are "
								"'Normal', 'Minimized', 'Maximized', and 'FullScreen'")
		else:
			self._properties["WindowState"] = value


	# property definitions follow:
	ActiveControl = property(_getActiveControl, None, None, 
		_("Contains a reference to the active control on the form, or None."))

	Icon = property(_getIcon, _setIcon, None, 
		_("Specifies the icon for the form. (wxIcon)"))

	IconBundle = property(_getIconBundle, _setIconBundle, None,
		_("Specifies the set of icons for the form. (wxIconBundle)"))

	BorderResizable = property(_getBorderResizable, _setBorderResizable, None,
		_("Specifies whether the user can resize this form. (bool)."))

	MenuBar = property(_getMenuBar, _setMenuBar, None,
		_("Specifies the menu bar instance for the form."))

	MenuBarClass = property(_getMenuBarClass, _setMenuBarClass, None,
		_("Specifies the menu bar class to use for the form, or None."))

	SaveUserGeometry = property(_getSaveUserGeometry, _setSaveUserGeometry, None,
		_("""Specifies whether the form's position and size as set by the user
			will get saved and restored in the next session. Default is True for
			forms and False for dialogs."""))
		
	ShowCaption = property(_getShowCaption, _setShowCaption, None,
		_("Specifies whether the caption is displayed in the title bar. (bool)."))

	ShowMaxButton = property(_getShowMaxButton, _setShowMaxButton, None,
		_("Specifies whether a maximize button is displayed in the title bar. (bool)."))

	ShowMinButton = property(_getShowMinButton, _setShowMinButton, None,
		_("Specifies whether a minimize button is displayed in the title bar. (bool)."))

	ShowCloseButton = property(_getShowCloseButton, _setShowCloseButton, None,
		_("Specifies whether a close button is displayed in the title bar. (bool)."))

	ShowStatusBar = property(_getShowStatusBar, _setShowStatusBar, None,
		_("Specifies whether the status bar gets automatically created."))

	ShowSystemMenu = property(_getShowSystemMenu, _setShowSystemMenu, None,
		_("Specifies whether a system menu is displayed in the title bar. (bool)."))

	TinyTitleBar = property(_getTinyTitleBar, _setTinyTitleBar, None,
		_("Specifies whether the title bar is small, like a tool window. (bool)."))

	WindowState = property(_getWindowState, _setWindowState, None,
		_("""Specifies the current state of the form. (int)
			
				Normal
				Minimized
				Maximized
				FullScreen"""))
