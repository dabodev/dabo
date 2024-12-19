# -*- coding: utf-8 -*-
import warnings

import wx

from .. import ui
from ..dLocalize import _
from . import dControlMixin, dImageMixin, makeDynamicProperty


class dBitmapButton(dControlMixin, dImageMixin, wx.BitmapButton):
    """
    Creates a button with a picture.

    The button can have up to three pictures associated with it:

        Picture: the normal picture shown on the button.
        DownPicture: the picture displayed when the button is depressed.
        FocusPicture: the picture displayed when the button has the focus.

    Otherwise, dBitmapButton behaves the same as a normal dButton.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dBitmapButton
        preClass = wx.BitmapButton
        # Initialize the self._*picture attributes
        self._picture = self._downPicture = self._focusPicture = ""
        # These atts underlie the image sizing properties.
        self._imgScale = self._imgHt = self._imgWd = None
        # This controls whether the button automatically resizes
        # itself when its Picture changes.
        self._autoSize = False
        # On some platforms, we need to add some 'breathing room'
        # around the bitmap image in order for it to appear correctly
        self._bmpBorder = 10

        dImageMixin.__init__(self)
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
        super(dBitmapButton, self)._initEvents()
        self.Bind(wx.EVT_BUTTON, self._onWxHit)

    def _sizeToBitmap(self):
        if self.Picture:
            bmp = self.Bitmap
            self.Size = (
                bmp.GetWidth() + self._bmpBorder,
                bmp.GetHeight() + self._bmpBorder,
            )

    # Property definitions:
    @property
    def AutoSize(self):
        """Controls whether the button resizes when the Picture changes. (bool)"""
        return self._autoSize

    @AutoSize.setter
    def AutoSize(self, val):
        self._autoSize = val

    @property
    def Bitmap(self):
        return self.GetBitmapLabel()

    @property
    def BitmapBorder(self):
        """Extra space around the bitmap, used when auto-sizing.  (int)"""
        return self._bmpBorder

    @BitmapBorder.setter
    def BitmapBorder(self, val):
        self._bmpBorder = val
        if self._autoSize:
            self._sizeToBitmap()

    @property
    def BorderStyle(self):
        """
        Specifies the type of border for this window. (String).

            Possible choices are:
                "None" - No border
                "Simple" - Border like a regular button
        """
        if self._hasWindowStyleFlag(wx.BU_AUTODRAW):
            return "Simple"
        elif self._hasWindowStyleFlag(wx.NO_BORDER):
            return "None"
        else:
            return "Default"

    @BorderStyle.setter
    def BorderStyle(self, val):
        self._delWindowStyleFlag(wx.NO_BORDER)
        self._delWindowStyleFlag(wx.BU_AUTODRAW)

        if val == "None":
            self._addWindowStyleFlag(wx.NO_BORDER)
        elif val == "Simple":
            self._addWindowStyleFlag(wx.BU_AUTODRAW)

    @property
    def CancelButton(self):
        """Specifies whether this Bitmap button gets clicked on -Escape-."""
        # need to implement
        return False

    @CancelButton.setter
    def CancelButton(self, val):
        warnings.warn(_("CancelButton isn't implemented yet."), Warning)

    @property
    def DefaultButton(self):
        """Specifies whether this Bitmap button gets clicked on -Enter-."""
        if self.Parent is not None:
            return self.Parent.GetDefaultItem() == self
        else:
            return False

    @DefaultButton.setter
    def DefaultButton(self, val):
        if self._constructed():
            if val:
                if self.Parent is not None:
                    self.Parent.SetDefaultItem(self._pemObject)
            else:
                if self._pemObject.GetParent().GetDefaultItem() == self._pemObject:
                    # Only change the default item to None if it wasn't self: if another object
                    # is the default item, setting self.DefaultButton = False shouldn't also set
                    # that other object's DefaultButton to False.
                    self.SetDefaultItem(None)
        else:
            self._properties["DefaultButton"] = val

    @property
    def DownBitmap(self):
        """The bitmap displayed on the button when it is depressed.  (wx.Bitmap)"""
        return self.GetBitmapSelected()

    @property
    def DownPicture(self):
        """Specifies the image displayed on the button when it is depressed.  (str)"""
        return self._downPicture

    @DownPicture.setter
    def DownPicture(self, val):
        self._downPicture = val
        if self._constructed():
            if isinstance(val, wx.Bitmap):
                bmp = val
            else:
                bmp = ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
            self.SetBitmapPressed(bmp)
        else:
            self._properties["DownPicture"] = val

    @property
    def FocusBitmap(self):
        """The bitmap displayed on the button when it receives focus.  (wx.Bitmap)"""
        return self.GetBitmapFocus()

    @property
    def FocusPicture(self):
        """Specifies the image displayed on the button when it receives focus.  (str)"""
        return self._focusPicture

    @FocusPicture.setter
    def FocusPicture(self, val):
        self._focusPicture = val
        if self._constructed():
            if isinstance(val, wx.Bitmap):
                bmp = val
            else:
                bmp = ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
            self.SetBitmapFocus(bmp)
        else:
            self._properties["FocusPicture"] = val

    @property
    def Picture(self):
        """
        Specifies the image normally displayed on the button. This is the default if none of the
        other *Picture properties are specified.  (str)
        """
        return self._picture

    @Picture.setter
    def Picture(self, val):
        self._picture = val
        if self._constructed():
            if isinstance(val, wx.Bitmap):
                bmp = val
            else:
                bmp = ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
            self.SetBitmapLabel(bmp)
            # If the others haven't been specified, default them to the same
            if not self._downPicture:
                self.SetBitmapPressed(bmp)
            if not self._focusPicture:
                self.SetBitmapFocus(bmp)
            if self._autoSize:
                self._sizeToBitmap()
        else:
            self._properties["Picture"] = val

    DynamicAutoSize = makeDynamicProperty(AutoSize)
    DynamicBitmap = makeDynamicProperty(Bitmap)
    DynamicBitmapBorder = makeDynamicProperty(BitmapBorder)
    DynamicCancelButton = makeDynamicProperty(CancelButton)
    DynamicDefaultButton = makeDynamicProperty(DefaultButton)
    DynamicDownBitmap = makeDynamicProperty(DownBitmap)
    DynamicDownPicture = makeDynamicProperty(DownPicture)
    DynamicFocusBitmap = makeDynamicProperty(FocusBitmap)
    DynamicFocusPicture = makeDynamicProperty(FocusPicture)
    DynamicPicture = makeDynamicProperty(Picture)


ui.dBitmapButton = dBitmapButton


class _dBitmapButton_test(dBitmapButton):
    def afterInit(self):
        # Demonstrate that the Picture props are working.
        self.Picture = "themes/tango/16x16/apps/accessories-text-editor.png"
        self.DownPicture = "themes/tango/16x16/apps/help-browser.png"
        self.FocusPicture = "themes/tango/16x16/apps/utilities-terminal.png"
        self.Width = 100
        self.Height = 25


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dBitmapButton_test)
