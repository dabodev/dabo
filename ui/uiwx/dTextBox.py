import wx, dabo, dabo.ui
import types
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
from dabo.dLocalize import _

class dTextBox(wx.TextCtrl, dcm.dDataControlMixin):
	""" Allows editing one line of string or unicode data.
	"""
	def __init__(self, parent, id=-1, password=False, style=0, 
		properties=None, *args, **kwargs):

		self._baseClass = dTextBox
		properties = self.extractKeywordProperties(kwargs, properties)
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)

		# If this is a password textbox, update the style parameter
		if password:
			style = style | wx.TE_PASSWORD

		pre = wx.PreTextCtrl()
		self._beforeInit(pre)
		pre.Create(parent, id, style=style|pre.GetWindowStyleFlag(), *args, **kwargs)
		self.PostCreate(pre)

		dcm.dDataControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self.setProperties(properties)
		self._afterInit()

		
	def initProperties(self):
		#dTextBox.doDefault()
		super(dTextBox, self).initProperties()
		self.SelectOnEntry = True


	def initEvents(self):
		#dTextBox.doDefault()
		super(dTextBox, self).initEvents()
		# catch wx.EVT_TEXT and raise dEvents.Hit:
		self.Bind(wx.EVT_TEXT, self._onWxHit)
		
		
	def flushValue(self):
		# Overridden: need to set Value to the converted value before running 
		# the default behavior.
		dataType = type(self.Value)
		
		# Need the string value from the textbox (not the raw Value): get 
		# from wx directly:
		strVal = self.GetValue()
		
		# Convert the current string value of the control, as entered by the 
		# user, into the proper data type.
		if dataType == bool:
			# Bools can't convert from string representations, because a zero-
			# length denotes False, and anything else denotes True.
			if strVal == "True":
				value = True
			else:
				value = False
				
		else:
			# Other types can convert directly.
			try:
				value = dataType(strVal)
			except ValueError:
				# The Python object couldn't convert it. Our validator, once implemented, 
				# won't let the user get this far. In the meantime, log the Error and just keep
				# the old value.
				dabo.errorLog.write("Couldn't convert literal '%s' to %s." % (strVal, dataType))
				value = self.Value
			
		# Only update self.Value if it differs:
		if value != self.Value:
			# Update the private variable directly to avoid emitting ValueChanged twice:
			# once in the Value setter, and once when we run the superclass code below.
			self._value = value
		
		# Call the wx SetValue() directly to reset the string value displayed to the user.
		# This resets the value to the string representation as Python shows it.
		self.SetValue(self._getStringValue(value))
			
		# Now that the dabo Value is set properly, the default behavior that flushes 
		# the value to the bizobj can be called:
		super(dTextBox, self).flushValue()
		
		
	# property get/set functions
	def _getAlignment(self):
		if self.hasWindowStyleFlag(wx.TE_RIGHT):
			return "Right"
		elif self.hasWindowStyleFlag(wx.TE_CENTRE):
			return "Center"
		else:
			return "Left"

	def _getAlignmentEditorInfo(self):
		return {'editor': 'list', 'values': ['Left', 'Center', 'Right']}

	def _setAlignment(self, value):
		# Note: alignment doesn't seem to work, at least on GTK2
		self.delWindowStyleFlag(wx.TE_LEFT)
		self.delWindowStyleFlag(wx.TE_CENTRE)
		self.delWindowStyleFlag(wx.TE_RIGHT)

		value = str(value)

		if value == 'Left':
			self.addWindowStyleFlag(wx.TE_LEFT)
		elif value == 'Center':
			self.addWindowStyleFlag(wx.TE_CENTRE)
		elif value == 'Right':
			self.addWindowStyleFlag(wx.TE_RIGHT)
		else:
			raise ValueError, "The only possible values are 'Left', 'Center', and 'Right'"

	def _getReadOnly(self):
		return not self._pemObject.IsEditable()
	def _setReadOnly(self, value):
		self._pemObject.SetEditable(not bool(value))

	def _getPasswordEntry(self):
		return self.hasWindowStyleFlag(wx.TE_PASSWORD)
	def _setPasswordEntry(self, value):
		self.delWindowStyleFlag(wx.TE_PASSWORD)
		if value:
			self.addWindowStyleFlag(wx.TE_PASSWORD)
		# Note: control needs to be recreated for this flag change
		#       to take effect.
	
	def _getSelectOnEntry(self):
		try:
			return self._SelectOnEntry
		except AttributeError:
			return False
	def _setSelectOnEntry(self, value):
		self._SelectOnEntry = bool(value)

		
	def _getValue(self):
		# Override the base behavior. Just return self._value
		# which has been updated by self._setValue() and self.flushValue()
		try:
			ret = self._value
		except AttributeError:
			# The default value is an empty string
			ret = self._value = ""
		return ret
			
					
	def _setValue(self, value):
		# Must convert all to string for sending to wx, but our internal 
		# _value will always retain the correct type.
		
		# Todo: set up validators based on the type of data we are editing,
		# so the user can't, for example, enter a letter "p" in a textbox
		# that is currently showing numeric data.
		
		strVal = self._getStringValue(value)
		_oldVal = self.Value
				
		# save the actual value for return by _getValue:
		self._value = value
		
		# Update the display no matter what:
		self.SetValue(strVal)
		
		if type(_oldVal) != type(value) or _oldVal != value:
			self._afterValueChanged()

		
	def _getStringValue(self, value):
		"""Given a value of any data type, return a string rendition.
		
		Used internally by _setValue and flushValue.
		"""
		if type(value) in (str, unicode):
			# keep it unicode instead of converting to str
			strVal = value
		else:
			# convert all other data types to string:
			strVal = str(value)
		return strVal

		
	# Property definitions:
	Value = property(_getValue, _setValue, None,
			"Specifies the current state of the control (the value of the field). (varies)")

	Alignment = property(_getAlignment, _setAlignment, None,
			"Specifies the alignment of the text. (str) \n"
			"   Left (default) \n"
			"   Center \n"
			"   Right")

	ReadOnly = property(_getReadOnly, _setReadOnly, None, 
			"Specifies whether or not the text can be edited. (bool)")

	PasswordEntry = property(_getPasswordEntry, _setPasswordEntry, None,
			"Specifies whether plain-text or asterisks are echoed. (bool)")
	
	SelectOnEntry = property(_getSelectOnEntry, _setSelectOnEntry, None, 
			"Specifies whether all text gets selected upon receiving focus. (bool)")


if __name__ == "__main__":
	import test

	# This test sets up several textboxes, each editing different data types.	
	class TestBase(dTextBox):
		def initProperties(self):
			TestBase.doDefault()
			self.LogEvents = ["ValueChanged",]
			
		def initEvents(self):
			TestBase.doDefault()
			self.bindEvent(dabo.dEvents.ValueChanged, self.onValueChanged)
			
		def onValueChanged(self, evt):
			print "%s.onValueChanged:" % self.Name, self.Value, type(self.Value)
		
			
	class IntText(TestBase):
		def afterInit(self):
			IntText.doDefault()
			self.Value = 23
		
	class FloatText(TestBase):
		def afterInit(self):
			FloatText.doDefault()
			self.Value = 23.5
	
	class BoolText(TestBase):
		def afterInit(self):
			BoolText.doDefault()
			self.Value = False
	
	class StrText(TestBase):
		def afterInit(self):
			StrText.doDefault()
			self.Value = "Lunchtime"
			
	test.Test().runTest((IntText, FloatText, StrText, BoolText))
