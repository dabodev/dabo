# -*- coding: utf-8 -*-
import wx

import ui
from lib.utils import ustr
from ui import dControlMixin
from ui import makeDynamicProperty


class dLine(dControlMixin, wx.StaticLine):
    """
    Creates a horizontal or vertical line.

    If Orientation is "Vertical", Height refers to the length of the line.
    If Orientation is "Horizontal", Width refers to the length of the line.
    The other value refers to how wide the control is, which affects how much
    buffer space will enclose the line, which will appear in the center of
    this space.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dLine
        preClass = wx.StaticLine

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
        super(dLine, self)._initEvents()

    # property get/set functions
    def _getOrientation(self):
        if self._hasWindowStyleFlag(wx.LI_VERTICAL):
            return "Vertical"
        else:
            return "Horizontal"

    def _setOrientation(self, value):
        # Note: Orientation must be set before object created.
        self._delWindowStyleFlag(wx.LI_VERTICAL)
        self._delWindowStyleFlag(wx.LI_HORIZONTAL)

        value = ustr(value)[0].lower()
        if value == "v":
            self._addWindowStyleFlag(wx.LI_VERTICAL)
        elif value == "h":
            self._addWindowStyleFlag(wx.LI_HORIZONTAL)
        else:
            raise ValueError(
                "The only possible values are " "'Horizontal' and 'Vertical'."
            )

    # property definitions follow:
    Orientation = property(
        _getOrientation,
        _setOrientation,
        None,
        "Specifies the Orientation of the line. (str) \n"
        "   Horizontal (default) \n"
        "   Vertical"
        "This is determined by the Width and Height properties. "
        "If the Width is greater than the Height, it will be Horizontal. "
        "Otherwise, it will be Vertical.",
    )
    DynamicOrientation = makeDynamicProperty(Orientation)


ui.dLine = dLine


class _dLine_test(dLine):
    def initProperties(self):
        self.Orientation = "Horizontal"
        self.Width = 200
        self.Height = 10


if __name__ == "__main__":
    from ui import test

    test.Test().runTest(_dLine_test)
