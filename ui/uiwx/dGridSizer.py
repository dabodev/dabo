import wx
import dabo
import dPemMixin
import dSizerMixin
from dabo.dLocalize import _

class dGridSizer(wx.GridBagSizer, dSizerMixin.dSizerMixin):
	_IsContainer = False
	
	def __init__(self, vgap=3, hgap=3, maxRows=0, maxCols=0):
		wx.GridBagSizer.__init__(self, vgap=vgap, hgap=hgap)
		
		self._maxRows = 0
		self._maxCols = 0
		self._maxDimension = "c"
		if not maxRows and not maxCols:
			# No max settings were passed, so default to 2 columns
			self.MaxCols = 2
		elif maxCols:
			self.MaxCols = maxCols
		else:
			# Rows were passed.
			self.MaxRows = maxRows
		self.SetFlexibleDirection(wx.BOTH)
		# Keep track of the highest numbered row/col that
		# contains an item
		self._highRow = self._highCol = -1


	def append(self, item, layout="normal", row=-1, col=-1, 
			rowSpan=1, colSpan=1, alignment=("middle", "left"), 
			border=0, borderFlags=("all",)):
		""" Inserts the passed item at the specified position in the grid. If no
		position is specified, the item is inserted at the first available open 
		cell as specified by the Max* properties.		
		"""
		(targetRow, targetCol) = self.determineAvailableCell(row, col)
		if type(item) == type(tuple()):
			# spacer
			self.Add(item, (targetRow, targetCol) )
		else:
			# item is the window to add to the sizer
			_wxFlags = self._getWxFlags(alignment, borderFlags, layout)
			self.Add(item, (targetRow, targetCol), span=(rowSpan, colSpan), 
					flag=_wxFlags, border=border)
		
		self._highRow = max(self._highRow, targetRow)
		self._highCol = max(self._highCol, targetCol)
		
		
	def appendItems(self, items, *args, **kwargs):
		""" Shortcut for appending multiple items at once. """
		for item in items:
			self.append(item, *args, **kwargs)
	
	
	def insert(self, *args, **kwargs):
		""" This is not supported for this type of sizer """
		return False
	
	
	def removeRow(self, rowNum):
		""" Deletes any items contained in the specified row, and
		then moves all items below it up to fill the space.
		"""
		for c in range(self._highCol):
			szitm = self.FindItemAtPosition( (rowNum, c) )
			if not szitm:
				continue
			itm = None
			if szitm.IsWindow():
				itm = szitm.GetWindow()
				self.Remove(itm)
				itm.Destroy()
			elif szitm.IsSpacer():
				itm = szitm.GetSpacer()
				self.Remove(itm)
		# OK, all items are removed. Now move all higher rows upward
		for r in range(rowNum+1, self._highRow+1):
			for c in range(self._highCol+1):
				self.moveCell(r, c, r-1, c, delay=True)
		self.layout()
		self._highRow -= 1
		
		
	def removeCol(self, colNum):
		""" Deletes any items contained in the specified column, and
		then moves all items below it up to fill the space.
		"""
		for r in range(self._highRow):
			szitm = self.FindItemAtPosition( (r, colNum) )
			if not szitm:
				continue
			itm = None
			if szitm.IsWindow():
				itm = szitm.GetWindow()
				self.Remove(itm)
				itm.Destroy()
			elif szitm.IsSpacer():
				itm = szitm.GetSpacer()
				self.Remove(itm)
		# OK, all items are removed. Now move all higher columns upward
		for r in range(self._highRow+1):
			for c in range(colNum+1, self._highCol+1):
				self.moveCell(r, c, r, c-1, delay=True)
		self.layout()
		self._highCol -= 1
		
		
	def setColExpand(self, expand, colNums, proportion=0):
		""" Sets the 'growable' status of one or more columns. """
		# If the colNums argument was passed first, switch it with the 
		# expand argument
		if type(expand) in (int, str):
			expand, colNums = colNums, expand
		if type(colNums) in (list, tuple):
			for col in colNums:
				self.setColExpand(expand, col, proportion)
		elif type(colNums) == str:
			if colNums.lower() == "all":
				chldrn = self.GetChildren()
				c = {}
				for chld in chldrn:
					(row, col) = chld.GetPosTuple()
					c[col] = True
				for column in c.keys():
					self.setColExpand(expand, column, proportion)
		else:
			if expand:
				self.AddGrowableCol(colNums, proportion=proportion)
			else:
				# If the col isn't growable, it will throw an error
				try:
					self.RemoveGrowableCol(colNums)
				except: pass
		self.Layout()
		
		
	def setRowExpand(self, expand, rowNums, proportion=0):
		""" Sets the 'growable' status of one or more rows. """
		# If the colNums argument was passed first, switch it with the 
		# expand argument
		if type(expand) in (int, str):
			expand, rowNums = rowNums, expand
		if type(rowNums) in (list, tuple):
			for row in rowNums:
				self.setRowExpand(expand, row, proportion)
		elif type(rowNums) == str:
			if rowNums.lower() == "all":
				chldrn = self.GetChildren()
				r = {}
				for chld in chldrn:
					(row, col) = chld.GetPosTuple()
					r[row] = True
				for row in r.keys():
					self.setRowExpand(expand, row, proportion)
		else:
			if expand:
				self.AddGrowableRow(rowNums, proportion=proportion)
			else:
				# If the row isn't growable, it will throw an error
				try:
					self.RemoveGrowableRow(rowNums)
				except: pass
		self.Layout()
		
	
	def moveCell(self, fromRow, fromCol, toRow, toCol, delay=False):
		""" Move the contents of the specified cell to the target
		location. By default, layout() is called; this can be changed when 
		moving a number of cells by specifying delay=True. In this
		event, the calling code is responsible for calling layout() when all
		the moving is done.
		"""
		sz = self.FindItemAtPosition( (fromRow, fromCol) )
		if sz:
			if sz.IsWindow():
				item = sz.GetWindow()
				self.SetItemPosition(item, (toRow, toCol) )
				if not delay:
					self.layout()

			
	def determineAvailableCell(self, row, col):
		(targetRow, targetCol) = (row, col)
		if (row == -1) or (col == -1):
			# Get the first available cell
			(emptyRow, emptyCol) = self.findFirstEmptyCell()
			if row == -1:
				targetRow = emptyRow
			if col == -1:
				targetCol = emptyCol
		return (targetRow, targetCol)
		
				
	def findFirstEmptyCell(self):
		""" The idea is this: use the MaxDimension to determine how
		we look through the grid. When we find an empty cell, return
		its coordinates.
		"""
		ret = ()
		if self.MaxDimension == "c":
			emptyRow = 0
			maxCol = max(1, self.MaxCols)
			while not ret:
				for c in range(maxCol):
					if not self.FindItemAtPosition( (emptyRow, c) ):
						# Empty!
						ret = (emptyRow, c)
						break
				emptyRow += 1
		else:
			emptyCol = 0
			maxRow = max(1, self.MaxRows)
			while not ret:
				for r in range(maxRow):
					if not self.FindItemAtPosition( (r, emptyCol) ):
						# Empty!
						ret = (r, emptyCol)
						break
				emptyCol += 1
		return ret


	def drawOutline(self, win):
		""" Need to override this method to draw the outline
		properly for the grid.
		"""
		dc = wx.ClientDC(win)
		dc.SetBrush(wx.TRANSPARENT_BRUSH)
		dc.SetLogicalFunction(wx.COPY)
		x, y = self.GetPosition()
		w, h = self.GetSize()
		rows = self.GetRows()
		cols = self.GetCols()
		vgap = self.GetVGap()
		hgap = self.GetHGap()
		x2,y2 = x,y
		rhts = self.GetRowHeights()
		dc.SetPen(wx.Pen("blue", 1, wx.SOLID))
		for hh in rhts:
			dc.DrawRectangle(x2, y2, w, hh)
			y2 += hh+vgap
		x2 = x
		y2 = y
		cwds = self.GetColWidths()
		dc.SetPen(wx.Pen("red", 1, wx.SOLID))
		for ww in cwds:
			dc.DrawRectangle(x2, y2, ww, h)
			x2 += ww+hgap
		dc.SetPen(wx.Pen("green", 3, wx.LONG_DASH))
		dc.DrawRectangle(x,y,w,h)
	
	
	def _getMaxRows(self):
		return self._maxRows
	def _setMaxRows(self, rows):
		self._maxRows = rows
		if rows:
			self.MaxDimension = "r"
			self.MaxCols = 0
		
	def _getMaxCols(self):
		return self._maxCols
	def _setMaxCols(self, cols):
		self._maxCols = cols
		if cols:
			self.MaxDimension = "c"
			self.MaxRows = 0
	
	def _getMaxDimension(self):
		return self._maxDimension
	def _setMaxDimension(self, val):
		self._maxDimension = val
		
	MaxRows = property(_getMaxRows, _setMaxRows, None,
			_("When adding elements to the sizer, controls the max number "
			"of rows to add before a new column is started. (int)") )

	MaxCols = property(_getMaxCols, _setMaxCols, None,
			_("When adding elements to the sizer, controls the max number "
			"of columns to add before a new row is started. (int)") )

	MaxDimension = property(_getMaxDimension, _setMaxDimension, None,
			_("When adding elements to the sizer, this property determines "
			" if we use rows or columns as the limiting value. (char: 'r' or 'c'(default) )") )
	
	Orientation = property(_getMaxDimension, _setMaxDimension, None, 
		"Alias for the MaxDimensions property.")
	
		
if __name__ == "__main__":
	s = dGridSizer()
