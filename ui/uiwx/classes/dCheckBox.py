import wx
import dControlMixin as cm
import dDataControlMixin as dcm


class dCheckBox(wx.CheckBox, dcm.dDataControlMixin, cm.dControlMixin):
    def __init__(self, parent, name="dCheckBox", label=""):
        
        self._baseClass = dCheckBox
        
        pre = wx.PreCheckBox()
        self.beforeInit(pre)                  # defined in dPemMixin
        pre.Create(parent, -1, label)
        
        self.this = pre.this
        self._setOORInfo(self)
        
        cm.dControlMixin.__init__(self, name)
        dcm.dDataControlMixin.__init__(self)
        self.afterInit()                      # defined in dPemMixin

            
    def initEvents(self):
        # init the common events:
        cm.dControlMixin.initEvents(self)
        dcm.dDataControlMixin.initEvents(self)
        
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
