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
