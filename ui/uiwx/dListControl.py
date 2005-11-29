import wx
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import wx.lib.mixins.listctrl	as ListMixin
import dControlItemMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class dListControl(wx.ListCtrl, dcm.dControlItemMixin, 
		ListMixin.ListCtrlAutoWidthMixin):
	"""Creates a list control, which is a flexible, virtual list box.

	The List Control is ideal for visually dealing with data sets where each 
	'row' is a unit, where it doesn't make sense to deal with individual 
	elements inside of the row. If you need to be	able work with individual 
	elements, you should use a dGrid.
	"""	

	# The ListMixin allows the rightmost column to expand as the 
	# control is resized. There is no way to turn that off as of now.	

	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dListControl
		
		self._lastSelectedIndex = None
		self._hitIndex = None
		self._valCol = 0

		try:
			style = style | wx.LC_REPORT
		except:
			style = wx.LC_REPORT
		preClass = wx.PreListCtrl
		dcm.dControlItemMixin.__init__(self, preClass, parent, properties, style=style, *args, **kwargs)
		ListMixin.ListCtrlAutoWidthMixin.__init__(self)
		# Dictionary for tracking images by key value
		self.__imageList = {}	


	def _initEvents(self):
		super(dListControl, self)._initEvents()
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.__onSelection)
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.__onDeselection)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.__onActivation)
		self.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.__onFocus)
		self.Bind(wx.EVT_LIST_KEY_DOWN, self.__onWxKeyDown)
	
	
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
		"""Selects the specified row. In a MultipleSelect control, any 
		other selected rows remain selected.
		"""
		if row < self.RowCount:
			self.SetItemState(row, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
		else:
			dabo.errorLog.write("An attempt was made to select a non-existent row")


	def selectOnly(self, row):
		"""Selects the specified row. In a MultipleSelect control, any 
		other selected rows are de-selected first.
		"""
		if self.MultipleSelect:
			self.unselectAll()
		self.SetItemState(row, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)


	def unselect(self, row):
		"""De-selects the specified row. In a MultipleSelect control, any 
		other selected rows remain selected.
		"""
		self.SetItemState(row, 0, wx.LIST_STATE_SELECTED)


	def selectAll(self):
		"""Selects all rows in a MultipleSelect control, or generates a 
		warning if the control is not set to MultipleSelect.
		"""
		if self.MultipleSelect:
			for row in range(self.RowCount):
				self.select(row)
		else:
			dabo.errorLog.write("'selectAll()' may only be called on List Controls that designated as MultipleSelect")
			

	def unselectAll(self):
		"""De-selects all rows."""
		for row in range(self.RowCount):
			self.unselect(row)
	# Override the default selectNone to something appropriate for this control.
	selectNone = unselectAll
	
	
	def setColumnWidth(self, col, wd):
		"""Sets the width of the specified column."""
		self.SetColumnWidth(col, wd)


	def append(self, tx, col=0, row=None):
		""" Appends a row with the associated text in the specified column.
		If the value for tx is a list/tuple, the values will be set in the columns
		starting with the passed value. If either case results in an attempt to
		add to a non-existent column, it will be ignored.
		"""
		insert = False
		new_item = None

		if row is None:
			row = self.RowCount
			insert = True
		if isinstance(tx, (list, tuple)):
			if insert:
				new_item = self.InsertStringItem(row, "")
			currCol = col
			for itm in tx:
				new_item = self.append(itm, currCol, row)
				currCol += 1
		else:
			if col < self.ColumnCount:
				if insert:
					new_item = self.InsertStringItem(row, "")
				self.SetStringItem(row, col, tx)
			else:
				# should we raise an error? Add the column automatically?
				pass
		return new_item
		
	
	def appendRows(self, seq, col=0):
		""" Accepts a list/tuple of data. Each element in the sequence
		will be another row in the control. If the data is plain text, it
		will be added in the specified column. If the data is also a 
		list/tuple, it will be appended into columns beginning with the
		specified column.
		"""
		for itm in seq:
			self.append(itm, col=col)
			
	
	def insert(self, tx, row=0, col=0):
		""" Inserts the item at the specified row, or at the beginning if no
		row is specified. Item is inserted at the specified column, as in self.append()
		"""
		self.InsertStringItem(row, "")
		self.append(tx, col, row)
	
	
	def insertRows(self, seq, row=0, col=0):
		""" Accepts a list/tuple of data. Each element in the sequence
		will be another row in the control. If the data is plain text, it
		will be inserted in the specified column at the specified row. 
		If the data is also a list/tuple, it will be inserted into columns 
		beginning with the specified column.
		"""
		for itm in seq:
			self.insert(itm, row=row, col=col)


	def removeRow(self, row):
		"""Deletes the specified row if it exists, or generates a warning
		if it does not.
		"""
		if row < self.RowCount:
			self.DeleteItem(row)
		else:
			dabo.errorLog.write("An attempt was made to remove a non-existent row")
	
	
	def clear(self):
		""" Remove all the rows in the control. """
		self.DeleteAllItems()
		
	
	# Image-handling function
	def addImage(self, img, key=None):
		""" Adds the passed image to the control's ImageList, and maintains
		a reference to it that is retrievable via the key value.
		"""
		if key is None:
			key = str(img)
		if isinstance(img, basestring):
			img = dabo.ui.strToBmp(img)
		il = self.GetImageList(wx.IMAGE_LIST_NORMAL)
		if not il:
			il = wx.ImageList(16, 16, initialCount=0)
			self.AssignImageList(il, wx.IMAGE_LIST_NORMAL)
		idx = il.Add(img)
		self.__imageList[key] = idx
		
	
	def setItemImg(self, itm, imgKey):
		""" Sets the specified item's image to the image corresponding
		to the specified key. May also optionally pass the index of the 
		image in the ImageList rather than the key.
		"""
		if isinstance(imgKey, int):
			imgIdx = imgKey
		else:
			imgIdx = self.__imageList[imgKey]
		self.SetItemImage(itm, imgIdx, imgIdx)
		self.GetItem(itm).SetImage(imgIdx)

	
	def getItemImg(self, itm):
		""" Returns the index of the specified item's image in the 
		current image list, or -1 if no image is set for the item.
		"""
		ret = self.GetItem(itm).GetImage()
		return ret
		
	
	def __onActivation(self, evt):
		self._hitIndex = evt.GetIndex()
		# Call the default Hit code
		self._onWxHit(evt)
		

	def __onFocus(self, evt):
		self.raiseEvent(dEvents.GotFocus, evt)
		

	def __onSelection(self, evt):
		self._lastSelectedIndex = evt.GetIndex()
		self.raiseEvent(dEvents.ListSelection, evt)
		
	
	def __onDeselection(self, evt):
		self.raiseEvent(dEvents.ListDeselection, evt)
		
	
	def __onWxKeyDown(self, evt):
		self.raiseEvent(dEvents.KeyDown, evt)
		
		
	def _getSelectedIndices(self):
		ret = []
		pos = -1
		while True:
			indx = self.GetNextItem(pos, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
			if indx == -1:
				break
			pos = indx
			ret.append(indx)
		return ret
		
		
	def _setSelectedIndices(self, selList):
		if self._constructed():
			self.unselectAll()
			for id in selList:
				self.SetItemState(id, wx.LIST_STATE_SELECTED, 
						wx.LIST_STATE_SELECTED)
		else:
			self._properties["SelectedIndices"] = selList
			

	def _getColCount(self):
		return self.GetColumnCount()
		
		
	def _getRowCount(self):
		return self.GetItemCount()
		
		
	def _getHitIndex(self):
		return self._hitIndex
		

	def _getLastSelectedIndex(self):
		return self._lastSelectedIndex
		

	def _getMultipleSelect(self):
		return not self._hasWindowStyleFlag(wx.LC_SINGLE_SEL)
		

	def _setMultipleSelect(self, val):
		if bool(val):
			self._delWindowStyleFlag(wx.LC_SINGLE_SEL)
		else:
			self._addWindowStyleFlag(wx.LC_SINGLE_SEL)
			

	def _getHeaderVisible(self):
		return not self._hasWindowStyleFlag(wx.LC_NO_HEADER)
		

	def _setHeaderVisible(self, val):
		if bool(val):
			self._delWindowStyleFlag(wx.LC_NO_HEADER)
		else:
			self._addWindowStyleFlag(wx.LC_NO_HEADER)
			

	def _getHorizontalRules(self, val):
		return self._hasWindowStyleFlag(wx.LC_HRULES)
		

	def _setHorizontalRules(self, val):
		if bool(val):
			self._addWindowStyleFlag(wx.LC_HRULES)
		else:
			self._delWindowStyleFlag(wx.LC_HRULES)
			

	def _getValue(self):
		item = None
		idx = self.LastSelectedIndex
		colcnt = self.ColumnCount
		vc = self.ValueColumn
		
		if idx is not None:
			if 0 <= vc <= colcnt:
				item = self.GetItem(idx, vc)
		if item is None:
			return None
		else:
			return item.GetText()
			

	def _setValue(self, val):
		if self._constructed():
			if isinstance(val, int):
				self.Select(val)
			elif isinstance(val, basestring):
				self.Select(self.FindItem(-1, val))
		else:
			self._properties["Value"] = val
			

	def _getValues(self):
		ret = []
		indxs = self.SelectedIndices
		for idx in indxs:
			try:
				item = self.GetItem(idx, self.ValueColumn)
			except TypeError:
				item = None
			if item is not None:
				ret.append(item.GetText())
		return ret
		
	
	def _getValCol(self):
		return self._valCol
	def _setValCol(self, val):
		self._valCol = val
		
		
	def _getVerticalRules(self, val):
		return self._hasWindowStyleFlag(wx.LC_VRULES)
		

	def _setVerticalRules(self, val):
		if bool(val):
			self._addWindowStyleFlag(wx.LC_VRULES)
		else:
			self._delWindowStyleFlag(wx.LC_VRULES)


	ColumnCount = property(_getColCount, None, None, 
			_("Number of columns in the control (read-only).  (int)") )

	HeaderVisible = property(_getHeaderVisible, _setHeaderVisible, None, 
			_("Specifies whether the header is shown or not."))

	HitIndex = property(_getHitIndex, None, None,
			_("Returns the index of the last hit item."))

	HorizontalRules = property(_getHorizontalRules, _setHorizontalRules, None,
			_("Specifies whether light rules are drawn between rows."))

	LastSelectedIndex = property(_getLastSelectedIndex, None, None,
			_("Returns the index of the last selected item."))

	MultipleSelect = property(_getMultipleSelect, _setMultipleSelect, None,
			_("Specifies whether multiple rows can be selected in the list."))

	RowCount = property(_getRowCount, None, None, 
			_("Number of rows in the control (read-only).  (int)") )

	SelectedIndices = property(_getSelectedIndices, _setSelectedIndices, None, 
			_("Returns a list of selected row indices.  (list of int)") )
	
	Value = property(_getValue, _setValue, None,
			_("Returns current value (str)" ) )
		
	Values = property(_getValues, None, None,
			_("Returns a list containing the Value of all selected rows  (list of str)" ) )

	ValueColumn = property(_getValCol, _setValCol, None,
			_("The column whose text is reflected in Value (default=0).  (int)") )
			
	VerticalRules = property(_getVerticalRules, _setVerticalRules, None,
			_("Specifies whether light rules are drawn between rows."))

	

class _dListControl_test(dListControl):
	def afterInit(self):
		self.setColumns( ("Main Column", "Another Column") )
		self.setColumnWidth(0, 150)
		self.append( ("The Phantom Menace", "Episode 1") )
		self.append( ("Attack of the Clones", "Episode 2") )
		self.append( ("Revenge of the Sith", "Episode 3") )
		self.insert( ("A New Hope", "Episode 4") )

	def initProperties(self):
		self.Width = 275
		self.Height = 200
		self.MultipleSelect = True
		self.HorizontalRules = True
		self.VerticalRules = True
		#self.HeaderVisible = False
		
	def onHit(self, evt):
		print "KeyValue: ", self.KeyValue
		print "PositionValue: ", self.PositionValue
		print "StringValue: ", self.StringValue
		print "Value: ", self.Value

	def onListSelection(self, evt):
		print "List Selection!", self.Value, self.LastSelectedIndex, self.SelectedIndices

	def onListDeselection(self, evt):
		print "Row deselected:", evt.EventData["index"]


if __name__ == '__main__':
	class TestForm(dabo.ui.dForm): pass
	app = dabo.dApp(MainFormClass=TestForm)
	app.setup()
	
	mf = app.MainForm
	mf.testListControl = _dListControl_test(mf)

	app.start()

