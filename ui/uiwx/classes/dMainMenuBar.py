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
import dIcons

class FileMenu(m.dMenu):
    def __init__(self, mainFrame):
        FileMenu.doDefault(mainFrame)
        
        item = wx.MenuItem(self, -1, "E&xit\tAlt+F4", "Exit the application")
        item.SetBitmap(dIcons.getIconBitmap("close"))
        self.AppendItem(item)
        mainFrame.Bind(wx.EVT_MENU, self.actionList.getAction("FileExit")["func"], item)
        

class EditMenu(m.dMenu):
    def __init__(self, mainFrame):
        EditMenu.doDefault(mainFrame)
        
        item = wx.MenuItem(self, -1, "Cut\tCtrl+X", "Cut selected text")
        item.SetBitmap(dIcons.getIconBitmap("cut"))
        self.AppendItem(item)
        mainFrame.Bind(wx.EVT_MENU, self.actionList.getAction("EditCut")["func"], item)
        
        item = wx.MenuItem(self, -1, "&Copy\tCtrl+C", "Copy selected text")
        item.SetBitmap(dIcons.getIconBitmap("copy"))
        self.AppendItem(item)
        mainFrame.Bind(wx.EVT_MENU, self.actionList.getAction("EditCopy")["func"], item)

        item = wx.MenuItem(self, -1, "&Paste\tCtrl+V", "Paste text from clipboard")
        item.SetBitmap(dIcons.getIconBitmap("paste"))
        self.AppendItem(item)
        mainFrame.Bind(wx.EVT_MENU, self.actionList.getAction("EditPaste")["func"], item)
        
        self.AppendSeparator()
        
        item = wx.MenuItem(self, -1, "&Find\tCtrl+F", "Find text in the active window")
        item.SetBitmap(dIcons.getIconBitmap("find"))
        self.AppendItem(item)
        mainFrame.Bind(wx.EVT_MENU, self.actionList.getAction("EditFind")["func"], item)
        
        self.AppendSeparator()
        
        item = wx.MenuItem(self, -1, "Preferences", "Set user preferences")
        item.SetBitmap(dIcons.getIconBitmap("configure"))
        self.AppendItem(item)
        wx.App_SetMacPreferencesMenuItemId(item.GetId())   # Put the prefs item in the App Menu on Mac
        mainFrame.Bind(wx.EVT_MENU, self.actionList.getAction("EditPreferences")["func"], item)

        
class HelpMenu(m.dMenu):
    def __init__(self, mainFrame):
        HelpMenu.doDefault(mainFrame)
        
        item = wx.MenuItem(self, -1, "&About", "About this application")
        item.SetBitmap(dIcons.getIconBitmap("apply"))
        self.AppendItem(item)
        wx.App_SetMacAboutMenuItemId(item.GetId())   # Put the about menu in the App Menu on Mac
        mainFrame.Bind(wx.EVT_MENU, self.actionList.getAction("HelpAbout")["func"], item)
        
        
class dMainMenuBar(mb.dMenuBar):
    def __init__(self, mainFrame):
        super(dMainMenuBar, self).__init__()
        self.Append(FileMenu(mainFrame), "&File")
        self.Append(EditMenu(mainFrame), "&Edit")
        self.Append(HelpMenu(mainFrame), "&Help")
        wx.App_SetMacHelpMenuTitleName("&Help")
           
