''' daboApp.py: The application object and the main frame object. '''

import sys, os, wx, wx.help
from dabo.db import *
from dabo.biz import *
from dabo.ui.uiwx.classes import *

class uiApp(wx.App):
    def OnInit(self):
        return True

    def setup(self, dApp):
        wx.InitAllImageHandlers()
        self.helpProvider = wx.help.SimpleHelpProvider()
        wx.help.HelpProvider_Set(self.helpProvider)

        self.dApp = dApp
        
        self.mainFrame = dFormMain(dApp)
        self.mainFrame.Show(True)
        self.SetTopWindow(self.mainFrame)
    
    def start(self, dApp):
        self.setup(dApp)
        self.MainLoop()
    
