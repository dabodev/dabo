# -*- coding: utf-8 -*-
import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
dui = dabo.ui
from ClassDesignerComponents import LayoutPanel
from ClassDesignerComponents import LayoutBasePanel
from ClassDesignerComponents import LayoutSpacerPanel
from ClassDesignerComponents import LayoutSizer
from ClassDesignerComponents import LayoutBorderSizer
from ClassDesignerComponents import LayoutGridSizer


class ObjectPropertySheet(dui.dPanel):
	def afterInit(self):
		self.app = self.Application
		self.propGrid = grd = dui.dGrid(self)
		self.propGrid.bindEvent(dEvents.MouseLeftDoubleClick, self.onEdit)
		sz = self.Sizer = dui.dSizer("v")
		sz.append1x(self.propGrid)
		col = dui.dColumn(grd, Caption=_("Property Name"), Order=10,
				DataField="propName", DataType=str, Name="PropName",
				Width=100, Sortable=True)
		grd.addColumn(col)
		col = dui.dColumn(grd, Caption=_("Default Value"), Order=20,
				DataField="defaultValue",  Name="DefaultValue",
				Width=80, Sortable=False)
		grd.addColumn(col)
		col = dui.dColumn(grd, Caption=_("Comment"), Order=30,
				DataField="comment", DataType=str, Name="Comment",
				Width=200, Sortable=False)
		grd.addColumn(col)
		col = dui.dColumn(grd, Caption=_("Get"), Order=40,
				DataField="getter", DataType=bool, Name="Get", Width=40,
				Sortable=False)
		grd.addColumn(col)
		col = dui.dColumn(grd, Caption=_("Set"), Order=50,
				DataField="setter", DataType=bool, Name="Set", Width=40,
				Sortable=False)
		grd.addColumn(col)
		col = dui.dColumn(grd, Caption=_("Del"), Order=60,
				DataField="deller", DataType=bool, Name="Del", Width=40,
				Sortable=False)
		grd.addColumn(col)

		self.addButton = dui.dButton(self, Caption=_("Add"))
		self.addButton.bindEvent(dEvents.Hit, self.onAdd)
		self.editButton = dui.dButton(self, Caption=_("Edit"))
		self.editButton.bindEvent(dEvents.Hit, self.onEdit)
		self.delButton = dui.dButton(self, Caption=_("Delete"))
		self.delButton.bindEvent(dEvents.Hit, self.onDelete)
		hsz = dui.dSizer("H")
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
		self.addButton.Enabled = self.editButton.Enabled = \
				self.delButton.Enabled = not isinstance(obj,
				(LayoutPanel, LayoutBasePanel, LayoutSpacerPanel, LayoutSizer,
				LayoutBorderSizer, LayoutGridSizer))
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
		props = pd.keys()
		data = []
		for prop in props:
			data.append(pd[prop])
		self.propGrid.DataSet = data
		self.propGrid.fillGrid(True)
 		self.editButton.Enabled = self.delButton.Enabled = (len(props) > 0)

