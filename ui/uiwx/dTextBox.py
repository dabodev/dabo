import re, datetime
import wx, dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
from dabo.dLocalize import _

class dTextBox(wx.TextCtrl, dcm.dDataControlMixin):
	""" Allows editing one line of string or unicode data.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dTextBox
		preClass = wx.PreTextCtrl
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	
	def _initEvents(self):
		super(dTextBox, self)._initEvents()
		self.Bind(wx.EVT_TEXT, self._onWxHit)
		
		
	def flushValue(self):
		# Call the wx SetValue() directly to reset the string value displayed to the user.
		# This resets the value to the string representation as Python shows it.
		self.SetValue(self._getStringValue(self.Value))
			
		# Now that the dabo Value is set properly, the default behavior that flushes 
		# the value to the bizobj can be called:
		super(dTextBox, self).flushValue()
	
	
	def selectAll(self):
		"""Each subclass must define their own selectAll method. This will 
		be called if SelectOnEntry is True when the control gets focus.
		"""
		self.SetSelection(-1, -1)
		
		
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
		return not self.IsEditable()
	def _setReadOnly(self, value):
		if self._constructed():
			self.SetEditable(not bool(value))
		else:
			self._properties["ReadOnly"] = value


	def _getPasswordEntry(self):
		return self.hasWindowStyleFlag(wx.TE_PASSWORD)

	def _setPasswordEntry(self, value):
		self.delWindowStyleFlag(wx.TE_PASSWORD)
		if value:
			self.addWindowStyleFlag(wx.TE_PASSWORD)
	
	def _getSelectOnEntry(self):
		try:
			return self._SelectOnEntry
		except AttributeError:
			return False
	def _setSelectOnEntry(self, value):
		self._SelectOnEntry = bool(value)

		
	def _getValue(self):
		# Return the value as reported by wx, but convert it to the data type as
		# reported by self._value.
		try:
			_value = self._value
		except AttributeError:
			_value = self._value = ""
		dataType = type(_value)
		
		# Get the string value as reported by wx, which is the up-to-date 
		# string value of the control:
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
		elif dataType in (datetime.date, datetime.datetime):
			# We expect the string to be in ISO 8601 format.
			if dataType == datetime.date:
				value = self._getDateFromString(strVal)
			elif dataType == datetime.datetime:
				value = self._getDateTimeFromString(strVal)
				
			if value is None:
				# String wasn't in ISO 8601 format... put it back to a valid
				# string with the previous value and the user will have to 
				# try again.
				dabo.errorLog.write("Couldn't convert literal '%s' to %s."
					% (strVal, dataType))
				value = self._value
				
		elif str(dataType) == "<type 'DateTime'>":
			# mx DateTime type. MySQLdb will use this if mx is installed.
			try:
				import mx.DateTime
				value = mx.DateTime.DateTimeFrom(str(strVal))
			except ImportError:
				value = self._value
		
		else:
			# Other types can convert directly.
			try:
				value = dataType(strVal)
			except (ValueError, TypeError):
				# The Python object couldn't convert it. Our validator, once 
				# implemented, won't let the user get this far. In the meantime, 
				# log the Error and just keep the old value.
				dabo.errorLog.write("Couldn't convert literal '%s' to %s." 
					% (strVal, dataType))
				value = self._value
		return value		
	
					
	def _setValue(self, value):
		if self._constructed():
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
		else:
			self._properties["Value"] = value

		
	def _getStringValue(self, value):
		"""Given a value of any data type, return a string rendition.
		
		Used internally by _setValue and flushValue.
		"""
		if isinstance(value, basestring):
			# keep it unicode instead of converting to str
			strVal = value
		elif isinstance(value, datetime.date):
			# Use the ISO 8601 date string format so we can convert
			# back from a known quantity later...
			strVal = value.isoformat()
		elif isinstance(value, datetime.datetime):
			# Use the ISO 8601 datetime string format (with a " " separator
			# instead of "T") 
			strVal = value.isoformat(" ")
		else:
			# convert all other data types to string:
			strVal = str(value)   # (floats look like 25.55)
			#strVal = repr(value) # (floats look like 25.55000000000001)
		return strVal

		
	def _getDateFromString(self, string):
		"""Given a string in ISO 8601 date format, return a 
		datetime.date object.
		"""
		try:
			regex = self._dregex
		except AttributeError:
			regex = self._dregex = re.compile(self._getDateRegex())
			
		m = regex.match(string)
		if m is not None:
			groups = m.groupdict()
			try:		
				return datetime.date(int(groups["year"]), 
					int(groups["month"]),
					int(groups["day"]))
			except ValueError:
				# Could be that the day was out of range for the particular month
				# (Sept. only has 30 days but the regex will allow 31, etc.)
				return None
		else:
			# The regex didn't match
			return None
	
	def _getDateRegex(self):
		exp = {}
		exp["year"] = "(?P<year>[0-9]{4,4})"              ## year 0000-9999
		exp["month"] = "(?P<month>0[1-9]|1[012])"         ## month 01-12
		exp["day"] = "(?P<day>0[1-9]|[1-2][0-9]|3[0-1])"  ## day 01-31
		
		exps = "^%s-%s-%s$" % (exp["year"], exp["month"], exp["day"])
			
		return re.compile(exps)

			
	def _getDateTimeFromString(self, string):
		"""Given a string in ISO 8601 datetime format, return a 
		datetime.datetime object.
		"""
		try:
			regex = self._dtregex
		except AttributeError:
			regex = self._dtregex = re.compile(self._getDateTimeRegex())
			
		m = regex.match(string)
		if m is not None:
			groups = m.groupdict()
			if len(groups["ms"]) == 0:
				# no ms in the expression
				groups["ms"] = 0
		
			try:		
				return datetime.datetime(int(groups["year"]), 
					int(groups["month"]),
					int(groups["day"]),
					int(groups["hour"]),
					int(groups["minute"]),
					int(groups["second"]),
					int(groups["ms"]))
			except ValueError:
				# Could be that the day was out of range for the particular month
				# (Sept. only has 30 days but the regex will allow 31, etc.)
				return None
		else:
			# The regex didn't match
			return None
	
	def _getDateTimeRegex(self):
		exp = {}
		exp["year"] = "(?P<year>[0-9]{4,4})"              ## year 0000-9999
		exp["month"] = "(?P<month>0[1-9]|1[012])"         ## month 01-12
		exp["day"] = "(?P<day>0[1-9]|[1-2][0-9]|3[0-1])"  ## day 01-31
		exp["hour"] = "(?P<hour>[0-1][0-9]|2[0-3])"       ## hour 00-23
		exp["minute"] = "(?P<minute>[0-5][0-9])"          ## minute 00-59
		exp["second"] = "(?P<second>[0-5][0-9])"          ## second 00-59
		exp["ms"] = "\.{0,1}(?P<ms>[0-9]{0,6})"           ## optional ms
		
		exps = "^%s-%s-%s %s:%s:%s%s$" % (exp["year"], exp["month"],
			exp["day"], exp["hour"], exp["minute"], exp["second"], exp["ms"])
			
		return re.compile(exps)

			
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
			self.Value = 23
		
	class FloatText(TestBase):
		def afterInit(self):
			self.Value = 23.5
	
	class BoolText(TestBase):
		def afterInit(self):
			self.Value = False
	
	class StrText(TestBase):
		def afterInit(self):
			self.Value = "Lunchtime"

	class DateText(TestBase):
		def afterInit(self):
			self.Value = datetime.date.today()
	
	class DateTimeText(TestBase):
		def afterInit(self):
			self.Value = datetime.datetime.now()
	
	testParms = [IntText, FloatText, StrText, BoolText, DateText, DateTimeText]			
	
	try:
		import mx.DateTime
		class MxDateTimeText(TestBase):
			def afterInit(self):
				self.Value = mx.DateTime.now()
				
		testParms.append(MxDateTimeText)
	except:
		# skip it: mx may not be available
		pass
		
	test.Test().runTest(testParms)
