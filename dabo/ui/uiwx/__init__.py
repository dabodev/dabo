# -*- coding: utf-8 -*-
import sys
import os
import re
import glob
import urllib
import datetime
import time
import cStringIO
import warnings
import traceback
import dabo
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.lib import utils
import dabo.dEvents as dEvents
import dKeys

# Very VERY first thing: ensure a minimal wx is selected, but only if
# wx hasn't already been imported, and if we aren't running frozen:
if "wx" not in sys.modules and not getattr(sys, "frozen", False):
	minWx = "2.8"
	try:
		import wxversion
	except ImportError:
		sys.exit("wxPython needs to be at least version %s." % minWx)
	wxversion.ensureMinimal(minWx)

######################################################
# Very first thing: check for proper wxPython build:
_failedLibs = []
# note: may need wx.animate as well
for lib in ("wx", "wx.stc", "wx.lib.foldpanelbar", "wx.gizmos",
		"wx.lib.calendar", "wx.lib.masked", "wx.lib.buttons"):

	if getattr(sys, "frozen", False):
		# Just import it without catching the ImportError. This will let the
		# developer know which libs are essential to distribute, when trying
		# to run the exe on the target system. Could be some sub-library, not
		# simply "wx", "wx.stc", etc.
		__import__(lib)
	else:
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
if wx.VERSION >= (2, 8, 8):
	from dBorderlessButton import dBorderlessButton
from dButton import dButton
from dCalendar import dCalendar
from dCalendar import dExtendedCalendar
from dCheckBox import dCheckBox
from dCheckList import dCheckList
from dCollapsiblePanel import dCollapsiblePanel
from dColorDialog import dColorDialog
from dComboBox import dComboBox
from dDatePicker import dDatePicker
from dDateTextBox import dDateTextBox
from dDropdownList import dDropdownList
from dDialog import dDialog
from dDialog import dStandardButtonDialog
from dDialog import dOkCancelDialog
from dDialog import dYesNoDialog
from dEditableList import dEditableList
from dEditBox import dEditBox
from dEditor import dEditor
from dFileDialog import dFileDialog
from dFileDialog import dFolderDialog
from dFileDialog import dSaveDialog
from dReportProgress import dReportProgress
from dSlidePanelControl import dSlidePanelControl
from dSlidePanelControl import dSlidePanel
from dFont import dFont
from dFontDialog import dFontDialog
from dForm import dForm
from dForm import dToolForm
from dForm import dBorderlessForm
from dFormMain import dFormMain
from dGauge import dGauge
from dGlWindow import dGlWindow
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
from dMaskedTextBox import dMaskedTextBox
from dNumericBox import dNumericBox
try:
	from dMediaControl import dMediaControl
except ImportError:
	# Versions of wxPython < 2.8.11 on some platforms
	# do not have the wx.media.MediaCtrl class
	pass
from dMenuBar import dMenuBar
from dMenu import dMenu
from dMenuItem import dMenuItem
from dMenuItem import dCheckMenuItem
from dMenuItem import dRadioMenuItem
from dMenuItem import dSeparatorMenuItem
import dMessageBox
from dRadioList import dRadioList
from dPanel import dDataPanel
from dPanel import dPanel
from dPanel import dScrollPanel
from dPageFrame import dPageFrame
from dPageFrame import dPageToolBar
from dPageFrame import dPageList
from dPageFrame import dPageSelect
from dPageFrame import dDockTabs
from dPageFrameNoTabs import dPageFrameNoTabs
from dPage import dPage
from dPdfWindow import dPdfWindow
from dSearchBox import dSearchBox
from dShell import dShell
from dShell import dShellForm
from dSizer import dSizer
from dSizer import dSizerV
from dSizer import dSizerH
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
from dTreeView import dNode
from dTreeView import dTreeView
from dLed import dLed
import dUICursors as dUICursors
import gridRenderers
from dPageFrameMixin import dPageFrameMixin
from dAutoComplete import dAutoComplete


# Needs importing after at least dPanel:
from dDockForm import dDockForm

try:
	from dLinePlot import dLinePlot
except ImportError:
	pass

try:
	from dRichTextBox import dRichTextBox
except ImportError:
	pass

#The flatnotebook version we need is not avialable with wxPython < 2.8.4
if wx.VERSION >= (2, 8, 4):
	from dPageFrame import dPageStyled

# Support the old names, but issue deprecation warnings.
class dFoldPanelBar(dSlidePanelControl):
	def __init__(self, *args, **kwargs):
		"""**Deprecated:** use dSlidePanelControl instead"""
		warnings.warn(_("'dFoldPanelBar' is a deprecated name. Use 'dSlidePanelControl' instead"), DeprecationWarning)
		super(dFoldPanelBar, self).__init__(*args, **kwargs)

class dFoldPanel(dSlidePanel):
	def __init__(self, *args, **kwargs):
		"""**Deprecated:** use dSlidePanel instead"""
		warnings.warn(_("'dFoldPanel' is a deprecated name. Use 'dSlidePanel' instead"), DeprecationWarning)
		super(dFoldPanel, self).__init__(*args, **kwargs)

class dCheckListBox(dCheckList):
	def __init__(self, *args, **kwargs):
		"""**Deprecated:** use dCheckList instead"""
		warnings.warn(_("'dCheckListBox' is a deprecated name. Use 'dCheckList' instead"), DeprecationWarning)
		super(dCheckListBox, self).__init__(*args, **kwargs)

artConstants = {}
for item in (it for it in dir(wx) if it.startswith("ART_")):
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

def getUiApp(app, uiAppClass=None, callback=None, forceNew=False):
	"""
	This returns an instance of uiApp. If one is already running, that
	instance is returned. Otherwise, a new instance is created.
	"""
	if uiAppClass is None:
		uiAppClass = uiApp
	if forceNew:
		ret = None
	else:
		ret = wx.GetApp()
	if ret is None:
		ret = uiAppClass(app, callback)
	else:
		# existing app; fire the callback, if any
		if callback is not None:
			wx.CallAfter(callback)
	return ret


