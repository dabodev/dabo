from dDataControlMixin import dDataControlMixin
from dabo.dLocalize import _
import wx
import dabo

class dControlItemMixin(dDataControlMixin):
	""" This mixin class factors out the common code among all of the
	controls that contain lists of items.
	"""
	def __init__(self, *args, **kwargs):
		self._keys = []
		self._invertedKeys = []
		self._valueMode = "string"
		super(dControlItemMixin, self).__init__(*args, **kwargs)

		
	def appendItem(self, txt, select=False):
		""" Adds a new item to the end of the list """
		chc = self._choices
		chc.append(txt)
		self.Choices = chc
		if select:
			self.StringValue = txt
	
	
	def insertItem(self, pos, txt, select=False):
		""" Inserts a new item into the specified position. """
		chc = self._choices[:pos]
		chc.append(txt)
		chc += self._choices[pos:]
		self.Choices = chc
		if select:
			self.StringValue = txt
	
	
	def removeItem(self, pos):
		""" Removes the item at the specified position. """
		del self._choices[pos]
		self.Delete(pos)


	def removeAll(self):
		""" Removes all entries from the control. """
		self._choices = []
		self.Clear()
		
	
	def clearSelections(self):
		""" Stub method. Only used in the list box, where there
		can be multiple selections.
		"""
		pass
		

	def setSelection(self, index):
		if self.Count > index:
			self.SetSelection(index)
		else:
			## pkm: I think on Windows the order of property setting
			## matters, and the selected row is getting set before
			## the items have been set. Make a log and ignore for now.
			dabo.errorLog.write("dControlItemMixin::setSelection(): index > count")


	def _isMultiSelect(self):
		"""Return whether this control has multiple-selectable items."""
		try:
			ms = self.MultipleSelect
		except AttributeError:
			ms = False
		return ms

		
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
		else:
			self._properties["Choices"] = choices


	def _getCount(self):
		return self.GetCount()
	

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
		elif isinstance(val, (list, tuple)):
			self._keys = val
			self._invertedKeys = None
		else:
			raise TypeError, _("Keys must be a dictionary or list/tuple.")
			

	def _getKeyValue(self):
		selections = self.PositionValue
		values = []
		if not self._isMultiSelect():
			if selections is None:
				return None
			else:
				selections = (selections,)
		for selection in selections:
			if selection < 0:
				# This is returned by the control to indicate no selection
				continue
			if isinstance(self.Keys, (list, tuple)):
				try:
					values.append(self.Keys[selection])
				except IndexError:
					values.append(None)
			else:
				try:
					values.append(self._invertedKeys[selection])
				except KeyError:
					values.append(None)
		
		if not self._isMultiSelect():
			if len(values) > 0:
				return values[0]
			else:
				return None		
		else:
			return tuple(values)
			
		
	def _setKeyValue(self, value):
		if self._constructed():
			# This function takes a key value or values, such as 10992 or
			# (10992, 92991), finds the mapped position or positions, and 
			# and selects that position or positions.
	
			# convert singular to tuple:
			if not isinstance(value, (list, tuple)):
				value = (value,)
		
			# Clear all current selections:
			self.clearSelections()
		
			# Select items that match indices in value:
			for key in value:
				if not self.Keys.has_key(key):
					# self.Keys does not have the requested key. This could happen, for
					# example, if the bound field is a foreign key, and we are just adding
					# a new record. In my case, the iclientid field is ''. I want the list
					# to display "< None >" and map that to a value of None, so I set up a
					# Choice and a Key for that in my app code.

					# setting key to None here will result in an exception if there is no
					# key on None (user code must set their Keys to have a None key). But
					# the effect this has is that if the control is getting set to a value
					# that doesn't exist in self.Keys, we'll set the list to select the 
					# item that is matched to None, if available. Else, it's a runtime
					# exception.
					key = None
				self.setSelection(self.Keys[key])
			self._afterValueChanged()
		else:
			self._properties["KeyValue"] = value


	def _getPositionValue(self):
		if hasattr(self, "SelectedIndices"):
			ret = tuple(self.SelectedIndices)
			if not self._isMultiSelect():
				# Only return a single index
				ret = ret[0]
		else:
			if not self._isMultiSelect():
				ret = self.GetSelection()
			else:
				selections = self.GetSelections()
				ret = tuple(selections)
		return ret
		

	def _setPositionValue(self, value):
		if self._constructed():
			# convert singular to tuple:
			if not isinstance(value, (list, tuple)):
				value = (value,)
			# Clear all current selections:
			self.clearSelections()
			# Select items that match indices in value:
			for index in value:
				if index is None:
					continue
				try:
					self.setSelection(index)
				except: pass
			self._afterValueChanged()
		else:
			self._properties["PositionValue"] = value

	
	def _getStringValue(self):
		selections = self.PositionValue
		if not self._isMultiSelect():
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
		if not self._isMultiSelect():
			# convert to singular
			if len(strings) > 0:
				return strings[0]
			else:
				return None
		else:
			return tuple(strings)
			
	
	def _setStringValue(self, value):
		if self._constructed():
			# convert singular to tuple:
			if not isinstance(value, (list, tuple)):
				value = (value,)
			# Clear all current selections:
			self.clearSelections()
			# Select items that match the string tuple:
			for string in value:
				if string is None:
					continue
				if isinstance(string, basestring):
					index = self.FindString(string)
					if index < 0:
						raise ValueError, _("String must be present in the choices.")
					else:
						self.setSelection(index)
				else:
					raise TypeError, _("Unicode or string required.")
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
		-> Optionally, Keys can be a list/tuple that is a 1:1 mapping of the 
		Choices property. So if your 3rd Choices entry is selected, KeyValue
		will return the 3rd entry in the Keys property.		
		""") )
		
	KeyValue = property(_getKeyValue, _setKeyValue, None,
		_("""Specifies the key value or values of the selected item or items.
		-> Type can vary. Read-write at runtime.
		Returns the key value or values of the selected item(s), or selects 
		the item(s) with the specified KeyValue(s).	An exception will be 
		raised if the Keys property hasn't been set up to accomodate.
		""") )
		
	PositionValue = property(_getPositionValue, _setPositionValue, None,
		_("""Specifies the position (index) of the selected item(s).
		-> Integer or tuple of integers. Read-write at runtime.
		Returns the current position(s), or sets the current position(s).
		""") )

	StringValue = property(_getStringValue, _setStringValue, None,
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

