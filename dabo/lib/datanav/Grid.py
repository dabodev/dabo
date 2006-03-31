""" Grid.py

This is a grid designed to browse records of a bizobj. It is part of the 
dabo.lib.datanav subframework. It does not descend from dControlMixin at this 
time, but is self-contained. There is a dGridDataTable definition here as 
well, that defines the 'data' that gets displayed in the grid.
"""
import dabo
import dabo.ui
import dabo.dException as dException
dabo.ui.loadUI("wx")
from dabo.dLocalize import _, n_
import dabo.dEvents as dEvents

class Grid(dabo.ui.dGrid):
	def _beforeInit(self, pre):
		self._fldSpecs = None
		self.includeFields = []
		self.fieldCaptions = {}
		self.colOrders = {}
		self.built = False
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
		## enter/esc don't seem to work as bindKey's in grids:
		#self.bindKey("enter", self._onEnterKey)
		#self.bindKey("escape", self._onEscapeKey)

		if hasattr(self.Form, "preview") and self.Form.preview:
			self.DataSource = self.Form.previewDataSource
		
		# Highlight the selected row for the grid
		self._selectionMode = "Row"
		# Turn on alternate row coloring
		self.AlternateRowColoring = True

	def populate(self):
		ds = self.DataSource
		if not ds:
			# Usually, datanav grids will have a DataSource pointing to the DataSource
			# of a bizobj. However, they could also have no datasource but instead a
			# raw DataSet. This is true in minesweeper, for example.
			ds = self.DataSet

		if not self.built and ds:
			if self.FieldSpecs is not None:
				self.buildFromDataSet(ds, 
						keyCaption=self.fieldCaptions, 
						includeFields=self.includeFields, 
						colOrder=self.colOrders,
						colWidths=self.colWidths,
						colTypes=self.colTypes,
						autoSizeCols=False)
			self.built = True
		else:
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
		try:
			if self.Form.FormType == "PickList":
				self.pickRecord()
			else:
				self.editRecord()

		except AttributeError:
			## FormType is a prop of datanav forms. Even though we expect Grid to be 
			## part of a datanav form, let's try to make it work even out of that
			## context
			pass


	def _onGridKeyDown(self, evt):
		keyCode = evt.EventData["keyCode"]
		hasModifiers = evt.EventData["hasModifiers"]
		if keyCode == 13 and not hasModifiers:
			self._onEnterKey()
			evt.stop()
		elif keyCode == 27 and not hasModifiers:
			self._onEscapeKey()
			evt.stop()

	def _onEnterKey(self, evt=None):
		try:
			if self.Form.FormType == "PickList":
				self.pickRecord()
			else:
				self.editRecord()
		except AttributeError:
			pass


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


	def newRecord(self, evt=None):
		""" Request that a new row be added."""
		self.Parent.newRecord(self.DataSource)


	def editRecord(self, evt=None):
		""" Request that the current row be edited."""
		self.Parent.editRecord(self.DataSource)


	def deleteRecord(self, evt=None):
		""" Request that the current row be deleted."""
		self.Parent.deleteRecord(self.DataSource)
		self.fillGrid()


	def pickRecord(self, evt=None):
		""" The form is a picklist, and the user picked a record."""
		self.Form.pickRecord()
		
		
	def fillContextMenu(self, menu):
		""" Display a context menu of relevant choices.
	
		By default, the choices are 'New', 'Edit', and 'Delete'.
		"""
		try:
			if self.Form.FormType == 'PickList':
				menu.append(_("&Pick"), bindfunc=self.pickRecord, bmp="edit",
						help=_("Pick this record"))
			else:
				menu.append(_("&New"), bindfunc=self.newRecord, bmp="blank",
						help=_("Add a new record"))
				menu.append("&Edit", bindfunc=self.editRecord, bmp="edit",
						help=_("Edit this record"))
				menu.append("&Delete", bindfunc=self.deleteRecord, bmp="delete",
						help=_("Delete this record"))
			return menu
		except AttributeError:
			# may not be a datanav form
			pass


	def _getFldSpecs(self):
		return self._fldSpecs

	def _setFldSpecs(self, val):
		self._fldSpecs = val

		if val is None:
			return

		# Update the props
		self.includeFields = [kk for kk in val
				if val[kk]["listInclude"] == "1" ]

		self.fieldCaptions = {}
		for kk in val.keys():
			if kk not in self.includeFields:
				continue
			self.fieldCaptions[kk] = val[kk]["caption"]

		self.colOrders = {}
		for kk in val.keys():
			if kk not in self.includeFields:
				continue
			self.colOrders[kk] = int(val[kk]["listOrder"])

		self.colWidths = {}
		for kk in val.keys():
			if kk not in self.includeFields:
				continue
			self.colWidths[kk] = int(val[kk]["listColWidth"])

		self.colTypes = {}
		for kk in val.keys():
			if kk not in self.includeFields:
				continue
			self.colTypes[kk] = val[kk]["type"]


	FieldSpecs = property(_getFldSpecs, _setFldSpecs, None, 
			_("Holds the fields specs for this form  (dict)") )

