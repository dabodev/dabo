import wx
import common

class CommandButton(wx.Button, common.Common):
    def __init__(self, frame, widgetId=-1, caption=""):
        if widgetId < 0:
            widgetId = wx.NewId()
        wx.Button.__init__(self, frame, widgetId, caption)
        self.SetName("CommandButton")
        common.Common.__init__(self)
        self.frame = frame
        
    def initEvents(self):
        # init the common events:
        common.Common.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_BUTTON(self, self.GetId(), self.onEvent)
        
    # Event callback methods (override in subclasses):
    def OnButton(self, event): pass
   
if __name__ == "__main__":
    import test
    test.Test().runTest(CommandButton)
