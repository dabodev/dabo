import wx
from dPage import *
from dControlMixin import dControlMixin

class dPageFrame(wx.Notebook, dControlMixin):
    def __init__(self, parent, name="dPageFrame"):
        wx.Notebook.__init__(self, parent, -1)
        dControlMixin.__init__(self, name)
        self.addDefaultPages()        
        self.lastSelection = 0

    def initEvents(self):
        dControlMixin.initEvents(self)
        wx.EVT_NOTEBOOK_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)

    def addDefaultPages(self):
        ''' dPageFrame.addDefaultPages() -> None
         
            Add the standard pages, plus the childview page(s)
            if there are any. Subclasses may override or extend.
        '''
        self.AddPage(dSelectPage(self), "Select")
        self.AddPage(dBrowsePage(self), "Browse")
        self.AddPage(dEditPage(self), "Edit")
        
    def OnPageChanged(self, event):
        newPage = self.GetPage(event.GetSelection())
        oldPage = self.GetPage(self.lastSelection)    
        
        oldPage.onLeavePage()
        newPage.onEnterPage()
        
        self.lastSelection = self.GetSelection()

        event.Skip()

