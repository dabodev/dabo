import re
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
		wd, ht = self.cal.Size
		self.Size = (wd+10, ht+10)
		self.BackColor = (192, 192, 0)
		self.cal.Visible = True
		
	def onCalSelection(self, evt):
		if self.ctrl is not None:
			self.ctrl.setDate(self.cal.Date)
			self.ctrl.setFocus()
		self.Visible = False
		
		

class dDateTextBox(dTextBox):
	""" This is a specialized textbox class designed to work with date values.
	It provides handy shortcut keystrokes so that users can quickly navigate
	to the date value they need. The keystrokes are the same as those used
	by Quicken, the popular personal finance program.
	"""
	def beforeInit(self):
		self.date = datetime.date.today()
		self.formats = {
				"American": {"prompt": "American (MM/DD/YYYY)", 
					"setting" : "American", 
					"format" : "%m/%d/%Y"},
				"YMD": {"prompt": "YMD (YYYY-MM-DD)", 
					"setting": "YMD", 
					"format" : "%Y-%m-%d"},
				"European": {"prompt": "European (DD.MM.YYYY)", 
					"setting": "european", 
					"format" : "%d.%m.%Y"} }
		self.dateTimeFormats = {
				"American": {"prompt": "American (MM/DD/YYYY)", 
					"setting" : "American", 
					"format" : "%m/%d/%Y %H:%M:%S"},
				"YMD": {"prompt": "YMD (YYYY-MM-DD)", 
					"setting": "YMD", 
					"format" : "%Y-%m-%d %H:%M:%S"},
				"European": {"prompt": "European (DD.MM.YYYY)", 
					"setting": "european", 
					"format" : "%d.%m.%Y %H:%M:%S"} }
		# Default format; can be changed in settings_override.py
		# or by using the RightClick menu.
		self.dateFormat = dabo.settings.dateFormat
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
		self.bindEvent(dEvents.MouseRightDown, self.__onRightDown)
		self.bindEvent(dEvents.KeyChar, self.__onChar)
		self.bindEvent(dEvents.MouseLeftDoubleClick, self.__onDblClick)
		self.bindEvent(dEvents.LostFocus, self.__onLostFocus)
	
		
	def __onLostFocus(self, evt):
		""" Since the actual value is the date object, we need to refresh
		the displayed text with the properly formatted character date.
		"""
		# Refresh the displayed value
		self.Value = self.GetValue()
	
	
	def __onDblClick(self, evt):
		""" Display a calendar to allow users to select dates."""
		self.showCalendar()
		
		
	def showCalendar(self):
		availHt = self.Parent.Bottom - self.Bottom
		try:
			self.calPanel.cal.Date = self.strToDate(self.Value)
		except:
			self.calPanel = CalPanel(self.Parent, dt=self.strToDate(self.Value), 
					ctrl=self)
		self.calPanel.Position = (self.Left, self.Bottom)
		if self.Bottom + self.calPanel.Height > self.Parent.Bottom:
			# Maybe we should move it above
			if self.calPanel.Height <= self.Top:
				self.calPanel.Bottom = self.Top
			else:
				# We can't fit it cleanly, so try to fit as much as possible
				self.calPanel.Top = max(0, (self.Parent.Height - self.calPanel.Height) )
		if self.Left + self.calPanel.Width > self.Parent.Right:
			# Try moving it to the left
			self.calPanel.Left = max(0, (self.Parent.Width - self.calPanel.Width) )
		self.calPanel.Visible = True
		self.calPanel.setFocus()
		
	
	def __onRightDown(self, evt):
		""" Display a context menu for selecting the desired date format """
		menu = dabo.ui.dMenu()
		for nm, format in self.formats.items():
			itm = menu.append(format["prompt"], OnHit=self.onRClickMenu)
			format["id"] = itm.GetId()
		self.showContextMenu(menu)
		evt.Continue = False  # otherwise, a GTK unicode menu will appear
	
	
	def onRClickMenu(self, evt):
		""" Set the date format to the selected value."""
		try:
			# See which format has the matching ID
			id = evt.EventData["id"]
			for fmt in self.formats.values():
				if fmt["id"] == id:
					self.dateFormat = fmt["setting"]
			self._setValue(self.date)
		except: pass
	
	
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
		dateEntryKeys = "0123456789/- :"
		if self.ampm:
			dateEntryKeys + "apm"
			
		if key in shortcutKeys:
			# There is a conflict if the key, such as '-', is used in both the 
			# date formatting and as a shortcut. So let's check the text
			# of this field to see if it is a full date or if the user is typing in
			# a value.
			adjust = True
			val = self.GetValue()
			
			if val and self.strToDate(val, testing=True) is None:
				adjust = False
			else:
				# They've just finished typing a new date, or are just
				# positioned on the field. Either way, update the stored 
				# date to make sure they are in sync.
				self.Value = val
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


	def adjustDate(self, key, ctrl=False, shift=False):
		""" Modifies the current date value if the key is one of the 
		shortcut keys.
		"""
		# Save the original value for comparison
		orig = self.date.toordinal()
		# Default direction
		forward = True
		# Flag to indicate errors in date processing
		self.dateOK = True
		# Flag to indicate if we consider boundary conditions
		checkBoundary = True
		# Are we working with dates or datetimes
		isDateTime = isinstance(self.date, datetime.datetime)
		# Did the key move to a boundary?
		toBoundary = False
		
		if key == "t":
			# Today
			if isDateTime:
				self.date = datetime.datetime.now()
			else:
				self.date = datetime.date.today()
			self.Value = self.date
		elif key == "@":
			# DEV! For testing the handling of bad dates
			self.Value = "18/33/1888"
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
				self.date = self.date.replace(day=1)
				self.Value = self.date
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
				self.Value = self.date
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
			self.date = self.date.replace(month=1, day=1)
			self.Value = self.date
			forward = False
			toBoundary = True
		elif key == "r":
			# Last day of year
			self.date = self.date.replace(month=12, day=31)
			self.Value = self.date
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
			if self.date.toordinal() == orig:
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
		self.date += datetime.timedelta(hours=hours)
		self.Value = self.date

	
	def minuteInterval(self, minutes):
		"""Adjusts the date by the given number of minutes; negative
		values move backwards.
		"""
		self.date += datetime.timedelta(minutes=minutes)
		self.Value = self.date

	
	def secondInterval(self, seconds):
		"""Adjusts the date by the given number of seconds; negative
		values move backwards.
		"""
		self.date += datetime.timedelta(seconds=seconds)
		self.Value = self.date

	
	def dayInterval(self, days):
		"""Adjusts the date by the given number of days; negative
		values move backwards.
		"""
		self.date += datetime.timedelta(days)
		self.Value = self.date

	
	def monthInterval(self, months):
		"""Adjusts the date by the given number of months; negative 
		values move backwards.
		"""
		mn = self.date.month + months
		yr = self.date.year
		dy = self.date.day
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
				self.date = self.date.replace(year=yr, month=mn, day=dy)
				ok = True
			except:
				dy -= 1
		self.Value = self.date
	
	
	def setToLastMonthDay(self):
		mn = self.date.month
		td = datetime.timedelta(1)
		while mn == self.date.month:
			self.date += td
		# We're now at the first of the next month. Go back one.
		self.date -= td
		

	def getDateTuple(self):
		return (self.date.year, self.date.month, self.date.day )


	def setDate(self, dt):
		"""Sets the Value to the passed date if this is holding a date value, or
		sets the date portion of the Value if it is a datetime.
		"""
		val = self.date
		if isinstance(val, datetime.datetime):
			self.Value = val.replace(year=dt.year, month=dt.month, day=dt.day)
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
			if self.dateFormat == "American":
				month, day, year, hr, mn, sec = self.dbYearLastDTPat.match(val).groups()
			else:
				day, month, year, hr, mn, sec = self.dbYearLastDTPat.match(val).groups()
			# Convert to numeric
			year = int(year)
			month = int(month)
			day = int(day)
			hr = int(hr)
			mn = int(mn)
			sec = int(round(float(sec), 0) )
		elif self.dbYearLastDPat.match(val):
			# Date-only pattern, YearLast format
			if self.dateFormat == "American":
				month, day, year = self.dbYearLastDPat.match(val).groups()
			else:
				day, month, year = self.dbYearLastDPat.match(val).groups()
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
				
			try:
				if self.dateFormat == "American":
					if  not dtPieces:
						# There was no separator. If the string is in the format
						# 'MMDDYYYY' or even 'MMDDYY', break it up manually
						if len(dt) == 8:
							month = int(dt[:2])
							day = int(dt[2:4])
							year = int(dt[4:])
						elif len(dt) == 6:
							month = int(dt[:2])
							day = int(dt[2:4])
							year = int(dt[4:])
					else:
						month = dtPieces[0]
						day = dtPieces[1]
						year = dtPieces[2]
				elif self.dateFormat == "YMD":
					if  not dtPieces:
						# There was no separator. If the string is in the format
						# 'YYYYMMDD' or even 'YYMMDD', break it up manually
						if len(dt) == 8:
							year = int(dt[:4])
							month = int(dt[4:6])
							day = int(dt[6:])
						elif len(dt) == 6:
							year = int(dt[:2])
							month = int(dt[2:4])
							day = int(dt[4:])
					else:
						year = dtPieces[0]
						month = dtPieces[1]
						day = dtPieces[2]
				# Adjust the rollover for 2-digit years
				if year < 100:
					if year > self.rollover:
						year += 1900
					else:
						year += 2000
			except:
				return ret
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
	
	
	def setFieldVal(self, val):
		""" We need to convert this back to standard database format """
		fmt = "%Y-%m-%d"
		return self.super(self.date.Format(fmt))
	
	def strFromDate(self):
		""" Returns the string representation of the date object
		given the current format.
		"""
		return self.date.strftime(self.getCurrentFormat())
	
	
	def getCurrentFormat(self):
		fmtSrc = self.formats
		if isinstance(self.date, datetime.datetime):
			fmtSrc = self.dateTimeFormats
		fmt = [ f["format"]
				for f in fmtSrc.values() 
				if f["setting"] == self.dateFormat][0]
		return fmt
		
	
	def _setValue(self, val):
		""" We need to override this method, since the actual value
		of this control is in date format, but is represented by its
		text version, which depends on the selected format.
		"""
		if type(val) == type(self.date):
			self.date = val
		else:
			# We need to parse the text into a date object.
			parsedDate = self.strToDate(val)
			# Make sure it's valid
			if parsedDate is not None:
				self.date = parsedDate
			else:
				self.dateOK = False
		# self.super() causes a recursion that we need to figure out.
		#self.super(self.strFromDate())
		super(dDateTextBox, self)._setValue(self.strFromDate())
		
	def _getValue(self):
		return super(dDateTextBox, self)._getValue()
		
		
	Value = property(_getValue, _setValue, None,
			_("""Specifies the current state of the control (the value 
			of the field). (datetime.date or datetime.datetime)""") )


	DynamicValue = makeDynamicProperty(Value)
	


