import wx, warnings, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dToggleButton(wx.ToggleButton, dcm.dDataControlMixin):
	""" Allows the user to set an on/off condition by pressing a button.
	"""
	def __init__(self, parent, id=-1, name="dToggleButton", style=0, *args, **kwargs):

		self._baseClass = dToggleButton

		pre = wx.PreToggleButton()
		self._beforeInit(pre)
		pre.Create(parent, id, name=name, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		
		dcm.dDataControlMixin.__init__(self, name)
		self._afterInit()


	def initEvents(self):
		dToggleButton.doDefault()
		# Respond to EVT_TOGGLEBUTTON and raise dEvents.Button:
		self.Bind(wx.EVT_TOGGLEBUTTON, self._onWxHit)
		

	# Event callback methods (override in subclasses):
	def onHit(self, evt):
		if self.debug:
			if self.Value:
				state = "down"
			else:
				state = "up"
			dabo.infoLog.write(_("%s: onHit() called. State: %s") % (self.Name, state))

		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.


if __name__ == "__main__":
	import test
	test.Test().runTest(dToggleButton)
