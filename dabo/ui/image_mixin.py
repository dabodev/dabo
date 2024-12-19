# -*- coding: utf-8 -*-
import os

import wx

from .. import ui
from ..dLocalize import _
from . import makeDynamicProperty


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

    # Property definitions
    @property
    def Bitmap(self):
        """The bitmap representation of the displayed image.  (wx.Bitmap)"""
        if self._bmp is None:
            self._bmp = wx.EmptyBitmap(1, 1, 1)
        return self._bmp

    @Bitmap.setter
    def Bitmap(self, val):
        self._bmp = val

    @property
    def BitmapHeight(self):
        """Height of the actual displayed bitmap  (int)"""
        return self._bitmapHeight

    @property
    def BitmapWidth(self):
        """Width of the actual displayed bitmap  (int)"""
        return self._bitmapWidth

    @property
    def ImageHeight(self):
        """
        When set, sets the height of all images shown on this control. Default=None, which performs
        no resizing.  (int)
        """
        return self._imgHt

    @ImageHeight.setter
    def ImageHeight(self, val):
        self._imgHt = val
        pic = self.Picture
        if pic:
            self.Picture = pic
        if self._autoSize:
            self._sizeToBitmap()
        self.refresh()

    @property
    def ImageScale(self):
        """
        When set, scales all images shown on this control. The value is a decimal, not a percent, so
        1.0 is normal size, 0.5 is half size, etc. Default=None, which performs no scaling  (float)
        """
        return self._imgScale

    @ImageScale.setter
    def ImageScale(self, val):
        self._imgScale = val
        pic = self.Picture
        if pic:
            self.Picture = pic
        if self._autoSize:
            self._sizeToBitmap()
        self.refresh()

    @property
    def ImageWidth(self):
        """
        When set, sets the width of all images shown on this control.  Default=None, which performs
        no resizing.  (int)
        """
        return self._imgWd

    @ImageWidth.setter
    def ImageWidth(self, val):
        self._imgWd = val
        pic = self.Picture
        if pic:
            self.Picture = pic
        if self._autoSize:
            self._sizeToBitmap()
        self.refresh()

    @property
    def Picture(self):
        """The file used as the source for the displayed image.  (str)"""
        return self.GetBitmap()

    @Picture.setter
    def Picture(self, val):
        if self._constructed():
            self._picture = val
            if isinstance(val, wx.Bitmap):
                bmp = val
            else:
                bmp = ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
            self.Freeze()
            self.SetBitmap(bmp)
            self.Thaw()
        else:
            self._properties["Picture"] = val

    DynamicBitmap = makeDynamicProperty(Bitmap)
    DynamicImageHeight = makeDynamicProperty(ImageHeight)
    DynamicImageScale = makeDynamicProperty(ImageScale)
    DynamicImageWidth = makeDynamicProperty(ImageWidth)
    DynamicPicture = makeDynamicProperty(Picture)


ui.dImageMixin = dImageMixin