def callAfter(fnc, *args, **kwargs):
	"""
	Call the passed function with the passed arguments in the next
	event loop.
	"""
	if dabo.saveCallAfterStack:
		dabo.ui.lastCallAfterStack = "".join(traceback.format_stack())
	wx.CallAfter(fnc, *args, **kwargs)


_callAfterIntervalReferences = dabo.ui._callAfterIntervalReferences = {}
def callAfterInterval(interval, func, *args, **kwargs):
	"""
	Call the given function after <interval> milliseconds have elapsed.

	If the function is called again before the interval has elapsed, the original
	timer is destroyed and a new one instantiated. IOW, you can call this in a
	tight loop, and only the last call will get executed. Useful when you want to
	refresh something because you changed it, but the frequency of changes can be
	high.
	"""
	if dabo.saveCallAfterStack:
		dabo.ui.lastCallAfterStack = "".join(traceback.format_stack())
	if isinstance(func, int):
		# Arguments are in the old order
		interval, func = func, interval
	func_ref = func
	if func.func_closure:
		func_ref = func.func_code
	futureCall = _callAfterIntervalReferences.pop((func_ref, args), None)
	if futureCall:
		futureCall.Stop()

	def ca_func(_func_ref, _func, *args, **kwargs):
		"""Wrapper to call the user func and pop it off the references dict."""
		defunct = _callAfterIntervalReferences.pop((_func_ref, args), None)
		try:
			_func(*args, **kwargs)
		except wx._core.PyDeadObjectError:
			pass

	_callAfterIntervalReferences[(func_ref, args)] = wx.FutureCall(interval, ca_func, func_ref, func, *args, **kwargs)


def setAfter(obj, prop, val):
	"""
	Like callAfter(), but allows you to set a property instead of calling
	a function.
	"""
	try:
		fnc = getattr(obj.__class__, prop).fset
		wx.CallAfter(fnc, obj, val)
	except StandardError, e:
		dabo.log.error(_("setAfter() failed to set property '%(prop)s' to value '%(val)s': %(e)s.")
				% locals())


def setAfterInterval(interval, obj, prop, val):
	"""
	Like callAfterInterval(), but allows you to set a property instead
	of calling a function.
	"""
	try:
		fnc = getattr(obj.__class__, prop).fset
		callAfterInterval(interval, fnc, obj, val)
	except StandardError, e:
		dabo.log.error(_("setAfterInterval() failed to set property '%(prop)s' to value '%(val)s': %(e)s.")
				% locals())


def callEvery(interval, func, *args, **kwargs):
	"""
	Creates and returns a timer object that fires the specified function
	at the specified interval. Interval is given in milliseconds. It will pass along
	any additional arguments to the function when it is called.
	"""
	def _onHit(evt):
		func(*args, **kwargs)
	ret = dTimer(Interval=interval)
	ret.bindEvent(dEvents.Hit, _onHit)
	ret.start()
	return ret


def yieldUI(_safe=False, *args, **kwargs):
	"""Yield to other apps/messages."""
	if _safe:
		wx.YieldIfNeeded(*args, **kwargs)
	else:
		wx.Yield(*args, **kwargs)


def sendIdle():
	"""Used to force idle events, which can be needed for thread message processing."""
	wx.WakeUpIdle()


def beep():
	wx.Bell()


def busyInfo(msg="Please wait...", *args, **kwargs):
	"""
	Display a message that the system is busy.

	Assign the return value to a local object, and the message will stay until the
	object is explicitly unbound. For example::

		bi = dabo.ui.busyInfo("Please wait while I count to 10000...")
		for i in range(10000):
			pass
		bi = None

	"""
	bi = wx.BusyInfo(msg, *args, **kwargs)
	try:
		wx.Yield()
	except wx._core.PyAssertionError:
		# pkm: I got a message 'wxYield called recursively' which
		#      I'm unable to reproduce.
		pass
	return bi


def continueEvent(evt):
	try:
		evt.Skip()
	except AttributeError, e:
		# Event could be a Dabo event, not a wx event
		if isinstance(evt, dEvents.dEvent):
			pass
		else:
			dabo.log.error("Incorrect event class (%s) passed to continueEvent. Error: %s"
					% (ustr(evt), ustr(e)))


def discontinueEvent(evt):
	try:
		evt.Skip(False)
	except AttributeError, e:
		# Event could be a Dabo event, not a wx event
		if isinstance(evt, dEvents.dEvent):
			pass
		else:
			dabo.log.error("Incorrect event class (%s) passed to continueEvent. Error: %s"
					% (ustr(evt), ustr(e)))


