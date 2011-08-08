# -*- coding: utf-8 -*-
import dabo
import dabo.ui
from uiApp import uiApp

dabo.log.info("The Tkinter module is experimental only, and doesn't work. You've been warned.")
uiType = {'shortName': 'tk', 'moduleName': 'uitk', 'longName': 'Tkinter'}

_uiApp = None

# Import dPemMixin first, and then manually put into dabo.ui module. This is
# because dControlMixin, which is in dabo.ui, descends from dPemMixin, which
# is in dabo.ui.uitk. Must also do this for dControlMixin.
from dPemMixin import dPemMixin
dabo.ui.dPemMixin = dPemMixin
from dControlMixin import dControlMixin
dabo.ui.dControlMixin = dControlMixin

# Import into public namespace:
#from dAbout import dAbout
from dCheckBox import dCheckBox
#from dComboBox import dComboBox
#from dCommandButton import dCommandButton
#from dDateControl import dDateControl
#from dDialog import dDialog
#from dEditBox import dEditBox
#from dForm import dForm
#from dFormDataNav import dFormDataNav
from dFormMain import dFormMain
#from dGauge import dGauge
#from dGridDataNav import dGridDataNav
from dLabel import dLabel
#from dListbook import dListbook
#from dLogin import dLogin
#from dMainMenuBar import dMainMenuBar
#from dMenuBar import dMenuBar
#from dMenu import dMenu
#from dRadioGroup import dRadioGroup
from dPanel import dPanel
#from dPanel import dScrollPanel
#from dPageFrame import dPageFrame
#from dPage import dPage
#from dSlider import dSlider
#from dSpinner import dSpinner
#from dTextBox import dTextBox
#from dTreeView import dTreeView

# Tell Dabo Designer what classes to put in the selection menu:
#__dClasses = [dCheckBox, dCommandButton, dDateControl, dEditBox, dForm,
#		dFormDataNav, dFormMain, dGauge, dLabel, dListbook, dPanel,
#		dPageFrame, dPage, dRadioGroup, dScrollPanel, dSlider,
#		dSpinner, dTextBox]

#daboDesignerClasses = []
#for __classRef in __dClasses:
#	__classDict = {}
#	__classDict['class'] = __classRef
#	__classDict['name'] = __classRef.__name__
#	__classDict['prompt'] = "%s&%s" % (__classRef.__name__[0], __classRef.__name__[1:])
#	__classDict['topLevel'] = __classRef.__name__.find('Form') >= 0
#	__classDict['doc'] = __classRef.__doc__
#	daboDesignerClasses.append(__classDict)


def continueEvent(evt):
	# Tkinter determines whether to let an event continue propagation based on whether
	# the string "break" is returned from the event handler or not.
	return None

def discontinueEvent(evt):
	# Tkinter determines whether to let an event continue propagation based on whether
	# the string "break" is returned from the event handler or not.
	return "break"


def getEventData(uiEvent):
	ed = {}
	if isinstance(uiEvent, dabo.dEvents.dEvent):
		return ed
	ed["mousePosition"] = (uiEvent.x, uiEvent.y)

	if "shift_" in uiEvent.keysym.lower():
		ed["shiftDown"] = True
	else:
		ed["shiftDown"] = False

	if "alt_" in uiEvent.keysym.lower():
		ed["altDown"] = True
	else:
		ed["altDown"] = False

	if "control_" in uiEvent.keysym.lower():
		ed["controlDown"] = True
	else:
		ed["controlDown"] = False

	#ed["commandDown"] = wxEvt.CmdDown()
	#ed["metaDown"] = wxEvt.MetaDown()
	ed["keyCode"] = uiEvent.keysym_num
	ed["rawKeyCode"] = uiEvent.keycode
	if len(uiEvent.char) == 0:
		ed["keyChar"] = None
	else:
		ed["keyChar"] = uiEvent.char
	#ed["rawKeyFlags"] = uiEvent.keysym_num
	#ed["unicodeChar"] = wxEvt.GetUniChar()
	#ed["unicodeKey"] = wxEvt.GetUnicodeKey()
	#ed["hasModifiers"] = wxEvt.HasModifiers()
	return ed


def getUiApp(app, uiAppClass=None, callback=None, forceNew=None):
	"""This returns an instance of uiApp. If one is already running, that
	instance is returned. Otherwise, a new instance is created.
	"""
	ret = _uiApp
	if ret is None:
		ret = uiApp(app, callback)
	else:
		# existing app; fire the callback, if any
		if callback is not None:
			callback()
	return ret


