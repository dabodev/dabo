import wx, dControlMixin

class dPageFrame(wx.Notebook, dControlMixin.dControlMixin):
    def __init__(self, parent, name="dPageFrame"):
        wx.Notebook.__init__(self, parent, -1)
        dControlMixin.dControlMixin.__init__(self, name)
        self.lastSelection = 0

        
    def initEvents(self):
        dControlMixin.dControlMixin.initEvents(self)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    
    def OnPageChanged(self, event):
        ls = self.lastSelection
        cs = event.GetSelection()

        event.Skip()    # This must happen before onLeave/EnterPage below

        newPage = self.GetPage(cs)
        oldPage = self.GetPage(ls)    
        
        oldPage.onLeavePage()
        newPage.onEnterPage()
        
        self.lastSelection = cs
