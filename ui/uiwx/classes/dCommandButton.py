import wx
import dControlMixin as cm

class dCommandButton(wx.Button, cm.dControlMixin):
    def __init__(self, parent, name="dCommandButton", label="", 
            pos=wx.DefaultPosition, size=wx.DefaultSize):
        
        pre = wx.PreButton()
        self.beforeInit(pre)                  # defined in dPemMixin
        pre.Create(parent, -1, label, pos, size)
        
        self.this = pre.this
        self._setOORInfo(self)
        
        cm.dControlMixin.__init__(self, name)
        self.afterInit()                      # defined in dPemMixin
        
        
    def initEvents(self):
        # init the common events:
        cm.dControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_BUTTON(self, self.GetId(), self.OnButton)
        
    # Event callback methods (override in subclasses):
    def OnButton(self, event):
        event.Skip()

    
    # Property get/set/del methods follow. Scroll to bottom to see the property
    # definitions themselves.
    def _getDefault(self):
        return self.Parent.GetDefaultItem() == self
    def _setDefault(self, value):
        if value:
            self.Parent.SetDefaultItem(self)
        else:
            self.Parent.SetDefaultItem(None)
        
    
    # Property definitions:
    Default = property(_getDefault, _setDefault, None, 
                        'Specifies whether this command button gets clicked on <Enter>. (bool)')
              
               
if __name__ == "__main__":
    import test
    class c(dCommandButton):
        def OnButton(self, event): print "Button!"

    test.Test().runTest(c)