if __name__ == "__main__":
	import test
	test.Test().runTest(dDateTextBox)






#################################
# 	wx.DatePicker-based version of the class
# The one I've written seems to do everything 
# this does and more, so I'm sticking with that.
# I'll probably delete this soon, but for now 
# I'm leaving it here, but commented out.
#################################
#################################
# # I'm in the process of attempting to convert the date text box 
# # to use the native wx.DatePickerCtrl instead of a plain text box.
# # If you'd like to try the new version of the class, just change 
# # 'True' to 'False' in the line below:
# USE_ORIG_CLASS = False
# 
# #####################
# #   This is the new version of the class
# #   It may be unstable and contain debugging output
# #####################
# try:
# 	dpClass = wx.DatePickerCtrl
# except:
# 	# Older wxPython versions don't have this class
# 	USE_ORIG_CLASS = True
# 	dpClass = wx.TextCtrl
# 
# class dDateTextBoxNew(dpClass, dcm.dDataControlMixin):
# 	""" Convenient control for managing dates."""
# 	def __init__(self, parent, properties=None, *args, **kwargs):
# 		self._baseClass = dDateTextBox
# 		preClass = wx.PreDatePickerCtrl
# 		
# 		style = self._extractKey((kwargs, properties), "style")
# 		if not style:
# 			style = wx.DP_DROPDOWN | wx.DP_ALLOWNONE | wx.DP_SHOWCENTURY 
# 		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, 
# 				style=style, validator=wx.DefaultValidator, *args, **kwargs)
# 
# 	
# 	def afterInit(self):
# 		# Tooltip help
# 		self.ToolTipText = """Available Keys:
# =============
# T : Today
# + : Up One Day
# - : Down One Day
# [ : Up One Month
# ] : Down One Month
# M : First Day of Month
# H : Last Day of montH
# Y : First Day of Year
# R : Last Day of yeaR
# C: Popup Calendar to Select
# """
# 		# Grab a reference to the inner text control
# 		self.txt = [cc for cc in self.GetChildren() 
# 				if isinstance(cc, wx.TextCtrl) ][0]
# 		# turn off the the beep
# 		v1 = self.txt.GetValidator()
# 		self.vld = v1.Clone()
# 		self.vld.SetBellOnError(False)
# 
# 		print "BEFORE", self.vld
# 
# 		self.txt.SetValidator(self.vld)
# 		
# 		print "AFTER", self.vld
# 		
# 	
# 	def _initEvents(self):
# 		super(dDateTextBoxNew, self)._initEvents()
# 		self.bindEvent(dEvents.KeyChar, self.__onChar)
# 		self.Bind(wx.EVT_DATE_CHANGED, self.__onWxChange)
# 		self.bindEvent(dEvents.ValueChanged, self.onChange)
# 
# 		self.txt = [cc for cc in self.GetChildren() 
# 				if isinstance(cc, wx.TextCtrl) ][0]
# 		self.txt.Bind(wx.EVT_CHAR, self.__onInnerKeyChar)
# # 		self.txt.Bind(wx.EVT_KEY_DOWN, self.__onInnerKeyDown)
# 		self.txt.Bind(wx.EVT_KEY_UP, self.__onInnerKeyUp)
# 
# 	
# 	def __onInnerKeyChar(self, evt):
# # 		evt.StopPropagation()
# # 		print "INNER", evt.KeyCode()
# 		self.raiseEvent(dEvents.KeyChar, evt)
# 		
# # 	def __onInnerKeyDown(self, evt):
# # 		print "INNER DOWN", evt.KeyCode()
# # 		self.raiseEvent(dEvents.KeyDown, evt)
# 		
# 	def __onInnerKeyUp(self, evt):
# 		print "INNER UP", evt.KeyCode()
# 		self.raiseEvent(dEvents.KeyChar, evt)
# 		
# 	
# 	def __onWxChange(self, evt):
# 		self.raiseEvent(dEvents.ValueChanged, evt)
# 	
# 	def onChange(self, evt):
# 		"""Called whenever the user changes the value in the control"""
# 		pass
# #		print "CHANGE!", self.Value
# 		
# 	
# 	def __onChar(self, evt):
# 		""" If a shortcut key was pressed, process that. Otherwise, eat 
# 		inappropriate characters.
# 		"""
# 		
# 		print "CHAR", evt.EventData["keyCode"]
# 		
# 		try:
# 			keycode = evt.EventData["keyCode"]
# 		except:
# 			# spurious key event; ignore
# 			return
# 		if keycode < 0 or keycode > 255:
# 			# Let it be handled higher up
# 			
# 			print "IGNORING"
# 			return
# 
# 		key = chr(keycode).lower()
# 		shortcutKeys = "t+-mhyrc[]"
# 		dateEntryKeys = "0123456789/-"
# 		
# 		if key in shortcutKeys:
# 			evt.Continue = False
# 			self.adjustDate(key)
# 			
# 
# 	def adjustDate(self, key):
# 		""" Modifies the current date value if the key is one of the 
# 		shortcut keys.
# 		"""
# 		if key == "t":
# 			# Today
# 			self.Value = wx.DateTime.Now()
# 		elif key == "+":
# 			# Forward 1 day
# 			self.dayInterval(1)
# 		elif key == "-":
# 			# Back 1 day
# 			self.dayInterval(-1)
# 		elif key == "m":
# 			# First day of month
# 			val = self.getValidValue()
# 			if val.GetDay() == 1:
# 				# Already at the first of the month; go back one month
# 				self.dayInterval(-1)
# 			val = self.getValidValue()
# 			newVal = val.SetDay(1)
# 			self.Value = newVal
# 		elif key == "h":
# 			# Last day of month
# 			val = self.getValidValue()
# 			origDay = val.GetDay()
# 			val.SetToLastMonthDay()
# 			if origDay == val.GetDay():
# 				# Already at end of month; increment the month
# 				self.dayInterval(1)
# 				val = self.getValidValue()
# 				val.SetToLastMonthDay()
# 			self.Value = val
# 		elif key == "y":
# 			# First day of year
# 			val = self.getValidValue()
# 			if val.GetDay() == 1:
# 				if val.GetMonth() == 0:
# 				# Already at the first of the year; go back one year
# 					self.dayInterval(-1)
# 			val = self.getValidValue()
# 			newval = val.SetDay(1)
# 			newval = newval.SetMonth(0)
# 			self.Value = newval
# 		elif key == "r":
# 			# Last day of year
# 			val = self.getValidValue()
# 			origDay, origMonth = val.GetDay(), val.GetMonth()
# 			val.SetMonth(11)
# 			val.SetToLastMonthDay()
# 			if (origDay, origMonth) == (val.GetDay(), val.GetMonth()):
# 				# Already at end of month; increment the month
# 				self.dayInterval(1)
# 				val = self.getValidValue()
# 				val.SetMonth(11)
# 				val.SetToLastMonthDay()
# 			self.Value = val
# 		elif key == "[":
# 			# Back one month
# 			self.monthInterval(-1)
# 		elif key == "]":
# 			# Forward one month
# 			self.monthInterval(1)
# 		else:
# 			# This shouldn't happen, because onChar would have filtered it out.
# 			dabo.infoLog.write("Warning in dDateTextBox.adjustDate: %s key sent." % key)
# 			return
# 	
# 	
# 	def getValidValue(self):
# 		""" Returns the value of the control, or Now() if the control
# 		does not contain a valid date.
# 		"""
# 		val = self.GetValue()
# 		if not val.IsValid():
# 			val = wx.DateTime.Now()
# 		return val		
# 
# 
# 	def dayInterval(self, days):
# 		val = self.getValidValue()
# 		newval = val.AddDS(wx.DateSpan.Days(days))
# 		self.Value = newval
# 
# 	
# 	def monthInterval(self, months):
# 		val = self.getValidValue()
# 		newval = val.AddDS(wx.DateSpan.Months(months))
# 		self.Value = newval
# 	
# 	
# 	def getBlankValue(self):
# 		""" Override the default method; we need a wx-specific value."""
# 		return wx.DateTime()
