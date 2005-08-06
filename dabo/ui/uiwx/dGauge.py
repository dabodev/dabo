import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm

class dGauge(wx.Gauge, cm.dControlMixin):
	""" Allows the creation of progress bars.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dGauge
		preClass = wx.PreGauge
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _initEvents(self):
		super(dGauge, self)._initEvents()

		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getRange(self):
		return self.GetRange()
			
	def _setRange(self, value):
		if self._constructed():
			self.SetRange(value)
		else:
			self._properties["Range"] = value
		
		
	def _getOrientation(self):
		if self.IsVertical():
			return "Vertical"
		else:
			return "Horizontal"
			
	def _setOrientation(self, value):
		self.delWindowStyleFlag(wx.GA_HORIZONTAL)
		self.delWindowStyleFlag(wx.GA_VERTICAL)
		if value.lower()[:1] == "h":
			self.addWindowStyleFlag(wx.GA_HORIZONTAL)
		else:
			self.addWindowStyleFlag(wx.GA_VERTICAL)

	def _getOrientationEditorInfo(self):
		return {"editor": "list", "values": ["Horizontal", "Vertical"]}

	def _getValue(self):
		return self.GetValue()
		
	def _setValue(self, value):
		if self._constructed():
			self.SetValue(value)
		else:
			self._properties["Value"] = value
		
	# Property definitions:
	Orientation = property(_getOrientation, _setOrientation, None, 
			"Specifies whether the gauge is displayed as Horizontal or Vertical.")
	Range = property(_getRange, _setRange, None, 
			"Specifies the maximum value for the gauge.")
	Value = property(_getValue, _setValue, None, 
			"Specifies the state of the gauge, relative to max value.")


if __name__ == "__main__":
	import test
	class C(dGauge):
		def afterInit(self):
			C.doDefault()
			self._timer = dabo.ui.dTimer(self.GetParent())
			self._timer.bindEvent(dabo.dEvents.Hit, self.onTimer)
			self.setup()
			
		def setup(self):
			self.Range = 100
			self.Value = 0
			self._timer.Interval = 8
			self._timer.start()
			
		def onTimer(self, evt):
			if self.Value < self.Range:
				self.Value += 1
			else:
				self._timer.stop()
				self.setup()				
	
	test.Test().runTest(C)
