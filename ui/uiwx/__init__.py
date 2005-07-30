import wx
import dabo.ui
import dabo.dConstants as k
from uiApp import uiApp

uiType = {'shortName': 'wx', 'moduleName': 'uiwx', 'longName': 'wxPython'}
uiType['version'] = wx.VERSION_STRING
_platform = wx.PlatformInfo[1]
if wx.PlatformInfo[0] == "__WXGTK__":
	_platform += " (%s)" % wx.PlatformInfo[3]
uiType['platform'] = _platform

# The wx app object must be created before working with anything graphically.
# As we don't want to require people to use dApp, and as dApp is the one that
# creates wx.App (via uiApp), let's create an initial app object just to get
# it loaded and make wx happy. It'll get replaced when dApp instantiates.
#app = wx.PySimpleApp()

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

# Import into public namespace:
from dBox import dBox
from dBitmap import dBitmap
from dBitmapButton import dBitmapButton
from dButton import dButton
from dCheckBox import dCheckBox
from dColorDialog import dColorDialog
from dComboBox import dComboBox
from dCommandButton import dCommandButton
from dDateTextBox import dDateTextBox
from dDropdownList import dDropdownList
from dDialog import dDialog
from dDialog import dOkCancelDialog
from dEditBox import dEditBox
from dFileDialog import dFileDialog
from dFileDialog import dFolderDialog
from dFileDialog import dSaveDialog
from dFontDialog import dFontDialog
from dForm import dForm
from dForm import dToolForm
from dFormMain import dFormMain
from dGauge import dGauge
from dGrid import dGrid
from dGrid import dColumn
from dGridSizer import dGridSizer
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
from dPanel import dPanel
from dPanel import dScrollPanel
from dPageFrame import dPageFrame
from dPageFrame import dPageList
from dPageFrame import dPageSelect
from dPageNoTabs import dPageNoTabs
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
from dToggleButton import dToggleButton
from dTreeView import dTreeView
import dUICursors as dUICursors
import dShell


def callAfter(fnc, *args, **kwargs):
	"""There are times when this functionality is needed when creating UI
	code. This function simply wraps the wx.CallAfter function so that 
	developers do not need to use wx code in their apps.
	"""
	wx.CallAfter(fnc, *args, **kwargs)
	
	
def continueEvent(evt):
	evt.Skip()
	
def discontinueEvent(evt):
	evt.Skip(False)
	
def getEventData(wxEvt):
	ed = {}

	if isinstance(wxEvt, (wx.KeyEvent, wx.MouseEvent, wx.TreeEvent,
			wx.CommandEvent, wx.CloseEvent, wx.grid.GridEvent,
			wx.grid.GridSizeEvent) ):
		
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
		
	if isinstance(wxEvt, (wx.KeyEvent, wx.MouseEvent) ):
		ed["mousePosition"] = wxEvt.GetPositionTuple()
		ed["altDown"] = wxEvt.AltDown()
		ed["commandDown"] = wxEvt.CmdDown()
		ed["controlDown"] = wxEvt.ControlDown()
		ed["metaDown"] = wxEvt.MetaDown()
		ed["shiftDown"] = wxEvt.ShiftDown()
		if isinstance(wxEvt, wx.MouseEvent):
			ed["mouseDown"] = wxEvt.Dragging()

	if isinstance(wxEvt, wx.KeyEvent):
		ed["keyCode"] = wxEvt.KeyCode()
		ed["rawKeyCode"] = wxEvt.GetRawKeyCode()
		ed["rawKeyFlags"] = wxEvt.GetRawKeyFlags()
		ed["unicodeChar"] = wxEvt.GetUniChar()
		ed["unicodeKey"] = wxEvt.GetUnicodeKey()
		ed["hasModifiers"] = wxEvt.HasModifiers()
		try:
			if wx.Platform == "__WXMAC__":
				ed["keyChar"] = chr(wxEvt.GetKeyCode())
			else:	
				ed["keyChar"] = chr(wxEvt.GetRawKeyCode())
		except (ValueError, OverflowError):
			ed["keyChar"] = None

	if isinstance(wxEvt, wx.CloseEvent):
		ed["force"] = not wxEvt.CanVeto()
		
	if isinstance(wxEvt, wx.TreeEvent):
		tree = wxEvt.GetEventObject()
		sel = tree.Selection
		ed["selectedNode"] = sel
		if isinstance(sel, list):
			ed["selectedCaption"] = ", ".join([ss.Caption for ss in sel])
		else:
			ed["selectedCaption"] = tree.Selection.Caption
	
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
		ed["rowOrCol"] = wxEvt.GetRowOrCol()
		ed["position"] = wxEvt.GetPosition()
		ed["altDown"] = wxEvt.AltDown()
		ed["controlDown"] = wxEvt.ControlDown()
		ed["metaDown"] = wxEvt.MetaDown()
		ed["shiftDown"] = wxEvt.ShiftDown()
		try:
			# Don't think this is implemented yet
			ed["commandDown"] = wxEvt.CmdDown()
		except: pass
	
	return ed
	
	
