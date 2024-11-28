# -*- coding: utf-8 -*-
import sys

if __name__ == "__main__":
    sys.exit("This isn't meant to be run stand-alone. Please run ide/ClassDesigner.py instead.")
import os
import time

from ... import application
from ... import ui
from ... import events
from ...application import dApp
from ...dLocalize import _
from ...ide.class_designer_components import LayoutSizer
from ...ide.class_designer_components import LayoutGridSizer
from ...ui.dialogs import Wizard as Wizard
from ...ui.dialogs import WizardPage as WizardPage
from . import qlw_image_data as ImageData


class PgConnectionSelect(WizardPage):
    def createBody(self):
        self.Caption = _("Select Data Connection")
        self.HorizontalScroll = False
        sz = self.Sizer
        sz.DefaultBorder = 16
        sz.DefaultBorderTop = sz.DefaultBorderLeft = sz.DefaultBorderRight = True
        sz.DefaultBorderBottom = False
        sz.appendSpacer(1)
        sz.DefaultBorderTop = False

        gsz = ui.dGridSizer(MaxCols=2)
        lbl = ui.dLabel(self, Caption=_("Select a Connection:"))
        dd = self.ddNames = ui.dListBox(
            self, RegID="ddName", DataSource="form", DataField="ConnectionName"
        )
        gsz.appendItems((lbl, dd))
        lbl = ui.dLabel(self, Caption=_("-or-"))
        gsz.append(lbl, colSpan=2, halign="center")

        lbl = ui.dLabel(self, Caption=_("Open a Connection File:"))
        btn = ui.dButton(self, Caption=_("Select..."), RegID="btnFile")
        gsz.appendItems((lbl, btn))
        btn.bindEvent(events.Hit, self.onFileSelect)
        lbl = ui.dLabel(self, Caption=_("-or-"))
        gsz.append(lbl, colSpan=2, halign="center")

        lbl = ui.dLabel(self, Caption=_("New Connection File:"))
        btn = ui.dButton(self, Caption=_("Create..."), RegID="btnCreate")
        btn.bindEvent(events.Hit, self.onFileCreate)
        gsz.appendItems((lbl, btn))
        if self.Application.Platform == "GTK":
            # Gtk does not allow a modal form to invoke another modal form.
            btn.Enabled = False
            btn.Caption = _(" Not available in Gtk ")
            btn.FontSize -= 2
            btn.FontItalic = True

        sz.append1x(gsz)
        sz.appendSpacer(1)
        self.layout()

    def onEnterPage(self, dir):
        self.populateConnNames()

    def onLeavePage(self, dir):
        # This will return False if the connection cannot be made.
        if not self.Wizard.ConnectionName:
            ui.stop(_("You must select a connection before proceeding."))
            return False
        return self.Wizard.makeConnection()

    def populateConnNames(self):
        dd = self.ddNames
        dd.DataField = ""
        connNames = self.Application.getConnectionNames()
        dd.Choices = connNames
        ui.setAfter(dd, "DataField", "ConnectionName")
        if connNames:
            ui.setAfter(dd, "PositionValue", 0)
        dd.refresh()

    def setConnectionNames(self, names):
        self.ddNames.Choices = names
        self.ddNames.PositionValue = 0
        self._connectionName = self.ddName.StringValue

    def afterInit(self):
        self._connectionName = ""

    def onFileSelect(self, evt):
        f = ui.getFile("cnxml", message=_("Select the connection file to use"))
        if not f:
            # User canceled
            return
        self.Form.ConnectionFile = f
        self.Application.addConnectFile(f)
        self.populateConnNames()

    def onFileCreate(self, evt):
        """Run the Connection Editor"""
        from CxnEditor import EditorForm

        frm = EditorForm(self.Form)
        frm.bindEvent(events.Close, self.onCxnClose)
        frm.newFile()
        frm.show()

    def onCxnClose(self, evt):
        frm = evt.EventObject
        self.Form.ConnectionFile = frm.connFile
        self.Application.addConnectFile(frm.connFile)
        self.populateConnNames()
        self.ddNames.StringValue = frm.currentConn


