import sys, os, wx
import dabo
import dabo.ui as ui
import dabo.dEvents as dEvents
import dabo.lib.utils as utils
from dabo.dObject import dObject
from dabo.dLocalize import _, n_
import dabo.dConstants as kons


class SplashScreen(wx.Frame):
	"""This is a specialized form that is meant to be used as a startup
	splash screen. It takes an image file, bitmap, icon, etc., which is used
	to size and shape the form. If you specify a mask color, that color 
	will be masked in the bitmap to appear transparent, and will affect the 
	shape of the form. 
	
	You may also pass a 'timeout' value; this is in milliseconds, and determines
	how long until the splash screen automatically closes. If you pass zero
	(or don't pass anything), the screen will remain visible until the user 
	clicks on it.
	
	Many thanks to Andrea Gavana, whose 'AdvancedSplash' class was a
	huge inspiration (and source of code!) for this Dabo class. I also borrowed
	some ideas/code from the wxPython demo by Robin Dunn.
	"""
	def __init__(self, bitmap=None, maskColor=None, timeout=0):
		style = wx.FRAME_NO_TASKBAR | wx.FRAME_SHAPED | wx.STAY_ON_TOP
		wx.Frame.__init__(self, None, -1, style=style)
		
		if isinstance(bitmap, basestring):
			# Convert it
			self._bmp = dabo.ui.pathToBmp(bitmap)
		else:
			self._bmp = bitmap
		
		if maskColor is not None:
			if isinstance(maskColor, basestring):
				maskColor = dabo.dColors.colorTupleFromName(maskColor)
			self._bmp.SetMask(wx.Mask(self._bmp, maskColor))
			
		if wx.Platform == "__WXGTK__":
			self.Bind(wx.EVT_WINDOW_CREATE, self.setSizeAndShape)
		else:
			self.setSizeAndShape()
		
		self.Bind(wx.EVT_MOUSE_EVENTS, self._onMouseEvents)
		self.Bind(wx.EVT_PAINT, self._onPaint)
		if timeout > 0:
			self.fc = wx.FutureCall(timeout, self._onTimer)
		

	def setSizeAndShape(self, evt=None):
		w = self._bmp.GetWidth()
		h = self._bmp.GetHeight()
		self.SetSize((w, h))
		reg = wx.RegionFromBitmap(self._bmp)
		self.SetShape(reg)
		self.CenterOnScreen()
		if evt is not None:
			evt.Skip()
		

	def _onMouseEvents(self, evt):
		if evt.LeftDown() or evt.RightDown():
			self._disappear()
		
		
	def _onTimer(self):
		self._disappear()

	
	def _disappear(self):
		try:
			self.fc.Stop()
		except:
			pass
		self.Close()


	def _onPaint(self, evt):
		dc = wx.BufferedPaintDC(self, self._bmp)
		# I plan on adding support for a text string to be 
		# displayed. This is Andrea's code, which I may use as 
		# the basis for this.
# 		textcolour = self.GetTextColour()
# 		textfont = self.GetTextFont()
# 		textpos = self.GetTextPosition()
# 		text = self.GetText()
# 		dc.SetFont(textfont[0])
# 		dc.SetTextForeground(textcolour)
# 		dc.DrawText(text, textpos[0], textpos[1])
		# Seems like this only helps on OS X.
		if wx.Platform == "__WXMAC__":
			wx.SafeYield(self, True)
		evt.Skip()



