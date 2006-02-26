import wx
import dabo

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dIcons
from dabo.ui import makeDynamicProperty


class dBitmap(wx.StaticBitmap, cm.dControlMixin):
	"""Creates a simple bitmap control to display images on your forms."""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dBitmap
		preClass = wx.StaticBitmap
		picName = self._extractKey((kwargs, properties), "Picture", "")
		
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		
		if picName:
			self.Picture = picName


	def _getBitmap(self):
		return self.GetBitmap()
		
	def _setBitmap(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				bmp = dabo.ui.dIcons.getIconBitmap(val)
			elif isinstance(val, wx.Bitmap):
				bmp = val
			elif not val:
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
			if isinstance(val, wx.Bitmap):
				bmp = val
			else:
				bmp = dabo.ui.strToBmp(val)
			self.SetBitmap(bmp)
		else:
			self._properties["Picture"] = val
	
	
	Bitmap = property(_getBitmap, _setBitmap, None,
		_("Use this to set the image.  (bitmap)") )
	DynamicBitmap = makeDynamicProperty(Bitmap)
	
	Picture = property(_getPicture, _setPicture, None,
		_("Specifies the image to be used for the bitmap.  (str)") )
	DynamicPicture = makeDynamicProperty(Picture)


class _dBitmap_test(dBitmap):
	def initProperties(self):
		self.Picture = "daboIcon016"
#		self.Size = (40,30)
	
if __name__ == "__main__":
	import test
	test.Test().runTest(_dBitmap_test)
