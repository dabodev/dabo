import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm

class dBox(wx.StaticBox, cm.dControlMixin):
	""" Create a static (not data-aware) box.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dBox
		preClass = wx.PreStaticBox
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	
	def _initEvents(self):
		super(dBox, self)._initEvents()


if __name__ == "__main__":
	import test
	test.Test().runTest(dBox)
