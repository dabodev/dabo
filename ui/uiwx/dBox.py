import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm

class dBox(wx.StaticBox, cm.dControlMixin):
	""" Create a static (not data-aware) box.
	"""
	def __init__(self, parent, id=-1, label="", pos=(-1, -1), size=(-1, -1), style=0, *args, **kwargs):

		self._baseClass = dBox
		
		name, _explicitName = self._processName(kwargs, "dBox")
		
		pre = wx.PreStaticBox()
		self._beforeInit(pre)
		
		pre.Create(parent, id, label, pos, size, style=style | pre.GetWindowStyle(), *args, **kwargs)
		self.PostCreate(pre)
		
		cm.dControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self._afterInit()


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)

		# init the widget's specialized event(s):

	# property get/set functions


if __name__ == "__main__":
	import test
	test.Test().runTest(dBox)
