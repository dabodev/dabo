import wx
import dControlMixin as cm
import dDataControlMixin as dcm

class dGauge(wx.Gauge, dcm.dDataControlMixin, cm.dControlMixin):
	""" Allows editing integer values.
	"""
	def __init__(self, parent, id=-1, name="dGauge", style=0, *args, **kwargs):

		self._baseClass = dGauge
		self._range = 100

		pre = wx.PreGauge()
		self.beforeInit(pre)                  # defined in dPemMixin
		
		print self._range
		
		pre.Create(parent, id, self._range, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name)
		dcm.dDataControlMixin.__init__(self)
		self.afterInit()                      # defined in dPemMixin


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)
		dcm.dDataControlMixin.initEvents(self)


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getRange(self):
		return self._range
	def _setRange(self, value):
		self._range = value
		
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


	# Property definitions:
	Orientation = property(_getOrientation, _setOrientation, None, 
			"Specifies the gauge is displayed as Horizontal or Vertical")
	Range = property(_getRange, _setRange, None, 
			"Maximum value for the gauge")


if __name__ == "__main__":
	import test
	class c(dGauge):
		def afterInit(self):
			self.Value = 75
	test.Test().runTest(c)
