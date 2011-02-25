# -*- coding: utf-8 -*-
import wx
import dabo
import dPemMixin
import dSizerMixin
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dGridSizer(dSizerMixin.dSizerMixin, wx.GridBagSizer):
	def __init__(self, *args, **kwargs):
		"""
		dGridSizer is a sizer that can lay out items in a virtual grid arrangement.
		Items can be placed in specific row/column positions if that position is
		unoccupied. You can specify either MaxCols or MaxRows, and then append
		items to the grid sizer; it will place them in the first open row/col
		position, until the Max* dimension is reached; after that, it starts over in
		the next row/col. This allows for easily adding items without having to
		explicitly track each one's row/col. For example, if I have a bunch of
		labels and edit controls to add, and I want them in a grid arrangement
		with labels on the left and controls on the right, I can set MaxCols to 2,
		and then append label, control, label, control, ..., and the dGridSizer
		will automatically arrange them as desired.
		"""
		self._baseClass = dGridSizer
		self._parent = None
		wx.GridBagSizer.__init__(self)	##, vgap=vgap, hgap=hgap)

		self._maxRows = 0
		self._maxCols = 0
		self._maxDimension = "c"
		self.SetFlexibleDirection(self.bothFlag)
		# Keep track of which rows/cols are set to expand.
		self._rowExpandState = {}
		self._colExpandState = {}

		properties = self._extractKeywordProperties(kwargs, {})
		if not ("MaxCols" in properties) and not ("MaxRows" in properties):
			# Default to 2 columns if nothing else specified
			properties["MaxCols"] = 2
		self.setProperties(properties)

		if kwargs:
			# Some kwargs haven't been handled.
			bad = ", ".join(kwargs.keys())
			raise TypeError(("Invalid keyword arguments passed to dGridSizer: %s") % bad)

		dSizerMixin.dSizerMixin.__init__(self, *args, **kwargs)


	def append(self, item, layout="normal", row=-1, col=-1,
			rowSpan=1, colSpan=1, alignment=None, halign="left",
			valign="middle", border=0, borderSides=("all",), flag=None):
		"""
		Inserts the passed item at the specified position in the grid. If no
		position is specified, the item is inserted at the first available open
		cell as specified by the Max* properties.
		"""
		(targetRow, targetCol) = self._determineAvailableCell(row, col)
		if isinstance(item, (tuple, int)):
			# spacer
			if isinstance(item, int):
				item = (item, item)
			szItem = self.Add(item, (targetRow, targetCol), span=(rowSpan, colSpan))
			spc = szItem.GetSpacer()
			spc._controllingSizer = self
			spc._controllingSizerItem = szItem
			szItem.ControllingSizer = self
		else:
			# item is the window to add to the sizer
			_wxFlags = self._getWxFlags(alignment, halign, valign, borderSides, layout)
			if flag:
				_wxFlags = _wxFlags | flag
			szItem = self.Add(item, (targetRow, targetCol), span=(rowSpan, colSpan),
					flag=_wxFlags, border=border)
			item._controllingSizer = self
			item._controllingSizerItem = szItem
			szItem.ControllingSizer = self
		return szItem


	def appendItems(self, items, *args, **kwargs):
		"""Shortcut for appending multiple items at once."""
		ret = []
		for item in items:
			ret.append(self.append(item, *args, **kwargs))
		return ret


	def appendSpacer(self, *args, **kwargs):
		"""Alias for append()"""
		return self.append(*args, **kwargs)


	def insert(self, *args, **kwargs):
		"""This is not supported for this type of sizer"""
		raise NotImplementedError(_("Grid Sizers do not support insert()"))


	def removeRow(self, rowNum):
		"""
		Deletes any items contained in the specified row, and
		then moves all items below it up to fill the space.
		"""
		for c in range(self.HighCol + 1):
			szitm = self.FindItemAtPosition((rowNum, c))
			if not szitm:
				continue
			itm = None
			if szitm.IsWindow():
				itm = szitm.GetWindow()
				self.remove(itm)
				itm.Destroy()
			elif szitm.IsSizer():
				szr = szitm.GetSizer()
				# Release the sizer and its contents
				self.remove(szr)
				szr.release(True)
			elif szitm.IsSpacer():
				itm = szitm.GetSpacer()
				self.remove(itm)
		# OK, all items are removed. Now move all higher rows upward
		for r in range(rowNum+1, self.HighRow+1):
			for c in range(self.HighCol+1):
				self.moveCell(r, c, r-1, c, delay=True)
		self.layout()


	def removeCol(self, colNum):
		"""
		Deletes any items contained in the specified column, and
		then moves all items to the right of it up to fill the space.
		"""
		for r in range(self.HighRow+1):
			szitm = self.FindItemAtPosition( (r, colNum) )
			if not szitm:
				continue
			itm = None
			if szitm.IsWindow():
				itm = szitm.GetWindow()
				self.remove(itm)
				itm.Destroy()
			elif szitm.IsSizer():
				szr = szitm.GetSizer()
				self.remove(szr)
				# Release the sizer and its contents
				szr.release(True)
			elif szitm.IsSpacer():
				itm = szitm.GetSpacer()
				self.remove(itm)
		# OK, all items are removed. Now move all higher columns to the left
		for r in range(self.HighRow+1):
			for c in range(colNum+1, self.HighCol+1):
				self.moveCell(r, c, r, c-1, delay=True)
		self.layout()


	def setColExpand(self, expand, colNum, proportion=0):
		"""Sets the 'growable' status of one or more columns."""
		# If the colNum argument was passed first, switch it with the
		# expand argument
		if isinstance(expand, basestring):
			expand, colNum = colNum, expand
		if isinstance(colNum, (list, tuple)):
			for col in colNum:
				self.setColExpand(expand, col, proportion)
		elif isinstance(colNum, basestring):
			if colNum.lower() == "all":
				for col in xrange(self.HighCol+1):
					self.setColExpand(expand, col, proportion)
			else:
				raise ValueError(
						_("Invalid value passed for 'colNum' parameter: '%s'. Only column numbers or the word 'all' are valid.") % colNum)
		else:
			curr = self.getColExpand(colNum)
			self._colExpandState[colNum] = expand
			if expand and not curr:
				self.AddGrowableCol(colNum, proportion=proportion)
			elif not expand and curr:
				self.RemoveGrowableCol(colNum)
		self.layout()


	def setRowExpand(self, expand, rowNum, proportion=0):
		"""Sets the 'growable' status of one or more rows."""
		# If the rowNum argument was passed first, switch it with the
		# expand argument
		if isinstance(expand, basestring):
			expand, rowNum = rowNum, expand
		if isinstance(rowNum, (list, tuple)):
			for row in rowNum:
				self.setRowExpand(expand, row, proportion)
		elif isinstance(rowNum, basestring):
			if rowNum.lower() == "all":
				for row in xrange(self.HighRow+1):
					self.setRowExpand(expand, row, proportion)
			else:
				raise ValueError(
						_("Invalid value passed for 'rowNum' parameter: '%s'. Only row numbers or the word 'all' are valid.") % rowNum)
		else:
			curr = self.getRowExpand(rowNum)
			self._rowExpandState[rowNum] = expand
			if expand and not curr:
				self.AddGrowableRow(rowNum, proportion=proportion)
			elif not expand and curr:
				self.RemoveGrowableRow(rowNum)
		self.layout()


	def setFullExpand(self):
		"""
		Convenience method for setting all columns and rows of the
		sizer to be growable. Must be called after all items are added,
		as any rows or columns added after the call will be the default
		of non-growable.
		"""
		self.setColExpand(True, "all")
		self.setRowExpand(True, "all")


	def setFullCollapse(self):
		"""
		Convenience method for setting all columns and rows of the
		sizer to not be growable.
		"""
		self.setColExpand(False, "all")
		self.setRowExpand(False, "all")


	def getRowExpand(self, row):
		"""Returns True if the specified row is growable."""
		return bool(self._rowExpandState.get(row, 0))


	def getColExpand(self, col):
		"""Returns True if the specified column is growable."""
		return bool(self._colExpandState.get(col, 0))


	def moveCell(self, fromRow, fromCol, toRow, toCol, delay=False):
		"""
		Move the contents of the specified cell to the target
		location. By default, layout() is called; this can be changed when
		moving a number of cells by specifying delay=True. In this
		event, the calling code is responsible for calling layout() when all
		the moving is done.
		"""
		sz = self.FindItemAtPosition( (fromRow, fromCol) )
		if sz:
			if sz.IsWindow():
				obj = sz.GetWindow()
				self.moveObject(obj, toRow, toCol, delay=delay)


	def moveObject(self, obj, targetRow, targetCol, delay=False):
		"""Moves the object to the given row/col if possible."""
		self.SetItemPosition(obj, (targetRow, targetCol) )
		if not delay:
			self.layout()


	def _determineAvailableCell(self, row, col):
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
		"""
		The idea is this: use the MaxDimension to determine how
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


	def getGridPos(self, obj):
		"""
		Given an object that is contained in this grid
		sizer, returns a (row,col) tuple for that item's location.
		"""
		if isinstance(obj, self.SizerItem):
			# Two of these will return None and one will return the actual object
			# The line below will return the one that is not None.
			itm = obj.GetWindow() or obj.GetSpacer() or obj.GetSizer()
		else:
			itm = obj
		return self.GetItemPosition(itm).Get()


	def getGridSpan(self, obj):
		"""
		Given an object that is contained in this grid
		sizer, returns a (row,col) tuple for that item's cell span.
		"""
		if isinstance(obj, self.SizerItem):
			szit = obj
		else:
			szit = obj.ControllingSizerItem
		try:
			row, col = szit.GetSpan()
		except wx.PyAssertionError, e:
			# Window isn't controlled by this sizer
			row, col = None, None
		return (row, col)


	def setGridSpan(self, obj, row=None, col=None):
		"""
		Given an object that is contained in this grid
		sizer, sets its span to the given values. Returns
		True if successful, or False if it fails, due to another
		item in the way.
		"""
		itm = None
		if isinstance(obj, (self.GridSizerItem, self.SizerItem)):
			itm = obj
			obj = self.getItem(obj)
		else:
			try:
				itm = obj.ControllingSizerItem
			except AttributeError:
				itm = None
		currRow, currCol = self.getGridSpan(itm)
		if row is None:
			row = currRow
		if col is None:
			col = currCol
		spn = wx.GBSpan(row, col)
		if itm is not None:
			try:
				itm.SetSpan(spn)
			except wx.PyAssertionError:
				raise dabo.ui.GridSizerSpanException(_("An item already exists in that location"))


	def _clearCells(self, obj, span, typ):
		"""
		When enlarging the row/colspan of an item, this method makes sure
		that any potentially spanned cells are either empty, or contain placeholder
		objects that can be safely removed.
		"""
		isCol = (typ.lower() == "col")
		currVal = self.getGridSpan(obj)[isCol]
		diff = span - currVal
		ret = True
		if diff > 0:
			for span in range(1, diff+1):
				if isCol:
					off = (0, span)
				else:
					off = (span, 0)
				spannedItem = self.getItemAtOffset(obj, off)
				if spannedItem is not None:
					if hasattr(spannedItem, "_placeholder"):
						spannedItem.release()
					else:
						ret = False
						break
		return ret


	def setRowSpan(self, obj, rowspan):
		"""Sets the row span, keeping the col span the same."""
		if rowspan > 1:
			if not self._clearCells(obj, rowspan, "row"):
				dabo.log.error("Cannot set RowSpan for %s; remove objects in the way first." % itm.Name)
				return
		self.setGridSpan(obj, row=rowspan)


	def setColSpan(self, obj, colspan):
		"""Sets the col span, keeping the row span the same."""
		if colspan > 1:
			if not self._clearCells(obj, colspan, "col"):
				dabo.log.error("Cannot set ColSpan for %s; remove objects in the way first." % itm.Name)
				return
		self.setGridSpan(obj, col=colspan)


	def getItemByRowCol(self, row, col, returnObject=True):
		"""
		Returns either the managed item or the sizer item at the
		given position if one exists. If not, returns None.
		"""
		ret = None
		itm = self.FindItemAtPosition((row, col))
		if (itm is not None) and returnObject:
			if itm.IsWindow():
				ret = itm.GetWindow()
			elif itm.IsSizer():
				ret = itm.GetSizer()
		else:
			# Return the sizer item itself.
			ret = itm
		return ret


	def getNeighbor(self, obj, dir):
		"""
		Returns the object adjacent to the given object. Possible
		values for 'dir' are: left, right, up, down.
		"""
		dir = dir[0].lower()
		if dir not in "lrud":
			return None
		offsets = {"l" : (0, -1), "r" : (0, 1), "u" : (-1, 0), "d" : (1, 0)}
		off = offsets[dir]
		return self.getItemAtOffset(obj, off)


	def getItemAtOffset(self, obj, off):
		"""
		Given an object and a (row, col) offset, returns
		the object at the offset position, or None if no such
		object exists.
		"""
		row, col = self.getGridPos(obj)
		newRow = row + off[0]
		newCol = col + off[1]
		return self.getItemByRowCol(newRow, newCol)


	def getItemProp(self, itm, prop):
		if not isinstance(itm, (self.SizerItem, self.GridSizerItem)):
			itm = itm.ControllingSizerItem
		ret = None
		if itm.IsWindow():
			chil = itm.GetWindow()
		else:
			chil = itm.GetSizer()
		row, col = self.getGridPos(chil)
		lowprop = prop.lower()
		if lowprop == "border":
			return itm.GetBorder()
		elif lowprop == "rowexpand":
			ret = self.getRowExpand(row)
		elif lowprop == "colexpand":
			ret = self.getColExpand(col)
		elif lowprop == "rowspan":
			ret = self.GetItemSpan(chil).GetRowspan()
		elif lowprop == "colspan":
			ret = self.GetItemSpan(chil).GetColspan()
		elif lowprop == "proportion":
			ret = itm.GetProportion()
		else:
			# Property is in the flag setting.
			flag = itm.GetFlag()
			szClass = dabo.ui.dSizer
			if lowprop == "halign":
				if flag & szClass.rightFlag:
					ret = "Right"
				elif flag & szClass.centerFlag:
					ret = "Center"
				else: 		#if flag & szClass.leftFlag:
					ret = "Left"
			elif lowprop == "valign":
				if flag & szClass.middleFlag:
					ret = "Middle"
				elif flag & szClass.bottomFlag:
					ret = "Bottom"
				else:		#if flag & szClass.topFlag:
					ret = "Top"
			elif lowprop == "expand":
				return bool(flag & szClass.expandFlag)
			elif lowprop == "bordersides":
				pdBorder = {"Bottom" : self.borderBottomFlag,
						"Left" : self.borderLeftFlag,
						"Right" : self.borderRightFlag,
						"Top" : self.borderTopFlag}
				if flag & self.borderAllFlag == self.borderAllFlag:
					ret = ["All"]
				else:
					ret = []
					for side, val in pdBorder.items():
						if (flag & val == val):
							ret.append(side)
					if not ret:
						ret = ["None"]
		if ret is None:
			print "NO PROP:", prop, itm
		return ret


	def copyGrid(self, oldGrid):
		"""
		This method takes an existing GridSizer, and moves
		the contents to the current grid. The properties of each
		cell's item are preserved, but row/column Expand settings
		must be handled separately.
		"""
		for r in range(oldGrid.HighRow+1):
			for c in range(oldGrid.HighCol+1):
				szitm = oldGrid.FindItemAtPosition( (r,c) )
				itm = oldGrid.getItem(szitm)
				if itm is None:
					continue
				f = szitm.GetFlag()
				oldGrid.remove(itm)
				self.append(itm, flag=f)


	def drawOutline(self, win, recurse=False, drawChildren=False):
		"""
		Need to override this method to draw the outline
		properly for the grid.
		"""
		self._resolveOutlineSettings()
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
		dc.SetPen(wx.Pen(self.outlineColor, self.outlineWidth, self.outlineStyle))
		for hh in rhts:
			dc.DrawRectangle(x2, y2, w, hh)
			y2 += hh+vgap
		x2 = x
		y2 = y
		cwds = self.GetColWidths()
		dc.SetPen(wx.Pen(self.outlineColor, self.outlineWidth, self.outlineStyle))
		for ww in cwds:
			dc.DrawRectangle(x2, y2, ww, h)
			x2 += ww+hgap
		dc.SetPen(wx.Pen(self.outlineColor, self.outlineWidth, self.outlineStyle))
		dc.DrawRectangle(x,y,w,h)

		for ch in self.Children:
			if ch.IsSizer():
				sz = ch.GetSizer()
				if hasattr(sz, "drawOutline"):
					sz.drawOutline(win, recurse)
			elif ch.IsWindow():
				w = ch.GetWindow()
				if isinstance(w, dabo.ui.dPageFrame):
					w = w.SelectedPage
				if hasattr(w, "Sizer") and w.Sizer:
					w.Sizer.drawOutline(w, True)


	def _getHGap(self):
		return self.GetHGap()

	def _setHGap(self, val):
		if isinstance(val, basestring):
			val = int(val)
		self.SetHGap(val)

	def _getHighCol(self):
		itms = self.ChildWindows + self.ChildSizers
		cols = [self.GetItemPosition(itm)[1] + (self.GetItemSpan(itm)[1]-1)
				for itm in itms]
		if cols:
			ret = max(cols)
		else:
			ret = -1
		return ret


	def _getHighRow(self):
		itms = self.ChildWindows + self.ChildSizers
		rows = [self.GetItemPosition(itm)[0] + (self.GetItemSpan(itm)[0]-1)
				for itm in itms]
		if rows:
			ret = max(rows)
		else:
			ret = -1
		return ret


	def _getMaxRows(self):
		return self._maxRows

	def _setMaxRows(self, rows):
		if isinstance(rows, basestring):
			rows = int(rows)
		self._maxRows = rows
		if rows:
			self.MaxDimension = "r"
			self.MaxCols = 0


	def _getMaxCols(self):
		return self._maxCols

	def _setMaxCols(self, cols):
		if isinstance(cols, basestring):
			cols = int(cols)
		self._maxCols = cols
		if cols:
			self.MaxDimension = "c"
			self.MaxRows = 0


	def _getMaxDimension(self):
		return self._maxDimension

	def _setMaxDimension(self, val):
		self._maxDimension = val


	def _getVGap(self):
		return self.GetVGap()

	def _setVGap(self, val):
		if isinstance(val, basestring):
			val = int(val)
		self.SetVGap(val)


	HGap = property(_getHGap, _setHGap, None,
			_("Horizontal gap between cells in the sizer  (int)"))

	HighCol = property(_getHighCol, None, None,
			_("Highest col position that contains any item. Read-only.  (int)"))

	HighRow = property(_getHighRow, None, None,
			_("Highest row position that contains any item. Read-only.  (int)"))

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
			_("Alias for the MaxDimensions property. (char: 'r' or 'c'(default) )") )

	VGap = property(_getVGap, _setVGap, None,
			_("Vertical gap between cells in the sizer  (int)"))


	DynamicHGap = makeDynamicProperty(HGap)
	DynamicMaxRows = makeDynamicProperty(MaxRows)
	DynamicMaxCols = makeDynamicProperty(MaxCols)
	DynamicMaxDimension = makeDynamicProperty(MaxDimension)
	DynamicOrientation = makeDynamicProperty(Orientation)
	DynamicVGap = makeDynamicProperty(VGap)


if __name__ == "__main__":
	s = dGridSizer()
