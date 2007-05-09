# -*- coding: utf-8 -*-
import warnings
from dabo.dLocalize import _
from Form import Form
from Grid import Grid
from Page import Page, SelectPage, EditPage, BrowsePage, SortLabel
from Page import IGNORE_STRING, SelectionOpDropdown
from PageFrame import PageFrameMixin, PageFrame
from Bizobj import Bizobj

warnings.warn(_("This version of the datanav framework is deprecated; please "
		"run the current AppWizard to regenerate your application using the datanav2 "
		"framework."), DeprecationWarning, 1)
