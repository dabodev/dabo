import re
import wx
import wx.calendar
import dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dabo.dLocalize import _
import dTextBox, dPanel, dCommandButton



class CalPanel(dPanel.dPanel):
	def __init__(self, parent, pos=(-1,-1), dt=wx.DateTime_Now(), ctrl=None ):
		if dt is None:
			self.date = wx.DateTime_Now()
		else:
			self.date = dt
		self.ctrl = ctrl
		CalPanel.doDefault(parent, pos=pos)
	
	def afterInit(self):
		""" Create the calendar control, and resize this panel 
		to the calendar's size
		"""
		self.cal = wx.calendar.CalendarCtrl(self, -1, self.date, pos = (5,5), 
				style = wx.calendar.CAL_SUNDAY_FIRST
				| wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION
				)
		self.Bind(wx.calendar.EVT_CALENDAR, self.onCal, id=self.cal.GetId())
		wd, ht = self.cal.GetSize()
		self.Size = (wd+10, ht+10)
		self.BackColor = (192, 192, 0)
		self.cal.Show(True)
		
	def onCal(self, evt):
		if self.ctrl is not None:
			self.ctrl.Value = evt.GetDate()
		self.cal.Destroy()
		self.Show(False)
		

class dDateTextBox(dTextBox.dTextBox):
	""" This is a specialized textbox class designed to work with date values.
	It provides handy shortcut keystrokes so that users can quickly navigate
	to the date value they need. The keystrokes are the same as those used
	by Quicken, the popular personal finance program.
	"""
	def __init__(self, parent, id=-1, name="dDateTextBox", style=0, *args, **kwargs):
		dDateTextBox.doDefault(parent, id, name, style, *args, **kwargs)

	def beforeInit(self, pre):
		self.date = wx.DateTime_Now()
		self.formats = {
				wx.NewId(): {"prompt": "American (MM/DD/YYYY)", 
					"setting" : "American", 
					"format" : "%m/%d/%Y"},
				wx.NewId(): {"prompt": "YMD (YYYY-MM-DD)", 
					"setting": "YMD", 
					"format" : "%Y-%m-%d"} }
		# Default format; can be changed in setup code or in RightClick
		self.dateFormat = "American"
		# Pattern for recognizing dates from databases
		self.dbPat = re.compile("(\d{4})[-/.](\d{2})[-/.](\d{2}) (\d{2}):(\d{2}):([\d\.]+)")
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
		# Temporary, while the new dEvents model is finished
		self.useWxEvents = True
	
	
	def afterInit(self):
		if self.showCalButton:
			# Create a button that will display the calendar
			self.calButton = dCommandButton.dCommandButton(self.Parent)
			self.calButton.Size = (self.Height, self.Height)
			self.calButton.Right = self.Right
			self.calButton.Caption = "V"
			self.calButton.Show(True)
			self.calButton.bindEvent(dabo.dEvents.Hit, self.onDblClick)
#			self.Parent.Bind(wx.EVT_BUTTON, self.onDblClick, id=self.calButton.GetId() )
# 			calSizer = wx.BoxSizer(wx.HORIZONTAL)
# 			calSizer.Add(self, 1, wx.EXPAND)
# 			calSizer.Add(self.calButton)
			
		# The first form is needed to avoid a GTK unicode menu from appearing:
		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
		#self.bindEvent(dabo.dEvents.MouseRightDown, self.onRightClick)
		if self.useWxEvents:
			self.Bind(wx.EVT_CHAR, self.onChar)
		else:
	 		self.bindEvent(dabo.dEvents.KeyChar, self.onChar)
		self.bindEvent(dabo.dEvents.MouseLeftDoubleClick, self.onDblClick)
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
	
	
	def onLostFocus(self, evt):
		""" Since the actual value is the date object, we need to refresh
		the displayed text with the properly formatted character date.
		"""
		dDateTextBox.doDefault(evt)
		# Refresh the displayed value
		self.Value = self.GetValue()
	
	
	def onDblClick(self, evt):
		""" Display a calendar to allow users to select dates.
		"""
		self.showCalendar()
		
	def showCalendar(self):
		self.calPanel = CalPanel(self.Parent, pos = (self.Left, self.Bottom), 
				dt = self.strToDate(self.Value), ctrl=self )
		self.calPanel.Show(True)
		self.calPanel.SetFocus()
		
	
	def onRightClick(self, evt):
		""" Display a context menu for selecting the desired date format """
		men = wx.Menu()
		for id, format in self.formats.items():
			itm = wx.MenuItem(men, id, format["prompt"])
			men.AppendItem(itm)
			self.Parent.Bind(wx.EVT_MENU, self.onRClickMenu, itm)
		self.Parent.PopupMenu(men, evt.GetPosition() )
		
		
	def onRClickMenu(self, evt):
		""" Set the date format to the selected value."""
		try:
			self.dateFormat = self.formats[evt.GetId()]["setting"]
			self._setValue(self.date)
		except: pass
	
	
	def onChar(self, evt):
		""" If a shortcut key was pressed, process that. Otherwise, eat 
		inappropriate characters.
		"""
		if self.useWxEvents:
			keycode = evt.GetKeyCode()
		else:
			keycode = evt.EventData["keyCode"]
		if keycode < 0 or keycode > 255:
			# Let it be handled higher up
			return
		
		# Tried adding this, but it doesn't do anything.
		#evt.StopPropagation()
		
		key = chr(keycode).lower()
		shortcutKeys = "t+-mhyrc[]"
		dateEntryKeys = "0123456789/-"
		
		if key in shortcutKeys:
			# There is a conflict if the key, such as '-', is used in both the 
			# date formatting and as a shortcut. So let's check the text
			# of this field to see if it is a full date or if the user is typing in
			# a value.
			adjust = True
			val = self.GetValue()
			
			if val and self.strToDate(val, testing=True) is None:
				adjust = False
				evt.Skip()
			else:
				# They've just finished typing a new date, or are just
				# positioned on the field. Either way, update the stored 
				# date to make sure they are in sync.
				self.Value = val
			if adjust:
				self.adjustDate(key)
	
		elif key in dateEntryKeys:
			# key can be used for date entry: allow
			evt.Skip()
		elif keycode in range(32, 129):
			# key is in ascii range, but isn't one of the above
			# allowed key sets. Disallow.
			pass
		else:
			# Pass the key up the chain to process - perhaps a Tab, Enter, or Backspace...
			evt.Skip()


	def adjustDate(self, key):
		""" Modifies the current date value if the key is one of the 
		shortcut keys.
		"""
		# Save the original value for comparison
		orig = self.date.GetJDN()
		# Default direction
		forward = True
		# Flag to indicate errors in date processing
		self.dateOK = True
		# Flag to indicate if we consider boundary conditions
		checkBoundary = True
		
		if key == "t":
			# Today
			self.date.SetToCurrent()
			self.Value = self.date
