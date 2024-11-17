# -*- coding: utf-8 -*-
import wx

from ui import dControlMixin


class dBox(dControlMixin, wx.StaticBox):
    """Creates a box for visually grouping objects on your form."""

    ## pkm: I'm not sure of the utility of this class, since you can draw
    ##      borders around panels and direct draw on any object. Opinions?
    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dBox
        preClass = wx.StaticBox
        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def _initEvents(self):
        super(dBox, self)._initEvents()


ui.dBox = dBox


class _dBox_test(dBox):
    def initProperties(self):
        self.Width = 100
        self.Height = 20


if __name__ == "__main__":
    from ui import test

    test.Test().runTest(_dBox_test)
