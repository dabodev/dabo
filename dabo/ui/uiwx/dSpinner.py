# -*- coding: utf-8 -*-
import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dSpinner(dcm.dDataControlMixin, wx.SpinCtrl):
	"""Creates a spinner, which is a textbox with clickable up/down arrows.

	Use this to edit integer values. You can set the maximum and minimum
	allowable values, as well as the increment when the user clicks the 
	arrows.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dSpinner
		preClass = wx.PreSpinCtrl
		if not "value" in kwargs:
			# This has to be initialized to a string value, for some odd reason
			kwargs["value"] = "0"			
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, attProperties, 
				*args, **kwargs)

	
	def _initEvents(self):
		super(dSpinner, self)._initEvents()
		self.Bind(wx.EVT_SPINCTRL, self._onWxHit)
		

	def _preInitUI(self, kwargs):
		# Force the use of arrow keys
		kwargs["style"] = kwargs["style"] | wx.SP_ARROW_KEYS
		return kwargs

	
	def _getInitPropertiesList(self):
		additional = ["SpinnerWrap",]
		original = list(super(dSpinner, self)._getInitPropertiesList())
		return tuple(original + additional)
		
	
	def _onWxHit(self, evt):
		# Flush the data on each hit, not just when focus is lost.
		self.flushValue()
		super(dSpinner, self)._onWxHit(evt)


	def getBlankValue(self):
		return 0

		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getChildren(self):
		# The native wx control will return the items that make up this composite
		# control, which our user doesn't want.
		return []
	
	
	def _getMax(self):
		return self.GetMax()

	def _setMax(self, value):
		if self._constructed():
			rangeLow = self.GetMin()
			rangeHigh = int(value)
			self.SetRange(rangeLow, rangeHigh)
		else:
			self._properties["Max"] = value


	def _getMin(self):
		return self.GetMin()

	def _setMin(self, value):
		if self._constructed():
			rangeLow = int(value)
			rangeHigh = self.Max
			self.SetRange(rangeLow, rangeHigh)
		else:
			self._properties["Min"] = value

	def _getSpinnerWrap(self):
		return self._hasWindowStyleFlag(wx.SP_WRAP)

	def _setSpinnerWrap(self, value):
		self._delWindowStyleFlag(wx.SP_WRAP)
		if value:
			self._addWindowStyleFlag(wx.SP_WRAP)


	# Property definitions:
	Children = property(_getChildren, None, None, 
			_("""Returns a list of object references to the children of 
			this object. Only applies to containers. Children will be None for 
			non-containers.  (list or None)"""))
	
	Max = property(_getMax, _setMax, None, 
			_("Specifies the highest possible value for the spinner. (int)"))

	Min = property(_getMin, _setMin, None, 
			_("Specifies the lowest possible value for the spinner. (int)"))

	SpinnerWrap = property(_getSpinnerWrap, _setSpinnerWrap, None,
			_("Specifies whether the spinner value wraps at the high/low value. (bool)"))


	DynamicMax = makeDynamicProperty(Max)
	DynamicMin = makeDynamicProperty(Min)
	DynamicSpinnerWrap = makeDynamicProperty(SpinnerWrap)



class _dSpinner_test(dSpinner):
	def initProperties(self):
		self.Max = 12
		self.Min = 5
		self.SpinnerWrap = True
		self.DataSource="form"
		self.DataField="Caption"

	def onHit(self, evt):
		print "HIT!", self.Value
		

if __name__ == "__main__":
	import test
	test.Test().runTest(_dSpinner_test)