# 		elif key == "q":
# 			# DEV! For testing the handling of bad dates
# 			self.Value = "18/33/1888"
		elif key == "+":
			# Forward 1 day
			self.dayInterval(1)
		elif key == "-":
			# Back 1 day
			self.dayInterval(-1)
			forward = False
		elif key == "m":
			# First day of month
			intv = -1 * (self.date.GetDay() -1)
			self.dayInterval(intv)
			forward = False
		elif key == "h":
			# Last day of month
			self.date.SetToLastMonthDay()
			self.Value = self.date
 		elif key == "y":
 			# First day of year
 			self.date.SetMonth(0).SetDay(1)
 			self.Value = self.date
			forward = False
 		elif key == "r":
 			# Last day of year
 			self.date.SetMonth(11).SetDay(31)
 			self.Value = self.date
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
		if checkBoundary and self.continueAtBoundary:
			if self.date.GetJDN() == orig:
				# Date hasn't changed; means we're at the boundary
				# (first or last of the chosen interval). Move 1 day in
				# the specified direction, then re-apply the key
				if forward:
					self.dayInterval(1)
				else:
					self.dayInterval(-1)
				self.adjustDate(key)
	
	
	def dayInterval(self, days):
		self.date.AddDS(wx.DateSpan.Days(days))
		self.Value = self.date

	
	def monthInterval(self, months):
		self.date.AddDS(wx.DateSpan.Months(months))
		self.Value = self.date
	

	def getDateTuple(self):
		return (self.date.GetYear(), self.date.GetMonth(), self.date.GetDay() )

	
	def strToDate(self, val, testing=False):
		""" This routine parses the text representing a date, using the 
		current format. It adjusts for years given with two digits, using 
		the rollover value to determine the century. It then returns a
		wx.DateTime object set to the entered date.
		"""
		val = str(val)
		ret = None
		
		# See if it matches any standard pattern. Values retrieved
		# from databases will always be in their own format
		if self.dbPat.match(val):
			year, month, day, hr, mn, sec = self.dbPat.match(val).groups()
			# Convert to numeric
			year = int(year)
			month = int(month)
			day = int(day)
			hr = int(hr)
			mn = int(mn)
			sec = int(round(float(sec), 0) )
		else:
			# See if there is a time component
			try:
				(dt, tm) = val.split()
				(hr, mn, sec) = tm.split(":")
				hr = int(hr)
				mn = int(mn)
				sec = int(round(float(sec), 0) )
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
		# Remember, months are zero-based here
		try:
			ret = wx.DateTimeFromDMY(day, month-1, year)
			ret.SetHour(hr)
			ret.SetMinute(mn)
			ret.SetSecond(sec)
		except:
			if not testing:
				# Don't fill up the logs with error messages from tests that 
				# are expected to fail.
				dabo.errorLog.write(_("Invalid date specified. Y,M,D = %s, %s, %s" % (year, month, day) ))
			ret = None
		return ret
	
	
	def setFieldVal(self, val):
		""" We need to convert this back to standard database format """
		fmt = "%Y-%m-%d"
		return dDateTextBox.doDefault(self.date.Format(fmt) )
	
	
	def strFromDate(self):
		""" Returns the string representation of the date object
		given the current format.
		"""
		return self.date.Format(self.getCurrentFormat())
	
	
	def getCurrentFormat(self):
		fmt = [ f["format"]
				for f in self.formats.values() 
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
		dDateTextBox.doDefault(self.strFromDate() )
		
	def _getValue(self):
		return self.GetValue()
		
	Value = property(_getValue, _setValue, None,
			"Specifies the current state of the control (the value of the field). (varies)" )
	


if __name__ == "__main__":
	import test
	test.Test().runTest(dDateTextBox)
