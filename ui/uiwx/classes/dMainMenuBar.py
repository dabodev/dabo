""" dMainMenuBar.py

This module contains the class definitions and logic to build
the main menu for all platforms. There are special needs for
complying with Apple's Human Interface Guidelines, for instance.
Also, some submenus, such as File|Open, get built dynamically
based on menu definition files in your custom app directory
hierarchy. The code here handles all that for you. 
    
ToDo: make these classes easily subclassable by the custom
app developer, so certain behavior can be overridden and/or
extended.
"""
import wx, os
import dMenu as m
import dMenuBar as mb

class FileMenu(m.dMenu):
    def __init__(self, mainFrame):
        super(FileMenu, self).__init__()
        
        Id = wx.NewId()
        self.Append(Id, "E&xit", "Exit")
        wx.App_SetMacExitMenuItemId(Id)   # Put the Exit item in the App Menu on Mac
        wx.EVT_MENU(mainFrame, Id,  mainFrame.dApp.actionList.getAction("FileExit")["func"])


class EditMenu(m.dMenu):
    def __init__(self, mainFrame):
        super(EditMenu, self).__init__()
        
        Id = wx.NewId()
        self.Append(Id, "&Copy", "Copy selected text")

        self.AppendSeparator()
        
        Id = wx.NewId()
        self.Append(Id, "Preferences", "Set user preferences")
        wx.App_SetMacPreferencesMenuItemId(Id)   # Put the prefs item in the App Menu on Mac
        wx.EVT_MENU(mainFrame, Id,  mainFrame.dApp.actionList.getAction("EditPreferences")["func"])
        
        
class HelpMenu(m.dMenu):
    def __init__(self, mainFrame):
        super(HelpMenu, self).__init__()
        
        Id = wx.NewId()
        self.Append(Id, "&About", "About")
        wx.App_SetMacAboutMenuItemId(Id)   # Put the about menu in the App Menu on Mac
        wx.EVT_MENU(mainFrame, Id, mainFrame.dApp.actionList.getAction("HelpAbout")["func"])

        
class dMainMenuBar(mb.dMenuBar):
    def __init__(self, mainFrame):
        super(dMainMenuBar, self).__init__()
        self.Append(FileMenu(mainFrame), "&File")
        self.Append(EditMenu(mainFrame), "&Edit")
        self.Append(HelpMenu(mainFrame), "&Help")
            
