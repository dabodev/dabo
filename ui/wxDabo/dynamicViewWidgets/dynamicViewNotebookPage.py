import wx

class Page(wx.ScrolledWindow):
    ''' Base class for the dynamic pages. Subclass 'EditPage' 
        and not this class.'''
        
    def __init__(self, parent, name="Page", style=0):
        wx.ScrolledWindow.__init__(self, parent, style)
        self.SetName(name)
        self.notebook = parent
        scrollBarStep = 10 # (make this a user-setting)
        self.SetScrollbars(scrollBarStep,scrollBarStep,-1,-1) # only show scrollbars if necessary

        self.initSizer()
        self.fillItems()
    
    def initSizer(self):
        ''' override if you want something else '''
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        
    def fillItems(self): pass
    def onEnterPage(self): pass
    def onLeavePage(self): pass

    
