import wx, warnings, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dToggleButton(wx.ToggleButton, dcm.dDataControlMixin):
	""" Allows the user to set an on/off condition by pressing a button.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dToggleButton
		preClass = wx.PreToggleButton
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	
	def _initEvents(self):
		super(dToggleButton, self)._initEvents()
		self.Bind(wx.EVT_TOGGLEBUTTON, self._onWxHit)
		


if __name__ == "__main__":
	import test
	
	class T(dToggleButton):
		def initEvents(self):
			T.doDefault()
			self.debug = True
			self.bindEvent(dEvents.Hit, self.onHit)
			
		def onHit(self, evt):
			if self.Value:
				state = "down"
			else:
				state = "up"
			dabo.infoLog.write(_("%s: onHit() called. State: %s") % (self.Name, state))
	
	test.Test().runTest(T)
