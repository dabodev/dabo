import wx, datetime
import dSpinner, dPanel, dDataControlMixin

class BaseSpinner(dSpinner.dSpinner):
	def initProperties(self):
		self.SelectOnEntry = True
	
	def refresh(self):
		""" Update control's value to match the current value from the bizobj.
		"""
		if self.Parent.DataSource and self.Parent.DataField:
			try:
				self.Parent.Value = self.Parent.getFieldVal()
				self.Parent.Enabled = self.Parent.enabled
			except (TypeError, dException.NoRecordsException):
				self.Parent.Value = self.Parent.getBlankValue()
				self.Parent.Enabled = False
			self.Parent._oldVal = self.Parent.Value
	
	def flushValue(self):
		""" Save any changes to the underlying bizobj field.
		"""
		curVal = self.Parent.Value
		if curVal != self.Parent._oldVal and self.Parent.DataSource and self.Parent.DataField:
			self.Parent.setFieldVal(curVal)
		self.Parent._oldVal = curVal
		
class YearSpinner(BaseSpinner):
	def initProperties(self):
		YearSpinner.doDefault()
		self.Min = 1
		self.Max = 9999
		self.Width = 55
	
class MonthSpinner(BaseSpinner):
	def initProperties(self):
		MonthSpinner.doDefault()
		self.Min = 1
		self.Max = 12
		self.Width = 35
		
class DaySpinner(BaseSpinner):
	def initProperties(self):
		DaySpinner.doDefault()
		self.Min = 1
		self.Max = 31
		self.Width = 35
			
		
class dDateControl(dPanel.dPanel, dDataControlMixin.dDataControlMixin):

	def __init__(self, *args, **kwargs):
		dPanel.dPanel.__init__(self, *args, **kwargs)
		dDataControlMixin.dDataControlMixin.__init__(self)
		
		
	def initProperties(self):
		self.addObject(MonthSpinner, 'spnMonth')
		self.addObject(DaySpinner, 'spnDay')
		self.addObject(YearSpinner, 'spnYear')
		
	def afterInit(self):
		self.Name = 'dDateControl'
		sz = wx.BoxSizer(wx.VERTICAL)
		#sz = self.GetSizer()
		bs = wx.BoxSizer(wx.HORIZONTAL)
		bs.Add(self.spnMonth)
		bs.Add(self.spnDay)
		bs.Add(self.spnYear)
		sz.Add(bs, 1, wx.EXPAND)
		self.SetSizer(sz)
		
	def GetValue(self):
		y,m,d = self.spnYear.Value, self.spnMonth.Value, self.spnDay.Value
		if y < 1 or y > 9999:
			y = 1
		if m < 1 or m > 12:
			m = 1
		if d < 1 or d > 31:
			d = 1
		try:
			return datetime.date(y,m,d)
		except ValueError:
			return datetime.date(1,1,1)

	def SetValue(self, value):
		if type(value) == type(datetime.date(1,1,1)):
			self.spnYear.Value = value.year
			self.spnMonth.Value = value.month
			self.spnDay.Value = value.day
		else:
			self.spnYear.Value, self.spnMonth.Value, self.spnDay.Value = 1,1,1
		
if __name__ == '__main__':
	import test
	class c(dDateControl):
		def OnText(self, event): print "OnText!"
	test.Test().runTest(c)
