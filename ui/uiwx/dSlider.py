import wx, dabo
import dControlMixin as cm
import dDataControlMixin as dcm
import dEvents
from dabo.dLocalize import _

class dSlider(wx.Slider, dcm.dDataControlMixin, cm.dControlMixin):
	""" Allows editing integer values with a slider control.
	
	Slider does not allow entering a value with the keyboard.
	"""
	def __init__(self, parent, id=-1, name="dSlider", style=0, *args, **kwargs):

		self._baseClass = dSlider

		pre = wx.PreSlider()
		self._beforeInit(pre)                  # defined in dPemMixin
		
		pre.Create(parent, id, 50, 0, 100, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name)
		self._afterInit()                      # defined in dPemMixin


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)
		self.bindEvent(dEvents.Scroll, self.onScroll)
		self.bindEvent(dEvents.Scroll, self._onScroll)
		
		
	def onScroll(self, evt):
		if self.debug:
			dabo.infoLog.write("onScroll received by %s" % self.Name)
		evt.Skip()
		
	def _onScroll(self, evt):
		self.raiseEvent(dEvents.ValueChanged)
		evt.Skip()

	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getMin(self):
		return self.GetMin()
	def _setMin(self, value):
		self.SetMin(value)
		
	def _getMax(self):
		return self.GetMax()
	def _setMax(self, value):
		self.SetMax(value)
		
	def _getOrientation(self):
		if self.GetWindowStyle() & wx.SL_VERTICAL:
			return "Vertical"
		else:
			return "Horizontal"
			
	def _setOrientation(self, value):
		self.delWindowStyleFlag(wx.SL_HORIZONTAL)
		self.delWindowStyleFlag(wx.SL_VERTICAL)
		if value.lower()[:1] == "h":
			self.addWindowStyleFlag(wx.SL_HORIZONTAL)
		else:
			self.addWindowStyleFlag(wx.SL_VERTICAL)

	def _getOrientationEditorInfo(self):
		return {"editor": "list", "values": ["Horizontal", "Vertical"]}
	
	def _getLineSize(self):
		return self.GetLineSize()
	def _setLineSize(self, value):
		return self.SetLineSize(value)

	def _getValue(self):
		return self.GetValue()
	def _setValue(self, value):
		self.SetValue(int(value))
		

	def _getShowLabels(self):
		return (self.GetWindowStyle() & wx.SL_LABELS > 0)
			
	def _setShowLabels(self, value):
		self.delWindowStyleFlag(wx.SL_LABELS)
		if value:
			self.addWindowStyleFlag(wx.SL_LABELS)



	# Property definitions:
	Orientation = property(_getOrientation, _setOrientation, None, 
			"Specifies whether the Slider is displayed as Horizontal or Vertical.")
	Min = property(_getMin, _setMin, None, 
			"Specifies the minimum value for the Slider.")
	Max = property(_getMax, _setMax, None, 
			"Specifies the maximum value for the Slider.")
	ShowLabels = property(_getShowLabels, _setShowLabels, None, 
			"Specifies if the labels are shown on the slider.")
	Value = property(_getValue, _setValue, None, 
			"Specifies the state of the Slider, relative to max value.")


if __name__ == "__main__":
	import test
	class c(dSlider):
		def afterInit(self):
			self.Value = 75
			self.ShowLabels = True
			self.Orientation = "Vertical"
	test.Test().runTest(c)
