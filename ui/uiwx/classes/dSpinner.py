import wx
import dControlMixin as cm
import dDataControlMixin as dcm

class dSpinner(wx.SpinCtrl, dcm.dDataControlMixin, cm.dControlMixin):
    
    def __init__(self, parent, name="dSpinner"):
        pre = wx.PreSpinCtrl()
        self.beforeInit(pre)                  # defined in dPemMixin
        pre.Create(parent, -1)
        
        self.this = pre.this
        self._setOORInfo(self)
        
        cm.dControlMixin.__init__(self, name)
        dcm.dDataControlMixin.__init__(self)
        self.afterInit()                      # defined in dPemMixin

    
    def afterInit(self):
        self.SpinnerLowValue = -64000
        self.SpinnerHighValue = 64000
        dSpinner.doDefault()
    
    
    def initEvents(self):
        # init the common events:
        cm.dControlMixin.initEvents(self)
        dcm.dDataControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_SPINCTRL(self, self.GetId(), self.OnSpin)
        wx.EVT_TEXT(self, self.GetId(), self.OnText)

    # Event callback method(s) (override in subclasses):
    def OnSpin(self, event): pass
    def OnText(self, event): pass

    
    # Property get/set/del methods follow. Scroll to bottom to see the property
    # definitions themselves.
    def _getSpinnerHighValue(self):
        return self.GetMax()
    def _setSpinnerHighValue(self, value):
        rangeLow = self.SpinnerLowValue
        rangeHigh = int(value)
        self.SetRange(rangeLow, rangeHigh)
    
    def _getSpinnerLowValue(self):
        return self.GetMin()
    def _setSpinnerLowValue(self, value):
        rangeLow = int(value)
        rangeHigh = self.SpinnerHighValue
        self.SetRange(rangeLow, rangeHigh)
    
    # Property definitions:
    SpinnerLowValue = property(_getSpinnerLowValue, _setSpinnerLowValue, None, 
                        'Specifies the lowest possible value for the spinner.')
    
    SpinnerHighValue = property(_getSpinnerHighValue, _setSpinnerHighValue, None, 
                        'Specifies the highest possible value for the spinner.')

if __name__ == "__main__":
    import test
    class c(dSpinner):
        def OnSpin(self, event): print "OnSpin!"
        def OnText(self, event): print "OnText!"
    test.Test().runTest(c)
