# -*- coding: utf-8 -*-
import wx

from .. import ui
from ..lib.utils import ustr
from ..localization import _
from ..ui import makeDynamicProperty


class AlignmentMixin(object):
    @property
    def Alignment(self):
        """
        Specifies the alignment of the text. (str)
            Left (default)
            Center
            Right
        """
        if self._hasWindowStyleFlag(wx.ALIGN_RIGHT):
            return "Right"
        elif self._hasWindowStyleFlag(wx.ALIGN_CENTRE):
            return "Center"
        else:
            return "Left"

    @Alignment.setter
    def Alignment(self, value):
        # Note: Alignment must be set before object created.
        self._delWindowStyleFlag(wx.ALIGN_LEFT)
        self._delWindowStyleFlag(wx.ALIGN_CENTRE)
        self._delWindowStyleFlag(wx.ALIGN_RIGHT)
        value = ustr(value).lower()

        if value == "left":
            self._addWindowStyleFlag(wx.ALIGN_LEFT)
        elif value == "center":
            self._addWindowStyleFlag(wx.ALIGN_CENTRE)
        elif value == "right":
            self._addWindowStyleFlag(wx.ALIGN_RIGHT)
        else:
            raise ValueError("The only possible values are 'Left', 'Center', and 'Right'.")

    DynamicAlignment = makeDynamicProperty(Alignment)


ui.AlignmentMixin = AlignmentMixin
