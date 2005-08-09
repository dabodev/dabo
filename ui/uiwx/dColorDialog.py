import wx
import dabo.dConstants as k
import dabo.common.dColors as dColors


class dColorDialog(wx.ColourDialog):
	def __init__(self, parent=None, color=None):
		self._baseClass = dColorDialog
		dat = wx.ColourData()
		# Needed in Windows
		dat.SetChooseFull(True)
		
		if color is not None:
			if isinstance(color, basestring):
				try:
					color = dColors.colorTupleFromName(color)
					dat.SetColour(color)
				except: pass
		super(dColorDialog, self).__init__(parent, data=dat)
		self._selColor = None
	

	def show(self):
		self._selColor = None
		ret = k.DLG_CANCEL
		res = self.ShowModal()
		if res ==  wx.ID_OK:
			ret = k.DLG_OK
			col = self.GetColourData().GetColour()
			self._selColor = col.Red(), col.Green(), col.Blue()
		return ret
	

	def release(self):
		self.Destroy()


	def getColor(self):
		return self._selColor
