''' dabo.ui.uiwx.dIcons.py 

Icons are saved in dabo.icons in png format. This is
the wrapper for wxPython to get the icon into a wxBitmap.
'''
import wx, dabo.icons

def getIconBitmap(iconName):
	''' Get a bitmap rendition of the icon.

	Look up the icon name in the Dabo icon module. If found, convert and 
	return a wx.Bitmap object. If not found, return a wx.NullBitmap object.
	'''
	try:
		fileName = dabo.icons.getIconFileName(iconName)
		r = wx.Image(fileName, wx.BITMAP_TYPE_PNG)
		r.SetMask(True)
		return r.ConvertToBitmap()
	except:
		r = wx.NullBitmap
	return r