def getEventData(wxEvt):
	ed = {}
	eventType = wxEvt.GetEventType()
	if isinstance(wxEvt, wx._core.FocusEvent):
		## segfault when dRadioList loses focus, on Gtk 2.8.10
		obj = None
	else:
		obj = wxEvt.GetEventObject()

	if isinstance(wxEvt, (wx.KeyEvent, wx.MouseEvent, wx.TreeEvent,
			wx.CommandEvent, wx.CloseEvent, wx.grid.GridEvent,
			wx.grid.GridSizeEvent, wx.SplitterEvent)):

		if dabo.allNativeEventInfo:
			# Cycle through all the attributes of the wx events, and evaluate them
			# for insertion into the dEvent.EventData dict.
			d = dir(wxEvt)
			upPems = [p for p in d if p[0].isupper()]
			for pem in upPems:
				if pem in ("Skip", "Clone", "Destroy", "Button", "ButtonIsDown",
						"GetLogicalPosition", "ResumePropagation", "SetEventObject",
						"SetEventType", "SetId", "SetExtraLong", "SetInt", "SetString",
						"SetTimestamp", "StopPropagation"):
					continue
				try:
					pemName = pem[0].lower() + pem[1:]
					ed[pemName] = getattr(wxEvt, pem)
				except (AttributeError, TypeError, wx._core.PyAssertionError):
					pass

	if isinstance(wxEvt, (wx.SplitterEvent,)):
		try:
			ed["mousePosition"] = (wxEvt.GetX(), wxEvt.GetY())
		except wx.PyAssertionError:
			ed["mousePosition"] = wx.GetMousePosition()

	if isinstance(wxEvt, (wx.KeyEvent, wx.MouseEvent)):
		ed["mousePosition"] = wxEvt.GetPositionTuple()
		ed["altDown"] = wxEvt.AltDown()
		ed["commandDown"] = wxEvt.CmdDown()
		ed["controlDown"] = wxEvt.ControlDown()
		ed["metaDown"] = wxEvt.MetaDown()
		ed["shiftDown"] = wxEvt.ShiftDown()
		if isinstance(wxEvt, wx.MouseEvent):
			ed["mouseDown"] = ed["dragging"] = wxEvt.Dragging()
			try:
				# MouseWheel scroll information
				ed["wheelRotation"] = wxEvt.WheelRotation * wxEvt.LinesPerAction
			except AttributeError:
				pass

	if isinstance(wxEvt, wx.ListEvent):
		pos = wxEvt.GetPosition()
		ht = obj.HitTest(pos)
		try:
			idx, flg = ht
		except TypeError:
			# Recent wx versions raise list events for unknown reasons.
			idx = ht
			flg = None
		ed["listIndex"] = idx
		try:
			ed["col"] = wxEvt.GetColumn()
		except AttributeError:
			pass

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
		except AttributeError:
			pass
		# See if it's a menu selection
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

	if (isinstance(wxEvt, wx.TreeEvent) or isinstance(obj, dabo.ui.dTreeView)) \
			and not isinstance(wxEvt, wx.WindowDestroyEvent):
		sel = obj.Selection
		ed["selectedNode"] = sel
		if isinstance(sel, list):
			ed["selectedCaption"] = ", ".join([ss.Caption for ss in sel])
		elif obj.Selection is not None:
			ed["selectedCaption"] = obj.Selection.Caption
		else:
			ed["selectedCaption"] = ""
		try:
			ed["itemID"] = wxEvt.GetItem()
			ed["itemNode"] = obj.find(ed["itemID"])[0]
		except (AttributeError, IndexError):
			pass

	if isinstance(wxEvt, wx.SplitterEvent):
		try:
			ed["sashPosition"] = wxEvt.GetSashPosition()
		except (AttributeError, wx.PyAssertionError):
			# On wx 2.8.12 the PyAssertionError exception is raised.
			ed["sashPosition"] = obj.SashPosition
		if eventType == wx.EVT_SPLITTER_UNSPLIT.evtType[0]:
			try:
				ed["windowRemoved"] = wxEvt.GetWindowBeingRemoved()
			except AttributeError:
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
		except AttributeError:
			pass

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
		except AttributeError:
			pass

	if isinstance(wxEvt, wx.calendar.CalendarEvent):
		ed["date"] = wxEvt.PyGetDate()
		# This will be undefined for all but the
		# EVT_CALENDAR_WEEKDAY_CLICKED event.
		ed["weekday"] = wxEvt.GetWeekDay()

	if isinstance(wxEvt, wx.lib.foldpanelbar.CaptionBarEvent):
		ed["expanded"] = wxEvt.GetFoldStatus()
		ed["collapsed"] = not ed["expanded"]
		ed["panel"] = obj.GetParent()

	try:
		if isinstance(wxEvt, wx.html.HtmlLinkEvent):
			ed["href"] = wxEvt.href
	except AttributeError:
		# wxPython 2.6 and earlier doesn't seem to have this event
		pass

	if isinstance(wxEvt, wx.ScrollWinEvent):
		ishz = (wxEvt.GetOrientation() == wx.HORIZONTAL)
		ed["orientation"] = {True: "Horizontal", False: "Vertical"}[ishz]
		ed["scrollpos"] = wxEvt.GetPosition()

	if isinstance(wxEvt, wx.stc.StyledTextEvent):
		# Adding all the event getters, even though most don't seem
		# to do anything.
		ed["alt"] = wxEvt.GetAlt()
		ed["control"] = wxEvt.GetControl()
		ed["dragAllowMove"] = wxEvt.GetDragAllowMove()
		ed["dragResult"] = wxEvt.GetDragResult()
		ed["dragText"] = wxEvt.GetDragText()
		ed["extraLong"] = wxEvt.GetExtraLong()
		ed["foldLevelNow"] = wxEvt.GetFoldLevelNow()
		ed["foldLevelPrev"] = wxEvt.GetFoldLevelPrev()
		ed["int"] = wxEvt.GetInt()
		ed["key"] = wxEvt.GetKey()
		ed["lParam"] = wxEvt.GetLParam()
		ed["length"] = wxEvt.GetLength()
		ed["line"] = wxEvt.GetLine()
		ed["linesAdded"] = wxEvt.GetLinesAdded()
		ed["listType"] = wxEvt.GetListType()
		ed["margin"] = wxEvt.GetMargin()
		ed["message"] = wxEvt.GetMessage()
		ed["modificationType"] = wxEvt.GetModificationType()
		ed["modifiers"] = wxEvt.GetModifiers()
		ed["position"] = wxEvt.GetPosition()
		ed["selection"] = wxEvt.GetSelection()
		ed["shift"] = wxEvt.GetShift()
		ed["string"] = wxEvt.GetString()
		ed["text"] = wxEvt.GetText()
		ed["wParam"] = wxEvt.GetWParam()
		ed["x"] = wxEvt.GetX()
		ed["y"] = wxEvt.GetY()

	return ed


def getMousePosition():
	"""Returns the position of the mouse on the screen."""
	return wx.GetMousePosition()


def getFormMousePosition():
	"""
	Returns the position of the mouse relative to the top left
	corner of the form.
	"""
	actwin = dabo.dAppRef.ActiveForm
	if actwin is not None:
		return actwin.relativeCoordinates(wx.GetMousePosition())
	else:
		return None


def getMouseObject():
	"""
	Returns a reference to the object below the mouse pointer
	at the moment the command is issued. Useful for interactive
	development when testing changes to classes 'in the wild' of a
	live application.
	"""
# 	print "MOUSE POS:", getMousePosition()
# 	win = wx.FindWindowAtPoint(getMousePosition())
	actwin = dabo.dAppRef.ActiveForm
# 	print "ACTWIN", actwin
	if isinstance(actwin, dabo.ui.dShell):
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


