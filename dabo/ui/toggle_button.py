# -*- coding: utf-8 -*-
import wx
import wx.lib.buttons as wxb

from .. import events, ui
from ..localization import _
from . import dDataControlMixin, dImageMixin


class dToggleButton(dDataControlMixin, dImageMixin, wxb.GenBitmapTextToggleButton):
    """
    Creates a button that toggles on and off, for editing boolean values.

    This is functionally equivilent to a dCheckbox, but visually much different.
    Also, it implies that pushing it will cause some sort of immediate action to
    take place, like you get with a normal button.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = ui.dToggleButton
        preClass = wxb.GenBitmapTextToggleButton
        # These are required arguments
        kwargs["bitmap"] = None
        kwargs["label"] = ""
        self._downPicture = None
        bw = self._extractKey(attProperties, "BezelWidth", None)
        if bw is not None:
            bw = int(bw)
        else:
            bw = self._extractKey((properties, kwargs), "BezelWidth", 5)
        kwargs["BezelWidth"] = bw
        style = self._extractKey((properties, attProperties, kwargs), "style", 0) | wx.BORDER_NONE
        kwargs["style"] = style
        dImageMixin.__init__(self)
        dDataControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )
        self.Bind(wx.EVT_BUTTON, self.__onButton)

    def __onButton(self, evt):
        self.flushValue()
        self.raiseEvent(events.Hit, evt)

    def getBlankValue(self):
        return False

    @property
    def BezelWidth(self):
        """Width of the bezel on the sides of the button. Default=5  (int)"""
        return self.GetBezelWidth()

    @BezelWidth.setter
    def BezelWidth(self, val):
        if self._constructed():
            self.SetBezelWidth(val)
            self.Refresh()
        else:
            self._properties["BezelWidth"] = val

    @property
    def DownPicture(self):
        """Picture displayed when the button is pressed  (str)"""
        return self._downPicture

    @DownPicture.setter
    def DownPicture(self, val):
        if self._constructed():
            self._downPicture = val
            if isinstance(val, wx.Bitmap):
                bmp = val
            else:
                bmp = ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
            self.SetBitmapSelected(bmp)
            self.refresh()
        else:
            self._properties["DownPicture"] = val

    @property
    def Picture(self):
        """Picture used for the normal (unselected) state  (str)"""
        return self._picture

    @Picture.setter
    def Picture(self, val):
        if self._constructed():
            self._picture = val
            if isinstance(val, wx.Bitmap):
                bmp = val
            else:
                bmp = ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
            notdown = not self._downPicture
            self.SetBitmapLabel(bmp, notdown)
            self.refresh()
        else:
            self._properties["Picture"] = val


ui.dToggleButton = dToggleButton


class _dToggleButton_test(dToggleButton):
    def afterInit(self):
        self.Caption = "Toggle me!"
        self.Size = (100, 31)
        self.Picture = "themes/tango/22x22/apps/accessories-text-editor.png"
        self.DownPicture = "themes/tango/22x22/apps/help-browser.png"

    def onHit(self, evt):
        if self.Value:
            state = "down"
        else:
            state = "up"
        bval = self.Value
        self.Caption = _("State: %(state)s (Boolean: %(bval)s)") % locals()


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dToggleButton_test)
