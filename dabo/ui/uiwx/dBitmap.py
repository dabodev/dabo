# -*- coding: utf-8 -*-
import wx
import dabo

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
import dImageMixin as dim
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dIcons
from dabo.ui import makeDynamicProperty


class dBitmap(cm.dControlMixin, dim.dImageMixin, wx.StaticBitmap):
	"""Creates a simple bitmap control to display images on your forms."""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dBitmap
		preClass = wx.StaticBitmap
		picName = self._extractKey((kwargs, properties, attProperties), "Picture", "")
		
		dim.dImageMixin.__init__(self)
		cm.dControlMixin.__init__(self, preClass, parent, properties, attProperties, 
				*args, **kwargs)
		
		if picName:
			self.Picture = picName



class _dBitmap_test(dBitmap):
	def initProperties(self):
		self.Picture = "daboIcon016"
#		self.Size = (40,30)
	
if __name__ == "__main__":
	import test
	test.Test().runTest(_dBitmap_test)
