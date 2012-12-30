# -*- coding: utf-8 -*-
import locale
import wx
import wx.lib.masked as masked
import dabo
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dTextBoxMixin as dtbm
import dDataControlMixin as ddcm
from decimal import Decimal
from types import NoneType
from dabo.dLocalize import _


class dNumericBox(dtbm.dTextBoxMixin, masked.NumCtrl):
	"""This is a specialized textbox class that maintains numeric values."""

	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		localeData = locale.localeconv()
		enc = locale.getdefaultlocale()[1]
		self._baseClass = dNumericBox
		kwargs["integerWidth"] = self._extractKey((properties, attProperties, kwargs),
				"IntegerWidth", 10)
		kwargs["fractionWidth"] = self._extractKey((properties, attProperties, kwargs),
				"DecimalWidth", 2)
		kwargs["Alignment"] = self._extractKey((properties, attProperties, kwargs),
				"Alignment", "Right")
		kwargs["selectOnEntry"] = self._extractKey((properties, attProperties, kwargs),
				"SelectOnEntry", self.SelectOnEntry)
		groupChar = self._extractKey((properties, attProperties, kwargs),
				"GroupChar", localeData["thousands_sep"].decode(enc))
		# Group char can't be empty string.
		if groupChar or groupChar >= " ":
			kwargs["groupChar"] = groupChar
			kwargs["groupDigits"] = True
		else:
			kwargs["groupChar"] = " "
			kwargs["groupDigits"] = False
		kwargs["autoSize"] = self._extractKey((properties, attProperties, kwargs),
				"AutoWidth", True)
		kwargs["allowNegative"] = self._extractKey((properties, attProperties, kwargs),
				"AllowNegative", True)
		kwargs["useParensForNegatives"] = self._extractKey((properties, attProperties, kwargs),
				"ParensForNegatives", False)
		kwargs["decimalChar"] = self._extractKey((properties, attProperties, kwargs),
				"DecimalChar", localeData["decimal_point"].decode(enc))
		kwargs["foregroundColour"] = self._extractKey((properties, attProperties, kwargs),
				"ForeColor", "Black")
		kwargs["validBackgroundColour"] = self._extractKey((properties, attProperties, kwargs),
			"BackColor", wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
		kwargs["invalidBackgroundColour"] = self._extractKey((properties, attProperties, kwargs),
				"InvalidBackColor", "Yellow")
		kwargs["signedForegroundColour"] = self._extractKey((properties, attProperties, kwargs),
				"SignedForeColor", "Red")
		kwargs["allowNone"] = self._extractKey((properties, attProperties, kwargs),
				"AllowNoneValue", False)
		kwargs["max"] = self._extractKey((properties, attProperties, kwargs),
				"MaxValue", None)
		kwargs["min"] = self._extractKey((properties, attProperties, kwargs),
				"MinValue", None)
		# Base class 'limited' property is inconvenient.
		kwargs["limited"] = False
		fontFace = self._extractKey((properties, attProperties, kwargs), "FontFace", "")
		if not fontFace and self.Application.Platform in ("Win",):
			fontFace = "Tahoma"
		elif not fontFace and self.Application.Platform in ("Mac",):
			fontFace = "Lucida Grande"
		if fontFace:
			 kwargs["FontFace"] = fontFace
		dtbm.dTextBoxMixin.__init__(self, masked.NumCtrl, parent, properties,
				attProperties, *args, **kwargs)

	#--- Public interface.

	def flushValue(self):
		# Because dTextBoxMixin method is improper here,
		# we use superclass method instead.
		return ddcm.dDataControlMixin.flushValue(self)

	def getBlankValue(self):
		dec = self.DecimalWidth
		if dec > 0:
			return Decimal("0.%s" % ("0" * dec))
		else:
			return 0

	def GetParensForNegatives(self):
		return self._useParensForNegatives

	def update(self):
		# Be very careful! If limits across allowed value,
		# control value will be automatically reseted to default value.
		maxVal = self.MaxValue
		self.MaxValue = None
		minVal = self.MinValue
		self.MinValue = None
		super(dNumericBox, self).update()
		if not "MaxValue" in self._dynamic:
			self.MaxValue = maxVal
		if not "MinValue" in self._dynamic:
			self.MinValue = minVal

	#--- Internal class interface.

	def _initEvents(self):
		super(dNumericBox, self)._initEvents()
		self.bindEvent(dEvents.GotFocus, self._onGotFocusFix)
		self.bindEvent(dEvents.LostFocus, self._onLostFocusFix)

	def _onGotFocusFix(self, evt):
		dabo.ui.callAfter(self._fixInsertionPoint)


	def _onLostFocusFix(self, evt):
		if self.LimitValue:
			max = self.MaxValue
			min = self.MinValue
			#if (max is not None and not (max >= self._value)) or \
			#		(min is not None and not (self._value >= min)):
			#	evt.stop()
			#	self.setFocus()

	def _onWxHit(self, evt, *args, **kwargs):
		# This fix wx masked controls issue firing multiple EVT_TEXT events.
		if self._value != self.Value:
			super(dNumericBox, self)._onWxHit(evt, *args, **kwargs)

	def _fixInsertionPoint(self):
		"""Fixes insertion point position when value change or
		when getting focus with mouse click."""
		if self.Enabled and not self.ReadOnly:
			dw = self.DecimalWidth
			if dw > 0:
				self.InsertionPoint = self._masklength - dw - 1
			else:
				self.InsertionPoint = self._masklength
			if self.SelectOnEntry:
				dabo.ui.callAfter(self.select, 0, self.InsertionPoint)

	#--- Properties methods.

	def _getGroupChar(self):
		if self.GetGroupDigits():
			ret = self.GetGroupChar()
		else:
			ret = None
		return ret

	def _setGroupChar(self, val):
		"""Set GroupChar to None to avoid grouping."""
		if self._constructed():
			if val is None:
				self.SetGroupDigits(False)
			else:
				self.SetGroupChar(val)
				self.SetGroupDigits(True)
		else:
			self._properties["GroupChar"] = val

	def _getAllowNegative(self):
		return self.GetAllowNegative()

	def _setAllowNegative(self, val):
		if self._constructed():
			self.SetAllowNegative(val)
		else:
			self._properties["AllowNegative"] = val

	def _getAllowNoneValue(self):
		return self.GetAllowNone()

	def _setAllowNoneValue(self, val):
		if self._constructed():
			self.SetAllowNone(val)
		else:
			self._properties["AllowNoneValue"] = val

	def _getAutoWidth(self):
		return self.GetAutoSize()

	def _setAutoWidth(self, val):
		if self._constructed():
			self.SetAutoSize(val)
		else:
			self._properties["AutoWidth"] = val

	def _getLimitValue(self):
		return getattr(self, "_limitValue", False)


	def _setLimitValue(self, val):
		self._limitValue = bool(val)

	def _getMinValue(self):
		val = self.GetMin()
		if val is not None and self._lastDataType is Decimal:
			val = Decimal(str(val))
		return val

	def _setMinValue(self, val):
		if self._constructed():
			if isinstance(val, Decimal):
				val = float(val)
			self.SetMin(val)
		else:
			self._properties["MinValue"] = val

	def _getMaxValue(self):
		val = self.GetMax()
		if val is not None and self._lastDataType is Decimal:
			val = Decimal(str(val))
		return val

	def _setMaxValue(self, val):
		if self._constructed():
			if isinstance(val, Decimal):
				val = float(val)
			self.SetMax(val)
		else:
			self._properties["MaxValue"] = val

	def _getIntegerWidth(self):
		return self.GetIntegerWidth()

	def _setIntegerWidth(self, val):
		if self._constructed():
			self.SetIntegerWidth(val)
		else:
			self._properties["IntegerWidth"] = val

	def _getInvalidBackColor(self):
		return self.GetInvalidBackgroundColour()

	def _setInvalidBackColor(self, val):
		if self._constructed():
			self.SetInvalidBackgroundColour(val)
		else:
			self._properties["InvalidBackColor"] = val

	def _getDecimalChar(self):
		return self.GetDecimalChar()

	def _setDecimalChar(self, val):
		if self._constructed():
			self.SetDecimalChar(val)
		else:
			self._properties["DecimalChar"] = val

	def _getDecimalWidth(self):
		return self.GetFractionWidth()

	def _setDecimalWidth(self, val):
		if self._constructed():
			self.SetFractionWidth(val)
		else:
			self._properties["DecimalWidth"] = val

	def _getParensForNegatives(self):
		return self.GetUseParensForNegatives()

	def _setParensForNegatives(self, val):
		if self._constructed():
			self.SetUseParensForNegatives(val)
		else:
			self._properties["ParensForNegatives"] = val

	def _getSignedForeColor(self):
		return self.GetSignedForegroundColour()

	def _setSignedForeColor(self, val):
		if self._constructed():
			self.SetSignedForegroundColour(val)
		else:
			self._properties["SignedForeColor"] = val

	def _getValue(self):
		val = ddcm.dDataControlMixin._getValue(self)
		if self._lastDataType is Decimal:
			val = Decimal(str(val))
		elif self._lastDataType is NoneType:
			chkVal = int(val)
			if chkVal != val:
				val = Decimal(str(val))
			elif chkVal <> 0:
				val = chkVal
			else:
				val = None
		return val

	def _setValue(self, val):
		self._lastDataType = type(val)
		if self._lastDataType is Decimal:
			val = float(val)
		elif val is None:
			val = float(0)
		ddcm.dDataControlMixin._setValue(self, val)
		dabo.ui.callAfter(self._fixInsertionPoint)

	def _getSelectOnEntry(self):
		try:
			return self.GetSelectOnEntry()
		except AttributeError:
			return False

	def _setSelectOnEntry(self, val):
		self.SetSelectOnEntry(bool(val))

	#--- Properties definitions.

	AllowNegative = property(_getAllowNegative, _setAllowNegative, None,
			_("""Enables/disables negative numbers. (bool)
			Default=True"""))

	AllowNoneValue = property(_getAllowNoneValue, _setAllowNoneValue, None,
			_("""Enables/disables undefined value - None. (bool)
			Default=False"""))

	AutoWidth = property(_getAutoWidth, _setAutoWidth, None,
			_("""Indicates whether or not the control should set its own
			width based on the integer and fraction widths. (bool)
			Default=True"""))

	DecimalChar = property(_getDecimalChar, _setDecimalChar, None,
			_("""Defines character that will be used to represent
			the decimal point. (str)
			Default value comes from locale setting."""))

	DecimalWidth = property(_getDecimalWidth, _setDecimalWidth, None,
			_("""Tells how many decimal places to show for numeric value. (int)
			Default=2"""))

	GroupChar = property(_getGroupChar, _setGroupChar, None,
			_("""What grouping character will be used if allowed.
			If set to None, no grouping is allowed. (str)
			Default value comes from locale setting."""))

	IntegerWidth = property(_getIntegerWidth, _setIntegerWidth, None,
			_("""Indicates how many places to the right of any decimal point
	        should be allowed in the control. (int)
	        Default=10"""))

	InvalidBackColor = property(_getInvalidBackColor, _setInvalidBackColor, None,
			_("""Color value used for illegal values or values
			out-of-bounds. (str)
			Default='Yellow'"""))

	LimitValue = property(_getLimitValue, _setLimitValue, None,
			_("""Limit control value to Min and Max bounds. When set to True,
			if invalid, will be automatically reseted to default.
			When False, only background color will change. (bool)
			Default=False"""))

	MaxValue = property(_getMaxValue, _setMaxValue, None,
			_("""The maximum value that the control should allow.
			Set to None if limit is disabled. (int, decimal)
			Default=None"""))

	MinValue = property(_getMinValue, _setMinValue, None,
			 _("""The minimum value that the control should allow.
			Set to None if limit is disabled. (int, decimal)
			Default=None"""))

	ParensForNegatives = property(_getParensForNegatives, _setParensForNegatives, None,
			_("""If true, this will cause negative numbers to be displayed with parens
			rather than with sign mark. (bool)
			Default=False"""))

	SelectOnEntry = property(_getSelectOnEntry, _setSelectOnEntry, None,
			_("""Specifies whether all text gets selected upon receiving focus. (bool)
			Default=False"""))

	SignedForeColor = property(_getSignedForeColor, _setSignedForeColor, None,
			_("""Color value used for negative values of the control. (str)
			Default='Red'"""))

	Value = property(_getValue, _setValue, None,
			_("""Specifies the current state of the control (the value of the field).
			(int, Decimal)"""))

	DynamicMaxValue = makeDynamicProperty(MaxValue)
	DynamicMinValue = makeDynamicProperty(MinValue)


if __name__ == "__main__":
	import test

	class _testDecimal2(dNumericBox):
		def initProperties(self):
			self.Value = Decimal("1.23")
			self.DecimalWidth = 3

	class _testDecimal0(dNumericBox):
		def initProperties(self):
			self.Value = Decimal("23")
			self.DecimalWidth = 0
	test.Test().runTest((_testDecimal2, _testDecimal0))
