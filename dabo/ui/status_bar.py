# -*- coding: utf-8 -*-
import wx

from .. import ui
from ..localization import _
from ..localization import n_
from . import dControlMixin


class dStatusBar(dControlMixin, wx.StatusBar):
    """
    Creates a status bar, which displays information to the user.

    The status bar is displayed at the bottom of the form. Add the status bar
    to your form using form.StatusBar=dStatusBar().
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dStatusBar
        preClass = wx.StatusBar
        self._platformIsWindows = self.Application.Platform == "Win"
        self._fieldCount = 1
        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def layout(self):
        """Wrap the wx version of the call, if possible."""
        self.Layout()
        for child in self.Children:
            try:
                child.layout()
            except AttributeError:
                pass
        try:
            # Call the Dabo version, if present
            self.Sizer.layout()
        except AttributeError:
            pass
        if self._platformIsWindows:
            self.refresh()

    @property
    def FieldCount(self):
        """Number of areas, or 'fields', in the status bar. Default=1  (int)"""
        return self._fieldCount

    @FieldCount.setter
    def FieldCount(self, val):
        if self._constructed():
            self._fieldCount = val
            self.SetFieldsCount(val)
        else:
            self._properties["FieldCount"] = val


ui.dStatusBar = dStatusBar
