# -*- coding: utf-8 -*-
from .. import ui
from ..dLocalize import _
from .. import events

from ..ui import dListControl
from ..ui import dPanel
from ..ui import dSizer


class MethodSheet(dPanel):
    def afterInit(self):
        self._methodList = dListControl(self, MultipleSelect=False)
        self._methodList.bindEvent(events.Hit, self.onList)
        sz = self.Sizer = dSizer("v")
        sz.append1x(self._methodList)
        self._methodList.addColumn(_("Event/Method"))

    def onList(self, evt):
        self.Application.editCode(self._methodList.StringValue)

    def _getMethodList(self):
        return self._methodList

    MethodList = property(
        _getMethodList,
        None,
        None,
        _("Reference to the method list control  (dListControl)"),
    )
