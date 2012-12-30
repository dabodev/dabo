# -*- coding: utf-8 -*-
import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dSlider(dcm.dDataControlMixin, wx.Slider):
	"""
	Creates a slider control, allowing editing integer values. Unlike dSpinner,
	dSlider does not allow entering a value with the keyboard.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dSlider
		self._continuous = False
		self._lastVal = None
		style = self._extractKey((kwargs, properties, attProperties), "style")
		if style is None:
			style = wx.SL_AUTOTICKS
		else:
			style = style | wx.SL_AUTOTICKS
		kwargs["style"] = style
		# These need to be added to the style kwarg in _initProperties
		self._tickPosition = None
		self._reversed = False

		preClass = wx.PreSlider
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def _initProperties(self):
		super(dSlider, self)._initProperties()
		style = self._preInitProperties["style"]
		if self._tickPosition:
			tickpos = self.TickPosition[0].upper()
			style = style | {"T": wx.SL_TOP, "B": wx.SL_BOTTOM, "L": wx.SL_LEFT, "R": wx.SL_RIGHT}[tickpos]
		if self._reversed:
			style = style | wx.SL_INVERSE
		self._preInitProperties["style"] = style


	def _initEvents(self):
		super(dSlider, self)._initEvents()
		self.Bind(wx.EVT_SCROLL, self._onWxHit)


	def _onWxHit(self, evt):
		newval = self.GetValue()
		changed = (newval != self._lastVal)
		self._lastVal = newval
		if (changed and self._continuous) or not dabo.ui.isMouseLeftDown():
			self.flushValue()
			super(dSlider, self)._onWxHit(evt)


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getContinuous(self):
		try:
			ret = self._continuous
		except AttributeError:
			ret = self._continuous = True
		return ret

	def _setContinuous(self, val):
		if self._constructed():
			self._continuous = val
		else:
			self._properties["Continuous"] = val


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
		tickpos = self._tickPosition
		isHoriz = (val.lower()[:1] == "h")
		if isHoriz and tickpos in ("Left", "Right"):
			dabo.log.error(_("Cannot set the slider to Horizontal when TickPosition is %s.") % tickpos)
		elif not isHoriz and tickpos in ("Top", "Bottom"):
			dabo.log.error(_("Cannot set the slider to Vertical when TickPosition is %s.") % tickpos)
		self._delWindowStyleFlag(wx.SL_HORIZONTAL)
		self._delWindowStyleFlag(wx.SL_VERTICAL)
		if isHoriz:
			self._addWindowStyleFlag(wx.SL_HORIZONTAL)
		else:
			self._addWindowStyleFlag(wx.SL_VERTICAL)


	def _getReversed(self):
		return self._reversed

	def _setReversed(self, val):
		# Ignore this once constructed
		if not self._constructed():
			self._reversed = val


	def _getShowLabels(self):
		return (self.GetWindowStyle() & wx.SL_LABELS > 0)

	def _setShowLabels(self, val):
		self._delWindowStyleFlag(wx.SL_LABELS)
		if val:
			self._addWindowStyleFlag(wx.SL_LABELS)


	def _getTickPosition(self):
		try:
			tp = self._tickPosition[0].upper()
		except TypeError:
			# No tick position set; return Bottom
			return "Bottom"
		return {"T": "Top", "B": "Bottom", "L": "Left", "R": "Right"}[tp]

	def _setTickPosition(self, val):
		# Ignore this once constructed
		if not self._constructed():
			self._tickPosition = val


	# Property definitions:
	Continuous = property(_getContinuous, _setContinuous, None,
			_("""When True, the Hit event is raised as the slider moves. When False (default),
			it is only raised when the thumb control is released.  (bool)"""))

	Max = property(_getMax, _setMax, None,
			_("Specifies the maximum value for the Slider. Default=100  (int)"))

	Min = property(_getMin, _setMin, None,
			_("Specifies the minimum value for the Slider. Default=0  (int)"))

	Orientation = property(_getOrientation, _setOrientation, None,
			_("""Specifies whether the Slider is displayed as Horizontal or Vertical.
			Default='Horizontal'  (str)"""))

	Reversed = property(_getReversed, _setReversed, None,
			_("""When True, the position of the Min and Max values are reversed. Must be set
			when the object is created; setting it afterwards has no effect. Default=False  (bool)"""))

	ShowLabels = property(_getShowLabels, _setShowLabels, None,
			_("""Specifies if the labels are shown on the slider. Must be set when the object is
			created; setting it afterwards has no effect. Default=True  (bool)"""))

	TickPosition = property(_getTickPosition, _setTickPosition, None,
			_("""Position of the tick marks; must be one of Top, Bottom (default), Left or Right.
			Not fully supported on all platforms. Must be set during object creation; has no
			effect once created.  (str)"""))

	DynamicOrientation = makeDynamicProperty(Orientation)
	DynamicMax = makeDynamicProperty(Max)
	DynamicMin = makeDynamicProperty(Min)
	DynamicShowLabels = makeDynamicProperty(ShowLabels)



class _dSlider_test(dSlider):
	def initProperties(self):
		self.Size = (300, 300)
		self.Max = 95
		self.Min = 23
		self.Value = 75
		self.ShowLabels = True
		# Try changing these to see their effects
# 		self.Reversed = True
#  		self.TickPosition = "Left"

	def onHit(self, evt):
		print "Hit! Value =", self.Value


if __name__ == "__main__":
	import test
	test.Test().runTest(_dSlider_test)
