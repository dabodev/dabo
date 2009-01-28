# -*- coding: utf-8 -*-
import re
import datetime
import time
import locale
import wx
import wx.lib.masked as masked
import dabo.lib.dates

import decimal
numericTypes = (int, long, decimal.Decimal, float)
valueErrors = (ValueError, decimal.InvalidOperation)

# Make this locale-independent
decimalPoint = locale.localeconv()["decimal_point"]

import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from dabo.ui import makeDynamicProperty


class dTextBoxMixinBase(dcm.dDataControlMixin):
	def __init__(self, preClass, parent, properties=None, attProperties=None, *args, **kwargs):
		self._oldVal = u""
		self._forceCase = None
		self._inForceCase = False
		self._inFlush = False
		self._textLength = None
		self._inTextLength = False
		self._flushOnLostFocus = True  ## see dabo.ui.dDataControlMixinBase::flushValue()
		
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
	
	
	def _initEvents(self):
		super(dTextBoxMixinBase, self)._initEvents()
		self.Bind(wx.EVT_TEXT, self._onWxHit)
	
	
	def flushValue(self):
		# Call the wx SetValue() directly to reset the string value displayed to the user.
		# This resets the value to the string representation as Python shows it. Also, we
		# must save and restore the InsertionPosition because wxGtk at least resets it to
		# 0 upon SetValue().
		if self._inFlush:
			return
		self._inFlush = True
		self._updateStringDisplay()
		ret = super(dTextBoxMixinBase, self).flushValue()
		self._inFlush = False
		return ret
	

	def _updateStringDisplay(self):
		insPos = self.InsertionPosition
		startPos = self.SelectionStart
		endPos = self.SelectionEnd
		setter = self.SetValue
		if hasattr(self, "ChangeValue"):
			setter = self.ChangeValue
		setter(self.getStringValue(self.Value))
		self.InsertionPosition = insPos
		self.SelectionStart = startPos
		self.SelectionEnd = endPos
		
	
	def getStringValue(self, val):
		"""Hook function if you want to implement dataTypes other than str"""
		return val
	
	
	def selectAll(self):
		"""Each subclass must define their own selectAll method. This will 
		be called if SelectOnEntry is True when the control gets focus.
		"""
		self.SetSelection(-1, -1)
		
		
	def getBlankValue(self):
		return ""
	
	
	def __onKeyChar(self, evt):
		"""This handles KeyChar events when ForceCase is set to a non-empty value."""
		if not self:
			# The control is being destroyed
			return
		keyChar = evt.keyChar
		if keyChar is not None and (keyChar.isalnum() 
				or keyChar in """,./<>?;':"[]\\{}|`~!@#$%%^&*()-_=+"""):
			dabo.ui.callAfter(self._checkForceCase)
			dabo.ui.callAfter(self._checkTextLength)
			
	
	def _checkTextLength(self):
		"""If the TextLength property is set, checks the current value of the control
		and truncates it if too long"""
		if not self:
			# The control is being destroyed
			return
		if not isinstance(self.Value, basestring):
			#Don't bother if it isn't a string type
			return
		length = self.TextLength
		if not length:
			return
		
		insPos = self.InsertionPosition
		self._inTextLength = True
		if len(self.Value) > length:
			self.Value = self.Value[:length]
			if insPos > length:
				self.InsertionPosition = length
			else:
				self.InsertionPosition = insPos
			self.refresh()
		self._inTextLength = False
	

	def _checkForceCase(self):
		"""If the ForceCase property is set, casts the current value of the control
		to the specified case.
		"""
		if not self:
			# The control is being destroyed
			return
		if not isinstance(self.Value, basestring):
			# Don't bother if it isn't a string type
			return
		case = self.ForceCase
		if not case:
			return
		insPos = self.InsertionPosition
		selLen = self.SelectionLength
		changed = False
		self._inForceCase = True
		if case == "upper":
			self.Value = self.Value.upper()
			changed = True
		elif case == "lower":
			self.Value = self.Value.lower()
			changed = True
		elif case == "title":
			self.Value = self.Value.title()
			changed = True
		if changed:
			#self.SelectionStart = selStart
			self.InsertionPosition = insPos
			self.SelectionLength = selLen
			self.refresh()
		self._inForceCase = False
	
	
	# property get/set functions
	def _getAlignment(self):
		if self._hasWindowStyleFlag(wx.TE_RIGHT):
			return "Right"
		elif self._hasWindowStyleFlag(wx.TE_CENTRE):
			return "Center"
		else:
			return "Left"

	def _setAlignment(self, val):
		if self._constructed():
			# Note: alignment doesn't seem to work, at least on GTK2
			# Second note: setting the Alignment flag seems to change
			# the control to Read-Write if it had previously been set to
			# ReadOnly=True.
			rw = self.IsEditable()
			self._delWindowStyleFlag(wx.TE_LEFT)
			self._delWindowStyleFlag(wx.TE_CENTRE)
			self._delWindowStyleFlag(wx.TE_RIGHT)
			val = val[0].lower()
			if val == "l":
				self._addWindowStyleFlag(wx.TE_LEFT)
			elif val == "c":
				self._addWindowStyleFlag(wx.TE_CENTRE)
			elif val == "r":
				self._addWindowStyleFlag(wx.TE_RIGHT)
			else:
				raise ValueError(_("The only possible values are 'Left', 'Center', and 'Right'"))
			self.SetEditable(rw)
		else:
			self._properties["Alignment"] = val
			
	
	def _getForceCase(self):
		return self._forceCase
	
	def _setForceCase(self, val):
		if self._constructed():
			if val is None:
				valKey = None
			else:
				valKey = val[0].upper()
			self._forceCase = {"U": "upper", "L": "lower", "T": "title", None: None,
					"None": None}.get(valKey)
			self._checkForceCase()
			self.unbindEvent(dEvents.KeyChar, self.__onKeyChar)
			if self._forceCase or self._textLength:
				self.bindEvent(dEvents.KeyChar, self.__onKeyChar)
		else:
			self._properties["ForceCase"] = val
	
	
	def _getInsertionPosition(self):
		return self.GetInsertionPoint()
	
	def _setInsertionPosition(self, val):
		self.SetInsertionPoint(val)
	
	
	def _getReadOnly(self):
		return not self.IsEditable()
		
	def _setReadOnly(self, val):
		if self._constructed():
			self.SetEditable(not bool(val))
		else:
			self._properties["ReadOnly"] = val
	
	
	def _getSelectedText(self):
		return self.GetStringSelection()
	
	
	def _getSelectionEnd(self):
		return self.GetSelection()[1]
	
	def _setSelectionEnd(self, val):
		start, end = self.GetSelection()
		self.SetSelection(start, val)
		self.refresh()
	
	
	def _getSelectionLength(self):
		start, end = self.GetSelection()
		return end - start
	
	def _setSelectionLength(self, val):
		start = self.GetSelection()[0]
		self.SetSelection(start, start + val)
		self.refresh()
	
	
	def _getSelectionStart(self):
		return self.GetSelection()[0]
	
	def _setSelectionStart(self, val):
		start, end = self.GetSelection()
		self.SetSelection(val, end)
		self.refresh()
	
	
	def _getSelectOnEntry(self):
		try:
			return self._SelectOnEntry
		except AttributeError:
			return False
			
	def _setSelectOnEntry(self, val):
		self._SelectOnEntry = bool(val)
	
	
	def _getTextLength(self):
		return self._textLength
	
	def _setTextLength(self, val):
		if self._constructed():
			if val == None:
				self._textLength = None
			else:
				val = int(val)
				if val < 1:
					raise ValueError('TextLength must be a positve Integer')
				self._textLength = val
			self._checkTextLength()
			
			self.unbindEvent(dEvents.KeyChar, self.__onKeyChar)
			if self._forceCase or self._textLength:
				self.bindEvent(dEvents.KeyChar, self.__onKeyChar)
		else:
			self._properties["TextLength"] = val
	
	
	def _getValue(self):
		try:
			_value = self._value
		except AttributeError:
			_value = self._value = unicode("")
		
		# Get the string value as reported by wx, which is the up-to-date 
		# string value of the control:
		strVal = self.GetValue()
		
		if _value is None:
			if strVal == self.Application.NoneDisplay:
				# Keep the value None
				return None
		return strVal
	
	def _setValue(self, val):
		if self._constructed():
			setter = self.SetValue
			if hasattr(self, "ChangeValue"):
				setter = self.ChangeValue
			if self._inForceCase:
				# Value is changing internally. Don't update the oldval
				# setting or change the type; just set the value.
				setter(val)
				return
			else:
				dabo.ui.callAfter(self._checkForceCase)
			
			if self._inTextLength:
				# Value is changing internally. Don't update the oldval
				# setting or change the type; just set the value.
				setter(val)
				return
			else:
				dabo.ui.callAfter(self._checkTextLength)
		
			if val is None:
				strVal = self.Application.NoneDisplay
			else:
				strVal = val
			_oldVal = self._oldVal = self.Value
				
			# save the actual value for return by _getValue:
			self._value = val

			# Update the display no matter what:
			setter(strVal)
		
			if type(_oldVal) != type(val) or _oldVal != val:
				self._afterValueChanged()		
		else:
			self._properties["Value"] = val

	
	
	#Property Definitions
	Alignment = property(_getAlignment, _setAlignment, None,
			_("""Specifies the alignment of the text. (str)
			   Left (default)
			   Center
			   Right"""))
	
	ForceCase = property(_getForceCase, _setForceCase, None,
			_("""Determines if we change the case of entered text. Possible values are:
				None, "" (empty string): No changes made (default)
				"Upper": FORCE TO UPPER CASE
				"Lower": force to lower case
				"Title": Force To Title Case
			These can be abbreviated to "u", "l" or "t"  (str)"""))
	
	InsertionPosition = property(_getInsertionPosition, _setInsertionPosition, None,
			_("Position of the insertion point within the control  (int)"))
	
	ReadOnly = property(_getReadOnly, _setReadOnly, None, 
			_("Specifies whether or not the text can be edited. (bool)"))
	
	SelectedText = property(_getSelectedText, None, None,
			_("Currently selected text. Returns the empty string if nothing is selected  (str)"))	
	
	SelectionEnd = property(_getSelectionEnd, _setSelectionEnd, None,
			_("""Position of the end of the selected text. If no text is
			selected, returns the Position of the insertion cursor.  (int)"""))
	
	SelectionLength = property(_getSelectionLength, _setSelectionLength, None,
			_("Length of the selected text, or 0 if nothing is selected.  (int)"))
	
	SelectionStart = property(_getSelectionStart, _setSelectionStart, None,
			_("""Position of the beginning of the selected text. If no text is
			selected, returns the Position of the insertion cursor.  (int)"""))
	
	SelectOnEntry = property(_getSelectOnEntry, _setSelectOnEntry, None, 
			_("Specifies whether all text gets selected upon receiving focus. (bool)"))
	
	TextLength = property(_getTextLength, _setTextLength, None,
			_("""The maximum length the entered text can be. (int)"""))
	
	Value = property(_getValue, _setValue, None,
			_("Specifies the current state of the control (the value of the field). (string)"))
	
	
	# Dynamic property declarations
	DynamicAlignment = makeDynamicProperty(Alignment)
	DynamicInsertionPosition = makeDynamicProperty(InsertionPosition)
	DynamicReadOnly = makeDynamicProperty(ReadOnly)
	DynamicSelectionEnd = makeDynamicProperty(SelectionEnd)
	DynamicSelectionLength = makeDynamicProperty(SelectionLength)
	DynamicSelectionStart = makeDynamicProperty(SelectionStart)
	DynamicSelectOnEntry = makeDynamicProperty(SelectOnEntry)
	DynamicValue = makeDynamicProperty(Value)



