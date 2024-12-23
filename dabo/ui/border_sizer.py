# -*- coding: utf-8 -*-
import wx

from .. import ui
from ..localization import _
from . import dBox, dButton, dForm, dLabel, dPanel, dSizer, dSizerMixin, makeDynamicProperty


class dBorderSizer(dSizerMixin, wx.StaticBoxSizer):
    """
    A BorderSizer is a regular box sizer, but with a visible box around
    the perimiter. You must either create the box first and pass it to the
    dBorderSizer's constructor, or pass a parent object, and the box
    will be created for you in the constructor as a child object of the parent
    you passed.
    """

    def __init__(self, box, orientation="h", properties=None, **kwargs):
        self._baseClass = dBorderSizer
        self._border = 0
        self._parent = None
        # Make sure that they got the params in the right order
        if isinstance(box, str):
            box, orientation = orientation, box
        if not isinstance(box, dBox):
            prnt = box
            box = dBox(prnt)
            box.sendToBack()
        # Convert Dabo orientation to wx orientation
        orient = self._extractKey((kwargs, properties), "Orientation", orientation)
        if orient[0].lower() == "v":
            orientation = wx.VERTICAL
        else:
            orientation = wx.HORIZONTAL
        wx.StaticBoxSizer.__init__(self, box, orientation)

        self._properties = {}
        # The keyword properties can come from either, both, or none of:
        #    + the properties dict
        #    + the kwargs dict
        # Get them sanitized into one dict:
        if properties is not None:
            # Override the class values
            for k, v in list(properties.items()):
                self._properties[k] = v
        properties = self._extractKeywordProperties(kwargs, self._properties)
        self.setProperties(properties)

        if kwargs:
            # Some kwargs haven't been handled.
            bad = ", ".join(list(kwargs.keys()))
            raise TypeError(("Invalid keyword arguments passed to dBorderSizer: %s") % kwargs)

        # Mark the box as part of the sizer
        self.Box._belongsToBorderSizer = True

        self._afterInit()

    def getNonBorderedClass(self):
        """Return the class that is the non-border sizer version of this class."""
        return dSizer

    # Property definitions
    @property
    def BackColor(self):
        """Color of the box background  (str or tuple)"""
        return self.Box.BackColor

    @BackColor.setter
    def BackColor(self, val):
        self.Box.BackColor = val

    @property
    def Box(self):
        """Reference to the box used in the sizer  (dBox)"""
        return self.GetStaticBox()

    @property
    def Caption(self):
        """Caption for the box  (str)"""
        return self.Box.Caption

    @Caption.setter
    def Caption(self, val):
        self.Box.Caption = val

    @property
    def FontBold(self):
        """Controls the bold setting of the box caption  (bool)"""
        return self.Box.FontBold

    @FontBold.setter
    def FontBold(self, val):
        self.Box.FontBold = val

    @property
    def FontFace(self):
        """Controls the type face of the box caption  (str)"""
        return self.Box.FontFace

    @FontFace.setter
    def FontFace(self, val):
        self.Box.FontFace = val

    @property
    def FontItalic(self):
        """Controls the italic setting of the box caption  (bool)"""
        return self.Box.FontItalic

    @FontItalic.setter
    def FontItalic(self, val):
        self.Box.FontItalic = val

    @property
    def FontSize(self):
        """Size of the box caption font  (int)"""
        return self.Box.FontSize

    @FontSize.setter
    def FontSize(self, val):
        self.Box.FontSize = val

    @property
    def FontUnderline(self):
        """Controls the underline setting of the box caption  (bool)"""
        return self.Box.FontUnderline

    @FontUnderline.setter
    def FontUnderline(self, val):
        self.Box.FontUnderline = val

    # Dynamic property declarations
    DynamicBackColor = makeDynamicProperty(BackColor)
    DynamicCaption = makeDynamicProperty(Caption)
    DynamicFontBold = makeDynamicProperty(FontBold)
    DynamicFontFace = makeDynamicProperty(FontFace)
    DynamicFontItalic = makeDynamicProperty(FontItalic)
    DynamicFontSize = makeDynamicProperty(FontSize)
    DynamicFontUnderline = makeDynamicProperty(FontUnderline)


ui.dBorderSizer = dBorderSizer


class TestForm(dForm):
    def afterInit(self):
        self.Sizer = dSizer("v", DefaultBorder=10)
        lbl = dLabel(self, Caption="Button in BoxSizer Below", FontSize=16)
        self.Sizer.append(lbl, halign="center")
        sz = dBorderSizer(self, "v")
        self.Sizer.append1x(sz)
        btn = dButton(self, Caption="Click")
        sz.append1x(btn)
        pnl = dPanel(self, BackColor="seagreen")
        self.Sizer.append1x(pnl, border=18)


class _dBorderSizer_test(dBorderSizer):
    def __init__(self, bx=None, *args, **kwargs):
        super(_dBorderSizer_test, self).__init__(box=bx, orientation="h", *args, **kwargs)


if __name__ == "__main__":
    from ..application import dApp

    app = dApp()
    app.MainFormClass = TestForm
    app.start()
