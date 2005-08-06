import re, datetime
import wx, dabo, dabo.ui
import wx.lib.masked
import wx.lib.masked.textctrl as textctrl
import wx.lib.masked.numctrl as numctrl

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dabo.ui.uiwx.dDataControlMixin as dcm
import dabo.ui.uiwx.dTextBox as dTextBox
import format

from dabo.dLocalize import _

def _add_properties(parent_name, param_names):
	ret = []
	for param in param_names:
		prop = param[0].upper() + param[1:]
		old_getter = '%s.Get%s'  % (parent_name, prop)
		old_setter = '%s.Set%s' % (parent_name, prop)
		new_setter = 'Set%s' % (prop)
		setter_def = 'def %s(self, val): %s(self, val),'\
			     'self._formatter.SetParameters(%s=val)' \
			     % (new_setter, old_setter, param)
		prop_def = '%s = property(%s, %s, None,'\
			   '"See documentation on wx.lib.masked.textctrl")' % (prop, old_getter, new_setter)
		ret.extend([setter_def, prop_def])

	return tuple(ret)
	
class dMaskedTextBox(textctrl.TextCtrl, dTextBox):
	""" Allows editing one line of string or unicode data
	using text mask.
	"""
	_IsContainer = False
	for p in _add_properties('textctrl.TextCtrl', textctrl.TextCtrl.exposed_basectrl_params):
		exec(p)
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dMaskedTextBox
		self._formatter = format.TextFormat(**kwargs)
		preClass = textctrl.TextCtrl
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	# dPemMixin clashes with textctrl.TextCtrl
	# fortunately they have different number of arguments
	def _setFont(self, *argv):
		if argv: dTextBox._setFont(self, *argv) 
		else: textctrl.TextCtrl._setFont(self)

	def _getValue(self):
		try:
			_value = self._value
		except AttributeError:
			_value = self._value = ""
			
		dataType = type(_value)
		if self._formatter.FormatType in ('date', 'time'):
			strVal = self.GetValue()
		else:
			strVal = self.GetPlainValue()

		value = self._formatter.fromstr(strVal, dataType)
		if value is None:
			dabo.errorLog.write("Couldn't convert literal '%s' to %s."
					    % (strVal, dataType))
			value = self._value
		return value

	def _setValue(self, value):
		strVal = self._getStringValue(value)
		_oldVal = self.Value
		self._value = value

		self.SetValue(strVal)
		
		if type(_oldVal) != type(value) or _oldVal != value:
			self._afterValueChanged()

		
	def _getStringValue(self, value):
		return self._formatter.format(value)

	Value = property(_getValue, _setValue, None,
			 "Specifies the current state of the control (the value of the field). (varies)")

class dMaskedNumBox(numctrl.NumCtrl, dTextBox):
	""" Allows editing numbers using masked formats.
	"""
	_IsContainer = False
	for p in _add_properties('numctrl.NumCtrl',
				 numctrl.NumCtrl.exposed_basectrl_params + \
				 tuple(numctrl.NumCtrl.valid_ctrl_params.keys())):
		exec(p)
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dMaskedNumBox
		self._formatter = format.NumFormat(**kwargs)
		preClass = numctrl.NumCtrl
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	def flushValue(self):
		self.SetValue(self.Value)
		super(numctrl.NumCtrl, self).flushValue()
		
	def _setFont(self, *argv):
		if argv: dTextBox._setFont(self, *argv)
		else: numctrl.NumCtrl._setFont(self)

	def _getValue(self):
		return self.GetValue()

	def _setValue(self, value):
		_oldVal = self.Value
		self._value = value
		self.SetValue(value)
		
		if type(_oldVal) != type(value) or _oldVal != value:
			self._afterValueChanged()

		
	def _getStringValue(self, value):
		return self._formatter.format(value)

	Value = property(_getValue, _setValue, None,
			 "Specifies the current state of the control (the value of the field). (varies)")

if __name__ == "__main__":
	import dabo.ui.uiwx.test as test

	# This test sets up several textboxes, each editing different data types.	
	class TestBase(dabo.common.dObject):
		def initProperties(self):
			TestBase.doDefault()
			self.LogEvents = ["ValueChanged",]
			
		def initEvents(self):
			TestBase.doDefault()
			self.bindEvent(dabo.dEvents.ValueChanged, self.onValueChanged)
			
		def onValueChanged(self, evt):
			print "%s.onValueChanged:" % self.Name, self.Value, type(self.Value)
			
	class DateText(TestBase, dMaskedTextBox):
		def afterInit(self):
			self.Autoformat = 'EUDATE24HRTIMEDDMMYYYY.HHMMSS'
			self.Value = datetime.date.today()
	
	class DateTimeText(TestBase, dMaskedTextBox):
		def afterInit(self):
			self.Autoformat = 'EUDATE24HRTIMEDDMMYYYY/HHMM'
			self.Value = datetime.datetime.now()

	class IntText(TestBase, dMaskedNumBox):
		def afterInit(self):
			self.Value = 23
		
	class FloatText(TestBase, dMaskedNumBox):
		def afterInit(self):
			self.FractionWidth = 2
			self.IntegerWidth = 5
			self.Value = 23.5
			
	class BoolText(TestBase, dMaskedTextBox):
		def afterInit(self):
			self.Value = False
	
	class StrText(TestBase, dMaskedTextBox):
		def afterInit(self):
			self.Formatcodes="F"
			self.Mask = "XXX-XXXXXXXXXXXXXXXXXXXXXXXXXx"
			self.Value = "Lunchtime"
	
	testParms = [IntText, FloatText, StrText, BoolText, DateText, DateTimeText]			
	
	try:
		import mx.DateTime
		class MxDateTimeText(dMaskedTextBox, TestBase):
			def afterInit(self):
				self.Autoformat = 'EUDATE24HRTIMEDDMMYYYY.HHMMSS'
				self.Value = mx.DateTime.now()

				
		testParms.append(MxDateTimeText)
	except:
		# skip it: mx may not be available
		pass
		
	test.Test().runTest(testParms)
