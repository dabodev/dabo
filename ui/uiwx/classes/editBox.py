import wx
import common

# The EditBox is just a TextBox with some additional styles,
# but what the hey, I'm used to having a separate control.
# Drink Dabo. It's good for you.

class EditBox(wx.TextCtrl, common.Common):
    def __init__(self, frame, widgetId=-1):
        if widgetId < 0:
            widgetId = wx.NewId()
        wx.TextCtrl.__init__(self, frame, widgetId, '', (-1,-1), (-1,-1), 
                wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_LINEWRAP)
        self.SetName("EditBox")
        common.Common.__init__(self)

        self.selectOnEntry = False
            
    def initEvents(self):
        # init the common events:
        common.Common.initEvents(self)
        
        # init the widget's specialized event(s):
        wx.EVT_TEXT(self, self.GetId(), self.onEvent)

    # Event callback methods (override in subclasses):
    def OnText(self, event): pass

if __name__ == "__main__":
    import test
    test.Test().runTest(EditBox)
