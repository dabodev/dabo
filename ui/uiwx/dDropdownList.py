import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dDropdownList(wx.Choice, dcm.dDataControlMixin):
	""" Allows presenting a choice of items for the user to choose from.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dDropdownList
		preClass = wx.PreChoice
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	
	def _initEvents(self):
		super(dDropdownList, self)._initEvents()
		self.Bind(wx.EVT_CHOICE, self._onWxHit)
		
		# wx.Choice doesn't seem to emit lostfocus and gotfocus events. Therefore,
		# flush the value on every hit.
		self.bindEvent(dEvents.Hit, self.__onHit )
	
	def __onHit(self, evt):
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
		self.PositionValue = self.Keys[val]
	
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
		"""Specifies the string choices to display in the list.
		
		List of strings. Read-write at runtime.
		
		The list index becomes the PositionValue, and the string becomes the
		StringValue.
		""")	

	Keys = property(_getKeys, _setKeys, None,
		"""Specifies a mapping between arbitrary values and item positions.
		
		Dictionary. Read-write at runtime.
		
		The Keys property is a dictionary, where each key resolves into a 
		list index (position). If using keys, you should update the Keys
		property whenever you update the Choices property, to make sure they
		are in sync.
		""")
		
	KeyValue = property(_getKeyValue, _setKeyValue, None,
		"""Specifies the key value of the selected item.
		
		Type can vary. Read-write at runtime.
		
		Returns the key value of the selected item, or changes the current 
		position to the position that is mapped to the specified key value.
		An exception will be raised if the Keys property hasn't been set up
		to accomodate.
		""")
		
	PositionValue = property(_getPosValue, _setPosValue, None,
		"""Specifies the position (index) of the selected item.
		
		Integer. Read-write at runtime.
		
		Returns the current position, or sets the current position.
		""")

	StringValue = property(_getStrValue, _setStrValue, None,
		"""Specifies the text of the selected item.
		
		String. Read-write at runtime.
		
		Returns the text of the current item, or changes the current position
		to the position with the specified text. An exception is raised if there
		is no position with matching text.
		""" )

	Value = property(_getValue, _setValue, None,
		"""Specifies which item is currently selected in the list.
		
		Type can vary. Read-write at runtime.
			
		Value refers to one of the following, depending on the setting of ValueMode:
			+ ValueMode="Position" : the index of the selected item (integer)
			+ ValueMode="String"   : the displayed string of the selected item (string)
			+ ValueMode="Key"      : the key of the selected item (can vary)
		""")
	
	ValueMode = property(_getValueMode, _setValueMode, None,
		"""Specifies the information that the Value property refers to.
		
		String. Read-write at runtime.
		
		'Position' : Value refers to the position in the choices (integer).
		'String'   : Value refers to the displayed string for the selection (default) (string).
		'Key'      : Value refers to a separate key, set using the Keys property (can vary).
		""")

		
if __name__ == "__main__":
	import test
	class _T(dDropdownList):
		def afterInit(self):
			_T.doDefault()
			self.BackColor = "aquamarine"
			self.ForeColor = "wheat"
			self.setup()
		
		def initEvents(self):
			_T.doDefault()
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
		
	test.Test().runTest(_T)
