import wx
from dControlMixin import dControlMixin

class dCommandButton(wx.Button, dControlMixin):
    def __init__(self, frame, widgetId=-1, caption=""):
        if widgetId < 0:
            widgetId = wx.NewId()
        wx.Button.__init__(self, frame, widgetId, caption)
        self.SetName("dCommandButton")
        dControlMixin.__init__(self)
        self.frame = frame
        
    def initEvents(self):
        # init the common events:
        dControlMixin.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_BUTTON(self, self.GetId(), self.onEvent)
        
    # Event callback methods (override in subclasses):
    def OnButton(self, event): pass

class dCommandButtonSave(dCommandButton):
    def __init__(self, parent):
        dCommandButton.__init__(self, parent)
        self.SetName("dCommandButtonSave")
        self.SetLabel("Save")
        
    def OnButton(self, event):
        if self.dForm:
            self.dForm.save()

class dCommandButtonCancel(dCommandButton):
    def __init__(self, parent):
        dCommandButton.__init__(self, parent)
        self.SetName("dCommandButtonCancel")
        self.SetLabel("Cancel")
        
    def OnButton(self, event):
        if self.dForm:
            self.dForm.cancel()
               
               
if __name__ == "__main__":
    import test
    class c(dCommandButton):
        def OnButton(self, event): print "Button!"

    test.Test().runTest(c)
