''' dabo.ui.uiwx.dIcons.py 

    Icons are saved in dabo.icons in Python-xpm format. This is
    the wrapper for wxPython to get the icon into a wxBitmap.
'''

import wx, dabo.icons

def getIconBitmap(iconName):
    ''' dIcons.getIconBitmap(string iconName) -> wx.Bitmap
    
        Look up the icon name in the Dabo icon module. If found,
        convert and return a wx.Bitmap object. If not found, return
        a wx.NullBitmap object.
    '''
    try:
        fileName = dabo.icons.getIconFileName(iconName)
        r = wx.Bitmap(fileName)
        return r
    except (NameError, AttributeError):
        r = wx.NullBitmap
    return r

