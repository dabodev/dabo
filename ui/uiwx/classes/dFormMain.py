''' dFormMain.py '''
import wx
from dFormMixin import dFormMixin

class dFormMain(wx.Frame, dFormMixin):
    def __init__(self, dApp):
        wx.MDIParentFrame.__init__(self, None, -1)
        self.SetName("dFormMain")
        dFormMixin.__init__(self, dApp)
        
        self.CreateStatusBar()
        if self.dApp:
            self.SetStatusText("Welcome to %s" % self.dApp.getAppInfo("appName"))
        
        self.SetMenuBar(mainMenu.MainMenuBar(self))
        
    def statusMessage(self, message=""):
        statusBar = self.GetStatusBar()
        try:
            statusBar.PopStatusText()
        except:
            pass
        statusBar.PushStatusText(message)
        statusBar.Update()  # Refresh() doesn't work, and this is only needed sometimes.
        
