# -*- coding: utf-8 -*-
import datetime

import wx
import wx.adv as wxcal

from .. import events
from .. import ui
from ..localization import _
from . import dControlMixin
from . import makeDynamicProperty

# settings: firstDayOfWeek


class BaseCalendar(dControlMixin, wxcal.CalendarCtrl):
    """
    This is the base wrapper of the wx calendar control. Do not
    use this directly; instead, use either the 'dCalendar' or the
    'dExtendedCalendar' subclasses.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dCalendar
        preClass = wxcal.CalendarCtrl

        style = kwargs.get("style", 0)
        dow = self._firstDayOfWeek = self._extractKey(
            (kwargs, properties, attProperties), "FirstDayOfWeek", "Sunday"
        )
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

        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

        # Store some event types in case we need to raise them
        self._setCalEventTypes()
        # Bind the native events
        self.Bind(wxcal.EVT_CALENDAR, self.__onWxCalendar)
        self.Bind(wxcal.EVT_CALENDAR_SEL_CHANGED, self.__onWxDateChanged)
        self.Bind(wxcal.EVT_CALENDAR_DAY, self.__onWxDayChanged)
        self.Bind(wxcal.EVT_CALENDAR_MONTH, self.__onWxMonthChanged)
        self.Bind(wxcal.EVT_CALENDAR_YEAR, self.__onWxYearChanged)
        self.Bind(wxcal.EVT_CALENDAR_WEEKDAY_CLICKED, self.__onWxDayHeaderClicked)
        self.bindEvent(events.CalendarDateChanged, self.__onDateChanged)
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
                newMn += 12
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
        self.raiseEvent(events.Hit, evt)

    def __onWxDateChanged(self, evt):
        evt.Skip()
        self.raiseEvent(events.CalendarDateChanged, evt)

    def __onWxDayChanged(self, evt):
        evt.Skip()
        self.raiseEvent(events.CalendarDayChanged, evt)

    def __onWxMonthChanged(self, evt):
        evt.Skip()
        self.raiseEvent(events.CalendarMonthChanged, evt)

    def __onWxYearChanged(self, evt):
        evt.Skip()
        self.raiseEvent(events.CalendarYearChanged, evt)

    def __onWxDayHeaderClicked(self, evt):
        evt.Skip()
        self.raiseEvent(events.CalendarDayHeaderClicked, evt)

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
    @property
    def Date(self):
        """The current Date of the calendar  (datetime.date)"""
        return self.GetDate()

    @Date.setter
    def Date(self, val):
        # curr = self.PyGetDate()
        curr = self.GetDate()
        if isinstance(val, tuple):
            val = datetime.date(*val)
        self.SetDate(val)
        # Raise the events, since the control doesn't raise native
        # events when changing the date programatically.
        evtClass = wxcal.CalendarEvent
        chg = False
        if curr.year != val.year:
            # evt = evtClass(self, self._evtCalYearType)
            # self.raiseEvent(events.CalendarYearChanged, evt)
            self.raiseEvent(events.CalendarYearChanged)
            chg = True
        if curr.month != val.month:
            # evt = evtClass(self, self._evtCalMonthType)
            # self.raiseEvent(events.CalendarMonthChanged, evt)
            self.raiseEvent(events.CalendarMonthChanged)
            chg = True
        if curr.day != val.day:
            # evt = evtClass(self, self._evtCalDayType)
            # self.raiseEvent(events.CalendarDayChanged, evt)
            self.raiseEvent(events.CalendarDayChanged)
            chg = True
        if chg:
            # evt = evtClass(self, self._evtCalSelType)
            # self.raiseEvent(events.CalendarDateChanged, evt)
            self.raiseEvent(events.CalendarDateChanged)
        self.Refresh()

    @property
    def FirstDayOfWeek(self):
        """
        Can be one of either 'Sunday' or 'Monday'. Determines which day of the week appears in the
        first column. Defaults to the value set in settings.firstDayOfWeek. Read-only at runtime.
        (str)
        """
        return self._firstDayOfWeek

    @property
    def FixedMonth(self):
        return self._fixedMonth

    @FixedMonth.setter
    def FixedMonth(self, val):
        """When True, the user cannot change the displayed month. Default=False  (bool)"""
        self._fixedMonth = val
        if val:
            # Fixing the month fixes the year, too
            self._fixedYear = True
        self.EnableMonthChange(not val)

    @property
    def FixedYear(self):
        return self._fixedYear

    @FixedYear.setter
    def FixedYear(self, val):
        """When True, the user cannot change the displayed year. Default=False  (bool)"""
        self._fixedYear = val
        if not val:
            # Enabling the year will also enable the month
            self._fixedMonth = False
        self.EnableYearChange(not val)

    @property
    def HeaderBackColor(self):
        """Background color of the calendar header  (str or tuple)"""
        return self.GetHeaderColourBg().Get()

    @HeaderBackColor.setter
    def HeaderBackColor(self, val):
        # Need to set both
        color = self.getWxColour(val)
        self.SetHeaderColours(self.GetHeaderColourFg(), color)
        self.refresh()

    @property
    def HeaderForeColor(self):
        """Forecolor of the calendar header  (str or tuple)"""
        return self.GetHeaderColourFg().Get()

    @HeaderForeColor.setter
    def HeaderForeColor(self, val):
        # Need to set both
        color = self.getWxColour(val)
        self.SetHeaderColours(color, self.GetHeaderColourBg())
        self.refresh()

    @property
    def HighlightBackColor(self):
        """Background color of the calendar highlight  (str or tuple)"""
        return self.GetHighlightColourBg().Get()

    @HighlightBackColor.setter
    def HighlightBackColor(self, val):
        # Need to set both
        color = self.getWxColour(val)
        self.SetHighlightColours(self.GetHighlightColourFg(), color)
        self.refresh()

    @property
    def HighlightForeColor(self):
        """Forecolor of the calendar highlight  (str or tuple)"""
        return self.GetHighlightColourFg().Get()

    @HighlightForeColor.setter
    def HighlightForeColor(self, val):
        # Need to set both
        color = self.getWxColour(val)
        self.SetHighlightColours(color, self.GetHighlightColourBg())
        self.refresh()

    @property
    def HolidayBackColor(self):
        """Background color of the calendar holiday  (str or tuple)"""
        return self.GetHolidayColourBg().Get()

    @HolidayBackColor.setter
    def HolidayBackColor(self, val):
        # Need to set both
        color = self.getWxColour(val)
        self.SetHolidayColours(self.GetHolidayColourFg(), color)
        self.refresh()

    @property
    def HolidayForeColor(self):
        """Forecolor of the calendar holiday  (str or tuple)"""
        return self.GetHolidayColourFg().Get()

    @HolidayForeColor.setter
    def HolidayForeColor(self, val):
        # Need to set both
        color = self.getWxColour(val)
        self.SetHolidayColours(color, self.GetHolidayColourBg())
        self.refresh()

    @property
    def HighlightHolidays(self):
        """Determines whether holidays are displayed as highlighted. Default=False.  (bool)"""
        return self._highlightHolidays

    @HighlightHolidays.setter
    def HighlightHolidays(self, val):
        self._highlightHolidays = val
        self.EnableHolidayDisplay(val)

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
        super().__init__(*args, **kwargs)


class dExtendedCalendar(BaseCalendar):
    """
    This formats the calendar into an extended layout, with a
    dropdown list for selecting any month, and a spinner for
    moving from year to year. Use this when you need to be able
    to navigate to any date quickly.
    """

    def __init__(self, *args, **kwargs):
        style = kwargs.get("style", 0)
        kwargs["style"] = style & ~wxcal.CAL_SEQUENTIAL_MONTH_SELECTION
        super().__init__(*args, **kwargs)


ui.BaseCalendar = BaseCalendar
ui.dCalendar = dCalendar
ui.dExtendedCalendar = dExtendedCalendar


if __name__ == "__main__":
    from ..application import dApp
    from . import dForm

    class TestForm(dForm):
        def afterInit(self):
            dCalendar(self, FirstDayOfWeek="monday", Position=(0, 0), RegID="cal")
            self.cal.HighlightHolidays = True
            self.cal.setHolidays(((None, 12, 25), (2006, 1, 4)))

        def onCalendarDayHeaderClicked_cal(self, evt):
            print("Day of week:", evt.weekday)

        def onCalendarDateChanged_cal(self, evt):
            print("DateChanged!", evt.date)

        def onCalendarDayChanged_cal(self, evt):
            print("DayChanged!", evt.date)

        def onCalendarMonthChanged_cal(self, evt):
            print("MonthChanged!", evt.date)

        def onCalendarYearChanged_cal(self, evt):
            print("YearChanged!", evt.date)

        def onHit_cal(self, evt):
            print("Hit!", evt.date)
            self.release()

    app = dApp()
    app.MainFormClass = TestForm
    app.start()
