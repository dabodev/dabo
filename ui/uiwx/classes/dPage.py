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
        if self.gridExists and pf.GetPage(pf.GetSelection()) == self:
            newRowNum = self.getDform().getBizobj().getRowNumber()
            col = self.grid.GetGridCursorCol()
            self.grid.SetGridCursor(newRowNum, col)
            if not self.grid.IsVisible(newRowNum, col):
                self.grid.MakeCellVisible(newRowNum, col)

    def onEnterPage(self):
        # For now, completely destroy the exising grid, if
        # any, and create it again. This seems to perform
        # very well anyway, but it is admittedly a complete
        # waste to have to do this every time the page is
        # activated... 
        if self.gridExists:
            self.GetSizer().RemoveWindow(self.grid)
            self.grid.Destroy()

        form = self.getDform()
        bizobj = form.getBizobj()
        if bizobj and bizobj.getRowCount() >= 0:
            self.grid = dGrid(self, bizobj, form)
            self.grid.AutoSizeColumns(True)
            self.grid.SetFocus()
            self.GetSizer().Add(self.grid, 1, wx.EXPAND)
            self.GetSizer().Layout()

            self.gridExists = True
        else:
            dMessageBox.stop("The browse grid cannot be displayed as there doesn't"
                             " appear to be a cursor available.")
            
                
class dEditPage(dPage): pass
