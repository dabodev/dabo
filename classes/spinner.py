import wx
import common

class Spinner(wx.SpinCtrl, common.Common):
    def __init__(self, parent):
        widgetId = wx.NewId()
        wx.SpinCtrl.__init__(self, parent, widgetId)
        self.SetName("Spinner")
        common.Common.__init__(self)
        
        self.SetRange(-64000, 64000)
    
    def initEvents(self):
        # init the common events:
        common.Common.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_SPINCTRL(self, self.GetId(), self.onEvent)

    # Event callback method(s) (override in subclasses):
    def OnSpin(self, event): pass
    

if __name__ == "__main__":
    import test
    test.Test().runTest(Spinner)
