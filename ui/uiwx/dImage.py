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

		self._picture = ""
		self._bmp = None
		self._scaleMode = "Proportional"
		self._imgProp = 1.0
		self.__image = None
		bmp = wx.EmptyBitmap(1, 1)
		fName = self.extractKey(kwargs, "Picture")

		dcm.dControlMixin.__init__(self, preClass, parent, properties, 
				bitmap=bmp, *args, **kwargs)
		
		# Display the picture, if any
		if fName is not None:
			if os.path.exists(fName):
				self.Picture = fName
				bmp = self.Bitmap
	
	
	def _initEvents(self):
		super(dImage, self)._initEvents()
		self.bindEvent(dEvents.Resize, self.onResize)
	
	
	def onResize(self, evt):
		self._showPic()


	def _showPic(self):
		"""Displays the picture according to the ScaleMode and image size."""
		if not self._Image.Ok():
			# No image to display
				return
		w, h = origW, origH = self.Width, self.Height
		if w == h == 1:
			# Initial empty bitmap, let the image determine the size
			w = origW = self._Image.GetWidth()
			h = origH = self._Image.GetHeight()
		w, h = float(w), float(h)
		
		szProp = w/h
		imgProp = self._imgProp
		sm = self.ScaleMode[0].lower()
		if sm == "c":
			# Clip; Don't change anything
			img = self._Image
		elif sm == "p":
			# Proportional; find the largest dimension that fits.
			if imgProp > szProp:
				# Image is wider than control, so limit it to the control width
				imgW = w
				imgH = w / imgProp
			else:
				# Use the height as the limiting size
				imgH = h
				imgW = h * imgProp
			img = self._Image.Scale(imgW, imgH)
		else:
			# Stretch; just use the control size
			img = self._Image.Scale(w, h)
		
		# We have the adjusted image; now generate the bitmap			
		self.Bitmap = img.ConvertToBitmap()
		try:
			self.SetBitmap(self.Bitmap)
		except TypeError, e: pass
		self.SetSize((origW, origH))


	# Property definitions
	def _getBmp(self):
		if self._bmp is None:
			self._bmp = wx.EmptyBitmap(1, 1)
		return self._bmp
	def _setBmp(self, val):
		self._bmp = val
		
	def _getPic(self):
		return self._picture
	def _setPic(self, val):
		if not os.path.exists(val):
			return
		self._picture = val
		self._Image.LoadFile(val)
		self._imgProp = float(self._Image.GetWidth()) / float(self._Image.GetHeight())
		self._showPic()
	
	def _getScaleMode(self):
		return self._scaleMode
	def _setScaleMode(self, val):
		"""Only the first letter is significant. """
		initial = val[0].lower()
		modes = {"c" : "Clip", "p" : "Proportional", "s" : "Stretch"}
		try:
			self._scaleMode = modes[initial]
			self._showPic()
		except KeyError:
			dabo.errorLog.write(_("ScaleMode must be either 'Clip', 'Proportional' or 'Stretch'.") )


	def _getImg(self):
		if self.__image is None:
			self.__image = wx.NullImage
		return self.__image

	
	Bitmap = property(_getBmp, _setBmp, None,
			_("The bitmap representation of the displayed image.  (wx.Bitmap)") )

	Picture = property(_getPic, _setPic, None,
			_("The file used as the source for the displayed image.  (str)") )
			
	ScaleMode = property(_getScaleMode, _setScaleMode, None,
			_("""Determines how the image responds to sizing. Can be one
			of the following:
				Clip: Only that part of the image that fits in the control's size is displayed
				Proportional: the image resizes to fit the control without changing
					its original proportions. (default)
				Stretch: the image resizes to the Height/Width of the control.
			""") )

	_Image = property(_getImg, None, None, 
			_("Underlying image handler object  (wx.Image)") )
 
	
if __name__ == "__main__":
	import test
	
	class Img(dImage): pass
			
	test.Test().runTest(Img)
