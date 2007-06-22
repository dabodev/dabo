# -*- coding: utf-8 -*-
import os
import tempfile
import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _
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
		self.__val = None
		self.__imageData = None
		bmp = wx.EmptyBitmap(1, 1)
		picName = self._extractKey((kwargs, properties, attProperties), "Picture", "")

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
	def _getPic(self):
		return self._picture

	def _setPic(self, val):
		if isinstance(val, wx.Image):
			# An image stored as a stream is being used
			self.__image = val
			self._picture = "(stream)"
		else:
			pathExists = os.path.exists(val)
			if not val:
				# Empty string passed; clear any current image
				self._picture = ""
				self._rotation = 0
				self._bmp = wx.EmptyBitmap(1, 1, 1)
				self.__image = wx.EmptyImage(1, 1)		# self._bmp.ConvertToImage()
				self._showPic()
				return
			elif not pathExists:
				origVal = val
				val = dabo.ui.getImagePath(val)
				if val is None or not os.path.exists(val):
					# Bad image reference
					raise IOError, "No file named '%s' exists." % origVal
			self._picture = val
			self._rotation = 0
			self._Image.LoadFile(val)
		if self._Image.Ok():
			self._imgProp = float(self._Image.GetWidth()) / float(self._Image.GetHeight())
		else:
			self._imgProp = 1.0
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
			dabo.logError(_("ScaleMode must be either 'Clip', 'Proportional' or 'Stretch'.") )


	def _getValue(self):
		return self.__val
		try:
			ret = self.__imageData
		except AttributeError:
			ret = self.__imageData = u""
		return ret

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
					log = wx.LogNull()
					img = dabo.ui.imageFromData(val)
				except:
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
			self.__image = wx.NullImage
		return self.__image


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
			f = dabo.ui.getFile("jpg", "png", "gif", "bmp", "*")
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

