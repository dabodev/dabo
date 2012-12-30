# -*- coding: utf-8 -*-
import wx
import wx.calendar as wxcal
import datetime
import dabo
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class BaseCalendar(dcm.dControlMixin, wxcal.CalendarCtrl):
	"""
	This is the base wrapper of the wx calendar control. Do not
	use this directly; instead, use either the 'dCalendar' or the
	'dExtendedCalendar' subclasses.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dCalendar
		preClass = wxcal.PreCalendarCtrl

		style = kwargs.get("style", 0)
		dow = self._firstDayOfWeek = self._extractKey((kwargs, properties, attProperties),
				"FirstDayOfWeek", "Sunday")
		if dow.lower().strip()[0] == "m":
			style = style | wxcal.CAL_MONDAY_FIRST
		else:
			style = style | wxcal.CAL_SUNDAY_FIRST
		kwargs["style"] = style
		# Initialize the other props
		self._fixedMonth = False
		self._fixedYear = False
		self._highlightHolidays = False
		self._holidays = []
		# We need to check if thes have changed when the days change.
		# If so, udpate the holidays.
		self._currentMonth = None
		self._currentYear = None

		dcm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)

		# Store some event types in case we need to raise them
		self._setCalEventTypes()
		# Bind the native events
		self.Bind(wxcal.EVT_CALENDAR, self.__onWxCalendar)
		self.Bind(wxcal.EVT_CALENDAR_SEL_CHANGED, self.__onWxDateChanged)
		self.Bind(wxcal.EVT_CALENDAR_DAY, self.__onWxDayChanged)
		self.Bind(wxcal.EVT_CALENDAR_MONTH, self.__onWxMonthChanged)
		self.Bind(wxcal.EVT_CALENDAR_YEAR, self.__onWxYearChanged)
		self.Bind(wxcal.EVT_CALENDAR_WEEKDAY_CLICKED, self.__onWxDayHeaderClicked)
		self.bindEvent(dEvents.CalendarDateChanged, self.__onDateChanged)
		# Get the events flowing!
		self.Date = self.Date


	def setHoliday(self, val):
		"""
		Adds the specified date to the list of holidays. This should be
		a tuple in the format (Y, M, D). If this is a holiday that is to apply
		to every year, pass the year as None (e.g.: (None, 12, 25)
		"""
		if val not in self._holidays:
			self._holidays.append(val)


	def setHolidays(self, dtList):
		for dt in dtList:
			self.setHoliday(dt)


	def __onDateChanged(self, evt):
		if not self.HighlightHolidays:
			return
		mn = evt.date.month
		yr = evt.date.year
		if (mn != self._currentMonth) or (yr != self._currentYear):
			self._currentMonth = mn
			self._currentYear = yr
			# Update the holidays
			self._updateHolidays()


	def _updateHolidays(self):
		mn, yr = self._currentMonth, self._currentYear
		hdays = [d for d in self._holidays if d[1] == mn]
		for hday in hdays:
			hyr = hday[0]
			if hyr is None or hyr == self._currentYear:
				self.SetHoliday(hday[2])


	def nextDay(self):
		self.goDays(1)


	def priorDay(self):
		self.goDays(-1)


	def goDays(self, val):
		self.Value += datetime.timedelta(val)


	def goMonths(self, val):
		# This can overflow, so we need to trap
		dt = self.Date
		mn = dt.month
		newMn = mn + val
		try:
			newDt = dt.replace(month=newMn)
		except ValueError:
			newYr = dt.year
			newDay = dt.day
			while newMn < 1:
				newYr -= 1
				newMn +=12
			while newMn > 12:
				newYr += 1
				newMn -= 12
			try:
				newDt = dt.replace(year=newYr, month=newMn, day=newDay)
			except ValueError:
				# The day is now illegal (e.g., Feb. 30).
				badDt = True
				while badDt:
					newDay -= 1
					try:
						newDt = dt.replace(year=newYr, month=newMn, day=newDay)
						badDt = False
					except ValueError:
						pass
		self.Date = newDt


	def __onWxCalendar(self, evt):
		evt.Skip()
		self.raiseEvent(dEvents.Hit, evt)


	def __onWxDateChanged(self, evt):
		evt.Skip()
		self.raiseEvent(dEvents.CalendarDateChanged, evt)


	def __onWxDayChanged(self, evt):
		evt.Skip()
		self.raiseEvent(dEvents.CalendarDayChanged, evt)


	def __onWxMonthChanged(self, evt):
		evt.Skip()
		self.raiseEvent(dEvents.CalendarMonthChanged, evt)


	def __onWxYearChanged(self, evt):
		evt.Skip()
		self.raiseEvent(dEvents.CalendarYearChanged, evt)


	def __onWxDayHeaderClicked(self, evt):
		evt.Skip()
		self.raiseEvent(dEvents.CalendarDayHeaderClicked, evt)


	def _setCalEventTypes(self):
		"""
		When we raise events, we need to include a native wx
		event type. Rather than compute them repeatedly, do it
		once here.
		"""
		self._evtCalType = wxcal.EVT_CALENDAR.evtType[0]
		self._evtCalSelType = wxcal.EVT_CALENDAR_SEL_CHANGED.evtType[0]
		self._evtCalDayType = wxcal.EVT_CALENDAR_DAY.evtType[0]
		self._evtCalMonthType = wxcal.EVT_CALENDAR_MONTH.evtType[0]
		self._evtCalYearType = wxcal.EVT_CALENDAR_YEAR.evtType[0]


	### Begin property defs  ###
	def _getDate(self):
		return self.PyGetDate()

	def _setDate(self, val):
		curr = self.PyGetDate()
		if isinstance(val, tuple):
			val = datetime.date(*val)
		self.PySetDate(val)
		# Raise the events, since the control doesn't raise native
		# events when changing the date programatically.
		evtClass = wxcal.CalendarEvent
		chg = False
		if curr.year != val.year:
			evt = evtClass(self, self._evtCalYearType)
			self.raiseEvent(dEvents.CalendarYearChanged, evt)
			chg = True
		if curr.month != val.month:
			evt = evtClass(self, self._evtCalMonthType)
			self.raiseEvent(dEvents.CalendarMonthChanged, evt)
			chg = True
		if curr.day != val.day:
			evt = evtClass(self, self._evtCalDayType)
			self.raiseEvent(dEvents.CalendarDayChanged, evt)
			chg = True
		if chg:
			evt = evtClass(self, self._evtCalSelType)
			self.raiseEvent(dEvents.CalendarDateChanged, evt)
		self.Refresh()


	def _getFirstDayOfWeek(self):
		return self._firstDayOfWeek


	def _getFixedMonth(self):
		return self._fixedMonth

	def _setFixedMonth(self, val):
		self._fixedMonth = val
		if val:
			# Fixing the month fixes the year, too
			self._fixedYear = True
		self.EnableMonthChange(not val)


	def _getFixedYear(self):
		return self._fixedYear

	def _setFixedYear(self, val):
		self._fixedYear = val
		if not val:
			# Enabling the year will also enable the month
			self._fixedMonth = False
		self.EnableYearChange(not val)


	def _getHeaderBackColor(self):
		return self.GetHeaderColourBg().Get()

	def _setHeaderBackColor(self, val):
		# Need to set both
		color = self._getWxColour(val)
		self.SetHeaderColours(self.GetHeaderColourFg(), color)
		self.refresh()


	def _getHeaderForeColor(self):
		return self.GetHeaderColourFg().Get()

	def _setHeaderForeColor(self, val):
		# Need to set both
		color = self._getWxColour(val)
		self.SetHeaderColours(color, self.GetHeaderColourBg())
		self.refresh()


	def _getHighlightBackColor(self):
		return self.GetHighlightColourBg().Get()

	def _setHighlightBackColor(self, val):
		# Need to set both
		color = self._getWxColour(val)
		self.SetHighlightColours(self.GetHighlightColourFg(), color)
		self.refresh()


	def _getHighlightForeColor(self):
		return self.GetHighlightColourFg().Get()

	def _setHighlightForeColor(self, val):
		# Need to set both
		color = self._getWxColour(val)
		self.SetHighlightColours(color, self.GetHighlightColourBg())
		self.refresh()


	def _getHolidayBackColor(self):
		return self.GetHolidayColourBg().Get()

	def _setHolidayBackColor(self, val):
		# Need to set both
		color = self._getWxColour(val)
		self.SetHolidayColours(self.GetHolidayColourFg(), color)
		self.refresh()


	def _getHolidayForeColor(self):
		return self.GetHolidayColourFg().Get()

	def _setHolidayForeColor(self, val):
		# Need to set both
		color = self._getWxColour(val)
		self.SetHolidayColours(color, self.GetHolidayColourBg())
		self.refresh()


	def _getHighlightHolidays(self):
		return self._highlightHolidays

	def _setHighlightHolidays(self, val):
		self._highlightHolidays = val
		self.EnableHolidayDisplay(val)


	Date = property(_getDate, _setDate, None,
			_("The current Date of the calendar  (datetime.date)"))

	FirstDayOfWeek = property(_getFirstDayOfWeek, None, None,
			_("""Can be one of either 'Sunday' or 'Monday'. Determines which day
			of the week appears in the first column. Defaults to the value set
			in dabo.firstDayOfWeek. Read-only at runtime.  (str)"""))

	FixedMonth = property(_getFixedMonth, _setFixedMonth, None,
			_("""When True, the user cannot change the displayed month.
			Default=False  (bool)"""))

	FixedYear = property(_getFixedYear, _setFixedYear, None,
			_("""When True, the user cannot change the displayed month.
			Default=False  (bool)"""))

	HeaderBackColor = property(_getHeaderBackColor, _setHeaderBackColor, None,
			_("Background color of the calendar header  (str or tuple)"))

	HeaderForeColor = property(_getHeaderForeColor, _setHeaderForeColor, None,
			_("Forecolor of the calendar header  (str or tuple)"))

	HighlightBackColor = property(_getHighlightBackColor, _setHighlightBackColor, None,
			_("Background color of the calendar highlight  (str or tuple)"))

	HighlightForeColor = property(_getHighlightForeColor, _setHighlightForeColor, None,
			_("Forecolor of the calendar highlight  (str or tuple)"))

	HolidayBackColor = property(_getHolidayBackColor, _setHolidayBackColor, None,
			_("Background color of the calendar holiday  (str or tuple)"))

	HolidayForeColor = property(_getHolidayForeColor, _setHolidayForeColor, None,
			_("Forecolor of the calendar holiday  (str or tuple)"))

	HighlightHolidays = property(_getHighlightHolidays, _setHighlightHolidays, None,
			_("""Determines whether holidays are displayed as highlighted.
			Default=False.  (bool)"""))

	Value = Date


	DynamicDate = makeDynamicProperty(Date)
	DynamicFirstDayOfWeek = makeDynamicProperty(FirstDayOfWeek)
	DynamicFixedMonth = makeDynamicProperty(FixedMonth)
	DynamicFixedYear = makeDynamicProperty(FixedYear)
	DynamicHeaderBackColor = makeDynamicProperty(HeaderBackColor)
	DynamicHeaderForeColor = makeDynamicProperty(HeaderForeColor)
	DynamicHighlightBackColor = makeDynamicProperty(HighlightBackColor)
	DynamicHighlightForeColor = makeDynamicProperty(HighlightForeColor)
	DynamicHolidayBackColor = makeDynamicProperty(HolidayBackColor)
	DynamicHolidayForeColor = makeDynamicProperty(HolidayForeColor)
	DynamicHighlightHolidays = makeDynamicProperty(HighlightHolidays)
	DynamicValue = makeDynamicProperty(Value)



class dCalendar(BaseCalendar):
	"""
	This formats the calendar into a more compact layout, with
	arrow buttons for moving back and forth a month at a time.
	"""
	def __init__(self, *args, **kwargs):
		style = kwargs.get("style", 0)
		kwargs["style"] = style | wxcal.CAL_SEQUENTIAL_MONTH_SELECTION
		super(dCalendar, self).__init__(*args, **kwargs)



class dExtendedCalendar(BaseCalendar):
	"""
	This formats the calendar into an extended layout, with a
	dropdown list for selecting any month, and a spinner for
	moving from year to year. Use this when you need to be able
	to navigate to any date quickly.
	"""
	def __init__(self, *args, **kwargs):
		style = kwargs.get("style", 0)
		kwargs["style"] = style &  ~wxcal.CAL_SEQUENTIAL_MONTH_SELECTION
		super(dExtendedCalendar, self).__init__(*args, **kwargs)



if __name__ == "__main__":
	from dabo.dApp import dApp
	class TestForm(dabo.ui.dForm):
		def afterInit(self):
			dCalendar(self, FirstDayOfWeek="monday",
					Position=(0,0), RegID="cal")
			self.cal.HighlightHolidays = True
			self.cal.setHolidays(((None,12,25), (2006, 1, 4)))

		def onCalendarDayHeaderClicked_cal(self, evt):
			print "Day of week:", evt.weekday
		def onCalendarDateChanged_cal(self, evt):
			print "DateChanged!", evt.date
		def onCalendarDayChanged_cal(self, evt):
			print "DayChanged!", evt.date
		def onCalendarMonthChanged_cal(self, evt):
			print "MonthChanged!", evt.date
		def onCalendarYearChanged_cal(self, evt):
			print "YearChanged!", evt.date
		def onHit_cal(self, evt):
			print "Hit!", evt.date
			self.release()


	app = dApp()
	app.MainFormClass = TestForm
	app.start()



