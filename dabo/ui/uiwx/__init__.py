import sys
import os
######################################################
# Very first thing: check for proper wxPython build:
_failedLibs = []
for lib in ("wx", "wx.stc", "wx.gizmos"):  ## note: may need wx.animate as well
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
from dFormMixin import dFormMixin
dabo.ui.dFormMixin = dFormMixin
from dSizerMixin import dSizerMixin
dabo.ui.dSizerMixin = dSizerMixin

# Import into public namespace:
from dBox import dBox
from dBitmap import dBitmap
from dBitmapButton import dBitmapButton
from dButton import dButton
from dCheckBox import dCheckBox
from dColorDialog import dColorDialog
from dComboBox import dComboBox
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

artConstants = {}
if hasattr(wx, "ART_ADD_BOOKMARK"):
	artConstants["addbookmark"] = wx.ART_ADD_BOOKMARK
if hasattr(wx, "ART_BUTTON"):
	artConstants["button"] = wx.ART_BUTTON
if hasattr(wx, "ART_CDROM"):
	artConstants["cd"] = wx.ART_CDROM
if hasattr(wx, "ART_CDROM"):
	artConstants["cdrom"] = wx.ART_CDROM
if hasattr(wx, "ART_CMN_DIALOG"):
	artConstants["commondialog"] = wx.ART_CMN_DIALOG
if hasattr(wx, "ART_CMN_DIALOG"):
	artConstants["dialog"] = wx.ART_CMN_DIALOG
if hasattr(wx, "ART_COPY"):
	artConstants["copy"] = wx.ART_COPY
if hasattr(wx, "ART_CROSS_MARK"):
	artConstants["cross"] = wx.ART_CROSS_MARK
if hasattr(wx, "ART_CROSS_MARK"):
	artConstants["crossmark"] = wx.ART_CROSS_MARK
if hasattr(wx, "ART_CUT"):
	artConstants["cut"] = wx.ART_CUT
if hasattr(wx, "ART_DELETE"):
	artConstants["delete"] = wx.ART_DELETE
if hasattr(wx, "ART_DEL_BOOKMARK"):
	artConstants["delbookmark"] = wx.ART_DEL_BOOKMARK
if hasattr(wx, "ART_ERROR"):
	artConstants["error"] = wx.ART_ERROR
if hasattr(wx, "ART_EXECUTABLE_FILE"):
	artConstants["exe"] = wx.ART_EXECUTABLE_FILE
if hasattr(wx, "ART_EXECUTABLE_FILE"):
	artConstants["exefile"] = wx.ART_EXECUTABLE_FILE
if hasattr(wx, "ART_FILE_OPEN"):
	artConstants["open"] = wx.ART_FILE_OPEN
if hasattr(wx, "ART_FILE_SAVE"):
	artConstants["save"] = wx.ART_FILE_SAVE
if hasattr(wx, "ART_FILE_SAVE_AS"):
	artConstants["saveas"] = wx.ART_FILE_SAVE_AS
if hasattr(wx, "ART_FIND"):
	artConstants["find"] = wx.ART_FIND
if hasattr(wx, "ART_FIND_AND_REPLACE"):
	artConstants["findreplace"] = wx.ART_FIND_AND_REPLACE
if hasattr(wx, "ART_FLOPPY"):
	artConstants["floppy"] = wx.ART_FLOPPY
if hasattr(wx, "ART_FOLDER"):
	artConstants["folder"] = wx.ART_FOLDER
if hasattr(wx, "ART_FOLDER_OPEN"):
	artConstants["folderopen"] = wx.ART_FOLDER_OPEN
if hasattr(wx, "ART_FRAME_ICON"):
	artConstants["frame"] = wx.ART_FRAME_ICON
if hasattr(wx, "ART_FRAME_ICON"):
	artConstants["frameicon"] = wx.ART_FRAME_ICON
if hasattr(wx, "ART_GO_BACK"):
	artConstants["back"] = wx.ART_GO_BACK
