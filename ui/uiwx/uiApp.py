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
        self.SetTopWindow(self.mainFrame)
        self.mainFrame.Show(True)
    
    def start(self, dApp):
        self.MainLoop()
    
    def onFileExit(self):
        self.mainFrame.Close(True)

    def onEditPreferences(self):
        print "Stub: uiApp.onEditPreferences()"
        
    def onHelpAbout(self):
        dlg = dAbout(self.mainFrame, self.dApp)
        dlg.Show()
