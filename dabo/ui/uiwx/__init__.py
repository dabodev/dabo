import sys
import os
import re
import glob
import urllib
import datetime
import time
import cStringIO
from dabo.dLocalize import _

######################################################
# Very first thing: check for proper wxPython build:
_failedLibs = []
# note: may need wx.animate as well
for lib in ("wx", "wx.stc", "wx.lib.foldpanelbar", "wx.gizmos", 
		"wx.lib.calendar", "wx.lib.masked", "wx.lib.buttons"):
	try:
		__import__(lib)
	except ImportError:
		_failedLibs.append(lib)

if len(_failedLibs) > 0:
	msg = """
Your wxPython installation was not built correctly. Please make sure that
the following required libraries have been built:

	%s
	""" % "\n\t".join(_failedLibs)
	
	sys.exit(msg)
del(_failedLibs)
#######################################################
import wx
from wx import ImageFromStream, BitmapFromImage
import dabo.ui
import dabo.dConstants as kons
from uiApp import uiApp

uiType = {"shortName": "wx", "moduleName": "uiwx", "longName": "wxPython"}
uiType["version"] = wx.VERSION_STRING
_platform = wx.PlatformInfo[1]
if wx.PlatformInfo[0] == "__WXGTK__":
	_platform += " (%s)" % wx.PlatformInfo[3]
uiType["platform"] = _platform

# Add these to the dabo.ui namespace
deadObjectException = wx._core.PyDeadObjectError
deadObject = wx._core._wxPyDeadObject
assertionException = wx._core.PyAssertionError
nativeScrollBar = wx.ScrollBar

# Import dPemMixin first, and then manually put into dabo.ui module. This is
# because dControlMixinBase, which is in dabo.ui, descends from dPemMixin, which 
# is in dabo.ui.uiwx. Must also do the same with dControlMixin, as dDataControlMixinBase
# descends from it.
from dPemMixin import dPemMixin
dabo.ui.dPemMixin = dPemMixin
from dControlMixin import dControlMixin
dabo.ui.dControlMixin = dControlMixin
from dDataControlMixin import dDataControlMixin
dabo.ui.dDataControlMixin = dDataControlMixin
from dFormMixin import dFormMixin
dabo.ui.dFormMixin = dFormMixin
from dSizerMixin import dSizerMixin
dabo.ui.dSizerMixin = dSizerMixin

# Import into public namespace:
from dBox import dBox
from dBitmap import dBitmap
from dBitmapButton import dBitmapButton
from dButton import dButton
from dCalendar import dCalendar
from dCalendar import dExtendedCalendar
from dCheckBox import dCheckBox
from dCheckListBox import dCheckListBox
from dColorDialog import dColorDialog
from dComboBox import dComboBox
from dDateTextBox import dDateTextBox
from dDropdownList import dDropdownList
from dDialog import dDialog
from dDialog import dOkCancelDialog
from dEditableList import dEditableList
from dEditBox import dEditBox
from dEditor import dEditor
from dFileDialog import dFileDialog
from dFileDialog import dFolderDialog
from dFileDialog import dSaveDialog
from dFoldPanelBar import dFoldPanelBar
from dFoldPanelBar import dFoldPanel
from dFont import dFont
from dFontDialog import dFontDialog
from dForm import dForm
from dForm import dToolForm
from dForm import dBorderlessForm
from dFormMain import dFormMain
from dGauge import dGauge
from dGrid import dGrid
from dGrid import dColumn
from dGridSizer import dGridSizer
from dHtmlBox import dHtmlBox
from dHyperLink import dHyperLink
import dIcons
from dImage import dImage
import dKeys
from dLabel import dLabel
from dLine import dLine
from dListBox import dListBox
from dListControl import dListControl
from dBaseMenuBar import dBaseMenuBar
from dMenuBar import dMenuBar
from dMenu import dMenu
from dMenuItem import *
import dMessageBox
from dRadioGroup import dRadioGroup
from dRadioList import dRadioList
from dPanel import dPanel
from dPanel import dScrollPanel
from dPageFrame import dPageFrame
from dPageFrame import dPageList
from dPageFrame import dPageSelect
from dPageFrameNoTabs import dPageFrameNoTabs
from dPage import dPage
from dSizer import dSizer
from dBorderSizer import dBorderSizer
from dSlider import dSlider
from dSpinner import dSpinner
from dSplitForm import dSplitForm
from dSplitter import dSplitter
from dStatusBar import dStatusBar
from dTextBox import dTextBox
from dTimer import dTimer
from dToolBar import dToolBar
from dToolBar import dToolBarItem
from dToggleButton import dToggleButton
from dTreeView import dTreeView
from dLed import dLed
import dUICursors as dUICursors
import dShell

try:
	from dGlWindow import dGlWindow
except ImportError:
	dabo.infoLog.write(_("PyOpenGL not present, so dGlWindow is not loaded."))


artConstants = {}
for item in dir(wx):
	if item[:4] == "ART_":
		daboConstant = item[4:].lower().replace("_", "")
		artConstants[daboConstant] = getattr(wx, item)

