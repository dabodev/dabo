import wx
from dControlMixin import dControlMixin
from dDataControlMixin import dDataControlMixin

class dTextBox(wx.TextCtrl, dDataControlMixin, dControlMixin):
    def __init__(self, parent, name="dTextBox"):
        wx.TextCtrl.__init__(self, parent, -1)
        dControlMixin.__init__(self, name)
        dDataControlMixin.__init__(self)

        self.SelectOnEntry = True
            
    def initEvents(self):
        # init the common events:
        dControlMixin.initEvents(self)
        dDataControlMixin.initEvents(self)
        
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
