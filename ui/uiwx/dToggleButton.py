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
		#dToggleButton.doDefault()
		super(dToggleButton, self).initEvents()
		# Respond to EVT_TOGGLEBUTTON and raise dEvents.Button:
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
