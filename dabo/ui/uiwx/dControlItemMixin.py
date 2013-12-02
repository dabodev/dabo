# -*- coding: utf-8 -*-
import wx
import dabo
from dDataControlMixin import dDataControlMixin
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.lib.propertyHelperMixin import _DynamicList
from dabo.ui import makeDynamicProperty



class dControlItemMixin(dDataControlMixin):
	"""
	This mixin class factors out the common code among all of the
	controls that contain lists of items.
	"""
	def __init__(self, *args, **kwargs):
		self._keys = []
		self._invertedKeys = []
		self._valueMode = "s"
		self._sorted = False
		self._sortFunction = None
		super(dControlItemMixin, self).__init__(*args, **kwargs)


	def _initEvents(self):
		super(dControlItemMixin, self)._initEvents()


	def _onWxHit(self, evt):
		self._userChanged = True
		# Flush value on every hit:
		self.flushValue()
		super(dControlItemMixin, self)._onWxHit(evt)
		# Since super method set this attribute again, we must reset it.
		self._userChanged = False


	def appendItem(self, txt, select=False):
		"""Adds a new item to the end of the list"""
		chc = self._choices
		chc.append(txt)
		self.Choices = chc
		if select:
			if self._isMultiSelect():
				self.StringValue += (txt,)
			else:
				self.StringValue = txt


	def insertItem(self, pos, txt, select=False):
		"""Inserts a new item into the specified position."""
		chc = self._choices[:pos]
		chc.append(txt)
		chc += self._choices[pos:]
		self.Choices = chc
		if select:
			self.StringValue = txt


	def removeItem(self, pos):
		"""Removes the item at the specified position."""
		del self._choices[pos]
		self.Delete(pos)


	def removeAll(self):
		"""Removes all entries from the control."""
		self._choices = []
		self.Clear()


	def clearSelections(self):
		"""
		Stub method. Only used in the list box, where there
		can be multiple selections.
		"""
		pass


	def setSelection(self, index):
		"""Same as setting property PositionValue."""
		self.PositionValue = index


	def _setSelection(self, index):
		"""Backend UI wrapper."""
		if self.Count > index:
			self.SetSelection(index)
		else:
			## pkm: The user probably set the Value property from inside initProperties(),
			##      and it is getting set before the Choice property has been applied.
			##      If this is the case, callAfter is the ticket.
			dabo.ui.callAfter(self.SetSelection, index)


	def _isMultiSelect(self):
		"""Return whether this control has multiple-selectable items."""
		try:
			ms = self.MultipleSelect
		except AttributeError:
			ms = False
		return ms


	def sort(self, sortFunction=None):
		"""
		Sorts the list items. By default, the Python 'cmp' function is
		used, but this can be overridden with a custom sortFunction.
		"""
		if sortFunction is None:
			sortFunction = self._sortFunction
		self._choices.sort(sortFunction)


	def _resetChoices(self):
		"""
		Sequence required to update the choices for the list. Refactored out
		to avoid duplicate code.
		"""
		self.Clear()
		self._setSelection(-1)
		if self._sorted:
			self.sort()
		self.AppendItems(self._choices)


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getChoices(self):
		try:
			_choices = self._choices
		except AttributeError:
			_choices = self._choices = []
		return _DynamicList(_choices, self)


	def _setChoices(self, choices):
		if self._constructed():
			self.lockDisplay()
			vm = self.ValueMode
			oldVal = self.Value
			self._choices = list(choices)
			self._resetChoices()
			if oldVal is not None:
				# Try to get back to the same row:
				try:
					self.Value = oldVal
				except ValueError:
					if self._choices:
						self.PositionValue = 0
			self.unlockDisplay()
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
			# What about duplicate values?
			self._invertedKeys = dict((v,k) for k,v in val.iteritems())
		elif isinstance(val, (list, tuple)):
			self._keys = val
			self._invertedKeys = None
		else:
			raise TypeError(_("Keys must be a dictionary or list/tuple."))


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

			invalidSelections = []
			# Select items that match indices in value:
			for key in value:
				if isinstance(self.Keys, dict):
					try:
						self.setSelection(self.Keys[key])
					except KeyError:
						invalidSelections.append(key)
				else:
					try:
						self.setSelection(self.Keys.index(key))
					except ValueError:
						invalidSelections.append(key)

			### pkm: getBlankValue() returns None, so if there isn't a Key for None (the default) the
			###      update cycle will result in the ValueError, which isn't friendly default behavior.
			###      So, I'm making it so that None values in *any* dControlItem class will be allowed.
			###      We can discuss whether we should expose a property to control this behavior or not.
			#if len(value) == 0 or (self._isMultiSelect() and invalidSelections == [None]):
			if len(value) == 0 or invalidSelections == [None]:
				# Value being set to an empty tuple, list, or dict, or to None in a Multi-Select control,
				# which means "nothing is selected":
				self._resetChoices()
				invalidSelections = []

			if invalidSelections:
				snm = self.Name
				dataSource = self.DataSource
				dataField = self.DataField
				raise ValueError(_("Trying to set %(snm)s.Value (DataSource: '%(dataSource)s', "
						"DataField: '%(dataField)s') to these invalid selections: %(invalidSelections)s") % locals())

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
					self._setSelection(index)
				except IndexError:
					pass
			self._afterValueChanged()
		else:
			self._properties["PositionValue"] = value


	def _getSorted(self):
		return self._sorted

	def _setSorted(self, val):
		if self._constructed():
			if self._sorted != val:
				self._sorted = val
				if val:
					# Force a re-ordering
					self.sort()
		else:
			self._properties["Sorted"] = val


	def _getSortFunction(self):
		return self._sortFunction

	def _setSortFunction(self, val):
		if self._constructed():
			if callable(val):
				self._sortFunction = val
				if not isinstance(self, dabo.ui.dListControl):
					# Force a re-ordering
					self.sort()
			else:
				raise TypeError(_("SortFunction must be callable"))
		else:
			self._properties["SortFunction"] = val


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
			except AttributeError:
				# If this is a list control, there is no native GetString.
				# Use the Dabo-supplied replacement
				try:
					strings.append(self._GetString(index))
				except IndexError:
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
						raise ValueError(_("String must be present in the choices: '%s'") % string)
					else:
						self.setSelection(index)
				else:
					raise TypeError(_("Unicode or string required."))
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
			vm = {"p": "position", "s": "string", "k": "key"}[self._valueMode]
		except AttributeError:
			vm = self._valueMode = "string"
		return vm


	def _setValueMode(self, val):
		val = ustr(val).lower()[0]
		if val in ("p", "s", "k"):
			self._valueMode = val


	# Property definitions:
	Choices = property(_getChoices, _setChoices, None,
			_("""Specifies the string choices to display in the list.
			-> List of strings. Read-write at runtime.
			The list index becomes the PositionValue, and the string
			becomes the StringValue.""") )

	Count = property(_getCount, None, None,
			_("""Number of items in the control.
			-> Integer. Read-only.""") )

	Keys = property(_getKeys, _setKeys, None,
			_("""Specifies a mapping between arbitrary values and item positions.
			-> Dictionary. Read-write at runtime.
			The Keys property is a dictionary, where each key resolves into a
			list index (position). If using keys, you should update the Keys
			property whenever you update the Choices property, to make sure they
			are in sync.
			-> Optionally, Keys can be a list/tuple that is a 1:1 mapping of the
			Choices property. So if your 3rd Choices entry is selected, KeyValue
			will return the 3rd entry in the Keys property.""") )

	KeyValue = property(_getKeyValue, _setKeyValue, None,
			_("""Specifies the key value or values of the selected item or items.
			-> Type can vary. Read-write at runtime.
			Returns the key value or values of the selected item(s), or selects
			the item(s) with the specified KeyValue(s).	An exception will be
			raised if the Keys property hasn't been set up to accomodate.""") )

	PositionValue = property(_getPositionValue, _setPositionValue, None,
			_("""Specifies the position (index) of the selected item(s).
			-> Integer or tuple of integers. Read-write at runtime.
			Returns the current position(s), or sets the current position(s).""") )

	Sorted = property(_getSorted, _setSorted, None,
			_("""Are the items in the control automatically sorted? Default=False.
			If True, whenever the Choices property is changed, the resulting list
			will be first sorted using the SortFunction property, which defaults to
			None, giving a default sort order.  (bool)"""))

	SortFunction = property(_getSortFunction, _setSortFunction, None,
			_("""Function used to sort list items when Sorted=True. Default=None,
			which gives the default sorting  (callable or None)"""))

	StringValue = property(_getStringValue, _setStringValue, None,
			_("""Specifies the text of the selected item.
			-> String or tuple of strings. Read-write at runtime.
			Returns the text of the selected item(s), or selects the item(s)
			with the specified text. An exception is raised if there is no
			position with matching text.""") )

	Value = property(_getValue, _setValue, None,
			_("""Specifies which item is currently selected in the list.
			-> Type can vary. Read-write at runtime.
			Value refers to one of the following, depending on the setting of ValueMode:

				+ ValueMode="Position" : the index of the selected item(s) (integer)
				+ ValueMode="String"   : the displayed string of the selected item(s) (string)
				+ ValueMode="Key"      : the key of the selected item(s) (can vary)""") )

	ValueMode = property(_getValueMode, _setValueMode, None,
			_("""Specifies the information that the Value property refers to.
			-> String. Read-write at runtime.

			============= =========================
			'Position'    Value refers to the position in the choices (integer).
			'String'      Value refers to the displayed string for the selection (default) (string).
			'Key'         Value refers to a separate key, set using the Keys property (can vary).
			============= =========================

			"""))

	DynamicKeyValue = makeDynamicProperty(KeyValue)
	DynamicPositionValue = makeDynamicProperty(PositionValue)
	DynamicStringValue = makeDynamicProperty(StringValue)
	DynamicValue = makeDynamicProperty(Value)
	DynamicValueMode = makeDynamicProperty(ValueMode)