if hasattr(wx, "ART_GO_DIR_UP"):
	artConstants["directoryup"] = wx.ART_GO_DIR_UP
if hasattr(wx, "ART_GO_DOWN"):
	artConstants["down"] = wx.ART_GO_DOWN
if hasattr(wx, "ART_GO_FORWARD"):
	artConstants["forward"] = wx.ART_GO_FORWARD
if hasattr(wx, "ART_GO_HOME"):
	artConstants["home"] = wx.ART_GO_HOME
if hasattr(wx, "ART_GO_TO_PARENT"):
	artConstants["parent"] = wx.ART_GO_TO_PARENT
if hasattr(wx, "ART_GO_UP"):
	artConstants["up"] = wx.ART_GO_UP
if hasattr(wx, "ART_HARDDISK"):
	artConstants["hd"] = wx.ART_HARDDISK
if hasattr(wx, "ART_HARDDISK"):
	artConstants["harddisk"] = wx.ART_HARDDISK
if hasattr(wx, "ART_HELP"):
	artConstants["help"] = wx.ART_HELP
if hasattr(wx, "ART_HELP_BOOK"):
	artConstants["helpbook"] = wx.ART_HELP_BOOK
if hasattr(wx, "ART_HELP_BROWSER"):
	artConstants["helpbrowser"] = wx.ART_HELP_BROWSER
if hasattr(wx, "ART_HELP_FOLDER"):
	artConstants["helpfolder"] = wx.ART_HELP_FOLDER
if hasattr(wx, "ART_HELP_PAGE"):
	artConstants["helppage"] = wx.ART_HELP_PAGE
if hasattr(wx, "ART_HELP_SETTINGS"):
	artConstants["helpsettings"] = wx.ART_HELP_SETTINGS
if hasattr(wx, "ART_HELP_SIDE_PANEL"):
	artConstants["helpsidepanel"] = wx.ART_HELP_SIDE_PANEL
if hasattr(wx, "ART_INFORMATION"):
	artConstants["info"] = wx.ART_INFORMATION
if hasattr(wx, "ART_INFORMATION"):
	artConstants["information"] = wx.ART_INFORMATION
if hasattr(wx, "ART_LIST_VIEW"):
	artConstants["listview"] = wx.ART_LIST_VIEW
if hasattr(wx, "ART_MENU"):
	artConstants["menu"] = wx.ART_MENU
if hasattr(wx, "ART_MESSAGE_BOX"):
	artConstants["messagebox"] = wx.ART_MESSAGE_BOX
if hasattr(wx, "ART_MISSING_IMAGE"):
	artConstants["missingimage"] = wx.ART_MISSING_IMAGE
if hasattr(wx, "ART_NEW"):
	artConstants["new"] = wx.ART_NEW
if hasattr(wx, "ART_NEW_DIR"):
	artConstants["newdir"] = wx.ART_NEW_DIR
if hasattr(wx, "ART_NORMAL_FILE"):
	artConstants["normalfile"] = wx.ART_NORMAL_FILE
if hasattr(wx, "ART_NORMAL_FILE"):
	artConstants["file"] = wx.ART_NORMAL_FILE
if hasattr(wx, "ART_OTHER"):
	artConstants["other"] = wx.ART_OTHER
if hasattr(wx, "ART_PASTE"):
	artConstants["paste"] = wx.ART_PASTE
if hasattr(wx, "ART_PRINT"):
	artConstants["print"] = wx.ART_PRINT
if hasattr(wx, "ART_QUESTION"):
	artConstants["question"] = wx.ART_QUESTION
if hasattr(wx, "ART_QUIT"):
	artConstants["quit"] = wx.ART_QUIT
if hasattr(wx, "ART_REDO"):
	artConstants["redo"] = wx.ART_REDO
if hasattr(wx, "ART_REMOVABLE"):
	artConstants["removable"] = wx.ART_REMOVABLE
if hasattr(wx, "ART_REPORT_VIEW"):
	artConstants["reportview"] = wx.ART_REPORT_VIEW
