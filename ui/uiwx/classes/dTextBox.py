import wx
import dControlMixin as cm
import dDataControlMixin as dcm

class dTextBox(wx.TextCtrl, dcm.dDataControlMixin, cm.dControlMixin):
    def __init__(self, parent, name="dTextBox"):
        
        self._baseClass = dTextBox
        
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
    
    def _getPasswordEntry(self):
        return self.hasWindowStyleFlag(wx.TE_PASSWORD)
    def _setPasswordEntry(self, value):
        if value:
            self.addWindowStyleFlag(wx.TE_PASSWORD)
        else:
            self.delWindowStyleFlag(wx.TE_PASSWORD)
                
    # Property definitions:
    Alignment = property(_getAlignment, _setAlignment, None,
                        'Specifies the alignment of the text. (int) \n'
                        '   0 : Left (default) \n'
                        '   1 : Center \n'
                        '   2 : Right')
    ReadOnly = property(_getReadOnly, _setReadOnly, None, 
                        'Specifies whether or not the text can be edited. (bool)')
                        
    PasswordEntry = property(_getPasswordEntry, _setPasswordEntry, None,
                        'Specifies whether plain-text or asterisks are echoed. (bool)')
    

if __name__ == "__main__":
    import test
    class c(dTextBox):
        def OnText(self, event): print "OnText!"
    test.Test().runTest(c)
