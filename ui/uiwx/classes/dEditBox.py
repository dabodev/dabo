import wx
from dControlMixin import dControlMixin
from dDataControlMixin import dDataControlMixin

# The EditBox is just a TextBox with some additional styles.

class dEditBox(wx.TextCtrl, dDataControlMixin, dControlMixin):
    def __init__(self, frame, widgetId=-1):
        if widgetId < 0:
            widgetId = wx.NewId()
        wx.TextCtrl.__init__(self, frame, widgetId, '', (-1,-1), (-1,-1), 
                wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_LINEWRAP)
        self.SetName("dEditBox")
        dControlMixin.__init__(self)
        dDataControlMixin.__init__(self)

        self.selectOnEntry = False
            
    def initEvents(self):
        # init the common events:
        dControlMixin.initEvents(self)
        dDataControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_TEXT(self, self.GetId(), self.onEvent)

    # Event callback methods (override in subclasses):
    def OnText(self, event): pass

if __name__ == "__main__":
    import test
    class c(dEditBox):
        def OnText(self, event): print "OnText!" 
    test.Test().runTest(c)
