from uiApp import uiApp

uiType = {'shortName': 'tk', 'moduleName': 'uitk', 'longName': 'Tkinter'}


# Copied from the uiwx package. Uncomment classes as they get implemented.

# Import into public namespace:
#from dAbout import dAbout
#from dCheckBox import dCheckBox
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
#from dLabel import dLabel
#from dListbook import dListbook
#from dLogin import dLogin
#from dMainMenuBar import dMainMenuBar
#from dMenuBar import dMenuBar
#from dMenu import dMenu
#from dRadioGroup import dRadioGroup
#from dPanel import dPanel
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


def getEventData(uiEvent):
	ed = {}
	ed["mousePosition"] = (uiEvent.x, uiEvent.y)
	return ed