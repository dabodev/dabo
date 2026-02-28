# -*- coding: utf-8 -*-
import warnings
from pathlib import Path

import wx

from .. import ui
from ..localization import _
from . import dControlMixin
from . import dImageMixin
from . import makeDynamicProperty


class dButtonMixin(dControlMixin, dImageMixin):
    """Contains the properties and methods common to buttons"""

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
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
        # Bitmap position: wx.TOP puts the bitmap above the label (text below bitmap)
        self._picturePosition = wx.TOP
        self._pictureMargin = 4

        dImageMixin.__init__(self)
        dControlMixin.__init__(
            self,
            self._preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def _afterInit(self):
        """
        The various pictures cannot be set at construction, so those values will be stored in the
        underlying attributes, so they can be set here.
        """
        self.FocusPicture = self._focusPicture
        self.DownPicture = self._downPicture
        self.Picture = self._picture
        super()._afterInit()

    def _get_parent_with_set_default(self):
        """Usually only the top level window has Get/SetDefaultItem()."""
        parent_with_set_default = self.Parent
        while parent_with_set_default:
            if hasattr(parent_with_set_default, "SetDefaultItem"):
                break
            parent_with_set_default = parent_with_set_default.Parent
        if not parent_with_set_default:
            # Shouldn't happen, but just in case
            warnings.warn(_(f"Cannot set Default for {self.Name}"), Warning)
        return parent_with_set_default

    def _sizeToBitmap(self):
        if self.Picture:
            self.Size = self.GetBestSize()

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
        return self.GetBitmap()

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
        """
        No longer supported in wxPython.

        Previously this would be the button that would get clicked on -Escape-.
        """
        warnings.warn(_("CancelButton is no deprecated and no longer works."), Warning)
        return False

    @CancelButton.setter
    def CancelButton(self, val):
        warnings.warn(_("CancelButton is no deprecated and no longer works."), Warning)

    @property
    def DefaultButton(self):
        """Specifies whether this Bitmap button gets clicked on -Enter-."""
        parent_with_set_default = self._get_parent_with_set_default()
        if parent_with_set_default:
            return parent_with_set_default.GetDefaultItem() == self
        else:
            return False

    @DefaultButton.setter
    def DefaultButton(self, val):
        if self._constructed():
            parent_with_set_default = self._get_parent_with_set_default()
            if not parent_with_set_default:
                # Warning was already issued
                return
            if val:
                parent_with_set_default.SetDefaultItem(self._pemObject)
            else:
                if parent_with_set_default.GetDefaultItem() == self._pemObject:
                    # Only change the default item to None if it wasn't self: if another object
                    # is the default item, setting self.DefaultButton = False shouldn't also set
                    # that other object's DefaultButton to False.
                    parent_with_set_default.SetDefaultItem(None)
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
            if not val:
                self._downPicture = ""
                return
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
            if not val:
                self._focusPicture = ""
                return
            if isinstance(val, wx.Bitmap):
                bmp = val
            else:
                bmp = ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
            self.SetBitmapFocus(bmp)
        else:
            self._properties["FocusPicture"] = val

    @property
    def HoverBitmap(self):
        """The bitmap displayed on the buttoni when the cursor hovers over it.  (wx.Bitmap)"""
        return self.GetBitmapCurrent()

    @property
    def HoverPicture(self):
        return self._hover_picture

    @HoverPicture.setter
    def HoverPicture(self, val):
        self._hover_picture = val
        if self._constructed():
            if not val:
                self._hover_picture = ""
                return
            if isinstance(val, wx.Bitmap):
                bmp = val
            else:
                bmp = ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
            self.SetBitmapCurrent(bmp)
        else:
            self._properties["HoverPicture"] = val

    @property
    def PictureBitmap(self):
        """The bitmap displayed normally on the button.  (wx.Bitmap)"""
        return self.GetBitmap()

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
            if not val:
                self._picture = ""
                return
            if isinstance(val, wx.Bitmap):
                bmp = val
            else:
                bmp = ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
            self.SetBitmap(bmp)
            if isinstance(self, dButton):
                # Apply position and margins after SetBitmap — on macOS, SetBitmap
                # resets the position to the default (LEFT) if called first.
                self.SetBitmapPosition(self._picturePosition)
                self.SetBitmapMargins(self._pictureMargin, self._pictureMargin)
                # Recalculate the button's best size to fit both bitmap and label.
                self.InvalidateBestSize()
                self.SetInitialSize()
            # If the others haven't been specified, default them to the same
            if not self._downPicture:
                self.SetBitmapPressed(bmp)
            if not self._focusPicture:
                self.SetBitmapFocus(bmp)
            if self._autoSize:
                self._sizeToBitmap()
        else:
            self._properties["Picture"] = val

    @property
    def PictureMargin(self):
        """Padding in pixels between the bitmap and the label text.  (int)"""
        return self._pictureMargin

    @PictureMargin.setter
    def PictureMargin(self, val):
        self._pictureMargin = val
        if self._constructed():
            self.SetBitmapMargins(val, val)
        else:
            self._properties["PictureMargin"] = val

    @property
    def PicturePosition(self):
        """Position of the bitmap relative to the label text.
        Use wx.TOP (bitmap above, text below; default), wx.BOTTOM, wx.LEFT, or wx.RIGHT.  (int)"""
        return self._picturePosition

    @PicturePosition.setter
    def PicturePosition(self, val):
        self._picturePosition = val
        if self._constructed():
            self.SetBitmapPosition(val)
        else:
            self._properties["PicturePosition"] = val

    DynamicAutoSize = makeDynamicProperty(AutoSize)
    DynamicBitmap = makeDynamicProperty(Bitmap)
    DynamicBitmapBorder = makeDynamicProperty(BitmapBorder)
    DynamicDefaultButton = makeDynamicProperty(DefaultButton)
    DynamicDownBitmap = makeDynamicProperty(DownBitmap)
    DynamicDownPicture = makeDynamicProperty(DownPicture)
    DynamicFocusBitmap = makeDynamicProperty(FocusBitmap)
    DynamicFocusPicture = makeDynamicProperty(FocusPicture)
    DynamicPicture = makeDynamicProperty(Picture)
    DynamicPictureMargin = makeDynamicProperty(PictureMargin)
    DynamicPicturePosition = makeDynamicProperty(PicturePosition)


class dButton(dButtonMixin, wx.Button):
    """
    Creates a button. The button typically has a Caption, but can also have a Picture.

    The button can have up to three pictures associated with it:

        Picture: the normal picture shown on the button.
        DownPicture: the picture displayed when the button is depressed.
        FocusPicture: the picture displayed when the button has the focus.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dButton
        self._preClass = wx.Button
        super().__init__(
            parent, properties=properties, attProperties=attProperties, *args, **kwargs
        )

    def _initEvents(self):
        super()._initEvents()
        self.Bind(wx.EVT_BUTTON, self._onWxHit)


class dBitmapButton(dButton):
    has_warned = False

    def __init__(self, *args, **kwargs):
        if not self.has_warned:
            warnings.warn(
                "dBitmapButton is deprecated and will be removed in a future release. Please "
                "update your code to use dButton instead.",
                DeprecationWarning,
            )
            self.has_warned = True
        super().__init__(*args, **kwargs)


ui.dButton = dButton
ui.dBitmapButton = dBitmapButton


class _dButton_test(dButton):
    def afterInit(self):
        self.Caption = "Testing!"
        # Demonstrate that the Picture props are working.
        self.Picture = Path("themes/tango/16x16/apps/accessories-text-editor.png")
        self.DownPicture = "themes/tango/16x16/apps/help-browser.png"
        self.FocusPicture = "themes/tango/16x16/apps/utilities-terminal.png"


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dButton_test)
