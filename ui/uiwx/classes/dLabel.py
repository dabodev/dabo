import wx
import dControlMixin as cm

class dLabel(wx.StaticText, cm.dControlMixin):
    def __init__(self, parent, name="dLabel", label="", windowStyle=None):
        wx.StaticText.__init__(self, parent, -1, label, (-1,-1), (-1,-1), windowStyle)
        cm.dControlMixin.__init__(self, name)
    
        self.setDefaultFont()
        
        
    def initEvents(self):
        # init the common events:
        cm.dControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):

        
if __name__ == "__main__":
    import test
    test.Test().runTest(dLabel)
