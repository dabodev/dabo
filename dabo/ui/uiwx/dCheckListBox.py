import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlItemMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dCheckListBox(wx.CheckListBox, dcm.dControlItemMixin):
	"""Creates a listbox, allowing the user to choose one or more items
	by checking/unchecking each one
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dCheckListBox
		self._choices = []

		preClass = wx.PreCheckListBox
		dcm.dControlItemMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

			
	def _initEvents(self):
		super(dCheckListBox, self)._initEvents()
		self.Bind(wx.EVT_CHECKLISTBOX, self._onWxHit)
	
	
	def GetSelections(self):
		"""Need to overrid the native method, as this reports the 
		line with focus, not the checked items.
		"""
		ret = []
		for cnt in xrange(self.Count):
			if self.IsChecked(cnt):
				ret.append(cnt)
		return ret
		
		
	def clearSelections(self):
		"""Need to override for this control"""
		for cnt in xrange(self.Count):
			self.Check(cnt, False)


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
			_("Need to fake this so that the mixin reports values correctly  (bool)"))
	
	
	
class _dCheckListBox_test(dCheckListBox):
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
	test.Test().runTest(_dCheckListBox_test)

