import wx, dabo, dabo.ui
import dabo.dEvents as dEvents
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dDataControlMixin as dcm
from dabo.dLocalize import _

class dComboBox(wx.ComboBox, dcm.dDataControlMixin):
	"""Combination DropdownList and TextBox.
	
	The user can choose an item in the dropdown, or enter freeform text.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dComboBox
		preClass = wx.PreComboBox
		self._userVal = False
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _initEvents(self):
		super(dComboBox, self)._initEvents()
		self.Bind(wx.EVT_COMBOBOX, self.__onComboBox)
		self.Bind(wx.EVT_TEXT_ENTER, self.__onTextBox)
			
	
	def __onComboBox(self, evt):
		self._userVal = False
		evt.Skip()
		self.raiseEvent(dabo.dEvents.Hit, evt)
		
		
	def __onTextBox(self, evt):
		self._userVal = True
		evt.Skip()
		self.raiseEvent(dabo.dEvents.Hit, evt)
	
	
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

	def _getUserValue(self):
		if self._userVal:
			return self._pemObject.GetValue()
		else:
			return self._pemObject.GetStringSelection()
				
	def _setUserValue(self, value):
		self.SetValue(value)
		# don't call _afterValueChanged(), because value tracks the item in the list,
		# not the displayed value. User code can query UserValue and then decide to
		# add it to the list, if appropriate.
	
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
		
		This can differ from the text currently showing in the text box, if the 
		user has edited it. See UserValue for that.
		""" )

	UserValue = property(_getUserValue, _setUserValue, None,
		"""Specifies the text displayed in the textbox portion of the ComboBox.
		
		String. Read-write at runtime.
		
		UserValue can differ from StringValue, which would mean that the user
		has typed in arbitrary text. Unlike StringValue, PositionValue, and 
		KeyValue, setting UserValue does not change the currently selected item
		in the list portion of the ComboBox.
		""")

	Value = property(_getValue, _setValue, None,
		"""Specifies which item is currently selected in the list.
		
		Type can vary. Read-write at runtime.
			
		Value refers to one of the following, depending on the setting of ValueMode:
			+ ValueMode="Position" : the index of the selected item (integer)
			+ ValueMode="String"   : the displayed string of the selected item(s) (string)
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
	
	class T(dComboBox):
		def afterInit(self):
			T.doDefault()
			self.BackColor = "aquamarine"
			self.ForeColor = "wheat"
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
			print "UserValue: ", self.UserValue
			
	test.Test().runTest(T)
