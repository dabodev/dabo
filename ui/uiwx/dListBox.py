import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dListBox(wx.ListBox, dcm.dDataControlMixin):
	""" Allows presenting a choice of items for the user to choose from.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dListBox
		preClass = wx.PreListBox
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

			
	def _initEvents(self):
		super(dListBox, self)._initEvents()
		self.Bind(wx.EVT_LISTBOX, self._onWxHit)
		

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
		selections = self.PositionValue
		values = []
		
		if not self.MultipleSelect:
			if selections is None:
				return None
			else:
				selections = (selections,)

		for selection in selections:
			try:
				values.append(inverted[selection])
			except KeyError:
				values.append(None)
		
		if not self.MultipleSelect:
			if len(values) > 0:
				return values[0]
			else:
				return None		
		else:
			return tuple(values)
		
	def _setKeyValue(self, value):
		# This function takes a key value or values, such as 10992 or
		# (10992, 92991), finds the mapped position or positions, and 
		# and selects that position or positions.
	
		# convert singular to tuple:
		if type(value) not in (list, tuple):
			value = (value,)
		
		# Clear all current selections:
		self.SetSelection(-1)
		
		# Select items that match indices in value:
		for key in value:
			if key is None:
				continue
			self.SetSelection(self.Keys[key])
		self._afterValueChanged()
	
	def _getMultipleSelect(self):
		return self.hasWindowStyleFlag(wx.LB_EXTENDED)

	def _setMultipleSelect(self, val):
		if bool(val):
			self.delWindowStyleFlag(wx.LB_SINGLE)
			self.addWindowStyleFlag(wx.LB_EXTENDED)
		else:
			self.delWindowStyleFlag(wx.LB_EXTENDED)
			self.addWindowStyleFlag(wx.LB_SINGLE)
			
	def _getPosValue(self):
		selections = self._pemObject.GetSelections()
		if not self.MultipleSelect:
			# convert to singular
			if len(selections) > 0:
				return selections[0]
			else:
				return None
		else:
			return tuple(selections)

					
	def _setPosValue(self, value):
		# convert singular to tuple:
		if type(value) not in (list, tuple):
			value = (value,)
		
		# Clear all current selections:
		self.SetSelection(-1)
		
		# Select items that match indices in value:
		for index in value:
			if index is None:
				continue
			self.SetSelection(index)
		self._afterValueChanged()

	
	def _getStrValue(self):
		selections = self.PositionValue
		if not self.MultipleSelect:
			if selections is None:
				return None
			else:
				selections = (selections,)
		strings = []
		for index in selections:
			strings.append(self.GetString(index))
		if not self.MultipleSelect:
			# convert to singular
			if len(strings) > 0:
				return strings[0]
			else:
				return None
		else:
			return tuple(strings)
	
	
	def _setStrValue(self, value):
		# convert singular to tuple:
		if type(value) not in (list, tuple):
			value = (value,)
		
		# Clear all current selections:
		self.SetSelection(-1)
		
		# Select items that match the string tuple:
		for string in value:
			if string is None:
				continue
			if type(string) in (str, unicode):
				index = self.FindString(string)
				if index < 0:
					raise ValueError, "String must be present in the choices."
				else:
					self.SetSelection(index)
			else:
				raise TypeError, "Unicode or string required."
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
		"""Specifies the key value or values of the selected item or items.
		
		Type can vary. Read-write at runtime.
		
		Returns the key value or values of the selected item(s), or selects 
		the item(s) with the specified KeyValue(s).	An exception will be 
		raised if the Keys property hasn't been set up to accomodate.
		""")
		
	MultipleSelect = property(_getMultipleSelect, _setMultipleSelect, None,
		"""Specifies whether more that one item can be selected at once.
		
		Boolean. Read-write at runtime.
		
		If MultipleSelect is False, the Value properties will return a 
		singular value representing the currently selected item, or None. 
		If MultipleSelect is True, the Value properties will return	a tuple
		representing the selected item(s), or the empty tuple if no items
		are selected.
		""")
		
	PositionValue = property(_getPosValue, _setPosValue, None,
		"""Specifies the position (index) of the selected item(s).
		
		Integer or tuple of integers. Read-write at runtime.
		
		Returns the current position(s), or sets the current position(s).
		""")

	StringValue = property(_getStrValue, _setStrValue, None,
		"""Specifies the text of the selected item.
		
		String or tuple of strings. Read-write at runtime.
		
		Returns the text of the selected item(s), or selects the item(s) 
		with the specified text. An exception is raised if there is no 
		position with matching text.
		""" )

	Value = property(_getValue, _setValue, None,
		"""Specifies which item is currently selected in the list.
		
		Type can vary. Read-write at runtime.
			
		Value refers to one of the following, depending on the setting of ValueMode:
			+ ValueMode="Position" : the index of the selected item(s) (integer)
			+ ValueMode="String"   : the displayed string of the selected item(s) (string)
			+ ValueMode="Key"      : the key of the selected item(s) (can vary)
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

