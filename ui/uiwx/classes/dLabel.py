import wx
import dControlMixin as cm

class dLabel(wx.StaticText, cm.dControlMixin):
    def __init__(self, parent, name="dLabel", label="", windowStyle=None):
        
        self._baseClass = dLabel
        
        pre = wx.PreStaticText()
        self.beforeInit(pre)                  # defined in dPemMixin
        pre.Create(parent, -1, label, (-1,-1), (-1,-1), windowStyle)
        
        self.this = pre.this
        self._setOORInfo(self)
        
        cm.dControlMixin.__init__(self, name)
        self.afterInit()                      # defined in dPemMixin
    
        
    def initEvents(self):
        # init the common events:
        cm.dControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):

        
if __name__ == "__main__":
    import test
    test.Test().runTest(dLabel)