# artConstant aliases:
artConstants["cd"] = artConstants.get("cdrom")
artConstants["commondialog"] = artConstants.get("cmndialog")
artConstants["configure"] = artConstants.get("helpsettings")
artConstants["dialog"] = artConstants.get("cmndialog")
artConstants["cross"] = artConstants.get("crossmark")
artConstants["exe"] = artConstants.get("executablefile")
artConstants["exefile"] = artConstants.get("executablefile")
artConstants["exit"] = artConstants.get("quit")
artConstants["open"] = artConstants.get("fileopen")
artConstants["save"] = artConstants.get("filesave")
artConstants["saveas"] = artConstants.get("filesaveas")
artConstants["findreplace"] = artConstants.get("findandreplace")
artConstants["frame"] = artConstants.get("frameicon")
artConstants["back"] = artConstants.get("goback")
artConstants["directoryup"] = artConstants.get("godirup")
artConstants["down"] = artConstants.get("godown")
artConstants["forward"] = artConstants.get("goforward")
artConstants["home"] = artConstants.get("gohome")
artConstants["parent"] = artConstants.get("gotoparent")
artConstants["up"] = artConstants.get("goup")
artConstants["hd"] = artConstants.get("harddisk")
artConstants["info"] = artConstants.get("information")
artConstants["file"] = artConstants.get("normalfile")


def getUiApp(app, callback=None):
	"""This returns an instance of uiApp. If one is already running, that
	instance is returned. Otherwise, a new instance is created.
	"""
	ret = wx.GetApp()
	if ret is None:
		ret = uiApp(app, callback)
	else:
		# existing app; fire the callback, if any
		if callback is not None:
			wx.CallAfter(callback)
	return ret
	

def callAfter(fnc, *args, **kwargs):
	"""There are times when this functionality is needed when creating UI
	code. This function simply wraps the wx.CallAfter function so that 
	developers do not need to use wx code in their apps.
	"""
	wx.CallAfter(fnc, *args, **kwargs)
	

_callAfterIntervalReferences = {}
def callAfterInterval(interval, func, *args, **kwargs):
	"""Call the given function after <interval> milliseconds have elapsed.

	If the function is called again before the interval has elapsed, the original
	timer is destroyed and a new one instantiated. IOW, you can call this in a
	tight loop, and only the last call will get executed. Useful when you want to
	refresh something because you changed it, but the frequency of changes can be
	high.
	"""
	if isinstance(func, int):
		# Arguments are in the old order
		interval, func = func, interval
	futureCall = _callAfterIntervalReferences.get((func, args))
	if futureCall:
		futureCall.Stop()
	_callAfterIntervalReferences[(func, args)] = wx.FutureCall(interval, func, *args, **kwargs)


def setAfter(obj, prop, val):
	"""Like callAfter(), but allows you to set a property instead of calling
	a function.
	"""
	try:
		fnc = eval("obj.__class__.%s.fset" % prop)
		wx.CallAfter(fnc, obj, val)
	except StandardError, e:
		dabo.errorLog.write(_("setAfter() failed to set property '%s' to value '%s': %s.")
				% (prop, val, e))
	

def setAfterInterval(interval, obj, prop, val):
	"""Like callAfterInterval(), but allows you to set a property instead 
	of calling a function.
	"""
	try:
		fnc = eval("obj.__class__.%s.fset" % prop)
		callAfterInterval(interval, fnc, obj, val)
	except StandardError, e:
		dabo.errorLog.write(_("setAfterInterval() failed to set property '%s' to value '%s': %s.")
				% (prop, val, e))


def callEvery(interval, func, *args, **kwargs):
	"""Creates and returns a timer object that fires the specified function 
	at the specified interval. Interval is given in milliseconds. It will pass along
	any additional arguments to the function when it is called.
	"""
	def _onHit(evt):
		func(*args, **kwargs)
	ret = dTimer(Interval=interval)
	ret.bindEvent(dabo.dEvents.Hit, _onHit)
	ret.start()
	return ret


def yieldUI(*args, **kwargs):
	"""Yield to other apps/messages."""
	wx.Yield(*args, **kwargs)	


def beep():
	wx.Bell()
	

def busyInfo(msg="Please wait...", *args, **kwargs):
	"""Display a message that the system is busy.

	Assign the return value to a local object, and the message will stay until the 
	object is explicitly unbound. For example:

	bi = dabo.ui.busyInfo("Please wait while I count to 10000...")
	for i in range(10000):
		pass
	bi = None
	"""
	bi = wx.BusyInfo(msg, *args, **kwargs)
	wx.Yield()
	return bi


def continueEvent(evt):
	try:
		evt.Skip()
	except AttributeError, e:
		# Event could be a Dabo event, not a wx event
		if isinstance(evt, dabo.dEvents.Event):
			pass
		else:
			dabo.errorLog.write("Incorrect event class (%s) passed to continueEvent. Error: %s"
					% (str(evt), str(e)))
	
	
def discontinueEvent(evt):
	try:
		evt.Skip(False)
	except AttributeError, e:
		# Event could be a Dabo event, not a wx event
		if isinstance(evt, dabo.dEvents.Event):
			pass
		else:
			dabo.errorLog.write("Incorrect event class (%s) passed to continueEvent. Error: %s"
					% (str(evt), str(e)))
	
	