class uiApp(wx.App, dObject):
	def __init__(self, app, callback=None, *args):
		self.dApp = app
		self.callback = callback
		wx.App.__init__(self, 0, *args)
		dObject.__init__(self)
		
		self.Name = _("uiApp")
		# wx has properties for appName and vendorName, so Dabo should update
		# these. Among other possible uses, I know that on Win32 wx will use
		# these for determining the registry key structure.
		self.SetAppName(self.dApp.getAppInfo("appName"))
		self.SetClassName(self.dApp.getAppInfo("appName"))
		self.SetVendorName(self.dApp.getAppInfo("vendorName"))
		
		# Set the platform info.
		self.charset = "unicode"
		if not self.charset in wx.PlatformInfo:
			self.charset = "ascii"
		txt = "wxPython Version: %s %s (%s)" % (wx.VERSION_STRING, 
				wx.PlatformInfo[1], self.charset)
		if wx.PlatformInfo[0] == "__WXGTK__":
			self._platform = _("GTK")
			txt += " (%s)" % wx.PlatformInfo[3]
		elif wx.PlatformInfo[0] == "__WXMAC__":
			self._platform = _("Mac")
		elif wx.PlatformInfo[0] == "__WXMSW__":
			self._platform = _("Win")
		dabo.infoLog.write(txt)
		self.Bind(wx.EVT_ACTIVATE_APP, self._onWxActivate)
		self.Bind(wx.EVT_KEY_DOWN, self._onWxKeyDown)
		self.Bind(wx.EVT_KEY_UP, self._onWxKeyUp)
		self.Bind(wx.EVT_CHAR, self._onWxKeyChar)

		self._drawSizerOutlines = False
		# Various attributes used by the FindReplace dialog
		self._findString = ""
		self._replaceString = ""
		self._findReplaceFlags = wx.FR_DOWN
		self._findDlgID = self._replaceDlgID = None
		self.findReplaceData = None
		self.findDialog = None
		# Atts used to manage MRU (Most Recently Used) menus.
		self._mruMenuPrompts = {}
		self._mruMenuFuncs = {}
		self._mruMenuLinks = {}
		self._mruMaxItems = 12
		wx.InitAllImageHandlers()
		
		
	def OnInit(self):
		app = self.dApp
		if app.showSplashScreen:
			splash = SplashScreen(app.splashImage, app.splashMaskColor, 
					app.splashTimeout)
			splash.CenterOnScreen()
			splash.Show()
			if wx.PlatformInfo[0] == "__WXMSW__":
				# This seems to help the splash repaint properly on Windows.
				splash.Update()
		if self.callback is not None:
			wx.CallAfter(self.callback)
		del self.callback
		return True


	def setup(self):
		frm = self.dApp.MainForm
		if frm is None:
			if self.dApp.MainFormClass is not None:
				mfc = self.dApp.MainFormClass
				if isinstance(mfc, basestring):
					# It is a path to .cdxml file
					frm = self.dApp.MainForm = dabo.ui.createForm(mfc)
				else:
					frm = self.dApp.MainForm = mfc()
		if frm is not None:
			if len(frm.Caption) == 0:
				# The MainForm has no caption. Put in the application name, which by
				# default (as of this writing) is "Dabo Application"
				frm.Caption = self.dApp.getAppInfo("appName")

			
	def setMainForm(self, val):
		try:
			self.dApp.MainForm.Destroy()
		except:
			pass
		self.SetTopWindow(val)
		# For performance, block all event bindings until after the form is shown.
		eb = val._EventBindings[:]
		val._EventBindings = []
		val.Show(self.dApp.showMainFormOnStart)
		val._EventBindings = eb


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
			self.dApp.raiseEvent(dEvents.Activate, evt)
		else:
			self.dApp.raiseEvent(dEvents.Deactivate, evt)
		evt.Skip()
	
	def _onWxKeyChar(self, evt):
		self.dApp.raiseEvent(dEvents.KeyChar, evt)
		evt.Skip()
			
	def _onWxKeyDown(self, evt):
		self.dApp.raiseEvent(dEvents.KeyDown, evt)
		evt.Skip()
			
	def _onWxKeyUp(self, evt):
		self.dApp.raiseEvent(dEvents.KeyUp, evt)
		evt.Skip()
			

	def onCmdWin(self, evt):
		self.showCommandWindow()


	def showCommandWindow(self, context=None):
		"""Display a command window for debugging."""
		if context is None:
			context = self.ActiveForm
		dlg = dabo.ui.dShell.dShell(context)
		dlg.Show()

	
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
			# First close all non-child forms. Some may be 'dead'
			# already, so let's find those first.
			for frm in frms:
				try:
					junk = frm.Visible
				except dabo.ui.deadObjectException:
					frms.remove(frm)
			# Now we can work with the rest
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
			handled = False
			if cut:
				if hasattr(win, "cut"):
					handled = (win.cut() is not None)
				if not handled:
					# See if the control is inside a grid
					grd = self._getContainingGrid(win)
					if grd and hasattr(grd, "cut"):
						handled = (grd.cut() is not None)
				if not handled:
					if hasattr(win, "Cut"):
						win.Cut()
						handled = True
			else:
				if hasattr(win, "copy"):
					handled = (win.copy() is not None)
				if not handled:
					# See if the control is inside a grid
					grd = self._getContainingGrid(win)
					if grd and hasattr(grd, "copy"):
						handled = (grd.copy() is not None)
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
			handled = False
			if hasattr(win, "paste"):
				handled = (win.paste() is not None)
			if not handled:
				# See if the control is inside a grid
				grd = self._getContainingGrid(win)
				if grd and hasattr(grd, "paste"):
					handled = (grd.paste() is not None)
			if not handled:
				# See if it has a wx-level Paste() method
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
		

	def onEditSelectAll(self, evt):
		if self.ActiveForm:
			win = self.ActiveForm.ActiveControl
			if win:
				try:
					win.SetSelection(-1, -1)
				except: pass			

			
	def _getContainingGrid(self, win):
		"""Returns the grid that contains the specified window, or None
		if the window is not contained in a grid.
		"""
		ret = None
		while win:
			if isinstance(win, wx.grid.Grid):
				ret = win
				break
			try:
				win = win.GetParent()
			except AttributeError:
				win = None
		return ret
		
		
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
		""" Display a Find dialog.	By default, both 'Find' and 'Find/Replace'
		will be a single dialog. By calling this method with replace=False,
		you will get a Find-only version of the dialog.
		"""
		if self.findDialog is not None:
			self.findDialog.Raise()
			return
		if self.ActiveForm:
			win = self.ActiveForm.ActiveControl
			if win:
				self.findWindow = win			# Save reference for use by self.OnFind()
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
				

	def addToMRU(self, menu, prompt, bindfunc=None):
		"""Adds the specified menu to the top of the list of 
		MRU prompts for that menu.
		"""
		if isinstance(menu, basestring):
			# They passed the menu caption directly
			cap = menu
		else:
			cap = menu.Caption
		mn = self._mruMenuPrompts.get(cap, [])
		if prompt in mn:
			mn.remove(prompt)
		mn.insert(0, prompt)
		self._mruMenuPrompts[cap] = mn[:self._mruMaxItems]
		mf = self._mruMenuFuncs.get(cap, {})
		mf[prompt] = bindfunc
		self._mruMenuFuncs[cap] = mf

	
	def onMenuOpenMRU(self, menu):
		"""Make sure that the MRU items are there and are in the 
		correct order.
		"""
		cap = menu.Caption
		mnPrm = self._mruMenuPrompts.get(cap, [])
		if not mnPrm:
			return
		if menu._mruSeparator is None:
			menu._mruSeparator = menu.appendSeparator()
		tmplt = "&%s %s"
		promptList = [tmplt % (pos+1, txt) 
				for pos, txt in enumerate(mnPrm)]
		idx = -1
		ok = True
		for prm in promptList:
			try:
				newIdx = menu.getItemIndex(prm)
				if newIdx is None or (newIdx < idx):
					ok = False
					break
				else:
					idx = newIdx
			except IndexError:
				# The menu items aren't in this menu
				ok = False
				break
		if not ok:
			# Remove all the items
			lnks = self._mruMenuLinks.get(menu, {})
			kids = menu.Children
			for itm in lnks.values()[::-1]:
				if itm not in kids:
					continue
				try:
					pos = kids.index(itm)
					menu.remove(pos, True)
				except IndexError, ValueErrror:
					pass
			# Add them all back
			lnks = {}
			fncs = self._mruMenuFuncs.get(cap, {})
			for pos, txt in enumerate(mnPrm):
				itm = menu.append(tmplt % (pos+1, txt), bindfunc=fncs.get(txt, None))
				lnks[itm.GetId()] = itm
			self._mruMenuLinks[menu] = lnks
	
	
	def getMRUListForMenu(self, menu):
		"""Gets the current list of MRU entries for the given menu."""
		if isinstance(menu, basestring):
			# They passed the menu caption directly
			cap = menu
		else:
			cap = menu.Caption
		return self._mruMenuPrompts.get(cap, [])
		
	
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
		if self._platform == "Win":
			v = wx.GetActiveWindow()
		else:
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
	
	
	ActiveForm = property(_getActiveForm, _setActiveForm, None, 
			_("Returns the form that currently has focus, or None.	(dForm)" ) )

	DrawSizerOutlines = property(_getDrawSizerOutlines, _setDrawSizerOutlines, None,
			_("Determines if sizer outlines are drawn on the ActiveForm.  (bool)") )
	
