''' dabo.ui.uiwx.dIcons.py 

Icons are saved in dabo.icons in png format. This is
the wrapper for wxPython to get the icon into a wxBitmap.
'''
import wx, dabo.icons
import os.path

def getIconBitmap(iconName):
	''' Get a bitmap rendition of the icon.

	Look up the icon name in the Dabo icon module. If found, convert and 
	return a wx.Bitmap object. If not found, return a wx.NullBitmap object.
	'''
	fileName = dabo.icons.getIconFileName(iconName)
	if os.path.exists(fileName):
		if wx.GetApp():
			r = wx.Image(fileName, wx.BITMAP_TYPE_PNG)
			r.SetMask(True)
			return r.ConvertToBitmap()
		else:
			return wx.NullBitmap
	else:
		return wx.NullBitmap

