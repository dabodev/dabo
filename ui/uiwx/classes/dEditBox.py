import wx
import dControlMixin as cm
import dDataControlMixin as dcm

# The EditBox is just a TextBox with some additional styles.

class dEditBox(wx.TextCtrl, dcm.dDataControlMixin, cm.dControlMixin):
    def __init__(self, parent, name="dEditBox"):
        pre = wx.PreTextCtrl()
        self.beforeInit(pre)                  # defined in dPemMixin
        pre.Create(parent, -1, '', (-1,-1), (-1,-1),
                wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_LINEWRAP)
        
        self.this = pre.this
        self._setOORInfo(self)
        
        cm.dControlMixin.__init__(self, name)
        dcm.dDataControlMixin.__init__(self)
        self.afterInit()                      # defined in dPemMixin
 

    def afterInit(self):
        self.SelectOnEntry = False
        dEditBox.doDefault()
            
        
    def initEvents(self):
        # init the common events:
        cm.dControlMixin.initEvents(self)
        dcm.dDataControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_TEXT(self, self.GetId(), self.OnText)

    # Event callback methods (override in subclasses):
    def OnText(self, event):
        event.Skip()

if __name__ == "__main__":
    import test
    class c(dEditBox):
        def OnText(self, event): print "OnText!" 
    test.Test().runTest(c)
