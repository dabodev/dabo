import wx
from dControlMixin import dControlMixin

class dLabel(wx.StaticText, dControlMixin):
    def __init__(self, parent, widgetId=-1, caption="", 
                pos = (-1,-1), size = (-1,-1), windowStyle=wx.ST_NO_AUTORESIZE):
        if widgetId < 0:
            widgetId = wx.NewId()
        wx.StaticText.__init__(self, parent, widgetId, caption, pos, size, windowStyle)
        self.SetName("dLabel")
        dControlMixin.__init__(self)
    
        self.setDefaultFont()
        
    def initEvents(self):
        # init the common events:
        dControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):

if __name__ == "__main__":
    import test
    test.Test().runTest(dLabel)
