# -*- coding: utf-8 -*-
import wx
import dabo
from dabo import dConstants as k


class dFontDialog(wx.FontDialog):
    """Creates a font dialog, which asks the user to choose a font."""

    def __init__(self, parent=None, fontData=None):
        self._baseClass = dabo.ui.dFontDialog

        dat = wx.FontData()
        if fontData is not None:
            dat.SetInitialFont(fontData)
        super(dFontDialog, self).__init__(parent=parent, data=dat)

    def show(self):
        ret = k.DLG_CANCEL
        res = self.ShowModal()
        if res == wx.ID_OK:
            ret = k.DLG_OK
        return ret

    def getFont(self):
        return self.GetFontData().GetChosenFont()

    def release(self):
        self.Destroy()


dabo.ui.dFontDialog = dFontDialog


if __name__ == "__main__":
    from dabo.ui import test

    test.Test().runTest(dFontDialog)