def getMouseObject():
	return wx.FindWindowAtPoint(wx.GetMousePosition())


def getString(message="Please enter a string:", caption="Dabo",	defaultValue=""):
	dlg = wx.TextEntryDialog(None, message, caption, defaultValue)
	retVal = dlg.ShowModal()
	if retVal in (wx.ID_YES, wx.ID_OK):
		val = dlg.GetValue()
	else:
		val = None
	dlg.Destroy()
	return val


# For convenience, make it so one can call dabo.ui.stop("Can't do that")
# instead of having to type dabo.ui.dMessageBox.stop("Can't do that")
areYouSure = dMessageBox.areYouSure
stop = dMessageBox.stop
info = dMessageBox.info


def getColor(color=None):
	ret = None
	dlg = dColorDialog(None, color)
	if dlg.show() == k.DLG_OK:
		ret = dlg.getColor()
	dlg.release()
	return ret


def getFont(font=None):
	ret = None
	dlg = dFontDialog(None, font)
	if dlg.show() == k.DLG_OK:
		ret = dlg.getFont()
	dlg.release()
	return ret


def _getPath(cls, **kwargs):
	ret = None
	fd = cls(parent=None, **kwargs)
	if fd.show() == k.DLG_OK:
		ret = fd.Path
	fd.release()
	return ret

def getFile(*args, **kwargs):
	wc = _getWild(*args)
	return _getPath(dFileDialog, wildcard=wc, **kwargs)

def getSaveAs(*args, **kwargs):
	if not kwargs.has_key("message"):
		kwargs["message"] = "Save to:"
	if kwargs.has_key("wildcard"):
		args = list(args)
		args.append(kwargs["wildcard"])
	kwargs["wildcard"] = _getWild(*args)
	return _getPath(dSaveDialog, **kwargs)

def getFolder(message="Choose a folder", defaultPath="", wildcard="*"):
	return _getPath(dFolderDialog, message=message, defaultPath=defaultPath, 
			wildcard=wildcard)

def _getWild(*args):
	ret = "*"
	if args:
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
				fDesc = "Dabo FileSpec Files (*.fsxml)|*.fsxml"
			elif a == "cnxml":
				fDesc = "Dabo Connection Files (*.cnxml)|*.cnxml"
			else:
				if a in fileDict:
					fDesc = tmplt % (fileDict[a], a, a)
				else:
					fDesc = "%s files (*.%s)|*.%s" % (a.upper(), a, a)
			arglist.append(fDesc)
		ret = "|".join(arglist)
	return ret


def sortList(chc, Caption=""):
	"""Wrapper function for the list sorting dialog. Accepts a list,
	and returns the sorted list if the user clicks 'OK'. If they cancel
	out, the original list is returned.
	"""
	from dabo.ui.dialogs.SortingForm import SortingForm
	ret = chc
	sf = SortingForm(None, Choices=list(chc))
	if Caption:
		sf.Caption = Caption
	if sf.show() == k.DLG_OK:
		ret = sf.Choices
	sf.release()
	return ret


