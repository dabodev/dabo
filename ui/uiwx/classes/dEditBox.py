import wx
import dControlMixin as cm
import dDataControlMixin as dcm

# The EditBox is just a TextBox with some additional styles.

class dEditBox(wx.TextCtrl, dcm.dDataControlMixin, cm.dControlMixin):
    def __init__(self, parent, name="dEditBox"):
    
        self._baseClass = dEditBox
        
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

            
    # property get/set functions
    def _getAlignment(self):
        if self.hasWindowStyleFlag(wx.TE_RIGHT):
            return 2
        elif self.hasWindowStyleFlag(wx.TE_CENTRE):
            return 1
        else:
            return 0
    def _setAlignment(self, value):
        if value == 0:
            self.addWindowStyleFlag(wx.TE_LEFT)
        elif value == 1:
            self.addWindowStyleFlag(wx.TE_CENTRE)
        elif value == 2:
            self.addWindowStyleFlag(wx.TE_RIGHT)
    
    def _getReadOnly(self):
        return not self.IsEditable()
    def _setReadOnly(self, value):
        self.SetEditable(not value)
        
    # property definitions follow:
    Alignment = property(_getAlignment, _setAlignment, None,
                        'Specifies the alignment of the text. (int) \n'
                        '   0 : Left (default) \n'
                        '   1 : Center \n'
                        '   2 : Right')
    ReadOnly = property(_getReadOnly, _setReadOnly, None, 
                        'Specifies whether or not the text can be edited. (bool)')
    

if __name__ == "__main__":
    import test
    class c(dEditBox):
        def OnText(self, event): print "OnText!" 
    test.Test().runTest(c)
