# -*- coding: utf-8 -*-
import os
import tempfile
import imghdr
import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.lib import utils

#import dControlMixin as dcm
from dDataControlMixin import dDataControlMixin as dcm
import dImageMixin as dim
from dabo.ui import makeDynamicProperty


class dImage(dcm, dim.dImageMixin, wx.StaticBitmap):
	""" Create a simple bitmap to display images."""
	def __init__(self, parent, properties=None, attProperties=None, 
			*args, **kwargs):
		self._baseClass = dImage
		preClass = wx.StaticBitmap

		self._scaleMode = "Proportional"
		self._imgProp = 1.0
		self._rotation = 0
		self.__image = None
		self._inShowPic = False
		self._inReload = False
		self.__val = None
		self.__imageData = None
		bmp = wx.EmptyBitmap(1, 1)
		picName = self._extractKey((kwargs, properties, attProperties), "Picture", "")
		self._pictureIndex = self._extractKey((kwargs, properties, attProperties), "PictureIndex", -1)
	
		dim.dImageMixin.__init__(self)
		dcm.__init__(self, preClass, parent, properties, attProperties, 
				bitmap=bmp, *args, **kwargs)
		
		# Display the picture, if any. This will also initialize the 
		# self._picture attribute
		self.Picture = picName
	
	
	def _initEvents(self):
		super(dImage, self)._initEvents()
		self.bindEvent(dEvents.Resize, self._onResize)
	
	
	def _onResize(self, evt):
		if not self._inShowPic:
			self._showPic()
		
	
	def update(self):
		dabo.ui.callAfterInterval(100, super(dImage, self).update)
	
	
	def rotateCounterClockwise(self):
		self._rotation -= 1
		if self._rotation == -4:
			self._rotation = 0
		self._showPic()
		
		
	def rotateClockwise(self):
		self._rotation += 1
		if self._rotation == 4:
			self._rotation = 0
		self._showPic()
	
	
	def getImgType(self):
		data = self.__imageData
		ret = (None, None)
		if data:
			ret = None
			fname = self.Application.getTempFile(ext="")
			open(fname, "wb").write(self.__imageData)
			aux = wx.NullImage
			hnds = aux.GetHandlers()
			for hnd in hnds:
				aux.RemoveHandler(hnd.GetName())
			for hnd in hnds:
				try:
					if hnd.LoadFile(fname):
						ret = (hnd.GetName(), hnd.GetExtension())
						break
				except StandardError, e:
					print "ERROR", e
		return ret
	
	
	def getOriginalImgSize(self):
		"""Since the image can be scaled, this returns the size of
		the unscaled image.
		"""
		img = self._Image
		return (img.GetWidth(), img.GetHeight())


	def _showPic(self):
		"""Displays the picture according to the ScaleMode and image size."""
		if self._inShowPic:
			return
		if not self._Image.Ok():
			# No image to display
			self.Bitmap = wx.EmptyBitmap(1, 1)
			self.Freeze()
			self.SetBitmap(self.Bitmap)
			self.Thaw()
			return

		self._inShowPic = True
		img = self._Image.Copy()
		switchProportions = False
		if self._rotation:
			cw = (self._rotation > 0)
			absRotate = abs(self._rotation)
			switchProportions = (absRotate % 2 == 1)
			for xx in range(absRotate):
				img = img.Rotate90(cw)
			
		w, h = origW, origH = self.Width, self.Height
		if w == h == 1:
			# Initial empty bitmap, let the image determine the size
			w = origW = img.GetWidth()
			h = origH = img.GetHeight()
		w, h = float(w), float(h)
		
		if h == 0:
			szProp = 1
		else:
			szProp = w/h
		imgProp = self._imgProp
		
		if switchProportions:
			# The image has been rotated.
			imgProp = 1/imgProp
			
		sm = self.ScaleMode[0].lower()
		
		if self._Image.GetWidth() ==  self._Image.GetHeight() == 1:
			# Empty bitmap; no need to scale.
			img = img
		elif sm == "c":
			# Clip; Don't change anything
			img = img
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
			img = img.Scale(imgW, imgH)
		else:
			# Stretch; just use the control size
			img = img.Scale(w, h)
		
		# We have the adjusted image; now generate the bitmap
		self.Bitmap = img.ConvertToBitmap()
		self._bitmapHeight = self.Bitmap.GetHeight()
		self._bitmapWidth = self.Bitmap.GetWidth()
		
		self.Freeze()
		try:
			self.SetBitmap(self.Bitmap)
		except TypeError, e: pass
		self.Thaw()
		self.SetSize((origW, origH))
		self._inShowPic = False
		

	# Property definitions
	def _getFrameCount(self):
		typ = imghdr.what(file(self.Picture))
		if typ in ("gif", ):
			anim = wx.animate.Animation(self.Picture)
			cnt = anim.GetFrameCount()
		else:
			cnt = self.__image.GetImageCount(self.Picture)
		return cnt


	def _getPic(self):
		return self._picture
		
	def _setPic(self, val):
		if isinstance(val, wx.Image):
			# An image stored as a stream is being used
			self.__image = self.__val = val
			self._picture = "(stream)"
		elif isinstance(val, wx.Bitmap):
			# a raw bitmap is being supplied
			self._bmp = val
			self.__image = self.__val = val.ConvertToImage()
			self._picture = "(stream)"
		else:
			pathExists = os.path.exists(val)
			if not val:
				# Empty string passed; clear any current image
				self._picture = ""
				self._rotation = 0
				self._bmp = wx.EmptyBitmap(1, 1, 1)
				self.__image = self.__val = wx.EmptyImage(1, 1)		# self._bmp.ConvertToImage()
				self._showPic()
				return
			elif not pathExists:
				origVal = val
				val = dabo.ui.getImagePath(val)
				if val is None or not os.path.exists(val):
					# This will raise an IOError if it fails
					val = utils.resolvePathAndUpdate(origVal)
				if val is None or not os.path.exists(val):
					# Bad image reference
					raise IOError("No file named '%s' exists." % origVal)
			self._picture = val
			self._rotation = 0
			idx = self.PictureIndex
			if idx != -1:
				# The image count is 1-based.
				maxIdx = self.FrameCount - 1
				if idx > maxIdx:
					dabo.errorLog.write(_("Attempt to set PictureIndex (%(idx)s)to a value greater than the maximum index available (%(maxIdx)s).") % locals())
					idx = self.PictureIndex = maxIdx
			try:
				self._Image.LoadFile(val, index=idx)
			except IndexError:
				# Note: when I try to load an invalid index, I get a segfault, so I don't know
				# how useful this is.
				self._Image.LoadFile(val, index=-1)
		if self._Image.Ok():
			self._imgProp = float(self._Image.GetWidth()) / float(self._Image.GetHeight())
		else:
			self._imgProp = 1.0
		self._showPic()


	def _getPictureIndex(self):
		return self._pictureIndex

	def _setPictureIndex(self, val):
		if self._constructed():
			self._pictureIndex = val
			if not self._inReload:
				# Re-load the image
				self._inReload = True
				self.Picture = self._picture
				self._inReload = False
		else:
			self._properties["PictureIndex"] = val


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


	def _getValue(self):
		if self._Image.IsOk():
			return self._Image.GetData()
		else:
			return None

	def _setValue(self, val):
		if self._constructed():
			if self.__val == val:
				return
			self.__val = val
			try:
				isFile = os.path.exists(val)
			except TypeError:
				isFile = False
			if not isFile:
				# Probably an image stream
				try:
					img = dabo.ui.imageFromData(val)
				except TypeError:
					# No dice, so just bail
					img = wx.EmptyImage(1, 1)
				self._setPic(img)
			else:
				self._setPic(val)
			if ((type(self.__imageData) != type(val)) or (self.__imageData != val)):
				tfname = self.Application.getTempFile(ext="")
				try:
					self.__image.SaveFile(tfname, wx.BITMAP_TYPE_BMP)
					self.__imageData = open(tfname, "rb").read()
				except StandardError,e:
					self.__imageData = u""
				self._afterValueChanged()
			self.flushValue()
		else:
			self._properties["Value"] = val


	def _getImg(self):
		if self.__image is None:
			self.__image = wx.NullImage.Copy()
		return self.__image

	
	FrameCount = property(_getFrameCount, None, None,
			_("Number of frames in the current image. Will be 1 for most images, but can be greater for animated GIFs, ICOs and some TIFF files. (read-only) (int)"))
	
	Picture = property(_getPic, _setPic, None,
			_("The file used as the source for the displayed image.  (str)") )

	PictureIndex = property(_getPictureIndex, _setPictureIndex, None,
			_("""When displaying images from files that can contain multiple 
			images, such as GIF, TIFF and ICO, this determines which image 
			is used. Default=-1, which displays the first image for GIF and TIFF, 
			and the main image for ICO.  (int)"""))
	
	ScaleMode = property(_getScaleMode, _setScaleMode, None,
			_("""Determines how the image responds to sizing. Can be one
			of the following:
				Clip: Only that part of the image that fits in the control's size is displayed
				Proportional: the image resizes to fit the control without changing
					its original proportions. (default)
				Stretch: the image resizes to the Height/Width of the control.
			""") )
	
	Value = property(_getValue, _setValue, None,
			_("Image content for this control  (binary img data)"))	

	_Image = property(_getImg, None, None, 
			_("Underlying image handler object  (wx.Image)") )


	DynamicPicture = makeDynamicProperty(Picture)
	DynamicScaleMode = makeDynamicProperty(ScaleMode)

	
