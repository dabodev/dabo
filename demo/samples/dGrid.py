# -*- coding: utf-8 -*-
import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import datetime


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dColumn
from dabo.ui import dGridSizer
from dabo.ui import dRadioList
from dabo.ui import dButton
from dabo.ui import dSpinner
from dabo.ui import dLine
from dabo.ui import dCheckBox

dGrid = dabo.ui.dGrid


class DemoGrid(dGrid):
    def initProperties(self):
        thisYear = datetime.datetime.now().year
        self.DataSet = [
            {
                "name": "Ed Leafe",
                "age": thisYear - 1957,
                "coder": True,
                "color": "cornsilk",
            },
            {
                "name": "Paul McNett",
                "age": thisYear - 1969,
                "coder": True,
                "color": "wheat",
            },
            {
                "name": "Ted Roche",
                "age": thisYear - 1958,
                "coder": True,
                "color": "goldenrod",
            },
            {
                "name": "Derek Jeter",
                "age": thisYear - 1974,
                "coder": False,
                "color": "white",
            },
            {
                "name": "Halle Berry",
                "age": thisYear - 1966,
                "coder": False,
                "color": "orange",
            },
            {
                "name": "Steve Wozniak",
                "age": thisYear - 1950,
                "coder": True,
                "color": "yellow",
            },
            {
                "name": "LeBron James",
                "age": thisYear - 1984,
                "coder": False,
                "color": "gold",
            },
            {
                "name": "Madeline Albright",
                "age": thisYear - 1937,
                "coder": False,
                "color": "red",
            },
        ]
        self.Editable = False

    def afterInit(self):
        col = dColumn(
            self,
            Name="Geek",
            Order=10,
            DataField="coder",
            DataType="bool",
            Width=60,
            Caption="Geek?",
            Sortable=False,
            Searchable=False,
            Editable=True,
        )
        self.addColumn(col)

        #         col.CustomRenderers[1] = col.stringRendererClass
        #         col.CustomEditors[1] = col.stringEditorClass
        col.HeaderFontBold = False

        col = dColumn(
            self,
            Name="Person",
            Order=20,
            DataField="name",
            DataType="string",
            Width=200,
            Caption="Celebrity Name",
            Sortable=True,
            Searchable=True,
            Editable=True,
            Expand=False,
        )
        self.addColumn(col)

        col.HeaderFontItalic = True
        col.HeaderBackColor = "peachpuff"
        col.HeaderVerticalAlignment = "Top"
        col.HeaderHorizontalAlignment = "Left"

        self.addColumn(
            Name="Age",
            Order=30,
            DataField="age",
            DataType="integer",
            Width=40,
            Caption="Age",
            Sortable=True,
            Searchable=True,
            Editable=True,
        )

        col = dColumn(
            self,
            Name="Color",
            Order=40,
            DataField="color",
            DataType="string",
            Width=40,
            Caption="Favorite Color",
            Sortable=True,
            Searchable=True,
            Editable=True,
            Expand=False,
        )
        self.addColumn(col)

        col.ListEditorChoices = dabo.dColors.colors
        col.CustomEditorClass = col.listEditorClass

        col.HeaderVerticalAlignment = "Bottom"
        col.HeaderHorizontalAlignment = "Right"
        col.HeaderForeColor = "brown"

        self.RowLabels = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v")
        sz.appendSpacer(20)

        txt = _(
            "Click on a column's header to sort on that column. The leftmost column is set to not be sortable, though. "
            + "You can also drag the columns to re-arrange their order. Right-clicking on a column header gives you auto-size "
            + "choices. You can also drag the lines between columns or rows to manually change their size."
        )
        lbl = self.gridCaption = dLabel(self, Alignment="center", Caption=txt, WordWrap=True)
        # Keep the label 80% of the panel
        lbl.DynamicWidth = lambda: self.Width * 0.8
        lbl.FontSize -= 1

        sz.append(lbl, halign="center")
        sz.appendSpacer(15)

        self.grid = DemoGrid(self)
        sz.append(self.grid, 2, "x", border=40, borderSides=("left", "right"))
        sz.appendSpacer(20)
        gsz = dGridSizer(HGap=15)

        chk = dCheckBox(self, Caption="Allow Editing?", DataSource=self.grid, DataField="Editable")
        chk.refresh()
        gsz.append(chk, row=0, col=0)

        chk = dCheckBox(
            self,
            Caption="Show Row Labels",
            DataSource=self.grid,
            DataField="ShowRowLabels",
        )
        gsz.append(chk, row=1, col=0)
        chk.refresh()

        chk = dCheckBox(
            self,
            Caption="Size All Rows Together?",
            DataSource=self.grid,
            DataField="SameSizeRows",
        )
        gsz.append(chk, row=2, col=0)
        chk.refresh()

        chk = dCheckBox(
            self,
            Caption="Alternate Row Coloring?",
            DataSource=self.grid,
            DataField="AlternateRowColoring",
        )
        gsz.append(chk, row=3, col=0)
        chk.refresh()

        chk = dCheckBox(
            self,
            Caption="Show Cell Borders?",
            DataSource=self.grid,
            DataField="ShowCellBorders",
        )
        gsz.append(chk, row=4, col=0)
        chk.refresh()

        chk = dCheckBox(
            self,
            Caption="Allow Multiple Selection?",
            DataSource=self.grid,
            DataField="MultipleSelection",
        )
        chk.refresh()
        gsz.append(chk, row=0, col=1)

        chk = dCheckBox(
            self,
            Caption="Allow Row Resizing?",
            DataSource=self.grid,
            DataField="ResizableRows",
        )
        chk.refresh()
        gsz.append(chk, row=1, col=1)

        chk = dCheckBox(
            self,
            Caption="Allow Column Resizing?",
            DataSource=self.grid,
            DataField="ResizableColumns",
        )
        chk.refresh()
        gsz.append(chk, row=2, col=1)

        chk = dCheckBox(
            self,
            Caption="Vertical Headers?",
            DataSource=self.grid,
            DataField="VerticalHeaders",
        )
        chk.refresh()
        gsz.append(chk, row=3, col=1)

        chk = dCheckBox(
            self,
            Caption="Auto-adjust Header Height?",
            DataSource=self.grid,
            DataField="AutoAdjustHeaderHeight",
        )
        chk.refresh()
        gsz.append(chk, row=4, col=1)

        radSelect = dRadioList(
            self,
            Choices=["Row", "Col", "Cell"],
            ValueMode="string",
            Caption="Sel Mode",
            DataSource=self.grid,
            DataField="SelectionMode",
        )
        radSelect.refresh()
        gsz.append(radSelect, row=0, col=2, rowSpan=5)

        lbl = dLabel(self, Caption="Sort Indicator Size")
        spnSort = dSpinner(
            self,
            Min=2,
            Max=20,
            DataSource=self.grid,
            DataField="SortIndicatorSize",
            OnHit=self.onSortSizeChange,
        )
        gsz.append(lbl, row=0, col=3)
        gsz.append(spnSort, row=1, col=3, halign="center")

        btn = dButton(self, Caption="Sort Indicator Color")
        btn.bindEvent(dEvents.Hit, self.onSetSortIndicatorColor)
        gsz.append(btn, row=3, col=3, halign="center")

        sz.append(gsz, halign="Center", border=10)
        gsz.setColExpand(True, 2)

        hsz = dSizer("h")
        lbl = dLabel(self, Caption="Col. 1 Header:")
        hsz.append(lbl)
        hsz.appendSpacer(4)
        btn = dButton(self, Caption="Text")
        btn.bindEvent(dEvents.Hit, self.onSetHeadColor)
        hsz.append(btn)
        hsz.appendSpacer(4)
        btn = dButton(self, Caption="Background")
        btn.bindEvent(dEvents.Hit, self.onSetHeadColor)
        hsz.append(btn)
        hsz.appendSpacer(40)

        lbl = dLabel(self, Caption="Selected Cells:")
        hsz.append(lbl)
        hsz.appendSpacer(4)
        btn = dButton(self, Caption="Text")
        btn.bindEvent(dEvents.Hit, self.onSetSelColor)
        hsz.append(btn)
        hsz.appendSpacer(4)
        btn = dButton(self, Caption="Background")
        btn.bindEvent(dEvents.Hit, self.onSetSelColor)
        hsz.append(btn)

        sz.appendSpacer(4)
        sz.append(dLine(self), "x", border=50, borderSides=("left", "right"))
        sz.appendSpacer(8)
        sz.append(hsz, halign="center")
        sz.appendSpacer(4)

        dabo.ui.callAfter(self.update)
        dabo.ui.callAfter(self.layout)

    def onSetHeadColor(self, evt):
        isText = evt.EventObject.Caption == "Text"
        c1 = self.grid.Columns[1]
        clr = {True: c1.HeaderForeColor, False: c1.HeaderBackColor}[isText]
        new = dabo.ui.getColor(clr)
        if new:
            if isText:
                c1.HeaderForeColor = new
            else:
                c1.HeaderBackColor = new
        self.grid.refresh()

    def onSetSelColor(self, evt):
        isText = evt.EventObject.Caption == "Text"
        clr = {True: self.grid.SelectionForeColor, False: self.grid.SelectionBackColor}[isText]
        new = dabo.ui.getColor(clr)
        if new:
            if isText:
                self.grid.SelectionForeColor = new
            else:
                self.grid.SelectionBackColor = new
        self.grid.refresh()

    def onSetSortIndicatorColor(self, evt):
        clr = self.grid.SortIndicatorColor
        new = dabo.ui.getColor(clr)
        if new:
            self.grid.SortIndicatorColor = new
        self.grid.refresh()

    def onSortSizeChange(self, evt):
        self.grid.refresh()


category = "Controls.dGrid"

overview = """
<p>The <b>dGrid</b> class is used to display (and optionally edit)
tabular data. It is highly customizable; this demo shows off many of the
properties used to control its appearance and behavior.
"""
