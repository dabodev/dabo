import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dSpinner(wx.SpinCtrl, dcm.dDataControlMixin):
	""" Allows editing integer values.
	"""
	def __init__(self, parent, id=-1, name="dSpinner", style=0, *args, **kwargs):

		self._baseClass = dSpinner

		pre = wx.PreSpinCtrl()
		self._beforeInit(pre)
		pre.Create(parent, id, name=name, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)

		dcm.dDataControlMixin.__init__(self, name)
		self._afterInit()


	def initEvents(self):
		dSpinner.doDefault()
		# Catch the wx events and raise the dabo events:
		self.Bind(wx.EVT_SPINCTRL, self._onWxHit)
		

	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getMax(self):
		return self._pemObject.GetMax()
	def _setMax(self, value):
		rangeLow = self._pemObject.GetMin()
		rangeHigh = int(value)
		self._pemObject.SetRange(rangeLow, rangeHigh)

	def _getMin(self):
		return self.GetMin()
	def _setMin(self, value):
		rangeLow = int(value)
		rangeHigh = self.Max
		self.SetRange(rangeLow, rangeHigh)

	def _getSpinnerWrap(self):
		return self.hasWindowStyleFlag(wx.SP_WRAP)
	def _setSpinnerWrap(self, value):
		self.delWindowStyleFlag(wx.SP_WRAP)
		if value:
			self.addWindowStyleFlag(wx.SP_WRAP)

	def _getSpinnerArrowKeys(self):
		return self.hasWindowStyleFlag(wx.SP_ARROW_KEYS)
	def _setSpinnerArrowKeys(self, value):
		self.delWindowStyleFlag(wx.SP_ARROW_KEYS)
		if value:
			self.addWindowStyleFlag(wx.SP_ARROW_KEYS)

	# Property definitions:
	Min = property(_getMin, _setMin, None, 
						'Specifies the lowest possible value for the spinner. (int)')

	Max = property(_getMax, _setMax, None, 
						'Specifies the highest possible value for the spinner. (int)')

	SpinnerWrap = property(_getSpinnerWrap, _setSpinnerWrap, None,
						'Specifies whether the spinner value wraps at the high/low value. (bool)')

	SpinnerArrowKeys = property(_getSpinnerArrowKeys, _setSpinnerArrowKeys, None,
						'Specifies whether the user can use the arrow keys to increment. (bool)')

if __name__ == "__main__":
	import test
	test.Test().runTest(dSpinner)
