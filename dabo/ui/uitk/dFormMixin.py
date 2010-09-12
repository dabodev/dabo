# -*- coding: utf-8 -*-
""" dFormMixin.py """
import dPemMixin as pm
from dabo.dLocalize import _
from dabo.lib.utils import ustr
import dabo.dEvents as dEvents

class dFormMixin(pm.dPemMixin):
	def __init__(self, preClass, parent=None, properties=None, *args, **kwargs):
#		if parent:
#			style = wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT
#		else:
#			style = wx.DEFAULT_FRAME_STYLE

#		kwargs["style"] = style

		super(dFormMixin, self).__init__(preClass, parent, properties, *args, **kwargs)

		self.debugText = ""
		self.useOldDebugDialog = False
		self.restoredSP = False
		self._holdStatusText = ""
		if self.Application is not None:
			self.Application.uiForms.add(self)



# 	def OnActivate(self, event):
# 		if bool(event.GetActive()) == True and self.restoredSP == False:
# 			# Restore the saved size and position, which can't happen
# 			# in __init__ because we may not have our name yet.
# 			self.restoredSP = True
# 			self.restoreSizeAndPosition()
# 		event.Skip()
#
#
# 	def afterSetMenuBar(self):
# 		""" Subclasses can extend the menu bar here.
# 		"""
# 		pass
#
#
# 	def onDebugDlg(self, evt):
# 		# Handy hook for getting info.
# 		dlg = wx.TextEntryDialog(self, "Command to Execute", "Debug", self.debugText)
# 		if dlg.ShowModal() == wx.ID_OK:
# 			self.debugText = dlg.GetValue()
# 			try:
# 				# Handy shortcuts for common references
# 				bo = self.getBizobj()
# 				exec(self.debugText)
# 			except:
# 				dabo.log.info(_("Could not execute: %s") % self.debugText)
# 		dlg.Destroy()
#
#
# 	def getMenu(self):
# 		""" Get the navigation menu for this form.
#
# 		Every form maintains an internal menu of actions appropriate to itself.
# 		For instance, a dForm with a primary bizobj will maintain a menu with
# 		'requery', 'save', 'next', etc. choices.
#
# 		This function sets up the internal menu, which can optionally be
# 		inserted into the mainForm's menu bar during SetFocus.
# 		"""
# 		menu = dMenu.dMenu()
# 		return menu
#
#
# 	def OnClose(self, event):
# 		if self.GetParent() == wx.GetApp().GetTopWindow():
# 			self.Application.uiForms.remove(self)
# 		self.saveSizeAndPosition()
# 		event.Skip()
#
# 	def OnSetFocus(self, event):
# 		event.Skip()
#
#
# 	def OnKillFocus(self, event):
# 		event.Skip()
#
#
# 	def restoreSizeAndPosition(self):
# 		""" Restore the saved window geometry for this form.
#
# 		Ask dApp for the last saved setting of height, width, left, and top,
# 		and set those properties on this form.
# 		"""
# 		if self.Application:
# 			name = self.getAbsoluteName()
#
# 			left = self.Application.getUserSetting("%s.left" % name)
# 			top = self.Application.getUserSetting("%s.top" % name)
# 			width = self.Application.getUserSetting("%s.width" % name)
# 			height = self.Application.getUserSetting("%s.height" % name)
#
# 			if (type(left), type(top)) == (type(int()), type(int())):
# 				self.SetPosition((left,top))
# 			if (type(width), type(height)) == (type(int()), type(int())):
# 				self.SetSize((width,height))
#
#
# 	def saveSizeAndPosition(self):
# 		""" Save the current size and position of this form.
# 		"""
# 		if self.Application:
# 			if self == wx.GetApp().GetTopWindow():
# 				for form in self.Application.uiForms:
# 					try:
# 						form.saveSizeAndPosition()
# 					except wx.PyDeadObjectError:
# 						pass
#
# 			name = self.getAbsoluteName()
#
# 			pos = self.GetPosition()
# 			size = self.GetSize()
#
# 			self.Application.setUserSetting("%s.left" % name, "I", pos[0])
# 			self.Application.setUserSetting("%s.top" % name, "I", pos[1])
# 			self.Application.setUserSetting("%s.width" % name, "I", size[0])
# 			self.Application.setUserSetting("%s.height" % name, "I", size[1])
#
#
# 	def setStatusText(self, *args):
# 		""" Set the text of the status bar.
#
# 		Call this instead of SetStatusText() and dabo will decide whether to
# 		send the text to the main frame or this frame. This matters with MDI
# 		versus non-MDI forms.
# 		"""
# 		if isinstance(self, wx.MDIChildFrame):
# 			controllingFrame = self.Application.MainForm
# 		else:
# 			controllingFrame = self
# 		if controllingFrame.GetStatusBar():
# 			controllingFrame.SetStatusText(*args)
# 			controllingFrame.GetStatusBar().Update()
#
#
# 	def _appendToMenu(self, menu, caption, function, bitmap=wx.NullBitmap, menuId=-1):
# 		item = wx.MenuItem(menu, menuId, caption)
# 		item.SetBitmap(bitmap)
# 		menu.AppendItem(item)
#
# 		if isinstance(self, wx.MDIChildFrame):
# 			controllingFrame = self.Application.MainForm
# 		else:
# 			controllingFrame = self
#
# 		if wx.Platform == '__WXMAC__':
# 			# Trial and error reveals that this works on Mac, while calling
# 			# controllingFrame.Bind does not. I've posted an inquiry about
# 			# this to wxPython-mac@wxwidgets.org, but in the meantime we have
# 			# this platform-specific code to tide us over.
# 			menu.Bind(wx.EVT_MENU, function, item)
# 		else:
# 			controllingFrame.Bind(wx.EVT_MENU, function, item)
#
#
# 	def _appendToToolBar(self, toolBar, caption, bitmap, function, statusText=""):
# 		toolId = wx.NewId()
# 		toolBar.AddSimpleTool(toolId, bitmap, caption, statusText)
#
# 		if isinstance(self, wx.MDIChildFrame):
# 			controllingFrame = self.Application.MainForm
# 		else:
# 			controllingFrame = self
# 		wx.EVT_MENU(controllingFrame, toolId, function)
#
#
# 	# property get/set/del functions follow:
# 	def _getIcon(self):
# 		try:
# 			return self._Icon
# 		except AttributeError:
# 			return None
# 	def _setIcon(self, icon):
# 		self.SetIcon(icon)
# 		self._Icon = icon       # wx doesn't provide GetIcon()
#
# 	def _getIconBundle(self):
# 		try:
# 			return self._Icons
# 		except:
# 			return None
# 	def _setIconBundle(self, icons):
# 		self.SetIcons(icons)
# 		self._Icons = icons       # wx doesn't provide GetIcons()
#
# 	def _getBorderResizable(self):
# 		return self._hasWindowStyleFlag(wx.RESIZE_BORDER)
# 	def _setBorderResizable(self, value):
# 		self._delWindowStyleFlag(wx.RESIZE_BORDER)
# 		if value:
# 			self._addWindowStyleFlag(wx.RESIZE_BORDER)
#
# 	def _getShowMaxButton(self):
# 		return self._hasWindowStyleFlag(wx.MAXIMIZE_BOX)
# 	def _setShowMaxButton(self, value):
# 		self._delWindowStyleFlag(wx.MAXIMIZE_BOX)
# 		if value:
# 			self._addWindowStyleFlag(wx.MAXIMIZE_BOX)
#
# 	def _getShowMinButton(self):
# 		return self._hasWindowStyleFlag(wx.MINIMIZE_BOX)
# 	def _setShowMinButton(self, value):
# 		self._delWindowStyleFlag(wx.MINIMIZE_BOX)
# 		if value:
# 			self._addWindowStyleFlag(wx.MINIMIZE_BOX)
#
# 	def _getShowCloseButton(self):
# 		return self._hasWindowStyleFlag(wx.CLOSE_BOX)
# 	def _setShowCloseButton(self, value):
# 		self._delWindowStyleFlag(wx.CLOSE_BOX)
# 		if value:
# 			self._addWindowStyleFlag(wx.CLOSE_BOX)
#
# 	def _getShowCaption(self):
# 		return self._hasWindowStyleFlag(wx.CAPTION)
# 	def _setShowCaption(self, value):
# 		self._delWindowStyleFlag(wx.CAPTION)
# 		if value:
# 			self._addWindowStyleFlag(wx.CAPTION)
#
# 	def _getShowSystemMenu(self):
# 		return self._hasWindowStyleFlag(wx.SYSTEM_MENU)
# 	def _setShowSystemMenu(self, value):
# 		self._delWindowStyleFlag(wx.SYSTEM_MENU)
# 		if value:
# 			self._addWindowStyleFlag(wx.SYSTEM_MENU)
#
# 	def _getTinyTitleBar(self):
# 		return self._hasWindowStyleFlag(wx.FRAME_TOOL_WINDOW)
# 	def _setTinyTitleBar(self, value):
# 		self._delWindowStyleFlag(wx.FRAME_TOOL_WINDOW)
# 		if value:
# 			self._addWindowStyleFlag(wx.FRAME_TOOL_WINDOW)
#
# 	def _getWindowState(self):
# 		try:
# 			if self.IsFullScreen():
# 				return 'FullScreen'
# 			elif self.IsMaximized():
# 				return 'Maximized'
# 			elif self.IsMinimized():
# 				return 'Minimized'
# 			else:
# 				return 'Normal'
# 		except AttributeError:
# 			# These only work on Windows, I fear
# 			return 'Normal'
#
# 	def _getWindowStateEditorInfo(self):
# 		return {'editor': 'list', 'values': ['Normal', 'Minimized', 'Maximized', 'FullScreen']}
#
# 	def _setWindowState(self, value):
# 		value = ustr(value)
# 		if value == 'Normal':
# 			if self.IsFullScreen():
# 				self.ShowFullScreen(False)
# 			elif self.IsMaximized():
# 				self.Maximize(False)
# 			elif self.IsIconized:
# 				self.Iconize(False)
# 			else:
# 				# window already normal, but just in case:
# 				self.Maximize(False)
# 		elif value == 'Minimized':
# 			self.Iconize()
# 		elif value == 'Maximized':
# 			self.Maximize()
# 		elif value == 'FullScreen':
# 			self.ShowFullScreen()
# 		else:
# 			raise ValueError("The only possible values are "
# 							"'Normal', 'Minimized', 'Maximized', and 'FullScreen'")
#
# 	# property definitions follow:
# 	Icon = property(_getIcon, _setIcon, None, 'Specifies the icon for the form. (wxIcon)')
# 	IconBundle = property(_getIconBundle, _setIconBundle, None,
# 							'Specifies the set of icons for the form. (wxIconBundle)')
#
# 	BorderResizable = property(_getBorderResizable, _setBorderResizable, None,
# 					'Specifies whether the user can resize this form. (bool).')
#
# 	ShowCaption = property(_getShowCaption, _setShowCaption, None,
# 					'Specifies whether the caption is displayed in the title bar. (bool).')
#
# 	ShowMaxButton = property(_getShowMaxButton, _setShowMaxButton, None,
# 					'Specifies whether a maximize button is displayed in the title bar. (bool).')
#
# 	ShowMinButton = property(_getShowMinButton, _setShowMinButton, None,
# 					'Specifies whether a minimize button is displayed in the title bar. (bool).')
#
# 	ShowCloseButton = property(_getShowCloseButton, _setShowCloseButton, None,
# 					'Specifies whether a close button is displayed in the title bar. (bool).')
#
# 	ShowSystemMenu = property(_getShowSystemMenu, _setShowSystemMenu, None,
# 					'Specifies whether a system menu is displayed in the title bar. (bool).')
#
# 	TinyTitleBar = property(_getTinyTitleBar, _setTinyTitleBar, None,
# 					'Specifies whether the title bar is small, like a tool window. (bool).')
#
# 	WindowState = property(_getWindowState, _setWindowState, None,
# 					'Specifies the current state of the form. (int)\n'
# 					'    Normal \n'
# 					'    Minimized \n'
# 					'    Maximized \n'
# 					'    FullScreen')
