import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dSlider(wx.Slider, dcm.dDataControlMixin):
	""" Allows editing integer values with a slider control.
	
	Slider does not allow entering a value with the keyboard.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dSlider
		
		style = self._extractKey(kwargs, "style")
		if style is None:
			kwargs["style"] = wx.SL_AUTOTICKS
		else:
			kwargs["style"] = style | wx.SL_AUTOTICKS
		
		preClass = wx.PreSlider
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	
	def _initEvents(self):
		super(dSlider, self)._initEvents()
		self.Bind(wx.EVT_SCROLL, self._onWxHit)


	def _onWxHit(self, evt):
		self.flushValue()
		super(dSlider, self)._onWxHit(evt)

				
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getMin(self):
		return self.GetMin()

	def _setMin(self, value):
		if self._constructed():
			self.SetMin(value)
		else:
			self._properties["Min"] = value
		

	def _getMax(self):
		return self.GetMax()

	def _setMax(self, value):
		if self._constructed():
			self.SetMax(value)
		else:
			self._properties["Max"] = value
		

	def _getOrientation(self):
		if self.GetWindowStyle() & wx.SL_VERTICAL:
			return "Vertical"
		else:
			return "Horizontal"
			
	def _setOrientation(self, value):
		self._delWindowStyleFlag(wx.SL_HORIZONTAL)
		self._delWindowStyleFlag(wx.SL_VERTICAL)
		if value.lower()[:1] == "h":
			self._addWindowStyleFlag(wx.SL_HORIZONTAL)
		else:
			self._addWindowStyleFlag(wx.SL_VERTICAL)


	def _getLineSize(self):
		return self.GetLineSize()

	def _setLineSize(self, value):
		if self._constructed():
			return self.SetLineSize(value)
		else:
			self._properties["LineSize"] = value


	def _getShowLabels(self):
		return (self.GetWindowStyle() & wx.SL_LABELS > 0)
			
	def _setShowLabels(self, value):
		self._delWindowStyleFlag(wx.SL_LABELS)
		if value:
			self._addWindowStyleFlag(wx.SL_LABELS)


	# Property definitions:
	Orientation = property(_getOrientation, _setOrientation, None, 
			"Specifies whether the Slider is displayed as Horizontal or Vertical.")

	Min = property(_getMin, _setMin, None, 
			"Specifies the minimum value for the Slider.")

	Max = property(_getMax, _setMax, None, 
			"Specifies the maximum value for the Slider.")

	ShowLabels = property(_getShowLabels, _setShowLabels, None, 
			"Specifies if the labels are shown on the slider.")


class _dSlider_test(dSlider):
	def initProperties(self):
		self.Size = (200, 40)
		self.Max = 95
		self.Min = 23
		self.Value = 75
		self.ShowLabels = True
		self.Orientation = "Horizontal"

if __name__ == "__main__":
	import test
	test.Test().runTest(_dSlider_test)
