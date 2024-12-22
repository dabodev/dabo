# -*- coding: utf-8 -*-
import wx

from .. import dColors, ui
from ..dLocalize import _
from . import dForm, dSplitter, makeDynamicProperty


class dSplitForm(dForm):
    def __init__(self, *args, **kwargs):
        self._splitter = None
        super().__init__(*args, **kwargs)

    def unsplit(self):
        self.Splitter.unsplit()

    def split(self, dir=None):
        self.Splitter.split(dir)

    @property
    def MinPanelSize(self):
        """Controls the minimum width/height of the panels.  (int)"""
        return self.Splitter.MinPanelSize

    @MinPanelSize.setter
    def MinPanelSize(self, val):
        if self._constructed():
            self.Splitter.MinPanelSize = val
        else:
            self._properties["MinPanelSize"] = val

    @property
    def Orientation(self):
        """Determines if the window splits Horizontally or Vertically.  (str)"""
        return self.Splitter.Orientation

    @Orientation.setter
    def Orientation(self, val):
        if self._constructed():
            self.Splitter.Orientation = val
        else:
            self._properties["MinPanelSize"] = val

    @property
    def Panel1(self):
        """Returns the Top/Left panel.  (SplitterPanel)"""
        return self.Splitter.Panel1

    @Panel1.setter
    def Panel1(self, pnl):
        if self._constructed():
            self.Splitter.Panel1 = pnl
        else:
            self._properties["Panel1"] = pnl

    @property
    def Panel2(self):
        """Returns the Bottom/Right panel.  (SplitterPanel)"""
        return self.Splitter.Panel2

    @Panel2.setter
    def Panel2(self, pnl):
        if self._constructed():
            self.Splitter.Panel2 = pnl
        else:
            self._properties["Panel2"] = pnl

    @property
    def SashPosition(self):
        """Position of the sash when the window is split.  (int)"""
        return self.Splitter.SashPosition

    @SashPosition.setter
    def SashPosition(self, val):
        if self._constructed():
            self.Splitter.SashPosition = val
        else:
            self._properties["SashPosition"] = val

    @property
    def Splitter(self):
        """Reference to the main splitter in the form  (dSplitter"""
        if self._splitter is None:
            win = self._splitter = dSplitter(
                self, createPanes=True, createSizers=True, RegID="MainSplitter"
            )

            def addToSizer(frm, itm):
                if not frm.Sizer:
                    ui.callAfter(addToSizer, frm, itm)
                else:
                    frm.Sizer.append1x(itm)
                    frm.layout()
                itm.toggleSplit()
                itm.toggleSplit()

            win.Visible = True
            ui.callAfter(addToSizer, self, win)
        return self._splitter

    DynamicMinPanelSize = makeDynamicProperty(MinPanelSize)
    DynamicOrientation = makeDynamicProperty(Orientation)
    DynamicSashPosition = makeDynamicProperty(SashPosition)


ui.dSplitForm = dSplitForm


class _dSplitForm_test(dSplitForm):
    def initProperties(self):
        self.Caption = "Splitter Demo"

    def afterInit(self):
        self.Splitter.Panel1.BackColor = dColors.randomColor()
        self.Splitter.Panel2.BackColor = dColors.randomColor()


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dSplitForm_test)
