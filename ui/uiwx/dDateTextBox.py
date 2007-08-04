# -*- coding: utf-8 -*-
import re
import locale
import datetime
import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dTextBox import dTextBox
from dPanel import dPanel
from dButton import dButton
from dabo.ui import makeDynamicProperty


class CalPanel(dPanel):
	def __init__(self, parent, pos=None, dt=None, ctrl=None ):
		if dt is None:
			self.date = datetime.date.today()
		else:
			self.date = dt
		self.ctrl = ctrl
		super(CalPanel, self).__init__(parent, pos=pos)
		
	
	def afterInit(self):
		""" Create the calendar control, and resize this panel 
		to the calendar's size.
		"""
		self.cal = dabo.ui.dCalendar(self, Position=(5, 5))
		self.cal.Date = self.date
		self.cal.bindEvent(dEvents.Hit, self.onCalSelection)
		self.cal.bindEvent(dEvents.KeyChar, self.onCalKey)
		wd, ht = self.cal.Size
		self.Size = (wd+10, ht+10)
		self.BackColor = (192, 192, 0)
		self.cal.Visible = True
		
		
	def onCalSelection(self, evt):
		if self.ctrl is not None:
			self.ctrl.setDate(self.cal.Date)
			self.ctrl.setFocus()
		self.Visible = False
	
	
	def onCalKey(self, evt):
		if evt.keyCode == wx.WXK_ESCAPE:
			evt.Continue = False
			if self.ctrl is not None:
				self.ctrl.setFocus()
			self.Visible = False
		
		

