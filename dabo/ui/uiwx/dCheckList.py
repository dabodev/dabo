# -*- coding: utf-8 -*-
import wx
import dabo
import dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlItemMixin as dcm
from dabo.dLocalize import _


class dCheckList(dcm.dControlItemMixin, wx.CheckListBox):
	"""
	Creates a listbox, allowing the user to choose one or more items
	by checking/unchecking each one.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dCheckList
		self._choices = []
		preClass = wx.PreCheckListBox
		dcm.dControlItemMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def _initEvents(self):
		super(dCheckList, self)._initEvents()
		self.Bind(wx.EVT_CHECKLISTBOX, self._onWxHit)


	def GetSelections(self):
		# Need to override the native method, as this reports the
		# line with focus, not the checked items.
		ret = []
		for cnt in xrange(self.Count):
			if self.IsChecked(cnt):
				ret.append(cnt)
		return ret


	def selectAll(self):
		"""Set all items to checked."""
		for cnt in xrange(self.Count):
			self.Check(cnt, True)


	def clearSelections(self):
		"""Set all items to unchecked."""
		for cnt in xrange(self.Count):
			self.Check(cnt, False)
	# Just to keep the naming consistent
	selectNone = clearSelections


	def invertSelections(self):
		"""Switch all the items from False to True, and vice-versa."""
		for cnt in xrange(self.Count):
			self.Check(cnt, not self.IsChecked(cnt))


	def setSelection(self, index):
		if self.Count > index:
			self.Check(index, True)
		else:
			## pkm: The user probably set the Value property from inside initProperties(),
			##      and it is getting set before the Choice property has been applied.
			##      If this is the case, callAfter is the ticket.
			dabo.ui.callAfter(self.Check, index, True)


	def _getMultipleSelect(self):
		return True


	MultipleSelect = property(_getMultipleSelect, None, None,
			_("MultipleSelect for dCheckList is always True."))



class _dCheckList_test(dCheckList):
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
		print "double click"

	def onMouseLeftDown(self, evt):
		print "mousedown"

if __name__ == "__main__":
	import test
	test.Test().runTest(_dCheckList_test)

