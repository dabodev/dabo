import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dDropdownList(wx.Choice, dcm.dDataControlMixin):
	""" Allows presenting a choice of items for the user to choose from.
	"""
	def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, 
			choices=["Dabo", "Default"], name="dDropdownList", style=0, *args, **kwargs):

		self._baseClass = dDropdownList

		pre = wx.PreChoice()
		self._beforeInit(pre)
		style=style|pre.GetWindowStyle()
		pre.Create(parent, id, pos, size, choices, name=name, *args, **kwargs)

		self.PostCreate(pre)

		dcm.dDataControlMixin.__init__(self, name)
		self._afterInit()


	def initEvents(self):
		#dDropdownList.doDefault()
		super(dDropdownList, self).initEvents()
		
		# catch the wx event and raise the dabo event:
		self.Bind(wx.EVT_CHOICE, self._onWxHit)
		

	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getValue(self):
		return self.GetStringSelection()
		
	def _setValue(self, value):
		self.SetStringSelection(value)

	# Property definitions:
	Value = property(_getValue, _setValue, None,
			"Specifies the current state of the control (the value of the field). (varies)")

if __name__ == "__main__":
	import test
	test.Test().runTest(dDropdownList)
