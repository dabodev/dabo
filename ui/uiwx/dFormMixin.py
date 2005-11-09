""" dFormMixin.py """
import os
import wx, dabo
import dPemMixin as pm
import dBaseMenuBar as mnb
import dMenu
import dabo.icons
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from dabo.lib.xmltodict import xmltodict as XTD
from dabo.lib.utils import dictStringify


class dFormMixin(pm.dPemMixin):
	def __init__(self, preClass, parent=None, properties=None, 
			src=None, *args, **kwargs):
		
		self._childList = None
		if src:
			# This is being created from a Class Designer file. 
			try:
				# The Class Designer adds some atts that it uses that are in
				# the way at runtime. Make sure they are filtered out
				attsToSkip = ["designerClass", "SlotCount"]
				contents = XTD(src, attsToSkip)
			except StandardError, e:
				dabo.errorLog.write("Error parsing source file '%s': %s" % (src, str(e)))
				self.release()
				return False
			# Add the atts to the keyword args
			kwargs.update(dictStringify(contents["attributes"]))
			# We've extracted all we need to know about the form,
			# so set the child list to the contained child objects.
			self._childList = contents["children"]
				
		if False and parent:
			## pkm 3/10/05: I like it better now without the float on parent option
			##              and think it is a better default to stick with the wx
			##              default frame style. You can still override the style
			##              by passing it to the constructor.
			style = wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT
		else:
			style = self._extractKey(kwargs, "style", 0)
			if not style:
				# No style was explicitly set
				style = wx.DEFAULT_FRAME_STYLE	
		kwargs["style"] = style
		self._objectRegistry = {}
		super(dFormMixin, self).__init__(preClass, parent, properties, *args, **kwargs)
		

	def _getInitPropertiesList(self):
		additional = ["ShowCloseButton", "ShowMinButton", "ShowMaxButton", 
				"ShowSystemMenu", "TinyTitleBar", "FloatOnParent", "ShowInTaskBar"]
		original = list(super(dFormMixin, self)._getInitPropertiesList())
		return tuple(original + additional)
		

	def _afterInit(self):
		if self.Application and self.MenuBarClass:
			try:
					self.MenuBar = self.MenuBarClass()
			except AttributeError:
				# perhaps we are a dDialog
				pass
			self.afterSetMenuBar()

		self._iconFile = dabo.icons.getIconFileName("daboIcon048")
		if not self.Icon:
			self.Icon = wx.Icon(self._iconFile, wx.BITMAP_TYPE_PNG)

		self.debugText = ""
		self.useOldDebugDialog = False
		self.restoredSP = False
		self._holdStatusText = ""
		if self.Application is not None:
			self.Application.uiForms.add(self)
		# Flag to skip updates when they aren't needed
		self._isClosed = False
		# Sizer outline drawing flag
		self.__needOutlineRedraw = False
		# Centering information
		self._normLeft = self.Left
		self._normTop = self.Top
		self._centered = False
		
		if self._childList is not None:
			# This will contain information for constructing the contained
			# objects for this form.
			self._addChildren(self._childList)			
		super(dFormMixin, self)._afterInit()
	
				
	def _addChildren(self, childList, parent=None, szr=None):
		"""This method receives a list of dicts containing information
		on the child objects to be added. Each of these objects may 
		contain child objects of their own, and so this method may be
		called recursively.
		"""
		if parent is None:
			parent = self
		
		for child in childList:
			try:
				nm = child["name"]
				szrInfo = {}
				atts = dictStringify(child["attributes"])
				if atts.has_key("sizerInfo"):
					# The value is a string representation of the dict, so
					# we need to eval() it.
					szrInfo = eval(atts["sizerInfo"])
					del atts["sizerInfo"]
				kids = []
				if child.has_key("children"):
					kids = child["children"]
					
				# Right now we are limiting this to Dabo classes.
				cls = dabo.ui.__dict__[nm]
				if issubclass(cls, dabo.ui.dSizer):
					ornt = "Horizontal"
					if atts.has_key("Orientation"):
						ornt = atts["Orientation"]
						del atts["Orientation"]
					parent.Sizer = sz = cls(orientation=ornt, properties=atts)
					if kids:
						self._addChildren(kids, parent=parent, szr=sz)

				elif issubclass(cls, dabo.ui.dGridSizer):
					# This should have a MaxDimension property that
					# will determine which of the Rows/Columns atts
					# we use.
					dim = "c"
					rows, cols = 0, 0
					if atts.has_key("Rows"):
						rows = atts["Rows"]
						del atts["Rows"]
					if atts.has_key("Columns"):
						rows = atts["Columns"]
						del atts["Columns"]
					if atts.has_key("MaxDimension"):
						dim = atts["MaxDimension"].lower()
						del atts["MaxDimension"]
					
					if dim == "c":
						sz = cls(maxCols=cols, properties=atts)
					else:
						sz = cls(maxRows=rows, properties=atts)
					parent.Sizer = sz
					if kids:
						self._addChildren(kids, parent=parent, szr=sz)

				else: 
					row, col = (None, None)
					if atts.has_key("rowColPos"):
						row, col = eval(atts["rowColPos"])
						del atts["rowColPos"]
					obj = cls(parent=parent, properties=atts)
					if szr:
						if row is not None and col is not None:
							szr.append(obj, row=row, col=col)
						else:
							szr.append(obj)
						if szrInfo:
							szr.setItemProps(obj.ControllingSizerItem, szrInfo)
					if kids:
						if isinstance(obj, (dabo.ui.dPageFrame, dabo.ui.dPageList, 
								dabo.ui.dPageSelect, dabo.ui.dPageFrameNoTabs)):
							# 'kids' will each be a dPage
							for pageno, pg in enumerate(obj.Pages):
								pgInfo = kids[pageno]
								if pgInfo.has_key("attributes"):
									pg.setPropertiesFromAtts(pgInfo["attributes"])
								if pgInfo.has_key("children"):
									self._addChildren(pgInfo["children"], parent=pg)
						else:
							self._addChildren(kids, parent=obj)
		
			except StandardError, e:
				# This is for development only. It will be changed to a 
				# writing in the error log when this is stable
				print "ERROR creating children:", e
	
	
	def _initEvents(self):
		super(dFormMixin, self)._initEvents()
		self.Bind(wx.EVT_ACTIVATE, self.__onWxActivate)
		self.Bind(wx.EVT_CLOSE, self.__onWxClose)
		self.bindEvent(dEvents.Activate, self.__onActivate)
		self.bindEvent(dEvents.Deactivate, self.__onDeactivate)
		self.bindEvent(dEvents.Close, self.__onClose)
		self.bindEvent(dEvents.Resize, self.__onResize)
		self.bindEvent(dEvents.Move, self.__onMove)
		self.bindEvent(dEvents.Paint, self.__onPaint)
		self.bindEvent(dEvents.Idle, self.__onIdle)
	
		
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
			restoredSP = self.restoredSP
		except:
			restoredSP = False
		if not restoredSP:
			self.restoreSizeAndPosition()
		
		# If the ShowStatusBar property was set to True, this will create it
		sb = self.StatusBar
		# If the ShowToolBar property was set to True, this will create it
		tb = self.ToolBar
		
		if self.Application is not None:
			self.Application._setActiveForm(self)
	
	def __onDeactivate(self, evt):
