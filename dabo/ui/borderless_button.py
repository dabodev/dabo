# -*- coding: utf-8 -*-
import inspect
import sys

import wx

try:
    import wx.lib.platebtn as platebtn
except ImportError:
    raise ImportError("Your version of wxPython is too old for dBorderlessButton")

from .. import application, dColors, events, settings, ui
from ..dLocalize import _

dabo_module = settings.get_dabo_package()


class dBorderlessButton(ui.dControlMixin, platebtn.PlateButton):
    """
    Creates a button that can be pressed by the user to trigger an action.

    Example::

        class MyButton(ui.dBorderlessButton):
            def initProperties(self):
                self.Caption = "Press Me"

            def onHit(self, evt):
                self.Caption = "Press Me one more time"

    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dBorderlessButton
        preClass = platebtn.PlateButton

        self._backColorHover = (128, 128, 128)
        # Initialize the self._*picture attributes
        self._picture = self._hoverPicture = self._focusPicture = ""
        # These atts underlie the image sizing properties.
        self._imgScale = self._imgHt = self._imgWd = None
        # This controls whether the button automatically resizes
        # itself when its Picture changes.
        self._autoSize = False
        # On some platforms, we need to add some 'breathing room'
        # around the bitmap image in order for it to appear correctly
        self._bmpBorder = 10

        ui.dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def _initEvents(self):
        super()._initEvents()
        # The EVT_BUTTON event for this control is fired
        # to the parent of the control rather than the control.
        # Binding to EVT_LEFT_UP fixes the problem. -nwl
        self.Bind(wx.EVT_LEFT_UP, self._onWxHit)

    def _getInitPropertiesList(self):
        return super()._getInitPropertiesList() + ("ButtonShape",)

    # Property definitions
    @property
    def BackColorHover(self):
        """
        Color of the button background when mouse is hovered over control (str or tuple)
        Default=(128, 128, 128) Changing this color with change the color of the control when
        pressed as well.
        """
        return self._backColorHover

    @BackColorHover.setter
    def BackColorHover(self, val):
        if self._constructed():
            if isinstance(val, str):
                val = dColors.colorTupleFromName(val)
            if isinstance(val, tuple):
                self._backColoHover = val
                self.SetPressColor(wx.Color(*val))
            else:
                raise ValueError("BackColorHover must be a valid color string or tuple")
        else:
            self._properties["BackColorHover"] = val

    @property
    def NormalBitmap(self):
        """The bitmap normally displayed on the button.  (wx.Bitmap)"""
        return self.GetBitmapLabel()

    @property
    def ButtonShape(self):
        """Shape of the button. (str)

        Normal/Rounded : button with rounded corners. (default)
        Square         : button with square corners.
        """
        if self._hasWindowStyleFlag(platebtn.PB_STYLE_SQUARE):
            return "Square"
        else:
            return "Normal"

    @ButtonShape.setter
    def ButtonShape(self, val):
        sst = val[:1].lower()
        if sst == "s":
            self._addWindowStyleFlag(platebtn.PB_STYLE_SQUARE)
        elif sst in ("n", "r"):
            self._delWindowStyleFlag(platebtn.PB_STYLE_SQUARE)
        else:
            nm = self.Name
            raise ValueError(f"Invalid value of {nm}.ButtonShape property: {val}")

    @property
    def CancelButton(self):
        # need to implement
        return False

    @CancelButton.setter
    def CancelButton(self, val):
        warnings.warn(_("CancelButton isn't implemented yet."), Warning)

    @property
    def DefaultButton(self):
        """Specifies whether this command button gets clicked on -Enter-."""
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
    def Font(self):
        """The font properties of the button. (obj)"""
        from ..ui import dFont

        if hasattr(self, "_font") and isinstance(self._font, dFont):
            v = self._font
        else:
            v = self.Font = dFont(_nativeFont=self.GetFont())
        stack = inspect.stack()
        # We want to see the calling function to tell if it's coming from wx or
        # from Dabo.
        caller = stack[1]
        call_path = caller.filename.split("/")
        if "wx" in call_path:
            return v._nativeFont
        return v

    @Font.setter
    def Font(self, val):
        # PVG: also accept wxFont parameter
        if isinstance(val, (wx.Font,)):
            val = ui.dFont(_nativeFont=val)
        if self._constructed():
            self._font = val
            try:
                self.SetFont(val._nativeFont)
            except AttributeError:
                dabo_module.error(_("Error setting font for %s") % self.Name)
            val.bindEvent(events.FontPropertiesChanged, self._onFontPropsChanged)
        else:
            self._properties["Font"] = val

    @property
    def Picture(self):
        """Specifies the image normally displayed on the button. (str)"""
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
        else:
            self._properties["Picture"] = val


ui.dBorderlessButton = dBorderlessButton


class _dBorderlessButton_test(dBorderlessButton):
    def initProperties(self):
        self.Caption = "You better not push me"
        self.FontSize = 8
        self.Width = 223
        self.Picture = "themes/tango/32x32/apps/accessories-text-editor.png"

    def onContextMenu(self, evt):
        print("context menu")

    def onMouseRightClick(self, evt):
        print("right click")

    def onHit(self, evt):
        self.ForeColor = "purple"
        self.FontBold = True
        self.FontItalic = True
        self.Caption = "Ok, you cross this line, and you die."
        self.Width = 333
        self.Form.layout()


if __name__ == "__main__":
    from ui import test

    test.Test().runTest(_dBorderlessButton_test)
