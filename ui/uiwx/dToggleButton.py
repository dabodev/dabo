import wx, warnings
import dabo
import dControlMixin as cm
import dDataControlMixin as dcm
from dabo.dLocalize import _
import dEvents

class dToggleButton(wx.ToggleButton, dcm.dDataControlMixin, cm.dControlMixin):
	""" Allows the user to set an on/off condition by pressing a button.
	"""
	def __init__(self, parent, id=-1, name="dToggleButton", style=0, *args, **kwargs):

		self._baseClass = dToggleButton

		pre = wx.PreToggleButton()
		self._beforeInit(pre)                  # defined in dPemMixin
		pre.Create(parent, id, name, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		
		dcm.dDataControlMixin.__init__(self)
		cm.dControlMixin.__init__(self, name)
		self._afterInit()                      # defined in dPemMixin


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)
		dcm.dDataControlMixin.initEvents(self)

		# Respond to EVT_TOGGLEBUTTON and raise dEvents.Button:
		self.bindEvent(wx.EVT_TOGGLEBUTTON, self._onWxButton)
		
		# init the widget's specialized event(s):
		self.bindEvent(dEvents.Button, self.onButton)
		self.bindEvent(dEvents.Button, self._onButton)

	# Event callback methods (override in subclasses):
	def onButton(self, event):
		if self.debug:
			if self.Value:
				state = "down"
			else:
				state = "up"
			dabo.infoLog.write(_("onButton received by %s. State: %s") % (self.Name, state))
		event.Skip()

	# Private Event callback methods (do not override):
	def _onButton(self, event):
		self.raiseEvent(dEvents.ValueChanged)
		event.Skip()
		
	def _onWxButton(self, event):
		self.raiseEvent(dEvents.Button)
		event.Skip()
		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.


if __name__ == "__main__":
	import test
	test.Test().runTest(dToggleButton)