def getEventData(wxEvt):
	ed = {}
	eventType = wxEvt.GetEventType()
	
	if isinstance(wxEvt, (wx.KeyEvent, wx.MouseEvent, wx.TreeEvent,
			wx.CommandEvent, wx.CloseEvent, wx.grid.GridEvent,
			wx.grid.GridSizeEvent, wx.SplitterEvent) ):
		
		if dabo.allNativeEventInfo:
			# Cycle through all the attributes of the wx events, and evaluate them
			# for insertion into the dEvent.EventData dict.
			d = dir(wxEvt)
			try:
				upPems = [p for p in d if p[0].isupper()]
				for pem in upPems:
					if pem in ("Skip", "Clone", "Destroy", "Button", "ButtonIsDown", 
							"GetLogicalPosition", "ResumePropagation", "SetEventObject", 
							"SetEventType", "SetId", "SetExtraLong", "SetInt", "SetString", 
							"SetTimestamp", "StopPropagation"):
						continue
					try:
						pemName = pem[0].lower() + pem[1:]
						ed[pemName] = eval("wxEvt.%s()" % pem)
					except:
						pass
			except:
				pass
	
	if isinstance(wxEvt, (wx.SplitterEvent,) ):
		try:
			ed["mousePosition"] = (wxEvt.GetX(), wxEvt.GetY())
		except:
			ed["mousePosition"] = wx.GetMousePosition()

	if isinstance(wxEvt, (wx.KeyEvent, wx.MouseEvent) ):
		ed["mousePosition"] = wxEvt.GetPositionTuple()
		ed["altDown"] = wxEvt.AltDown()
		ed["commandDown"] = wxEvt.CmdDown()
		ed["controlDown"] = wxEvt.ControlDown()
		ed["metaDown"] = wxEvt.MetaDown()
		ed["shiftDown"] = wxEvt.ShiftDown()
		if isinstance(wxEvt, wx.MouseEvent):
			ed["mouseDown"] = ed["dragging"] = wxEvt.Dragging()

	if isinstance(wxEvt, wx.ListEvent):
		pos = wxEvt.GetPosition()
		obj = wxEvt.GetEventObject()
		idx, flg = obj.HitTest(pos)
		ed["listIndex"] = idx

	if isinstance(wxEvt, wx.MenuEvent):
		menu = wxEvt.GetMenu()
		ed["menuObject"] = menu
		if menu is None:
			# pkm: appears to happen with submenus on Windows?
			ed["prompt"] = None
		else:
			ed["prompt"] = menu.Caption
		

	if isinstance(wxEvt, wx.CommandEvent):
		# It may have mouse information
		try:
			ed["mousePosition"] = wxEvt.GetPoint().Get()
		except: pass
		# See if it's a menu selection
		obj = wxEvt.GetEventObject()
		if isinstance(obj, dMenu):
			itmID = wxEvt.GetId()
			itm = obj._daboChildren.get(itmID, None)
			if itm is not None:
				ed["prompt"] = itm.Caption
				ed["menuItem"] = itm

	if isinstance(wxEvt, wx.KeyEvent):
		ed["keyCode"] = wxEvt.GetKeyCode()
		ed["rawKeyCode"] = wxEvt.GetRawKeyCode()
		ed["rawKeyFlags"] = wxEvt.GetRawKeyFlags()
		ed["unicodeChar"] = wxEvt.GetUniChar()
		ed["unicodeKey"] = wxEvt.GetUnicodeKey()
		ed["hasModifiers"] = wxEvt.HasModifiers()
		try:
			if wx.Platform in ("__WXMAC__", "__WXGTK__"):
				ed["keyChar"] = chr(wxEvt.GetKeyCode())
			else:	
				ed["keyChar"] = chr(wxEvt.GetRawKeyCode())
		except (ValueError, OverflowError):
			ed["keyChar"] = None
		if not ed["keyChar"]:
			# See if it is one of the keypad keys
			numpadKeys = { wx.WXK_NUMPAD0: "0", wx.WXK_NUMPAD1: "1", 
					wx.WXK_NUMPAD2: "2", wx.WXK_NUMPAD3: "3", wx.WXK_NUMPAD4: "4", 
					wx.WXK_NUMPAD5: "5", wx.WXK_NUMPAD6: "6", wx.WXK_NUMPAD7: "7", 
					wx.WXK_NUMPAD8: "8", wx.WXK_NUMPAD9: "9", wx.WXK_NUMPAD_SPACE: " ",
					wx.WXK_NUMPAD_TAB: "\t", wx.WXK_NUMPAD_ENTER: "\r", 
					wx.WXK_NUMPAD_EQUAL: "=", wx.WXK_NUMPAD_MULTIPLY: "*", 
					wx.WXK_NUMPAD_ADD: "+", wx.WXK_NUMPAD_SUBTRACT: "-", 
					wx.WXK_NUMPAD_DECIMAL: ".", wx.WXK_NUMPAD_DIVIDE: "/"}
			ed["keyChar"] = numpadKeys.get(ed["keyCode"], None)
	
	if isinstance(wxEvt, wx.ContextMenuEvent):
		ed["mousePosition"] = wxEvt.GetPosition()

	if isinstance(wxEvt, wx.CloseEvent):
		ed["force"] = not wxEvt.CanVeto()
		
	if isinstance(wxEvt, wx.TreeEvent):
		tree = wxEvt.GetEventObject()
		sel = tree.Selection
		ed["selectedNode"] = sel
		if isinstance(sel, list):
			ed["selectedCaption"] = ", ".join([ss.Caption for ss in sel])
		elif tree.Selection is not None:
			ed["selectedCaption"] = tree.Selection.Caption
		else:
			ed["selectedCaption"] = ""
		try:
			ed["itemID"] = wxEvt.GetItem()
			ed["itemNode"] = tree.find(ed["itemID"])[0]
		except:
			pass
	
	if isinstance(wxEvt, wx.SplitterEvent):
		try:
			ed["sashPosition"] = wxEvt.GetSashPosition()
		except:
			ed["sashPosition"] = wxEvt.GetEventObject().SashPosition
		if wxEvt.GetEventType() == wx.EVT_SPLITTER_UNSPLIT.evtType[0]:
			try:
				ed["windowRemoved"] = wxEvt.GetWindowBeingRemoved()
			except:
				ed["windowRemoved"] = None
		
	if hasattr(wxEvt, "GetId"):
		ed["id"] = wxEvt.GetId()

	if hasattr(wxEvt, "GetIndex"):
		ed["index"] = wxEvt.GetIndex()
	else:
		if hasattr(wxEvt, "GetSelection"):
			ed["index"] = wxEvt.GetSelection()

	
	if isinstance(wxEvt, wx.grid.GridEvent):
		ed["row"] = wxEvt.GetRow()
		ed["col"] = wxEvt.GetCol()
		ed["position"] = wxEvt.GetPosition()
		ed["altDown"] = wxEvt.AltDown()
		ed["controlDown"] = wxEvt.ControlDown()
		ed["metaDown"] = wxEvt.MetaDown()
		ed["shiftDown"] = wxEvt.ShiftDown()
		try:
			# Don't think this is implemented yet
			ed["commandDown"] = wxEvt.CmdDown()
		except: pass
	
	if isinstance(wxEvt, wx.grid.GridSizeEvent):
		#ed["rowOrCol"] = wxEvt.GetRowOrCol()
		if eventType == wx.grid.EVT_GRID_ROW_SIZE.evtType[0]:
			ed["row"] = wxEvt.GetRowOrCol()
		elif eventType == wx.grid.EVT_GRID_COL_SIZE.evtType[0]:
			ed["col"] = wxEvt.GetRowOrCol()
		ed["position"] = wxEvt.GetPosition()
		ed["altDown"] = wxEvt.AltDown()
		ed["controlDown"] = wxEvt.ControlDown()
		ed["metaDown"] = wxEvt.MetaDown()
		ed["shiftDown"] = wxEvt.ShiftDown()
		try:
			# Don't think this is implemented yet
			ed["commandDown"] = wxEvt.CmdDown()
		except: pass
	
	if isinstance(wxEvt, wx.calendar.CalendarEvent):
		ed["date"] = wxEvt.PyGetDate()
		# This will be undefined for all but the
		# EVT_CALENDAR_WEEKDAY_CLICKED event.
		ed["weekday"] = wxEvt.GetWeekDay()

	if isinstance(wxEvt, wx.lib.foldpanelbar.CaptionBarEvent):
		ed["expanded"] = wxEvt.GetFoldStatus()
		ed["collapsed"] = not ed["expanded"]
		ed["panel"] = wxEvt.GetEventObject().GetParent()
		
	return ed
	

