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
from dFormMain import dFormMain
from dGauge import dGauge
from dGrid import dGrid
from dGridSizer import dGridSizer
import dIcons
from dImage import dImage
import dKeys
from dLabel import dLabel
from dLine import dLine
from dListbook import dListbook
from dListBox import dListBox
from dListControl import dListControl
from dBaseMenuBar import dBaseMenuBar
from dMenuBar import dMenuBar
from dMenu import dMenu
from dMenuItem import *
from dRadioGroup import dRadioGroup
from dPanel import dPanel
from dPanel import dScrollPanel
from dPageFrame import dPageFrame
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
from dToggleButton import dToggleButton
from dTreeView import dTreeView
import dUICursors as dUICursors

import dShell


# Tell Dabo Designer what classes to put in the selection menu:
__dClasses = [dBox, dBitmapButton, dButton, dCheckBox, dComboBox, 
		dDateTextBox, dDropdownList, dEditBox, dForm, dGauge, dGrid, 
		dLabel, dLine, dListbook, dListBox, dListControl, dRadioGroup,
		dPanel, dScrollPanel, dPageFrame, dPage, dSlider, dSpinner,  
		dSplitForm, dSplitter, dTextBox, dTimer, dToggleButton, dTreeView]

# These are the classes that can be added to any container class in 
# the Designer.
__dControlClasses = [dBox, dBitmapButton, dButton, dCheckBox, 
		dComboBox, dDateTextBox, dDropdownList, dEditBox, dGauge, 
		dGrid, dLabel, dLine, dListbook, dListBox, dListControl, dRadioGroup, 
		dPanel, dScrollPanel, dPageFrame, dPage, dSlider, dSpinner, dSplitter, 
		dTextBox, dTimer, dToggleButton, dTreeView]

daboDesignerClasses = []
for __classRef in __dClasses:
	__classDict = {}
	__classDict["class"] = __classRef
	__classDict["name"] = __classRef.__name__
	__classDict["prompt"] = "%s&%s" % (__classRef.__name__[0], __classRef.__name__[1:])
	__classDict["topLevel"] = __classRef.__name__.find("Form") >= 0
	__classDict["doc"] = __classRef.__doc__
	daboDesignerClasses.append(__classDict)

daboDesignerControls = []
for __classRef in __dControlClasses:
	__classDict = {}
	__classDict["class"] = __classRef
	__classDict["name"] = __classRef.__name__
	__classDict["prompt"] = "%s&%s" % (__classRef.__name__[0], __classRef.__name__[1:])
	__classDict["doc"] = __classRef.__doc__
	daboDesignerControls.append(__classDict)

propsToShowInDesigner = ("Alignment", "AskToSave", "AutoResize", 
		"AutoSize", "BackColor", "BaseClass", "BorderResizable", "BorderStyle", 
		"Bottom", "CancelButton", "Caption", "Centered", "Choices", "Class", 
		"DataField", "DataSource", "DefaultButton", "DownPicture", "Enabled", 
		"FocusPicture", "Font", "FontBold", "FontDescription", "FontFace", 
		"FontInfo", "FontItalic", "FontSize", "FontUnderline", "ForeColor", 
		"Height", "HelpContextText", "Icon", "IconBundle", "Interval", "Left", 
		"Max", "MaxElements", "Min", "MinPanelSize", "Modal", 
		"MousePointer", "MultipleSelect", "Name", "Orientation", "PageClass", 
		"PageCount", "PasswordEntry", "Picture", "Position", "Range", "ReadOnly", 
		"Right", "SashPosition", "SaveRestoreValue", "SelectOnEntry", 
		"ShowCaption", "ShowCloseButton", "ShowLabels", "ShowMaxButton", 
		"ShowMinButton", "ShowStatusBar", "ShowSystemMenu", "Size", "Sizer", 
		"SpinnerArrowKeys", "SpinnerWrap", "StringValue", "SuperClass", 
		"TabPosition", "TinyTitleBar", "ToolTipText", "Top", "UserValue", "Value", 
		"ValueMode", "Visible", "Width", "WindowState")

propsToEditInDesigner = ("Alignment", "AskToSave", "AutoResize", "AutoSize", 
		"BackColor", "BorderResizable", "BorderStyle", "Bottom", "CancelButton", 
		"Caption", "Centered", "Choices", "DataField", "DataSource", "DefaultButton", 
		"DownPicture", "Enabled", "FocusPicture", "Font", "FontBold", "FontFace", 
		"FontItalic", "FontSize", "FontUnderline", "ForeColor", "Height", 
		"HelpContextText", "Icon", "IconBundle", "Interval", "Left", "Max", 
		"MaxElements", "Min", "MinPanelSize", "Modal", "MultipleSelect", "Name", 
		"Orientation", "PageClass", "PageCount", "PasswordEntry", "Picture", 
		"Range", "ReadOnly", "Right", "SashPosition", "SaveRestoreValue", 
		"SelectOnEntry", "ShowCaption", "ShowCloseButton", "ShowLabels", 
		"ShowMaxButton", "ShowMinButton", "ShowStatusBar", "ShowSystemMenu", 
		"SpinnerArrowKeys", "SpinnerWrap", "TabPosition", "TinyTitleBar", 
		"ToolTipText", "Top", "UserValue", "Value", "ValueMode", "Visible", "Width", 
		"WindowState")


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
		ed["selectedNode"] = tree.Selection
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
	wc = _getWild(*args)
	return _getPath(dSaveDialog, wildcard=wc, **kwargs)

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
	ret = chc
	sf = dabo.ui.dialogs.SortingForm(None, Choices=list(chc))
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
	if type(dataSource) not in (list, tuple):
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

