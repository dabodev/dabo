import wx
from dControlMixin import dControlMixin
from dDataControlMixin import dDataControlMixin

class dSpinner(wx.SpinCtrl, dDataControlMixin, dControlMixin):
    def __init__(self, parent, name="dSpinner"):
        wx.SpinCtrl.__init__(self, parent, -1)
        dControlMixin.__init__(self, name)
        dDataControlMixin.__init__(self)
        
        self.SetRange(-64000, 64000)
    
    def initEvents(self):
        # init the common events:
        dControlMixin.initEvents(self)
        dDataControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_SPINCTRL(self, self.GetId(), self.onEvent)
        wx.EVT_TEXT(self, self.GetId(), self.onEvent)

    # Event callback method(s) (override in subclasses):
    def OnSpin(self, event): pass
    def OnText(self, event): pass
    
if __name__ == "__main__":
    import test
    class c(dSpinner):
        def OnSpin(self, event): print "OnSpin!"
        def OnText(self, event): print "OnText!"
    test.Test().runTest(c)
