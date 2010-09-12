# -*- coding: utf-8 -*-
import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents
if __name__ == "__main__":
	dabo.ui.loadUI("wx")


class MethodSheet(dabo.ui.dPanel):
	def afterInit(self):
		self._methodList = dabo.ui.dListControl(self, MultipleSelect=False)
		self._methodList.bindEvent(dEvents.Hit, self.onList)
		sz = self.Sizer = dabo.ui.dSizer("v")
		sz.append1x(self._methodList)
		self._methodList.addColumn(_("Event/Method"))


	def onList(self, evt):
		self.Application.editCode(self._methodList.StringValue)


	def _getMethodList(self):
		return self._methodList


	MethodList = property(_getMethodList, None, None,
			_("Reference to the method list control  (dListControl)"))
