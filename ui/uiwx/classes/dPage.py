''' dPage.py '''
import wx
from dGrid import dGrid
from dControlMixin import dControlMixin
from dEditBox import dEditBox
from dTextBox import dTextBox
from dSpinner import dSpinner
from dCheckBox import dCheckBox
from dLabel import dLabel
import dMessageBox, dEvents

class dPage(wx.Panel, dControlMixin):
        
    def __init__(self, parent, name="dPage"):
        wx.Panel.__init__(self, parent, 0)
        dControlMixin.__init__(self, name)

        self.initSizer()
        self.itemsFilled = False
        
    def initSizer(self):
        ''' Set up the default vertical box sizer for the page.
        '''
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
    def fillItems(self):
        ''' Fill the controls in the page.
        
        Called when the page is entered.
        '''
        pass
        
    def onEnterPage(self):
        ''' Occurs when this page becomes the active page.
        '''
        if not self.itemsFilled:
            self.fillItems()
            self.itemsFilled = True
        
    def onLeavePage(self):
        ''' Occurs when this page will no longer be the active page.
        '''
        pass
        
    def onValueRefresh(self, event):
        ''' Occurs when the dForm asks dControls to refresh themselves.
        
        While dPage isn't a data-aware control, this may be useful information
        to act upon.
        '''
        event.Skip()
    

class dSelectPage(dPage):
    
    def fillItems(self):
        dataSource = self.getDform().getBizobj().dataSource
        columnDefs = self.getDform().getColumnDefs(dataSource)

        stringMatchAll = []
        
        for column in columnDefs:
            for selectType in column["selectTypes"]:
                if selectType == "stringMatchAll":
                    stringMatchAll.append(column)

        if len(stringMatchAll) > 0:        
            labelCaption = "String Match:"
            labelWidth = 150

            bs = wx.BoxSizer(wx.HORIZONTAL)

            labelAlignment = wx.ALIGN_RIGHT

            label = dLabel(self, windowStyle = labelAlignment|wx.ST_NO_AUTORESIZE)
            label.SetSize((labelWidth,-1))
            label.SetName("lblStringMatchAll")
            label.SetLabel(labelCaption)
                
            objectRef = dTextBox(self)
            objectRef.SetName("stringMatchAll")

            bs.Add(label)
            bs.Add(objectRef, 1, wx.ALL, 0)

            self.GetSizer().Add(bs, 0, wx.EXPAND)

        self.GetSizer().Layout()


class dBrowsePage(dPage):
    def __init__(self, parent):
        dPage.__init__(self, parent, "BrowsePage")
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.gridExists = False
    
    def onRowNumChanged(self, event):
        # If RowNumChanged is received AND we are the
        # active page, select the row in the grid
        pf = self.GetParent()
        if not self.gridExists:
            self.createGrid()
        if self.gridExists and pf.GetPage(pf.GetSelection()) == self:
            self.fillGrid()
        event.Skip()
    
    def onEnterPage(self):
        bizobj = self.getDform().getBizobj()
        if bizobj and bizobj.getRowCount() >= 0:
            if not self.gridExists:
                self.createGrid()
            if self.gridExists:
                self.fillGrid()
            
    def createGrid(self):
        form = self.getDform()
        bizobj = form.getBizobj()
        self.grid = dGrid(self, bizobj, form)
        self.grid.AutoSizeColumns(True)
        self.GetSizer().Add(self.grid, 1, wx.EXPAND)
        self.GetSizer().Layout()
        self.gridExists = True
        self.grid.SetFocus()

    def fillGrid(self):
        form = self.getDform()
        bizobj = form.getBizobj()
        self.grid.columnDefs = form.getColumnDefs(bizobj.dataSource)
        self.grid.fillGrid()
        
    def editRecord(self):
        # Called by the grid: user wants to edit the current row
        self.GetParent().SetSelection(2)

                
class dEditPage(dPage):
    def onEnterPage(self):
        dPage.onEnterPage(self)
        self.onValueRefresh()

    def onValueRefresh(self, event=None):
        form = self.getDform()
        bizobj = form.getBizobj()
        if bizobj and bizobj.getRowCount() >= 0:
            self.Enable(True)
        else:
            self.Enable(False)
        if event:
            event.Skip()
        
    def fillItems(self):
        dataSource = self.getDform().getBizobj().dataSource
        columnDefs = self.getDform().getColumnDefs(dataSource)
            
        for column in columnDefs:
            
            if column["showEdit"] == True:
                fieldName = column["fieldName"]
                labelCaption = "%s:" % column["caption"]
                fieldType = column["type"]
                fieldEnabled = column["editEdit"]
                
                labelWidth = 150
                
                bs = wx.BoxSizer(wx.HORIZONTAL)
                
                labelAlignment = wx.ALIGN_RIGHT

                label = dLabel(self, windowStyle = labelAlignment|wx.ST_NO_AUTORESIZE)
                label.SetSize((labelWidth,-1))
                label.SetName("lbl%s" % fieldName)
                label.SetLabel(labelCaption)
                
                if fieldType in ["M",]:
                    classRef = dEditBox
                elif fieldType in ["I",]:
                    classRef = dSpinner
                elif fieldType in ["L",]:
                    classRef = dCheckBox
                else:
                    classRef = dTextBox
                
                objectRef = classRef(self, fieldName)
                objectRef.dataSource = dataSource
                objectRef.dataField = fieldName
                objectRef.Enable(fieldEnabled)
                if self.getDform().getBizobj().getRowCount() >= 0:
                    objectRef.refresh()

                if fieldType in ["M",]:
                    expandFlags = wx.EXPAND
                else:
                    expandFlags = 0
                bs.Add(label)
                bs.Add(objectRef, 1, expandFlags|wx.ALL, 0)
                        
                if fieldType in ["M",]:
                    self.GetSizer().Add(bs, 1, wx.EXPAND)
                else:
                    self.GetSizer().Add(bs, 0, wx.EXPAND)
                
        self.GetSizer().Layout()

