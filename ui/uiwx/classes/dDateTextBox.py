import wx
import dabo
from dabo.dLocalize import _
import dTextBox
import re


class dDateTextBox(dTextBox.dTextBox):
	""" This is a specialized textbox class designed to work with date values.
	It provides handy shortcut keystrokes so that users can quickly navigate
	to the date value they need. The keystrokes are the same as those used
	by Quicken, the popular personal finance program.
	"""
	
	def beforeInit(self, pre):
		self.date = wx.DateTime()
		self.date.SetToCurrent()
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

	
	def afterInit(self):
		self.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
		self.Bind(wx.EVT_CHAR, self.onChar)
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
"""
	
	
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
		keycode = evt.KeyCode()
		if keycode < 0 or keycode > 255:
			# Let it be handled higher up
			evt.Skip()
			return
		key = chr(keycode).lower()
		shortcutKeys = [ch for ch in "tq+-mhyr[]"]
		dateEntryKeys = [ch for ch in "0123456789/-"]
		
		if key in shortcutKeys:
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
		else:
			# This shouldn't happen, because onChar would have filtered it out.
			dabo.infoLog.write("Warning in dDateTextBox.adjustDate: %s key sent." % key)
			return
		
		if not self.dateOK:
			return
		if self.continueAtBoundary:
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

	
	def strToDate(self, val):
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
				if self.dateFormat == "American":
					month = dtPieces[0]
					day = dtPieces[1]
					year = dtPieces[2]
				elif self.dateFormat == "YMD":
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
			dabo.errorLog.write(_("Invalid date specified. Y,M,D = %s, %s, %s" % (year, month, day) ))
			ret = None
		return ret
	
	
	def setFieldVal(self, val):
		""" We need to convert this back to standard database format """
		fmt = "%Y-%m-%d"
		return dDateTextBox.doDefault(self.date.Format(fmt) )
		
	
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
		fmt = [ f["format"]
				for f in self.formats.values() 
				if f["setting"] == self.dateFormat][0]
		dDateTextBox.doDefault(self.date.Format(fmt) )
	def _getValue(self):
		return self.GetValue()
	Value = property(_getValue, _setValue, None,
			"Specifies the current state of the control (the value of the field). (varies)" )
	


if __name__ == "__main__":
	import test
	class c(dDateTextBox): pass
	test.Test().runTest(c)