#		self.saveSizeAndPosition()
		if self.Application is not None and self.Application.ActiveForm == self:
			self.Application._setActiveForm(None)
	

	def __onMove(self, evt):
		try:
			restoredSP = self.restoredSP
		except:
			restoredSP = False
		if restoredSP:		
			self.saveSizeAndPosition()
	
	
	def __onResize(self, evt):
		try:
			restoredSP = self.restoredSP
		except:
			restoredSP = False
		if restoredSP:		
			self.saveSizeAndPosition()
	
	
	def __onPaint(self, evt):
		self.__needOutlineRedraw = self.Application.DrawSizerOutlines
	
	
	def __onIdle(self, evt):
		if self.__needOutlineRedraw:
			if self.Sizer:
				self.Sizer.drawOutline(self, recurse=True)
	
	
	def __onClose(self, evt):
		force = evt.EventData["force"]
		if not force:
			if self._beforeClose(evt) == False:
				evt.stop()
				return
			# Run the cleanup code.
			self.closing()
		
		app = self.Application

		# On the Mac, this next line prevents Bus Errors when closing a form.
		self.Visible = False	
		self._isClosed = True
		self.SetFocus()
		if app is not None:
			try:
				self.Application.uiForms.remove(self)
			except: pass
	
	def _getStatusBar(self):
		if hasattr(self, "GetStatusBar"):
			ret = self.GetStatusBar()
			if (ret is None
					and not isinstance(self, wx.MDIChildFrame) 
					and self.ShowStatusBar):
				ret = dabo.ui.dStatusBar(self)
				self.SetStatusBar(ret)
		else:
			ret = None
		return ret
		
	def _getToolBar(self):
		if hasattr(self, "GetToolBar"):
			ret = self.GetToolBar()
			if ret is None and self.ShowToolBar:
				ret = dabo.ui.dToolBar(self)
				self.ToolBar = ret
		else:
			ret = None
		return ret
		
	def _setToolBar(self, val):
		self.SetToolBar(val)
		if val is not None:
			# the wx toolbar doesn't otherwise know what form it is attached to:
			val.Form = self
	
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


	def refresh(self):
		"""Refreshed the values of the controls, and also calls the
		wxPython Refresh to update the form.
		"""
		self.refreshControls()
		self.Refresh()
		
		
	def refreshControls(self, grid=None):
		""" Refresh the value of all contained dControls.

		Raises EVT_VALUEREFRESH which will be caught by all dControls, who will
		in turn refresh themselves with the current value of the field in the
		bizobj. 
		"""
		self.raiseEvent(dEvents.ValueRefresh)
		try:
			self.setStatusText(self.getCurrentRecordText(grid=grid))
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
	
	
	def onEditUndo(self, evt):
		"""If you want your form to respond to the Undo menu item in
		the Edit menu that is installed in the Dabo base menu, override 
		this method, and either return nothing, or return something other
		than False.
		"""
		return False
		
		
	def onEditRedo(self, evt):
		"""If you want your form to respond to the Redo menu item in
		the Edit menu that is installed in the Dabo base menu, override 
		this method, and either return nothing, or return something other
		than False.
		"""
		return False
		
		
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
			state = self.Application.getUserSetting("%s.windowstate" % name)

			if isinstance(left, int) and isinstance(top, int):
				self.Position = (left,top)
			if isinstance(width, int) and isinstance(height, int):
				self.Size = (width,height)

			if state is not None:
				if state == "Minimized":
					state = "Normal"
				self.WindowState = state
			self.restoredSP = True


	def saveSizeAndPosition(self):
		""" Save the current size and position of this form.
		"""
		if self.Application:
			if self.SaveUserGeometry:
				name = self.getAbsoluteName()
				state = self.WindowState
				self.Application.setUserSetting("%s.windowstate" % name, state)

				if state == 'Normal':
					# Don't save size and position when the window
					# is minimized, maximized or fullscreen because
					# windows doesn't supply correct value if the window
					# is in one of these staes.
					pos = self.Position
					size = self.Size

					self.Application.setUserSetting("%s.left" % name, pos[0])
					self.Application.setUserSetting("%s.top" % name, pos[1])
					self.Application.setUserSetting("%s.width" % name, size[0])
					self.Application.setUserSetting("%s.height" % name, size[1])


	def setStatusText(self, *args):
		"""Moved functionality to the StatusText property setter."""
		self._setStatusText(*args)
		
	
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
	
	
	def registerObject(self, obj):
		"""Stores a reference to the passed object using the RegID key
		property of the object for later retrieval. You may reference the 
		object as if it were a child object of this form; i.e., by using simple
		dot notation, with the RegID as the 'name' of the object. 		
		"""
		if hasattr(obj, "RegID"):
			id = obj.RegID
			if self._objectRegistry.has_key(id):
				raise KeyError, _("Duplicate RegID '%s' found") % id
			self._objectRegistry[id] = obj
			if hasattr(self, id) or self.__dict__.has_key(id):
				dabo.errorLog.write(_("RegID '%s' conflicts with existing name") % id)
			else:
				self.__dict__[id] = obj
		
	
	def getObjectByRegID(self, id):
		"""Given a RegID value, this will return a reference to the 
		associated object, if any. If not, returns None.
		"""
		if self._objectRegistry.has_key(id):
			return self._objectRegistry[id]
		else:
			return None
			
			
	def _appendToMenu(self, menu, caption, function, bitmap=wx.NullBitmap, menuId=-1):
		menu.append(caption, bindfunc=function, bmp=bitmap)

	def appendToolBarButton(self, name, pic, bindfunc=None, toggle=False, tip="", help=""):
		self.ToolBar.appendButton(name, pic, bindfunc=bindfunc, toggle=toggle, 
				tip=tip, help=help)
