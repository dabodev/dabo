# -*- coding: utf-8 -*-
import os.path

import wx
import icons

_bmpCache = {}


def getIconBitmap(iconName, setMask=True, noEmptyBmp=False):
    """
    Get a bitmap rendition of the icon.

    Look up the icon name in the Dabo icon module. If found, convert and
    return a wx.Bitmap object. If not found, return a wx.NullBitmap object
    if noEmptyBmp is False; otherwise, return None.
    """
    if iconName in _bmpCache:
        return _bmpCache[iconName]
    fileName = icons.getIconFileName(iconName)
    if fileName and os.path.exists(fileName):
        ret = ui.pathToBmp(fileName)
    else:
        if noEmptyBmp:
            ret = None
        else:
            ret = wx.EmptyBitmap(1, 1)
    _bmpCache[iconName] = ret
    return ret
