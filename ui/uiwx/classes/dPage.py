''' dPage.py '''
import wx, dPanel

class dPage(dPanel.dPanel):
        
    def __init__(self, parent, name="dPage"):
        dPage.doDefault(parent, name)
    
        
    def afterInit(self):
        self.initSizer()
        self.itemsCreated = False
        dPage.doDefault()
        
        
    def initSizer(self):
        ''' Set up the default vertical box sizer for the page.
        '''
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
    
    def createItems(self):
        ''' Create the controls in the page.
        
        Called when the page is entered for the first time, allowing subclasses
        to delay-populate the page.
        '''
        pass
        
        
    def onEnterPage(self):
        ''' Occurs when this page becomes the active page.
        
        Subclasses may override or extend.
        '''
        if not self.itemsCreated:
            self.createItems()
            self.itemsCreated = True
        
            
    def onLeavePage(self):
        ''' Occurs when this page will no longer be the active page.
        
        Subclasses may override.
        '''
        pass
        
        
    def onValueRefresh(self, event):
        ''' Occurs when the dForm asks dControls to refresh themselves.
        
        While dPage isn't a data-aware control, this may be useful information
        to act upon.
        '''
        event.Skip()
    
