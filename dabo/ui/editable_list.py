# -*- coding: utf-8 -*-
import wx
from wx import adv as wx_adv

from .. import ui
from ..localization import _
from . import dControlMixin, makeDynamicProperty


class dEditableList(dControlMixin, wx_adv.EditableListBox):
    """
    Creates an editable list box, complete with buttons to control
    editing, adding/deleting items, and re-ordering them.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dEditableList
        preClass = wx_adv.EditableListBox
        self._canAdd = self._extractKey((kwargs, properties, attProperties), "CanAdd", True)
        if isinstance(self._canAdd, str):
            self._canAdd = self._canAdd == "True"
        self._canDelete = self._extractKey((kwargs, properties, attProperties), "CanDelete", True)
        if isinstance(self._canDelete, str):
            self._canDelete = self._canDelete == "True"
        self._canOrder = self._extractKey((kwargs, properties, attProperties), "CanOrder", True)
        if isinstance(self._canOrder, str):
            self._canOrder = self._canOrder == "True"
        self._editable = self._extractKey((kwargs, properties, attProperties), "Editable", True)
        style = self._extractKey((kwargs, properties, attProperties), "style", 0)
        if self._canAdd:
            # style = style  | wx.gizmos.EL_ALLOW_NEW
            style = style | wx.adv.EL_ALLOW_NEW
        if self._editable:
            style = style | wx.adv.EL_ALLOW_EDIT
        if self._canDelete:
            style = style | wx.adv.EL_ALLOW_DELETE
        kwargs["style"] = style
        # References to the components of this control
        self._addButton = None
        self._deleteButton = None
        self._editButton = None
        self._downButton = None
        self._upButton = None
        self._panel = None

        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def GetValue(self):
        """
        This control doesn't natively support values, as it is designed
        to simply order and/or edit the list. We need to provide this so that
        the dControlMixin code which calls GetValue() doesn't barf.
        """
        return None

    def layout(self):
        """
        Calling the native Layout() method isn't sufficient, as it doesn't seem
        to call the top panel's Layout(). So we'll do it manually.
        """
        self.Layout()
        self._Panel.Layout()
        if self.Application.Platform == "Win":
            self.refresh()

    ## Property definitions
    @property
    def AddButton(self):
        """Reference to the new item button  (wx.Button)"""
        if self._addButton is None:
            self._addButton = self.GetNewButton()
        return self._addButton

    @property
    def CanAdd(self):
        """Determines if the user can add new entries to the list  (bool)"""
        return self._canAdd

    @CanAdd.setter
    def CanAdd(self, val):
        if self._constructed():
            self._canAdd = val
            self._AddButton.Show(val)
            self.layout()
        else:
            self._properties["CanAdd"] = val

    @property
    def CanDelete(self):
        """Determines if the user can delete entries from the list  (bool)"""
        return self._canDelete

    @CanDelete.setter
    def CanDelete(self, val):
        if self._constructed():
            self._canDelete = val
            self._DeleteButton.Show(val)
            self.layout()
        else:
            self._properties["CanDelete"] = val

    @property
    def CanOrder(self):
        """Determines if the user can re-order items  (bool)"""
        return self._canOrder

    @CanOrder.setter
    def CanOrder(self, val):
        if self._constructed():
            self._canOrder = val
            self._UpButton.Show(val)
            self._DownButton.Show(val)
        else:
            self._properties["CanOrder"] = val
        self.layout()

    @property
    def Caption(self):
        """Text that appears in the top panel of the control  (str)"""
        return self._Panel.GetChildren()[0].GetLabel()

    @Caption.setter
    def Caption(self, val):
        if self._constructed():
            self._Panel.GetChildren()[0].SetLabel(val)
        else:
            self._properties["Caption"] = val

    @property
    def Choices(self):
        """List that contains the entries in the control  (list)"""
        return self.GetStrings()

    @Choices.setter
    def Choices(self, val):
        if self._constructed():
            self.SetStrings(val)
        else:
            self._properties["Choices"] = val

    @property
    def DeleteButton(self):
        """Reference to the delete item button  (wx.Button)"""
        if self._deleteButton is None:
            self._deleteButton = self.GetDelButton()
        return self._deleteButton

    @property
    def DownButton(self):
        """Reference to the move item down button  (wx.Button)"""
        if self._downButton is None:
            self._downButton = self.GetDownButton()
        return self._downButton

    @property
    def Editable(self):
        """Determines if the user can change existing entries  (bool)"""
        return self._editable

    @Editable.setter
    def Editable(self, val):
        if self._constructed():
            self._editable = val
            self._EditButton.Show(val)
            self.layout()
        else:
            self._properties["Editable"] = val

    @property
    def EditButton(self):
        """Reference to the edit item button  (wx.Button)"""
        if self._editButton is None:
            self._editButton = self.GetEditButton()
        return self._editButton

    @property
    def Panel(self):
        """Reference to the panel that contains the caption and buttons  (wx.Panel)"""
        if self._panel is None:
            self._panel = [pp for pp in self.Children if isinstance(pp, wx.Panel)][0]
        return self._panel

    @property
    def UpButton(self):
        """Reference to the move item up button  (wx.Button)"""
        if self._upButton is None:
            self._upButton = self.GetUpButton()
        return self._upButton

    DynamicCanAdd = makeDynamicProperty(CanAdd)
    DynamicCanDelete = makeDynamicProperty(CanDelete)
    DynamicCanOrder = makeDynamicProperty(CanOrder)
    DynamicCaption = makeDynamicProperty(Caption)
    DynamicEditable = makeDynamicProperty(Editable)


ui.dEditableList = dEditableList


class _dEditableList_test(dEditableList):
    def afterInit(self):
        self.Choices = ["Johnny", "Joey", "DeeDee"]
        self.Caption = "Editable table List"

    def onDestroy(self, evt):
        # Need to check this, because apparently under the hood
        # wxPython destroys and re-creates the control when you
        # edit, add or delete an entry.
        if self._finito:
            print("Result:", self.Choices)


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dEditableList_test)
