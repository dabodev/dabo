import wx
from dControlMixin import dControlMixin

class dTextBox(wx.TextCtrl, dControlMixin):
    def __init__(self, parent, widgetId=-1):
        if widgetId < 0:
            widgetId = wx.NewId()
        wx.TextCtrl.__init__(self, parent, widgetId)
        self.SetName("dTextBox")
        dControlMixin.__init__(self)

        self.selectOnEntry = True
            
    def initEvents(self):
        # init the common events:
        dControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_TEXT(self, self.GetId(), self.onEvent)


    # Event callback method(s) (override in subclasses):
    def OnText(self, event): pass
    

if __name__ == "__main__":
    import test
    class c(dTextBox):
        def OnText(self, event): print "OnText!"
    test.Test().runTest(c)
