import wx
import common

class Label(wx.StaticText, common.Common):
    def __init__(self, parent, widgetId=-1, caption="", 
                pos = (-1,-1), size = (-1,-1), windowStyle=wx.ST_NO_AUTORESIZE):
        if widgetId < 0:
            widgetId = wx.NewId()
        wx.StaticText.__init__(self, parent, widgetId, caption, pos, size, windowStyle)
        self.SetName("Label")
        common.Common.__init__(self)
    
        self.setDefaultFont()
        
    def initEvents(self):
        # init the common events:
        common.Common.initEvents(self)
        
        # init the widget's specialized event(s):

if __name__ == "__main__":
    import test
    test.Test().runTest(Label)
