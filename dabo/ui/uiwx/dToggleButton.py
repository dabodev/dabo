import wx, warnings, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dToggleButton(wx.ToggleButton, dcm.dDataControlMixin):
	""" Allows the user to set an on/off condition by pressing a button.
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

	def initEvents(self):
		self.autoBindEvents()
		
	def onHit(self, evt):
		if self.Value:
			state = "down"
		else:
			state = "up"
		self.Caption = _("State: %s" % state)


if __name__ == "__main__":
	import test
	test.Test().runTest(_dToggleButton_test)