class PgSelect(WizardPage):
    def createBody(self):
        self.Caption = _("Select Fields to Add")
        self._currTable = None

        sz = self.Sizer
        sz.appendSpacer(16)
        lbl = ui.dLabel(self, Caption=_("Select Table:"))
        tb = self.tblSelector = ui.dDropdownList(self)
        tbls = list(self.Wizard.DE.keys())
        tbls.sort()
        tb.Choices = tbls
        tb.PositionValue = 0
        tb.bindEvent(events.Hit, self.onTableSelection)

        hsz = ui.dSizer("h", DefaultSpacing=12)
        hsz.append(lbl)
        hsz.append(tb)
        sz.append(hsz, alignment="center")
        sz.appendSpacer(16)

        # Now create the field list, and populate it with the
        # selected table's fields
        lbl = ui.dLabel(self, Caption=_("Fields:"))
        sz.append(lbl, 0, alignment="left")
        lst = self.lstFields = ui.dListControl(self, MultipleSelect=True)
        lst.ValueColumn = 2
        lst.setColumns((_("PK"), _("Type"), _("Name")))
        lst.setColumnWidth(0, 30)
        sz.append(lst, 1, "x")
        sz.appendSpacer(16)
        btnSz = ui.dSizer("h")
        btnSz.DefaultSpacing = 10
        btnAll = ui.dButton(self, Caption=_("Select All"))
        btnAll.bindEvent(events.Hit, self.onSelectAll)
        btnSz.append(btnAll, 1, "x")
        btnNone = ui.dButton(self, Caption=_("Select None"))
        btnNone.bindEvent(events.Hit, self.onSelectNone)
        btnSz.append(btnNone, 1, "x")
        sz.append(btnSz, 0, "x")
        sz.appendSpacer(20)

        self.onTableSelection(None)

    def onEnterPage(self, dir):
        dd = self.tblSelector
        chc = dd.Choices
        # jfcs 03/01/07 sort the keys to display tables in an order
        chc.sort()
        keys = list(self.Wizard.DE.keys())
        # jfcs 03/01/07 sort the keys to display tables in an order
        keys.sort()
        if chc != keys:
            # DE has changed
            dd.Choices = keys
            dd.PositionValue = 0
            self.onTableSelection(None)

    def onTableSelection(self, evt):
        """Populate the field list control with a list of the fields in the
        selected table.
        """
        self._currTable = self.tblSelector.Value
        if not self._currTable:
            return
        self.lstFields.clear()
        # Create the items for the list
        fldDict = self.Wizard.DE[self._currTable]
        flds = list(fldDict.keys())
        flds.sort()
        pktext = {True: "X", False: ""}
        typeText = {
            "C": "char",
            "I": "int",
            "M": "text",
            "D": "date",
            "L": "blob",
            "T": "datetime",
            "B": "bool",
            "N": "float",
            "E": "enum",
            "F": "float",
            "G": "long",
            "?": "unknown",
        }
        fldInfo = [(pktext[fldDict[p]["pk"]], typeText[fldDict[p]["type"]], p) for p in flds]
        self.lstFields.appendRows(fldInfo)

    def onSelectAll(self, evt):
        self.lstFields.selectAll()

    def onSelectNone(self, evt):
        self.lstFields.unselectAll()

    def onLeavePage(self, dir):
        selFlds = self.lstFields.Values
        selTbl = self._currTable
        if dir == "forward":
            # Make sure that they selected something
            if not (selFlds) or not (selTbl):
                ui.info(_("Please select something first."))
                return False
        self.Wizard.flds = selFlds
        self.Wizard.tbl = selTbl


