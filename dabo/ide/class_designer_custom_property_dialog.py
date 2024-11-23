# -*- coding: utf-8 -*-
from .. import events
from .. import ui

from ..dLocalize import _
from ..ui import dCheckBox
from ..ui import dDropdownList
from ..ui import dGridSizer
from ..ui import dLabel
from ..ui import dOkCancelDialog
from ..ui import dSizer
from ..ui import dTextBox


class ClassDesignerCustomPropertyDialog(dOkCancelDialog):
    def addControls(self):
        sz = dGridSizer(MaxCols=2, HGap=8, VGap=12)
        lbl = dLabel(self, Caption=_("Property Name"))
        self.txtPropName = dTextBox(self, SelectOnEntry=True)
        self.txtPropName.bindEvent(events.KeyChar, self.onKeyPropName)
        sz.append(lbl, halign="right")
        sz.append(self.txtPropName, "x")

        lbl = dLabel(self, Caption=_("Comment"))
        self.txtComment = dTextBox(self, SelectOnEntry=True)
        sz.append(lbl, halign="right")
        sz.append(self.txtComment, "x")

        lbl = dLabel(self, Caption=_("Default Value"))
        self.txtDefaultVal = dTextBox(
            self, SelectOnEntry=True, Value=None, OnKeyChar=self.updEnabled
        )
        self.ddType = dDropdownList(
            self, Choices=["", "string", "integer", "float", "boolean", "datetime"]
        )
        self.ddType.PositionValue = 0
        sz.append(lbl, halign="right")
        hsz = dSizer("h")
        hsz.append(self.txtDefaultVal, 1)
        hsz.append(self.ddType, halign="right", border=5, borderSides="left")
        sz.append(hsz, "x")

        self.chkGet = chk = dCheckBox(self, Alignment="right", Caption=_("Get Method"))
        self.txtGet = dTextBox(self, SelectOnEntry=True)
        sz.append(chk, halign="right")
        sz.append(self.txtGet, "x")
        chk.DataSource = self.txtGet
        chk.DataField = "Enabled"
        chk.Value = True

        self.chkSet = chk = dCheckBox(self, Alignment="right", Caption=_("Set Method"))
        self.txtSet = dTextBox(self, SelectOnEntry=True)
        sz.append(chk, halign="right")
        sz.append(self.txtSet, "x")
        chk.DataSource = self.txtSet
        chk.DataField = "Enabled"
        chk.Value = True

        self.chkDel = chk = dCheckBox(self, Alignment="right", Caption=_("Del Method"))
        self.txtDel = dTextBox(self, SelectOnEntry=True)
        sz.append(chk, halign="right")
        sz.append(self.txtDel, "x")
        chk.DataSource = self.txtDel
        chk.DataField = "Enabled"
        chk.Value = False

        sz.setColExpand(True, 1)
        self.Sizer.append1x(sz, border=12)
        self.AutoSize = False
        ui.callAfter(self.fitToSizer)
        ui.setAfter(self, "Width", 700)
        self.Caption = _("Custom Property Definition")
        self.update()

    def onKeyPropName(self, evt):
        ui.callAfter(self.createPropNames)

    def createPropNames(self):
        """Occurs when the user types anything in the Prop Name textbox."""
        pos = self.txtPropName.InsertionPosition
        propName = self.txtPropName.Value.strip()
        if not propName:
            return
        # Capitalize it
        propName = propName[0].upper() + propName[1:]
        self.txtPropName.Value = propName
        getName = "_get%s" % propName
        setName = "_set%s" % propName
        delName = "_del%s" % propName
        currGet = self.txtGet.Value.strip()
        currSet = self.txtSet.Value.strip()
        currDel = self.txtDel.Value.strip()
        if not currGet or currGet.startswith("_get"):
            self.txtGet.Value = getName
        if not currSet or currSet.startswith("_set"):
            self.txtSet.Value = setName
        if not currDel or currDel.startswith("_del"):
            self.txtDel.Value = delName
        self.txtPropName.InsertionPosition = pos
        self.refresh()

    def setData(self, dct):
        """This method receives a dict containing the various
        property values as the keys.
        """
        self.txtPropName.Value = dct["propName"]
        self.txtComment.Value = dct["comment"]
        self.txtDefaultVal.Value = dct["defaultValue"]
        self.ddType.Value = dct["defaultType"]
        if dct["getter"] is None:
            self.txtGet.Value = ""
            self.chkGet.Value = False
        else:
            self.txtGet.Value = dct["getter"]
            self.chkGet.Value = True
        if dct["setter"] is None:
            self.txtSet.Value = ""
            self.chkSet.Value = False
        else:
            self.txtSet.Value = dct["setter"]
            self.chkSet.Value = True
        if dct["deller"] is None:
            self.txtDel.Value = ""
            self.chkDel.Value = False
        else:
            self.txtDel.Value = dct["deller"]
            self.chkDel.Value = True
        self.createPropNames()
        ui.callAfter(self.refresh)

    def getData(self):
        """This method returns a dict containing the various
        property values as the keys.
        """
        ret = {}
        ret["propName"] = self.txtPropName.Value
        ret["comment"] = self.txtComment.Value
        ret["defaultValue"] = self.txtDefaultVal.Value
        ret["defaultType"] = self.ddType.Value
        if self.chkGet.Value:
            ret["getter"] = self.txtGet.Value
        else:
            ret["getter"] = None
        if self.chkSet.Value:
            ret["setter"] = self.txtSet.Value
        else:
            ret["setter"] = None
        if self.chkDel.Value:
            ret["deller"] = self.txtDel.Value
        else:
            ret["deller"] = None
        return ret

    def needDefType(self):
        ret = bool(self.txtDefaultVal.Value)
        return ret

    def updEnabled(self, evt):
        ui.callAfterInterval(500, self.setEnabled)

    def setEnabled(self):
        hasDefault = bool(self.txtDefaultVal.Value)
        self.ddType.Enabled = hasDefault
        if not hasDefault:
            # Clear the default type
            self.ddType.PositionValue = 0
