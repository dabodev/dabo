# -*- coding: utf-8 -*-
import glob
import os
import sys

import wx

from .. import ui

defaultExtension = "png"
_bmpCache = {}


def getIconBitmap(iconName, setMask=True, noEmptyBmp=False):
    """
    Get a bitmap rendition of the icon.

    Look up the icon name in the Dabo icon module. If found, convert and
    return a wx.Bitmap object. If not found, return a wx.NullBitmap object
    if noEmptyBmp is False; otherwise, return None.
    """
    global _bmpCache
    if iconName in _bmpCache:
        return _bmpCache[iconName]
    fileName = getIconFileName(iconName)
    if fileName and os.path.exists(fileName):
        ret = ui.pathToBmp(fileName)
    else:
        if noEmptyBmp:
            ret = None
        else:
            ret = wx.EmptyBitmap(1, 1)
    _bmpCache[iconName] = ret
    return ret


def addExtension(iconName):
    """If there isn't an extension, add the default extension."""
    splitext = os.path.splitext(iconName)
    if len(splitext[1]) == 0:
        iconName = "%s.%s" % (iconName, defaultExtension)
    return iconName


def getIcon(iconName):
    iconName = addExtension(iconName)
    return open("%s/%s" % (__path__[-1:][0], iconName), "rb").read()


def getIconFileName(iconName):
    """Returns the full path and file name of the passed icon name.

    If not found, returns None.
    """
    iconName = addExtension(iconName)
    ret = os.path.join(__path__[-1:][0], "%s" % iconName)

    if not os.path.exists(ret):
        ret = None
        for pth in sys.path:
            icn = os.path.join(pth, "%s" % iconName)
            if os.path.exists(icn):
                ret = icn
                break
    return ret


def getAvailableIcons():
    """Returns a list of all available icon names."""
    ret = []
    pth = __path__[0]
    defExt = ".%s" % defaultExtension
    exts = ["png", "jpg", "gif", "bmp"]
    for ext in exts:
        ics = glob.glob("%s/*.%s" % (pth, ext))
        ret += [os.path.split(ic)[-1].replace(defExt, "") for ic in ics]
    return ret
