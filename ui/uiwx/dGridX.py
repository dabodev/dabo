""" Grid.py

This is a grid designed to browse records of a bizobj. It is part of the 
dabo.lib.datanav subframework. It does not descend from dControlMixin at this 
time, but is self-contained. There is a dGridDataTable definition here as 
well, that defines the 'data' that gets displayed in the grid.
"""
import datetime
import wx
import wx.grid
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import dabo.dException as dException
from dabo.dLocalize import _, n_
import dControlMixin as cm
import dKeys
import dUICursors


class dGridDataTable(wx.grid.PyGridTableBase):
	def __init__(self, parent):
		super(dGridDataTable, self).__init__()

		self.grid = parent
		# This is specific to the datanav grids
# 		self.preview = self.grid.Form.preview
		self.bizobj = None		#self.grid.Form.getBizobj(parent.DataSource) 
		# Holds a copy of the current data to prevent unnecessary re-drawing
		self.__currData = []

		self.initTable()


	def initTable(self):
		self.relativeColumns = []
		self.colLabels = []
		self.colNames = []
		self.colDefs = []
		self.dataTypes = []
		self.imageBaseThumbnails = []
		self.imageLists = {}
		self.data = []
	
	
	def setColumns(self, colDefs):
		"""This method receives a list of column definitions, and creates
		the appropriate columns.
		"""
		# Column order should already be in the definition. If there is a custom
		# setting by the user, override it.
		idx = 0
		colFlds = []
		# Make a copy
		colDefs = list(colDefs)
		# See if the defs have changed. If so, clear the data to force
		# a re-draw of the table.
		if colDefs != self.colDefs:
			self.__currData = []
		for col in colDefs:
			nm = col.Field
			while not nm:
				nm = str(idx)
				idx += 1
				if nm in colFlds:
					nm = ""
			colFlds.append(nm)
			colName = "Column_%s" % nm
			pos = self.grid.Application.getUserSetting("%s.%s.%s.%s" % (
					self.grid.Form.Name, 
					self.grid.Name,
					colName,
					"ColumnOrder"))
			if pos is not None:
				colDefs.Order = pos
			# If the data types are actual types and not strings, convert
			# them to common strings.
			if type(col.DataType) == type:
				typeDict = {
						str : "string", 
						unicode : "unicode", 
						int : "integer",
						float : "float", 
						long : "long", 
						datetime.date : "date", 
						datetime.datetime : "datetime", 
						datetime.time : "time" }
				try:
					col.DataType = typeDict[col.DataType]
				except: pass
				
		# Make sure that all cols have an Order set
		for num in range(len(colDefs)):
			col = colDefs[num]
			if col.Order < 0:
				col.Order = num
		
		colDefs.sort(self.orderSort)
		self.colDefs = colDefs
		self.setColumnInfo()
		
	
	def orderSort(self, col1, col2):
		return cmp(col1.Order, col2.Order)
		
		
	def setColumnInfo(self):
		self.colLabels = [col.Caption for col in self.colDefs]
		self.dataTypes = [self.convertType(col.DataType) 
				for col in self.colDefs]
	
	
	def convertType(self, typ):
		"""Convert common types, names and abbreviations for 
		data types into the constants needed by the wx.grid.
		"""
		# Default
		ret = wx.grid.GRID_VALUE_STRING
		if type(typ) == str:
			lowtyp = typ.lower()
		else:
			lowtyp = typ
		if lowtyp in (bool, "bool", "boolean", "logical", "l"):
			ret = wx.grid.GRID_VALUE_BOOL
		if lowtyp in (int, long, "int", "integer", "bigint", "i", "long"):
			ret = wx.grid.GRID_VALUE_NUMBER
		elif lowtyp in (str, unicode, "char", "varchar", "text", "c", "s"):
			ret = wx.grid.GRID_VALUE_STRING
		elif lowtyp in (float, "float", "f"):
			ret = wx.grid.GRID_VALUE_FLOAT
		elif lowtyp in (datetime.date, datetime.datetime, datetime.time, 
				"date", "datetime", "time", "d", "t"):
			ret = wx.grid.GRID_VALUE_STRING
		return ret
		
		
	def fillTable(self, force=False):
		""" Fill the grid's data table to match the data set."""
		rows = self.GetNumberRows()
		oldRow = self.grid.CurrCol    # current row per the grid
		oldCol = self.grid.CurrCol  # current column per the grid
		if not oldCol:
			oldCol = 0

		# Get the data from the parent grid.
		dataSet = self.grid.getDataSet()
		
		if not force:
			if self.__currData == dataSet:
				# Nothing's changed; no need to re-fill the table
				return
		else:
			self.__currData = dataSet
		
		self.Clear()
		self.data = []
		for record in dataSet:
			recordDict = []
			for col in self.colDefs:
				fld = col.Field
				if record.has_key(fld):
					recordVal = record[fld]
					if col.DataType.lower() in ("string", "unicode", "str", "char", "text", "varchar"):
						# Limit to first 'n' chars...
						recordVal = str(recordVal)[:self.grid.stringDisplayLen]
					elif col.DataType.lower() == "bool":
						# coerce to bool (could have been 0/1)
						if type(recordVal) in (unicode, str):
							recordVal = bool(int(recordVal))
						else:
							recordVal = bool(recordVal)
				else:
					# If there is no such value, don't display anything
					recordVal = ""
				recordDict.append(recordVal)
			self.data.append(recordDict)
		self.grid.BeginBatch()
		# The data table is now current, but the grid needs to be
		# notified.
		if len(self.data) > rows:
			# tell the grid we've added row(s)
			num = len(self.data) - rows
			msg = wx.grid.GridTableMessage(self,         # The table
				wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,  # what we did to it
				num)                                     # how many
			
		elif rows > len(self.data):
			# tell the grid we've deleted row(s)
			num = rows - len(self.data) 
			msg = wx.grid.GridTableMessage(self,        # The table
				wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,  # what we did to it
				0,                                      # position
				num)                                    # how many
		else:
			msg = None
		if msg:        
			self.grid.ProcessTableMessage(msg)

		# Column widths come from dApp user settings, the fieldSpecs, or get sensible
		# defaults based on field type.
		idx = 0
		for col in self.colDefs:
			fld = col.Field
			colName = "Column_%s" % fld
			gridCol = idx
			fieldType = col.DataType.lower()

			# 1) Try to get the column width from the saved user settings:
			width = self.grid.Application.getUserSetting("%s.%s.%s.%s" % (
					self.grid.Form.Name, 
					self.grid.Name,
					colName,
					"Width"))

			# 2) Try to get the column width from the fieldspecs:
			if width is None:
				width = col.Width
			
			# 3) Get sensible default width if the above two methods failed:
			if width is None or (width < 0):
				# old way
				minWidth = 10 * len(col.Caption)   ## Fudge!
				
				if fieldType[:3] == "int":
					width = 50
				elif fieldType[:3] in ("num", "flo", "dou"):
					width = 75
				elif fieldType[:4] == "bool":
					width = 75
				else:
					width = 200
				width = max(width, minWidth)

			self.grid.SetColSize(gridCol, width)
			idx += 1
		self.grid.EndBatch()


	def GetTypeName(self, row, col):
		try:
			ret = self.dataTypes[col]
		except:
			ret = wx.grid.GRID_VALUE_STRING
		return ret


	# Called to determine how the data can be fetched and stored by the
	# editor and renderer.  This allows you to enforce some type-safety
	# in the grid.
	def CanGetValueAs(self, row, col, typeName):
		colType = self.dataTypes[col].split(":")[0]
		if typeName == colType:
			return True
		else:
			return False
			
			
	def CanSetValueAs(self, row, col, typeName):
		return self.CanGetValueAs(row, col, typeName)


	def MoveColumn(self, col, to):
		""" Move the column to a new position."""
		oldSort = None
		if self.grid.sortedColumn is not None:
			oldSort = self.colDefs[self.grid.sortedColumn]
		
		oldColDef = self.colDefs[col]
		del self.colDefs[col]

		if to > col:
			self.colDefs.insert(to-1, oldColDef)
		else:
			self.colDefs.insert(to, oldColDef)
			
		for col in self.colDefs:
			colOrder = self.colDefs.index(col)
			self.grid.Application.setUserSetting("%s.%s.%s.%s" % (
					self.grid.Form.Name,
					self.grid.Name,
					"Column_%s" % col[0],
					"ColumnOrder"), (colOrder * 10) )
		
		# If a column was previously sorted, update its new position in the grid
		if oldSort is not None:
			self.grid.sortedColumn = self.colDefs.index(oldSort)
		self.setColumnInfo()
		self.fillTable(True)


	# The following methods are required by the grid, to find out certain
	# important details about the underlying table.                
	def GetNumberRows(self):
		try:
			num = len(self.data)
		except:
			num = 0
		return num

	def GetNumberCols(self):
		try:
			num = len(self.colLabels)
		except:
			num = 0
		return num


	def IsEmptyCell(self, row, col):
		try:
			return not self.data[row][col]
		except IndexError:
			return True

	def GetValue(self, row, col):
		try:
			ret = self.data[row][col]
		except:
			ret = ""
		return ret

	def SetValue(self, row, col, value):
		self.data[row][col] = value



