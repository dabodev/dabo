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
        self.SetVendorName(dApp.getAppInfo("vendorName"))
        
        # I *think* this may be how to set the application name as displayed
        # as the caption of Mac's application menu. Currently, it displays as
        # "Python" and I can't find any mention of how to change this caption,
        # but I found this function by hunting and pecking. Unfortunately, I
        # don't currently have a Mac to test this on but I wanted to get this
        # in here just in case. If it only changes the caption of the help 
        # menu, that would be wrong and this should be removed.
        wx.App_SetMacHelpMenuTitleName(dApp.getAppInfo("appName"))

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
