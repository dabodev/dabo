""" daboApp.py: The application object and the main frame object. """

import sys, os, wx
from dabo.db import *
from dabo.biz import *
from dabo.ui.uiwx.classes import *

class uiApp(wx.App):
	def __init__(self, *args):
		wx.App.__init__(self, 0, args)


	def OnInit(self):
		return True


	def setup(self, dApp):
		# wx has properties for appName and vendorName, so Dabo should update
		# these. Among other possible uses, I know that on Win32 wx will use
		# these for determining the registry key structure.
		self.SetAppName(dApp.getAppInfo("appName"))
		self.SetClassName(dApp.getAppInfo("appName"))
		self.SetVendorName(dApp.getAppInfo("vendorName"))
		
		wx.InitAllImageHandlers()

		self.dApp = dApp

		self.mainFrame = dFormMain(dApp)
		self.SetTopWindow(self.mainFrame)

		self.mainFrame.Show()
		if wx.Platform == '__WXMAC__':
			self.mainFrame.SetSize((1,1))


	def start(self, dApp):
		self.MainLoop()

	def onFileExit(self, event):
		self.mainFrame.Close(True)


	def onEditCut(self, event):
		self.onEditCopy(event, cut=True)


	def onEditCopy(self, event, cut=False):
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
		else:
			print "no selected text"


	def onEditPaste(self, event):
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
			else: 
				print "No text in the clipboard."

		else:
			print "Control isn't text-based."


	def onEditPreferences(self, event):
		print "Stub: uiApp.onEditPreferences()"


	def onEditFind(self, event):
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


	def OnFindClose(self, event):
		""" User clicked the close button, so hide the dialog.
		"""
		event.GetEventObject().Hide()
		event.Skip()


	def OnFind(self, event):
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
				print "Active control isn't text-based."
				return

			flags = event.GetFlags()
			findString = event.GetFindString()
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
				print "not found"


	def onHelpAbout(self, event):
		dlg = dAbout(self.mainFrame, self.dApp)
		dlg.Show()
