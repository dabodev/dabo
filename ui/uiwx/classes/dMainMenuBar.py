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
from dMenu import dMenu
from dMenuBar import dMenuBar

class FileOpenMenu(dMenu):
    def __init__(self, mainFrame):
        dMenu.__init__(self)
        self.mainFrame = mainFrame
        menu = self._getFileOpenMenu()
        self._fillMenu(menu, self) # recurse the items
            
    def _fillMenu(self, menuDict, parent):
        try:
            caption = menuDict["caption"]
        except KeyError:
            caption = "?"
        
        try:
            statusBarText = menuDict["statusBarText"]
        except KeyError:
            statusBarText = ""
                    
        try:
            submenu = menuDict["items"]
        except KeyError:
            submenu = []
        
        if submenu == []:
            ######## This was old Dabo
            pass
            
            # If this is a dynamicView-generated frame we are about to
            # open, the id has already been defined in the dynViewDef.
            # If not, just get a new id.
            
            #dynviews = wx.GetApp().dApp.dbDynamicViews
            #try:
            #    Id = dynviews[menuDict["viewDef"]]["Id"]
                #print "Dyn view Id found"
            #except KeyError:
                #print "Dyn view Id not found..."
            #    Id = wx.NewId()
            #menuItem = parent.Append(Id, caption, statusBarText)
            #wx.EVT_MENU(self.mainFrame, Id, self.mainFrame.OnFileOpen)

        else:
            if caption <> "?":
                Id = wx.NewId()
                menuItem = wx.Menu()
                parent.AppendMenu(Id, caption, menuItem, statusBarText)
            else:
                menuItem = parent
                
            for item in submenu:
                self._fillMenu(item, menuItem)
            

    def _getFileOpenMenu(self):
        try:
            #import dynamicMenus.menuFileOpen as menuDef
            #menu = menuDef.fileOpenMenuDef
### old (static) way:
#            file = open("./dynamicMenus/menuFileOpen.py", "r")
#            rs = wx.GetApp().dbc.dbRecordSet("select mname as mname, "
#                                "mvalue as mvalue from dabosettings "
#                                "where mname = 'menuFileOpen' and ldeleted=0")
#            file = rs[0].mvalue
#            exec(file) # creates the fileOpenMenuDef variable
            menu = fileOpenMenuDef
        except:
            menu = {}
            
        return menu
    
class FileMenu(wx.Menu):
    def __init__(self, mainFrame):
        wx.Menu.__init__(self)
#         Id = 23
#         self.AppendMenu(Id, "&Open\tCtrl+O", FileOpenMenu(mainFrame))
# 
#         Id = wx.NewId()
#         self.Append(Id, "&New Record\tCtrl+N", "Add a new record in the current window.")
#         #wx.EVT_MENU(mainFrame, Id,  mainFrame.OnNewRecord)
#         
        
        'App_SetMacHelpMenuTitleName', 'App_SetMacPreferencesMenuItemId', 'App_SetMacSupportPCMenuShortcuts'
        Id = wx.NewId()
        self.Append(Id, "E&xit", "Exit")
        wx.App_SetMacExitMenuItemId(Id)   # Put the Exit item in the App Menu on Mac
        wx.EVT_MENU(mainFrame, Id,  mainFrame.dApp.actionList.getAction("FileExit")["func"])


class EditMenu(dMenu):
    def __init__(self, mainFrame):
        dMenu.__init__(self)
        
        Id = wx.NewId()
        self.Append(Id, "&Copy", "Copy selected text")

        self.AppendSeparator()
        
        Id = wx.NewId()
        self.Append(Id, "Preferences", "Set user preferences")
        wx.App_SetMacPreferencesMenuItemId(Id)   # Put the prefs item in the App Menu on Mac
        wx.EVT_MENU(mainFrame, Id,  mainFrame.dApp.actionList.getAction("EditPreferences")["func"])
        
        
class HelpMenu(dMenu):
    def __init__(self, mainFrame):
        dMenu.__init__(self)
        
        Id = wx.NewId()
        self.Append(Id, "&About", "About")
        wx.App_SetMacAboutMenuItemId(Id)   # Put the about menu in the App Menu on Mac
        wx.EVT_MENU(mainFrame, Id, mainFrame.dApp.actionList.getAction("HelpAbout")["func"])

        
class dMainMenuBar(dMenuBar):
    def __init__(self, mainFrame):
        dMenuBar.__init__(self)
        self.Append(FileMenu(mainFrame), "&File")
        self.Append(EditMenu(mainFrame), "&Edit")
        self.Append(HelpMenu(mainFrame), "&Help")
            
