# -*- coding: utf-8 -*-
import locale
import wx
import dabo

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty



class dSpinnerX(dabo.ui.dPanel, dcm.dDataControlMixin):
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dSpinnerX
		self.__constructed = False
		self._spinWrap = False
		self._min = 0
		self._max = 100
		self._increment = 1
		val = self._extractKey((properties, attProperties, kwargs), "Value", 0)
		if isinstance(val, basestring):
			if val.find(locale.localeconv()["decimal_point"]) > -1:
				val = float(val)
			else:
				val = int(val)
		super(dSpinnerX, self).__init__(parent=parent, properties=properties, 
				attProperties=attProperties, *args, **kwargs)
		# Create the child controls
		self._textbox = dabo.ui.dTextBox(self, Value=val)
		class dSpinButton(dcm.dDataControlMixin, wx.SpinButton):
			def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
				preClass = wx.PreSpinButton
				dcm.dDataControlMixin.__init__(self, preClass, parent, properties, attProperties, 
						*args, **kwargs)

		self._spinner = dSpinButton(parent=self)
		self.__constructed = True
		self.Sizer = dabo.ui.dSizer("h")
		self.Sizer.append(self._textbox, 1, valign="middle")
		self.Sizer.appendSpacer(2)
		self.Sizer.append(self._spinner, valign="middle")
		self.fitToSizer()
		# Because several properties could not be set until after the child
		# objects were created, we need to manually call _setProperties() here.
		self._setProperties(self._properties)
		
		self._spinner.Bind(wx.EVT_SPIN_UP, self.__onWxSpinUp)
		self._spinner.Bind(wx.EVT_SPIN_DOWN, self.__onWxSpinDown)
	
	
	def _constructed(self):
		"""Returns True if the ui object has been fully created yet, False otherwise."""
		return self.__constructed
	
	
	def __onWxSpinUp(self, evt):
		evt.Veto()
		curr = self._textbox.Value
		new = curr + self.Increment
		if new <= self.Max:
			self._textbox.Value = new
		elif self._spinWrap:
			xs = new - self.Max
			self._textbox.Value = self.Min + xs


	def __onWxSpinDown(self, evt):
		evt.Veto()
		curr = self._textbox.Value
		new = curr - self.Increment
		if new >= self.Min:
			self._textbox.Value = new
		elif self._spinWrap:
			xs = self.Min - new
			self._textbox.Value = self.Max - xs


	# Property get/set definitions begin here
	def _getIncrement(self):
		return self._increment

	def _setIncrement(self, val):
		if self._constructed():
			self._increment = val
		else:
			self._properties["Increment"] = val


	def _getMax(self):
		return self._max

	def _setMax(self, val):
		if self._constructed():
			self._max = val
			self._spinner.SetRange(self.Min, val)
		else:
			self._properties["Max"] = val


	def _getMin(self):
		return self._min

	def _setMin(self, val):
		if self._constructed():
			self._min = val
			self._spinner.SetRange(val, self.Max)
		else:
			self._properties["Min"] = val


	def _getSpinnerWrap(self):
		return self._spinner._hasWindowStyleFlag(wx.SP_WRAP)

	def _setSpinnerWrap(self, val):
		if self._constructed():
			self._spinWrap = val
			self._spinner._delWindowStyleFlag(wx.SP_WRAP)
			if val:
				self._spinner._addWindowStyleFlag(wx.SP_WRAP)
		else:
			self._properties["SpinnerWrap"] = val


	def _getValue(self):
		return self._textbox.Value

	def _setValue(self, val):
		if self._constructed():
			self._textbox.Value = val
		else:
			self._properties["Value"] = val


	Increment = property(_getIncrement, _setIncrement, None,
			_("Amount the control's value changes when the spinner buttons are clicked  (int/float)"))

	Max = property(_getMax, _setMax, None,
			_("Maximum value for the control  (int/float)"))
	
	Min = property(_getMin, _setMin, None,
			_("Minimum value for the control  (int/float)"))

	SpinnerWrap = property(_getSpinnerWrap, _setSpinnerWrap, None,
			_("Specifies whether the spinner value wraps at the high/low value. (bool)"))

	Value = property(_getValue, _setValue, None,
			_("Value of the control  (int/float)"))
	


	DynamicIncrement = makeDynamicProperty(Increment)
	DynamicMax = makeDynamicProperty(Max)
	DynamicMin = makeDynamicProperty(Min)
	DynamicSpinnerWrap = makeDynamicProperty(SpinnerWrap)




class _dSpinnerX_test(dSpinnerX):
	def initProperties(self):
		self.Max = 12
		self.Min = -5
		self.Value = 4.50
		self.Increment = 0.75
		self.SpinnerWrap = True
# 		self.DataSource="form"
# 		self.DataField="Caption"

	def onHit(self, evt):
		print "HIT!", self.Value
		

if __name__ == "__main__":
	import test
	test.Test().runTest(_dSpinnerX_test)
