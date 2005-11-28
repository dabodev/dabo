import sys, os, wx
import dabo
import dabo.ui as ui
import dabo.dEvents as dEvents
import dabo.lib.utils as utils
from dabo.dObject import dObject
from dabo.dLocalize import _, n_
import dabo.dConstants as kons


class uiApp(wx.App, dObject):
	def __init__(self, *args):
		wx.App.__init__(self, 0, args)
		dObject.__init__(self)
		self.Bind(wx.EVT_ACTIVATE_APP, self._onWxActivate)
		
		self.Name = _("uiApp")
		self._noneDisp = _("<null>")
		self._drawSizerOutlines = False
		# Various attributes used by the FindReplace dialog
		self._findString = ""
		self._replaceString = ""
		self._findReplaceFlags = wx.FR_DOWN
		self._findDlgID = self._replaceDlgID = None
		self.findReplaceData = None
		self.findDialog = None
		
		
	def OnInit(self):
		return True


	def setup(self, dApp):
		# wx has properties for appName and vendorName, so Dabo should update
		# these. Among other possible uses, I know that on Win32 wx will use
		# these for determining the registry key structure.
		self.SetAppName(dApp.getAppInfo("appName"))
		self.SetClassName(dApp.getAppInfo("appName"))
		self.SetVendorName(dApp.getAppInfo("vendorName"))
		
		self.charset = "unicode"
		if not self.charset in wx.PlatformInfo:
			self.charset = "ascii"
		string = "wxPython Version: %s %s (%s)" % (wx.VERSION_STRING, 
			wx.PlatformInfo[1], self.charset)
			
		if wx.PlatformInfo[0] == "__WXGTK__":
			string += " (%s)" % wx.PlatformInfo[3]
			self._platform = _("GTK")
		elif wx.PlatformInfo[0] == "__WXMAC__":
			self._platform = _("Mac")
		elif wx.PlatformInfo[0] == "__WXMSW__":
			self._platform = _("Win")

		dabo.infoLog.write(string)
			
		wx.InitAllImageHandlers()

		self.dApp = dApp
	
		frm = dApp.MainForm
		if frm is None:
			if dApp.MainFormClass is not None:
				mfc = dApp.MainFormClass
				if isinstance(mfc, basestring):
					# It is a path to .cdxml file
					frm = self.dApp.MainForm = dabo.ui.createForm(mfc)
				else:
					frm = self.dApp.MainForm = mfc()
		if frm is not None:
			if len(frm.Caption) == 0:
				# The MainForm has no caption. Put in the application name, which by
				# default (as of this writing) is "Dabo Application"
				frm.Caption = dApp.getAppInfo("appName")

			
	def setMainForm(self, val):
		try:
			self.dApp.MainForm.Destroy()
		except:
			pass
		self.SetTopWindow(val)
		val.Show(self.dApp.showMainFormOnStart)
		

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
		""" Raise the Dabo Activate or Deactivate appropriately."""
		if bool(evt.GetActive()):
			self.raiseEvent(dEvents.Activate, evt)
		else:
			self.raiseEvent(dEvents.Deactivate, evt)
		evt.Skip()
			
	
	def onWinClose(self, evt):
		"""Close the topmost window, if any."""
		if self.ActiveForm:
			self.ActiveForm.close()


	def onFileExit(self, evt):
		"""The MainForm contains the logic in its close methods to 
		cycle through all the forms and determine if they can all be
		safely closed. If it closes them all, it will close itself.
		"""
		frms = self.Application.uiForms
		if self.dApp.MainForm:
			# First close all non-child forms
			orphans = [frm for frm in frms
					if frm.Parent is not self.dApp.MainForm]
			for orphan in orphans:
				orphan.close()
			# Now close the main form. It will close any of its children.
			self.dApp.MainForm.close()
		else:
			while frms:
				frm = frms[0]
				# This will allow forms to veto closing (i.e., user doesn't
				# want to save pending changes). 
				try:
					if frm.close() == False:
						# The form stopped the closing process. The user
						# must deal with this form (save changes, etc.) 
						# before the app can exit.
						frm.bringToFront()
						return False
					else:
						frms.remove(frm)
				except:
					# Object is already deleted
					frms.remove(frm)
		

	def onEditCut(self, evt):
		self.onEditCopy(evt, cut=True)


	def onEditCopy(self, evt, cut=False):
		# If Dabo subclasses define copy() or cut(), it will handle. Otherwise, 
		# some controls (stc...) have Cut(), Copy(), Paste() methods - call those.
		# If neither of the above works, then copy text to the clipboard.
		if self.ActiveForm:
			win = self.ActiveForm.ActiveControl
			if cut:
				handled = (win.cut() is not None)
				if not handled:
					if hasattr(win, "Cut"):
						win.Cut()
						handled = True
			else:
				handled = (win.copy() is not None)
				if not handled:
					if hasattr(win, "Copy"):
						win.Copy()
						handled = True

			if not handled:
				# If it's a text control, get the string that is selected from it.
				try:
					selectedText = win.GetStringSelection()
				except AttributeError:
					selectedText = None
	
				if selectedText:
					self.copyToClipboard(selectedText)
					if cut:
						win.Remove(win.GetSelection()[0], win.GetSelection()[1])
	

	def copyToClipboard(self, txt):
		data = wx.TextDataObject()
		data.SetText(txt)
		cb = wx.TheClipboard
		cb.Open()
		cb.SetData(data)
		cb.Close()


	def onEditPaste(self, evt):
		if self.ActiveForm:
			win = self.ActiveForm.ActiveControl
			handled = (win.paste() is not None)
			if not handled:
				if hasattr(win, "Paste"):
					win.Paste()
					handled = True
			
			if not handled:
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
		dabo.infoLog.write(_("Stub: uiApp.onEditPreferences()"))


	def onEditUndo(self, evt):
		if self.ActiveForm:
			hasCode = self.ActiveForm.onEditUndo(evt)
			if hasCode is False:
				win = self.ActiveForm.ActiveControl
				try:
					win.Undo()
				except AttributeError:
					dabo.errorLog.write(_("No apparent way to undo."))
	

	def onEditRedo(self, evt):
		if self.ActiveForm:
			hasCode = self.ActiveForm.onEditRedo(evt)
			if hasCode is False:
				win = self.ActiveForm.ActiveControl
				try:
					win.Redo()
				except AttributeError:
					dabo.errorLog.write(_("No apparent way to redo."))


	def onEditFindAlone(self, evt):
		self.onEditFind(evt, False)
		
		
	def onEditFind(self, evt, replace=True):
		""" Display a Find dialog.  By default, both 'Find' and 'Find/Replace'
		will be a single dialog. By calling this method with replace=False,
		you will get a Find-only version of the dialog.
		"""
		if self.findDialog is not None:
			self.findDialog.Raise()
			return
		if self.ActiveForm:
			win = self.ActiveForm.ActiveControl
			if win:
				self.findWindow = win           # Save reference for use by self.OnFind()
				try:
					data = self.findReplaceData
				except AttributeError:
					data = None
				if data is None:
					data = wx.FindReplaceData(self._findReplaceFlags)
					data.SetFindString(self._findString)
					data.SetReplaceString(self._replaceString)
					self.findReplaceData = data
				if replace:
					dlg = wx.FindReplaceDialog(win, data, _("Find/Replace"), 
							wx.FR_REPLACEDIALOG)
				else:
					dlg = wx.FindReplaceDialog(win, data, _("Find"))
				
				# Map enter key to find button:
				anId = wx.NewId()
				dlg.SetAcceleratorTable(wx.AcceleratorTable([(wx.ACCEL_NORMAL, wx.WXK_RETURN, anId),]))
				dlg.Bind(wx.EVT_MENU, self.onEnterInFindDialog, id=anId)
	
				dlg.Bind(wx.EVT_FIND, self.OnFind)
				dlg.Bind(wx.EVT_FIND_NEXT, self.OnFind)
				dlg.Bind(wx.EVT_FIND_REPLACE, self.OnFindReplace)
				dlg.Bind(wx.EVT_FIND_REPLACE_ALL, self.OnFindReplaceAll)
				dlg.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)
	
				dlg.Show()
				self.findDialog = dlg
			
	
	def setFindDialogIDs(self):
		"""Since the Find dialog is a wxPython control, we can't determine
		which text control holds the Find value, and which holds the Replace
		value. One thing that is certain, though, on all platforms is that the
		Find textbox is physically above the Replace textbox, so we can use
		its position to determine its function.
		"""
		tbs = [{ctl.GetPosition()[1] : ctl.GetId()} 
				for ctl in self.findDialog.GetChildren()
				if isinstance(ctl, wx.TextCtrl)]
		
		tbs.sort()
		self._findDlgID = tbs[0].values()[0]
		self._replaceDlgID = tbs[1].values()[0]
		
		
	def onEnterInFindDialog(self, evt):
		"""We need to simulate what happens in the Find dialog when
		the user clicks the Find button. This requires that we manually 
		update the find data with the dialog values, and then carry out the
		find as before.
		"""
		frd = self.findReplaceData
		kids = self.findDialog.GetChildren()
		flags = 0
		if self._findDlgID is None:
			self.setFindDialogIDs()
		for kid in kids:
			if isinstance(kid, wx.TextCtrl):
				if kid.GetId() == self._findDlgID:
					frd.SetFindString(kid.GetValue())
				elif kid.GetId() == self._replaceDlgID:
					frd.SetReplaceString(kid.GetValue())
			elif isinstance(kid, wx.CheckBox):
				lbl = kid.GetLabel()
				if lbl == "Whole word":
					if kid.GetValue():
						flags = flags | wx.FR_WHOLEWORD
				elif lbl == "Match case":
					if kid.GetValue():
						flags = flags | wx.FR_MATCHCASE
			elif isinstance(kid, wx.RadioBox):
				# Search direction; either 'Up' or 'Down'
				if kid.GetStringSelection() == "Down":
					flags = flags | wx.FR_DOWN
		frd.SetFlags(flags)
		# We've set all the values; now do the Find.
		self.OnFind(evt)
					

	def onEditFindAgain(self, evt):
		"""Repeat the last search."""
		if self.findReplaceData is None:
			if self._findString:
				data = wx.FindReplaceData(self._findReplaceFlags)
				data.SetFindString(self._findString)
				data.SetReplaceString(self._replaceString)
				self.findReplaceData = data
		try:
			fd = self.findReplaceData
			self.OnFind(fd)
		except AttributeError, e:
			self.onEditFind(None)
			return
			

	def OnFindClose(self, evt):
		""" User clicked the close button, so hide the dialog."""
		frd = self.findReplaceData
		self._findString = frd.GetFindString()
		self._replaceString = frd.GetReplaceString()
		self._findReplaceFlags = frd.GetFlags()
		self.findReplaceData = None
		self.findDialog.Destroy()
		self.findDialog = None
		evt.Skip()

	
	def OnFindReplace(self, evt):
		self.OnFind(evt, action="Replace")
		
		
	def OnFindReplaceAll(self, evt):
		total = 0
		wx.BeginBusyCursor()
		while True:
			ret = self.OnFind(evt, action="Replace")
			if not ret:
				break
			total += 1
		wx.EndBusyCursor()
		# Tell the user what was done
		msg = _("%s replacements were made") % total
		if total == 1:
			msg = _("1 replacement was made")
		dabo.ui.info(msg, title=_("Replacement Complete"))
		
		
	def OnFind(self, evt, action="Find"):
		""" User clicked the 'find' button in the find dialog.
		Run the search on the current control, if it is a text-based control.
		Select the found text in the control.
		"""
		flags = self.findReplaceData.GetFlags()
		findString = self.findReplaceData.GetFindString()
		replaceString = self.findReplaceData.GetReplaceString()
		replaceString2 = self.findReplaceData.GetReplaceString()
		downwardSearch = (flags & wx.FR_DOWN) == wx.FR_DOWN
		wholeWord = (flags & wx.FR_WHOLEWORD) == wx.FR_WHOLEWORD
		matchCase = (flags & wx.FR_MATCHCASE) == wx.FR_MATCHCASE

		ret = None
		win = self.findWindow
		if win:
			if isinstance(win, wx.stc.StyledTextCtrl):
				# STC
				if action == "Replace":
					# Make sure that there is something to replace
					selectPos = win.GetSelection()
					if selectPos[1] - selectPos[0] > 0:	
						# There is something selected to replace
						win.ReplaceSelection(replaceString)
				selectPos = win.GetSelection()
				if downwardSearch:
					start = selectPos[1]
					finish = win.GetTextLength()
					pos = win.FindText(start, finish, findString, flags)
				else:
					start = selectPos[0]
					txt = win.GetText()[:start]
					txRev = utils.reverseText(txt)
					fsRev = utils.reverseText(findString)
					if not matchCase:
						fsRev = fsRev.lower()
						txRev = txRev.lower()
					# Don't have the code to implement Whole Word search yet.
					posRev = txRev.find(fsRev)
					if posRev > -1:
						pos = len(txt) - posRev - len(fsRev)
					else:
						pos = -1
				if pos > -1:
					ret = True
					win.SetSelection(pos, pos+len(findString))
				return ret
				
			else:
				try: 
					value = win.GetValue()
				except AttributeError:
					value = None
				if not isinstance(value, basestring):
					dabo.errorLog.write(_("Active control isn't text-based."))
					return

				if action == "Replace":
					# If we have a selection, replace it.
					selectPos = win.GetSelection()
					if selectPos[1] - selectPos[0] > 0:
						win.ReplaceSelection(replaceString)

				selectPos = win.GetSelection()
				if downwardSearch:
					currentPos = selectPos[1]
					value = win.GetValue()[currentPos:]
				else:
					currentPos = selectPos[0]
					value = win.GetValue()[:currentPos]
					value = utils.reverseText(value)
					findString = utils.reverseText(findString)
				if not matchCase:
					value = value.lower()
					findString = findString.lower()
				# Don't have the code to implement Whole Word search yet.

				result = value.find(findString)
				if result >= 0:
					selStart = currentPos + result
					if not downwardSearch:
						# Need to allow for the reversed text positions
						selStart = len(value) - result - len(findString)
					selEnd = selStart + len(findString)
					win.SetSelection(selStart, selEnd)
					win.ShowPosition(win.GetSelection()[1])
				else:
					dabo.infoLog.write(_("Not found"))
				

	def onShowSizerLines(self, evt):
		"""Toggles whether sizer lines are drawn. This is simply a tool 
		to help people visualize how sizers lay out objects.
		"""
		self._drawSizerOutlines = not self._drawSizerOutlines
		if self.ActiveForm:
			self.ActiveForm.refresh()
		
	
	def getLoginInfo(self, message=None):
		""" Display the login form, and return the user/password 
		as entered by the user.
		"""
		import dabo.ui.dialogs.login as login
		ld = login.Login(self.dApp.MainForm)
		ld.setMessage(message)
		ld.show()
		user, password = ld.user, ld.password
		return user, password
	
	
	def _getActiveForm(self):
		try:
			v = self._activeForm
		except AttributeError:
			v = self._activeForm = None
		return v

	def _setActiveForm(self, frm):
		self._activeForm = frm
		
		
	def _getDrawSizerOutlines(self):
		return self._drawSizerOutlines
	
	def _setDrawSizerOutlines(self, val):
		self._drawSizerOutlines = val
	
	
	def _getNoneDisp(self):
		return self._noneDisp

	def _setNoneDisp(self, val):
		self._noneDisp = val
		

	
	ActiveForm = property(_getActiveForm, None, None, 
			_("Returns the form that currently has focus, or None.  (dForm)" ) )

	DrawSizerOutlines = property(_getDrawSizerOutlines, _setDrawSizerOutlines, None,
			_("Determines if sizer outlines are drawn on the ActiveForm.  (bool)") )
	
	NoneDisplay = property(_getNoneDisp, _setNoneDisp, None, 
			_("Text to display for null (None) values.  (str)") )
	
