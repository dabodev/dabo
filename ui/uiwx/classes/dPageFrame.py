import wx
from dPage import *

class dPageFrame(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, -1)
        self.SetName("dPageFrame")        
        self.parent = parent

        self.addDefaultPages()        
        self.lastSelection = 0

        wx.EVT_NOTEBOOK_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)
        
        # Put on Browse page by default:
        #self.AdvanceSelection()
    
    def addDefaultPages(self):
        """ Add the standard pages, plus the childview page(s) if any,
            as defined in the master view """
        self.AddPage(dPage(self), "Select")
        self.AddPage(dBrowsePage(self), "Browse")
        self.AddPage(dPage(self), "Edit")
    
    def setInitialStatusMessage(self, message):
        self.initialStatusMessage = message
        
    def OnPageChanged(self, event):
        newPage = self.GetPage(event.GetSelection())
        oldPage = self.GetPage(self.lastSelection)    
        
        oldPage.onLeavePage()
        newPage.onEnterPage()
        
        self.lastSelection = self.GetSelection()

        event.Skip()

