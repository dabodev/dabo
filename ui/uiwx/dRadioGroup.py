import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty
import warnings


class dRadioGroup(dcm.dDataControlMixin, wx.RadioBox):
	"""Creates a group of radio buttons, allowing mutually-exclusive choices.

	Like a dDropdownList, use this to present the user with multiple choices and
	for them to choose from one of the choices. Where the dDropdownList is
	suitable for lists of one to a couple hundred choices, a dRadioGroup is 
	really only suitable for lists of one to a dozen at most.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		warnings.warn(_("Deprecated; use the dabo.ui.dRadioList control instead."), 
				DeprecationWarning, 1)
		self._baseClass = dRadioGroup
		preClass = wx.PreRadioBox
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def enableKey(self, item, val=True):
		"""Enables or disables an individual button, referenced by key value."""
		index = self.Keys[item]
		self.EnableItem(index, val)
	
	def enablePosition(self, item, val=True):
		"""Enables or disables an individual button, referenced by position (index)."""
		self.EnableItem(item, val)
		
	def enableString(self, item, val=True):
		"""Enables or disables an individual button, referenced by string display value."""
		index = self.FindString(item)
		self.EnableItem(index, val)
		
	def enable(self, item, val=True):
		"""Enables or disables an individual button.
		
		The item argument specifies which button to enable/disable, and its type
		depends on the setting of self.ValueType:
		
			"position" : The item is referenced by index position.
			"string"   : The item is referenced by its string display value.
			"key"      : The item is referenced by its key value.
		"""
		if self.ValueMode == "position":
			self.enablePosition(item, val)
		elif self.ValueMode == "string":
			self.enableString(item, val)
		elif self.ValueMode == "key":
			self.enableKey(item, val)
		
		
	def showKey(self, item, val=True):
		"""Shows or hides an individual button, referenced by key value."""
		index = self.Keys[item]
		self.ShowItem(index, val)
	
	def showPosition(self, item, val=True):
		"""Shows or hides an individual button, referenced by position (index)."""
		self.ShowItem(item, val)
		
	def showString(self, item, val=True):
		"""Shows or hides an individual button, referenced by string display value."""
		index = self.FindString(item)
		self.ShowItem(index, val)
		
	def show(self, item, val=True):
		"""Shows or hides an individual button.
		
		The item argument specifies which button to hide/show, and its type
		depends on the setting of self.ValueType:
		
			"position" : The item is referenced by index position.
			"string"   : The item is referenced by its string display value.
			"key"      : The item is referenced by its key value.
		"""
		if self.ValueMode == "position":
			self.showPosition(item, val)
		elif self.ValueMode == "string":
			self.showString(item, val)
		elif self.ValueMode == "key":
			self.showKey(item, val)
		
		
	def _getInitPropertiesList(self):
		additional = ["MaxElements", "Choices"]
		original = list(super(dRadioGroup, self)._getInitPropertiesList())
		return tuple(original + additional)


	def _preInitUI(self, kwargs):
		if kwargs.has_key("choices"):
			warnings.warn(_("Change the 'choices' argument to 'Choices'"), DeprecationWarning)
		if not kwargs.has_key("choices"):
			# wx requires the choices=[] argument, but Dabo's spelling is Choices.
			kwargs["choices"] = self.Choices
		if not kwargs.has_key("majorDimension"):
			self._maxElements = kwargs["majorDimension"] = 1
		return kwargs

				
	def _initEvents(self):
		super(dRadioGroup, self)._initEvents()
		self.Bind(wx.EVT_RADIOBOX, self._onWxHit)
	
			
	def _onWxHit(self, evt):
		self.flushValue()
		self.super(evt)
		
	
		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getChoices(self):
		try:
			_choices = self._choices
		except AttributeError:
			_choices = self._choices = []
		return _choices
		
	def _setChoices(self, choices):
		if self._constructed():
			raise ValueError, "Cannot change RadioGroup choices at runtime."
		else:
			self._choices = self._properties["Choices"] = choices
	
	def _getKeys(self):
		try:
			keys = self._keys
		except AttributeError:
			keys = self._keys = {}
		return keys
		
	def _setKeys(self, val):
		if isinstance(val, dict):
			self._keys = val
			self._invertedKeys = dict([[v,k] for k,v in val.iteritems()])
		else:
			raise TypeError, "Keys must be a dictionary."
			
	def _getKeyValue(self):
		# Return the current key value based on the current position value
		try:
			return self._invertedKeys[self.PositionValue]
		except KeyError:
			return None
		
	def _setKeyValue(self, val):
		if self._constructed():
			# This function takes a key value, such as 10992, finds the mapped position,
			# and makes that position the active button.
			self.PositionValue = self.Keys[val]
		else:
			self._properties["KeyValue"] = val
	
	def _getMaxElements(self):
		try:
			_maxElements = self._maxElements
		except AttributeError:
			_maxElements = self._maxElements = 1
		return _maxElements
		
	def _setMaxElements(self, val):
		if self._constructed():
			raise ValueError, "Cannot change RadioGroup MaxElements at runtime."
		else:
			self._maxElements = self._initProperties["majorDimension"] = int(val)
		
	def _getOrientation(self):
		if self._hasWindowStyleFlag(wx.RA_SPECIFY_ROWS):
			return "Column"
		elif self._hasWindowStyleFlag(wx.RA_SPECIFY_COLS):
			return "Row"
		else:
			return "None"
	
	def _setOrientation(self, val):
		val = str(val).lower()
		self._delWindowStyleFlag(wx.RA_SPECIFY_ROWS)
		self._delWindowStyleFlag(wx.RA_SPECIFY_COLS)
		if val == "row":
			self._addWindowStyleFlag(wx.RA_SPECIFY_COLS)
		elif val[:3] == "col":
			self._addWindowStyleFlag(wx.RA_SPECIFY_ROWS)
		elif val == "none":
			pass
		else:
			raise ValueError, "The only possible settings are 'None', 'Row', and 'Column'."
			
		
	def _getPositionValue(self):
		return self.GetSelection()
	
	def _setPositionValue(self, value):
		if self._constructed():
			self.SetSelection(int(value))
			self._afterValueChanged()
		self._properties["PositionValue"] = value

	def _getStringValue(self):
		return self.GetStringSelection()
	
	def _setStringValue(self, value):
		if self._constructed():
			try:
				self.SetStringSelection(str(value))
			except:
				raise ValueError, "Value must be present in the choices. (%s:%s)" % (
					value, self.Choices)
			self._afterValueChanged()
		else:
			self._properties["StringValue"] = value
	
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
		"""Specifies the string choices to display in the RadioGroup.
		
		List of strings. Read-only at runtime.
		
		The list index becomes the PositionValue, and the string becomes the
		StringValue.
		""")	

	Keys = property(_getKeys, _setKeys, None,
		"""Specifies a mapping between arbitrary values and button positions.
		
		Dictionary. Read-write at runtime.
		
		The Keys property is a dictionary, where each key resolves into a 
		button index (position). If using keys, you should update the Keys
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
	DynamicKeyValue = makeDynamicProperty(KeyValue)
		
	MaxElements = property(_getMaxElements, _setMaxElements, None,
		"""Specifies when to grow the radio group in the opposite Orientation.
		
		Integer. Read-only at runtime.
		
		Specifies the maximum rows, if Orientation=='Row', or the maximum columns,
		if Orientation=='Column'. When the max is reached, the radio group will grow
		in the opposite direction to accomodate. 
		""")
	DynamicMaxElements = makeDynamicProperty(MaxElements)
	
	Orientation = property(_getOrientation, _setOrientation, None,
		"""Specifies whether this is a vertical or horizontal RadioGroup.
		
		String. Read-only at runtime. Possible values:
			'None'
			'Row'
			'Column'
		
		If there are more than a few radio buttons, you may wish to set MaxElements
		to start growing the RadioGroup in two dimensions.
		""")
	DynamicOrientation = makeDynamicProperty(Orientation)

	PositionValue = property(_getPositionValue, _setPositionValue, None,
		"""Specifies the position (index) of the selected button.
		
		Integer. Read-write at runtime.
		
		Returns the current position, or sets the current position.
		""")
	DynamicPositionValue = makeDynamicProperty(PositionValue)

	StringValue = property(_getStringValue, _setStringValue, None,
		"""Specifies the text of the selected button.
		
		String. Read-write at runtime.
		
		Returns the text of the current item, or changes the current position
		to the position with the specified text. An exception is raised if there
		is no position with matching text.
		""" )
	DynamicStringValue = makeDynamicProperty(StringValue)

	Value = property(_getValue, _setValue, None,
		"""Specifies which button is currently selected in the group.
		
		Type can vary. Read-write at runtime.
			
		Value refers to one of the following, depending on the setting of ValueMode:
			+ ValueMode="Position" : the index of the selected button (integer)
			+ ValueMode="String"   : the displayed string of the selected button (string)
			+ ValueMode="Key"      : the key of the selected button (can vary)
		""")
	DynamicValue = makeDynamicProperty(Value)
	
	ValueMode = property(_getValueMode, _setValueMode, None,
		"""Specifies the information that the Value property refers to.
		
		String. Read-write at runtime.
		
		'Position' : Value refers to the position in the choices (integer).
		'String'   : Value refers to the displayed string for the selection (default) (string).
		'Key'      : Value refers to a separate key, set using the Keys property (can vary).
		""")
	DynamicValueMode = makeDynamicProperty(ValueMode)
	

class _dRadioGroup_test_deprecated(dRadioGroup):
	def initProperties(self):
		self.ForeColor = "darkblue"
		self.BackColor = "wheat"
		self.Orientation = "None"
		self.setup()
		
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
		self.enable(42, False)
		

if __name__ == "__main__":
	import test
	test.Test().runTest(_dRadioGroup_test_deprecated)
