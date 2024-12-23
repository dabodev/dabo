# -*- coding: utf-8 -*-
import wx

from .. import ui
from ..localization import _
from . import dControlItemMixin, makeDynamicProperty


class dListBox(dControlItemMixin, wx.ListBox):
    """Creates a listbox, allowing the user to choose one or more items."""

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dListBox
        self._choices = []

        preClass = wx.ListBox
        dControlItemMixin.__init__(
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
        self.Bind(wx.EVT_LISTBOX, self._onWxHit)

    def clearSelections(self):
        for elem in self.GetSelections():
            # self.SetSelection(elem, False)
            self.SetSelection(elem)

    def selectAll(self):
        if self.MultipleSelect:
            for ii in range(self.Count):
                self.SetSelection(ii)

    def unselectAll(self):
        self.clearSelections()

    def invertSelections(self):
        """Switch all the items from False to True, and vice-versa."""
        for ii in range(self.Count):
            if self.IsSelected(ii):
                self.Deselect(ii)
            else:
                self.SetSelection(ii)

    @property
    def MultipleSelect(self):
        """Can multiple items be selected at once?  (bool)"""
        return self._hasWindowStyleFlag(wx.LB_EXTENDED)

    @MultipleSelect.setter
    def MultipleSelect(self, val):
        if bool(val):
            self._delWindowStyleFlag(wx.LB_SINGLE)
            self._addWindowStyleFlag(wx.LB_EXTENDED)
        else:
            self._delWindowStyleFlag(wx.LB_EXTENDED)
            self._addWindowStyleFlag(wx.LB_SINGLE)

    DynamicMultipleSelect = makeDynamicProperty(MultipleSelect)


ui.dListBox = dListBox


class _dListBox_test(dListBox):
    def initProperties(self):
        # Simulate a database:
        actors = (
            {"lname": "Jason Leigh", "fname": "Jennifer", "iid": 42},
            {"lname": "Cates", "fname": "Phoebe", "iid": 23},
            {"lname": "Reinhold", "fname": "Judge", "iid": 13},
        )

        choices = []
        keys = {}

        for actor in actors:
            choices.append("%s %s" % (actor["fname"], actor["lname"]))
            keys[actor["iid"]] = len(choices) - 1

        #        self.MultipleSelect = True
        self.Choices = choices
        self.Keys = keys
        self.ValueMode = "Key"
        self.Value = 23

    def onHit(self, evt):
        print("HIT:")
        print("\tKeyValue: ", self.KeyValue)
        print("\tPositionValue: ", self.PositionValue)
        print("\tStringValue: ", self.StringValue)
        print("\tValue: ", self.Value)
        print("\tCount: ", self.Count)

    def onMouseLeftDoubleClick(self, evt):
        print("double click at position %s" % self.PositionValue)

    def onMouseLeftDown(self, evt):
        print("mousedown")


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dListBox_test)