class dDateTextBox(dTextBox):
	""" This is a specialized textbox class designed to work with date values.
	It provides handy shortcut keystrokes so that users can quickly navigate
	to the date value they need. The keystrokes are the same as those used
	by Quicken, the popular personal finance program.
	"""
	def beforeInit(self):
		# Pattern for recognizing dates from databases
		self.dbDTPat = re.compile("(\d{4})[-/\.](\d{1,2})[-/\.](\d{1,2}) (\d{1,2}):(\d{1,2}):([\d\.]+)")
		self.dbDPat = re.compile("(\d{4})[-/\.](\d{1,2})[-/\.](\d{1,2})")
		self.dbYearLastDTPat = re.compile("(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4}) (\d{1,2}):(\d{1,2}):([\d\.]+)")
		self.dbYearLastDPat = re.compile("(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{4})")

		# Two-digit year value that is the cutoff in interpreting 
		# dates as being either 19xx or 20xx.
		self.rollover = 50
		# Optional behavior: if a key is pressed for moving to the first
		# or last of a period and the date is already at that boundary, do
		# we continue to the next period? E.g.: if the current date is 
		# March 31 and the user presses 'H'. We are already at the end of 
		# the month, so do we interpret this to mean continue to the end
		# of the following month, or do we do nothing?
		self.continueAtBoundary = True
		# Do we display a button on the right side for activating the calendar?
		### TODO: still needs a lot of work to display properly.
		self.showCalButton = False
		# Do we display datetimes in 24-hour clock, or with AM/PM?
		self.ampm = False
	
	
	def afterInit(self):
		self._baseClass = dDateTextBox
		self.Value = datetime.date.today()
		if self.showCalButton:
			# Create a button that will display the calendar
			self.calButton = dButton(self.Parent, Size=(self.Height, self.Height),
					Right=self.Right, Caption="V")
			self.calButton.Visible = True
			self.calButton.bindEvent(dEvents.Hit, self.onDblClick)
			
		# Tooltip help
		self.ToolTipText = """Available Keys:
=============
T : Today
+ : Up One Day
- : Down One Day
[ : Up One Month
] : Down One Month
M : First Day of Month
H : Last Day of montH
Y : First Day of Year
R : Last Day of yeaR
C: Popup Calendar to Select
"""
	
	def initEvents(self):
		super(dDateTextBox, self).initEvents()
		self.bindEvent(dEvents.KeyChar, self.__onChar)
		self.bindEvent(dEvents.LostFocus, self.__onLostFocus)
		self.bindEvent(dEvents.MouseLeftDoubleClick, self.__onDblClick)
	
		
	def __onDblClick(self, evt):
		""" Display a calendar to allow users to select dates."""
		self.showCalendar()
		
		
	def showCalendar(self):
		availHt = self.Parent.Bottom - self.Bottom
		try:
			self.calPanel.cal.Date = self.Value
		except:
			self.calPanel = CalPanel(self.Parent, dt=self.Value, ctrl=self)
		cp = self.calPanel
		cp.Position = (self.Left, self.Bottom)
		if self.Bottom + cp.Height > self.Parent.Bottom:
			# Maybe we should move it above
			if cp.Height <= self.Top:
				cp.Bottom = self.Top
			else:
				# We can't fit it cleanly, so try to fit as much as possible
				cp.Top = max(0, (self.Parent.Height - cp.Height) )
		if self.Left + cp.Width > self.Parent.Right:
			# Try moving it to the left
			cp.Left = max(0, (self.Parent.Width - cp.Width) )
		cp.Visible = True
		cp.bringToFront()
		cp.setFocus()
		
	
	def __onChar(self, evt):
		""" If a shortcut key was pressed, process that. Otherwise, eat 
		inappropriate characters.
		"""
		try:
			key = evt.keyChar.lower()
			ctrl = evt.controlDown
			shift = evt.shiftDown
			
			if ctrl:
				if shift and self.Application.Platform == "GTK":
					# Linux reads keys differently depending on the Shift key
					key = {72: "h", 77: "m", 83: "s"}[evt.keyCode]
				else:
					key = {8: "h", 13: "m", 19: "s"}[evt.keyCode]
		except:
			# spurious key event; ignore
			return
		
		shortcutKeys = "t+-mhsyrc[]"
		dateEntryKeys = "0123456789/- :."
		if self.ampm:
			dateEntryKeys + "apm"
		
		if key in shortcutKeys:
			# There is a conflict if the key, such as '-', is used in both the 
			# date formatting and as a shortcut. So let's check the text
			# of this field to see if it is a full date or if the user is typing in
			# a value.
			adjust = True
			val = self.GetValue()
			
			if val:
				valDt = self.strToDate(val, testing=True)
				if valDt is None:
					adjust = False
				else:
					# They've just finished typing a new date, or are just
					# positioned on the field. Either way, update the stored 
					# date to make sure they are in sync.
					self.Value = valDt
					evt.Continue = False
				if adjust:
					self.adjustDate(key, ctrl, shift)
	
		elif key in dateEntryKeys:
			# key can be used for date entry: allow
			pass
		elif evt.keyCode in range(32, 129):
			# key is in ascii range, but isn't one of the above
			# allowed key sets. Disallow.
			evt.stop()
		else:
			# Pass the key up the chain to process - perhaps a Tab, Enter, or Backspace...
			pass

	
	def __onLostFocus(self, evt):
		val = self.Value
		try:
			newVal = self.strToDate(self.GetValue())
			if newVal != val:
				self.Value = newVal
		except: pass
		

	def adjustDate(self, key, ctrl=False, shift=False):
		""" Modifies the current date value if the key is one of the 
		shortcut keys.
		"""
		# Save the original value for comparison
		orig = self.Value.toordinal()
		# Default direction
		forward = True
		# Flag to indicate errors in date processing
		self.dateOK = True
		# Flag to indicate if we consider boundary conditions
		checkBoundary = True
		# Are we working with dates or datetimes
		isDateTime = isinstance(self.Value, datetime.datetime)
		# Did the key move to a boundary?
		toBoundary = False
		
		if key == "t":
			# Today
			if isDateTime:
				self.Value = datetime.datetime.now()
			else:
				self.Value = datetime.date.today()
		elif key == "+":
			# Forward 1 day
			self.dayInterval(1)
		elif key == "-":
			# Back 1 day
			self.dayInterval(-1)
			forward = False
		elif key == "m":
			if ctrl:
				if isDateTime:
					# Changing the minute value
					amt = 1
					if shift:
						amt = -1
						forward = False
					self.minuteInterval(amt)
				else:
					return
			else:
				# First day of month
				self.Value = self.Value.replace(day=1)
				forward = False
				toBoundary = True
		elif key == "h":
			if ctrl:
				if isDateTime:
					# Changing the hour value
					amt = 1
					if shift:
						amt = -1
						forward = False
					self.hourInterval(amt)
				else:
					return
			else:
				# Last day of month
				self.setToLastMonthDay()
				toBoundary = True
		elif key == "s":
			if ctrl:
				if isDateTime:
					# Changing the second value
					amt = 1
					if shift:
						amt = -1
						forward = False
					self.secondInterval(amt)
			else:
				return
		elif key == "y":
			# First day of year
			self.Value = self.Value.replace(month=1, day=1)
			forward = False
			toBoundary = True
		elif key == "r":
			# Last day of year
			self.Value = self.Value.replace(month=12, day=31)
			toBoundary = True
		elif key == "[":
			# Back one month
			self.monthInterval(-1)
			forward = False
		elif key == "]":
			# Forward one month
			self.monthInterval(1)
		elif key == "c":
			# Show the calendar
			self.showCalendar()
			checkBoundary = False
		else:
			# This shouldn't happen, because onChar would have filtered it out.
			dabo.infoLog.write("Warning in dDateTextBox.adjustDate: %s key sent." % key)
			return
		
		if not self.dateOK:
			return
		if toBoundary and checkBoundary and self.continueAtBoundary:
			if self.Value.toordinal() == orig:
				# Date hasn't changed; means we're at the boundary
				# (first or last of the chosen interval). Move 1 day in
				# the specified direction, then re-apply the key
				if forward:
					self.dayInterval(1)
				else:
					self.dayInterval(-1)
				self.adjustDate(key)
	
	
	def hourInterval(self, hours):
		"""Adjusts the date by the given number of hours; negative
		values move backwards.
		"""
		self.Value += datetime.timedelta(hours=hours)

	
	def minuteInterval(self, minutes):
		"""Adjusts the date by the given number of minutes; negative
		values move backwards.
		"""
		self.Value += datetime.timedelta(minutes=minutes)

	
	def secondInterval(self, seconds):
		"""Adjusts the date by the given number of seconds; negative
		values move backwards.
		"""
		self.Value += datetime.timedelta(seconds=seconds)

	
	def dayInterval(self, days):
		"""Adjusts the date by the given number of days; negative
		values move backwards.
		"""
		self.Value += datetime.timedelta(days)

	
	def monthInterval(self, months):
		"""Adjusts the date by the given number of months; negative 
		values move backwards.
		"""
		mn = self.Value.month + months
		yr = self.Value.year
		dy = self.Value.day
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
				self.Value = self.Value.replace(year=yr, month=mn, day=dy)
				ok = True
			except:
				dy -= 1
	
	
	def setToLastMonthDay(self):
		mn = self.Value.month
		td = datetime.timedelta(1)
		while mn == self.Value.month:
			self.Value += td
		# We're now at the first of the next month. Go back one.
		self.Value -= td
		

	def getDateTuple(self):
		dt = self.Value
		return (dt.year, dt.month, dt.day )


	def setDate(self, dt):
		"""Sets the Value to the passed date if this is holding a date value, or
		sets the date portion of the Value if it is a datetime.
		"""
		val = self.Value
		if isinstance(val, datetime.datetime):
			self.Value = val.replace(year=dt.year, month=dt.month, day=dt.day)
		elif isinstance(val, basestring):
			self.Value = self.strToDate(dt)
		else:
			self.Value = dt

			
	def strToDate(self, val, testing=False):
		""" This routine parses the text representing a date, using the 
		current format. It adjusts for years given with two digits, using 
		the rollover value to determine the century. It then returns a
		datetime.date object set to the entered date.
		"""
		val = str(val)
		ret = None
		isDateTime = False
		# See if it matches any standard pattern. Values retrieved
		# from databases will always be in their own format
		if self.dbDTPat.match(val):
			# DateTime pattern
			isDateTime = True
			year, month, day, hr, mn, sec = self.dbDTPat.match(val).groups()
			# Convert to numeric
			year = int(year)
			month = int(month)
			day = int(day)
			hr = int(hr)
			mn = int(mn)
			sec = int(round(float(sec), 0) )
		elif self.dbDPat.match(val):
			# Date-only pattern
			year, month, day = self.dbDPat.match(val).groups()
			hr = mn = sec = 0
			# Convert to numeric
			year = int(year)
			month = int(month)
			day = int(day)
		elif self.dbYearLastDTPat.match(val):
			# DateTime pattern, YearLast format
			isDateTime = True
			month, day, year, hr, mn, sec = self.dbYearLastDTPat.match(val).groups()
			# Convert to numeric
			year = int(year)
			month = int(month)
			day = int(day)
			hr = int(hr)
			mn = int(mn)
			sec = int(round(float(sec), 0) )
		elif self.dbYearLastDPat.match(val):
			# Date-only pattern, YearLast format
			month, day, year = self.dbYearLastDPat.match(val).groups()
			hr = mn = sec = 0
			# Convert to numeric
			year = int(year)
			month = int(month)
			day = int(day)
		else:
			# See if there is a time component
			try:
				(dt, tm) = val.split()
				(hr, mn, sec) = tm.split(":")
				hr = int(hr)
				mn = int(mn)
				sec = int(round(float(sec), 0) )
				isDateTime = True
			except:
				dt = val
				(hr, mn, sec) = (0, 0, 0)

			try:
				sep = [c for c in dt if not c.isdigit()][0]
				dtPieces = [int(p) for p in dt.split(sep)]
			except:
				# There is no separator
				sep = ""
				dtPieces = []
				
		if isDateTime:
			try:
				ret = datetime.datetime(year, month, day, hr, mn, sec)
			except:
				if not testing:
					# Don't fill up the logs with error messages from tests that 
					# are expected to fail.
					dabo.errorLog.write(_("Invalid datetime specified: %s") % val )
				ret = None
		else:
			try:
				ret = datetime.date(year, month, day)
			except:
				if not testing:
					# Don't fill up the logs with error messages from tests that 
					# are expected to fail.
					dabo.errorLog.write(_("Invalid date specified: %s") % val )
				ret = None
		return ret
	
	

if __name__ == "__main__":
	import test
	test.Test().runTest(dDateTextBox)