class PgLayout(WizardPage):
    def createBody(self):
        self.Caption = _("Layout Selection")
        self.layouts = []
        # select a layout type
        lt = self.layoutType = ui.dListBox(self, Height=160, ValueMode="Position")
        lt.bindEvent(events.Hit, self.onLayoutSelect)

        # Define images for each layout. They will be
        # accessed by position relative to the choices
        # in the dripdown list
        self.imgs = (
            ui.imageFromData(ImageData.getLayoutLabelLeftData()),
            ui.imageFromData(ImageData.getLayoutLabelTopData()),
            ui.imageFromData(ImageData.getLayoutGridData()),
        )
        img = self.layoutImg = ui.dImage(self, Width=200)

        sz = self.Sizer
        sz.append(lt, 0, "x")
        sz.appendSpacer(20)
        sz.append(img, 1, alignment="center")

    def onLayoutSelect(self, evt=None):
        self.Wizard.layoutType = self.Wizard.availableLayouts[self.layoutType.Value]
        self.layoutImg.Picture = self.imgs[self.layoutType.Value]
        self.layout()

    def onEnterPage(self, dir):
        layouts = self.Wizard.availableLayouts
        if len(self.Wizard.flds) == 1:
            layouts.remove("Grid")
        self.layoutType.Choices = layouts
        if dir == "forward":
            self.layoutType.Value = 0
            self.onLayoutSelect()


class PgOrdering(WizardPage):
    def createBody(self):
        self.Caption = _("Order Fields")

        #         lbl = ui.dLabel(self, Caption="""Select a field, and then use the buttons
        # to change its order""")
        fs = self.fldSorter = ui.dEditableList(
            self,
            Caption=_("Set the field order"),
            Editable=False,
            CanDelete=False,
            CanAdd=False,
        )
        fs.Height = 300
        #         self.Sizer.append(lbl, 0, "x", alignment="right")
        self.Sizer.append(fs, 0, "x")

    def onEnterPage(self, dir):
        self.fldSorter.Choices = self.Wizard.flds

    def onLeavePage(self, dir):
        if dir == "forward":
            self.Wizard.flds = self.fldSorter.Choices


