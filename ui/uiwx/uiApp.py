import sys, os, wx
import dabo
import dabo.ui as ui
import dabo.dEvents as dEvents
from dabo.common.dObject import dObject

class uiApp(wx.App, dObject):
	def __init__(self, *args):
		wx.App.__init__(self, 0, args)
		dObject.__init__(self)
		self.Bind(wx.EVT_ACTIVATE_APP, self._onWxActivate)
		
		self.Name = "uiApp"
		
		
	def OnInit(self):
		return True


	def setup(self, dApp):
		# wx has properties for appName and vendorName, so Dabo should update
		# these. Among other possible uses, I know that on Win32 wx will use
		# these for determining the registry key structure.
		self.SetAppName(dApp.getAppInfo("appName"))
		self.SetClassName(dApp.getAppInfo("appName"))
		self.SetVendorName(dApp.getAppInfo("vendorName"))
		
		dabo.infoLog.write("wxPython Version: %s %s (%s)" % (
			wx.VERSION_STRING, wx.PlatformInfo[1], wx.PlatformInfo[3]))
			
		wx.InitAllImageHandlers()

		self.dApp = dApp
		
		if dApp.MainFrameClass is not None:
			self.dApp.MainFrame = dApp.MainFrameClass()
			self.SetTopWindow(self.dApp.MainFrame)
			self.dApp.MainFrame.Show()


	def start(self, dApp):
		# Manually raise Activate, as wx doesn't do that automatically
		self.raiseEvent(dEvents.Activate)
		self.MainLoop()

	
	def finish(self):
		# Manually raise Deactivate, as wx doesn't do that automatically
		self.raiseEvent(dEvents.Deactivate)
				
		
	def _onWxActivate(self, evt):
		""" Raise the Dabo Activate or Deactivate appropriately.
		"""
		if bool(evt.GetActive()):
			self.raiseEvent(dEvents.Activate, evt)
		else:
			self.raiseEvent(dEvents.Deactivate, evt)
		evt.Skip()
			
	
	def onFileExit(self, evt):
		if self.dApp.MainFrame is not None:
			self.dApp.MainFrame.Close(True)


	def onEditCut(self, evt):
		self.onEditCopy(evt, cut=True)


	def onEditCopy(self, evt, cut=False):
		win = wx.GetActiveWindow().FindFocus()
		try:
			selectedText = win.GetStringSelection()
		except AttributeError:
			selectedText = None

		if selectedText:
			data = wx.TextDataObject()
			data.SetText(selectedText)
			cb = wx.TheClipboard
			cb.Open()
			cb.SetData(data)
			cb.Close()

			if cut:
				win.Remove(win.GetSelection()[0], win.GetSelection()[1])


	def onEditPaste(self, evt):
		win = wx.GetActiveWindow().FindFocus()
		try:
			selection = win.GetSelection()
		except AttributeError:
			selection = None

		if selection != None:
			data = wx.TextDataObject()
			cb = wx.TheClipboard
			cb.Open()
			success = cb.GetData(data)
			cb.Close() 
			if success: 
				win.Replace(selection[0], selection[1], data.GetText())
		


	def onEditPreferences(self, evt):
		dabo.infoLog.write("Stub: uiApp.onEditPreferences()")


	def onEditFind(self, evt):
		""" Display a Find dialog. 
		"""
		win = wx.GetActiveWindow().FindFocus()
		if win:
			self.findWindow = win           # Save reference for use by self.OnFind()

			try:
				data = self.findReplaceData
			except AttributeError:
				data = wx.FindReplaceData(wx.FR_DOWN)
				self.findReplaceData = data
			dlg = wx.FindReplaceDialog(win, data, "Find")

			dlg.Bind(wx.EVT_FIND, self.OnFind)
			dlg.Bind(wx.EVT_FIND_NEXT, self.OnFind)
			dlg.Bind(wx.EVT_CLOSE, self.OnFindClose)

			dlg.Show()


	def OnFindClose(self, evt):
		""" User clicked the close button, so hide the dialog.
		"""
		evt.GetEventObject().Hide()
		evt.Skip()


	def OnFind(self, evt):
		""" User clicked the 'find' button in the find dialog.

		Run the search on the current control, if it is a text-based control.
		Select the found text in the control.
		"""
		win = self.findWindow
		if win:
			try: 
				value = win.GetValue()
			except AttributeError:
				value = None
			if type(value) not in (type(str()), type(unicode())):
				dabo.errorLog.write("Active control isn't text-based.")
				return

			flags = evt.GetFlags()
			findString = evt.GetFindString()
			downwardSearch = (flags & wx.FR_DOWN) == wx.FR_DOWN
			wholeWord = (flags & wx.FR_WHOLEWORD) == wx.FR_WHOLEWORD
			matchCase = (flags & wx.FR_MATCHCASE) == wx.FR_MATCHCASE

			currentPos = win.GetInsertionPoint()

			if downwardSearch:
				value = win.GetValue()[currentPos:]
			else:
				value = win.GetValue()[0:currentPos]
				value = list(value)
				value.reverse()
				value = ''.join(value)
				findString = list(findString)
				findString.reverse()
				findString = ''.join(findString)

			if not matchCase:
				value = value.lower()
				findString = findString.lower()

			result = value.find(findString)
			if result >= 0:
				if downwardSearch:
					win.SetSelection(currentPos+result, currentPos+result+len(findString))
				else:
					win.SetSelection(currentPos-result, currentPos-result-len(findString))
				win.ShowPosition(win.GetSelection()[1])
			else:
				dabo.infoLog.write("Not found")


	def onHelpAbout(self, evt):
		dlg = ui.dAbout(self.dApp.MainFrame, self.dApp)
		dlg.Show()

		
	def getLoginInfo(self, message=None):
		""" Display the login form, and return the user/password as entered by the user.
		"""
		try:
			ld = self.loginDialog
		except AttributeError:
			ld = ui.dLogin(self.dApp.MainFrame)
		if message:
			ld.setMessage(message)
		ld.CenterOnParent()
		ld.ShowModal()
		user, password = ld.user, ld.password
		self.loginDialog = ld
		return user, password

	
