# -*- coding: utf-8 -*-
import sys
import os
import time
import logging
import wx
import dabo
import dabo.ui as ui
import dabo.dColors as dColors
import dabo.dEvents as dEvents
import dabo.lib.utils as utils
from dabo.dObject import dObject
from dabo.dLocalize import _, n_
from dabo.lib.utils import cleanMenuCaption
import dabo.dConstants as kons



class SplashScreen(wx.Frame):
	"""
	This is a specialized form that is meant to be used as a startup
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

		self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
		if isinstance(bitmap, basestring):
			# Convert it
			self._bmp = dabo.ui.pathToBmp(bitmap)
		else:
			self._bmp = bitmap

		if maskColor is not None:
			if isinstance(maskColor, basestring):
				maskColor = dColors.colorTupleFromName(maskColor)
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
		self.Show(False)
		try:
			self.fc.Stop()
			self.fc.Destroy()
		except AttributeError:
			pass


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



class uiApp(dObject, wx.App):
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
		dabo.log.info(txt)
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
		if wx.VERSION < (2, 9):  ## Done automatically now
			wx.InitAllImageHandlers()
		# Set up the debug logging
		self.debugWindow = None
		# Set up the object inspector
		self.inspectorWindow = None
		log = logging.getLogger("Debug")
		class DebugLogHandler(logging.Handler):
			def emit(self, record):
				msg = record.getMessage()
				try:
					self.messages.append(msg)
				except AttributeError:
					self.messages = [msg]
				self.updateTarget()
			def updateTarget(self):
				try:
					self.target
					self.messages
				except AttributeError:
					return
				if self.target:
					self.target.Value = "\n".join(self.messages)
		hnd = self._debugHandler = DebugLogHandler()
		fmt = logging.Formatter("%(message)s")
		hnd.setFormatter(fmt)
		log.setLevel(logging.DEBUG)
		log.addHandler(hnd)
		super(uiApp, self).__init__(*args)


	def OnInit(self):
		app = self.dApp
		if not self.checkForUpdates():
			return False
		if app.showSplashScreen:
			splash = app._splashScreen = SplashScreen(app.splashImage, app.splashMaskColor,
					app.splashTimeout)
			splash.CenterOnScreen()
			splash.Show()
			splash.Refresh()
			time.sleep(0.2)
			if wx.PlatformInfo[0] == "__WXMSW__":
				# This seems to help the splash repaint properly on Windows.
				splash.Update()
		if self.callback is not None:
			wx.CallAfter(self.callback)
		del self.callback
		return True


	def checkForUpdates(self, force=False):
		answer = False
		msg = ""
		updAvail = False
		checkResult = self.dApp._checkForUpdates(force=force)
		if isinstance(checkResult, Exception):
			### 2014-10-04, Koczian, using ustr to avoid crash
			check_uni = utils.ustr(checkResult)
			dabo.ui.stop(_("There was an error encountered when checking Web Update: %s") % check_uni,
					_("Web Update Problem"))
			### 2014-10-04, Koczian, end of change
		else:
			# The response will be a boolean for 'first time', along with the dict of updates.
			isFirst, updates = checkResult
			fileUpdates = updates.get("files")
			updAvail = bool(fileUpdates)
			if updAvail:
				notes = ["%s: %s" % tuple(nt) for nt in updates.get("notes", "")]
				noteText = "\n\n".join(notes)
				# The format of each entry is the output from svn, and has the format:
				#			'M      dabo/ui/uiwx/dFormMixin.py'
				# We need to break that up into: (changeType, project, file)
				step1 = [ch.split() for ch in fileUpdates]
				# This is now in the format of [['M', 'dabo/ui/uiwx/dFormMixin.py'], ...]
				# Filter out non-standard projects. Do this first, since some base trunk
				# files can be in the list, and will throw an IndexError.
				step2 = [(ch[0], ch[1]) for ch in step1
						if ch[1].split("/", 1)[0] in ("dabo", "demo", "ide")]
				step2.sort(lambda x,y: cmp(x[1], y[1]))
				# Now split off the project
				step3 = [{"mod":ch[0], "project":ch[1].split("/", 1)[0], "file":ch[1].split("/", 1)[1]} for ch in step2]
				changedFiles = step3
				updAvail = bool(changedFiles)

		if updAvail:
			prop = 0
			xpand = "n"
			msg = _("Updates are available. Do you want to install them now?")
			if isFirst:
				msg = _(
"""This appears to be the first time you are running Dabo. When starting
up, Dabo will check for updates and install them if you wish. Click 'Yes'
to get the latest version of Dabo now, or 'No' if you do not wish to run
these automatic updates.""").replace("\n", " ")
				prop = 2
				xpand = "x"
				# Default to checking once a day.
				self.dApp._setWebUpdate(True, 24*60)

		if msg:
			class WebUpdateConfirmDialog(dabo.ui.dYesNoDialog):
				def initProperties(self):
					self.Caption = "Updates Available"
					self.AutoSize = False
					self.Height = 600
					self.Width = 500
				def addControls(self):
					headline = dabo.ui.dLabel(self, Caption=msg, FontSize=12,
							WordWrap=True, ForeColor="darkblue")
					self.Sizer.appendSpacer(12)
					self.Sizer.append(headline, proportion=prop, layout=xpand, halign="center", border=12)
					self.Sizer.appendSpacer(12)
					edtNotes = dabo.ui.dEditBox(self, Value=noteText)
					self.Sizer.append(edtNotes, 2, "x")
					self.Sizer.appendSpacer(12)
					grd = dabo.ui.dGrid(self, ColumnCount=3)
					col0, col1, col2 = grd.Columns
					col0.DataField = "mod"
					col1.DataField = "project"
					col2.DataField = "file"
					col0.Caption = "Change"
					col1.Caption = "Project"
					col2.Caption = "File"
					col0.Width = 60
					col1.Width = 60
					col2.Width = 300
					grd.DataSet = changedFiles
					self.Sizer.append(grd, 3, "x")
					self.Sizer.appendSpacer(20)

			dlg = WebUpdateConfirmDialog()
			dlg.show()
			answer = dlg.Accepted
			dlg.release()
			if answer:
				self._setUpdatePathLocations()
				try:
					success = self.dApp._updateFramework()
				except IOError, e:
					dabo.log.error(_("Cannot update files; Error: %s") % e)
					dabo.ui.info(_("You do not have permission to update the necessary files. "
							"Please re-run the app with administrator privileges."), title=_("Permission Denied"))
					self.dApp._resetWebUpdateCheck()
					answer = False

				if success is None:
					# Update was not successful
					dabo.ui.info(_("There was a problem getting a response from the Dabo site. "
							"Please check your internet connection and try again later."), title=_("Update Failed"))
					answer = False
					self.dApp._resetWebUpdateCheck()
				elif isinstance(success, basestring):
					# Error message was returned
					dabo.ui.stop(success, title=_("Update Failure"))
				elif success is False:
					# There were no changed files available.
					dabo.ui.info(_("There were no changed files available - your system is up-to-date!"),
							title=_("No Update Needed"))
					answer = False
				else:
					dabo.ui.info(_("Dabo has been updated to the current master version. The app "
							"will now exit. Please re-run the application."), title=_("Success!"))
		return not answer


	def _setUpdatePathLocations(self):
		prf = self.dApp._frameworkPrefs
		loc_demo = prf.getValue("demo_directory")
		loc_ide = prf.getValue("ide_directory")
		if loc_demo and loc_ide:
			return

		class PathDialog(dabo.ui.dOkCancelDialog):
			def initProperties(self):
				self.Caption = _("Dabo Project Locations")
			def addControls(self):
				gsz = dabo.ui.dGridSizer(MaxCols=3)
				lbl = dabo.ui.dLabel(self, Caption=_("IDE Directory:"))
				txt = dabo.ui.dTextBox(self, Enabled=False, Value=loc_ide, RegID="txtIDE", Width=200)
				btn = dabo.ui.dButton(self, Caption="...", OnHit=self.onGetIdeDir)
				gsz.appendItems((lbl, txt, btn), border=5)
				gsz.appendSpacer(10, colSpan=3)
				lbl = dabo.ui.dLabel(self, Caption=_("Demo Directory:"))
				txt = dabo.ui.dTextBox(self, Enabled=False, Value=loc_demo, RegID="txtDemo", Width=200)
				btn = dabo.ui.dButton(self, Caption="...", OnHit=self.onGetDemoDir)
				gsz.appendItems((lbl, txt, btn), border=5)
				gsz.setColExpand(True, 1)
				self.Sizer.append(gsz, halign="center", border=10)
				self.Sizer.appendSpacer(25)
			def onGetIdeDir(self, evt):
				default = loc_ide
				if default is None:
					default = dabo.frameworkPath
				f = dabo.ui.getDirectory(_("Select the location of the IDE folder"), defaultPath=default)
				if f:
					self.txtIDE.Value = f
			def onGetDemoDir(self, evt):
				default = loc_demo
				if default is None:
					default = dabo.frameworkPath
				f = dabo.ui.getDirectory(_("Select the location of the Demo folder"), defaultPath=default)
				if f:
					self.txtDemo.Value = f

		dlg = PathDialog()
		dlg.show()
		if dlg.Accepted:
			prf.ide_directory = dlg.txtIDE.Value
			prf.demo_directory = dlg.txtDemo.Value
		dlg.release()


	def displayInfoMessage(self, msg, defaultShowInFuture=True):
		"""Display a dialog to the user that includes an option to not show the message again."""
		from dabo.ui.dialogs.infoMessage import DlgInfoMessage
		dlg = DlgInfoMessage(Message=msg, DefaultShowInFuture=defaultShowInFuture)
		dlg.show()
		ret = dlg.chkShowInFuture.Value
		dlg.release()
		return ret


	def _handleZoomKeyPress(self, evt):
		## Zoom In / Out / Normal:
		alt = evt.AltDown()
		ctl = evt.ControlDown()
		kcd = evt.GetKeyCode()
		if not self.ActiveForm or alt or not ctl:
			evt.Skip()
			return

		try:
			char = chr(evt.GetKeyCode())
		except (ValueError, OverflowError):
			char = None

		plus = char in ("=", "+") or kcd == wx.WXK_NUMPAD_ADD
		minus = char == "-" or kcd == wx.WXK_NUMPAD_SUBTRACT
		slash = char == "/" or kcd == wx.WXK_NUMPAD_DIVIDE

		if plus:
			self.fontZoomIn()
		elif minus:
			self.fontZoomOut()
		elif slash:
			self.fontZoomNormal()
		else:
			return False
		return True


	# The following three functions handle font zooming
	def fontZoomIn(self):
		af = self.ActiveForm
		if af:
			af.iterateCall("fontZoomIn")
	def fontZoomOut(self):
		af = self.ActiveForm
		if af:
			af.iterateCall("fontZoomOut")
	def fontZoomNormal(self):
		af = self.ActiveForm
		if af:
			af.iterateCall("fontZoomNormal")


	def setup(self):
		wx.SystemOptions.SetOptionInt("mac.textcontrol-use-spell-checker", 1)
		frm = self.dApp.MainForm
		if frm is None:
			if self.dApp.MainFormClass is not None:
				mfc = self.dApp.MainFormClass
				if isinstance(mfc, basestring):
					# It is a path to .cdxml file
					frm = self.dApp.MainForm = dabo.ui.createForm(mfc)
				else:
					frm = self.dApp.MainForm = mfc()


	def setMainForm(self, frm):
		"""Hook called when dApp.MainForm is set."""
		try:
			self.dApp.MainForm.Destroy()
		except AttributeError:
			pass

		self.SetTopWindow(frm)

		if not frm.Caption:
			frm.Caption = self.dApp.getAppInfo("appName")

		# For performance, block all event bindings until after the form is shown.
		eb = frm._EventBindings[:]
		frm._EventBindings = []
		frm.Show(self.dApp.showMainFormOnStart)
		frm._EventBindings = eb


	def start(self):
		# Manually raise Activate, as wx doesn't do that automatically
		try:
			self.dApp.MainForm.raiseEvent(dEvents.Activate)
		except AttributeError:
			self.raiseEvent(dEvents.Activate)
		self.MainLoop()


	def exit(self):
		"""Exit the application event loop."""
		self.Exit()


	def finish(self):
		# Manually raise Deactivate, as wx doesn't do that automatically
		self.raiseEvent(dEvents.Deactivate)


	def _getPlatform(self):
		return self._platform


	def MacOpenFile(self, filename=None, *args, **kwargs):
		self.dApp.onUiOpenFile(filename, *args, **kwargs)


	def MacPrintFile(self, filename=None, *args, **kwargs):
		self.dApp.onUiPrintFile(filename, *args, **kwargs)


	def MacNewFile(self, filename=None, *args, **kwargs):
		self.dApp.onUiNewFile(filename, *args, **kwargs)


	def MacReopenApp(self, filename=None, *args, **kwargs):
		self.dApp.onUiReopenApp(filename, *args, **kwargs)


	def _onWxActivate(self, evt):
		"""Raise the Dabo Activate or Deactivate appropriately."""
		if bool(evt.GetActive()):
			self.dApp.raiseEvent(dEvents.Activate, evt)
		else:
			self.dApp.raiseEvent(dEvents.Deactivate, evt)
		evt.Skip()


	def _onWxKeyChar(self, evt):
		self.dApp.raiseEvent(dEvents.KeyChar, evt)


	def _onWxKeyDown(self, evt):
		if self._handleZoomKeyPress(evt):
			return
		self.dApp.raiseEvent(dEvents.KeyDown, evt)


	def _onWxKeyUp(self, evt):
		self.dApp.raiseEvent(dEvents.KeyUp, evt)


	def onCmdWin(self, evt):
		self.showCommandWindow(self.ActiveForm)


	def onDebugWin(self, evt):
		self.toggleDebugWindow(self.ActiveForm)


	def onObjectInspectorWin(self, evt):
		self.toggleInspectorWindow(self.ActiveForm)


	def showCommandWindow(self, context=None):
		"""Display a command window for debugging."""
		if context is None:
			context = self.ActiveForm
		dlg = dabo.ui.dShellForm(context)
		dlg.show()


	def toggleDebugWindow(self, context=None):
		"""Display a debug output window."""
		if context is None:
			context = self.ActiveForm
		class DebugWindow(dabo.ui.dToolForm):
			def afterInit(self):
				self.Caption = _("Debug Output")
				self.out = dabo.ui.dEditBox(self, ReadOnly=True)
				self.out.bindEvent(dEvents.ContextMenu, self.onContext)
				self.Sizer.append1x(self.out)
				self._txtlen = len(self.out.Value)
				self.tmr = dabo.ui.dTimer(self, Interval=500, OnHit=self.onOutValue)
				self.tmr.start()
			def onContext(self, evt):
				self.out.Value = ""
			def onClose(self, evt):
				self.tmr.stop()
				self.tmr.release()
			def onOutValue(self, evt):
				curr = len(self.out.Value)
				if curr != self._txtlen:
					self._txtlen = curr
					self.out.scrollToEnd()

		if not self.debugWindow:
			self.debugWindow = DebugWindow(context)
			# Set the handler action
			self._debugHandler.target = self.debugWindow.out
		if self.debugWindow.Visible:
			checked = False
			self.debugWindow.hide()
		else:
			checked = True
			self._debugHandler.updateTarget()
			self.debugWindow.show()
		# Having issues with the check mark on the menu being out of sync.
		try:
			mb = context.MenuBar
			mb.debugMenuItem.Checked = checked
			mb.Refresh()
		except AttributeError:
			#Either no such item, or not a valid reference
			pass


	def toggleInspectorWindow(self, context=None):
		"""Display the object inspector window."""
		if context is None:
			context = self.ActiveForm
			if not context:
				context = self.dApp.MainForm
		activeControl = context.ActiveControl
		if not self.inspectorWindow:
#			loc = os.path.dirname(dabo.ui.uiwx.__file__)
#			pth = os.path.join(loc, "inspector.cdxml")
#			self.inspectorWindow = dabo.ui.createForm(pth, parent=context, show=False)
			from object_inspector import InspectorFormClass
			self.inspectorWindow = InspectorFormClass(parent=context)
		insp = self.inspectorWindow
		insp.createObjectTree()
		dabo.ui.callAfter(insp.setSelectedObject, activeControl, silent=True)
		insp.Visible = True
		insp.bringToFront()
		try:
			mb = context.MenuBar
			mb.inspectorMenuItem.Checked = insp.Visible
			mb.Refresh()
		except AttributeError:
			# Either no such item, or not a valid reference
			pass


	def onWinClose(self, evt):
		"""Close the topmost window, if any."""
		if self.ActiveForm:
			self.ActiveForm.close()


	def onFileExit(self, evt):
		"""
		The MainForm contains the logic in its close methods to
		cycle through all the forms and determine if they can all be
		safely closed. If it closes them all, it will close itself.
		"""
		app = self.dApp
		frms = app.uiForms
		if app.MainForm:
			# First close all non-child forms. Some may be 'dead'
			# already, so let's find those first.
			for frm in frms:
				if not frm:
					frms.remove(frm)
			# Now we can work with the rest
			orphans = [frm for frm in frms
					if frm
					and (frm.Parent is not app.MainForm)
					and (frm is not app.MainForm)]
			for orphan in orphans:
				if orphan:
					orphan.close(force=True)
			# Now close the main form. It will close any of its children.
			mf = app.MainForm
			if mf and not mf._finito:
				mf.close()
		else:
			while frms:
				frm = frms[0]
				# This will allow forms to veto closing (i.e., user doesn't
				# want to save pending changes).
				if frm:
					if frm.close(force=True) is False:
						# The form stopped the closing process. The user
						# must deal with this form (save changes, etc.)
						# before the app can exit.
						frm.bringToFront()
						return False
				frms.remove(frm)


	def onEditCut(self, evt):
		self.onEditCopy(evt, cut=True)


	def onEditCopy(self, evt, cut=False):
		# If Dabo subclasses define copy() or cut(), it will handle. Otherwise,
		# some controls (stc...) have Cut(), Copy(), Paste() methods - call those.
		# If neither of the above works, then copy text to the clipboard.
		if self.ActiveForm:
			win = self.ActiveForm.FindFocus()
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


	@classmethod
	def copyToClipboard(cls, val):
		txtData = wx.TextDataObject()
		bmpData = wx.BitmapDataObject()
		ok = False
		for (data, setMethod) in ((txtData, txtData.SetText), (bmpData, bmpData.SetBitmap)):
			try:
				setMethod(val)
				ok = True
				break
			except TypeError:
				continue
		if ok:
			cb = wx.TheClipboard
			cb.Open()
			cb.SetData(data)
			cb.Close()
		else:
			raise TypeError(_("Only text and bitmaps are supported."))


	def onEditPaste(self, evt):
		if self.ActiveForm:
			win = self.ActiveForm.FindFocus()
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
						try:
							win.Replace(selection[0], selection[1], data.GetText())
						except (AttributeError, IndexError, KeyError):
							# Could have been a control with a GetSelection() method, such
							# as a dPageFrame, and the selection doesn't refer to selected text.
							pass


	def onEditSelectAll(self, evt):
		af = self.ActiveForm
		if af:
			ac = af.ActiveControl
			if ac:
				try:
					ac.SelectAll()
				except AttributeError:
					try:
						ac.SetSelection(-1, -1)
					except (TypeError, AttributeError):
						try:
							af.selectAll()
						except AttributeError:
							pass


	def _getContainingGrid(self, win):
		"""
		Returns the grid that contains the specified window, or None
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
		"""
		If a preference handler is defined for the form, use that. Otherwise,
		use the generic preference dialog.
		"""
		from dabo.ui.dialogs import PreferenceDialog

		af = self.ActiveForm
		try:
			af.onEditPreferences(evt)
		except AttributeError:
			if self.PreferenceDialogClass:
				dlgPref = getattr(af, "_prefDialog", None)
				if dlgPref is None:
					dlgPref = self.PreferenceDialogClass(af)
					if af:
						af._prefDialog = dlgPref
				if isinstance(dlgPref, PreferenceDialog):
					if af:
						af.fillPreferenceDialog(dlgPref)
					# Turn off AutoPersist for any of the dialog's preferenceKeys. Track those that
					# previously had it on, so we know which ones to revert afterwards.
					keysToRevert = [pk for pk in dlgPref.preferenceKeys
							if pk.AutoPersist]
					for k in keysToRevert:
						k.AutoPersist = False

				dlgPref.show()

				if isinstance(dlgPref, PreferenceDialog):
					if dlgPref.Accepted:
						if hasattr(dlgPref, "_onAcceptPref"):
							dlgPref._onAcceptPref()
						for k in dlgPref.preferenceKeys:
							k.persist()
							if k in keysToRevert:
								k.AutoPersist = True
					else:
						if hasattr(dlgPref, "_onCancelPref"):
							dlgPref._onCancelPref()
						for k in dlgPref.preferenceKeys:
							k.cancel()
							if k in keysToRevert:
								k.AutoPersist = True
				try:
					if self.dApp.ReleasePreferenceDialog and dlgPref.Modal:
						dlgPref.release()
						del (af._prefDialog)
				except dabo.ui.deadObjectException:
					pass
			else:
				dabo.log.info(_("Stub: dApp.onEditPreferences()"))


	def onEditUndo(self, evt):
		if self.ActiveForm:
			hasCode = self.ActiveForm.onEditUndo(evt)
			if hasCode is False:
				win = self.ActiveForm.ActiveControl
				try:
					win.Undo()
				except AttributeError:
					dabo.log.error(_("No apparent way to undo."))


	def onEditRedo(self, evt):
		if self.ActiveForm:
			hasCode = self.ActiveForm.onEditRedo(evt)
			if hasCode is False:
				win = self.ActiveForm.ActiveControl
				try:
					win.Redo()
				except AttributeError:
					dabo.log.error(_("No apparent way to redo."))


	def onEditFindAlone(self, evt):
		self.onEditFind(evt, False)


	def onEditFind(self, evt, replace=True):
		"""
		Display a Find dialog.	By default, both 'Find' and 'Find/Replace'
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
		"""
		Since the Find dialog is a wxPython control, we can't determine
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
		try:
			self._replaceDlgID = tbs[1].values()[0]
		except IndexError:
			# Not a Replace dialog
			self._replaceDlgID = None


	def onEnterInFindDialog(self, evt):
		"""
		We need to simulate what happens in the Find dialog when
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
		except AttributeError:
			self.onEditFind(None)
			return


	def OnFindClose(self, evt):
		"""User clicked the close button, so hide the dialog."""
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
		try:
			lock = self.findWindow.getDisplayLocker()
		except AttributeError:
			lock = None
		# Get the first find
		ret = self.OnFind(evt, action="Find")
		while ret:
			ret = self.OnFind(evt, action="Replace")
			if not ret:
				break
			total += 1
			ret = self.OnFind(evt, action="Find")
		wx.EndBusyCursor()
		del lock
		# Tell the user what was done
		if total == 1:
			msg = _("1 replacement was made")
		else:
			msg = _("%s replacements were made") % total
		dabo.ui.info(msg, title=_("Replacement Complete"))


	def OnFind(self, evt, action="Find"):
		"""
		User clicked the 'find' button in the find dialog.
		Run the search on the current control, if it is a text-based control.
		Select the found text in the control.
		"""
		flags = self.findReplaceData.GetFlags()
		findString = self.findReplaceData.GetFindString()
		replaceString = self.findReplaceData.GetReplaceString()
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
						return True
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

			elif isinstance(win, dabo.ui.dGrid):
				return win.findReplace(action, findString, replaceString, downwardSearch,
						wholeWord, matchCase)
			else:
				# Regular text control
				try:
					value = win.GetValue()
				except AttributeError:
					value = None
				if not isinstance(value, basestring):
					dabo.log.error(_("Active control isn't text-based."))
					return

				if action == "Replace":
					# If we have a selection, replace it.
					selectPos = win.GetSelection()
					if selectPos[1] - selectPos[0] > 0:
						win.Replace(selectPos[0], selectPos[1], replaceString)
						ret = True

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
					ret = True
					selStart = currentPos + result
					if not downwardSearch:
						# Need to allow for the reversed text positions
						selStart = len(value) - result - len(findString)
					selEnd = selStart + len(findString)
					win.SetSelection(selStart, selEnd)
					win.ShowPosition(win.GetSelection()[1])
				else:
					dabo.log.info(_("Not found"))
				return ret


	def addToMRU(self, menuOrCaption, prompt, bindfunc=None):
		"""
		Adds the specified menu to the top of the list of
		MRU prompts for that menu.
		"""
		if isinstance(menuOrCaption, basestring):
			# They passed the menu caption directly
			cap = menuOrCaption
		else:
			cap = menuOrCaption.Caption
		cleanCap = cleanMenuCaption(cap)
		mn = self._mruMenuPrompts.get(cleanCap, [])
		if prompt in mn:
			mn.remove(prompt)
		mn.insert(0, prompt)
		self._mruMenuPrompts[cleanCap] = mn[:self._mruMaxItems]
		mf = self._mruMenuFuncs.get(cleanCap, {})
		mf[prompt] = bindfunc
		self._mruMenuFuncs[cleanCap] = mf


	def onMenuOpenMRU(self, menu):
		"""
		Make sure that the MRU items are there and are in the
		correct order.
		"""
		cap = menu.Caption
		cleanCap = cleanMenuCaption(cap)
		topLevel = isinstance(menu.Parent, dabo.ui.dMenuBar)
		mnPrm = self._mruMenuPrompts.get(cleanCap, [])
		if not mnPrm:
			return
		if topLevel and (menu._mruSeparator is None):
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
					menu.remove(itm)
				except (IndexError, ValueError), e:
					pass
			# Add them all back
			lnks = {}
			fncs = self._mruMenuFuncs.get(cleanCap, {})
			for pos, txt in enumerate(mnPrm):
				itm = menu.append(tmplt % (pos+1, txt), OnHit=fncs.get(txt, None))
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
		"""
		Toggles whether sizer lines are drawn. This is simply a tool
		to help people visualize how sizers lay out objects.
		"""
		self._drawSizerOutlines = not self._drawSizerOutlines
		if self.ActiveForm:
			self.ActiveForm.refresh()


	def onReloadForm(self, evt):
		"""Re-creates the active form with a newer class definition."""
		frm = evt.EventObject
		if not frm:
			frm = self.ActiveForm
		try:
			pth = frm._sourceFilePath
		except AttributeError:
			dabo.log.error(_("Only .cdxml forms can be re-loaded"))
			return
		self.dApp.resyncFiles()
		frm.lockDisplay()
		# Store the old form's bizobj dict
		bizDict = frm.bizobjs
		bizPrimary = frm.PrimaryBizobj
		newForm = dabo.ui.createForm(pth)
		newForm.Position = frm.Position
		newForm.Size = frm.Size
		newForm.bizobjs = bizDict
		newForm.PrimaryBizobj = bizPrimary
		dabo.ui.callAfter(frm.release)
		newForm.update()
		newForm.show()


	def _getActiveForm(self):
		af = getattr(self, "_activeForm", None)
		if af is None:
			af = wx.GetActiveWindow()
		if isinstance(af, wx.MDIParentFrame):
			afc = af.GetActiveChild()
			if afc:
				return afc
		return af

	def _setActiveForm(self, frm):
		self._activeForm = frm


	def _getDrawSizerOutlines(self):
		return self._drawSizerOutlines

	def _setDrawSizerOutlines(self, val):
		self._drawSizerOutlines = val


	def _getPreferenceDialogClass(self):
		return self.dApp.PreferenceDialogClass

	def _setPreferenceDialogClass(self, val):
		self.dApp.PreferenceDialogClass = val


	ActiveForm = property(_getActiveForm, _setActiveForm, None,
			_("Returns the form that currently has focus, or None.	(dForm)" ) )

	DrawSizerOutlines = property(_getDrawSizerOutlines, _setDrawSizerOutlines, None,
			_("Determines if sizer outlines are drawn on the ActiveForm.  (bool)") )

	PreferenceDialogClass = property(_getPreferenceDialogClass, _setPreferenceDialogClass, None,
			_("Class to instantiate for the application's preference editing  (dForm/dDialog)"))