def getObjectAtPosition(x, y=None):
	"""
	Given a screen position, returns the object immediately under that
	position, or None if there is no such object. You can pass separate
	x,y coordinates, or an x,y tuple.
	"""
	if y is None:
		x, y = x
	win = wx.FindWindowAtPoint((x,y))
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


def isMouseLeftDown():
	if wx.VERSION < (2, 9):
		return wx.GetMouseState().leftDown
	else:
		return wx.GetMouseState().leftIsDown


def isMouseRightDown():
	if wx.VERSION < (2, 9):
		return wx.GetMouseState().rightDown
	else:
		return wx.GetMouseState().rightIsDown


def isMouseMiddleDown():
	if wx.VERSION < (2, 9):
		return wx.GetMouseState().middleDown
	else:
		return wx.GetMouseState().middleIsDown


def isMouseAux1Down():
	if wx.VERSION < (2, 9):
		return False
	else:
		return wx.GetMouseState().aux1IsDown


def isMouseAux2Down():
	if wx.VERSION < (2, 9):
		return False
	else:
		return wx.GetMouseState().aux2IsDown


def getDisplaySize():
	"""Returns the current display resolution in (width, height) format."""
	return wx.DisplaySize()


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


def _getActiveForm():
	app = dabo.dAppRef
	if app is not None:
		return app.ActiveForm
	return None


def getString(message=_("Please enter a string:"), caption="Dabo",
		defaultValue="", **kwargs):
	"""
	Simple dialog for returning a small bit of text from the user.

	Any additional keyword arguments are passed along to the dTextBox when it
	is instantiated. Some useful examples::

		# Give the textbox a default value:
		txt = dabo.ui.getString(defaultValue="initial string value")

		# Password Entry (\*'s instead of the actual text)
		txt = dabo.ui.getString(PasswordEntry=True)

	"""
	class StringDialog(dabo.ui.dOkCancelDialog):
		def addControls(self):
			self.Caption = caption
			lbl = dabo.ui.dLabel(self, Caption=message)
			self.strVal = dabo.ui.dTextBox(self, **kwargs)
			hs = dabo.ui.dSizer("h")
			hs.append(lbl, halign="Right")
			hs.appendSpacer(5)
			hs.append(self.strVal, 1)
			self.Sizer.append(hs, "expand")
			dabo.ui.callAfter(self.strVal.setFocus)

	if defaultValue:
		kwargs["Value"] = defaultValue
	dlg = StringDialog(_getActiveForm())
	dlg.show()
	if dlg.Accepted:
		val = dlg.strVal.Value
	else:
		val = None
	dlg.release()
	return val


def getInt(message=_("Enter an integer value:"), caption="Dabo",
		defaultValue=0, **kwargs):
	"""Simple dialog for returning an integer value from the user."""
	class IntDialog(dabo.ui.dOkCancelDialog):
		def addControls(self):
			self.Caption = caption
			lbl = dabo.ui.dLabel(self, Caption=message)
			self.spnVal = dabo.ui.dSpinner(self, **kwargs)
			hs = dabo.ui.dSizer("h")
			hs.append(lbl, halign="Right")
			hs.appendSpacer(5)
			hs.append(self.spnVal)
			self.Sizer.append(hs)
			dabo.ui.callAfter(self.spnVal.setFocus)

	if defaultValue:
		kwargs["Value"] = defaultValue
	dlg = IntDialog(_getActiveForm())
	dlg.show()
	if dlg.Accepted:
		val = dlg.spnVal.Value
	else:
		val = None
	dlg.Destroy()
	return val


# The next two methods prompt the user to select from a list. The first allows
# a single selection, while the second allows for multiple selections.
def getChoice(choices, message=None, caption=None, defaultPos=None):
	"""
	Simple dialog for presenting the user with a list of choices from which
	they can select one item.
	"""
	return _getChoiceDialog(choices, message, caption, defaultPos, False)


def getChoices(choices, message=None, caption=None, defaultPos=None):
	"""
	Simple dialog for presenting the user with a list of choices from which
	they can select one or more items. Returns a tuple containing the selections.
	"""
	return _getChoiceDialog(choices, message, caption, defaultPos, True)


def _getChoiceDialog(choices, message, caption, defaultPos, mult):
	if message is None:
		message = _("Please make your selection:")
	if caption is None:
		caption = "Dabo"
	if defaultPos is None:
		defaultPos = 0
	if mult is None:
		mult = False
	class ChoiceDialog(dabo.ui.dOkCancelDialog):
		def addControls(self):
			self.Caption = caption
			lbl = dabo.ui.dLabel(self, Caption=message)
			self.lst = dabo.ui.dListBox(self, Choices=choices,
					PositionValue=defaultPos, MultipleSelect=mult,
					OnMouseLeftDoubleClick=self.onMouseLeftDoubleClick)
			sz = self.Sizer
			sz.appendSpacer(25)
			sz.append(lbl, halign="center")
			sz.appendSpacer(5)
			sz.append(self.lst, 4, halign="center")
			if mult:
				hsz = dabo.ui.dSizer("h")
				btnAll = dabo.ui.dButton(self, Caption=_("Select All"),
						OnHit=self.selectAll)
				btnNone = dabo.ui.dButton(self, Caption=_("Unselect All"),
						OnHit=self.unselectAll)
				btnInvert = dabo.ui.dButton(self, Caption=_("Invert Selection"),
						OnHit=self.invertSelection)
				hsz.append(btnAll)
				hsz.appendSpacer(8)
				hsz.append(btnNone)
				hsz.appendSpacer(8)
				hsz.append(btnInvert)
				sz.appendSpacer(16)
				sz.append(hsz, halign="center", border=20)
				sz.appendSpacer(8)
				sz.append(dabo.ui.dLine(self), "x", border=44,
						borderSides=("left", "right"))
			sz.appendSpacer(24)

		def onMouseLeftDoubleClick(self, evt):
			self.runOK()

		def selectAll(self, evt):
			self.lst.selectAll()

		def unselectAll(self, evt):
			self.lst.unselectAll()

		def invertSelection(self, evt):
			self.lst.invertSelections()

	dlg = ChoiceDialog(_getActiveForm())
	dlg.show()
	if dlg.Accepted:
		val = dlg.lst.StringValue
	else:
		val = None
	dlg.release()
	return val


