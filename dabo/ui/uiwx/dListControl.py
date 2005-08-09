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
	""" The List Control is ideal for visually dealing with data sets
	where each 'row' is a unit, where it doesn't make sense to deal
	with individual elements inside of the row. If you need to be
	able work with individual elements, you should use a grid.
	"""	

	# The mixin allows the rightmost column to expand as the 
	# control is resized. There is no way to turn that off as of now.	

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
		self._valCol = 0
		# Dictionary for tracking images by key value
		self.__imageList = {}	


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


	def selectAll(self):
		for row in range(self.RowCount):
			self.select(row)
			

	def unselectAll(self):
		for row in range(self.RowCount):
			self.unselect(row)
			
	
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
		if isinstance(tx, (list, tuple)):
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
		if row < self.RowCount:
			self.DeleteItem(row)
	
	
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
			img = dabo.ui.dIcons.getIconBitmap(img)
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
		ret = GetItem(itm).GetImage()
		return ret
		
	
	def __onSelection(self, evt):
		self._selIndex = evt.GetIndex()
		# Call the default Hit code
		self._onWxHit(evt)
	
	def onHit(self, evt): pass
	
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
		
	def _getValue(self):
		ret = None
		try:
			ret = self.GetItem(self._selIndex, self._valCol).GetText()
		except: pass
		return ret
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
		indxs = self._getSelected()
		for idx in indxs:
			try:
				ret.append(self.GetItem(idx, self._valCol).GetText())
			except: pass
		return ret
	
	def _getValCol(self):
		return self._valCol
	def _setValCol(self, val):
		self._valCol = val
		

	ColumnCount = property(_getColCount, None, None, 
			_("Number of columns in the control (read-only).  (int)") )

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
			


class _dListControl_test(dListControl):
	def afterInit(self):
		self.setColumns( ("Main Column", "Another Column") )
		self.setColumnWidth(0, 150)
		self.append( ("Second Line", "222") )
		self.append( ("Third Line", "333") )
		self.append( ("Fourth Line", "444") )
		self.insert( ("First Line", "111") )

	def initProperties(self):
		self.Width = 275
		self.Height = 200
		
	def onHit(self, evt):
		print "HIT!", self.Value

			
if __name__ == "__main__":
	import test
	test.Test().runTest(_dListControl_test)
