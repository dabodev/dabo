import commandButton, wx

class CommandButtonCancel(commandButton.CommandButton):
    def __init__(self, frame):
        widgetId = wx.NewId()
        commandButton.CommandButton.__init__(self, frame, widgetId)
        self.SetLabel("Cancel")
        
    # Event callback methods (override in subclasses):
    def OnButton(self, event):
        self.frame.EndModal(wx.ID_CANCEL)
        
   
if __name__ == "__main__":
    import test
    test.Test().runTest(CommandButton)
