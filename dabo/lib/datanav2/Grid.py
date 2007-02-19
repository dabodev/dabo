import dabo
import dabo.ui
import dabo.dException as dException
dabo.ui.loadUI("wx")
from dabo.dLocalize import _, n_
import dabo.dEvents as dEvents

class Grid(dabo.ui.dGrid):
	def _beforeInit(self, pre):
		self.customSort = True
		super(Grid, self)._beforeInit(pre)


	def _initEvents(self):
		self.super()
		self.bindEvent(dEvents.GridMouseLeftDoubleClick, self.onGridLeftDClick)
		self.bindEvent(dEvents.KeyDown, self._onGridKeyDown)


	def _afterInit(self):
		super(Grid, self)._afterInit()

		self.bindKey("f2", self._onSortKey)
		self.bindKey("delete", self._onDeleteKey)

		if hasattr(self.Form, "preview") and self.Form.preview:
			self.DataSource = self.Form.previewDataSource
		
		# Highlight the selected row for the grid
		self.SelectionMode = "Row"
		# Limit selection to a single row
		self._multipleSelection = False
		# Turn on alternate row coloring
		self.AlternateRowColoring = True


	def populate(self):
		ds = self.DataSource
		if not ds:
			# Usually, datanav grids will have a DataSource pointing to the DataSource
			# of a bizobj. However, they could also have no datasource but instead a
			# raw DataSet. This is true in minesweeper, for example.
			ds = self.DataSet
		self.refresh()


	def sort(self):
		# The superclass will have already set the sort properties.
		# We want to send those to the bizobj for sorting.
		bizobj = self.Form.getBizobj(self.DataSource)
		bizobj.sort(self.sortedColumn, self.sortOrder, self.caseSensitiveSorting)
		
	
	def onGridLeftDClick(self, evt): 
		""" Occurs when the user double-clicks a cell in the grid. 
		By default, this is interpreted as a request to edit the record.
		"""
		self.processEditRecord()

	def processEditRecord(self):
		## FormType is a prop of datanav forms. Even though we expect Grid to be 
		## part of a datanav form, let's try to make it work even out of that
		## context
		ft = getattr(self.Form, "FormType", None)
		if ft is None:
			return
		if ft == "PickList":
			self.pickRecord()
		else:
			self.editRecord()


	def _onGridKeyDown(self, evt):
		keyCode = evt.EventData["keyCode"]
		hasModifiers = evt.EventData["hasModifiers"]
		if keyCode == 13 and not hasModifiers:
			self.processEditRecord()
			evt.stop()
		elif keyCode == 27 and not hasModifiers:
			self._onEscapeKey()
			evt.stop()


	def _onDeleteKey(self, evt):
		try:
			if self.Form.FormType != "PickList":
				self.deleteRecord()
		except AttributeError:
			pass
	

	def _onSortKey(self, evt):
		self.processSort()
	

	def _onEscapeKey(self, evt=None):
		try:
			if self.Form.FormType == "PickList":
				self.Form.hide()
		except AttributeError:
			pass


	def _onNewRecord(self, evt=None):
		self.newRecord()

	def newRecord(self):
		""" Request that a new row be added."""
		self.Parent.newRecord(self.DataSource)


	def _onEditRecord(self, evt=None):
		self.editRecord()

	def editRecord(self):
		""" Request that the current row be edited."""
		self.Parent.editRecord(self.DataSource)


	def _onDeleteRecord(self, evt=None):
		self.deleteRecord()

	def deleteRecord(self):
		""" Request that the current row be deleted."""
		self.Parent.deleteRecord(self.DataSource)
		self.fillGrid(True)


	def _onPickRecord(self, evt=None):
		self.pickRecord()

	def pickRecord(self):
		""" The form is a picklist, and the user picked a record."""
		self.Form.pickRecord()
		
		
	def fillContextMenu(self, menu):
		""" Display a context menu of relevant choices.
	
		By default, the choices are 'New', 'Edit', and 'Delete'.
		"""
		try:
			if self.Form.FormType == 'PickList':
				menu.append(_("&Pick"), OnHit=self._onPickRecord, bmp="edit",
						help=_("Pick this record"))
			else:
				menu.append(_("&New"), OnHit=self._onNewRecord, bmp="blank",
						help=_("Add a new record"))
				menu.append("&Edit", OnHit=self._onEditRecord, bmp="edit",
						help=_("Edit this record"))
				menu.append("&Delete", OnHit=self._onDeleteRecord, bmp="delete",
						help=_("Delete this record"))
			return menu
		except AttributeError:
			# may not be a datanav form
			pass


