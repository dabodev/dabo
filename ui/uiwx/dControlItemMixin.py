from dDataControlMixin import dDataControlMixin
from dabo.dLocalize import _
import wx


class dControlItemMixin(dDataControlMixin):
	""" This mixin class factors out the common code among all of the
	controls that contain lists of items.
	"""
	def appendItem(self, txt):
		""" Adds a new item to the end of the list """
		chc = self._choices
		chc.append(txt)
		self.Choices = chc
	
	
	def insertItem(self, pos, txt):
		""" Inserts a new item into the specified position. """
		chc = self._choices[:pos]
		chc.append(txt)
		chc += self._choices[pos:]
		self.Choices = chc
		
	
	def clearSelections(self):
		""" Stub method. Only used in the list box, where there
		can be multiple selections.
		"""
		pass
		
		
	def _getValueModeEditorInfo(self):
		return {"editor": "list", "values": ["string", "position", "key"]}


	def _getChoicesEditorInfo(self):
		return {"editor" : "choice"}
	
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getChoices(self):
		try:
			_choices = self._choices
		except AttributeError:
			_choices = self._choices = []
		return _choices
		
	def _setChoices(self, choices):
		vm = self.ValueMode
		oldVal = self.Value
		self.Clear()
		self._choices = list(choices)
		self.AppendItems(self._choices)
		if oldVal is not None:
			# Try to get back to the same row:
			try:
				self.Value = oldVal
			except ValueError:
				self.PositionValue = 0

	def _getCount(self):
		return self.GetCount()
	
	def _getKeys(self):
		try:
			keys = self._keys
		except AttributeError:
			keys = self._keys = {}
		return keys
		
	def _setKeys(self, val):
		if type(val) == dict:
			self._keys = val
			self._invertedKeys = dict([[v,k] for k,v in val.iteritems()])
		else:
			raise TypeError, _("Keys must be a dictionary.")
			
	def _getKeyValue(self):
		selections = self.PositionValue
		values = []
		
		if not self.isMultiSelect:
			if selections is None:
				return None
			else:
				selections = (selections,)

		for selection in selections:
			try:
				values.append(self._invertedKeys[selection])
			except KeyError:
				values.append(None)
		
		if not self.isMultiSelect:
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
		self.clearSelections()
		
		# Select items that match indices in value:
		for key in value:
			if key is None:
				continue
			self.SetSelection(self.Keys[key])
		self._afterValueChanged()


	def _getPosValue(self):
		if not self.isMultiSelect:
			return self._pemObject.GetSelection()
		else:
			selections = self._pemObject.GetSelections()
			return tuple(selections)
	def _setPosValue(self, value):
		# convert singular to tuple:
		if type(value) not in (list, tuple):
			value = (value,)
		# Clear all current selections:
		self.clearSelections()
		# Select items that match indices in value:
		for index in value:
			if index is None:
				continue
			self.SetSelection(index)
		self._afterValueChanged()

	
	def _getStrValue(self):
		selections = self.PositionValue
		if not self.isMultiSelect:
			if selections is None:
				return None
			else:
				selections = (selections,)
		strings = []
		for index in selections:
			if (index < 0) or (index > (self.Count-1)):
				continue
			try:
				strings.append(self.GetString(index))
			except:
				# Invalid index; usually an empty list
				pass
		if not self.isMultiSelect:
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
		self.clearSelections()
		# Select items that match the string tuple:
		for string in value:
			if string is None:
				continue
			if type(string) in (str, unicode):
				index = self.FindString(string)
				if index < 0:
					raise ValueError, _("String must be present in the choices.")
				else:
					self.SetSelection(index)
			else:
				raise TypeError, _("Unicode or string required.")
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
		_("""Specifies the string choices to display in the list.
		-> List of strings. Read-write at runtime.
		The list index becomes the PositionValue, and the string becomes the
		StringValue.
		""") )
	
	Count = property(_getCount, None, None,
		_("""Number of items in the control.
		-> Integer. Read-only.
		""") )

	Keys = property(_getKeys, _setKeys, None,
		_("""Specifies a mapping between arbitrary values and item positions.
		-> Dictionary. Read-write at runtime.
		The Keys property is a dictionary, where each key resolves into a 
		list index (position). If using keys, you should update the Keys
		property whenever you update the Choices property, to make sure they
		are in sync.
		""") )
		
	KeyValue = property(_getKeyValue, _setKeyValue, None,
		_("""Specifies the key value or values of the selected item or items.
		-> Type can vary. Read-write at runtime.
		Returns the key value or values of the selected item(s), or selects 
		the item(s) with the specified KeyValue(s).	An exception will be 
		raised if the Keys property hasn't been set up to accomodate.
		""") )
		
	PositionValue = property(_getPosValue, _setPosValue, None,
		_("""Specifies the position (index) of the selected item(s).
		-> Integer or tuple of integers. Read-write at runtime.
		Returns the current position(s), or sets the current position(s).
		""") )

	StringValue = property(_getStrValue, _setStrValue, None,
		_("""Specifies the text of the selected item.
		-> String or tuple of strings. Read-write at runtime.
		Returns the text of the selected item(s), or selects the item(s) 
		with the specified text. An exception is raised if there is no 
		position with matching text.
		""") )

	Value = property(_getValue, _setValue, None,
		_("""Specifies which item is currently selected in the list.
		-> Type can vary. Read-write at runtime.
		Value refers to one of the following, depending on the setting of ValueMode:
			+ ValueMode="Position" : the index of the selected item(s) (integer)
			+ ValueMode="String"   : the displayed string of the selected item(s) (string)
			+ ValueMode="Key"      : the key of the selected item(s) (can vary)
		""") )
	
	ValueMode = property(_getValueMode, _setValueMode, None,
		_("""Specifies the information that the Value property refers to.
		-> String. Read-write at runtime.
		'Position' : Value refers to the position in the choices (integer).
		'String'   : Value refers to the displayed string for the selection (default) (string).
		'Key'      : Value refers to a separate key, set using the Keys property (can vary).
		""") )

