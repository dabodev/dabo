# -*- coding: utf-8 -*-
import re
import datetime
import wx
import wx.lib.masked as masked
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dTextBoxMixin as tbm

class dTextBox(tbm.dTextBoxMixin, wx.TextCtrl):
	"""Creates a text box for editing one line of string data."""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dTextBox
		
		msk = self._extractKey((properties, attProperties, kwargs), "Mask")
		if msk is not None:
			kwargs["mask"] = msk
			kwargs["formatcodes"] = "_"
			def _preMask():
				return wx.lib.masked.TextCtrl
			preClass = wx.lib.masked.TextCtrl
			
			dTextBox.__bases__ = (tbm.dTextBoxMixin, masked.TextCtrl)
		else:
			preClass = wx.PreTextCtrl
		
		tbm.dTextBoxMixin.__init__(self, preClass, parent, properties, attProperties, 
				*args, **kwargs)



class _dTextBox_test(dTextBox):
	def afterInit(self):
		self.Value = "Dabo rules!"
		self.Size = (200, 20)

if __name__ == "__main__":
	import test
	import datetime

	# This test sets up several textboxes, each editing different data types.	
	class TestBase(dTextBox):
		def initProperties(self):
			self.SelectOnEntry = True
			self.super()
			self.LogEvents = ["ValueChanged",]
			
		def onValueChanged(self, evt):
			if self.IsSecret:
				print "%s changed, but the new value is a secret! " % self.Name,
			else:
				print "%s.onValueChanged:" % self.Name, self.Value, type(self.Value),
			if self.Mask:
				print "Masked Value:", self.MaskedValue
			else:
				print

	class IntText(TestBase):
		def afterInit(self):
			self.Value = 23
		
	class FloatText(TestBase):
		def afterInit(self):
			self.Value = 23.5
	
	class BoolText(TestBase):
		def afterInit(self):
			self.Value = False
	
	class StrText(TestBase):
		def afterInit(self):
			self.Value = "Lunchtime"

	class PWText(TestBase):
		def __init__(self, *args, **kwargs):
			kwargs["PasswordEntry"] = True
			super(PWText, self).__init__(*args, **kwargs)
		def afterInit(self):
			self.Value = "TopSecret!"

	class DateText(TestBase):
		def afterInit(self):
			self.Value = datetime.date.today()
	
	class DateTimeText(TestBase):
		def afterInit(self):
			self.Value = datetime.datetime.now()
	
	class MaskedText(TestBase):
		def __init__(self, *args, **kwargs):
			kwargs["Mask"] = "(###) ###-####"
			super(MaskedText, self).__init__(*args, **kwargs)
	
	testParms = [IntText, FloatText, StrText, PWText, BoolText, DateText, DateTimeText, MaskedText]
	
	try:
		import mx.DateTime
		class MxDateTimeText(TestBase):
			def afterInit(self):
				self.Value = mx.DateTime.now()
				
		testParms.append(MxDateTimeText)
	except ImportError:
		# skip it: mx may not be available
		pass

	try:
		import decimal
		class DecimalText(TestBase):
			def afterInit(self):
				self.Value = decimal.Decimal("23.42")

		testParms.append(DecimalText)

	except ImportError:
		# decimal only in python >= 2.4
		pass

		
	test.Test().runTest(testParms)
