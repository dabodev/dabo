import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dDropdownList(wx.Choice, dcm.dDataControlMixin):
	""" Allows presenting a choice of items for the user to choose from.
	"""
	def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, 
			choices=["Dabo", "Default"], style=0, properties=None, *args, **kwargs):

		self._baseClass = dDropdownList
		properties = self.extractKeywordProperties(kwargs, properties)
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)

		self._choices = list(choices)

		pre = wx.PreChoice()
		self._beforeInit(pre)
		style=style|pre.GetWindowStyle()
		pre.Create(parent, id, pos, size, choices, *args, **kwargs)

		self.PostCreate(pre)

		dcm.dDataControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self.setProperties(properties)
		self._afterInit()
		

	def initEvents(self):
		#dDropdownList.doDefault()
		super(dDropdownList, self).initEvents()
		
		# catch the wx event and raise the dabo event:
		self.Bind(wx.EVT_CHOICE, self._onWxHit)
		
		# wx.Choice doesn't seem to emit lostfocus and gotfocus events. Therefore,
		# flush the value on every hit.
		self.bindEvent(dEvents.Hit, self._onHit )
	
	def _onHit(self, evt):
		self.flushValue()
		
	
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getChoices(self):
		try:
			_choices = self._choices
		except AttributeError:
			_choices = self._choices = []
		return _choices
		
	def _setChoices(self, choices):
		oldVal = self.Value
		self.Clear()
		self._choices = list(choices)
		self.AppendItems(self._choices)
		
		# Try to get back to the same row:
		try:
			self.Value = oldVal
		except ValueError:
			self.PositionValue = 0

	def _getKeys(self):
		try:
			keys = self._keys
		except AttributeError:
			keys = self._keys = {}
		return keys
		
	def _setKeys(self, val):
		if type(val) == dict:
			self._keys = val
		else:
			raise TypeError, "Keys must be a dictionary."
			
	def _getKeyValue(self):
		# invert the dict so we can get the key based on current position:
		inverted = dict([[v,k] for k,v in self.Keys.iteritems()])
		try:
			return inverted[self.PositionValue]
		except KeyError:
			return None
		# (note that the above method has to make a new dict every time the KeyValue
		# is accessed... possible performance bottleneck on large lists!)
		
	def _setKeyValue(self, val):
		# This function takes a key value, such as 10992, finds the mapped position,
		# and makes that position the active list selection.
		try:
			self.PositionValue = self.Keys[val]
		except KeyError:
			self.PositionValue = 0
	
	def _getPosValue(self):
		return self._pemObject.GetSelection()
	def _setPosValue(self, value):
		self._pemObject.SetSelection(int(value))
		self._afterValueChanged()

	def _getStrValue(self):
		return self._pemObject.GetStringSelection()
	def _setStrValue(self, value):
		try:
			self._pemObject.SetStringSelection(str(value))
		except:
			raise ValueError, "Value must be present in the choices. (%s:%s)" % (
				value, self.Choices)
		self._afterValueChanged()

	def _getValue(self):
		if self.ValueMode == "position":
			ret = self.PositionValue
		elif self.ValueMode == "key":
			ret = self.KeyValue
		else:
			ret = self.StringValue
		return ret
		
	def _setValue(self, value):
		if self.ValueMode == "position":
			self.PositionValue = value
		elif self.ValueMode == "key":
			self.KeyValue = value
		else:
			self.StringValue = value

	def _getValueMode(self):
		try:
			vm = self._valueMode
		except AttributeError:	
			vm = self._valueMode = "string"
		return vm
		
	def _setValueMode(self, val):
		val = str(val).lower()
		if val in ("position", "string", "key"):
			self._valueMode = val
			
		
	# Property definitions:
	Choices = property(_getChoices, _setChoices, None,
		"Specifies the list of choices available in the list. (list of strings)")	

	Keys = property(_getKeys, _setKeys, None,
		"""Specifies a mapping between the position of an item, and another value, such as
		a primary key in a lookup table. 
		
		The Keys property is a dictionary, where each key resolves into a list index (position).
		""")
		
	KeyValue = property(_getKeyValue, _setKeyValue, None,
		"""The key value of the selected item.
		
		The Keys property must be set up in a 1:1 fashion with the positions.
		""")
		
	PositionValue = property(_getPosValue, _setPosValue, None,
			"Position of selected value (int)" )

	StringValue = property(_getStrValue, _setStrValue, None,
			"Text of selected value (str)" )

	Value = property(_getValue, _setValue, None,
			"Specifies the current value, the type of which depends on the setting of ValueMode.")
	
	ValueMode = property(_getValueMode, _setValueMode, None,
		"""Specifies the information that the Value property refers to.
		
		'position' : Value refers to the position in the choices (the index).
		'string'   : Value refers to the displayed string for the selection (default).
		'key'      : Value refers to a separate key, set using the Keys property.
		""")

if __name__ == "__main__":
	import test
	
	class T(dDropdownList):
		def afterInit(self):
			T.doDefault()
			self.BackColor = "aquamarine"
			self.ForeColor = "wheatdd"
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
			
			self.Choices = choices
			self.Keys = keys
			self.ValueMode = 'key'
			
		def onHit(self, evt):
			print "KeyValue: ", self.KeyValue
			print "PositionValue: ", self.PositionValue
			print "StringValue: ", self.StringValue
			print "Value: ", self.Value
			
	test.Test().runTest(T)
