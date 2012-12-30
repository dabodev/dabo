# -*- coding: utf-8 -*-
import wx, dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlItemMixin as dcm
from dabo.dLocalize import _


class dDropdownList(dcm.dControlItemMixin, wx.Choice):
	"""
	Creates a dropdown list, which allows the user to select one item.

	This is a very simple control, suitable for choosing from one of a handful
	of items. Only one column can be displayed. A more powerful, flexible
	control for all kinds of lists is dListControl, but dDropdownList does
	suffice for simple needs.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dDropdownList
		self._choices = []

		preClass = wx.PreChoice
		dcm.dControlItemMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def _initEvents(self):
		super(dDropdownList, self)._initEvents()
		self.Bind(wx.EVT_CHOICE, self._onWxHit)


class _dDropdownList_test(dDropdownList):
	def initProperties(self):
		# Simulating a database
		developers = ({"lname": "McNett", "fname": "Paul", "iid": 42},
			{"lname": "Leafe", "fname": "Ed", "iid": 23})

		choices = []
		keys = {}
		for developer in developers:
			choices.append("%s %s" % (developer['fname'], developer['lname']))
			keys[developer["iid"]] = len(choices) - 1

		self.Choices = choices
		self.Keys = keys
		self.ValueMode = "key"


	def onValueChanged(self, evt):
		print "KeyValue: ", self.KeyValue
		print "PositionValue: ", self.PositionValue
		print "StringValue: ", self.StringValue
		print "Value: ", self.Value


if __name__ == "__main__":
	import test
	test.Test().runTest(_dDropdownList_test)
