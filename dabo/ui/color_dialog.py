# -*- coding: utf-8 -*-
import wx

from .. import application, color_tools, constants, settings, ui


class dColorDialog(wx.ColourDialog):
    """Creates a dialog that allows the user to pick a color."""

    def __init__(self, parent=None, color=None):
        self._baseClass = dColorDialog
        dat = wx.ColourData()
        # Needed in Windows
        dat.SetChooseFull(True)

        if color is not None:
            if isinstance(color, str):
                try:
                    color = color_tools.colorTupleFromName(color)
                    dat.SetColour(color)
                except KeyError:
                    pass
            elif isinstance(color, tuple):
                dat.SetColour(color)

        if parent is None:
            parent = settings.get_application().ActiveForm
        super().__init__(parent, data=dat)
        self._selColor = None

    def show(self):
        self._selColor = None
        ret = constants.DLG_CANCEL
        res = self.ShowModal()
        if res == wx.ID_OK:
            ret = constants.DLG_OK
            col = self.GetColourData().GetColour()
            self._selColor = col.Red(), col.Green(), col.Blue()
        return ret

    def release(self):
        self.Destroy()

    def getColor(self):
        return self._selColor


ui.dColorDialog = dColorDialog


if __name__ == "__main__":
    from . import test

    test.Test().runTest(dColorDialog)
