''' dFormMain.py '''
import wx
from dFormMixin import dFormMixin
from dMainMenuBar import dMainMenuBar

class dFormMain(wx.Frame, dFormMixin):
    def __init__(self, dApp=None):
        wx.Frame.__init__(self, None, -1, "dFormMain")
        self.SetName("dFormMain")
        dFormMixin.__init__(self, dApp)
        
        self.CreateStatusBar()
        if self.dApp:
            self.SetStatusText("Welcome to %s" % self.dApp.getAppInfo("appName"))
            self.SetLabel("%s Version %s" % (self.dApp.getAppInfo("appName"),
                                             self.dApp.getAppInfo("appVersion")))
        else:
            self.SetLabel("Dabo")
            self.SetStatusText("Welcome to Dabo!")
        
        self.SetMenuBar(dMainMenuBar(self))
        self.SetSize((640,480))
        self.SetPosition((0,0))
        
    def statusMessage(self, message=""):
        statusBar = self.GetStatusBar()
        try:
            statusBar.PopStatusText()
        except:
            pass
        statusBar.PushStatusText(message)
        statusBar.Update()  # Refresh() doesn't work, and this is only needed sometimes.
    
 
        
if __name__ == "__main__":
    import test
    test.Test().runTest(dFormMain)