if hasattr(wx, "ART_TICK_MARK"):
	artConstants["tickmark"] = wx.ART_TICK_MARK
if hasattr(wx, "ART_TIP"):
	artConstants["tip"] = wx.ART_TIP
if hasattr(wx, "ART_TOOLBAR"):
	artConstants["toolbar"] = wx.ART_TOOLBAR
if hasattr(wx, "ART_UNDO"):
	artConstants["undo"] = wx.ART_UNDO
if hasattr(wx, "ART_WARNING"):
	artConstants["warning"] = wx.ART_WARNING


def callAfter(fnc, *args, **kwargs):
	"""There are times when this functionality is needed when creating UI
	code. This function simply wraps the wx.CallAfter function so that 
	developers do not need to use wx code in their apps.
	"""
	wx.CallAfter(fnc, *args, **kwargs)
	

def yieldUI(*args, **kwargs):
	"""Yield to other apps/messages."""
	wx.Yield(*args, **kwargs)	


def busyInfo(msg="Please wait...", *args, **kwargs):
	"""Display a message that the system is busy.

	To use this, assign the return value to a local object. but note that the 
	message will stay until the object is explicitly unbound. For example:

	bi = dabo.ui.busyInfo("Please wait while I count to 10000...")
	for i in range(10000):
		pass
	bi = None
"""
	return wx.BusyInfo(msg, *args, **kwargs)


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
		else:
			ed["selectedCaption"] = tree.Selection.Caption
	
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
	"""Returns a reference to the object below the mouse pointer
	at the moment the command is issued. Useful for interactive 
	development when testing changes to classes 'in the wild' of a 
	live application.
	"""
	return wx.FindWindowAtPoint(wx.GetMousePosition())


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
	if dlg.show() == k.DLG_OK:
		ret = dlg.getColor()
	dlg.release()
	return ret


def getFont(font=None):
	"""Displays the font selection dialog for the platform.
	Returns a font object that can be assigned to a control's
	Font property.
	"""
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
	"""Displays the file selection dialog for the platform.
	Returns the path to the selected file, or None if no selection
	was made.
	"""
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
	"""Displays the folder selection dialog for the platform.
	Returns the path to the selected folder, or None if no selection
	was made.
	"""
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
				fDesc = "Dabo FieldSpec Files (*.fsxml)|*.fsxml"
			elif a == "cnxml":
				fDesc = "Dabo Connection Files (*.cnxml)|*.cnxml"
			elif a == "rfxml":
				fDesc = "Dabo Report Format Files (*.rfxml)|*.rfxml"
			elif a == "cdxml":
				fDesc = "Dabo Class Designer Files (*.cdxml)|*.cdxml"
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


def createForm(srcFile, show=False):
	"""Pass in a .cdxml file from the Designer, and this will
	instantiate a form from that spec. Returns a reference
	to the newly-created form.
	"""
	frm = dForm(src=srcFile)
	if show:
		frm.show()
	return frm
	
	
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

	grd = dGrid(parent)
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
	
	if not isinstance(wind, dabo.ui.dForm):
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
	return ret
	

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
		# Create a list of the places to search for the image, with
		# the most likely choices first.
		paths = [val] + iconpaths + dabopaths
		# See if it's a standard icon
		for pth in paths:
			ret = dIcons.getIconBitmap(pth, noEmptyBmp=True)
			if ret:
				break
		if not ret:
			# See if it's a built-in graphic
			ret = getBitmap(val)
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
	
	
def getBitmap(name):
	"""wxPython comes with several built-in bitmaps for common icons. 
	This wraps the procedure for generating these bitmaps. If a name is
	passed for which there is no icon, None is returned. Different versions
	of wxPython contain different art constants, so each assignment is
	bracketed 
	NOTE: this returns a raw bitmap, not a dabo.ui.dBitmap object.
	"""
	ret = None
	try:
		const = artConstants[name.lower()]
	except KeyError:
		const = None
	if const:
		ret = wx.ArtProvider.GetBitmap(const)
	return ret

			
	
