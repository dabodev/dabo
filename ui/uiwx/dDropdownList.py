import wx
import dControlMixin as cm
import dDataControlMixin as dcm

class dDropdownList(wx.Choice, dcm.dDataControlMixin, cm.dControlMixin):
	""" Allows editing integer values.
	"""
	def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, 
			choices=["Dabo", "Default"], name="dDropdownList", style=0, *args, **kwargs):

		self._baseClass = dDropdownList

		pre = wx.PreChoice()
		self._beforeInit(pre)                  # defined in dPemMixin
		style=style|pre.GetWindowStyle()
		pre.Create(parent, id, pos, size, choices, *args, **kwargs)

		self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name)
		dcm.dDataControlMixin.__init__(self)
		self._afterInit()                      # defined in dPemMixin


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)
		dcm.dDataControlMixin.initEvents(self)

		# init the widget's specialized event(s):
		wx.EVT_CHOICE(self, self.GetId(), self.OnChoice)

	# Event callback method(s) (override in subclasses):
	def OnChoice(self, event):
		self.raiseValueChanged()


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getValue(self):
		return self.GetStringSelection()
		
	def _setValue(self, value):
		self.SetStringSelection(value)
		self.raiseValueChanged()

	# Property definitions:
	Value = property(_getValue, _setValue, None,
			"Specifies the current state of the control (the value of the field). (varies)")

if __name__ == "__main__":
	import test
	class c(dDropdownList):
		def OnChoice(self, event): print "OnChoice!"
	test.Test().runTest(c)
