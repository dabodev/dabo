''' dGrid.py

    This is a grid designed to browse records of a bizobj. It does
    not descend from dControlMixin at this time, but is self-contained.
    There is a dGridDataTable definition here as well, that defines
    the 'data' that gets displayed in the grid.
'''
import wx, wx.grid
import urllib

class dGridDataTable(wx.grid.PyGridTableBase):
    def __init__(self, parent):
        wx.grid.PyGridTableBase.__init__(self)
        
        self.bizobj = parent.bizobj 
        self.grid = parent
        
        self.initTable()
         
    def initTable(self):
        self.colLabels = []
        self.colNames = []
        self.dataTypes = []
        self.imageBaseThumbnails = []
        self.imageLists = {}
        self.data = []
        
        for column in self.grid.columnDefs:
            self.colLabels.append(column["caption"])
            self.colNames.append(column["name"])
            self.dataTypes.append(self.getWxGridType(column["type"]))

    def fillTable(self):
        ''' dGridDataTable.fillTable() -> None
        
            Clear the grid and rebuild to match the current rows in
            the bizobj.
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
            for column in self.grid.columnDefs:
                recordVal = record[column["name"]]
                if column["type"] == "M":
                    # Show only the first 64 chars of the long text:
                    recordVal = str(recordVal)[:64]
                recordDict.append(recordVal)

            self.data.append(recordDict)
        
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
        
        # Something is still wrong with the MakeCellVisible call:
        # the -1 was trial and error to get the best results.
        self.grid.SetGridCursor(oldRow, oldCol)
        self.grid.MakeCellVisible(oldRow-1, oldCol)
                
        
    def getWxGridType(self,xBaseType):
        ''' dGridDataTable.getWxGridType(char) -> int
        
            Given a 1-char friendly xBase-style datatype, return
            a wx-style unfriendly datatype that can be used by the
            grid data table to determine the editors to use for the
            various columns.
        '''
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
            return true

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
    def __init__(self, parent, bizobj, form, name="dGrid",
                 columnDefs=[]):
        wx.grid.Grid.__init__(self, parent, -1)
        
        self.bizobj = bizobj
        self.form = form
        self.columnDefs = columnDefs
        
        ID_IncrementalSearchTimer = wx.NewId()
        self.currentIncrementalSearch = ""
        self.incrementalSearchTimerInterval = 500
        self.incrementalSearchTimer = wx.Timer(self, ID_IncrementalSearchTimer)
        
        self.sortedColumn = None
        self.sortOrder = ""
                
        self.SetRowLabelSize(0)
        self.SetMargins(0,0)
        self.AutoSizeColumns(True)      # If grid seems slow, this could be the problem.
        self.EnableEditing(False)
        
        wx.EVT_TIMER(self,  ID_IncrementalSearchTimer, self.OnIncrementalSearchTimer)
        wx.EVT_KEY_DOWN(self, self.OnKeyDown)
        
        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_PAINT(self.GetGridColLabelWindow(), self.OnColumnHeaderPaint)

        wx.grid.EVT_GRID_CELL_LEFT_DCLICK(self, self.OnLeftDClick)
        wx.grid.EVT_GRID_ROW_SIZE(self, self.OnGridRowSize)
        wx.grid.EVT_GRID_SELECT_CELL(self, self.OnGridSelectCell)
        wx.grid.EVT_GRID_CELL_RIGHT_CLICK(self, self.OnRightClick)
        wx.grid.EVT_GRID_LABEL_LEFT_CLICK(self, self.OnGridLabelLeftClick)
        
    def fillGrid(self):
        ''' dGrid.fillGrid() -> None
        
            Call this to refresh the contents of the grid based on the 
            current state of the bizobj.
        '''
        if not self.GetTable():
            self.SetTable(dGridDataTable(self), True)
        self.GetTable().fillTable()
    
    def OnGridSelectCell(self, event):
        ''' dGrid.OnGridSelectCell(event) -> None
        
            Called when a grid sell becomes active. This is crucial to
            keeping the bizobj updated with row changes made in the grid.
        '''
        oldRow = self.GetGridCursorRow()
        newRow = event.GetRow()
        self.bizobj.moveToRowNum(newRow)
        self.form.refreshControls()
        event.Skip()
        
    def OnPaint(self, evt): 
        evt.Skip()

    def OnColumnHeaderPaint(self, evt):
        ''' dGrid.OnColumnHeaderPaint(event) -> None
        
            Occurs when it is time to paint the column headers. The headers
            are not individual objects, but rather one window. Dabo uses this
            paint method to put sort indicators in the appropriate column.
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
            dc.DrawRectangle(rect[0] - (col<>0 and 1 or 0), 
                             rect[1], 
                             rect[2] + (col<>0 and 1 or 0), 
                             rect[3])
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
        ''' dGrid.OnIncrementalSearchTimer(event) -> None
        
            Occurs when the timer reaches its interval, which means
            that the incremental search wait period is over. Any future
            keypress will start a new incremental search instead of
            appending to an existing one.
        '''
        self.currentIncrementalSearch = ""
        self.incrementalSearchTimer.Stop()
           
             
    def OnLeftDClick(self, evt): 
        ''' dGrid.OnLeftDClick(event) -> None
        
            Occurs when the user double-clicks a cell in the grid. By
            default, this is interpreted as a request to edit the 
            record.
        '''
        self.editRecord()
    
        
    def OnRightClick(self, evt):
        ''' dGrid.OnRightClick(event) -> None
            
            Occurs when the user right-clicks a cell in the grid. By
            default, this is interpreted as a request to display the
            popup menu, as defined in self.popupMenu().
        '''
        
        # Select the cell that was right-clicked upon
        self.SetGridCursor(evt.GetRow(), evt.GetCol())
        
        # Make the popup menu appear in the location that was clicked
        self.mousePosition = evt.GetPosition()
        
        # Display the popup menu, if any
        self.popupMenu()
        evt.Skip()
    
        
    def OnGridLabelLeftClick(self, evt):
        ''' dGrid.OnGridLabelLeftClick(event) -> None
        
            Occurs when the user left-clicks a grid column label. By
            default, this is interpreted as a request to sort the 
            column.
        '''
        self.processSort(evt.GetCol())

                            
    def OnKeyDown(self, evt): 
        ''' dGrid.OnKeyDown(event) -> None
        
            Occurs when the user presses a key inside the grid. Default
            actions depend on the key being pressed.
            
                       Enter:  edit the record
                         Del:  delete the record
                          F2:  sort the current column
                AlphaNumeric:  incremental search
        '''
        keyCode = evt.GetKeyCode()
        
        if keyCode == 13:           # Enter
            self.editRecord()
        else:
            if keyCode == 127:      # Del
                self.deleteRecord()
            elif keyCode == 343:    # F2
                self.processSort()
            elif keyCode in range(240) and not evt.HasModifiers():
                self.processIncrementalSearch(chr(keyCode))
            else:
                pass
            evt.Skip()

            
    def newRecord(self, event=None):
        ''' dGrid.newRecord() -> None
        
            Request that a new row be added.
        '''
        try:
            self.GetParent().getDform().new()
            self.GetParent().editRecord()
        except AttributeError:
            pass
        
    
    def editRecord(self, event=None):
        ''' dGrid.editRecord() -> None
        
            Request that the current row be edited.
        '''
        try:
            self.GetParent().editRecord()
        except AttributeError:
            pass
           
    
    def deleteRecord(self, event=None):
        ''' dGrid.deleteRecord() -> None
        
            Request that the current row be deleted.
        '''
        try:
            self.GetParent().getDform().delete()
        except AttributeError:
            pass
    
                    
    def processSort(self, gridCol=None):
        ''' dGrid.processSort(int) -> None
        
            Sort the grid column, toggling between ascending
            and descending. If the grid column index isn't 
            passed, the current grid column will be used.
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
     
        
    def processIncrementalSearch(self, char):
        ''' dGrid.processIncrementalSearch(char) -> None
        
            Add the passed char to the incremental search string if it
            exists, and run the search. Called by dGrid.OnKeyDown() when
            an alphanumeric character is entered.
        '''
        # Stop the timer, add the character to the incremental search string,
        # process the search, and restart the timer
        self.incrementalSearchTimer.Stop()
        self.currentIncrementalSearch = ''.join((self.currentIncrementalSearch, char))
        
        self.GetParent().getDform().SetStatusText('Search: %s'
                             % self.currentIncrementalSearch)
        
        gridCol = self.GetGridCursorCol()
        if gridCol < 0:
            gridCol = 0
        cursorCol = self.GetTable().colNames[gridCol]
        
        row = self.bizobj.seek(self.currentIncrementalSearch, cursorCol, 
                                caseSensitive=False, near=True)
        
        if row > -1:
            self.SetGridCursor(row, gridCol)
            self.MakeCellVisible(row, gridCol)
        self.incrementalSearchTimer.Start(self.incrementalSearchTimerInterval)

        
    def popupMenu(self):
        ''' dGrid.popupMenu() -> None
        
            Display a popup menu of relevant choices. By default, the choices
            are 'New', 'Edit', and 'Delete'.
        '''
        popup = wx.Menu()
        id_new,id_edit,id_delete = wx.NewId(), wx.NewId(), wx.NewId()
        popup.Append(id_new, "&New", "Add a new record")
        popup.Append(id_edit, "&Edit", "Edit this record")
        popup.Append(id_delete, "&Delete", "Delete record")
        
        wx.EVT_MENU(popup, id_new, self.newRecord)
        wx.EVT_MENU(popup, id_edit, self.editRecord)
        wx.EVT_MENU(popup, id_delete, self.deleteRecord)
        
        self.PopupMenu(popup, self.mousePosition)
        popup.Destroy()
        
              
    def OnGridRowSize(self, evt):
        ''' dGrid.OnGridRowSize(event) -> None
        
            Occurs when the user sizes the height of the row. Dabo 
            overrides the default and applies that size change to all
            rows, not just the row the user sized.
        '''
        self.SetDefaultRowSize(self.GetRowSize(evt.GetRowOrCol()), True)
        evt.Skip()
                        
        
    def getHTML(self, justStub=True, tableHeaders=True):
        ''' dGrid.getHTML([justStub(bool)[,tableHeaders(bool)]]) -> string
        
            Get HTML suitable for printing out the data in 
            this grid via wxHtmlEasyPrinting. 
            
            If justStub is False, make it like a standalone
            HTML file complete with <HTML><HEAD> etc...
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
        
