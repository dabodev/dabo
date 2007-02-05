import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dSlider(dcm.dDataControlMixin, wx.Slider):
	"""Creates a slider control, allowing editing integer values. Unlike dSpinner, 
	dSlider does not allow entering a value with the keyboard.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dSlider		
		style = self._extractKey((kwargs, properties, attProperties), "style")
		if style is None:
			kwargs["style"] = wx.SL_AUTOTICKS
		else:
			kwargs["style"] = style | wx.SL_AUTOTICKS		
		preClass = wx.PreSlider
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)

	
	def _initEvents(self):
		super(dSlider, self)._initEvents()
#		self.Bind(wx.EVT_SCROLL, self._onWxHit)
		self.Bind(wx.EVT_SCROLL_THUMBRELEASE, self._onWxHit)


	def _onWxHit(self, evt):
		self.flushValue()
		super(dSlider, self)._onWxHit(evt)

				
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getMax(self):
		return self.GetMax()

	def _setMax(self, val):
		if self._constructed():
			currmin = self.GetMin()
			currval = min(self.GetValue(), val)
			self.SetRange(currmin, val)
			self.SetValue(currval)
		else:
			self._properties["Max"] = val
		

	def _getMin(self):
		return self.GetMin()

	def _setMin(self, val):
		if self._constructed():
			currmax = self.GetMax()
			currval = max(self.GetValue(), val)
			self.SetRange(val, currmax)
			self.SetValue(currval)
		else:
			self._properties["Min"] = val
		

	def _getOrientation(self):
		if self.GetWindowStyle() & wx.SL_VERTICAL:
			return "Vertical"
		else:
			return "Horizontal"
			
	def _setOrientation(self, val):
		self._delWindowStyleFlag(wx.SL_HORIZONTAL)
		self._delWindowStyleFlag(wx.SL_VERTICAL)
		if val.lower()[:1] == "h":
			self._addWindowStyleFlag(wx.SL_HORIZONTAL)
		else:
			self._addWindowStyleFlag(wx.SL_VERTICAL)


	def _getShowLabels(self):
		return (self.GetWindowStyle() & wx.SL_LABELS > 0)
			
	def _setShowLabels(self, val):
		self._delWindowStyleFlag(wx.SL_LABELS)
		if val:
			self._addWindowStyleFlag(wx.SL_LABELS)


	# Property definitions:
	Max = property(_getMax, _setMax, None, 
			_("Specifies the maximum value for the Slider. Default=100  (int)"))

	Min = property(_getMin, _setMin, None, 
			_("Specifies the minimum value for the Slider. Default=0  (int)"))

	Orientation = property(_getOrientation, _setOrientation, None, 
			_("""Specifies whether the Slider is displayed as Horizontal or Vertical. Must be set
			when the object is created; setting it afterwards has no effect. Default='Horizontal'  (str)"""))

	ShowLabels = property(_getShowLabels, _setShowLabels, None, 
			_("""Specifies if the labels are shown on the slider. Must be set
			when the object is created; setting it afterwards has no effect. Default=True  (bool)"""))


	DynamicOrientation = makeDynamicProperty(Orientation)
	DynamicMax = makeDynamicProperty(Max)
	DynamicMin = makeDynamicProperty(Min)
	DynamicShowLabels = makeDynamicProperty(ShowLabels)


 
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
