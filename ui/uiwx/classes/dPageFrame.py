import wx, dControlMixin

class dPageFrame(wx.Notebook, dControlMixin.dControlMixin):
    
    def __init__(self, parent, name="dPageFrame"):
        
        self._baseClass = dPageFrame
        
        pre = wx.PreNotebook()
        self.beforeInit(pre)                  # defined in dPemMixin
        pre.Create(parent, -1)
        
        self.this = pre.this
        self._setOORInfo(self)
        
        dControlMixin.dControlMixin.__init__(self, name)
        self.afterInit()                      # defined in dPemMixin
        
        
    def afterInit(self):
        self.lastSelection = 0
        dPageFrame.doDefault()

        
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