if __name__ == "__main__":
	class ImgForm(dabo.ui.dForm):
		def afterInit(self):
			self.Caption = "dImage Demonstration"
			self.mainPanel = mp = dabo.ui.dPanel(self)
			self.Sizer.append1x(mp)
			sz = dabo.ui.dSizer("v")
			mp.Sizer = sz
			# Create a panel with horiz. and vert.  sliders
			self.imgPanel = dabo.ui.dPanel(mp)
			self.VSlider = dabo.ui.dSlider(mp, Orientation="V", Min=1, Max=100,
				Value=100, OnHit=self.onSlider)
			self.HSlider = dabo.ui.dSlider(mp, Orientation="H", Min=1, Max=100,
				Value=100, OnHit=self.onSlider)
			
			psz = self.imgPanel.Sizer = dabo.ui.dSizer("V")
			hsz = dabo.ui.dSizer("H")
			hsz.append1x(self.imgPanel)
			hsz.appendSpacer(10)
			hsz.append(self.VSlider, 0, "x")
			sz.DefaultBorder = 25
			sz.DefaultBorderLeft = sz.DefaultBorderRight = True
			sz.appendSpacer(25)
			sz.append(hsz, 1, "x")
			sz.appendSpacer(10)
			sz.append(self.HSlider, 0, "x")
			sz.appendSpacer(10)

			# Create the image control
			self.img = dImage(self.imgPanel)
			
			hsz = dabo.ui.dSizer("H")
			hsz.DefaultSpacing = 10
			dabo.ui.dBitmapButton(mp, RegID="btnRotateCW",
					Picture="rotateCW", OnHit=self.rotateCW)
			dabo.ui.dBitmapButton(mp, RegID="btnRotateCCW",
					Picture="rotateCCW", OnHit=self.rotateCCW)
			hsz.append(self.btnRotateCW)
			hsz.append(self.btnRotateCCW)			
			self.ddScale = dabo.ui.dDropdownList(mp, 
					Choices=["Proportional", "Stretch", "Clip"],
					DataSource = "self.Form.img",
					DataField = "ScaleMode")
			self.ddScale.PositionValue = 0
			btn = dabo.ui.dButton(mp, Caption="Load Image", 
					OnHit=self.onLoadImage)
			btnOK = dabo.ui.dButton(mp, Caption="Done", OnHit=self.close)
			hsz.append(self.ddScale, 0, "x")
			hsz.append(btn, 0, "x")
			hsz.append(btnOK, 0, "x")
			sz.append(hsz, 0, alignment="right")
			sz.appendSpacer(25)
			
			# Set the idle update flage
			self.needUpdate = False


		def rotateCW(self, evt):
			self.img.rotateClockwise()


		def rotateCCW(self, evt):
			self.img.rotateCounterClockwise()


		def onSlider(self, evt):
			# Vertical sliders have their low value on the bottom on OSX;
			# on MSW and GTK, the low value is at the top
			val = evt.EventObject.Value * 0.01
			dir = evt.EventObject.Orientation[0].lower()
			if dir == "h":
				# Change the width of the image
				self.img.Width = (self.imgPanel.Width * val)
			else:
				self.img.Height = (self.imgPanel.Height * val)
			
			
		def onLoadImage(self, evt): 
			f = dabo.ui.getFile("jpg", "png", "gif", "bmp", "tif", "ico", "*")
			if f:
				self.img.Picture = f
		
		
		def onResize(self, evt):
			self.needUpdate = True
			
		
		def onIdle(self, evt):
			if self.needUpdate:
				self.needUpdate = False
				wd = self.HSlider.Value * 0.01 * self.imgPanel.Width
				ht = self.VSlider.Value * 0.01 * self.imgPanel.Height
				self.img.Size = (wd, ht)
						

	app = dabo.dApp()
	app.MainFormClass = ImgForm
	app.start()
	
