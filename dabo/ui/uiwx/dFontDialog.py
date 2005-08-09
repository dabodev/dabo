import wx
import dabo.dConstants as k


class dFontDialog(wx.FontDialog):
	def __init__(self, parent=None, fontData=None):
		self._baseClass = dFontDialog
		
		dat = wx.FontData()
		if fontData is not None:
			dat.SetInitialFont(fontData)
		super(dFontDialog, self).__init__(parent=parent, data=dat)

	def show(self):
		ret = k.DLG_CANCEL
		res = self.ShowModal()
		if res ==  wx.ID_OK:
			ret = k.DLG_OK
		return ret
	
	def getFont(self):
		return self.GetFontData().GetChosenFont()
	
	def release(self):
		self.Destroy()
