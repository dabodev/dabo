""" Dabo Base Classes for wx

This is a subpackage of Dabo, and contains all the base classes of the 
framework, both visual and non-visual, for the wx ui.
"""

# Import into private namespace:
import dEvents
import dMessageBox
import dIcons

# Import into public namespace:
from dAbout import dAbout
from dCheckBox import dCheckBox
from dComboBox import dComboBox
from dCommandButton import dCommandButton
from dControlMixin import dControlMixin
from dDataControlMixin import dDataControlMixin
from dEditBox import dEditBox
from dForm import dForm
from dFormDataNav import dFormDataNav
from dFormMain import dFormMain
from dFormMixin import dFormMixin
from dGauge import dGauge
from dGrid import dGrid
from dLabel import dLabel
from dMainMenuBar import dMainMenuBar
from dMenuBar import dMenuBar
from dMenu import dMenu
from dRadioGroup import dRadioGroup
from dPanel import dPanel
from dPanel import dScrollPanel
from dPageFrame import dPageFrame
from dPage import dPage
from dSlider import dSlider
from dSpinner import dSpinner
from dTextBox import dTextBox
from dTreeView import dTreeView

# Tell Dabo Designer what classes to put in the selection menu:
__dClasses = [dCheckBox, dCommandButton, dEditBox, dForm,
		dFormDataNav, dFormMain, dGauge, dLabel, dPanel, 
		dPageFrame, dPage, dRadioGroup, dScrollPanel, dSlider, 
		dSpinner, dTextBox]

daboDesignerClasses = []
for __classRef in __dClasses:
	__classDict = {}
	__classDict['class'] = __classRef
	__classDict['name'] = __classRef.__name__
	__classDict['prompt'] = "%s&%s" % (__classRef.__name__[0], __classRef.__name__[1:])
	__classDict['topLevel'] = __classRef.__name__.find('Form') >= 0
	__classDict['doc'] = __classRef.__doc__
	daboDesignerClasses.append(__classDict)
