import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dIcons

class dBitmap(wx.StaticBitmap, cm.dControlMixin):
	""" Create a simple bitmap to display images. 
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dBitmap
		preClass = wx.StaticBitmap
		bmpName = self.extractKey(kwargs, "bitmap")
		if bmpName is None:
			bmpName = "empty"
		bmp = dabo.ui.dIcons.getIconBitmap(bmpName)
		kwargs["bitmap"] = bmp

		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _getBitmap(self):
		return self.GetBitmap()
	def _setBitmap(self, bmp):
		if self._constructed():
			if type(bmp) == str:
				bmp = dabo.ui.dIcons.getIconBitmap(bmp)
			elif not bmp:
				bmp = wx.EmptyBitmap(1,1)
				self.SetPosition((-100,-100))
			self.SetBitmap(bmp)
		else:
			self._properties["Bitmap"] = bmp

	Bitmap = property(_getBitmap, _setBitmap, None,
		_("Use this to set the image.  (bitmap)") )
	
	
if __name__ == "__main__":
	import test
	
	class B(dBitmap):
		def initProperties(self):
			self.Bitmap = "daboIcon096"
			
	test.Test().runTest(B)
