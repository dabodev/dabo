import wx
import dabo.ui
from uiApp import uiApp

uiType = {'shortName': 'wx', 'moduleName': 'uiwx', 'longName': 'wxPython'}

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
from dAbout import dAbout
from dBox import dBox
from dBitmapButton import dBitmapButton
from dCheckBox import dCheckBox
from dComboBox import dComboBox
from dCommandButton import dCommandButton
from dDataNavForm import dDataNavForm
from dDateTextBox import dDateTextBox
from dDropdownList import dDropdownList
from dDialog import dDialog
from dEditBox import dEditBox
from dForm import dForm
from dFormDataNav import dFormDataNav
from dFormMain import dFormMain
from dGauge import dGauge
from dGrid import dGrid
from dGridSizer import dGridSizer
from dGridDataNav import dGridDataNav
from dLabel import dLabel
from dLine import dLine
from dListbook import dListbook
from dListBox import dListBox
from dLogin import dLogin
from dMainMenuBar import dMainMenuBar
from dMenuBar import dMenuBar
from dMenu import dMenu
from dRadioGroup import dRadioGroup
from dPanel import dPanel
from dPanel import dScrollPanel
from dPageFrame import dPageFrame
from dPage import dPage
from dSizer import dSizer
from dBorderSizer import dBorderSizer
from dSlider import dSlider
from dSpinner import dSpinner
from dTextBox import dTextBox
from dTimer import dTimer
from dToggleButton import dToggleButton
from dTreeView import dTreeView

from getMouseObject import getMouseObject

import dShell


# Tell Dabo Designer what classes to put in the selection menu:
__dClasses = [dBitmapButton, dBox, dCheckBox, dCommandButton,  
		dDateTextBox, dDropdownList, dEditBox, dForm, dFormDataNav, dFormMain, 
		dGauge, dLabel, dLine, dListbook, dPanel, dPageFrame, dPage, 
		dRadioGroup, dScrollPanel, dSlider, dSpinner, dTextBox, dToggleButton]

daboDesignerClasses = []
for __classRef in __dClasses:
	__classDict = {}
	__classDict['class'] = __classRef
	__classDict['name'] = __classRef.__name__
	__classDict['prompt'] = "%s&%s" % (__classRef.__name__[0], __classRef.__name__[1:])
	__classDict['topLevel'] = __classRef.__name__.find('Form') >= 0
	__classDict['doc'] = __classRef.__doc__
	daboDesignerClasses.append(__classDict)


def continueEvent(evt):
	evt.Skip()
	
def discontinueEvent(evt):
	evt.Skip(False)
	
def getEventData(wxEvt):
	ed = {}

	if isinstance(wxEvt, wx.KeyEvent) or isinstance(wxEvt, wx.MouseEvent) or \
			isinstance(wxEvt, wx.CommandEvent):
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
