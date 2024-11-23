# -*- coding: utf-8 -*-

from ..dLocalize import _
from .. import events
from .class_designer_components import LayoutPanel
from .class_designer_components import LayoutBasePanel
from .class_designer_components import LayoutSpacerPanel
from .class_designer_components import LayoutSizer
from .class_designer_components import LayoutBorderSizer
from .class_designer_components import LayoutGridSizer

from ..ui import dButton
from ..ui import dColumn
from ..ui import dGrid
from ..ui import dPanel
from ..ui import dSizer


class ObjectPropertySheet(dPanel):
    def afterInit(self):
        self.app = self.Application
        self.propGrid = grd = dGrid(self)
        self.propGrid.bindEvent(events.MouseLeftDoubleClick, self.onEdit)
        sz = self.Sizer = dSizer("v")
        sz.append1x(self.propGrid)
        col = dColumn(
            grd,
            Caption=_("Property Name"),
            Order=10,
            DataField="propName",
            DataType=str,
            Name="PropName",
            Width=100,
            Sortable=True,
        )
        grd.addColumn(col)
        col = dColumn(
            grd,
            Caption=_("Default Value"),
            Order=20,
            DataField="defaultValue",
            Name="DefaultValue",
            Width=80,
            Sortable=False,
        )
        grd.addColumn(col)
        col = dColumn(
            grd,
            Caption=_("Comment"),
            Order=30,
            DataField="comment",
            DataType=str,
            Name="Comment",
            Width=200,
            Sortable=False,
        )
        grd.addColumn(col)
        col = dColumn(
            grd,
            Caption=_("Get"),
            Order=40,
            DataField="getter",
            DataType=bool,
            Name="Get",
            Width=40,
            Sortable=False,
        )
        grd.addColumn(col)
        col = dColumn(
            grd,
            Caption=_("Set"),
            Order=50,
            DataField="setter",
            DataType=bool,
            Name="Set",
            Width=40,
            Sortable=False,
        )
        grd.addColumn(col)
        col = dColumn(
            grd,
            Caption=_("Del"),
            Order=60,
            DataField="deller",
            DataType=bool,
            Name="Del",
            Width=40,
            Sortable=False,
        )
        grd.addColumn(col)

        self.addButton = dButton(self, Caption=_("Add"))
        self.addButton.bindEvent(events.Hit, self.onAdd)
        self.editButton = dButton(self, Caption=_("Edit"))
        self.editButton.bindEvent(events.Hit, self.onEdit)
        self.delButton = dButton(self, Caption=_("Delete"))
        self.delButton.bindEvent(events.Hit, self.onDelete)
        hsz = dSizer("H")
        hsz.append(self.addButton)
        hsz.appendSpacer(12)
        hsz.append(self.editButton)
        hsz.appendSpacer(12)
        hsz.append(self.delButton)
        sz.append(hsz, border=10)
        self.populatePropList()

    def onAdd(self, evt):
        """Add a custom property to the object."""
        self.app.editObjectProperty(None)
        self.populatePropList()

    def onEdit(self, evt):
        currProp = self.propGrid.getValue(col=0)
        self.app.editObjectProperty(currProp)
        self.populatePropList()

    def onDelete(self, evt):
        currProp = self.propGrid.getValue(col=0)
        self.app.deleteObjectProperty(currProp)
        self.populatePropList()

    def select(self, obj):
        """Called when the selected object changes."""
        if isinstance(obj, (list, tuple)):
            if len(obj) == 0:
                return
            else:
                obj = obj[0]
        self.addButton.Enabled = self.editButton.Enabled = self.delButton.Enabled = not isinstance(
            obj,
            (
                LayoutPanel,
                LayoutBasePanel,
                LayoutSpacerPanel,
                LayoutSizer,
                LayoutBorderSizer,
                LayoutGridSizer,
            ),
        )
        self.populatePropList()

    def populatePropList(self):
        """Fill the grid with the custom Properties for the selected object."""
        sel = self.app._selection
        if len(sel) == 0:
            # Nothing there yet!
            return
        elif len(sel) > 1:
            pd = {}
        else:
            obj = self.app._selection[0]
            pd = self.app._classPropDict.get(obj, {})
        props = list(pd.keys())
        data = []
        for prop in props:
            data.append(pd[prop])
        self.propGrid.DataSet = data
        self.propGrid.fillGrid(True)

        self.editButton.Enabled = self.delButton.Enabled = len(props) > 0
