import commandButton, wx

class CommandButtonAccept(commandButton.CommandButton):
    def __init__(self, frame):
        widgetId = wx.NewId()
        commandButton.CommandButton.__init__(self, frame, widgetId)
        self.SetLabel("Accept")
        
    # Event callback methods (override in subclasses):
    def OnButton(self, event):
        self.frame.EndModal(wx.ID_OK)
   
if __name__ == "__main__":
    import test
    test.Test().runTest(CommandButton)
