import wx, warnings, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dToggleButton(wx.ToggleButton, dcm.dDataControlMixin):
	"""Creates a button that toggles on and off, for editing boolean values.

	This is functionally equivilent to a dCheckbox, but visually much different.
	Also, it implies that pushing it will cause some sort of immediate action to
	take place, like you get with a normal button.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dToggleButton
		preClass = wx.PreToggleButton
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	
	def _initEvents(self):
		super(dToggleButton, self)._initEvents()
		self.Bind(wx.EVT_TOGGLEBUTTON, self._onWxHit)
		

class _dToggleButton_test(dToggleButton):
	def afterInit(self):
		self.Caption = "Toggle me!"
		self.Size = (100, 31)

	def onHit(self, evt):
		if self.Value:
			state = "down"
		else:
			state = "up"
		self.Caption = _("State: %s" % state)


if __name__ == "__main__":
	import test
	test.Test().runTest(_dToggleButton_test)