def getMousePosition():
	"""Returns the position of the mouse on the screen."""
	return wx.GetMousePosition()


def getFormMousePosition():
	"""Returns the position of the mouse relative to the top left
	corner of the form.
	"""
	actwin = dabo.dAppRef.ActiveForm
	return actwin.relativeCoordinates(wx.GetMousePosition())
	

def getMouseObject():
	"""Returns a reference to the object below the mouse pointer
	at the moment the command is issued. Useful for interactive 
	development when testing changes to classes 'in the wild' of a 
	live application.
	"""
# 	print "MOUSE POS:", getMousePosition()
# 	win = wx.FindWindowAtPoint(getMousePosition())
	actwin = dabo.dAppRef.ActiveForm
# 	print "ACTWIN", actwin
	if isinstance(actwin, dabo.ui.dShell.dShell):
		actwin.lockDisplay()
		actwin.sendToBack()	
	else:
		actwin = None
	win = wx.FindWindowAtPointer()
	if actwin is not None:
		actwin.bringToFront()
		actwin.unlockDisplay()
	while not isinstance(win, dabo.ui.dPemMixin):
		try:
			win = win.GetParent()
		except AttributeError:
			break
	return win


def isControlDown():
	return wx.GetMouseState().controlDown


def isCommandDown():
	return wx.GetMouseState().cmdDown


def isShiftDown():
	return wx.GetMouseState().shiftDown


def isAltDown():
	return wx.GetMouseState().altDown


#### This will have to wait until I can figure out how to simulate a 
#### modal form for the calendar.
# def popupCalendar(dt=None, x=None, y=None, pos="topleft"):
# 	"""Pops up a calendar control at the specified x,y location, relative
# 	to the position. Positions can be one of 'topleft', 'topright', 
# 	'bottomleft', 'bottomright'. If no date is specified, defaults to 
# 	today. Returns the selected date, or None if the user presses Esc.
# 	"""
# 	class popCal(dBorderlessForm):
# 		def afterInit(self):
# 			dCalendar(self, RegID="cal", Position=(0,0))
# 			self.Size = self.cal.Size
# 			
# 		def onHit_cal(self, evt):
# 			self.Visible = False
# 		
# 	pos = pos.lower().strip()
# 	if dt is None:
# 		dt = datetime.date.today()
# 	if x is None or y is None:
# 		x,y = wx.GetMousePosition()
# 	else:
# 		x, y = wx.ClientToScreen(x, y)
# 	
# 	calForm = popCal(None)
# 	calForm.cal.Date = dt
# 	if "right" in pos:
# 		x = x - calForm.Width
# 	if "bottom" in pos:
# 		y = y - calForm.Height
# 	calForm.Position = x, y
# 	calForm.Visible = True
# 	calForm.setFocus()
# # 	while calForm.Visible:
# # 		time.sleep(0.5)
# # 		print "wake", calForm.Visible
# 	ret = calForm.cal.Date
# 	calForm.release()
# 	return ret
	