class PgSample(WizardPage):
    def createBody(self):
        self.Caption = _("Sample")
        self.HorizontalScroll = False
        self.lastStyle = ""
        self.lastFldList = []
        self.controls = {}
        self.controlSizer = None
        self.samplePanel = None
        self.sampleWidth = None
        self.editText = None
        self.grid = None
        self._outsideBorder = 0
        self._betweenSpacing = 0
        self._columnSpacing = 0
        self._labelAlignment = "Left"
        self._labels = []
        self._layoutControls = []
        self._controlSizer = None
        self._useColons = False
        self._useTitleCase = False
        lbl = ui.dLabel(
            self,
            Caption=_("Double-click a caption to edit"),
            FontSize=8,
            FontItalic=True,
        )
        self.Sizer.append(lbl, halign="center")
        self.rClickLbl = ui.dLabel(
            self,
            Caption=_("Right-click a control to change its type"),
            FontSize=8,
            FontItalic=True,
        )
        self.Sizer.append(self.rClickLbl, halign="center", border=3, borderSides="top")
        self.samplePanel = ui.dScrollPanel(self, BackColor="papayawhip")
        itm = self.Sizer.append1x(self.samplePanel, border=3, borderSides="top")
        self.samplePanel.Sizer = LayoutSizer("v")

        # Define an editable label class
        class EditLabel(ui.dLabel):
            def afterInit(self):
                self.origCap = self.Caption
                # The label will be on the sample panel, which is on the page
                # that contains the actual event code.
                self.bindEvent(events.MouseLeftDoubleClick, self.Parent.Parent.onLblEdit)
                # Store the original caption for later reference
                ui.callAfter(self._storeCaption)

            def _storeCaption(self, cap=None):
                if cap is None:
                    cap = self.Caption
                # Save the Caption as an editing reference
                self.origCap = self.Caption

        # Save the classdef for future use
        self.editLabelClass = EditLabel

    def onEnterPage(self, dir):
        if dir != "forward":
            return
        if self.sampleWidth is None:
            self.sampleWidth = self.samplePanel.Width
        else:
            self.samplePanel.Width = self.sampleWidth
        layType = self.Wizard.layoutType
        flds = self.Wizard.flds
        if (layType == self.lastStyle) and (flds == self.lastFldList):
            # Nothing has changed
            return

        # Release all existing controls
        sc = self.controls
        for kk in list(sc.keys()):
            for vv in list(sc[kk].values()):
                if isinstance(vv, ui.dPemMixin):
                    vv.release()
        del sc
        self.controls = {}
        self._labels = []
        for ctl in self._layoutControls:
            ctl.release()
        self._layoutControls = []
        try:
            self.grid.release()
        except:
            pass
        sp = self.samplePanel
        sp.Sizer.clear()

        # Update the lastX props
        self.lastFldList = flds
        self.lastStyle = layType

        # Create the new controls
        self.rClickLbl.Visible = layType.lower() != "grid"
        if layType.lower() == "grid":
            self.makeGrid()
            return

        # See if it is label-left or label-above
        if layType.lower().find("above") > -1:
            style = "above"
            cs = self.controlSizer = LayoutSizer("v")
        else:
            style = "left"
            cs = self.controlSizer = LayoutGridSizer(MaxCols=2, HGap=0, VGap=self.BetweenSpacing)
            cs.setColExpand(True, 1)
        # Go through the list, and add the items to the sizer in order. Any
        # field which was previously created will be restored
        for fld in flds:
            cap = self._formatCaption(fld)
            lbl = self.editLabelClass(sp, Caption=cap)
            self._labels.append(lbl)
            cls = ui.dTextBox
            ctl = cls(sp)
            ctl.bindEvent(events.ContextMenu, self.onCtlRightClick)

            cs.append(lbl, halign=self.LabelAlignment)
            if style == "above":
                cs.append(ctl, "expand", borderSides="bottom")
            else:
                cs.append(ctl, "expand")
            fdc = self.controls[fld] = {}
            fdc["caption"] = fld
            fdc["label"] = lbl
            fdc["control"] = ctl
            fdc["controlClass"] = cls
            fdc["width"] = None
            if (style == "above") and not fld == flds[-1]:
                # We're not on the last field, so add a spacer
                cs.appendSpacer(self.BetweenSpacing)

        sp.Sizer.append(cs, 0, "x", border=self.OutsideBorder, borderSides="all")

        # Now create the spacer controls
        self.UseColons = False
        self.UseTitleCase = False
        self.OutsideBorder = 10
        self.BetweenSpacing = 5
        self.ColumnSpacing = 5
        gs = self._controlSizer
        if gs is None:
            gs = self._controlSizer = ui.dGridSizer(MaxCols=2)
            self.Sizer.appendSpacer(5)
            self.Sizer.append(gs, 0, halign="center")
        gs.clear()

        lbl = ui.dLabel(self, Caption=_("Outside Border:"))
        gs.append(lbl, halign="right")
        spn = ui.dSpinner(self, DataSource="self.Parent", DataField="OutsideBorder")
        spn.Value = self.OutsideBorder
        gs.append(spn)
        self._layoutControls.append(lbl)
        self._layoutControls.append(spn)

        lbl = ui.dLabel(self, Caption=_("Spacing:"))
        gs.append(lbl, halign="right")
        spn = ui.dSpinner(self, DataSource="self.Parent", DataField="BetweenSpacing")
        spn.Value = self.BetweenSpacing
        gs.append(spn)
        self._layoutControls.append(lbl)
        self._layoutControls.append(spn)

        if style == "left":
            # Add a spinner for column separation
            lbl = ui.dLabel(self, Caption=_("Column Separation:"))
            gs.append(lbl, halign="right")
            spn = ui.dSpinner(self, DataSource="self.Parent", DataField="ColumnSpacing")
            spn.Value = self.ColumnSpacing
            gs.append(spn)
            self._layoutControls.append(lbl)
            self._layoutControls.append(spn)

        lbl = ui.dLabel(self, Caption=_("Label Alignment:"))
        gs.append(lbl, halign="right")
        dd = ui.dDropdownList(self, DataSource="self.Parent", DataField="LabelAlignment")
        dd.Choices = ["Left", "Center", "Right"]
        dd.Value = self.LabelAlignment
        gs.append(dd)
        self._layoutControls.append(lbl)
        self._layoutControls.append(dd)

        lbl = ui.dLabel(self, Caption=_("Labels with Colons:"))
        gs.append(lbl, halign="right")
        chk = ui.dCheckBox(self, DataSource="self.Parent", DataField="UseColons")
        chk.Value = self.UseColons
        gs.append(chk)
        self._layoutControls.append(lbl)
        self._layoutControls.append(chk)

        lbl = ui.dLabel(self, Caption=_("Title-case Labels:"))
        gs.append(lbl, halign="right")
        chk = ui.dCheckBox(self, DataSource="self.Parent", DataField="UseTitleCase")
        chk.Value = self.UseTitleCase
        gs.append(chk)
        self._layoutControls.append(lbl)
        self._layoutControls.append(chk)

        self.refresh()
        self.samplePanel.Width = self.sampleWidth
        self.layout()

    def _formatCaption(self, cap):
        if self.UseTitleCase:
            cap = cap.title()
        if self.UseColons:
            cap = "%s:" % cap.rstrip(":")
        else:
            cap = cap.rstrip(":")
        return cap

    def onCtlRightClick(self, evt):
        self._editedControl = evt.EventObject
        pop = ui.dMenu()
        currclass = self._editedControl.__class__
        if not currclass is ui.dTextBox:
            pop.append(_("Plain Textbox"), OnHit=self.onChangeControl)
        if not currclass is ui.dDateTextBox:
            pop.append(_("Date Textbox"), OnHit=self.onChangeControl)
        if not currclass is ui.dEditBox:
            pop.append(_("Edit Box"), OnHit=self.onChangeControl)
        if not currclass is ui.dCheckBox:
            pop.append(_("Check Box"), OnHit=self.onChangeControl)
        if not currclass is ui.dSpinner:
            pop.append(_("Spinner"), OnHit=self.onChangeControl)
        self.showContextMenu(pop)
        evt.stop()

    def onChangeControl(self, evt):
        #### ALSO: need to update the wizard's fields
        #             self.editLabel.Caption = tx
        #             self.controls[self.editLabel.origCap]["caption"] = tx
        chc = evt.prompt
        classes = {
            _("Plain Textbox"): ui.dTextBox,
            _("Date Textbox"): ui.dDateTextBox,
            _("Edit Box"): ui.dEditBox,
            _("Check Box"): ui.dCheckBox,
            _("Spinner"): ui.dSpinner,
        }
        cls = classes[chc]
        obj = self._editedControl
        self._editedControl = None
        sz = obj.ControllingSizer
        isGridSz = _("above") not in self.Wizard.layoutType.lower()
        if isGridSz:
            row, col = sz.getGridPos(obj)
        else:
            pos = obj.getPositionInSizer()
        newobj = cls(obj.Parent)
        newobj.unbindEvent(events.ContextMenu)
        newobj.unbindEvent(events.MouseRightClick)
        newobj.bindEvent(events.ContextMenu, self.onCtlRightClick)
        # Update the wizard's field dict
        key = [kk for kk in list(self.controls.keys()) if self.controls[kk]["control"] is obj][0]
        self.controls[key]["control"] = newobj
        self.controls[key]["controlClass"] = cls
        sz.remove(obj, destroy=True)
        if isGridSz:
            sz.append(newobj, "expand", row=row, col=col, borderSides="bottom")
        else:
            sz.insert(pos, newobj, "expand")
        self.layout()

    def onLblEdit(self, evt):
        lbl = self.editLabel = evt.EventObject
        oldCap = lbl.Caption

        et = self.editText
        if et is None:
            et = self.editText = ui.dTextBox(self.samplePanel, SelectOnEntry=True)
            et.bindEvent(events.LostFocus, self.onEndLblEdit)
            et.bindEvent(events.KeyChar, self.onTextKey)
            et.Visible = False
        et.Value = oldCap

        et.Position = lbl.Position
        et.Width = lbl.Width + 100
        et.Visible = True
        et.SetFocus()
        ui.callAfter(et.selectAll)

    def onTextKey(self, evt):
        keyCode = evt.EventData["keyCode"]
        keys = ui.dKeys
        exit = False
        if keyCode == keys.key_Escape:
            exit = True
        elif keyCode == keys.key_Return:
            self.onEndLblEdit(evt)
        if exit:
            self.editText.Visible = False
            self.editText.Position = (-50, -50)

    def onEndLblEdit(self, evt):
        tx = self.editText.Value
        self.editLabel._storeCaption(tx)
        tx = self._formatCaption(tx)
        if tx:
            #### ALSO: need to update the wizard's fields
            self.editLabel.Caption = tx
            self.controls[self.editLabel.origCap]["caption"] = tx
            self.layout()
        self.editText.Visible = False
        self.editText.Position = (-50, -50)

    def makeGrid(self):
        frm = self.Wizard
        flds = frm.flds
        tblInfo = frm.DE[frm.tbl]
        sp = self.samplePanel
        cs = self.controlSizer
        if cs is None:
            cs = self.controlSizer = ui.dSizer("v")
        # Go through the list, and add the items to the grid as columns
        self.grid = grd = ui.dGrid(sp)

        class sampleCol(ui.dColumn):
            def afterInit(self):
                self.Width = 40

        dummyRec = {}
        for fld in flds:
            c = sampleCol(grd)
            c.Caption = fld
            c.Field = fld
            typ = tblInfo[fld]["type"]
            if typ in ("I", "N", "F"):
                dummyRec[fld] = 99
                c.DataType = int
            elif typ in ("C", "M"):
                dummyRec[fld] = _("dummy")
                c.DataType = str
            else:
                dummyRec[fld] = _("dummy")
                c.DataType = str

            grd.addColumn(c)
        # Make some dummy data
        ds = []
        for ii in range(10):
            ds.append(dummyRec)
        grd.DataSet = ds
        grd.fillGrid(True)
        grd.RowHeight = 18
        grd.processSort = self.gridProcessSort
        grd.bindEvent(events.GridHeaderMouseLeftDoubleClick, self.onHeaderDClick)

        cs.append1x(grd)
        sp.Sizer.append1x(cs, border=20, borderSides="all")
        self.layout()

    def onHeaderDClick(self, evt):
        xPos = evt.mousePosition[0]
        grid = evt.EventObject
        col = grid.Columns[grid.getColNumByX(xPos)]
        oldcap = col.Caption
        newcap = ui.getString(
            message=_("Enter a new caption:"),
            caption=_("New Caption"),
            defaultValue=oldcap,
        )
        if newcap is not None and newcap != oldcap:
            col.Caption = newcap

    def gridProcessSort(self, col):
        # Dummy method; we don't want anything to happen
        pass

    def onLeavePage(self, dir):
        if dir == "forward":
            if self.Wizard.layoutType.lower() == "grid":
                # Create the controlInfo
                inf = {}
                for col in self.grid.Columns:
                    fld = col.Field
                    inf[fld] = {
                        "caption": col.Caption,
                        "controlClass": None,
                        "width": col.Width,
                    }
                self.Wizard.controlInfo = inf
            else:
                self.Wizard.controlInfo = self.controls
        return True

    def _getBetweenSpacing(self):
        return self._betweenSpacing

    def _setBetweenSpacing(self, val):
        self._betweenSpacing = val
        cs = self.controlSizer
        if isinstance(cs, LayoutGridSizer):
            cs.VGap = val
        else:
            for itm in cs.ChildWindows:
                if not isinstance(itm, ui.dLabel):
                    cs.setItemProp(itm, "border", val)
        cs.layout()

    def _getColumnSpacing(self):
        return self._columnSpacing

    def _setColumnSpacing(self, val):
        self._columnSpacing = val
        cs = self.controlSizer
        if isinstance(cs, LayoutGridSizer):
            cs.HGap = val
        cs.layout()

    def _getLabelAlignment(self):
        return self._labelAlignment

    def _setLabelAlignment(self, val):
        self._labelAlignment = val
        for lbl in self._labels:
            lbl.ControllingSizer.setItemProp(lbl.ControllingSizerItem, "HAlign", val)

    def _getOutsideBorder(self):
        return self._outsideBorder

    def _setOutsideBorder(self, val):
        self._outsideBorder = val
        sps = self.samplePanel.Sizer
        cs = sps.Children[0]
        sps.setItemProp(cs, "Border", val)
        self.samplePanel.layout()

    def _getUseColons(self):
        return self._useColons

    def _setUseColons(self, val):
        self._useColons = val
        for lbl in self._labels:
            cap = self._formatCaption(lbl.origCap)
            lbl.Caption = cap
        self.samplePanel.layout()

    def _getUseTitleCase(self):
        return self._useTitleCase

    def _setUseTitleCase(self, val):
        self._useTitleCase = val
        for lbl in self._labels:
            cap = self._formatCaption(lbl.origCap)
            lbl.Caption = cap
        self.samplePanel.layout()

    BetweenSpacing = property(
        _getBetweenSpacing,
        _setBetweenSpacing,
        None,
        _("Spacing added between elements in pixels  (int)"),
    )

    ColumnSpacing = property(
        _getColumnSpacing,
        _setColumnSpacing,
        None,
        _("Spacing between the label and the editing control  (int)"),
    )

    LabelAlignment = property(
        _getLabelAlignment,
        _setLabelAlignment,
        None,
        _("Alignment of the labels  (enum: left, center, right)"),
    )

    OutsideBorder = property(
        _getOutsideBorder,
        _setOutsideBorder,
        None,
        _("Size of the surrounding border in pixels  (int)"),
    )

    UseColons = property(
        _getUseColons,
        _setUseColons,
        None,
        _("Do we append colons to the field labels?  (bool)"),
    )

    UseTitleCase = property(
        _getUseTitleCase,
        _setUseTitleCase,
        None,
        _("Do we title-case the field labels?  (bool)"),
    )


