import wx
import common

class TextBox(wx.TextCtrl, common.Common):
    def __init__(self, parent, widgetId=-1):
        if widgetId < 0:
            widgetId = wx.NewId()
        wx.TextCtrl.__init__(self, parent, widgetId)
        self.SetName("TextBox")
        common.Common.__init__(self)

        self.selectOnEntry = True
            
    def initEvents(self):
        # init the common events:
        common.Common.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_TEXT(self, self.GetId(), self.onEvent)

    # Event callback method(s) (override in subclasses):
    def OnText(self, event):
        event.Skip()
    

if __name__ == "__main__":
    import test
    test.Test().runTest(TextBox)
