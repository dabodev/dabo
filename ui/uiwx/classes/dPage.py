''' dPage.py '''
import wx

class dPage(wx.Panel):
    ''' Base class for the dynamic pages. Subclass 'EditPage' 
        and not this class.'''
        
    def __init__(self, parent, name="Page"):
        wx.Panel.__init__(self, parent, 0)
        self.SetName(name)
        self.dPageFrame = parent
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
class dBrowsePage(dPage): pass
class dEditPage(dPage): pass