def browse(dataSource):
	"""Given a data source, a form with a grid containing the data
	is created and displayed. If the source is a Dabo cursor object, 
	its getDataSet() method will be called to extract the data.
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
	
	browseForm = dabo.ui.dForm(None, Caption=cap)
	grd = dGrid(browseForm)
	grd.buildFromDataSet(dataSet)
	browseForm.Sizer.append(grd, 1, "x")
	browseForm.layout()
	browseForm.show()
	# This will allow you to optionally manage the grid and form
	return browseForm, grd


def fontMetric(txt=None, wind=None, face=None, size=None, bold=None,
		italic=None):
	"""Calculate the width and height of the given text using the supplied
	font information. If any font parameters are missing, they are taken 
	from the specified window, or, if no window is specified, the currently
	active form. If no form is active, the app's MainForm is used.
	"""
	if wind is None:
		wind = dabo.dAppRef.ActiveForm
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
	
	dc = wx.ClientDC(wind)
	dc.SetFont(fnt)
	return dc.GetTextExtent(txt)

def getBitmap(name):
	"""wxPython comes with several built-in bitmaps for common icons. 
	This wraps the procedure for generating these bitmaps. If a name is
	passed for which there is no icon, None is returned. 
	NOTE: this returns a raw bitmap, not a dabo.ui.dBitmap object.
	"""
	ret = None
	constants = {"addbookmark" : wx.ART_ADD_BOOKMARK,
		"button" : wx.ART_BUTTON,
		"cd" : wx.ART_CDROM,
		"cdrom" : wx.ART_CDROM,
		"commondialog" : wx.ART_CMN_DIALOG,
		"dialog" : wx.ART_CMN_DIALOG,
		"copy" : wx.ART_COPY,
		"cross" : wx.ART_CROSS_MARK,
		"crossmark" : wx.ART_CROSS_MARK,
		"cut" : wx.ART_CUT,
		"delete" : wx.ART_DELETE,
		"delbookmark" : wx.ART_DEL_BOOKMARK,
		"error" : wx.ART_ERROR,
		"exe" : wx.ART_EXECUTABLE_FILE,
		"exefile" : wx.ART_EXECUTABLE_FILE,
		"open" : wx.ART_FILE_OPEN,
		"save" : wx.ART_FILE_SAVE,
		"saveas" : wx.ART_FILE_SAVE_AS,
		"find" : wx.ART_FIND,
		"findreplace" : wx.ART_FIND_AND_REPLACE,
		"floppy" : wx.ART_FLOPPY,
		"folder" : wx.ART_FOLDER,
		"folderopen" : wx.ART_FOLDER_OPEN,
		"frame" : wx.ART_FRAME_ICON,
		"frameicon" : wx.ART_FRAME_ICON,
		"back" : wx.ART_GO_BACK,
		"directoryup" : wx.ART_GO_DIR_UP,
		"down" : wx.ART_GO_DOWN,
		"forward" : wx.ART_GO_FORWARD,
		"home" : wx.ART_GO_HOME,
		"parent" : wx.ART_GO_TO_PARENT,
		"up" : wx.ART_GO_UP,
		"hd" : wx.ART_HARDDISK,
		"harddisk" : wx.ART_HARDDISK,
		"help" : wx.ART_HELP,
		"helpbook" : wx.ART_HELP_BOOK,
		"helpbrowser" : wx.ART_HELP_BROWSER,
		"helpfolder" : wx.ART_HELP_FOLDER,
		"helppage" : wx.ART_HELP_PAGE,
		"helpsettings" : wx.ART_HELP_SETTINGS,
		"helpsidepanel" : wx.ART_HELP_SIDE_PANEL,
		"info" : wx.ART_INFORMATION,
		"information" : wx.ART_INFORMATION,
		"listview" : wx.ART_LIST_VIEW,
		"menu" : wx.ART_MENU,
		"messagebox" : wx.ART_MESSAGE_BOX,
		"missingimage" : wx.ART_MISSING_IMAGE,
		"new" : wx.ART_NEW,
		"newdir" : wx.ART_NEW_DIR,
		"normalfile" : wx.ART_NORMAL_FILE,
		"file" : wx.ART_NORMAL_FILE,
		"other" : wx.ART_OTHER,
		"paste" : wx.ART_PASTE,
		"print" : wx.ART_PRINT,
		"question" : wx.ART_QUESTION,
		"quit" : wx.ART_QUIT,
		"redo" : wx.ART_REDO,
		"removable" : wx.ART_REMOVABLE,
		"reportview" : wx.ART_REPORT_VIEW,
		"tickmark" : wx.ART_TICK_MARK,
		"tip" : wx.ART_TIP,
		"toolbar" : wx.ART_TOOLBAR,
		"undo" : wx.ART_UNDO,
		"warning" : wx.ART_WARNING}
	try:
		const = constants[name.lower()]
	except KeyError:
		const = None
	if const:
		ret = wx.ArtProvider.GetBitmap(const)
	return ret

	
	