# 	def _appendToToolBar(self, toolBar, caption, bitmap, function, statusText=""):
# 		toolId = wx.NewId()
# 		toolBar.AddSimpleTool(toolId, bitmap, caption, statusText)
# 
# 		if isinstance(self, wx.MDIChildFrame):
# 			controllingFrame = self.Application.MainForm
# 		else:
# 			controllingFrame = self
# 		wx.EVT_MENU(controllingFrame, toolId, function)


	# property get/set/del functions follow:

	def _getActiveControl(self):
		return self.FindFocus()
	
	def _getCentered(self):
		return self._centered
	def _setCentered(self, val):
		oldCentered = self._centered
		self._centered = val
		if val:
			if not oldCentered:
				# Save the old position
				self._normLeft = self.Left
				self._normTop = self.Top
			# Center it!
			self.CenterOnScreen(wx.BOTH)
		else:
			# restore the old position
			self.Left = self._normLeft
			self.Top = self._normTop

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
		return self._hasWindowStyleFlag(wx.RESIZE_BORDER)
	def _setBorderResizable(self, value):
		self._delWindowStyleFlag(wx.RESIZE_BORDER)
		if value:
			self._addWindowStyleFlag(wx.RESIZE_BORDER)


	def _getFloatOnParent(self):
		return self._hasWindowStyleFlag(wx.FRAME_FLOAT_ON_PARENT)

	def _setFloatOnParent(self, value):
		self._delWindowStyleFlag(wx.FRAME_FLOAT_ON_PARENT)
		if value:
			self._addWindowStyleFlag(wx.FRAME_FLOAT_ON_PARENT)


	def _getShowMaxButton(self):
		return self._hasWindowStyleFlag(wx.MAXIMIZE_BOX)
	def _setShowMaxButton(self, value):
		self._delWindowStyleFlag(wx.MAXIMIZE_BOX)
		if value:
			self._addWindowStyleFlag(wx.MAXIMIZE_BOX)

	def _getShowMinButton(self):
		return self._hasWindowStyleFlag(wx.MINIMIZE_BOX)
	def _setShowMinButton(self, value):
		self._delWindowStyleFlag(wx.MINIMIZE_BOX)
		if value:
			self._addWindowStyleFlag(wx.MINIMIZE_BOX)


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
		return self._hasWindowStyleFlag(wx.CLOSE_BOX)
	def _setShowCloseButton(self, value):
		self._delWindowStyleFlag(wx.CLOSE_BOX)
		if value:
			self._addWindowStyleFlag(wx.CLOSE_BOX)

	def _getShowCaption(self):
		return self._hasWindowStyleFlag(wx.CAPTION)
	def _setShowCaption(self, value):
		self._delWindowStyleFlag(wx.CAPTION)
		if value:
			self._addWindowStyleFlag(wx.CAPTION)


	def _getShowInTaskBar(self):
		return not self._hasWindowStyleFlag(wx.FRAME_NO_TASKBAR)

	def _setShowInTaskBar(self, value):
		self._delWindowStyleFlag(wx.FRAME_NO_TASKBAR)
		if not value:
			self._addWindowStyleFlag(wx.FRAME_NO_TASKBAR)


	def _getShowStatusBar(self):
		try:
			ret = self._showStatusBar
		except AttributeError:
			ret = self._showStatusBar = True
		return ret	
	def _setShowStatusBar(self, val):
		self._showStatusBar = bool(val)
		
	def _getShowSystemMenu(self):
		return self._hasWindowStyleFlag(wx.SYSTEM_MENU)
	def _setShowSystemMenu(self, value):
		self._delWindowStyleFlag(wx.SYSTEM_MENU)
		if value:
			self._addWindowStyleFlag(wx.SYSTEM_MENU)
			
	def _getShowToolBar(self):
		try:
			ret = self._showToolBar
		except AttributeError:
			# Default to no toolbar
			ret = self._showToolBar = False
		return ret
	def _setShowToolBar(self, val):
		self._showToolBar = bool(val)	
	

	def _getStatusText(self):
		ret = ""
		if isinstance(self, wx.MDIChildFrame):
			controllingFrame = self.Application.MainForm
		else:
			controllingFrame = self
		try:
			sb = controllingFrame.GetStatusBar()
		except AttributeError:
			# certain dialogs don't have status bars
			sb = None
		if sb:
			ret = sb.GetStatusText()
		return ret

	def _setStatusText(self, val):
		""" Set the text of the status bar. Dabo will decide whether to 
		send the text to the main frame or this frame. This matters with MDI
		versus non-MDI forms.
		"""
		hasStatus = True
		if isinstance(self, wx.MDIChildFrame):
			controllingFrame = self.Application.MainForm
		else:
			controllingFrame = self
		try:
			controllingFrame.GetStatusBar
		except AttributeError:
			hasStatus = False
		if hasStatus and controllingFrame.GetStatusBar():
			if self._holdStatusText:
				controllingFrame.SetStatusText(self._holdStatusText)
				self._holdStatusText = ""
			else:
				controllingFrame.SetStatusText(val)
			controllingFrame.GetStatusBar().Update()

	def _getTinyTitleBar(self):
		return self._hasWindowStyleFlag(wx.FRAME_TOOL_WINDOW)
	def _setTinyTitleBar(self, value):
		self._delWindowStyleFlag(wx.FRAME_TOOL_WINDOW)
		if value:
			self._addWindowStyleFlag(wx.FRAME_TOOL_WINDOW)

	def _getWindowState(self):
		try:
			if self.IsFullScreen():
				return "FullScreen"
			elif self.IsMaximized():
				return "Maximized"
			elif self.IsIconized():
				return "Minimized"
			else:
				return "Normal"
		except AttributeError:
			# These only work on Windows, I fear
			return "Normal"

	def _setWindowState(self, value):
		if self._constructed():
			lowvalue = str(value).lower().strip()
			if lowvalue == "normal":
				if self.IsFullScreen():
					self.ShowFullScreen(False)
				elif self.IsMaximized():
					self.Maximize(False)
				elif self.IsIconized():
					self.Iconize(False)
				else:
					# window already normal, but just in case:
					self.Maximize(False)
			elif lowvalue == "minimized":
				self.Iconize()
			elif lowvalue == "maximized":
				self.Maximize()
			elif lowvalue == "fullscreen":
				self.ShowFullScreen()
			else:
				raise ValueError, ("The only possible values are "
								"'Normal', 'Minimized', 'Maximized', and 'FullScreen'")
		else:
			self._properties["WindowState"] = value


	# property definitions follow:
	ActiveControl = property(_getActiveControl, None, None, 
		_("Contains a reference to the active control on the form, or None."))

	BorderResizable = property(_getBorderResizable, _setBorderResizable, None,
		_("Specifies whether the user can resize this form. (bool)."))

	Centered = property(_getCentered, _setCentered, None, 
		_("Centers the form on the screen when set to True.  (bool)"))

	Icon = property(_getIcon, _setIcon, None, 
		_("Specifies the icon for the form. (wxIcon)"))

	IconBundle = property(_getIconBundle, _setIconBundle, None,
		_("Specifies the set of icons for the form. (wxIconBundle)"))

	FloatOnParent = property(_getFloatOnParent, _setFloatOnParent, None,
		_("Specifies whether the form stays on top of the parent or not."))

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

	ShowInTaskBar = property(_getShowInTaskBar, _setShowInTaskBar, None,
		_("Specifies whether the form is shown in the taskbar.  (bool)."))

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

	ShowToolBar = property(_getShowToolBar, _setShowToolBar, None,
		_("Specifies whether the Tool bar gets automatically created."))

	StatusBar = property(_getStatusBar, None, None,
		_("Status bar for this form. (dStatusBar)"))

	StatusText = property(_getStatusText, _setStatusText, None,
		_("Text displayed in the form's status bar. (string)"))

	TinyTitleBar = property(_getTinyTitleBar, _setTinyTitleBar, None,
		_("Specifies whether the title bar is small, like a tool window. (bool)."))

	ToolBar = property(_getToolBar, _setToolBar, None,
		_("Tool bar for this form. (dToolBar)"))

	WindowState = property(_getWindowState, _setWindowState, None,
		_("""Specifies the current state of the form. (int)
			
				Normal
				Minimized
				Maximized
				FullScreen"""))
