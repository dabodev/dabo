# -*- coding: utf-8 -*-
import wx

from .. import constants
from .. import ui


class dFontDialog(wx.FontDialog):
    """Creates a font dialog, which asks the user to choose a font."""

    def __init__(self, parent=None, fontData=None):
        self._baseClass = ui.dFontDialog

        dat = wx.FontData()
        if fontData is not None:
            dat.SetInitialFont(fontData)
        super().__init__(parent=parent, data=dat)

    def show(self):
        ret = constants.DLG_CANCEL
        res = self.ShowModal()
        if res == wx.ID_OK:
            ret = constants.DLG_OK
        return ret

    def getFont(self):
        return self.GetFontData().GetChosenFont()

    def release(self):
        self.Destroy()


ui.dFontDialog = dFontDialog


if __name__ == "__main__":
    from . import test

    test.Test().runTest(dFontDialog)
