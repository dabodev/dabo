import sys, os, wx
import dabo
import dabo.ui as ui
import dabo.dEvents as dEvents
from dabo.common.dObject import dObject

class uiApp(wx.App, dObject):
	_IsContainer = False
	
	def __init__(self, *args):
		wx.App.__init__(self, 0, args)
		dObject.__init__(self)
		self.Bind(wx.EVT_ACTIVATE_APP, self._onWxActivate)
		# track the active form
		self.__activeForm = None
		
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

		string = "wxPython Version: %s %s" % (wx.VERSION_STRING, 
			wx.PlatformInfo[1])
			
		if wx.PlatformInfo[0] == "__WXGTK__":
			string += " (%s)" % wx.PlatformInfo[3]
			self._platform = "GTK"
		elif wx.PlatformInfo[0] == "__WXMAC__":
			self._platform = "Mac"
		elif wx.PlatformInfo[0] == "__WXMSW__":
			self._platform = "Win"

		dabo.infoLog.write(string)
			
		wx.InitAllImageHandlers()

		self.dApp = dApp
		
		if dApp.MainFormClass is not None:
			self.dApp.MainForm = dApp.MainFormClass()
			self.SetTopWindow(self.dApp.MainForm)
			self.dApp.MainForm.Show(dApp.showMainFormOnStart)
			

	def start(self, dApp):
		# Manually raise Activate, as wx doesn't do that automatically
		self.raiseEvent(dEvents.Activate)
		self.MainLoop()

	
	def finish(self):
		# Manually raise Deactivate, as wx doesn't do that automatically
		self.raiseEvent(dEvents.Deactivate)
	
	
	def _getPlatform(self):
		return self._platform
		
	def _onWxActivate(self, evt):
		""" Raise the Dabo Activate or Deactivate appropriately.
		"""
		if bool(evt.GetActive()):
			self.raiseEvent(dEvents.Activate, evt)
		else:
			self.raiseEvent(dEvents.Deactivate, evt)
		evt.Skip()
			
	
	def onFileExit(self, evt):
		if self.dApp.MainForm is not None:
			self.dApp.MainForm.Close(True)
		else:
			frmCollect = self.dApp.uiForms
			while len(frmCollect):
				for form in frmCollect:
					try:
						form.saveSizeAndPosition()
						frmCollect.remove(form)
						form.Close(True)
					except wx.PyDeadObjectError:
						pass
				


	def onEditCut(self, evt):
		self.onEditCopy(evt, cut=True)


	def onEditCopy(self, evt, cut=False):
		# Some controls (stc...) have Cut(), Copy(), Paste() methods,
		# while others do not. Try these methods first, but fall back
		# to interacting with wx.TheClipboard if necessary.
		if self.ActiveForm:
			win = self.ActiveForm.FindFocus()
			try:
				if cut:
					win.Cut()
				else:
					win.Copy()
					
			except AttributeError:
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
		if self.ActiveForm:
			win = self.ActiveForm.FindFocus()
			try:
				win.Paste()
			except AttributeError:
			
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


	def onEditUndo(self, evt):
		if self.ActiveForm:
			win = self.ActiveForm.FindFocus()
			try:
				win.Undo()
			except AttributeError:
				dabo.errorLog.write("No apparent way to undo.")
	

	def onEditRedo(self, evt):
		if self.ActiveForm:
			win = self.ActiveForm.FindFocus()
			try:
				win.Redo()
			except AttributeError:
				dabo.errorLog.write("No apparent way to redo.")


	def onEditFind(self, evt):
		""" Display a Find dialog. 
		"""
		if self.ActiveForm:
			win = self.ActiveForm.FindFocus()
			if win:
				self.findWindow = win           # Save reference for use by self.OnFind()
	
				try:
					data = self.findReplaceData
				except AttributeError:
					data = wx.FindReplaceData(wx.FR_DOWN)
					self.findReplaceData = data
				dlg = wx.FindReplaceDialog(win, data, "Find")
				
				# Map enter key to find button:
				anId = wx.NewId()
				dlg.SetAcceleratorTable(wx.AcceleratorTable([(wx.ACCEL_NORMAL, wx.WXK_RETURN, anId),]))
				dlg.Bind(wx.EVT_MENU, self.onEnterInFindDialog, id=anId)
	
				dlg.Bind(wx.EVT_FIND, self.OnFind)
				dlg.Bind(wx.EVT_FIND_NEXT, self.OnFind)
				dlg.Bind(wx.EVT_CLOSE, self.OnFindClose)
	
				dlg.Show()
	#- 			self.findDialog = dlg
			
	
	def onEnterInFindDialog(self, evt):
		## I don't know what to do from here: how do I simulate the user
		## clicking "find"...
		pass
#- 		findButton = None
#- 		dlg = self.findDialog
#- #- 		print dir(dlg)
#- 		for child in dlg.GetChildren():
#- 			if child.GetName() == "button" and child.GetLabel() == "Find":
#- 				findButton = child
#- 				break
#- 		if findButton is not None:
#- 			findButton.Command(wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED))			
					

	def onEditFindAgain(self, evt):
		"""Repeat the last search.
		"""
		try:
			fd = self.findReplaceData
			self.OnFind(fd)
		except AttributeError:
			self.onEditFind(None)
			return
			

	def OnFindClose(self, evt):
		""" User clicked the close button, so hide the dialog.
		"""
		evt.GetEventObject().Destroy()
		evt.Skip()


	def OnFind(self, evt):
		""" User clicked the 'find' button in the find dialog.

		Run the search on the current control, if it is a text-based control.
		Select the found text in the control.
		"""
#- 		flags = evt.GetFlags()
#- 		findString = evt.GetFindString()
		flags = self.findReplaceData.GetFlags()
		findString = self.findReplaceData.GetFindString()
		downwardSearch = (flags & wx.FR_DOWN) == wx.FR_DOWN
		wholeWord = (flags & wx.FR_WHOLEWORD) == wx.FR_WHOLEWORD
		matchCase = (flags & wx.FR_MATCHCASE) == wx.FR_MATCHCASE
		
		win = self.findWindow
		
		if win:
			try:
				# SCT:
				start = win.GetCurrentPos()
				flags = 0
				if downwardSearch:
					finish = win.GetTextLength()
				else:
					finish = 0
				pos = win.FindText(start, finish, findString, flags)
				if pos > -1:
					win.SetSelection(pos, pos+len(findString))
				
			except AttributeError:		
				try: 
					value = win.GetValue()
				except AttributeError:
					value = None
				if type(value) not in (type(str()), type(unicode())):
					dabo.errorLog.write("Active control isn't text-based.")
					return


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
		dlg = ui.dAbout(self.dApp.MainForm)
		dlg.show()

		
	def getLoginInfo(self, message=None):
		""" Display the login form, and return the user/password as entered by the user.
		"""
		try:
			ld = self.loginDialog
		except AttributeError:
			ld = ui.dLogin(self.dApp.MainForm)
		if message:
			ld.setMessage(message)
		ld.CenterOnParent()
		ld.ShowModal()
		user, password = ld.user, ld.password
		self.loginDialog = ld
		return user, password
	
	
	def onCmdWin(self, evt):
		"""Display a command window for debugging."""
		try:
			self.ActiveForm.onCmdWin(evt)
		except AttributeError:
			# Either no form active, or it's not a proper Dabo form
			pass
	

	def _getActiveForm(self):
		return self.__activeForm
	def _setActiveForm(self, frm):
		self.__activeForm = frm
	
	ActiveForm = property(_getActiveForm, _setActiveForm, None, 
			"Returns the form that currently has focus, or None.  (dForm)" )

