''' dGrid.py

    This is a grid designed to browse records of a bizobj. It does
    not descend from dControlMixin at this time, but is self-contained.
    There is a dGridDataTable definition here as well, that defines
    the 'data' that gets displayed in the grid.
'''
from wxPython.wx import *
from wxPython.grid import *
import wx
import urllib

class dGridDataTable(wxPyGridTableBase):
    def __init__(self, parent):
        wxPyGridTableBase.__init__(self)
        
        self.bizobj = parent.bizobj 
        self.grid = parent
        
        self.initTable()
         
    def initTable(self):
        self.colLabels = []
        self.colNames = []
        self.dataTypes = []
        self.imageBaseThumbnails = []
        self.imageLists = {}
        
        self.grid.SetDefaultRowSize(20)  # (make user-editable)

        for column in self.grid.columnDefs:
            if column["showGrid"] == True:
                self.colLabels.append(column["caption"])
                self.colNames.append(column["name"])
                self.dataTypes.append(self.wxGridType(column["type"]))

    def fillTable(self):
        rows = self.GetNumberRows()
        self.Clear()
        self.data = []
        oldRowNum = self.bizobj.getRowNumber()
        for record in range(self.bizobj.getRowCount()):
            recordDict = []
            self.bizobj.moveToRowNum(record)
            for column in self.grid.columnDefs:
                if column["showGrid"] == True:
                    recordVal = eval("self.bizobj.%s" % column["name"])
                    if column["type"] == "M":
                        # Show only the first 64 chars of the long text:
                        recordVal = str(recordVal)[:64]
                    recordDict.append(recordVal)

            self.data.append(recordDict)
            
        self.bizobj.moveToRowNum(oldRowNum)
        
        if len(self.data) <> rows:
            if len(self.data) > rows:
                num = len(self.data) - rows
                #print "add %s rows" % num
                # tell the grid we've added row(s)
                msg = wxGridTableMessage(self,                             # The table
                                    wxGRIDTABLE_NOTIFY_ROWS_APPENDED, # what we did to it
                                    num)            # how many

            elif rows > len(self.data):
                num = rows - len(self.data) 
                #print "delete %s rows" % num
                # tell the grid we've deleted row(s)
                msg = wxGridTableMessage(self,                             # The table
                                    wxGRIDTABLE_NOTIFY_ROWS_DELETED, # what we did to it
                                    0,          # position
                                    num)            # how many
                
            self.GetView().ProcessTableMessage(msg)
        
        self.grid.SetGridCursor(oldRowNum, 0)
        self.grid.MakeCellVisible(oldRowNum-1, 0)
                
    def wxGridType(self,xBaseType):
        if xBaseType == "I":
            return wxGRID_VALUE_NUMBER
        elif xBaseType == "C":
            return wxGRID_VALUE_STRING
        elif xBaseType == "N":
            return wxGRID_VALUE_FLOAT
        elif xBaseType == "M":
            return wxGRID_VALUE_STRING
        elif xBaseType == "D":
            return wxGRID_VALUE_STRING
        else:
            return wxGRID_VALUE_STRING
                
    #--------------------------------------------------
    # required methods for the wxPyGridTableBase interface

    def GetNumberRows(self):
        try:
            num = len(self.data)
        except:
            num = 0
        return num
            
    def GetNumberCols(self):
        return len(self.colLabels)

    def IsEmptyCell(self, row, col):
        try:
            return not self.data[row][col]
        except IndexError:
            return true


    # Get/Set values in the table.  The Python version of these
    # methods can handle any data-type, (as long as the Editor and
    # Renderer understands the type too,) not just strings as in the
    # C++ version.
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
            msg = wxGridTableMessage(self,                             # The table
                                    wxGRIDTABLE_NOTIFY_ROWS_APPENDED, # what we did to it
                                    1)                                # how many

            self.GetView().ProcessTableMessage(msg)


    #--------------------------------------------------
    # Some optional methods

    def AppendRows(self, rows):
        print "table.AppendRows():", rows
        return True
        
    # Called when the grid needs to display labels
    def GetColLabelValue(self, col):
        #print dir(self)
        if self.grid.sortedColumn == col:
            if self.gridRef.sortedColumnDescending == True:
                # I'd love to figure out how to include graphical
                # arrows in the grid columns!
                char = "_"
            else:
                char = "^"
        else:
            char = ""
        
        return "%s%s" % (char, self.colLabels[col])
        
    # Called to determine the kind of editor/renderer to use by
    # default, doesn't necessarily have to be the same type used
    # natively by the editor/renderer if they know how to convert.
    def GetTypeName(self, row, col):
        return self.dataTypes[col]

    # Called to determine how the data can be fetched and stored by the
    # editor and renderer.  This allows you to enforce some type-safety
    # in the grid.
    def CanGetValueAs(self, row, col, typeName):
        colType = self.dataTypes[col].split(':')[0]
        if typeName == colType:
            return true
        else:
            return False

    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)

        
