# -*- coding: utf-8 -*-
import wx
import dabo
import dabo.dConstants as kons
import dabo.dColors as dColors


class dColorDialog(wx.ColourDialog):
	"""Creates a dialog that allows the user to pick a color."""
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
				except KeyError:
					pass
			elif isinstance(color, tuple):
				dat.SetColour(color)

		if parent is None:
			parent = dabo.dAppRef.ActiveForm
		super(dColorDialog, self).__init__(parent, data=dat)
		self._selColor = None


	def show(self):
		self._selColor = None
		ret = kons.DLG_CANCEL
		res = self.ShowModal()
		if res ==  wx.ID_OK:
			ret = kons.DLG_OK
			col = self.GetColourData().GetColour()
			self._selColor = col.Red(), col.Green(), col.Blue()
		return ret


	def release(self):
		self.Destroy()


	def getColor(self):
		return self._selColor


if __name__ == "__main__":
	import test
	test.Test().runTest(dColorDialog)
