import wx
import dControlMixin as cm
import dDataControlMixin as dcm


class dCheckBox(wx.CheckBox, dcm.dDataControlMixin, cm.dControlMixin):
    def __init__(self, parent, id=-1, name="dCheckBox", *args, **kwargs):
        
        self._baseClass = dCheckBox
        
        pre = wx.PreCheckBox()
        self.beforeInit(pre)                  # defined in dPemMixin
        pre.Create(parent, id, name, *args, **kwargs)
        
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

    # property get/set functions
    def _getAlignment(self):
        if self.hasWindowStyleFlag(wx.ALIGN_RIGHT):
            return 2
        else:
            return 0
    def _setAlignment(self, value):
        if value == 2:
            self.addWindowStyleFlag(wx.ALIGN_RIGHT)
        else:
            self.delWindowStyleFlag(wx.ALIGN_RIGHT)
    
        
    # property definitions follow:
    Alignment = property(_getAlignment, _setAlignment, None,
                        'Specifies the alignment of the text. (int) \n'
                        '   0 : Checkbox to left of text (default) \n'
                        '   2 : Checkbox to right of text')
if __name__ == "__main__":
    import test
    class c(dCheckBox):
        def OnCheckBox(self, event): print "OnCheckBox!" 
    test.Test().runTest(c)
