# -*- coding: utf-8 -*-
from dabo.dLocalize import _


class QryOperatorEnum:
    __slots__ = ()
    AFTER = _("After")
    BEFORE = _("Before")
    BEGINS = _("Begins With")
    BETWEEN = _("Between")
    CONTAINS = _("Contains")
    EQUAL = _("Equals")
    FALSE = _("Is False")
    GREATER = _("Greater than")
    GREATEREQUAL = _("Greater than/Equal to")
    IGNORE = _("-ignore-")
    IS = _("Is")
    LESS = _("Less than")
    LESSEQUAL = _("Less than/Equal to")
    MATCH = _("Matches Words")
    ONBEFORE = _("On or Before")
    ONAFTER = _("On or After")
    TRUE = _("Is True")


QRY_OPERATOR = QryOperatorEnum()

# To achieve compatibility with existing code.
IGNORE_STRING = QRY_OPERATOR.IGNORE

from .Bizobj import Bizobj
from .Form import Form
from .Grid import Grid
from .Page import BrowsePage, EditPage, Page, SelectionOpDropdown, SelectPage, SortLabel
from .PageFrame import PageFrame, PageFrameMixin
