# -*- coding: utf-8 -*-
"""
@note: Color setting doesn't work for this control. It's a wx issue.
"""
import datetime
import wx
import dabo
if __name__ == "__main__":
	import dabo.ui
	dabo.ui.loadUI("wx")
import dDataControlMixin as dcm
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.ui import makeDynamicProperty


def dateTimePy2Wx(date):
	if isinstance(date, datetime.date):
		retVal = wx.DateTimeFromDMY(date.day, date.month - 1, date.year)
	elif isinstance(date, datetime.datetime):
		retVal = wx.DateTimeFromDMY(date.day, date.month - 1, date.year, date.hour,
			date.minute, date.second, date.microsecond)
	else:
		retVal = date
	return retVal


def dateTimeWx2Py(date):
	if date.IsValid():
		retVal = datetime.datetime(
			date.GetYear(),
			date.GetMonth() + 1,
			date.GetDay(),
			date.GetHour(),
			date.GetMinute(),
			date.GetSecond(),
			date.GetMillisecond()
		)
	else:
		retVal = None
	return retVal


class dDatePicker(dcm.dDataControlMixin, wx.DatePickerCtrl):
	"""
	Creates a DatePicker control.
	Control purpose is to maintain Date field types, but it can
	be used for Timestamp data field types too.
	It's behavior is similar to dDateTextBox control.
	"""

	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._invalidBackColor = "Yellow"
		self._valueMode = "d"
		self._timePart = [0, 0, 0, 0]
		self._lastWasNone = True
		self._baseClass = dDatePicker
		preClass = wx.PreDatePickerCtrl
		pickerMode = self._extractKey((properties, attProperties, kwargs),
				"PickerMode", "Dropdown")[:1].lower()
		if pickerMode not in "ds":
			pickerMode = "d"
		kwargs["style"] = kwargs.get("style", 0) | \
			 {"d": wx.DP_DROPDOWN, "s": wx.DP_SPIN}[pickerMode]
		if self._extractKey((properties, attProperties, kwargs), "AllowNullDate", False):
			kwargs["style"] |= wx.DP_ALLOWNONE
		if self._extractKey((properties, attProperties, kwargs), "ForceShowCentury", False):
			kwargs["style"] |= wx.DP_SHOWCENTURY
		dcm.dDataControlMixin.__init__(self, preClass, parent,
			properties, attProperties, *args, **kwargs)
		self._bindKeys()

		if self.AllowNullDate:
			self.SetValue(None) # Need this for the datetime not to display the current date when Null.

	def _initEvents(self):
		super(dDatePicker, self)._initEvents()
		self.Bind(wx.EVT_DATE_CHANGED, self._onWxHit)

	def _onWxHit(self, evt):
		self._userChanged = True
		self._lastWasNone = False
		self.flushValue()
		super(dDatePicker, self)._onWxHit(evt)

	def dayInterval(self, days):
		"""Adjusts the date by the given number of days; negative
		values move backwards.
		"""
		self.Value += datetime.timedelta(days)

	def monthInterval(self, months):
		"""Adjusts the date by the given number of months; negative
		values move backwards.
		"""
		val = self.Value
		mn = val.month + months
		yr = val.year
		dy = val.day
		while mn < 1:
			yr -= 1
			mn += 12
		while mn > 12:
			yr += 1
			mn -= 12
		# May still be an invalid day for the selected month
		ok = False
		while not ok:
			try:
				val = val.replace(year=yr, month=mn, day=dy)
				ok = True
			except ValueError:
				dy -= 1
		self.Value = val

	def setCurrentDate(self):
		if self._valueMode == "d":
			val = datetime.date.today()
		else:
			val = datetime.datetime.now()
		self.Value = val

	def setToMonthDay(self, day):
		val = self.Value
		if isinstance(day, basestring):
			if day[:1].lower() == "f":
				val = val.replace(day=1)
			elif day[:1].lower() == "l":
				mn = val.month
				td = datetime.timedelta(1)
				while mn == val.month:
					val += td
				# We're now at the first of the next month. Go back one.
				val -= td
		else:
			val = val.replace(day=day)
		self.Value = val

	def setToYearDay(self, day):
		val = self.Value
		if isinstance(day, basestring):
			if day[:1].lower() == "f":
				val = val.replace(month=1, day=1)
			elif day[:1].lower() == "l":
				val = val.replace(month=12, day=31)
		self.Value = val

	def _processKey(self, evt):
		key = evt.EventData["keyCode"]
		if key == 43:		# +
			self.dayInterval(1)
		elif key == 45:		# -
			self.dayInterval(-1)
		elif key == 116:	# T
			self.setCurrentDate()
		elif key == 91:		# [
			self.monthInterval(-1)
		elif key == 93:		# ]
			self.monthInterval(1)
		elif key == 109:	# m
			self.setToMonthDay("First")
		elif key == 104:	# h
			self.setToMonthDay("Last")
		elif key == 121:	# y
			self.setToYearDay("First")
		elif key == 114:	# r
			self.setToYearDay("Last")
		elif key == 100:	# d
			self._setCustomDate()
		elif key in (dabo.ui.dKeys.key_Delete, dabo.ui.dKeys.key_Back):
			self.Value = None
		else:
			print key

	def _setCustomDate(self):
		days = dabo.ui.getInt(
			message=_("Day shift:"), caption=_("Reschedule day"), Min= -365, Max=365)
		if days:
			self.dayInterval(days)

	def _bindKeys(self):
		# It seems that on Windows platform there is a bug in
		# control key handling implementation, because '=' key
		# is recognized as '+' key.
		# On Linux, '+' key seems to be unsupported.
		self.bindKey("+", self._processKey)
		self.bindKey("-", self._processKey)
		self.bindKey("d", self._processKey)
		self.bindKey("t", self._processKey)
		self.bindKey("[", self._processKey)
		self.bindKey("]", self._processKey)
		self.bindKey("m", self._processKey)
		self.bindKey("h", self._processKey)
		self.bindKey("y", self._processKey)
		self.bindKey("r", self._processKey)
		self.bindKey("=", self._processKey)
		self.bindKey("backspace", self._processKey)
		self.bindKey("delete", self._processKey)

	def _getPyValue(self, val):
		if self._lastWasNone:
			val = None
		elif val:
			if self._valueMode == "d":
				val = datetime.date(val.year, val.month, val.day)
			else:
				val = val.combine(val, datetime.time(
						self._timePart[0],
						self._timePart[1],
						self._timePart[2],
						self._timePart[3]
					)
				)

		return val

	def _getWxValue(self, val):
		if isinstance(val, basestring):
			val = datetime.datetime.strptime(val, "%Y-%m-%d")
		elif isinstance(val, tuple):
			val = datetime.datetime(*val)
		elif isinstance(val, wx.DateTime):
			return val
		if val is not None:
			self._valueMode = "d" if type(val) == datetime.date else "t"
		if self._valueMode == "t":
			if val is None:
				self._timePart = [0, 0, 0, 0]
			else:
				self._timePart[0] = val.hour
				self._timePart[1] = val.minute
				self._timePart[2] = val.second
				self._timePart[3] = val.microsecond
		if val is None:
			self._lastWasNone = True
			if self.AllowNullDate:
				val = wx.DateTime()
			else:
				val = self.GetLowerLimit()
		else:
			self._lastWasNone = False
			val = dateTimePy2Wx(val)
		return val

	def setInvalidDate(self):
		self.Value = wx.DefaultDateTime

	def GetValue(self):
		try:
			val = dateTimeWx2Py(super(dDatePicker, self).GetValue())
		except wx.PyAssertionError:
			val = None
		return self._getPyValue(val)

	def SetValue(self, val):
		val = self._getWxValue(val)
		try:
			super(dDatePicker, self).SetValue(val)
		except ValueError as e:
			nm = self.Name
			ue = ustr(e)
			dabo.log.error(_(u"Object '%(nm)s' has the following error: %(ue)s")
					% locals())

	def _getAllowNullDate(self):
		return self._hasWindowStyleFlag(wx.DP_ALLOWNONE)

	def _setAllowNullDate(self, val):
		if val:
			self._addWindowStyleFlag(wx.DP_ALLOWNONE)
		else:
			self._delWindowStyleFlag(wx.DP_ALLOWNONE)

	def _getForceShowCentury(self):
		return self._hasWindowStyleFlag(wx.DP_SHOWCENTURY)

	def _setForceShowCentury(self):
		if val:
			self._addWindowStyleFlag(wx.DP_SHOWCENTURY)
		else:
			self._delWindowStyleFlag(wx.DP_SHOWCENTURY)

	def _getInvalidBackColor(self):
		return self._invalidBackColor

	def _setInvalidBackColor(self, val):
		self._invalidBackColor = val

	def _getIsDateValid(self):
		return self.Value is not None

	def _getMaxValue(self):
		return self._getPyValue(dateTimeWx2Py(self.UpperLimit))

	def _setMaxValue(self, val):
		if self._constructed():
			val = self._getWxValue(val)
			self.SetRange(self.LowerLimit, val)
		else:
			self._properties["MinValue"] = val

	def _getMinValue(self):
		return self._getPyValue(dateTimeWx2Py(self.LowerLimit))

	def _setMinValue(self, val):
		if self._constructed():
			val = self._getWxValue(val)
			self.SetRange(val, self.UpperLimit)
		else:
			self._properties["MinValue"] = val

	def _getPickerMode(self):
		if self._hasWindowStyleFlag(wx.DP_DROPDOWN):
			mode = "Dropdown"
		else:
			mode = "Spin"
		return mode

	def _setPickerMode(self, val):
		mode = val[:1].lower()
		if mode in "ds":
			self._addWindowStyleFlag({"d": wx.DP_DROPDOWN, "s": wx.DP_SPIN}[mode])
		else:
			raise ValueError(_("The only allowed values are: 'Dropdown', 'Spin'."))

	def _getValueMode(self):
		return {"d": "Date", "t": "Timestamp"}[self._valueMode]

	def _setValueMode(self, val):
		val = val[:1].lower()
		if val in "dt":
			self._valueMode = val
		else:
			raise ValueError(_("The only allowed values are: 'Date', 'Timestamp'."))

	# Property definitions:
	AllowNullDate = property(_getAllowNullDate, _setAllowNullDate, None,
		_("""If True enable Null vale in date. (bool)(Default=False)"""))

	ForceShowCentury = property(_getForceShowCentury, _setForceShowCentury, None,
		_("""Regardless of locale setting, century is shown if True. (bool)
		(Default=False)"""))

	IsDateValid = property(_getIsDateValid, None, None,
		_("""Read-only property tells if Value holds valid date type value."""))

	InvalidBackColor = property(_getInvalidBackColor, _setInvalidBackColor, None,
		_("""Color value used for illegal values or values out-of-teh bounds. (str)
		(Default="Yellow")"""))

	MaxValue = property(_getMaxValue, _setMaxValue, None,
		_("""Holds upper value limit. (date, tuple, str)(Default=None)"""))

	MinValue = property(_getMinValue, _setMinValue, None,
		_("""Holds lower value limit. (date, tuple, str)(Default=None)"""))

	PickerMode = property(_getPickerMode, _setPickerMode, None,
		_("""Creates control with spin or dropdown calendar. (str)
		Available values are:
			- Spin
			- Dropdown (default)"""))

	ValueMode = property(_getValueMode, _setValueMode, None,
		_("""Enables handling Timestamp type. (str)(Default="Date")"""))

	DynamicMaxValue = makeDynamicProperty(MaxValue)
	DynamicMinValue = makeDynamicProperty(MinValue)


if __name__ == "__main__":
	import datetime
	import test

	class TestBase(dDatePicker):

		def onValueChanged(self, evt):
			print "onValueChanged"

	test.Test().runTest(TestBase, AllowNullDate=True, Value=datetime.date(1970,12,03))
	test.Test().runTest(TestBase, BackColor="orange", PickerMode="Spin", AllowNullDate=True)
