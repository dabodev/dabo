# -*- coding: utf-8 -*-
import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm

class dBox(cm.dControlMixin, wx.StaticBox):
	"""Creates a box for visually grouping objects on your form."""
	## pkm: I'm not sure of the utility of this class, since you can draw
	##      borders around panels and direct draw on any object. Opinions?
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dBox
		preClass = wx.PreStaticBox
		cm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def _initEvents(self):
		super(dBox, self)._initEvents()


class _dBox_test(dBox):
	def initProperties(self):
		self.Width = 100
		self.Height = 20

if __name__ == "__main__":
	import test
	test.Test().runTest(_dBox_test)