def getString(message="Please enter a string:", caption="Dabo",	defaultValue=""):
	"""Simple dialog for returning a small bit of text from the user."""
	dlg = wx.TextEntryDialog(None, message, caption, defaultValue)
	retVal = dlg.ShowModal()
	if retVal in (wx.ID_YES, wx.ID_OK):
		val = dlg.GetValue()
	else:
		val = None
	dlg.Destroy()
	return val


def getInt(message="Enter an integer value:", caption="Dabo",	defaultValue=0):
	"""Simple dialog for returning an integer value from the user."""
	class IntDialog(dabo.ui.dOkCancelDialog):
		def addControls(self):
			self.Caption = caption
			lbl = dabo.ui.dLabel(self, Caption=message)
			self.spnVal = dabo.ui.dSpinner(self, Value=defaultValue)
			hs = dabo.ui.dSizer("h")
			hs.append(lbl, halign="Right")
			hs.appendSpacer(5)
			hs.append(self.spnVal)
			self.Sizer.append(hs)
			
	dlg = IntDialog()
	dlg.show()
	if dlg.Accepted:
		val = dlg.spnVal.Value
	else:
		val = None
	dlg.Destroy()
	return val


# For convenience, make it so one can call dabo.ui.stop("Can't do that")
# instead of having to type dabo.ui.dMessageBox.stop("Can't do that")
areYouSure = dMessageBox.areYouSure
stop = dMessageBox.stop
info = dMessageBox.info
exclaim = dMessageBox.exclaim


def getColor(color=None):
	"""Displays the color selection dialog for the platform.
	Returns an RGB tuple of the selected color, or None if
	no selection was made.
	"""
	ret = None
	dlg = dColorDialog(None, color)
	if dlg.show() == kons.DLG_OK:
		ret = dlg.getColor()
	dlg.release()
	return ret


def getDate(dt=None):
	"""Displays a calendar dialog for the user to select a date. 
	Defaults to the given date parameter, or today if no value
	is passed.
	"""
	if dt is None:
		dt = datetime.date.today()
	try:
		mm, dd, yy = dt.month, dt.day, dt.year
	except:
		dabo.errorLog.write(_("Invalid date value passed to getDate(): %s") % dt)
		return None
	try:
		prnt = dabo.dAppRef.ActiveForm
	except:
		prnt = None
	dlg = wx.lib.calendar.CalenDlg(prnt, mm, dd, yy)
	dlg.Centre()
	if dlg.ShowModal() == wx.ID_OK:
		result = dlg.result
		day = int(result[1])
		month = result[2]
		year = int(result[3])
		monthNames = ["January", "February", "March", "April", "May", "June", 
				"July", "August", "September", "October", "November", "December"]
		ret = datetime.date(year, monthNames.index(month)+1, day)
	else:
		ret = None
	dlg.Destroy()
	return ret


def getFont(font=None):
	"""Displays the font selection dialog for the platform.
	Returns a font object that can be assigned to a control's
	Font property.
	"""
	fnt = None
	ret = None
	if font is None:
		param = None
	else:
		if not isinstance(font, dFont):
			# This will help identify older code
			dabo.errorLog.write("Invalid font class passed to getFont")
			return None
		param = font._nativeFont
	dlg = dFontDialog(None, param)
	if dlg.show() == kons.DLG_OK:
		fnt = dlg.getFont()
	dlg.release()
	if fnt is not None:
		ret = dFont(_nativeFont=fnt)
	return ret


def getAvailableFonts():
	"""Returns a list of all fonts available on the current system."""
	fEnum= wx.FontEnumerator()
	fEnum.EnumerateFacenames()
	list = fEnum.GetFacenames()
	list.sort()
	return list	


def _getPath(cls, wildcard, **kwargs):
	pth = None
	idx = None
	fd = cls(parent=None, wildcard=wildcard, **kwargs)
	if fd.show() == kons.DLG_OK:
		pth = fd.Path
		try:
			idx = fd.GetFilterIndex()
		except AttributeError:
			idx = None
	fd.release()
	return (pth, idx)


def getFile(*args, **kwargs):
	"""Display the file selection dialog for the platform, and return selection(s).

	Send an optional multiple=True for the user to pick more than one file. In 
	that case, the return value will be a sequence of unicode strings.

	Returns the path to the selected file or files, or None if no selection	was 
	made. Only file may be selected if multiple is False.

	Optionally, you may send wildcard arguments to limit the displayed files by
	file type. For example:
		getFile("py", "txt")
		getFile("py", "txt", multiple=True)
	"""
	wc = _getWild(*args)
	return _getPath(dFileDialog, wildcard=wc, **kwargs)[0]
		

def getFileAndType(*args, **kwargs):
	"""Displays the file selection dialog for the platform.
	Returns the path to the selected file, or None if no selection
	was made, as well as the wildcard value selected by the user.
	"""
	wc = _getWild(*args)
	pth, idx = _getPath(dFileDialog, wildcard=wc, **kwargs)
	if idx is None:
		ret = (pth, idx)
	else:
		ret = (pth, args[idx])
	return ret
	

