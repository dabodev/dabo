import wx, warnings
import dControlMixin as cm
from dabo.dLocalize import _

class dToggleButton(wx.ToggleButton, cm.dControlMixin):
	""" Allows the user to cause an action to occur by pushing a button.
	"""
	def __init__(self, parent, id=-1, name="dToggleButton", style=0, *args, **kwargs):

		self._baseClass = dToggleButton

		pre = wx.PreToggleButton()
		self._beforeInit(pre)                  # defined in dPemMixin
		pre.Create(parent, id, name, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		
		cm.dControlMixin.__init__(self, name)
		self._afterInit()                      # defined in dPemMixin


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)

		# init the widget's specialized event(s):
		wx.EVT_TOGGLEBUTTON(self, self.GetId(), self.OnToggleButton)

	# Event callback methods (override in subclasses):
	def OnToggleButton(self, event):
		event.Skip()


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.


if __name__ == "__main__":
	import test
	class c(dToggleButton):
		def OnToggleButton(self, event): 
			print "State:",
			if self.GetValue():
				print "down"
			else:
				print "up"

	test.Test().runTest(c)
