''' daboApp.py: The application object and the main frame object. '''

import sys, os, wx
from dabo.db import *
from dabo.biz import *
from dabo.ui.uiwx.classes import *

class uiApp(wx.App):
    def __init__(self, *args):
        wx.App.__init__(self, 0, args)
        
    def OnInit(self):
        return True

    def setup(self, dApp):
        wx.InitAllImageHandlers()
        
        # wx has properties for appName and vendorName, so Dabo should update
        # these. Among other possible uses, I know that on Win32 wx will use
        # these for determining the registry key structure.
        self.SetAppName(dApp.getAppInfo("appName"))
        self.SetClassName(dApp.getAppInfo("appName"))
        self.SetVendorName(dApp.getAppInfo("vendorName"))
        
        self.dApp = dApp
        
        self.mainFrame = dFormMain(dApp)
        self.SetTopWindow(self.mainFrame)

        self.mainFrame.Show(True)
        if wx.Platform == '__WXMAC__':
            self.mainFrame.SetSize((1,1))
            self.mainFrame.SetTitle(dApp.getAppInfo("appName"))    
    
    def start(self, dApp):
        self.MainLoop()
    
    def onFileExit(self):
        self.mainFrame.Close(True)

    def onEditPreferences(self):
        print "Stub: uiApp.onEditPreferences()"
        
    def onHelpAbout(self):
        dlg = dAbout(self.mainFrame, self.dApp)
        dlg.Show()