def getSaveAs(*args, **kwargs):
	if not kwargs.has_key("message"):
		kwargs["message"] = "Save to:"
	if kwargs.has_key("wildcard"):
		args = list(args)
		args.append(kwargs["wildcard"])
	kwargs["wildcard"] = _getWild(*args)
	return _getPath(dSaveDialog, **kwargs)[0]


def getSaveAsAndType(*args, **kwargs):
	if not kwargs.has_key("message"):
		kwargs["message"] = "Save to:"
	if kwargs.has_key("wildcard"):
		args = list(args)
		args.append(kwargs["wildcard"])
	kwargs["wildcard"] = _getWild(*args)
	pth, idx = _getPath(dSaveDialog, **kwargs)
	if idx is None:
		ret = (pth, idx)
	else:
		ret = (pth, args[idx])
	return ret


def getFolder(message="Choose a folder", defaultPath="", wildcard="*"):
	"""Displays the folder selection dialog for the platform.
	Returns the path to the selected folder, or None if no selection
	was made.
	"""
	return _getPath(dFolderDialog, message=message, defaultPath=defaultPath, 
			wildcard=wildcard)[0]


def _getWild(*args):
	ret = "*"
	if args:
		# Split any args passed in the format of "gif | jpg | png"
		expanded = []
		for arg in args:
			try:
				argSp = [aa.strip() for aa in arg.split("|")]
			except AttributeError:
				argSp = [arg]
			expanded += argSp
		args = expanded
		arglist = []
		tmplt = "%s Files (*.%s)|*.%s"
		fileDict = {"html" : "HTML", 
			"xml" : "XML",
			"txt" : "Text",
			"jpg" : "JPEG",
			"gif" : "GIF",
			"png" : "PNG",
			"ico" : "Icon", 
			"bmp" : "Bitmap" }
			
		for a in args:
			descrp = ext = ""
			if a == "py":
				fDesc = "Python Scripts (*.py)|*.py"
			elif a == "*":
				fDesc = "All Files (*)|*"
			elif a == "fsxml":
				fDesc = "Dabo FieldSpec Files (*.fsxml)|*.fsxml"
			elif a == "cnxml":
				fDesc = "Dabo Connection Files (*.cnxml)|*.cnxml"
			elif a == "rfxml":
				fDesc = "Dabo Report Format Files (*.rfxml)|*.rfxml"
			elif a == "cdxml":
				fDesc = "Dabo Class Designer Files (*.cdxml)|*.cdxml"
			elif a == "mnxml":
				fDesc = "Dabo Menu Designer Files (*.mnxml)|*.mnxml"
			else:
				if a in fileDict:
					fDesc = tmplt % (fileDict[a], a, a)
				else:
					fDesc = "%s files (*.%s)|*.%s" % (a.upper(), a, a)
			arglist.append(fDesc)
		ret = "|".join(arglist)
	return ret


def sortList(chc, Caption="", ListCaption=""):
	"""Wrapper function for the list sorting dialog. Accepts a list,
	and returns the sorted list if the user clicks 'OK'. If they cancel
	out, the original list is returned.
	"""
	from dabo.ui.dialogs.SortingForm import SortingForm
	ret = chc
	# Make sure all items are string types. Convert those that are not,
	# but store their original values in a dict to be used for converting
	# back.
	chcDict = {}
	strChc = []
	needConvert = False
	for itm in chc:
		key = itm
		if not isinstance(itm, basestring):
			needConvert = True
			key = str(itm)
			strChc.append(key)
		else:
			strChc.append(itm)
		chcDict[key] = itm
	sf = SortingForm(None, Choices=strChc, Caption=Caption,
			ListCaption=ListCaption)
	sf.show()
	if sf.Accepted:
		if needConvert:
			ret = [chcDict[itm] for itm in sf.Choices]
		else:
			ret = sf.Choices
	sf.release()
	return ret


def createForm(srcFile, show=False, *args, **kwargs):
	"""Pass in a .cdxml file from the Designer, and this will
	instantiate a form from that spec. Returns a reference
	to the newly-created form.
	"""
	from dabo.lib.DesignerXmlConverter import DesignerXmlConverter
	conv = DesignerXmlConverter()
	cls = conv.classFromXml(srcFile)
	frm = cls(*args, **kwargs)
	if show:
		frm.show()
	return frm


def createMenuBar(srcFile, form=None, previewFunc=None):
	"""Pass in an .mnxml file saved from the Menu Designer, 
	and this will instantiate a MenuBar from that spec. Returns 
	a reference to the newly-created MenuBar. You can optionally
	pass in a reference to the form to which this menu is
	associated, so that you can enter strings that represent 
	form functions in the Designer, such as 'form.close', which 
	will call the associated form's close() method. If 'previewFunc'
	is passed, the menu command that would have been eval'd 
	and executed on a live menu will instead be passed back as
	a parameter to that function.
	"""
	def addMenu(mb, menuDict, form, previewFunc):
		if form is None:
			form = dabo.dAppRef.ActiveForm
		menu = dabo.ui.dMenu(mb)
		atts = menuDict["attributes"]
		menu.Caption = atts["Caption"]
		menu.MRU = atts["MRU"]
		menu.HelpText = atts["HelpText"]
		mb.appendMenu(menu)
		try:
			items = menuDict["children"]
		except KeyError:
			# No children defined for this menu
			return
		app = dabo.dAppRef
		for itm in items:	
			if "Separator" in itm["name"]:
				menu.appendSeparator()
			else:
				itmatts = itm["attributes"]
				cap = itmatts["Caption"]
				hk = itmatts["HotKey"]
				pic = itmatts["Picture"]
				if hk:
					cap += "\t%s" % hk
				txt = cap
				binding = previewFunc
				fnc = ""
				useFunc = ("Action" in itmatts) and (itmatts["Action"])
				if useFunc:
					fnc = itmatts["Action"]
				if (binding is None) and fnc:
					binding = eval(fnc)
				help = itmatts["HelpText"]
				menuItem = menu.append(cap, OnHit=binding, help=help,
						picture=pic)	
	
	mnd = dabo.lib.xmltodict.xmltodict(srcFile)
	mb = dabo.ui.dMenuBar()
	for mn in mnd["children"]:
		addMenu(mb, mn, form, previewFunc)
	return mb
	
	