class dColumn(dabo.common.dObject):
	""" These aren't the actual columns that appear in the grid; rather,
	they provide a way to interact with the underlying grid table in a more
	straightforward manner.
	"""
	def __init__(self, parent=None):
		super(dColumn, self).__init__()
		# Normally I would make these properties, but there
		# is no need now for any getter/setter interaction, so 
		# I am naming them as if they were properties, in case 
		# we discover a need to turn them into props later on.
		self.Parent = parent
		self.Name = ""
		self.Order = -1
		self.Field = ""
		self.DataType = ""
		self.Width = 100
		self.Caption = "Column"
	


class dGrid(wx.grid.Grid, cm.dControlMixin):
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dGrid
		preClass = wx.grid.Grid
		
		# Grab the DataSet parameter if passed
		self._passedDataSet = self.extractKey(kwargs, "DataSet")
		self.dataSet = []
		
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		# List of column specs
		self.Columns = []
		
		
	def _afterInit(self):
		super(dGrid, self)._afterInit()
		self.bizobj = None
		self._hdr = None
		self.fieldSpecs = {}
		# This value is in miliseconds
		self._searchDelay = 600
		# When doing an incremental search, do we stop
		# at the nearest matching value?
		self.searchNearest = True
		# Do we do case-sensitive incremental searches?
		self.searchCaseSensitive = False
		# How many characters of strings do we display?
		self.stringDisplayLen = 64
		
		# Do we enforce that all rows are the same height? This
		# would normally be a property, but I'm making it a simple att
		# for now, since I don't see the immediate need for getter/setter
		# actions.
		self.SameSizeRows = True

		self.currSearchStr = ""
		self.incSearchTimer = dabo.ui.dTimer(self)
		self.incSearchTimer.bindEvent(dEvents.Hit, self.onSearchTimer)

		self.sortedColumn = None
		self.sortOrder = ""
		self.caseSensitiveSorting = False

		self.SetRowLabelSize(0)        # turn off row labels
		self.EnableEditing(False)      # this isn't a spreadsheet

		self.headerDragging = False    # flag used by mouse motion event handler
		self.headerDragFrom = 0
		self.headerDragTo = 0
		self.headerSizing = False

		self.bindEvent(dEvents.KeyDown, self.onKeyDown)
		self.bindEvent(dEvents.MouseLeftDoubleClick, self.onLeftDClick)
		
		self.Bind(wx.grid.EVT_GRID_ROW_SIZE, self.__onWxGridRowSize)
		self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.__onWxGridSelectCell)
		self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.__onWxColSize)
		self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.__onWxRightClick)

		self.bindEvent(dEvents.GridRowSize, self._onGridRowSize)
		self.bindEvent(dEvents.GridSelectCell, self._onGridSelectCell)
		self.bindEvent(dEvents.GridColSize, self._onGridColSize)
		self.bindEvent(dEvents.GridRightClick, self.onGridRightClick)

		self.initHeader()
		
		# If a data set was passed to the constructor, create the grid
		self.buildFromDataSet(self._passedDataSet)


	def initHeader(self):
		""" Initialize behavior for the grid header region."""
		header = self.Header

		self.Bind(wx.grid.EVT_GRID_ROW_SIZE, self.__onWxGridRowSize)

		header.Bind(wx.EVT_LEFT_DOWN, self.onHeaderLeftDown)
		header.Bind(wx.EVT_LEFT_UP, self.onHeaderLeftUp)
		header.Bind(wx.EVT_MOTION, self.onHeaderMotion)
		header.Bind(wx.EVT_PAINT, self.onHeaderPaint)


	def fillGrid(self, force=False):
		""" Refresh the grid to match the data in the data set."""
		# Save the focus, if any
		currFocus = self.FindFocus()
		# Get the default row size from dApp's user settings
		s = self.Application.getUserSetting("%s.%s.%s" % (self.Form.Name, 
				self.GetName(), "RowSize"))
		if s:
			self.SetDefaultRowSize(s)
		tbl = self._Table
