import dabo
import wx
import	wx.lib.mixins.listctrl	as ListMixin

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class dListControl(wx.ListCtrl, dcm.dDataControlMixin, 
					ListMixin.ListCtrlAutoWidthMixin):
	""" Mostly copied from the wxDemo. The mixin allows the 
	rightmost column to expand as the control is resized.
	
	This class as it stands is pretty incomplete, but it works well enough
	for the property sheet in the designer. Before including it in the
	general Dabo set of controls, we will need to streamline the adding
	of items, sorting, etc. - all the things that this control can do.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dListControl
		
		# The default is single selection. It will allow multiple selections 
		# if MultiSelect is passed as an init param.
		selType = wx.LC_SINGLE_SEL
		isMultiSel = self.extractKey(kwargs, "MultiSelect")
		if isMultiSel:
			selType = 0
		
		try:
			style = style | wx.LC_REPORT | selType
		except:
			style = wx.LC_REPORT | selType
		preClass = wx.PreListCtrl
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, style=style, *args, **kwargs)
		ListMixin.ListCtrlAutoWidthMixin.__init__(self)
		self._selIndex = 0


	def _initEvents(self):
		super(dListControl, self)._initEvents()
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.__onSelection)
		self.Bind(wx.EVT_LIST_KEY_DOWN, self.__onWxKeyDown)
		self.bindEvent(dEvents.Hit, self.onHit)
	
	
	def addColumn(self, caption):
		""" Add a column with the selected caption. """
		self.InsertColumn(self.GetColumnCount(), caption)
	
	
	def insertColumn(self, pos, caption):
		""" Inserts a column at the specified position
		with the selected caption. """
		self.InsertColumn(pos, caption)
	
	
	def setColumns(self, colList):
		""" Accepts a list/tuple of column headings, removes any
		existing columns, and creates new columns, one for each 
		element in the list"""
		self.DeleteAllColumns()
		for col in colList:
			self.addColumn(col)
			
	
	def select(self, row):
		self.SetItemState(row, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)


	def unselect(self, row):
		self.SetItemState(row, 0, wx.LIST_STATE_SELECTED)

	
	def setColumnWidth(self, col, wd):
		self.SetColumnWidth(col, wd)
	
	
	def append(self, tx, col=0, row=None):
		""" Appends a row with the associated text in the specified column.
		If the value for tx is a list/tuple, the values will be set in the columns
		starting with the passed value. If either case results in an attempt to
		add to a non-existent column, it will be ignored.
		"""
		insert = False
		if row is None:
			row = self.RowCount
			insert = True
		if type(tx) in (list, tuple):
			if insert:
				self.InsertStringItem(row, "")
			currCol = col
			for itm in tx:
				self.append(itm, currCol, row)
				currCol += 1
		else:
			if col < self.ColumnCount:
				if insert:
					self.InsertStringItem(row, "")
				self.SetStringItem(row, col, tx)
			else:
				# should we raise an error? Add the column automatically?
				pass
	
	
	def insert(self, tx, row=0, col=0):
		""" Inserts the item at the specified row, or at the beginning if no
		row is specified. Item is inserted at the specified column, as in self.append()
		"""
		self.InsertStringItem(row, "")
		self.append(tx, col, row)

	
	def __onSelection(self, evt):
		self._selIndex = evt.GetIndex()
		# Call the default Hit code
		self._onWxHit(evt)
	
	def onHit(self, evt): pass
	
	def __onWxKeyDown(self, evt):
		self.raiseEvent(dEvents.KeyDown, evt)
		
	def _getSelected(self):
		ret = []
		pos = -1
		while True:
			indx = self.GetNextItem(pos, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
			if indx == -1:
				break
			pos = indx
			ret.append(indx)
		return ret
	def _setSelected(self, selList):
		for id in selList:
			self.SetItemState(id, wx.LIST_STATE_SELECTED, 
					wx.LIST_STATE_SELECTED)

	def _getColCount(self):
		return self.GetColumnCount()
		
	def _getRowCount(self):
		return self.GetItemCount()
		
	def _getValue(self):
		ret = None
		try:
			ret = self.GetItemText(self._selIndex)
		except: pass
		return ret
	def _setValue(self, val):
		if type(val) == int:
			self.Select(val)
		elif type(val) in (str, unicode):
			self.Select(self.FindItem(-1, val))

	ColumnCount = property(_getColCount, None, None, 
			_("Number of columns in the control (read-only).  (int)") )

	RowCount = property(_getRowCount, None, None, 
			_("Number of rows in the control (read-only).  (int)") )

	SelectedIndices = property(_getSelected, _setSelected, None, 
			_("Returns a list of selected row indices.  (list of int)") )
			
	Value = property(_getValue, _setValue, None,
			_("Returns current value (str)" ) )
		
		
			
if __name__ == "__main__":
	import test
	
	class TestListControl(dListControl):
		def afterInit(self):
			self.setColumns( ("Main Column", "Another Column") )
			self.setColumnWidth(0, 150)
#			self.setColumnWidth(1, wx.LIST_AUTOSIZE)
			self.append( ("Second Line", "222") )
			self.append( ("Third Line", "333") )
			self.append( ("Fourth Line", "444") )
			self.insert( ("First Line", "111") )
		
		def onHit(self, evt):
			print "HIT!", self.Value
		
	test.Test().runTest(TestListControl)
