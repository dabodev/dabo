""" dabo: mainMenu.py 

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
import dynamicViewWidgets as dynview

class FileOpenMenu(wx.Menu):
    def __init__(self, mainFrame):
        wx.Menu.__init__(self)
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
            # If this is a dynamicView-generated frame we are about to
            # open, the id has already been defined in the dynViewDef.
            # If not, just get a new id.
            dynviews = wx.GetApp().dynamicViews
            try:
                Id = dynviews[menuDict["viewDef"]]["Id"]
                #print "Dyn view Id found"
            except KeyError:
                #print "Dyn view Id not found..."
                Id = wx.NewId()
            menuItem = parent.Append(Id, caption, statusBarText)
            wx.EVT_MENU(self.mainFrame, Id, self.mainFrame.OnFileOpen)

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
            file = open("./dynamicMenus/menuFileOpen.py", "r")
#            rs = wx.GetApp().dbc.dbRecordSet("select mname as mname, "
#                                "mvalue as mvalue from dabosettings "
#                                "where mname = 'menuFileOpen' and ldeleted=0")
#            file = rs[0].mvalue
            exec(file) # creates the fileOpenMenuDef variable
            menu = fileOpenMenuDef
        except:
            menu = {}
            
        return menu
    
class FileMenu(wx.Menu):
    def __init__(self, mainFrame):
        wx.Menu.__init__(self)
        Id = 23
        self.AppendMenu(Id, "&Open\tCtrl+O", FileOpenMenu(mainFrame))

        Id = wx.NewId()
        self.Append(Id, "&New Record\tCtrl+N", "Add a new record in the current window.")
        wx.EVT_MENU(mainFrame, Id,  mainFrame.OnNewRecord)
        
        Id = wx.NewId()
        self.Append(Id, "E&xit", "Exit")
        wx.EVT_MENU(mainFrame, Id,  mainFrame.OnExit)


class EditMenu(wx.Menu):
    def __init__(self, mainFrame):
        wx.Menu.__init__(self)
        
        Id = wx.NewId()
        self.Append(Id, "&Copy", "Copy selected text")
        
        Id = wx.NewId()
        self.Append(Id, "alt+1\tAlt+1")
        wx.EVT_MENU(mainFrame, Id, mainFrame.OnAlt1)
        
        Id = wx.NewId()
        self.Append(Id, "alt+2\tAlt+2")
        wx.EVT_MENU(mainFrame, Id, mainFrame.OnAlt2)
        
        Id = wx.NewId()
        self.Append(Id, "alt+3\tAlt+3")
        wx.EVT_MENU(mainFrame, Id, mainFrame.OnAlt3)

        Id = wx.NewId()
        self.Append(Id, "alt+4\tAlt+4")
        wx.EVT_MENU(mainFrame, Id, mainFrame.OnAlt4)
        
class HelpMenu(wx.Menu):
    def __init__(self, mainFrame):
        wx.Menu.__init__(self)
        
        Id = wx.NewId()
        self.Append(Id, "&About", "About")
        wx.EVT_MENU(mainFrame, Id, mainFrame.OnAbout)

class MainMenuBar(wx.MenuBar):
    def __init__(self, mainFrame):
        wx.MenuBar.__init__(self)
        self.Append(FileMenu(mainFrame), "&File")
        self.Append(EditMenu(mainFrame), "&Edit")
        self.Append(HelpMenu(mainFrame), "&Help")