def browse(dataSource, parent=None):
	"""Given a data source, a form with a grid containing the data
	is created and displayed. If the source is a Dabo cursor object, 
	its getDataSet() method will be called to extract the data.

	If parent is passed, the form isn't created, and the browsegrid
	becomes a child of parent instead.
	"""
	if not isinstance(dataSource, (list, tuple)):
		# See if it has a getDataSet() method available
		if hasattr(dataSource, "getDataSet"):
			dataSet = dataSource.getDataSet()
			try:
				cap = "Browse: %s" % dataSource.Table
			except:
				cap = "Browse"
		else:
			raise TypeError, "Incorrect data source passed to browse()"
	else:
		dataSet = dataSource
		cap = "Browse"

	parentPassed = True
	if parent is None:
		parent = dabo.ui.dForm(None, Caption=cap)
		parentPassed = False

	grd = dGrid(parent, AlternateRowColoring=True)
	grd.buildFromDataSet(dataSet)

	parent.Sizer.append(grd, 1, "x")
	parent.layout()

	if not parentPassed:
		parent.show()

	# This will allow you to optionally manage the grid and form
	return parent, grd


def fontMetricFromFont(txt, font):
	wind = wx.Frame(None)
	dc = wx.ClientDC(wind)
	dc.SetFont(font)
	ret = dc.GetTextExtent(txt)
	wind.Destroy()
	return ret


def fontMetricFromDrawObject(obj):
	"""Given a drawn text object, returns the width and height of the text."""
	return fontMetric(txt=obj.Text, face=obj.FontFace, size=obj.FontSize,
			bold=obj.FontBold, italic=obj.FontItalic)
	

def fontMetric(txt=None, wind=None, face=None, size=None, bold=None,
		italic=None):
	"""Calculate the width and height of the given text using the supplied
	font information. If any font parameters are missing, they are taken 
	from the specified window, or, if no window is specified, the currently
	active form. If no form is active, the app's MainForm is used.
	"""
	if wind is None:
		wind = dabo.dAppRef.ActiveForm
	needToRelease = False
	if wind is None:
		# Need to create one
		wind = wx.Frame(None)
		needToRelease = True
	if txt is None:
		try:
			txt = wind.Caption
		except:
			raise ValueError, "No text supplied to fontMetric call"
	fnt = wind.GetFont()
	if face is not None:
		fnt.SetFaceName(face)
	if size is not None:
		fnt.SetPointSize(size)
	if bold is not None:
		fnt.SetWeight(wx.BOLD)
	if italic is not None:
		fnt.SetStyle(wx.ITALIC)

	if not isinstance(wind, (dabo.ui.dForm, wx.Frame)):
		try:
			wind = wind.Form
		except:
			try:
				wind = wind.Parent
			except:
				pass
	dc = wx.ClientDC(wind)
	dc.SetFont(fnt)
	ret = dc.GetTextExtent(txt)
	if needToRelease:
		wind.Destroy()
	return ret


def saveScreenShot(obj=None, imgType=None, pth=None, delaySeconds=None):
	"""Takes a screenshot of the specified and writes it to a file, converting
	it to the requested image type. If no object is specified, the current
	ActiveForm is used. You can add an optional delaySeconds setting that 
	will let you set things up as needed before the image is taken; if not specified,
	the image is taken immediately.
	"""
	if delaySeconds is None:
		_saveScreenShot(obj=obj, imgType=imgType, pth=pth)
	else:
		millisecs = delaySeconds * 1000
		callAfterInterval(millisecs, _saveScreenShot, obj=obj, imgType=imgType, pth=pth)

def _saveScreenShot(obj, imgType, pth):
	if obj is None:
		obj = dabo.dAppRef.ActiveForm
	if obj is None:
		# Nothing active!
		stop(_("There is no active form to capture."), _("No Active Form"))
		return		
	bmp = obj.getCaptureBitmap()
	knownTypes = ("png", "jpg", "bmp", "pcx")
	if imgType is None:
		imgType = knownTypes
	else:
		if imgType.lower() not in knownTypes:
			imgType = knownTypes
		else:
			imgType = (imgType, )
	wxTypeDict = {"png":  wx.BITMAP_TYPE_PNG, 
			"jpg":  wx.BITMAP_TYPE_JPEG, 
			"bmp":  wx.BITMAP_TYPE_BMP,
			"pcx":  wx.BITMAP_TYPE_PCX}
	if pth is None:
		pth, typ = getSaveAsAndType(*imgType)
	else:
		typ = imgType[0]
	if pth is None:
		# User canceled
		return
	# Make sure that the file has the correct extension
	if not pth.lower().endswith(".%s" % typ):
		if pth.endswith("."):
			pth = "%s%s" % (pth, typ)
		else:
			pth = "%s.%s" % (pth, typ)
	img = wx.ImageFromBitmap(bmp)
	img.SaveFile(pth, wxTypeDict[typ])
		
	
		
	


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Using the img2py.py script in the wx.tools folder, you can convert
# an image to a text stream that can be included in a Python script.
# These next two methods take the image data and return a
# bitmap and an image, respectively.
def bitmapFromData(data):
	return BitmapFromImage(imageFromData(data))
	
	