class dGrid(wxGrid):
    def __init__(self, parent, bizobj, form, name="dGrid"):
        wxGrid.__init__(self, parent, -1)
        self.bizobj = bizobj
        self.form = form
        ID_IncrementalSearchTimer = wx.NewId()
    
        self.currentIncrementalSearch = ""
        self.incrementalSearchTimerInterval = 500
        self.incrementalSearchTimer = wx.Timer(self, ID_IncrementalSearchTimer)
        
        self.sortedColumn = None
        self.sortOrder = ""
        
        
        self.SetRowLabelSize(0)
        self.SetMargins(0,0)
        self.AutoSizeColumns(True)
        self.EnableEditing(False)
        
        self.fillGrid()

        EVT_TIMER(self,  ID_IncrementalSearchTimer, self.OnIncrementalSearchTimer)
        EVT_GRID_CELL_LEFT_DCLICK(self, self.OnLeftDClick)
        EVT_KEY_DOWN(self, self.OnKeyDown)
        EVT_GRID_CELL_RIGHT_CLICK(self, self.OnRightClick)
        EVT_GRID_LABEL_LEFT_CLICK(self, self.OnGridLabelLeftClick)

        EVT_GRID_SELECT_CELL(self, self.OnGridSelectCell)
        
        EVT_PAINT(self, self.OnPaint)

        columnLabelWindow = self.GetGridColLabelWindow()
        EVT_PAINT(columnLabelWindow, self.OnColumnHeaderPaint)

        EVT_GRID_ROW_SIZE(self, self.OnGridRowSize)
    
    def fillGrid(self):
        self.columnDefs = [{"name": "czip", "caption": "zipcode", "showGrid": True, "type": "C"},]
        table = dGridDataTable(self)
        self.SetTable(table, True)
        self.GetTable().fillTable()
    
    def OnGridSelectCell(self, event):
        oldRow = self.GetGridCursorRow()
        newRow = event.GetRow()
        self.bizobj.moveToRowNum(newRow)
        self.form.refreshControls()
        event.Skip()
        
    def OnPaint(self, evt): 
        evt.Skip()

    def OnColumnHeaderPaint(self, evt):
        #evt.Skip()
        w = self.GetGridColLabelWindow()
        dc = wx.PaintDC(w)
        clientRect = w.GetClientRect()
        font = dc.GetFont()
        totColSize = -self.GetViewStart()[0]*self.GetScrollPixelsPerUnit()[0] # Thanks Roger Binns
        for col in range(self.GetNumberCols()):
            dc.SetBrush(wxBrush("WHEAT", wxTRANSPARENT))
            dc.SetTextForeground(wxBLACK)
            #print col, w.GetRect(), self.GetColSize(col)
            colSize = self.GetColSize(col)
            rect = (totColSize,0,colSize,32)
            dc.DrawRectangle(rect[0] - (col<>0 and 1 or 0), rect[1], rect[2] + (col<>0 and 1 or 0), rect[3])
            totColSize += colSize
            
            if col == self.sortedColumn:
                font.SetWeight(wxBOLD)
                # draw a triangle, pointed up or down, at the
                # top left of the column.
                left = rect[0] + 3
                top = rect[1] + 3
                
                dc.SetBrush(wxBrush("WHEAT", wxSOLID))
                if self.sortOrder == "DESC":
                    dc.DrawPolygon([(left,top), (left+6,top), (left+3,top+4)])
                elif self.sortOrder == "ASC":
                    dc.DrawPolygon([(left+3,top), (left+6, top+4), (left, top+4)])
                else:
                    pass    
            else:
                font.SetWeight(wxNORMAL)

            dc.SetFont(font)
            dc.DrawLabel("%s" % self.GetTable().colLabels[col],
                     rect, wxALIGN_CENTER | wxALIGN_TOP)
            
    def OnIncrementalSearchTimer(self, evt):
        self.currentIncrementalSearch = ""
        self.incrementalSearchTimer.Stop() # may as well...
        #statusBar = wx.GetApp().GetTopWindow().GetStatusBar()
                
    def OnLeftDClick(self, evt): 
        self.editRecord()
    
    def OnRightClick(self, evt):
        # pkm: I'm used to VFP/Windows right-clicks actually 
        #       making active the control that was right-clicked.
        #       The following line does this:
        self.SetGridCursor(evt.GetRow(), evt.GetCol())
        self.mousePosition = evt.GetPosition()
        self.popupMenu()
        evt.Skip()
    
    def OnGridLabelLeftClick(self, evt):
        self.processSort(evt.GetCol())
        #evt.Skip()  
                    
    def OnKeyDown(self, evt): 
        keyCode = evt.GetKeyCode()
        #print dir(evt)
        if keyCode == 13:
            self.editRecord()
        else:
            if keyCode == 127:
                self.deleteRecord()
            elif keyCode in range(240) and not evt.HasModifiers():
                self.processIncrementalSearch(chr(keyCode))
            elif keyCode == 343:    # f2
                self.processSort()
            else:
                pass
                #print keyCode
            evt.Skip()

    def processSort(self, gridCol=None):
        table = self.GetTable()
        
        if gridCol == None:
            gridCol = self.GetGridCursorCol()
        
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
        
        self.ForceRefresh()
        table.fillTable()
     
    def processIncrementalSearch(self, char):
        # Stop the timer, add the character to the incremental search string,
        # process the search, and restart the timer
        self.incrementalSearchTimer.Stop()
        self.currentIncrementalSearch = ''.join((self.currentIncrementalSearch, char))
        
        self.GetParent().getDform().SetStatusText(''.join(('Search: ', self.currentIncrementalSearch)))
        
        table = self.GetTable()
        gridCol = self.GetGridCursorCol()
        if gridCol < 0:
            gridCol = 0
        cursorCol = table.colNames[gridCol]
        
        row = self.bizobj.seek(self.currentIncrementalSearch, cursorCol, 
                                caseSensitive=False, near=True)
        print self.currentIncrementalSearch, cursorCol, row, gridCol
        if row > -1:
            self.SetGridCursor(row, gridCol)
            self.MakeCellVisible(row, gridCol)
        self.incrementalSearchTimer.Start(self.incrementalSearchTimerInterval)

    def popupMenu(self): pass
                  
    def OnGridRowSize(self, evt):
        self.SetDefaultRowSize(self.GetRowSize(evt.GetRowOrCol()), True)
        evt.Skip()
                        
    def getHTML(self, justStub=True, tableHeaders=True):
        ''' Get HTML suitable for printing out the data in 
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
        
