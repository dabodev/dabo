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
        ''' dPage.initSizer() -> None
        
            Sets up the default sizer for the page, which is
            a vertical box sizer. Override if you want something
            different.
        '''
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
    def fillItems(self):
        ''' dPage.fillItems() -> None
        
            Called when it is time to add items to the page (when the
            page first becomes active).
        '''
        pass
        
    def onEnterPage(self):
        ''' dPage.onEnterPage() -> None
        
            This method gets called when this page becomes the 
            active page.
        '''
        if not self.itemsFilled:
            self.fillItems()
            self.itemsFilled = True
        
    def onLeavePage(self):
        ''' dPage.onLeavePage() -> None
            
            This method gets called when this page was the active
            page but another page will become the active page.
        '''
        pass
        
    def onValueRefresh(self, event):
        ''' dPage.onValueRefresh(event) -> None
        
            This method gets called when an event is received from
            dForm that controls need to refresh their values. While
            dPage isn't a data-aware control, this may be useful
            information to act on.
        '''
        event.Skip()
    

class dSelectPage(dPage): pass

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
    
    def onEnterPage(self):
        if not self.gridExists:
            self.createGrid()
        if self.gridExists:
            self.fillGrid()
            
    def createGrid(self):
        form = self.getDform()
        bizobj = form.getBizobj()
        self.grid = dGrid(self, bizobj, form)
        self.grid.AutoSizeColumns(True)
        self.grid.SetFocus()
        self.GetSizer().Add(self.grid, 1, wx.EXPAND)
        self.GetSizer().Layout()
        self.gridExists = True

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
        self.onValueRefresh()
        dPage.onEnterPage(self)

    def onValueRefresh(self, event=None):
        form = self.getDform()
        bizobj = form.getBizobj()
        if bizobj and bizobj.getRowCount() >= 0:
            self.Enable(True)
        else:
            self.Enable(False)
        
    def fillItems(self):
        try:
            dataSource = self.getDform().getBizobj().dataSource
        except (NameError, AttributeError):
            return
            
        columnDefs = self.getDform().getColumnDefs(dataSource)
            
        for column in columnDefs:
            
            if column["showEdit"] == True:
                fieldName = column["name"]
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
                
                objectRef = classRef(self)
                objectRef.Enable(fieldEnabled)
                objectRef.dataSource = dataSource
                objectRef.dataField = fieldName

                if fieldType in ["M",]:
                    expandFlags = wx.EXPAND
                else:
                    expandFlags = 0
                bs.Add(label)
                bs.Add(objectRef, 1, expandFlags|wx.ALL, 0)
                        
                objectRef.SetName(fieldName)
                
                if fieldType in ["M",]:
                    self.GetSizer().Add(bs, 1, wx.EXPAND)
                else:
                    self.GetSizer().Add(bs, 0, wx.EXPAND)
                
        self.GetSizer().Layout()