class dTextBoxMixin(dTextBoxMixinBase):
	def __init__(self, preClass, parent, properties=None, attProperties=None, *args, **kwargs):
		self._dregex = {}
		self._lastDataType = unicode
		
		dTextBoxMixinBase.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
		
		# Keep passwords, etc., from being written to disk
		if self.PasswordEntry:
			self.IsSecret = True
	
	
	def convertStringValueToDataType(self, strVal, dataType):
		"""Given a string value and a type, return an appropriate value of that type.
		If the value can't be converted, a ValueError will be raised.
		"""
		if dataType == bool:
			# Bools can't convert from string representations, because a zero-
			# length denotes False, and anything else denotes True.
			if strVal == "True":
				retVal = True
			else:
				retVal = False
		elif dataType in (datetime.date, datetime.datetime, datetime.time):
			# We expect the string to be in ISO 8601 format.
			if dataType == datetime.date:
				retVal = self._getDateFromString(strVal)
			elif dataType == datetime.datetime:
				retVal = self._getDateTimeFromString(strVal)
			elif dataType == datetime.time:
				retVal = self._getTimeFromString(strVal)
				
			if retVal is None:
				raise ValueError(_("String not in ISO 8601 format."))
		elif str(dataType) == "<type 'DateTime'>":
			# mx DateTime type. MySQLdb will use this if mx is installed.
			try:
				import mx.DateTime
				retVal = mx.DateTime.DateTimeFrom(str(strVal))
			except ImportError:
				raise ValueError(_("Can't import mx.DateTime"))
		elif str(dataType) == "<type 'DateTimeDelta'>":
			# mx TimeDelta type. MySQLdb will use this for Time columns if mx is installed.
			try:
				import mx.DateTime
				retVal = mx.DateTime.TimeFrom(str(strVal))
			except ImportError:
				raise ValueError(_("Can't import mx.DateTime"))
		elif (dataType == decimal.Decimal) and self.StrictNumericEntry:
			try:
				_oldVal = self._oldVal
			except AttributeError:
				_oldVal = None

			# Preprocess trying to do a decimal conversion, to filter out
			# invalid input before doing a number of things below:
			strVal = strVal.strip()
			try:
				decimal.Decimal(strVal)
			except decimal.InvalidOperation:
				raise ValueError(_("Invalid decimal value."))
			
			try:
				if type(_oldVal) == decimal.Decimal:
					# Enforce the precision as previously set programatically
					retVal = decimal.DefaultContext.quantize(decimal.Decimal(strVal), _oldVal)
				else:
					retVal = decimal.Decimal(strVal)
			except ValueError:
				raise ValueError(_("Can't convert to decimal."))
		elif dataType in (tuple, list):
			retVal = eval(strVal)
		elif not self.StrictNumericEntry and (dataType in numericTypes):
			isint = (strVal.count(decimalPoint) == 0) and (strVal.lower().count("e") == 0)
			try:
				if isint:
					if strVal.strip().endswith("L"):
						retVal = long(strVal)
					else:
						retVal = int(strVal)
				else:
					try:
						retVal = decimal.Decimal(strVal.strip())
					except decimal.InvalidOperation:
						raise ValueError(_("Invalid decimal value."))
			except valueErrors:
				raise ValueError(_("Invalid Numeric Value: %s") % strVal)
		else:
			# Other types can convert directly.
			if dataType == str:
				dataType = unicode
			try:
				retVal = dataType(strVal)
			except ValueError:
				# The Python object couldn't convert it. Our validator, once 
				# implemented, won't let the user get this far. Just keep the 
				# old value.
				raise ValueError(_("Can't convert."))
		return retVal
	
	
	def getStringValue(self, value):
		"""Given a value of any data type, return a string rendition.
		
		Used internally by _setValue and flushValue, but also exposed to subclasses
		in case they need specialized behavior. The value returned from this 
		function will be what is displayed in the UI textbox.
		"""
		if isinstance(value, basestring):
			# keep it unicode instead of converting to str
			strVal = value
		elif isinstance(value, datetime.datetime):
			strVal = dabo.lib.dates.getStringFromDateTime(value)
		elif isinstance(value, datetime.date):
			strVal = dabo.lib.dates.getStringFromDate(value)
		elif isinstance(value, datetime.time):
			# Use the ISO 8601 time string format
			strVal = value.isoformat()
		elif value is None:
			strVal = self.Application.NoneDisplay
		else:
			# convert all other data types to string:
			strVal = str(value)   # (floats look like 25.55)
			#strVal = repr(value) # (floats look like 25.55000000000001)
		return strVal
	
	
	def _getDateFromString(self, strVal):
		"""Given a string in an accepted date format, return a 
		datetime.date object, or None.
		"""
		formats = ["ISO8601"]
		if not self.StrictDateEntry:
			# Add some less strict date-entry formats:
			formats.append("YYYYMMDD")
			formats.append("YYMMDD")
			formats.append("MMDD")
			# (define more formats in dabo.lib.dates._getDateRegex, and enter 
			# them above in more explicit -> less explicit order.)
		return dabo.lib.dates.getDateFromString(strVal, formats)
	
	
	def _getDateTimeFromString(self, strVal):
		"""Given a string in ISO 8601 datetime format, return a 
		datetime.datetime object.
		"""
		formats = ["ISO8601"]
		if not self.StrictDateEntry:
			# Add some less strict date-entry formats:
			formats.append("YYYYMMDDHHMMSS")
			formats.append("YYMMDDHHMMSS")
			formats.append("YYYYMMDD")
			formats.append("YYMMDD")
			# (define more formats in dabo.lib.dates._getDateTimeRegex, and enter 
			# them above in more explicit -> less explicit order.)
		return dabo.lib.dates.getDateTimeFromString(strVal, formats)
	
	
	def _getTimeFromString(self, strVal):
		"""Given a string in ISO 8601 time format, return a 
		datetime.time object.
		"""
		formats = ["ISO8601"]
		return dabo.lib.dates.getTimeFromString(strVal, formats)
	
	
	def _getPasswordEntry(self):
		return self._hasWindowStyleFlag(wx.TE_PASSWORD)
	
	def _setPasswordEntry(self, val):
		self._delWindowStyleFlag(wx.TE_PASSWORD)
		if val:
			self._addWindowStyleFlag(wx.TE_PASSWORD)
			self.IsSecret = True
	
	
	def _getStrictDateEntry(self):
		try:
			ret = self._strictDateEntry
		except AttributeError:
			ret = self._strictDateEntry = False
		return ret
	
	def _setStrictDateEntry(self, val):
		self._strictDateEntry = bool(val)
	
	
	def _getStrictNumericEntry(self):
		try:
			ret = self._strictNumericEntry
		except AttributeError:
			ret = self._strictNumericEntry = True
		return ret

	def _setStrictNumericEntry(self, val):
		if self._constructed():
			self._strictNumericEntry = val
		else:
			self._properties["StrictNumericEntry"] = val


	#Overrides the dTextBoxMixinBase getter and setters because of the data conversion
	#introduced in this class
	def _getValue(self):
		# Return the value as reported by wx, but convert it to the data type as
		# reported by self._value.
		try:
			_value = self._value
		except AttributeError:
			_value = self._value = unicode("")
		dataType = type(_value)
		
		# Get the string value as reported by wx, which is the up-to-date 
		# string value of the control:
		if isinstance(self, masked.TextCtrl) and hasattr(self, "_template"):
			if self.UsePlainValue:
				strVal = self.GetPlainValue()
			else:
				strVal = self.GetValue()
		else:
			strVal = self.GetValue()
		
		# Convert the current string value of the control, as entered by the 
		# user, into the proper data type.
		skipConversion = False
		if _value is None:
			if strVal == self.Application.NoneDisplay:
				# Keep the value None
				convertedVal = None
				skipConversion = True
			else:
				# User changed the None value to something else, convert to the last
				# known real datatype.
				dataType = self._lastDataType
		
		if not skipConversion:
			try:
				convertedVal = self.convertStringValueToDataType(strVal, dataType)
				if self.getStringValue(convertedVal) != self.GetValue():
					self._updateStringDisplay
			except ValueError:
				# It couldn't convert; return the previous value.
				convertedVal = self._value
		return convertedVal
	
	def _setValue(self, val):
		if self._constructed():
			# Must convert all to string for sending to wx, but our internal 
			# _value will always retain the correct type.
			
			# TextCtrls in wxPython since 2.7 have a ChangeValue() method that is to 
			# be used instead of the old SetValue().
			setter = self.SetValue
			if hasattr(self, "ChangeValue"):
				setter = self.ChangeValue

			# Todo: set up validators based on the type of data we are editing,
			# so the user can't, for example, enter a letter "p" in a textbox
			# that is currently showing numeric data.
			
			if self._inForceCase:
				# Value is changing internally. Don't update the oldval
				# setting or change the type; just set the value.
				setter(val)
				return
			else:
				dabo.ui.callAfter(self._checkForceCase)
			
			if self._inTextLength:
				# Value is changing internally. Don't update the oldval
				# setting or change the type; just set the value.
				setter(val)
				return
			else:
				dabo.ui.callAfter(self._checkTextLength)
			
			strVal = self.getStringValue(val)
			_oldVal = self._oldVal = self.Value
				
			# save the actual value for return by _getValue:
			self._value = val
			
			if val is not None:
				# Save the type of the value, so that in the case of actual None
				# assignments, we know the datatype to expect.
				self._lastDataType = type(val)

			# Update the display if it is different from what is already displayed
			# (note that if we did it unconditionally, the user's selection could
			# be reset, which isn't very nice):
			if strVal != _oldVal:
				try:
					setter(strVal)
				except ValueError, e:
					#PVG: maskedtextedit sometimes fails, on value error..allow the code to continue
					uStrVal = self.Application.str2Unicode(strVal)
					dabo.errorLog.write(_("Error setting value to '%(uStrVal)s: %(e)s") % locals())

			if type(_oldVal) != type(val) or _oldVal != val:
				self._afterValueChanged()
		else:
			self._properties["Value"] = val
	
	
	# Property definitions:
	PasswordEntry = property(_getPasswordEntry, _setPasswordEntry, None,
			_("Specifies whether plain-text or asterisks are echoed. (bool)"))
	
	StrictDateEntry = property(_getStrictDateEntry, _setStrictDateEntry, None,
			_("""Specifies whether date values must be entered in strict ISO8601 format. Default=False.

			If not strict, dates can be accepted in YYYYMMDD, YYMMDD, and MMDD format,
			which will be coerced into sensible date values automatically."""))
	
	StrictNumericEntry = property(_getStrictNumericEntry, _setStrictNumericEntry, None,
			_("""When True, the DataType will be preserved across numeric types. When False, the 
			DataType will respond to user input to convert to the 'obvious' numeric type.  
			Default=True. (bool)"""))
	
	Value = property(_getValue, _setValue, None,
			_("Specifies the current state of the control (the value of the field). (varies)"))
	
	
	# Dynamic property declarations
	DynamicPasswordEntry = makeDynamicProperty(PasswordEntry)
	DynamicStrictDateEntry = makeDynamicProperty(StrictDateEntry)
	DynamicValue = makeDynamicProperty(Value)