# For convenience, make it so one can call dabo.ui.stop("Can't do that")
# instead of having to type dabo.ui.dMessageBox.stop("Can't do that")
areYouSure = dMessageBox.areYouSure
stop = dMessageBox.stop
info = dMessageBox.info
exclaim = dMessageBox.exclaim


def getColor(color=None):
	"""
	Displays the color selection dialog for the platform.
	Returns an RGB tuple of the selected color, or None if
	no selection was made.
	"""
	ret = None
	dlg = dColorDialog(_getActiveForm(), color)
	if dlg.show() == kons.DLG_OK:
		ret = dlg.getColor()
	dlg.release()
	return ret


def getDate(dt=None):
	"""
	Displays a calendar dialog for the user to select a date.
	Defaults to the given date parameter, or today if no value
	is passed.
	"""
	if dt is None:
		dt = datetime.date.today()
	try:
		mm, dd, yy = dt.month, dt.day, dt.year
	except AttributeError:
		dabo.log.error(_("Invalid date value passed to getDate(): %s") % dt)
		return None
	dlg = wx.lib.calendar.CalenDlg(_getActiveForm(), mm, dd, yy)
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
	"""
	Displays the font selection dialog for the platform.
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
			dabo.log.error("Invalid font class passed to getFont")
			return None
		param = font._nativeFont
	dlg = dFontDialog(_getActiveForm(), param)
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
	fd = cls(parent=_getActiveForm(), wildcard=wildcard, **kwargs)
	if fd.show() == kons.DLG_OK:
		pth = fd.Path
		try:
			idx = fd.GetFilterIndex()
		except AttributeError:
			idx = None
	fd.release()
	return (pth, idx)


def getFile(*args, **kwargs):
	"""
	Display the file selection dialog for the platform, and return selection(s).

	Send an optional multiple=True for the user to pick more than one file. In
	that case, the return value will be a sequence of unicode strings.

	Returns the path to the selected file or files, or None if no selection	was
	made. Only one file may be selected if multiple is False.

	Optionally, you may send wildcard arguments to limit the displayed files by
	file type. For example::

		getFile("py", "txt")
		getFile("py", "txt", multiple=True)

	"""
	wc = _getWild(*args)
	return _getPath(dFileDialog, wildcard=wc, **kwargs)[0]


def getFileAndType(*args, **kwargs):
	"""
	Displays the file selection dialog for the platform.
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
	try:
		kwargs["message"]
	except KeyError:
		kwargs["message"] = "Save to:"
	try:
		wc = kwargs["wildcard"]
		args = list(args)
		args.append(wc)
	except KeyError:
		pass
	kwargs["wildcard"] = _getWild(*args)
	return _getPath(dSaveDialog, **kwargs)[0]


def getSaveAsAndType(*args, **kwargs):
	try:
		kwargs["message"]
	except KeyError:
		kwargs["message"] = "Save to:"
	try:
		wc = kwargs["wildcard"]
		args = list(args)
		args.append(wc)
	except KeyError:
		pass
	kwargs["wildcard"] = _getWild(*args)
	pth, idx = _getPath(dSaveDialog, **kwargs)
	if idx is None:
		ret = (pth, idx)
	else:
		ret = (pth, args[idx])
	return ret


def getFolder(message=_("Choose a folder"), defaultPath="", wildcard="*"):
	"""
	Displays the folder selection dialog for the platform.
	Returns the path to the selected folder, or None if no selection
	was made.
	"""
	return _getPath(dFolderDialog, message=message, defaultPath=defaultPath,
			wildcard=wildcard)[0]
# Create an alias that uses 'directory' instead of 'folder'
getDirectory = getFolder


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
		fileDict = dabo.file_extensions
		fileDict.update(dabo.custom_extensions)
		tmplt = "%s (*.%s)|*.%s"
		normArgs = [arg.lower() for arg in args]
		for ftype in normArgs:
			try:
				fDesc = fileDict[ftype.lower()]
			except KeyError:
				fDesc = "%s Files" % ftype.upper()
			arglist.append(tmplt % (fDesc, ftype, ftype))
		ret = "|".join(arglist)
	return ret


def getSystemInfo(returnType=None):
	"""
	Return app information in the requested format (can be one
	of "dataset", "html", or "string" (default).
	"""
	if returnType is None:
		returnType = "string"
	rType = returnType.lower()[0]
	app = dabo.dAppRef
	ds = []
	if app:
		plat = app.Platform
	else:
		plat = sys.platform
	ds.append({"name": "Platform:", "value": plat})
	ds.append({"name": "Python Version:", "value": "%s on %s"
			% (sys.version.split()[0], sys.platform)})
	if app:
		appVersion = app.getAppInfo("appVersion")
		appName = app.getAppInfo("appName")
	else:
		appVersion = "?"
		appName = "Dabo"
	ds.append({"name": "Dabo Version:", "value": dabo.__version__})
	ds.append({"name": "UI Version:", "value": "%s on %s" % (dabo.ui.uiType["version"],
			dabo.ui.uiType["platform"])})
	if rType == "d":
		# Return the dataset
		return ds
	lines = []
	for r in ds:
		lines.append("%s %s" % (r["name"], r["value"]))
	eol = {"h": "<br>\n", "s": "\n"}[rType]
	return eol.join(lines)