class PgBiz(WizardPage):
    def createBody(self):
        self.Caption = _("Bizobj Code")
        lbl = ui.dLabel(self, Alignment="Center")
        lbl.Caption = """
You can optionally have the Wizard add code
to create a business object for your selected
table. The code is fairly basic, allowing you
to customize it as needed.""".strip()
        self.Sizer.append(lbl)
        rad = ui.dRadioList(
            self,
            Caption="",
            ValueMode="Key",
            Choices=[_("Add Bizobj Code"), _("Don't Add Bizobj Code")],
            Keys=[True, False],
            DataSource=self.Form,
            DataField="createBiz",
        )
        self.Sizer.appendSpacer(10)
        self.Sizer.append(rad, halign="center")


class QuickLayoutWizard(Wizard):
    def __init__(self, parent=None):
        super(QuickLayoutWizard, self).__init__(parent=parent)
        self.Modal = True
        self.Caption = _("Add From Data Environment")
        self.Picture = "daboIcon096"
        self.Size = (520, 560)
        self._dataEnv = {}
        self._connectionName = ""
        self._connectionFile = ""
        self.callback = None
        self.controlInfo = None
        self.flds = []
        self.tbl = ""
        self.availableLayouts = [
            _("Column; labels on Left"),
            _("Column; labels above"),
            _("Grid"),
        ]
        self.layoutType = ""
        self.createBiz = True

    def start(self):
        pgs = [PgConnectionSelect, PgSelect, PgOrdering, PgLayout, PgSample, PgBiz]
        cxn = None
        if self.ConnectionName:
            cxn = self.makeConnection(showAlert=False)
        if cxn:
            # We don't need the connection selector page
            pgs.pop(0)
        elif cxn is False:
            # Error; do not proceed.
            return False
        self.append(pgs)
        super(QuickLayoutWizard, self).start()

    def makeConnection(self, showAlert=True):
        if self.ConnectionFile:
            self.Application.addConnectFile(self.ConnectionFile)
        conn = self.Application.getConnectionByName(self.ConnectionName)
        if conn.ConnectInfo.DbType == "web":
            ui.stop(_("Sorry, you cannot use web connections with this wizard."))
            return False
        try:
            crs = conn.getDaboCursor()
            self.ConnectionFile = self.Application.dbConnectionNameToFiles[self.ConnectionName]
        except Exception as e:
            if showAlert:
                ui.stop(_("Could not make connection to '%s'") % self.ConnectionName)
            return False
        self._dataEnv = dict(
            (
                (
                    tb,
                    dict(((fld[0], {"type": fld[1], "pk": fld[2]}) for fld in crs.getFields(tb))),
                )
                for tb in crs.getTables()
            )
        )
        return True

    def finish(self):
        if callable(self.callback):
            # Get the wizard info into a usable form.
            ret = {}

            de = self._dataEnv[self.tbl]
            pkFlds = [fld for fld in list(de.keys()) if de[fld]["pk"]]
            ret["pk"] = ",".join(pkFlds)
            ret["layoutType"] = self.layoutType
            ret["connectionFile"] = self.ConnectionFile
            ret["connectionName"] = self.ConnectionName
            ret["table"] = self.tbl
            ret["fields"] = self.flds
            pgSample = self.getPageByClass(PgSample)
            ret["border"] = pgSample.OutsideBorder
            ret["spacing"] = pgSample.BetweenSpacing
            ret["colspacing"] = pgSample.ColumnSpacing
            ret["labelAlignment"] = pgSample.LabelAlignment
            ret["useColons"] = pgSample.UseColons
            ret["useTitleCase"] = pgSample.UseTitleCase
            info = {}
            for fld in self.flds:
                info[fld] = {}
                info[fld]["class"] = self.controlInfo[fld]["controlClass"]
                info[fld]["caption"] = self.controlInfo[fld]["caption"]
                info[fld]["width"] = self.controlInfo[fld]["width"]
            ret["fldInfo"] = info
            ret["createBizobj"] = self.createBiz
            # ui.callAfter(self.callback, ret)
            self.callback(ret)
            self.hide()
        return False

    def setConnectionName(self, nm):
        self.ConnectionName = nm

    def _getConnectionFile(self):
        return self._connectionFile

    def _setConnectionFile(self, val):
        self._connectionFile = val

    def _getConnectionName(self):
        return self._connectionName

    def _setConnectionName(self, val):
        self._connectionName = val

    def _getDE(self):
        return self._dataEnv

    def _setDE(self, deDict):
        self._dataEnv = deDict

    ConnectionFile = property(
        _getConnectionFile,
        _setConnectionFile,
        None,
        _("Path to the connection file used to access the database  (str)"),
    )

    ConnectionName = property(
        _getConnectionName,
        _setConnectionName,
        None,
        _("Name of the connection used to access the database  (str)"),
    )

    DE = property(_getDE, _setDE, None, _("Reference to the data env dictionary   (dict)"))


if __name__ == "__main__":
    app = dApp()
    app.MainFormClass = None
    app.setup()
    wiz = QuickLayoutWizard()
    wiz.start()
