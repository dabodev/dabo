''' dPage.py '''
import wx
from dGrid import dGrid

class dPage(wx.Panel):
    ''' Base class for the dynamic pages. Subclass 'EditPage' 
        and not this class.'''
        
    def __init__(self, parent, name="Page"):
        wx.Panel.__init__(self, parent, 0)
        self.SetName(name)
        self.parent = parent
        #scrollBarStep = 10 # (make this a user-setting)
        #self.SetScrollbars(scrollBarStep,scrollBarStep,-1,-1) # only show scrollbars if necessary

        self.initSizer()
        self.fillItems()
    
    def initSizer(self):
        ''' override if you want something else '''
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
    def fillItems(self): pass
    def onEnterPage(self): pass
    def onLeavePage(self): pass

    

class dSelectPage(dPage): pass

class dBrowsePage(dPage):
    def __init__(self, parent):
        dPage.__init__(self, parent, "BrowsePage")
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.gridExists = False
    
    def onEnterPage(self):
        if self.gridExists:
            self.GetSizer().RemoveWindow(self.grid)
            self.grid.Destroy()

        bizobj = self.parent.parent.getBizobj()
        if bizobj and bizobj.getRowCount() >= 0:
            self.grid = dGrid(self, bizobj)
            self.grid.AutoSizeColumns(True)
            self.grid.SetFocus()
            self.GetSizer().Add(self.grid, 1, wx.EXPAND)
            self.GetSizer().Layout()
            self.gridExists = True
            
                
class dEditPage(dPage): pass
