import wx
from dControlMixin import dControlMixin

class dLabel(wx.StaticText, dControlMixin):
    def __init__(self, parent, name="dLabel", label="", windowStyle=None):
        wx.StaticText.__init__(self, parent, -1, label, (-1,-1), (-1,-1), windowStyle)
        dControlMixin.__init__(self, name)
    
        self.setDefaultFont()
        
    def initEvents(self):
        # init the common events:
        dControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):

if __name__ == "__main__":
    import test
    test.Test().runTest(dLabel)
