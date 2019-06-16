# -*- coding: utf-8 -*-
import dabo.ui
from dabo.dLocalize import _
import dabo.dEvents as dEvents

dListControl = dabo.import_ui_name("dListControl")
dPanel = dabo.import_ui_name("dPanel")
dSizer = dabo.import_ui_name("dSizer")


class MethodSheet(dPanel):
    def afterInit(self):
        self._methodList = dListControl(self, MultipleSelect=False)
        self._methodList.bindEvent(dEvents.Hit, self.onList)
        sz = self.Sizer = dSizer("v")
        sz.append1x(self._methodList)
        self._methodList.addColumn(_("Event/Method"))


    def onList(self, evt):
        self.Application.editCode(self._methodList.StringValue)


    def _getMethodList(self):
        return self._methodList


    MethodList = property(_getMethodList, None, None,
            _("Reference to the method list control  (dListControl)"))
