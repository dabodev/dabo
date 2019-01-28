# -*- coding: utf-8 -*-
import wx
import dabo
from dabo import dException as dException
from dabo.dLocalize import _, n_
from dabo.ui.dControlMixin import dControlMixin


class dStatusBar(dControlMixin, wx.StatusBar):
    """
    Creates a status bar, which displays information to the user.

    The status bar is displayed at the bottom of the form. Add the status bar
    to your form using form.StatusBar=dStatusBar().
    """
    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dStatusBar
        wxClass = wx.StatusBar
        self._platformIsWindows = (self.Application.Platform == "Win")
        self._fieldCount = 1
        dControlMixin.__init__(self, wxClass, parent, properties=properties,
                attProperties=attProperties, *args, **kwargs)


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


    def _getFieldCount(self):
        return self._fieldCount

    def _setFieldCount(self, val):
        if self._constructed():
            self._fieldCount = val
            self.SetFieldsCount(val)
        else:
            self._properties["FieldCount"] = val


    FieldCount = property(_getFieldCount, _setFieldCount, None,
            _("Number of areas, or 'fields', in the status bar. Default=1  (int)"))

