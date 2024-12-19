# -*- coding: utf-8 -*-
import wx

from .. import ui
from ..dLocalize import _
from . import dTextBoxMixin, makeDynamicProperty


# The EditBox is just a TextBox with some additional styles.
class dEditBox(dTextBoxMixin, wx.TextCtrl):
    """
    Creates an editbox, which allows editing of string data of unlimited size.

    The editbox will create scrollbars as necessary, and can edit string or
    unicode data.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dEditBox

        preClass = wx.TextCtrl
        kwargs["style"] = wx.TE_MULTILINE
        self._wordWrap = self._extractKey((properties, attProperties, kwargs), "WordWrap", True)
        if self._wordWrap:
            kwargs["style"] = kwargs["style"] | wx.TE_BESTWRAP
        else:
            kwargs["style"] = kwargs["style"] | wx.TE_DONTWRAP
        dTextBoxMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def scrollToBeginning(self):
        """Moves the insertion point to the beginning of the text"""
        self.SetInsertionPoint(0)
        self.ShowPosition(0)
        self.Refresh()

    def scrollToEnd(self):
        """Moves the insertion point to the end of the text"""
        self.SetInsertionPointEnd()
        self.ShowPosition(self.GetLastPosition())
        self.Refresh()

    # property definitions follow:
    @property
    def ProcessTabs(self):
        """Specifies whether the user can enter tabs in the control."""
        return self._hasWindowStyleFlag(wx.TE_PROCESS_TAB)

    @ProcessTabs.setter
    def ProcessTabs(self, val):
        if val:
            self._addWindowStyleFlag(wx.TE_PROCESS_TAB)
        else:
            self._delWindowStyleFlag(wx.TE_PROCESS_TAB)

    @property
    def WordWrap(self):
        """
        Specifies whether lines longer than the width of the control get wrapped.

        This is a soft wrapping; newlines are not inserted. If False, a horizontal scrollbar will
        appear when a line is too long to fit in the horizontal space. Note that this must be set
        when the object is created, and changing it after instantiation will have no effect.
        Default=True  (bool)
        """
        return self._wordWrap

    @WordWrap.setter
    def WordWrap(self, val):
        self._wordWrap = val
        self._delWindowStyleFlag(wx.TE_DONTWRAP)
        self._delWindowStyleFlag(wx.TE_WORDWRAP)
        self._delWindowStyleFlag(wx.TE_BESTWRAP)
        if val:
            self._addWindowStyleFlag(wx.TE_BESTWRAP)
        else:
            self._addWindowStyleFlag(wx.TE_DONTWRAP)


ui.dEditBox = dEditBox


class _dEditBox_test(dEditBox):
    def initProperties(self):
        self.Value = """Love, exciting and new
Come aboard, we're expecting you
Love, life's sweetest reward
Let it flow, it floats back to you

Love Boat soon will be making another run
The Love Boat promises something for everyone
Set a course for adventure
Your mind on a new romance

Love won't hurt anymore
It's an open smile on a friendly shore
Yes love...
It's love...

Love Boat soon will be making another run
The Love Boat promises something for everyone
Set a course for adventure
Your mind on a new romance

Love won't hurt anymore
It's an open smile on a friendly shore
It's love...
It's love...
It's love...
It's the Love Boat
It's the Love Boat
"""

    def afterInit(self):
        self.Form.Size = (444, 244)
        ui.callAfter(self.adjustFormCaption)

    def adjustFormCaption(self):
        newcap = "%s - WordWrap: %s" % (self.Form.Caption, self.WordWrap)
        self.Form.Caption = newcap


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dEditBox_test, WordWrap=True)
    test.Test().runTest(_dEditBox_test, WordWrap=False)
