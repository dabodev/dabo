import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm

class dBox(wx.StaticBox, cm.dControlMixin):
	""" Create a static (not data-aware) box.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dBox
		preClass = wx.PreStaticBox
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	
	def _initEvents(self):
		super(dBox, self)._initEvents()


class _dBox_test(dBox):
	def initProperties(self):
		self.Width = 100
		self.Height = 20

if __name__ == "__main__":
	import test
	test.Test().runTest(_dBox_test)
