import wx, dabo
import os
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dControlMixin as dcm


class dImage(wx.StaticBitmap, dcm.dControlMixin):
	""" Create a simple bitmap to display images. 
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dImage
		preClass = wx.StaticBitmap

		self.__image = None
		bmp = wx.EmptyBitmap(1, 1)
		fName = self.extractKey(kwargs, "img")
		if fName is not None:
			if os.path.exists(fName):
				self._Image.LoadFile(fName)
				bmp = self._Image.ConvertToBitmap()

		dcm.dControlMixin.__init__(self, preClass, parent, properties, 
				bitmap=bmp, *args, **kwargs)		

	
	
	def _getImg(self):
		if self.__image is None:
			self.__image = wx.NullImage
		return self.__image

	_Image = property(_getImg, None, None, 
			_("Underlying image handler object  (wx.Image)") )
 
	
if __name__ == "__main__":
	import test
	
	class Img(dImage): pass
			
	test.Test().runTest(Img)