# 		tbl.bizobj = self.bizobj
		
		tbl.setColumns(self.Columns)
		tbl.fillTable(force)
		
		if force:
# 			row = self.bizobj.RowNumber
			row = max(0, self.CurrRow)
			col = max(0, self.CurrCol)
			# Needed on Linux to get the grid to have the focus:
			for window in self.Children:
				window.SetFocus()
			# Needed on win and mac to get the grid to have the focus:
			self.GetGridWindow().SetFocus()
			if  not self.IsVisible(row, col):
				self.MakeCellVisible(row, col)
				self.MakeCellVisible(row, col)
			self.SetGridCursor(row, col)
		if currFocus is not None:
			try:
				currFocus.SetFocus()
			except: pass
	
	
	def buildFromDataSet(self, ds, keyCaption=None):
		"""This method will create a grid for a given data set.
		A 'data set' is a sequence of dicts, each containing field/
		value pairs. The columns will be taken from ds[0].keys(),
		with each column header being set to the key name, unless
		the optional keyCaption parameter is passed. This parameter
		is a 1:1 dict containing the data set keys as its keys,
		and the desired caption as the corresponding value.
		"""
		if not ds:
			return
		origColNum = self.ColumnCount
		self.Columns = []
		self.dataSet = ds
		firstRec = ds[0]
		colKeys = firstRec.keys()
		# Add the columns
		for colKey in colKeys:
			# Use the keyCaption values, if possible
			try:
				cap = keyCaption[colKey]
			except:
				cap = colKey
			col = dColumn(self)
			col.Caption = cap
			col.Field = colKey
			col.DataType = type(firstRec[colKey])
			# Use a default width
			col.Width = -1
			self.Columns.append(col)

		# Update the number of columns
		colChange = self.ColumnCount - origColNum 
		if colChange != 0:
			msg = ""
			if colChange < 0:
				msg = wx.grid.GridTableMessage(self._Table,
						wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
						origColNum-1, abs(colChange))
			else:
				msg = wx.grid.GridTableMessage(self._Table,
						wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED,
						colChange)
			if msg:
				self.BeginBatch()
				self.ProcessTableMessage(msg)
				self.EndBatch()
		# Populate the grid
		self.fillGrid(True)


	def getDataSet(self):
		"""Customize to your needs. Default is to use an internal property,
		and if that is empty, simply ask the form."""
		ret = self.dataSet
		if not ret:
			try:
				ret = self.Form.getDataSet()
			except:
				ret = []
		return ret
		
		
	def _onGridColSize(self, evt):
		"Occurs when the user resizes the width of the column."
		col = evt.EventData["rowOrCol"]
		fld = self._Table.colDefs[col].Field

		colName = "Column_%s" % fld
		width = self.GetColSize(col)
		
		self.Application.setUserSetting("%s.%s.%s.%s" % (
				self.Form.Name, self.Name, colName, "Width"), width)
		self.onGridColSize(evt)
	
	def onGridColSize(self, evt): pass


	def _onGridSelectCell(self, evt):
		""" Occurs when the grid's cell focus has changed."""
		oldRow = self.CurrRow
		newRow = evt.EventData["row"]
		
		if oldRow != newRow:
			if self.bizobj:
				self.bizobj.RowNumber = newRow
		self.Form.refreshControls()
		self.onGridSelectCell(evt)

	def onGridSelectCell(self, evt): pass


	def onHeaderPaint(self, evt):
		""" Occurs when it is time to paint the grid column headers.
		NOTE: The event object is a raw wx Event, not a Dabo event.
		"""
		w = self.Header
		dc = wx.PaintDC(w)
		clientRect = w.GetClientRect()
		font = dc.GetFont()

		# Thanks Roger Binns for the correction to totColSize
		totColSize = -self.GetViewStart()[0] * self.GetScrollPixelsPerUnit()[0]

		# We are totally overriding wx's drawing of the column headers,
		# so we are responsible for drawing the rectangle, the column
		# header text, and the sort indicators.
		for col in range(self.ColumnCount):
			dc.SetBrush(wx.Brush("WHEAT", wx.TRANSPARENT))
			dc.SetTextForeground(wx.BLACK)
			colSize = self.GetColSize(col)
			rect = (totColSize, 0, colSize, 32)
			dc.DrawRectangle(rect[0] - (col != 0 and 1 or 0), 
					rect[1], 
					rect[2] + (col != 0 and 1 or 0), 
					rect[3])
			totColSize += colSize


			if self.Columns[col].Field == self.sortedColumn:
				font.SetWeight(wx.BOLD)
				# draw a triangle, pointed up or down, at the top left 
				# of the column. TODO: Perhaps replace with prettier icons
				left = rect[0] + 3
				top = rect[1] + 3

				dc.SetBrush(wx.Brush("WHEAT", wx.SOLID))
				if self.sortOrder == "DESC":
					# Down arrow
					dc.DrawPolygon([(left,top), (left+6,top), (left+3,top+4)])
				elif self.sortOrder == "ASC":
					# Up arrow
					dc.DrawPolygon([(left+3,top), (left+6, top+4), (left, top+4)])
				else:
					# Column is not sorted, so don't draw.
					pass    
			else:
				font.SetWeight(wx.NORMAL)

			dc.SetFont(font)
			dc.DrawLabel("%s" % self.GetTable().colLabels[col],
					rect, wx.ALIGN_CENTER | wx.ALIGN_TOP)


	def onSearchTimer(self, evt):
		""" Occurs when the incremental search timer reaches its interval. 
		It is time to run the search, if there is any search in the buffer.
		"""
		if len(self.currSearchStr) > 0:
			self.runIncSearch()
		else:
			self.incSearchTimer.stop()


	def onHeaderMotion(self, evt):
		""" Occurs when the mouse moves in the grid header.
		NOTE: The event object is a raw wx Event, not a Dabo event.
		"""
		headerIsDragging = self.headerDragging
		headerIsSizing = self.headerSizing
		dragging = evt.Dragging()
		header = self.Header

		if dragging:
			x,y = evt.GetX(), evt.GetY()

			if not headerIsSizing and (
				self.getColByX(x) == self.getColByX(x-2) == self.getColByX(x+2)):
				if not headerIsDragging:
					# A header reposition is beginning
					self.headerDragging = True
					self.headerDragFrom = (x,y)

				else:
					# already dragging.
					begCol = self.getColByX(self.headerDragFrom[0])
					curCol = self.getColByX(x)

					# The visual indicators (changing the mouse cursor) isn't currently
					# working. It would work without the evt.Skip() below, but that is 
					# needed for when the column is resized.
					uic = dUICursors
					if begCol == curCol:
						# Give visual indication that a move is initiated
						header.SetCursor(uic.getStockCursor(uic.Cursor_Size_WE))
					else:
						# Give visual indication that this is an acceptable drop target
						header.SetCursor(uic.getStockCursor(uic.Cursor_Bullseye))
			else:
				# A size action is happening
				self.headerSizing = True


	def onHeaderLeftUp(self, evt):
		""" Occurs when the left mouse button goes up in the grid header.

		Basically, this comes down to two possibilities: the end of a drag
		operation, or a single-click operation. If we were dragging, then
		it is possible a column needs to change position. If we were clicking,
		then it is a sort operation.
		
		NOTE: The event object is a raw wx Event, not a Dabo event.
		"""
		x,y = evt.GetX(), evt.GetY()
		if self.headerDragging:
			# A drag action is ending
			self.headerDragTo = (x,y)

			begCol = self.getColByX(self.headerDragFrom[0])
			curCol = self.getColByX(x)

			if begCol != curCol:
				if curCol > begCol:
					curCol += 1
				self._Table.MoveColumn(begCol, curCol)
		elif self.headerSizing:
			pass
		else:
			# we weren't dragging, and the mouse was just released.
			# Find out the column we are in based on the x-coord, and
			# do a processSort() on that column.
			col = self.getColByX(x)
			self.processSort(col)

		self.headerDragging = False
		self.headerSizing = False


	def onHeaderLeftDown(self, evt):
		""" Occurs when the left mouse button goes down in the grid header.
		"""
		pass


	def onLeftDClick(self, evt): 
		"Occurs when the user double-clicks a cell in the grid."
		pass


	def onGridRightClick(self, evt):
		""" Occurs when the user right-clicks a cell in the grid. 
		By default, this is interpreted as a request to display the popup 
		menu, as defined in self.popupMenu().
		"""

		# Select the cell that was right-clicked upon
		self.CurrRow = evt.GetRow()
		self.CurrCol = evt.GetCol()

		# Make the popup menu appear in the location that was clicked
		self.mousePosition = evt.GetPosition()

		# Display the popup menu, if any
		self.popupMenu()


	def OnGridLabelLeftClick(self, evt):
		""" Occurs when the user left-clicks a grid column label. 

		By default, this is interpreted as a request to sort the column.
		"""
		self.processSort(evt.GetCol())
	
	
	def onEnterKeyAction(self):
		"Customize in subclasses"
		pass
		
	def onDeleteKeyAction(self):
		"Customize in subclasses"
		pass
	
	def onEscapeAction(self):
		"Customize in subclasses"
		pass
	
	def processKeyPress(self, char):
		"""Hook method for classes that need to process 
		keys in addition to Enter, Delete and Escape.
		Example:
			if keyCode == dKeys.keyStrings["f2"]:    # F2
				self.processSort()
		"""
		pass
		

	def onKeyDown(self, evt): 
		""" Occurs when the user presses a key inside the grid. 
		Default actions depend on the key being pressed:
					Enter:  edit the record
						Del:  delete the record
						F2:  sort the current column
				AlphaNumeric:  incremental search
		"""
		keyCode = evt.EventData["keyCode"]
		try:
			char = chr(keyCode)
		except ValueError:       # keycode not in ascii range
			char = None

		if keyCode == dKeys.keyStrings["enter"]:           # Enter
			self.onEnterKeyAction()
		else:
			if keyCode == dKeys.keyStrings["delete"]:      # Del
				self.onDeleteKeyAction()
			elif keyCode == dKeys.keyStrings["escape"]:
				self.onEscapeAction()
			elif char and (char.isalnum() or char.isspace()) and not evt.HasModifiers():
				self.addToSearchStr(char)
			else:
				self.processKeyPress(char)


	def processSort(self, gridCol=None):
		""" Sort the grid column.

		Toggle between ascending and descending. If the grid column index isn't 
		passed, the currently active grid column will be sorted.
		"""
		if gridCol == None:
			gridCol = self.CurrCol
		
		if isinstance(gridCol, dColumn):
			columnToSort = gridCol
			sortCol = self.Columns.index(gridCol)
		else:
			sortCol = gridCol
			columnToSort = self.Columns[gridCol].Field

		sortOrder="ASC"
		if columnToSort == self.sortedColumn:
			sortOrder = self.sortOrder
			if sortOrder == "ASC":
				sortOrder = "DESC"
			else:
				sortOrder = "ASC"
		self.sortOrder = sortOrder
		self.sortedColumn = columnToSort
		
		# Create the list to hold the rows for sorting
		caseSensitive = self.caseSensitiveSorting
		sortList = []
		for row in self.dataSet:
			sortList.append([row[columnToSort], row])
		# At this point we have a list consisting of lists. Each of these member
		# lists contain the sort value in the zeroth element, and the row as
		# the first element.
		# First, see if we are comparing strings
		sortingStrings = type(sortList[0][0]) in (str,unicode)
		if sortingStrings and not caseSensitive:
			# Use a case-insensitive sort.
			sortList.sort(lambda x, y: cmp(x[0].lower(), y[0].lower()))
		else:
			sortList.sort()

		# Unless DESC was specified as the sort order, we're done sorting
		if sortOrder == "DESC":
			sortList.reverse()
		# Extract the rows into a new list, then set the dataSet to the new list
		newRows = []
		for elem in sortList:
			newRows.append(elem[1])
		self.dataSet = newRows
		self.fillGrid()


	def runIncSearch(self):
		""" Run the incremental search.
		"""
		gridCol = self.CurrCol
		if gridCol < 0:
			gridCol = 0
		fld = self.Columns[gridCol].Field
		if self.RowCount <= 0:
			# Nothing to seek within!
			return
		newRow = self.CurrRow
		ds = self.getDataSet()
		srchStr = self.currSearchStr
		near = self.searchNearest
		caseSensitive = self.searchCaseSensitive
		# Copy the specified field vals and their row numbers to a list, and 
		# add those lists to the sort list
		sortList = []
		for i in range(0, self.RowCount):
			sortList.append( [ds[i][fld], i] )

		# Determine if we are seeking string values
		compString = type(sortList[0][0]) in (str, unicode)
		if not compString:
			# coerce srchStr to be the same type as the field type
			if type(sortList[0][0]) == int:
				try:
					srchStr = int(srchStr)
				except ValueError:
					srchStr = int(0)
			elif type(sortList[0][0]) == long:
				try:
					srchStr = long(srchStr)
				except ValueError:
					srchStr = long(0)
			elif type(sortList[0][0]) == float:
				try:
					srchStr = float(srchStr)
				except ValueError:
					srchStr = float(0)

		if compString and not caseSensitive:
			# Use a case-insensitive sort.
			sortList.sort(lambda x, y: cmp(x[0].lower(), y[0].lower()))
		else:
			sortList.sort()

		# Now iterate through the list to find the matching value. I know that 
		# there are more efficient search algorithms, but for this purpose, we'll
		# just use brute force
		for fldval, row in sortList:
			if not compString or caseSensitive:
				match = (fldval == srchStr)
			else:
				# Case-insensitive string search.
				match = (fldval.lower() == srchStr.lower())
			if match:
				newRow = row
				break
			else:
				if near:
					newRow = row
				# If we are doing a near search, see if the row is less than the
				# requested matching value. If so, update the value of 'ret'. If not,
				# we have passed the matching value, so there's no point in 
				# continuing the search, but we mu
				if compString and not caseSensitive:
					toofar = fldval.lower() > srchStr.lower()
				else:
					toofar = fldval > srchStr
				if toofar:
					break
		self.CurrRow = newRow

		# Add a '.' to the status bar to signify that the search is
		# done, and clear the search string for next time.
		self.Form.setStatusText("Search: %s." % self.currSearchStr)
		self.currSearchStr = ""


	def addToSearchStr(self, key):
		""" Add a character to the current incremental search.

		Called by KeyDown when the user pressed an alphanumeric key. Add the 
		key to the current search and start the timer.        
		"""
		self.incSearchTimer.stop()
		self.currSearchStr = "".join((self.currSearchStr, key))
		self.Form.setStatusText("Search: %s"
				% self.currSearchStr)
		self.incSearchTimer.start(self.SearchDelay)


	def popupMenu(self):
		""" Display a popup menu of relevant choices. 
		By default, the choices are 'New', 'Edit', and 'Delete'.
		"""
		popup = dabo.ui.dMenu()
		popup.append("Dabo Grid")
		popup.append("Default Popup")
		self.PopupMenu(popup, self.mousePosition)
		popup.release()


	def _onGridRowSize(self, evt):
		""" Occurs when the user sizes the height of the row. If the
		property 'SameSizeRows' is True, Dabo overrides the wxPython 
		default and applies that size change to all rows, not just the row 
		the user sized.
		"""
		row = evt.GetRowOrCol()
		size = self.GetRowSize(row)

		# Persist the new size
		self.Application.setUserSetting("%s.%s.%s" % (
				self.Form.Name, self.Name, "RowSize"), size)
		
		if self.SameSizeRows:
			self.SetDefaultRowSize(size, True)
			self.ForceRefresh()
		# Call the user hook
		self.onGridRowSize(evt)
		
	def onGridRowSize(self, evt): pass


	def getHTML(self, justStub=True, tableHeaders=True):
		""" Get HTML suitable for printing out the data in this grid.

		This can be used by client code to get a quick and dirty report
		via wxHtmlEasyPrinting, for example. 

		If justStub is False, it will be a standalone HTML file complete 
		with <html><head> etc...
		"""
		cols = self.GetNumberCols()
		rows = self.GetNumberRows()

		if not justStub:
			html = ["<html><body>"]
		else:
			html = []

		html.append("""<table border="1" cellpadding="2" cellspacing="0" width="100%">""")

		# get the column widths as proportional percentages:
		gridWidth = 0
		for col in range(cols):
			gridWidth += self.GetColSize(col)

		if tableHeaders:
			html.append("<tr>")
			for col in range(cols):
				colSize = str(int((100 * self.GetColSize(col)) / gridWidth) - 2) + "%"
				#colSize = self.GetColSize(col)
				colValue = self.GetTable().colLabels[col]
				html.append("""<td align="center" valign="center" width="%s"><b>%s</b></td>"""
								% (colSize,colValue))
			html.append("</tr>")

		for row in range(rows):
			html.append("<tr>")
			for col in range(cols):
				colName = self.GetTable().colNames[col]
				colVal = self.GetTable().data[row][col]
				html.append("""<td align="left" valign="top"><font size="1">%s</font></td>"""
								% colVal)
			html.append("</tr>")

		html.append("</table>")

		if not justStub:
			html.append("</body></html>")
		return "\n".join(html)


	def getColByX(self, x):
		""" Given the x-coordinate, return the column number.
		"""
		col = self.XToCol(x + (self.GetViewStart()[0]*self.GetScrollPixelsPerUnit()[0]))
		if col == wx.NOT_FOUND:
			col = -1
		return col


	def __onWxGridRowSize(self, evt):
		self.raiseEvent(dEvents.GridRowSize, evt)
		evt.Skip()

	def __onWxColSize(self, evt):
		self.raiseEvent(dEvents.GridColSize, evt)
		evt.Skip()
		
	def __onWxGridSelectCell(self, evt):
		self.raiseEvent(dEvents.GridSelectCell, evt)
		evt.Skip()

	def __onWxRightClick(self, evt):
		self.raiseEvent(dEvents.GridRightClick, evt)
		evt.Skip()


	def maxColOrder(self):
		""" Return the highest value of Order for all columns."""
		ret = -1
		if len(self.Columns) > 0:
			ret = max([cc.Order for cc in self.Columns])
		return ret
		
		
	def addColumn(self, col=None, inBatch=False):
		""" Adds a column to the grid. If no column is passed, a 
		blank column is added, which can be customized later.
		"""
		if col is None:
			col = dColumn(self)
		if col.Order == -1:
			col.Order = self.maxColOrder() + 10
		self.Columns.append(col)
		if not inBatch:
			msg = wx.grid.GridTableMessage(self._Table,
					wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED,
					1)
			self.ProcessTableMessage(msg)
			self.fillGrid(True)


	def removeColumn(self, col=None):
		""" Removes a column to the grid. If no column is passed, 
		the last column is removed.
		"""
		colNum = None
		if col is None:
			colNum = self.ColumnCount - 1
		elif type(col) == int:
			colNum = col
		else:
			# They probably passed a specific column instance
			colNum = self.Columns.index(col)
			if colNum == -1:
				# No such column
				# raise an error?
				return
		del self.Columns[colNum]
		msg = wx.grid.GridTableMessage(self._Table,
				wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
				colNum, 1)
		self.ProcessTableMessage(msg)
		self.fillGrid(True)


	def _getNumCols(self):
		return len(self.Columns)
	def _setNumCols(self, val):
		msg = None
		if val > -1:
			colChange = val - self.ColumnCount 
			self.BeginBatch()
			if colChange == 0:
				# No change
				return
			elif colChange < 0:
				msg = wx.grid.GridTableMessage(self._Table,
						wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED,
						val, abs(colChange))
				self.Columns = self.Columns[:val]
			else:
				msg = wx.grid.GridTableMessage(self._Table,
						wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED,
						colChange)
				for cc in range(colChange):
					self.addColumn(inBatch=True)
			if msg:
				self.ProcessTableMessage(msg)
			self.EndBatch()
			self.fillGrid(True)
			
	def _getNumRows(self):
		return self._Table.GetNumberRows()
	
	def _getColNum(self):
		return self.GetGridCursorCol()
	def _setColNum(self, val):
		if val > -1:
			val = min(val, self.ColumnCount)
			rn = self.CurrRow
			self.SetGridCursor(rn, val)
			self.MakeCellVisible(rn, val)
		
	def _getRowNum(self):
		return self.GetGridCursorRow()
	def _setRowNum(self, val):
		if val > -1:
			val = min(val, self.RowCount)
			cn = self.CurrCol
			self.SetGridCursor(val, cn)
			self.MakeCellVisible(val, cn)

	def _getHdr(self):
		if not self._hdr:
			self._hdr = self.GetGridColLabelWindow()
		return self._hdr
		
	def _getSrchDel(self):
		return self._searchDelay
	def _setSrchDel(self, val):
		self._searchDelay = val
		
	def _getTbl(self):
		tbl = self.GetTable()
		if not tbl:
			tbl = dGridDataTable(self)
			self.SetTable(tbl, True)
		return tbl	
	def _setTbl(self, tbl):
		self.SetTable(tbl, True)


	ColumnCount = property(_getNumCols, _setNumCols, None, 
			_("Number of columns in the grid.  (int)") )
	
	CurrCol = property(_getColNum, _setColNum, None,
			_("Currently selected column  (int)") )
			
	CurrRow = property(_getRowNum, _setRowNum, None,
			_("Currently selected row  (int)") )
			
	Header = property(_getHdr, None, None,
			_("Reference to the grid header window.  (header object?)") )
			
	RowCount = property(_getNumRows, None, None, 
			_("Number of rows in the grid.  (int)") )

	SearchDelay = property(_getSrchDel, _setSrchDel, None,
			_("""Delay in miliseconds between keystrokes before the 
			incremental search clears  (int)""") )
			
	_Table = property(_getTbl, _setTbl, None,
			_("Reference to the internal table class  (dGridDataTable)") )



	

if __name__ == '__main__':

	class TestForm(dabo.ui.dForm):
		def afterInit(self):
			self.BackColor = "green"
			g = self.grid = dGrid(self)
			self.Sizer.append(g, 1, "x", border=40, borderFlags="all")
			
			g.dataSet = [{"name" : "Ed Leafe", "age" : 47, "coder" :  True},
					{"name" : "Mike Leafe", "age" : 18, "coder" :  False} ]

			col = dColumn(g)
			col.Name = "Person"
			col.Order = 10
			col.Field = "name"
			col.DataType = "string"
			col.Width = 300
			col.Caption = "Customer Name"
			g.addColumn(col)
		
			col = dColumn(g)
			col.Name = "Age"
			col.Order = 30
			col.Field = "age"
			col.DataType = "integer"
			col.Width = 40
			col.Caption = "Age"
			g.addColumn(col)
		
		
		def getDataSet(self):
			return self.dataSet
			
			
	app = dabo.dApp()
	app.MainFormClass = TestForm
	app.setup()
	app.start()
