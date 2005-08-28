""" dabo.ui.uiwx.dIcons.py 

Icons are saved in dabo.icons in png format. This is
the wrapper for wxPython to get the icon into a wxBitmap.
"""
import wx, dabo.icons
import os.path

def getIconBitmap(iconName, setMask=True):
	""" Get a bitmap rendition of the icon.

	Look up the icon name in the Dabo icon module. If found, convert and 
	return a wx.Bitmap object. If not found, return a wx.NullBitmap object.
	"""
	fileName = dabo.icons.getIconFileName(iconName)
	if os.path.exists(fileName):
		return dabo.ui.pathToBmp(fileName)
	else:
		return wx.EmptyBitmap(1, 1)

