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


class Grid(dabo.ui.dGrid):
	def _afterInit(self):
		super(Grid, self)._afterInit()
		self.bizobj = None
		self._fldSpecs = None
		self.skipFields = []
		self.fieldCaptions = {}
		self.colOrders = {}
		self.built = False
		self.customSort = True


	def getDataSet(self):
		ret = self.dataSet
		if not self.inAutoSizeCalc:
			if self.bizobj:
				ret = self.dataSet = self.bizobj.getDataSet()
		return ret
	

	def populate(self):
		ds = self.getDataSet()
		if not self.built and ds:
			self.buildFromDataSet(ds, 
					keyCaption=self.fieldCaptions, 
					columnsToSkip=self.skipFields, 
					colOrder=self.colOrders)
			self.built = True
		else:
			self.fillGrid()
		

	def sort(self):
		# The superclass will have already set the sort properties.
		# We want to send those to the bizobj for sorting.
		ds1 = self.dataSet
		self.bizobj.sort(self.sortedColumn, self.sortOrder)
		
	
	def setBizobj(self, biz):
		self.bizobj = biz

	def onLeftDClick(self, evt): 
		""" Occurs when the user double-clicks a cell in the grid. 
		By default, this is interpreted as a request to edit the record.
		"""
		if self.Form.FormType == "PickList":
			self.pickRecord()
		else:
			self.editRecord()


	def processKeyPress(self, keyCode): 
		""" This is called when a key that the grid doesn't already handle
		gets pressed. We want to trap F2 and sort the column when it is
		pressed.
		"""
		if keyCode == 343:    # F2
			self.processSort()
			return True
		else:
			return super(Grid, self).processKeyPress(keyCode)


	def onEnterKeyAction(self):
		if self.Form.FormType == "PickList":
			self.pickRecord()
		else:
			self.editRecord()
	
	def onDeleteKeyAction(self):
		if self.Form.FormType != "PickList":
			self.deleteRecord()
	
	def onEscapeAction(self):
		if self.Form.FormType == "PickList":
			self.Form.close()


	def newRecord(self, evt=None):
		""" Request that a new row be added."""
		self.Parent.newRecord(self.bizobj.DataSource)


	def editRecord(self, evt=None):
		""" Request that the current row be edited."""
		self.Parent.editRecord(self.bizobj.DataSource)


	def deleteRecord(self, evt=None):
		""" Request that the current row be deleted."""
		self.Parent.deleteRecord(self.bizobj.DataSource)
		self.setFocus()  ## required or assertion happens on Gtk


	def pickRecord(self, evt=None):
		""" The form is a picklist, and the user picked a record."""
		self.Form.pickRecord()
		
		
	def popupMenu(self):
		""" Display a popup menu of relevant choices. 
		By default, the choices are 'New', 'Edit', and 'Delete'.
		"""
		popup = dabo.ui.dMenu()

		if self.Form.FormType == 'PickList':
			popup.append(_("&Pick"), bindfunc=self.pickRecord, bmp="edit",
					help=_("Pick this record"))
		else:
			popup.append(_("&New"), bindfunc=self.newRecord, bmp="blank",
					help=_("Add a new record"))
			popup.append("&Edit", bindfunc=self.editRecord, bmp="edit",
					help=_("Edit this record"))
			popup.append("&Delete", bindfunc=self.deleteRecord, bmp="delete",
					help=_("Delete this record"))
		self.PopupMenu(popup, self.mousePosition)
		popup.release()


	def _getFldSpecs(self):
		return self._fldSpecs
	def _setFldSpecs(self, val):
		self._fldSpecs = val
		# Update the props
		self.skipFields = [kk for kk in val
				if val[kk]["listInclude"] == "0" ]
		self.fieldCaptions = {}
		for kk in val.keys():
			if kk in self.skipFields:
				continue
			self.fieldCaptions[kk] = val[kk]["caption"]

		self.colOrders = {}
		for kk in val.keys():
			if kk in self.skipFields:
				continue
			self.colOrders[kk] = val[kk]["listOrder"]

	FieldSpecs = property(_getFldSpecs, _setFldSpecs, None, 
			_("Holds the fields specs for this form  (dict)") )

