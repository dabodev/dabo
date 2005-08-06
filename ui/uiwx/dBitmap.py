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
		picName = self.extractKey(kwargs, "Picture", "")
		
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		
		if picName:
			self.Picture = picName


	def _getBitmap(self):
		return self.GetBitmap()
	def _setBitmap(self, bmp):
		if self._constructed():
			if isinstance(bmp, basestring):
				bmp = dabo.ui.dIcons.getIconBitmap(bmp)
			elif not bmp:
				bmp = wx.EmptyBitmap(1,1)
				self.SetPosition((-100,-100))
			self.SetBitmap(bmp)
		else:
			self._properties["Bitmap"] = bmp

	def _getPicture(self):
		return self.GetBitmap()
	def _setPicture(self, val):
		self._picture = val
		if self._constructed():
			bmp = dabo.ui.strToBmp(val)
			self.SetBitmap(bmp)
		else:
			self._properties["Picture"] = val
	
	
	Bitmap = property(_getBitmap, _setBitmap, None,
		_("Use this to set the image.  (bitmap)") )
	
	Picture = property(_getPicture, _setPicture, None,
		_("Specifies the image to be used for the bitmap.  (str)") )



	
	
if __name__ == "__main__":
	import test
	
	class B(dBitmap):
		def initProperties(self):
			self.Picture = "daboIcon096"
			
	test.Test().runTest(B)
