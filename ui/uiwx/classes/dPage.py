''' dPage.py '''
import wx
from dGrid import dGrid
from dControlMixin import dControlMixin
import dMessageBox, dEvents

class dPage(wx.Panel, dControlMixin):
        
    def __init__(self, parent, name="dPage"):
        wx.Panel.__init__(self, parent, 0)
        dControlMixin.__init__(self, name)

        self.initSizer()
        self.fillItems()
        
    def initSizer(self):
        ''' dPage.initSizer() -> None
        
            Sets up the default sizer for the page, which is
            a vertical box sizer. Override if you want something
            different.
        '''
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
    def fillItems(self):
        ''' dPage.fillItems() -> None
        
            Called during page init. This is where to add your
            controls to the page.
        '''
        pass
        
    def onEnterPage(self):
        ''' dPage.onEnterPage() -> None
        
            This method gets called when this page becomes the 
            active page.
        '''
        pass
        
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
        self.grid.columnDefs = form.getGridColumnDefs(bizobj.dataSource)
        self.grid.fillGrid()
        
    def editRecord(self):
        # Called by the grid: user wants to edit the current row
        self.GetParent().SetSelection(2)
        
class dEditPage(dPage):
    def onEnterPage(self):
        self.onValueRefresh()

    def onValueRefresh(self, event=None):
        form = self.getDform()
        bizobj = form.getBizobj()
        if bizobj and bizobj.getRowCount() >= 0:
            self.Enable(True)
        else:
            self.Enable(False)
        