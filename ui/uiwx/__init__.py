import wx
import dabo.ui
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

# Import into public namespace:
from dBox import dBox
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
from dFileDialog import dSaveDialog
from dForm import dForm
from dFormMain import dFormMain
from dGauge import dGauge
from dGrid import dGrid
from dGridSizer import dGridSizer
import dIcons
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
from dTextBox import dTextBox
from dTimer import dTimer
from dToggleButton import dToggleButton
from dTreeView import dTreeView
import dUICursors as dUICursors

from getMouseObject import getMouseObject
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

	if isinstance(wxEvt, wx.KeyEvent) or isinstance(wxEvt, wx.MouseEvent) or \
			isinstance(wxEvt, wx.CommandEvent):
		
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
		
	if isinstance(wxEvt, wx.KeyEvent) or isinstance(wxEvt, wx.MouseEvent):
		ed["mousePosition"] = wxEvt.GetPositionTuple()
		ed["altDown"] = wxEvt.AltDown()
		ed["commandDown"] = wxEvt.CmdDown()
		ed["controlDown"] = wxEvt.ControlDown()
		ed["metaDown"] = wxEvt.MetaDown()
		ed["shiftDown"] = wxEvt.ShiftDown()

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

	return ed