def sortList(chc, Caption="", ListCaption=""):
	"""
	Wrapper function for the list sorting dialog. Accepts a list,
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
			key = ustr(itm)
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


def copyToClipboard(val):
	uiApp.copyToClipboard(val)


def getFromClipboard():
	data = wx.TextDataObject()
	cb = wx.TheClipboard
	cb.Open()
	success = cb.GetData(data)
	cb.Close()
	if success:
		return data.GetText()
	else:
		# See if it's bitmap data
		data = wx.BitmapDataObject()
		cb.Open()
		success = cb.GetData(data)
		cb.Close()
		if success:
			return data.GetBitmap()
		else:
			return None


def getScrollWinEventClass(evt):
	"""
	Window scroll events use different codes across different platforms.
	This code identifies the appropriate event and returns the appropriate
	Dabo event class.
	"""
	evtType = evt.GetEventType()
	# Seems as though the wx events for window scrolling use a series of IDs
	# for these events, but the numbering changes with different platforms and
	# builds of wx. However, it seems that the base is always the generic
	# EVT_SCROLLWIN's typeId value.
	baseEvtNum = wx.EVT_SCROLLWIN.typeId
	evtOffset = evtType - baseEvtNum
	# Get the corresponding Dabo event class for the wx event.
	daboEvents = (dEvents.ScrollTop, dEvents.ScrollBottom, dEvents.ScrollLineUp,
			dEvents.ScrollLineDown, dEvents.ScrollPageUp, dEvents.ScrollPageDown,
			dEvents.ScrollThumbDrag, dEvents.ScrollThumbRelease)
	return daboEvents[evtOffset]


def _checkForRawXML(srcFile):
	isRawXML = srcFile.strip().startswith("<")
	if not isRawXML:
		try:
			srcFile = utils.resolvePathAndUpdate(srcFile)
		except IOError, e:
			dabo.log.error(_("Class file '%s' not found") % srcFile)
			raise
	return srcFile, isRawXML


def createClass(srcFile, *args, **kwargs):
	"""
	Given a .cdxml class definition file path, will return the
	corresponding Python class."""
	from dabo.lib.DesignerClassConverter import DesignerClassConverter
	srcFile, isRaw = _checkForRawXML(srcFile)
	conv = DesignerClassConverter()
	cls = conv.classFromText(srcFile)
	if not isRaw:
		cls._sourceFilePath = srcFile
	return cls


def createForm(srcFile, show=False, *args, **kwargs):
	"""
	Instantiate and return a form instance, given a .cdxml file.

	srcFile may be a path to the file on disk, or the cdxml text. If
	show is True, the form will be automatically displayed. Any
	additional arguments will be passed on to the constructor of the
	class.

	A common question on the dabo-users mailing list is how to
	instantiate a cdxml form as a child of another form. Easy! ::

		frm = dabo.ui.createForm("my.cdxml", parent=self)

	"""
	cls = createClass(srcFile)
	frm = cls(*args, **kwargs)
	if show:
		frm.show()
	return frm


def createMenuBar(src, form=None, previewFunc=None):
	"""
	Pass in either an .mnxml file path saved from the Menu Designer, or a dict representing
	the menu, which will be used to instantiate a MenuBar. Returns a reference to the
	newly-created MenuBar. You can optionally pass in a reference to the form to which this menu
	is associated, so that you can enter strings that represent form functions in the Designer,
	such as 'form.close', which will call the associated form's close() method. If 'previewFunc'
	is passed, the menu command that would have been eval'd and executed on a live menu will
	instead be passed back as a parameter to that function.
	"""
	def addMenu(mb, menuDict, form, previewFunc):
		if form is None:
			form = dabo.dAppRef.ActiveForm
		if isinstance(mb, dabo.ui.dMenuBar):
			menu = dabo.ui.dMenu(mb)
		else:
			menu = dabo.ui.dMenu()
		atts = menuDict["attributes"]
		menu.Caption = menu._extractKey(atts, "Caption")
		menu.MRU = menu._extractKey(atts, "MRU")
		menu.HelpText = menu._extractKey(atts, "HelpText")
		if atts:
			menu.setPropertiesFromAtts(atts, context={"form": form, "app": dabo.dAppRef})
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
			elif itm["name"] == "MenuPanel":
				addMenu(menu, itm, form, previewFunc)
			else:
				itmatts = itm["attributes"]
				cap = menu._extractKey(itmatts, "Caption")
				hk = menu._extractKey(itmatts, "HotKey")
				pic = menu._extractKey(itmatts, "Icon")
				if pic == "None":
					# Can be the string 'None' if changed in the Menu Designer
					pic = None
				special = menu._extractKey(itmatts, "special", None)
				binding = previewFunc
				fnc = menu._extractKey(itmatts, "Action", "")
				if (binding is None) and fnc:
					try:
						binding = eval(fnc)
					except NameError:
						binding = fnc
				mtype = menu._extractKey(itmatts, "MenuType", "")
				help = menu._extractKey(itmatts, "HelpText")
				menuItem = menu.append(cap, help=help, picture=pic, special=special,
						HotKey=hk, menutype=mtype)
				menuItem._bindingText = "%s" % fnc
				if itmatts:
					menuItem.setPropertiesFromAtts(itmatts,
							context={"form": form, "app": dabo.dAppRef})
				menuItem.bindEvent(dEvents.Hit, binding)

	if isinstance(src, dict):
		mnd = src
	else:
		try:
			# See if the src is a JSON-ified dict
			src = dabo.lib.jsonDecode(src)
		except ValueError:
			# Not JSON
			try:
				src = utils.resolvePathAndUpdate(src)
			except IOError, e:
				stop(e, _("File Not Found"))
				return
		mnd = dabo.lib.xmltodict.xmltodict(src)
	mb = dabo.ui.dMenuBar()
	for mn in mnd["children"]:
		addMenu(mb, mn, form, previewFunc)
	return mb


def makeGridEditor(controlClass, minWidth=None, minHeight=None, **controlProps):
	class _BaseCellEditor(wx.grid.PyGridCellEditor):
		_controlClass = None
		_minWidth = None
		_minHeight = None

		def Create(self, parent, id, evtHandler):
			"""
			Called to create the control, which must derive from wx.Control.

			*Must Override*

			"""
			if not self._controlClass:
				raise TypeError(_("Cannot create custom editor without a control class specified."))
			self._control = self._controlClass(parent, **controlProps)
			self._grid = parent.GetParent()
			self._control.bindEvent(dEvents.KeyDown, self._onKeyDown)
			self.SetControl(self._control)
			if evtHandler:
				self._control.PushEventHandler(evtHandler)

		def _onKeyDown(self, evt):
			ed = evt.EventData
			key, mod, shift = (ed["keyCode"], ed["hasModifiers"],
					ed["shiftDown"] or getattr(self, "_shiftDown", False))
			ctrl = self._control
			grid = self._grid

			if key == dKeys.key_Up and not mod and not shift:
				grid.HideCellEditControl()
				row = grid.CurrentRow - 1
				if row < 0:
					row = 0
				grid.CurrentRow = row
				evt.stop()

			elif key == dKeys.key_Down and not mod and not shift:
				grid.HideCellEditControl()
				row = grid.CurrentRow + 1
				if row > grid.RowCount - 1:
					row = grid.RowCount + 1
				grid.CurrentRow = row
				evt.stop()

		def SetSize(self, rect):
			"""
			Called to position/size the edit control within the cell rectangle.
			If you don't fill the cell (the rect) then be sure to override
			PaintBackground and do something meaningful there.
			"""
			wd = rect.width + 2
			if self._minWidth:
				wd = max(self._minWidth, wd)
			ht = rect.height+2
			if self._minHeight:
				ht = max(self._minHeight, ht)
			self._control.SetDimensions(rect.x, rect.y, wd, ht, wx.SIZE_ALLOW_MINUS_ONE)

		def PaintBackground(self, rect, attr):
			"""
			Draws the part of the cell not occupied by the edit control.  The
			base  class version just fills it with background colour from the
			attribute.	In this class the edit control fills the whole cell so
			don't do anything at all in order to reduce flicker.
			"""
			pass

		def BeginEdit(self, row, col, grid):
			"""
			Fetch the value from the table and prepare the edit control
			to begin editing.  Set the focus to the edit control.

			*Must Override*

			"""
			self.startValue = grid.GetTable().GetValue(row, col, _fromGridEditor=True)
			self._control.Value = self.startValue
			self._control.setFocus()

		def EndEdit(self, row, col, grid):
			"""
			Complete the editing of the current cell. Returns True if the value
			has changed.  If necessary, the control may be destroyed.

			*Must Override*

			"""
			changed = False
			val = self._control.Value
			if val != self.startValue:
				changed = True
				grid.GetTable().SetValue(row, col, val, _fromGridEditor=True)
			self.startValue = None
			return changed

		def Reset(self):
			"""
			Reset the value in the control back to its starting value.

			*Must Override*

			"""
			self._control.Value = self.startValue

		def IsAcceptedKey(self, evt):
			"""
			Return True to allow the given key to start editing: the base class
			version only checks that the event has no modifiers.  F2 is special
			and will always start the editor.
			"""
			return (not (evt.ControlDown() or evt.AltDown()) and
					evt.GetKeyCode() != wx.WXK_SHIFT)

		def StartingKey(self, evt):
			"""
			If the editor is enabled by pressing keys on the grid, this will be
			called to let the editor do something about that first key if desired.
			"""
			pass

		def StartingClick(self):
			"""
			If the editor is enabled by clicking on the cell, this method will be
			called to allow the editor to simulate the click on the control if
			needed.
			"""
			pass

		def Destroy(self):
			"""final cleanup"""
			self.base_Destroy()

		def Clone(self):
			"""
			Create a new object which is the copy of this one
			"""
			# pkm: I'm not seeing this method ever called. If it is ever called,
			#      the following line will make that clear. :)
			1/0
			return self.__class__


	class _CustomEditor(_BaseCellEditor):
		_controlClass = controlClass
		_minWidth = minWidth
		_minHeight = minHeight
	return _CustomEditor


def browse(dataSource, parent=None, keyCaption=None, includeFields=None,
		colOrder=None, colWidths=None, colTypes=None, autoSizeCols=True):
	"""
	Given a data source, a form with a grid containing the data
	is created and displayed. If the source is a Dabo cursor object,
	its getDataSet() method will be called to extract the data.

	If parent is passed, the form isn't created, and the browsegrid
	becomes a child of parent instead.

	The columns will be taken from the first record of the dataset,	with each
	column header caption being set to the field name, unless	the optional
	keyCaption parameter is passed. This parameter is a 1:1 dict containing
	the data set keys as its keys, and the desired caption as the
	corresponding value.

	If the includeFields parameter is a sequence, the only columns added will
	be the fieldnames included in the includeFields sequence. If the
	includeFields	parameter is None, all fields will be added to the grid.

	The columns will be in the order returned by ds.keys(), unless the
	optional colOrder parameter is passed. Like the keyCaption property,
	this is a 1:1 dict containing key:order.
	"""
	if not isinstance(dataSource, (list, tuple)):
		# See if it has a getDataSet() method available
		if hasattr(dataSource, "getDataSet"):
			dataSet = dataSource.getDataSet()
			try:
				cap = "Browse: %s" % dataSource.Table
			except AttributeError:
				cap = "Browse"
		else:
			raise TypeError("Incorrect data source passed to browse()")
	else:
		dataSet = dataSource
		cap = "Browse"

	parentPassed = True
	if parent is None:
		parent = dabo.ui.dForm(None, Caption=cap)
		parentPassed = False

	grd = dGrid(parent, AlternateRowColoring=True)
	grd.buildFromDataSet(dataSet, keyCaption=keyCaption,
			includeFields=includeFields, colOrder=colOrder, colWidths=colWidths,
			colTypes=colTypes, autoSizeCols=autoSizeCols)

	parent.Sizer.append(grd, 1, "x")
	parent.layout()

	if not parentPassed:
		parent.show()

	# This will allow you to optionally manage the grid and form
	return parent, grd


def getPositionInSizer(obj):
	"""
	Returns the current position of this control in its containing
	sizer. This is useful for when a control needs to be re-created in place.
	If the containing sizer is a box sizer, the integer position will be returned.
	If it is a grid sizer, a row,col tuple will be returned. If the object is
	not contained in a sizer, None will be returned.
	"""
	sz = obj.GetContainingSizer()
	if not sz:
		return None
	if isinstance(sz, wx.BoxSizer):
		chil = sz.GetChildren()
		for pos in range(len(chil)):
			# Yeah, normally we'd just iterate over the children, but
			# we want the position, so...
			szitem = chil[pos]
			if szitem.IsWindow():
				if szitem.GetWindow() == obj:
					return pos
		# If we reached here, something's wrong!
		dabo.log.error(_("Containing sizer did not match item %s") % obj.Name)
		return None
	elif isinstance(sz, wx.GridBagSizer):
		# Return a row,col tuple
		row, col = sz.getGridPos(obj)
		return (row, col)
	else:
		return None


def setPositionInSizer(obj, pos):
	sz = obj.GetContainingSizer()
	if not sz:
		return None
	sz.setPositionInSizer(obj, pos)


def fontMetricFromFont(txt, font):
	if isinstance(font, dabo.ui.dFont):
		font = font._nativeFont
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


def fontMetricFromDC(dc, text):
	"""
	Given a DC and text, returns the width and height of the text as it
	would be drawn in that DC.
	"""
	return dc.GetTextExtent(text)


def fontMetric(txt=None, wind=None, face=None, size=None, bold=None,
		italic=None):
	"""
	Calculate the width and height of the given text using the supplied
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
		except AttributeError:
			raise ValueError("No text supplied to fontMetric call")
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
		except AttributeError:
			try:
				wind = wind.Parent
			except AttributeError:
				pass
	dc = wx.ClientDC(wind)
	dc.SetFont(fnt)
	ret = dc.GetTextExtent(txt)
	if needToRelease:
		wind.Destroy()
	return ret


