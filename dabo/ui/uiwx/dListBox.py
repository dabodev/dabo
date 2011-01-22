# -*- coding: utf-8 -*-
import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlItemMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dListBox(dcm.dControlItemMixin, wx.ListBox):
	"""Creates a listbox, allowing the user to choose one or more items."""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dListBox
		self._choices = []

		preClass = wx.PreListBox
		dcm.dControlItemMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def _initEvents(self):
		super(dListBox, self)._initEvents()
		self.Bind(wx.EVT_LISTBOX, self._onWxHit)


	def clearSelections(self):
		for elem in self.GetSelections():
			self.SetSelection(elem, False)


	def selectAll(self):
		if self.MultipleSelect:
			for ii in xrange(self.Count):
				self.SetSelection(ii)


	def unselectAll(self):
		self.clearSelections()


	def invertSelections(self):
		"""Switch all the items from False to True, and vice-versa."""
		for ii in xrange(self.Count):
			if self.IsSelected(ii):
				self.Deselect(ii)
			else:
				self.SetSelection(ii)


	def _getMultipleSelect(self):
		return self._hasWindowStyleFlag(wx.LB_EXTENDED)
	def _setMultipleSelect(self, val):
		if bool(val):
			self._delWindowStyleFlag(wx.LB_SINGLE)
			self._addWindowStyleFlag(wx.LB_EXTENDED)
		else:
			self._delWindowStyleFlag(wx.LB_EXTENDED)
			self._addWindowStyleFlag(wx.LB_SINGLE)

	MultipleSelect = property(_getMultipleSelect, _setMultipleSelect, None,
			_("Can multiple items be selected at once?  (bool)") )


	DynamicMultipleSelect = makeDynamicProperty(MultipleSelect)


class _dListBox_test(dListBox):
	def initProperties(self):
		# Simulate a database:
		actors = ({"lname": "Jason Leigh", "fname": "Jennifer", "iid": 42},
			{"lname": "Cates", "fname": "Phoebe", "iid": 23},
			{"lname": "Reinhold", "fname": "Judge", "iid": 13})

		choices = []
		keys = {}

		for actor in actors:
			choices.append("%s %s" % (actor['fname'], actor['lname']))
			keys[actor["iid"]] = len(choices) - 1

#		self.MultipleSelect = True
		self.Choices = choices
		self.Keys = keys
		self.ValueMode = 'Key'
		self.Value = 23

	def onHit(self, evt):
		print "HIT:"
		print "\tKeyValue: ", self.KeyValue
		print "\tPositionValue: ", self.PositionValue
		print "\tStringValue: ", self.StringValue
		print "\tValue: ", self.Value
		print "\tCount: ", self.Count

	def onMouseLeftDoubleClick(self, evt):
		print "double click at position %s" % self.PositionValue

	def onMouseLeftDown(self, evt):
		print "mousedown"

if __name__ == "__main__":
	import test
	test.Test().runTest(_dListBox_test)

