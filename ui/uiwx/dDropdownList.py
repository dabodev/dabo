import wx, dabo
import dControlMixin as cm
import dDataControlMixin as dcm
import dEvents
from dabo.dLocalize import _

class dDropdownList(wx.Choice, dcm.dDataControlMixin, cm.dControlMixin):
	""" Allows presenting a choice of items for the user to choose from.
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
		self.bindEvent(dEvents.Choice, self._onChoice)
		self.bindEvent(dEvents.Choice, self.onChoice)

	# Event callback method(s) (override in subclasses):
	def onChoice(self, event):
		if self.debug:
			dabo.infoLog.write(_("onChoice received by %s") % self.Name)
		event.Skip()
			
	# Private callback methods (do not override):
	def _onChoice(self, event):
		self.raiseEvent(dEvents.ValueChanged)
		event.Skip()


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getValue(self):
		return self.GetStringSelection()
		
	def _setValue(self, value):
		self.SetStringSelection(value)
		self.raiseEvent(dEvents.ValueChanged)

	# Property definitions:
	Value = property(_getValue, _setValue, None,
			"Specifies the current state of the control (the value of the field). (varies)")

if __name__ == "__main__":
	import test
	test.Test().runTest(dDropdownList)