def imageFromData(data):
	stream = cStringIO.StringIO(data)
	return ImageFromStream(stream)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


# For applications that use the same image more than once,
# this speeds up resolution of the requested image name.
_bmpCache = {}	
def strToBmp(val, scale=None, width=None, height=None):
	"""This can be either a path, or the name of a built-in graphic.
	If an adjusted size is desired, you can either pass a 'scale' value
	(where 1.00 is full size, 0.5 scales it to 50% in both Height and 
	Width), or you can pass specific 'height' and 'width' values. The 
	final image will be a bitmap resized to those specs.	
	"""
	ret = None
	if _bmpCache.has_key(val):
		ret = _bmpCache[val]
	elif os.path.exists(val):
		ret = pathToBmp(val)
	else:
		# Include all the pathing possibilities
		iconpaths = [os.path.join(pth, val) 
				for pth in dabo.icons.__path__]
		dabopaths = [os.path.join(pth, val) 
				for pth in dabo.__path__]
		localpaths = [os.path.join(os.getcwd(), pth, val)
				for pth in ("icons", "resources")]
		# Create a list of the places to search for the image, with
		# the most likely choices first.
		paths = [val] + iconpaths + dabopaths + localpaths
		# See if it's a standard icon
		for pth in paths:
			ret = dIcons.getIconBitmap(pth, noEmptyBmp=True)
			if ret:
				break
		if not ret and len(val) > 0:
			# See if it's a built-in graphic
			ret = getCommonBitmap(val)
	if not ret:
		# Return an empty bitmap
		ret = wx.EmptyBitmap(1, 1)
	else:
		_bmpCache[val] = ret
	
	if ret is not None:
		if scale is None and width is None and height is None:
			# No resize specs
			pass
		else:
			img = ret.ConvertToImage()
			oldWd = float(img.GetWidth())
			oldHt = float(img.GetHeight())
			if scale is not None:
				# The bitmap should be scaled.
				newWd = oldWd * scale
				newHt = oldHt * scale
			else:
				if width is not None and height is not None:
					# They passed both
					newWd = width
					newHt = height
				elif width is not None:
					newWd = width
					# Scale the height
					newHt = oldHt * (newWd / oldWd)
				elif height is not None:
					newHt = height
					# Scale the width
					newWd = oldWd * (newHt / oldHt)
			img.Rescale(newWd, newHt)
			ret = img.ConvertToBitmap()	
	return ret
	
	
def pathToBmp(pth):
	img = wx.NullImage
	img.LoadFile(pth)
	return img.ConvertToBitmap()


def resizeBmp(bmp, wd, ht):
	img = bmp.ConvertToImage()
	img.Rescale(wd, ht)
	return img.ConvertToBitmap()
	
	
def getCommonBitmap(name):
	"""wxPython comes with several built-in bitmaps for common icons. 
	This wraps the procedure for generating these bitmaps. If a name is
	passed for which there is no icon, an image denoting a missing image
	is returned.

	NOTE: this returns a raw bitmap, not a dabo.ui.dBitmap object.
	"""
	const = artConstants.get(name.lower(), artConstants.get("missingimage"))
	if const:
		return wx.ArtProvider.GetBitmap(const)
	return None


def getImagePath(nm, url=False):
	"""Given the name of an image in either the Dabo common directory, or the 
	current directory, returns the full path to the image. If 'url' is true, returns
	the path in a 'file:///image.ext' format.
	"""
	ret = dabo.icons.getIconFileName(nm)
	if ret is None:
		# Not found in Dabo directories; try app HomeDirectory
		try:
			ret = glob.glob(os.path.join(dabo.dAppRef.HomeDirectory, nm))[0]
		except IndexError:
			pass
	if ret is None:
		# Not found yet; try current dir
		try:
			ret = glob.glob(os.path.join(os.getcwd(), nm))[0]
		except IndexError:
			pass
	if ret is None:
		# try all the sys.path directories
		for pth in sys.path:
			try:
				ret = glob.glob(os.path.join(pth, nm))[0]
				break
			except IndexError:
				pass
	if ret and url:
		if wx.Platform == "__WXMSW__":
			ret = "file:%s" % urllib.pathname2url(ret).replace("|", ":")
			ret = re.sub(r"([A-Z])\|/", r"\1/", ret, re.I)
		else:
			ret = "file://%s" % ret
	return ret
		


def setdFormClass(typ):
	"""Re-defines 'dForm' as either the SDI form class, or the child MDI
	form class, depending on the parameter, which can be either 'SDI'
	or 'MDI'.
	"""
	lowtype = typ.lower().strip()
	if lowtype == "mdi":
		dabo.ui.__dict__["dForm"] = dFormChildMDI
	elif lowtype == "sdi":
		dabo.ui.__dict__["dForm"] = dFormSDI


class GridSizerSpanException(dabo.dException.dException):
	"""Raised when an attempt is made to set the RowSpan or
	ColSpan of an item to an illegal value.
	"""
	pass
