''' dGrid.py

This is a grid designed to browse records of a bizobj. It does
not descend from dControlMixin at this time, but is self-contained.
There is a dGridDataTable definition here as well, that defines
the 'data' that gets displayed in the grid.
'''
import wx, wx.grid
import urllib
import dIcons

class dGridDataTable(wx.grid.PyGridTableBase):
	def __init__(self, parent):
		wx.grid.PyGridTableBase.__init__(self)

		self.bizobj = parent.bizobj 
		self.grid = parent

		self.initTable()


	def initTable(self):
		self.relativeColumns = []
		self.colLabels = []
		self.colNames = []
		self.dataTypes = []
		self.imageBaseThumbnails = []
		self.imageLists = {}
		self.data = []

		# Put column order in relative column order, if relative column order
		# exists in dApp.getUserSettings(). 
		for column in range(len(self.grid.columnDefs)):
			if self.grid.columnDefs[column]['showGrid']:
				order = self.grid.form.dApp.getUserSetting("%s.%s.%s.%s" % (
							self.grid.form.GetName(), 
							self.grid.GetName(),
							"Column%s" % column,
							"ColumnOrder"))
				if order == None:
					order = column
				self.relativeColumns.append(order)

		for relativeColumn in self.relativeColumns:
			column = self.grid.columnDefs[relativeColumn]
			if column['showGrid']:
				self.colLabels.append(column["caption"])
				self.colNames.append(column["fieldName"])
				self.dataTypes.append(self.getWxGridType(column["type"]))


	def fillTable(self):
		''' Fill the grid's data table to match the bizobj.
		'''
		rows = self.GetNumberRows()
		oldRow = self.bizobj.getRowNumber()    # current row per the bizobj
		oldCol = self.grid.GetGridCursorCol()  # current column per the grid
		if not oldCol:
			oldCol = 0

		self.Clear()
		self.data = []

		# Fill self.data based on bizobj records
		dataSet = self.bizobj.getDataSet()

		for record in dataSet:
			recordDict = []
			for relativeColumn in self.relativeColumns:
				column = self.grid.columnDefs[relativeColumn]
				if column['showGrid']:
					recordVal = record[column["fieldName"]]
					if column["type"] == "M":
						# Show only the first 64 chars of the long text:
						recordVal = str(recordVal)[:64]
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
			self.GetView().ProcessTableMessage(msg)


		# Column widths come from dApp user settings, or get sensible
		# defaults based on field type.
		for index in range(len(self.relativeColumns)):
			colName = "Column%s" % self.relativeColumns[index]
			gridCol = index
			fieldType = self.grid.columnDefs[self.relativeColumns[index]]['type']

			width = self.grid.form.dApp.getUserSetting("%s.%s.%s.%s" % (
						self.grid.form.GetName(), 
						self.grid.GetName(),
						colName,
						"Width"))

			if width == None:
				minWidth = 10 * len(self.colLabels[self.relativeColumns[index]])   ## Fudge!
				if fieldType == "I":
					width = 50
				elif fieldType == "N":
					width = 75
				else:
					width = 200

				if width < minWidth:
					width = minWidth

			self.grid.SetColSize(gridCol, width)
		self.grid.EndBatch()


	def getWxGridType(self, xBaseType):
		''' Get the wx data type, given a 1-char xBase type.

		This is used by the grid data table to determine the editors to use 
		for the various columns.
		'''
		if xBaseType == "L":
			return wx.grid.GRID_VALUE_BOOL
		if xBaseType == "I":
			return wx.grid.GRID_VALUE_NUMBER
		elif xBaseType == "C":
			return wx.grid.GRID_VALUE_STRING
		elif xBaseType == "N":
			return wx.grid.GRID_VALUE_FLOAT
		elif xBaseType == "M":
			return wx.grid.GRID_VALUE_STRING
		elif xBaseType == "D":
			return wx.grid.GRID_VALUE_STRING
		else:
			return wx.grid.GRID_VALUE_STRING


	def MoveColumn(self, col, to):
		''' Move the column to a new position.
		'''
		old = self.relativeColumns[col]
		del self.relativeColumns[col]

		if to > col:
			self.relativeColumns.insert(to-1,old)
		else:
			self.relativeColumns.insert(to,old)

		for index in range(len(self.relativeColumns)):
			self.grid.form.dApp.setUserSetting("%s.%s.%s.%s" % (
					self.grid.form.GetName(),
					self.grid.GetName(),
					"Column%s" % self.relativeColumns[index],
					"ColumnOrder"), "I", "%s" % (index))

		self.initTable()
		self.fillTable()


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
			return self.data[row][col]
		except IndexError:
			return ''

	def SetValue(self, row, col, value):
		try:
			self.data[row][col] = value
		except IndexError:
			# add a new row
			self.data.append([''] * self.GetNumberCols())
			self.SetValue(row, col, value)

			# tell the grid we've added a row
			msg = wx.grid.GridTableMessage(self,           # The table
				wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,  # what we did to it
				1)                                       # how many

			self.GetView().ProcessTableMessage(msg)


