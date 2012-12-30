# -*- coding: utf-8 -*-
import os
import wx
import dabo
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dImageMixin(object):
	def __init__(self):
		self._picture = ""
		self._bmp = None
		self._bitmapHeight = None
		self._bitmapWidth = None
		# These atts underlie the image sizing properties.
		self._imgScale = self._imgHt = self._imgWd = None
		# This is used by some controls to automatically set the size
		self._autoSize = False


	def _sizeToBitmap(self):
		if self.Picture:
			bmp = self.Bitmap
			self.Size = bmp.GetWidth(), bmp.GetHeight()


	def _getBmp(self):
		if self._bmp is None:
			self._bmp = wx.EmptyBitmap(1, 1, 1)
		return self._bmp

	def _setBmp(self, val):
		self._bmp = val


	def _getBitmapHeight(self):
		return self._bitmapHeight


	def _getBitmapWidth(self):
		return self._bitmapWidth


	def _getImgHt(self):
		return self._imgHt

	def _setImgHt(self, val):
		self._imgHt = val
		pic = self.Picture
		if pic:
			self.Picture = pic
		if self._autoSize:
			self._sizeToBitmap()
		self.refresh()


	def _getImgScale(self):
		return self._imgScale

	def _setImgScale(self, val):
		self._imgScale = val
		pic = self.Picture
		if pic:
			self.Picture = pic
		if self._autoSize:
			self._sizeToBitmap()
		self.refresh()


	def _getImgWd(self):
		return self._imgWd

	def _setImgWd(self, val):
		self._imgWd = val
		pic = self.Picture
		if pic:
			self.Picture = pic
		if self._autoSize:
			self._sizeToBitmap()
		self.refresh()


	def _getPicture(self):
		return self.GetBitmap()

	def _setPicture(self, val):
		if self._constructed():
			self._picture = val
			if isinstance(val, wx.Bitmap):
				bmp = val
			else:
				bmp = dabo.ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
			self.Freeze()
			self.SetBitmap(bmp)
			self.Thaw()
		else:
			self._properties["Picture"] = val


	Bitmap = property(_getBmp, _setBmp, None,
			_("The bitmap representation of the displayed image.  (wx.Bitmap)") )

	BitmapHeight = property(_getBitmapHeight, None, None,
			_("Height of the actual displayed bitmap  (int)"))

	BitmapWidth = property(_getBitmapWidth, None, None,
			_("Width of the actual displayed bitmap  (int)"))

	ImageHeight = property(_getImgHt, _setImgHt, None,
		_("""When set, sets the height of all images shown on this control.
		Default=None, which performs no resizing.  (int)""") )

	ImageScale = property(_getImgScale, _setImgScale, None,
		_("""When set, scales all images shown on this control. The value is
		a decimal, not a percent, so 1.0 is normal size, 0.5 is half size, etc.
		Default=None, which performs no scaling  (float)""") )

	ImageWidth = property(_getImgWd, _setImgWd, None,
		_("""When set, sets the width of all images shown on this control.
		Default=None, which performs no resizing.  (int)""") )

	Picture = property(_getPicture, _setPicture, None,
			_("The file used as the source for the displayed image.  (str)") )


	DynamicBitmap = makeDynamicProperty(Bitmap)
	DynamicImageHeight = makeDynamicProperty(ImageHeight)
	DynamicImageScale = makeDynamicProperty(ImageScale)
	DynamicImageWidth = makeDynamicProperty(ImageWidth)
	DynamicPicture = makeDynamicProperty(Picture)
