import wx
from dControlMixin import dControlMixin
from dDataControlMixin import dDataControlMixin

class dCheckBox(wx.CheckBox, dDataControlMixin, dControlMixin):
    def __init__(self, parent, name="dCheckBox", label=""):
        wx.CheckBox.__init__(self, parent, -1, label)
        dControlMixin.__init__(self, name)
        dDataControlMixin.__init__(self)

        self.selectOnEntry = False
            
    def initEvents(self):
        # init the common events:
        dControlMixin.initEvents(self)
        dDataControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_CHECKBOX(self, self.GetId(), self.OnCheckBox)

    # Event callback methods (override in subclasses):
    def OnCheckBox(self, event):
        event.Skip()

if __name__ == "__main__":
    import test
    class c(dCheckBox):
        def OnCheckBox(self, event): print "OnCheckBox!" 
    test.Test().runTest(c)