def saveScreenShot(obj=None, imgType=None, pth=None, delaySeconds=None):
	"""
	Takes a screenshot of the specified object and writes it to a file, converting
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
	"""
	This can be either a path, or the name of a built-in graphic.
	If an adjusted size is desired, you can either pass a 'scale' value
	(where 1.00 is full size, 0.5 scales it to 50% in both Height and
	Width), or you can pass specific 'height' and 'width' values. The
	final image will be a bitmap resized to those specs.
	"""
	ret = None
	cwd = os.getcwd()
	app = dabo.dAppRef
	if app:
		cwd = app.HomeDirectory

	try:
		ret = _bmpCache[val]
	except KeyError:
		if os.path.exists(val):
			ret = pathToBmp(val)
		else:
			# Include all the pathing possibilities
			iconpaths = [os.path.join(pth, val)
					for pth in dabo.icons.__path__]
			dabopaths = [os.path.join(pth, val)
					for pth in dabo.__path__]
			localpaths = [os.path.join(cwd, pth, val)
					for pth in ("icons", "resources")]
			# Create a list of the places to search for the image, with
			# the most likely choices first.
			paths = [val] + iconpaths + dabopaths + localpaths
			# See if it's running as a Mac application
			macAppIndicator = "/Contents/Resources"
			dpth = dabo.__path__[0]
			if macAppIndicator in dpth:
				# Running as a py2app application
				resPth = "%s%s" % (dpth.split(macAppIndicator)[0], macAppIndicator)
				macPaths = [os.path.join(resPth, pth, val)
					for pth in ("icons", "resources")]
				paths += macPaths

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
	"""
	wxPython comes with several built-in bitmaps for common icons.
	This wraps the procedure for generating these bitmaps. If a name is
	passed for which there is no icon, an image denoting a missing image
	is returned.

	.. note::

		This returns a raw bitmap, not a dabo.ui.dBitmap object.

	"""
	const = artConstants.get(name.lower(), artConstants.get("missingimage"))
	if const:
		return wx.ArtProvider.GetBitmap(const)
	return None


def getImagePath(nm, url=False):
	"""
	Given the name of an image in either the Dabo common directory, or the
	current directory, returns the full path to the image. If 'url' is true, returns
	the path in a 'file:///image.ext' format.
	"""
	def globfind(loc):
		loc = os.path.abspath(loc)
		try:
			return glob.glob(os.path.join(loc, nm))[0]
		except IndexError:
			return None

	ret = dabo.icons.getIconFileName(nm)
	if not ret:
		# Try other locations:
		trials = [dabo.dAppRef.HomeDirectory, os.getcwd()]
		trials.extend([p for p in sys.path])

		for trial in trials:
			ret = globfind(trial)
			if ret:
				break

	if ret and url:
		if wx.Platform == "__WXMSW__":
			ret = "file:%s" % urllib.pathname2url(ret).replace("|", ":")
			ret = re.sub(r"([A-Z])\|/", r"\1/", ret, re.I)
		else:
			ret = "file://%s" % ret
	return ret


def setdFormClass(typ):
	"""
	Re-defines 'dForm' as either the SDI form class, or the child MDI
	form class, depending on the parameter, which can be either 'SDI'
	or 'MDI'.
	"""
	lowtype = typ.lower().strip()
	if lowtype == "mdi":
		dabo.ui.__dict__["dForm"] = dFormChildMDI
	elif lowtype == "sdi":
		dabo.ui.__dict__["dForm"] = dFormSDI


def spawnProcess(cmd, wait=False, handler=None):
	"""
	Launch a separate process. Control is immediately returned to the
	calling program, unless you call this with 'wait=True'.
	"""
	class Proc(wx.Process):
		def __init__(self, parent, *args, **kwargs):
			super(Proc, self).__init__(parent, *args, **kwargs)
			self._handler = parent
		def OnTerminate(self, pid, status):
			if self._handler:
				try:
					handler.onProcTermintated(self, pid, status)
				except AttributeError:
					pass
		def read(self):
			# This is still not working; I'm not sure how it's supposed to work,
			# based on the scanty documentation.
			out = ""
			stream = self.GetInputStream()
			if stream.CanRead():
				 out = stream.read()
			stream = self.GetErrorStream()
			err = ""
			if stream.CanRead():
				err = "Errors:\n%s" % stream.read()
			return (out, err)
	proc = Proc(handler)
	proc.Redirect()
	if wait:
		flag = wx.EXEC_SYNC
	else:
		flag = wx.EXEC_ASYNC
	pidOrResult = wx.Execute(cmd, flag, proc)
	return pidOrResult, proc


class GridSizerSpanException(dabo.dException.dException):
	"""
	Raised when an attempt is made to set the RowSpan or
	ColSpan of an item to an illegal value.
	"""
	pass
