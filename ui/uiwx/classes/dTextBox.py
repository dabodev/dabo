import wx
import dControlMixin as cm
import dDataControlMixin as dcm

class dTextBox(wx.TextCtrl, dcm.dDataControlMixin, cm.dControlMixin):
    def __init__(self, parent, name="dTextBox"):
        pre = wx.PreTextCtrl()
        self.beforeInit(pre)                  # defined in dPemMixin
        pre.Create(parent, -1)
        
        self.this = pre.this
        self._setOORInfo(self)
        
        cm.dControlMixin.__init__(self, name)
        dcm.dDataControlMixin.__init__(self)
        self.afterInit()                      # defined in dPemMixin

    
    def afterInit(self):
        self.SelectOnEntry = True
        dTextBox.doDefault()
        
    
    def initEvents(self):
        # init the common events:
        cm.dControlMixin.initEvents(self)
        dcm.dDataControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_TEXT(self, self.GetId(), self.OnText)

        
    # Event callback method(s) (override in subclasses):
    def OnText(self, event):
        event.Skip()
    

if __name__ == "__main__":
    import test
    class c(dTextBox):
        def OnText(self, event): print "OnText!"
    test.Test().runTest(c)
