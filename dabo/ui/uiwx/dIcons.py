# -*- coding: utf-8 -*-
import wx
import os.path
import dabo.icons


def getIconBitmap(iconName, setMask=True, noEmptyBmp=False):
	""" Get a bitmap rendition of the icon.

	Look up the icon name in the Dabo icon module. If found, convert and 
	return a wx.Bitmap object. If not found, return a wx.NullBitmap object
	if noEmptyBmp is False; otherwise, return None.
	"""
	fileName = dabo.icons.getIconFileName(iconName)
	if fileName and os.path.exists(fileName):
		return dabo.ui.pathToBmp(fileName)
	else:
		if noEmptyBmp:
			return None
		else:
			return wx.EmptyBitmap(1, 1)
