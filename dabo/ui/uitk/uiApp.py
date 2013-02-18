# -*- coding: utf-8 -*-
import sys, os
import Tkinter
import dabo
import dabo.ui as ui
import dabo.dEvents as dEvents
from dabo.dObject import dObject


# First step is to figure out how to wrap a tk application object if there is one.
# When that is done, copy/paste/modify from uiwx/uiApp.py.

# It doesn't look like Tkinter has an application object, just a mainloop() method.
class uiApp(dObject):

	def __init__(self, app, callback=None, *args):
		self.Name = "uiApp"
		self.dApp = app
		self.callback = callback
		super(uiApp, self).__init__()

	def setup(self):

		if self.dApp.MainFormClass is not None:
			self.dApp.MainForm = self.dApp.MainFormClass()

	def start(self):
		self.raiseEvent(dEvents.Activate)
		Tkinter.mainloop()

	def exit(self):
		return

	def finish(self):
		self.raiseEvent(dEvents.Deactivate)

	def onFileExit(self, evt):
		self.MainForm.Close(True)


	def onEditCut(self, evt):
		self.onEditCopy(evt, cut=True)


	def onEditCopy(self, evt, cut=False):
		pass
# 		win = wx.GetActiveWindow().FindFocus()
# 		try:
# 			selectedText = win.GetStringSelection()
# 		except AttributeError:
# 			selectedText = None
#
# 		if selectedText:
# 			data = wx.TextDataObject()
# 			data.SetText(selectedText)
# 			cb = wx.TheClipboard
# 			cb.Open()
# 			cb.SetData(data)
# 			cb.Close()
#
# 			if cut:
# 				win.Remove(win.GetSelection()[0], win.GetSelection()[1])


	def onEditPaste(self, evt):
		pass
# 		win = wx.GetActiveWindow().FindFocus()
# 		try:
# 			selection = win.GetSelection()
# 		except AttributeError:
# 			selection = None
#
# 		if selection != None:
# 			data = wx.TextDataObject()
# 			cb = wx.TheClipboard
# 			cb.Open()
# 			success = cb.GetData(data)
# 			cb.Close()
# 			if success:
# 				win.Replace(selection[0], selection[1], data.GetText())



	def onEditPreferences(self, evt):
		dabo.log.info("Stub: uiApp.onEditPreferences()")


	def onEditFind(self, evt):
		""" Display a Find dialog.
		"""
		pass
# 		win = wx.GetActiveWindow().FindFocus()
# 		if win:
# 			self.findWindow = win           # Save reference for use by self.OnFind()
#
# 			try:
# 				data = self.findReplaceData
# 			except AttributeError:
# 				data = wx.FindReplaceData(wx.FR_DOWN)
# 				self.findReplaceData = data
# 			dlg = wx.FindReplaceDialog(win, data, "Find")
#
# 			dlg.Bind(wx.EVT_FIND, self.OnFind)
# 			dlg.Bind(wx.EVT_FIND_NEXT, self.OnFind)
# 			dlg.Bind(wx.EVT_CLOSE, self.OnFindClose)
#
# 			dlg.Show()


	def onEditFindAgain(self, evt):
		pass

	def onEditUndo(self, evt):
		pass

	def onEditRedo(self, evt):
		pass

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
		return
# 		win = self.findWindow
# 		if win:
# 			try:
# 				value = win.GetValue()
# 			except AttributeError:
# 				value = None
# 			if type(value) not in (type(str()), type(unicode())):
# 				dabo.log.error("Active control isn't text-based.")
# 				return
#
# 			flags = event.GetFlags()
# 			findString = event.GetFindString()
# 			downwardSearch = (flags & wx.FR_DOWN) == wx.FR_DOWN
# 			wholeWord = (flags & wx.FR_WHOLEWORD) == wx.FR_WHOLEWORD
# 			matchCase = (flags & wx.FR_MATCHCASE) == wx.FR_MATCHCASE
#
# 			currentPos = win.GetInsertionPoint()
#
# 			if downwardSearch:
# 				value = win.GetValue()[currentPos:]
# 			else:
# 				value = win.GetValue()[0:currentPos]
# 				value = list(value)
# 				value.reverse()
# 				value = ''.join(value)
# 				findString = list(findString)
# 				findString.reverse()
# 				findString = ''.join(findString)
#
# 			if not matchCase:
# 				value = value.lower()
# 				findString = findString.lower()
#
# 			result = value.find(findString)
# 			if result >= 0:
# 				if downwardSearch:
# 					win.SetSelection(currentPos+result, currentPos+result+len(findString))
# 				else:
# 					win.SetSelection(currentPos-result, currentPos-result-len(findString))
# 				win.ShowPosition(win.GetSelection()[1])
# 			else:
# 				dabo.log.info("Not found")


	def onHelpAbout(self, event):
		dlg = ui.dAbout(self.MainForm, self.dApp)
		dlg.Show()


	def getLoginInfo(self, message=None):
		""" Display the login form, and return the user/password as entered by the user.
		"""
		dlg = ui.dLogin(None)
		if message:
			dlg.setMessage(message)
		dlg.ShowModal()
		user, password = dlg.user, dlg.password
		dlg.Destroy()
		return user, password

	def setMainForm(self, val):
		pass
#		try:
#			self.dApp.MainForm.Destroy()
##		except:
#			pass
#		self.SetTopWindow(val)
#		val.Show(self.dApp.showMainFormOnStart)

