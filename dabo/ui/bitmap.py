# -*- coding: utf-8 -*-
import wx
import dabo
from dabo.ui import dControlMixin
from dabo.ui import dImageMixin
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dBitmap(dControlMixin, dImageMixin, wx.StaticBitmap):
    """Creates a simple bitmap control to display images on your forms."""
    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dBitmap
        preClass = wx.StaticBitmap
        picName = self._extractKey((kwargs, properties, attProperties), "Picture", "")

        dImageMixin.__init__(self)
        dControlMixin.__init__(self, preClass, parent, properties=properties,
                attProperties=attProperties, *args, **kwargs)

        if picName:
            self.Picture = picName


dabo.ui.dBitmap = dBitmap


class _dBitmap_test(dBitmap):
    def initProperties(self):
        self.Picture = "daboIcon016"
#        self.Size = (40,30)

if __name__ == "__main__":
    from dabo.ui import test
    test.Test().runTest(_dBitmap_test)