class dGrid(wx.grid.Grid):
	def __init__(self, parent, bizobj, form):
		wx.grid.Grid.__init__(self, parent, -1)

		self.bizobj = bizobj
		self.form = form

		ID_IncrementalSearchTimer = wx.NewId()
		self.currentIncrementalSearch = ""
		self.incrementalSearchTimerInterval = 300     # This needs to be user-tweakable
		self.incrementalSearchTimer = wx.Timer(self, ID_IncrementalSearchTimer)

		self.sortedColumn = None
		self.sortOrder = ""

		self.SetRowLabelSize(0)        # turn off row labels
		self.EnableEditing(False)      # this isn't a spreadsheet

		self.headerDragging = False    # flag used by mouse motion event handler
		self.headerDragFrom = 0
		self.headerDragTo = 0
		self.headerSizing = False

		self.Bind(wx.EVT_TIMER, self.OnIncrementalSearchTimer, self.incrementalSearchTimer)
		self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

		self.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.OnLeftDClick)
		self.Bind(wx.grid.EVT_GRID_ROW_SIZE, self.OnGridRowSize)
		self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.OnGridSelectCell)
		self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
		self.Bind(wx.grid.EVT_GRID_COL_SIZE, self.OnColSize)

		self.initHeader()


	def initHeader(self):
		''' Initialize behavior for the grid header region.
		'''
		header = self.GetGridColLabelWindow()

		header.Bind(wx.EVT_LEFT_DOWN, self.OnHeaderLeftDown)
		header.Bind(wx.EVT_LEFT_UP, self.OnHeaderLeftUp)
		header.Bind(wx.EVT_MOTION, self.OnHeaderMotion)
		header.Bind(wx.EVT_PAINT, self.OnColumnHeaderPaint)


	def fillGrid(self):
		''' Refresh the grid to match the data in the bizobj.
		'''

		# Get the default row size from dApp's user settings
		s = self.form.dApp.getUserSetting("%s.%s.%s" % (
						self.form.GetName(), 
						self.GetName(),
						"RowSize"))
		if s:
			self.SetDefaultRowSize(s)

		if not self.GetTable():
			self.SetTable(dGridDataTable(self), True)
		self.GetTable().fillTable()


	def OnColSize(self, event):
		''' Occurs when the user resizes the width of the column.
		'''
		col = event.GetRowOrCol()
		width = self.GetColSize(col)

		self.form.dApp.setUserSetting("%s.%s.%s.%s" % (
						self.form.GetName(), 
						self.GetName(),
						"Column%s" % self.GetTable().relativeColumns[col],
						"Width"), "I", width)

		event.Skip()


	def OnGridSelectCell(self, event):
		''' Occurs when the grid's cell focus has changed.
		'''
		oldRow = self.GetGridCursorRow()
		newRow = event.GetRow()
		self.bizobj.moveToRowNum(newRow)
		self.form.refreshControls()
		event.Skip()


	def OnColumnHeaderPaint(self, evt):
		''' Occurs when it is time to paint the grid column headers.
		'''
		w = self.GetGridColLabelWindow()
		dc = wx.PaintDC(w)
		clientRect = w.GetClientRect()
		font = dc.GetFont()

		# Thanks Roger Binns for the correction to totColSize
		totColSize = -self.GetViewStart()[0]*self.GetScrollPixelsPerUnit()[0]

		# We are totally overriding wx's drawing of the column headers,
		# so we are responsible for drawing the rectangle, the column
		# header text, and the sort indicators.
		for col in range(self.GetNumberCols()):
			dc.SetBrush(wx.Brush("WHEAT", wx.TRANSPARENT))
			dc.SetTextForeground(wx.BLACK)
			colSize = self.GetColSize(col)
			rect = (totColSize,0,colSize,32)
			dc.DrawRectangle((rect[0] - (col<>0 and 1 or 0), 
							rect[1]), 
							(rect[2] + (col<>0 and 1 or 0), 
							rect[3]))
			totColSize += colSize

			if col == self.sortedColumn:
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


	def OnIncrementalSearchTimer(self, evt):
		''' Occurs when the incremental search timer reaches its interval. 

		It is time to run the search, if there is any search in the buffer.
		'''
		if len(self.currentIncrementalSearch) > 0:
			self.processIncrementalSearch()
		else:
			self.incrementalSearchTimer.Stop()


	def OnHeaderMotion(self, evt):
		''' Occurs when the mouse moves in the grid header.
		'''
		headerIsDragging = self.headerDragging
		headerIsSizing = self.headerSizing
		dragging = evt.Dragging()
		header = self.GetGridColLabelWindow()

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
					if begCol == curCol:
						# Give visual indication that a move is initiated
						header.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
					else:
						# Give visual indication that this is an acceptable drop target
						header.SetCursor(wx.StockCursor(wx.CURSOR_BULLSEYE))
			else:
				# A size action is happening
				self.headerSizing = True
				evt.Skip()

		else:
			evt.Skip()


	def OnHeaderLeftUp(self, evt):
		''' Occurs when the left mouse button goes up in the grid header.

		Basically, this comes down to two possibilities: the end of a drag
		operation, or a single-click operation. If we were dragging, then
		it is possible a column needs to change position. If we were clicking,
		then it is a sort operation.
		'''
		x,y = evt.GetX(), evt.GetY()
		if self.headerDragging:
			# A drag action is ending
			self.headerDragTo = (x,y)

			begCol = self.getColByX(self.headerDragFrom[0])
			curCol = self.getColByX(x)

			if begCol != curCol:
				if curCol > begCol:
					curCol += 1
				self.GetTable().MoveColumn(begCol, curCol)
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
		evt.Skip()


	def OnHeaderLeftDown(self, evt):
		''' Occurs when the left mouse button goes down in the grid header.
		'''
		pass


	def OnLeftDClick(self, evt): 
		''' Occurs when the user double-clicks a cell in the grid. 

		By default, this is interpreted as a request to edit the record.
		'''
		self.editRecord()


	def OnRightClick(self, evt):
		''' Occurs when the user right-clicks a cell in the grid. 

		By default, this is interpreted as a request to display the popup 
		menu, as defined in self.popupMenu().
		'''

		# Select the cell that was right-clicked upon
		self.SetGridCursor(evt.GetRow(), evt.GetCol())

		# Make the popup menu appear in the location that was clicked
		self.mousePosition = evt.GetPosition()

		# Display the popup menu, if any
		self.popupMenu()
		evt.Skip()


	def OnGridLabelLeftClick(self, evt):
		''' Occurs when the user left-clicks a grid column label. 

		By default, this is interpreted as a request to sort the column.
		'''
		self.processSort(evt.GetCol())


	def OnKeyDown(self, evt): 
		''' Occurs when the user presses a key inside the grid. 

		Default actions depend on the key being pressed:

					Enter:  edit the record
						Del:  delete the record
						F2:  sort the current column
				AlphaNumeric:  incremental search
		'''
		keyCode = evt.GetKeyCode()
		try:
			char = chr(keyCode)
		except ValueError:       # keycode not in ascii range
			char = None

		if keyCode == 13:           # Enter
			self.editRecord()
		else:
			if keyCode == 127:      # Del
				self.deleteRecord()
			elif keyCode == 343:    # F2
				self.processSort()
			elif char and (char.isalnum() or char.isspace()) and not evt.HasModifiers():
				self.addToIncrementalSearch(char)
			else:
				evt.Skip()


	def newRecord(self, event=None):
		''' Request that a new row be added.
		'''
		try:
			self.GetParent().getDform().new()
			self.GetParent().editRecord()
		except AttributeError:
			pass


	def editRecord(self, event=None):
		''' Request that the current row be edited.
		'''
		try:
			self.GetParent().editRecord()
		except AttributeError:
			pass


	def deleteRecord(self, event=None):
		''' Request that the current row be deleted.
		'''
		try:
			self.GetParent().getDform().delete()
		except AttributeError:
			pass


	def processSort(self, gridCol=None):
		''' Sort the grid column.

		Toggle between ascending and descending. If the grid column index isn't 
		passed, the currently active grid column will be sorted.
		'''
		table = self.GetTable()

		if gridCol == None:
			gridCol = self.GetGridCursorCol()

		# Bizobj needs the name of the field
		columnToSort = table.colNames[gridCol]

		sortOrder="ASC"
		if gridCol == self.sortedColumn:
			sortOrder = self.sortOrder
			if sortOrder == "ASC":
				sortOrder = "DESC"
			else:
				sortOrder = "ASC"

		self.bizobj.sort(columnToSort, sortOrder)
		self.sortedColumn = gridCol
		self.sortOrder = sortOrder

		self.ForceRefresh()     # Redraw the up/down sort indicator
		table.fillTable()       # Sync the grid with the bizobj


	def processIncrementalSearch(self):
		''' Run the incremental search.
		'''
		gridCol = self.GetGridCursorCol()
		if gridCol < 0:
			gridCol = 0
		cursorCol = self.GetTable().colNames[gridCol]

		row = self.bizobj.seek(self.currentIncrementalSearch, cursorCol, 
								caseSensitive=False, near=True)

		if row > -1:
			self.SetGridCursor(row, gridCol)
			self.MakeCellVisible(row, gridCol)

		# Add a '.' to the status bar to signify that the search is
		# done, and clear the search string for next time.
		self.GetParent().getDform().setStatusText('Search: %s.'
				% self.currentIncrementalSearch)
		self.currentIncrementalSearch = ''


	def addToIncrementalSearch(self, key):
		''' Add a character to the current incremental search.

		Called by KeyDown when the user pressed an alphanumeric key. Add the 
		key to the current search and start the timer.        
		'''
		self.incrementalSearchTimer.Stop()

		self.currentIncrementalSearch = ''.join((self.currentIncrementalSearch, key))
		self.GetParent().getDform().setStatusText('Search: %s'
				% self.currentIncrementalSearch)

		self.incrementalSearchTimer.Start(self.incrementalSearchTimerInterval)


	def popupMenu(self):
		''' Display a popup menu of relevant choices. 

		By default, the choices are 'New', 'Edit', and 'Delete'.
		'''
		popup = wx.Menu()
		id_new,id_edit,id_delete = wx.NewId(), wx.NewId(), wx.NewId()

		item = wx.MenuItem(popup, id_new, "&New", "Add a new record")
		item.SetBitmap(dIcons.getIconBitmap("blank"))
		popup.AppendItem(item)

		item = wx.MenuItem(popup, id_edit, "&Edit", "Edit this record")
		item.SetBitmap(dIcons.getIconBitmap("edit"))
		popup.AppendItem(item)

		item = wx.MenuItem(popup, id_delete, "&Delete", "Delete this record")
		item.SetBitmap(dIcons.getIconBitmap("delete"))
		popup.AppendItem(item)

		wx.EVT_MENU(popup, id_new, self.newRecord)
		wx.EVT_MENU(popup, id_edit, self.editRecord)
		wx.EVT_MENU(popup, id_delete, self.deleteRecord)

		self.PopupMenu(popup, self.mousePosition)
		popup.Destroy()


	def OnGridRowSize(self, evt):
		''' Occurs when the user sizes the height of the row. 

		Dabo overrides the wxPython default and applies that size change to all
		rows, not just the row the user sized.
		'''
		row = evt.GetRowOrCol()
		size = self.GetRowSize(row)

		# Persist the new size
		self.form.dApp.setUserSetting("%s.%s.%s" % (
						self.form.GetName(), 
						self.GetName(),
						"RowSize"), "I", size)

		self.SetDefaultRowSize(size, True)
		self.ForceRefresh()
		evt.Skip()


	def getHTML(self, justStub=True, tableHeaders=True):
		''' Get HTML suitable for printing out the data in this grid.

		This can be used by client code to get a quick and dirty report
		via wxHtmlEasyPrinting, for example. 

		If justStub is False, it will be a standalone HTML file complete 
		with <HTML><HEAD> etc...
		'''
		cols = self.GetNumberCols()
		rows = self.GetNumberRows()

		if not justStub:
			html = ["<HTML><BODY>"]
		else:
			html = []

		html.append("<TABLE BORDER=1 CELLPADDING=2 CELLSPACING=0>")

		# get the column widths as proportional percentages:
		gridWidth = 0
		for col in range(cols):
			gridWidth += self.GetColSize(col)

		if tableHeaders:
			html.append("<TR>")
			for col in range(cols):
				colSize = str(int((100 * self.GetColSize(col)) / gridWidth) - 2) + "%"
				#colSize = self.GetColSize(col)
				colValue = str(self.GetColLabelValue(col))
				html.append("<TD ALIGN='center' VALIGN='center' WIDTH='%s'><B>%s</B></TD>"
								% (colSize,colValue))
			html.append("</TR>")

		for row in range(rows):
			html.append("<TR>")
			for col in range(cols):
				colName = self.GetTable().colNames[col]
				colVal = eval("self.wicket.viewCursor[row].%s" % colName)
				html.append("<TD ALIGN='left' VALIGN='top'><FONT SIZE=1>%s</FONT></TD>"
								% colVal)
			html.append("</TR>")

		html.append("</TABLE>")

		if not justStub:
			html.append("</BODY></HTML>")
		return "\n".join(html)


	def getColByX(self, x):
		''' Given the x-coordinate, return the column number.
		'''
		totColSize = 0
		for col in range(self.GetNumberCols()):
			colSize = self.GetColSize(col)
			totColSize += colSize
			if x <= totColSize:
				break

		if x > totColSize:
			return self.GetNumberCols() + 1
		elif x < 0:
			return -1
		else:
			return col
