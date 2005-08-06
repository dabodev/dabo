import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlItemMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dListBox(wx.ListBox, dcm.dControlItemMixin):
	""" Allows presenting a choice of items for the user to choose from.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dListBox
		self._choices = []
		self._keys = []
		self._invertedKeys = []
		self._valueMode = "string"
		self.isMultiSelect = False

		preClass = wx.PreListBox
		dcm.dControlItemMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		# This may have been set when created.
		self.isMultiSelect = self.hasWindowStyleFlag(wx.LB_EXTENDED)

			
	def _initEvents(self):
		super(dListBox, self)._initEvents()
		self.Bind(wx.EVT_LISTBOX, self._onWxHit)
	
	
	def clearSelections(self):
		for elem in self.GetSelections():
			self.SetSelection(elem, False)

	
	def _getMultipleSelect(self):
		return self.hasWindowStyleFlag(wx.LB_EXTENDED)
	def _setMultipleSelect(self, val):
		if bool(val):
			self.delWindowStyleFlag(wx.LB_SINGLE)
			self.addWindowStyleFlag(wx.LB_EXTENDED)
		else:
			self.delWindowStyleFlag(wx.LB_EXTENDED)
			self.addWindowStyleFlag(wx.LB_SINGLE)

	MultipleSelect = property(_getMultipleSelect, _setMultipleSelect, None,
			_("Can multiple items be selected at once?  (bool)") )



if __name__ == "__main__":
	import test
	class T(dListBox):
		def afterInit(self):
			T.doDefault()
			self.ForeColor = "aquamarine"
			self.setup()

		def initEvents(self):
			T.doDefault()
			self.bindEvent(dabo.dEvents.Hit, self.onHit)
			
		def setup(self):
			print "Simulating a database:"
			developers = ({"lname": "McNett", "fname": "Paul", "iid": 42},
				{"lname": "Leafe", "fname": "Ed", "iid": 23})
			
			choices = []
			keys = {}
			for developer in developers:
				choices.append("%s %s" % (developer['fname'], developer['lname']))
				keys[developer["iid"]] = len(choices) - 1
			self.MultipleSelect = True
			self.Choices = choices
			self.Keys = keys
			self.ValueMode = 'Key'
			self.Value = 23
			#self.Value = None
			#self.Value = ("Ed Leafe", "Paul McNett")
			#self.Value = 1
						
		def onHit(self, evt):
			print "KeyValue: ", self.KeyValue
			print "PositionValue: ", self.PositionValue
			print "StringValue: ", self.StringValue
			print "Value: ", self.Value
	
	test.Test().runTest(T)

