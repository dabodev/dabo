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
	def __init__(self, mainForm):
		FileMenu.doDefault(mainForm)

		item = wx.MenuItem(self, -1, "Debug Info\tCtrl+D", "Hook for printing out debug info" ) 
		self.AppendItem(item)
		mainForm.Bind(wx.EVT_MENU, mainForm.onDebugDlg, item)

		item = wx.MenuItem(self, -1, "E&xit\tAlt+F4", "Exit the application")
		item.SetBitmap(dIcons.getIconBitmap("close"))
		self.AppendItem(item)
		mainForm.Bind(wx.EVT_MENU, self.actionList.getAction("FileExit")["func"], item)


class EditMenu(m.dMenu):
	def __init__(self, mainForm):
		EditMenu.doDefault(mainForm)

		item = wx.MenuItem(self, -1, "Undo\tCtrl+Z", "Undo last action")
		item.SetBitmap(dIcons.getIconBitmap("undo"))
		self.AppendItem(item)
		mainForm.Bind(wx.EVT_MENU, self.actionList.getAction("EditUndo")["func"], item)

		item = wx.MenuItem(self, -1, "Redo\tCtrl+R", "Redo last action")
		item.SetBitmap(dIcons.getIconBitmap("redo"))
		self.AppendItem(item)
		mainForm.Bind(wx.EVT_MENU, self.actionList.getAction("EditRedo")["func"], item)

		self.AppendSeparator()

		item = wx.MenuItem(self, -1, "Cut\tCtrl+X", "Cut selected text")
		item.SetBitmap(dIcons.getIconBitmap("cut"))
		self.AppendItem(item)
		mainForm.Bind(wx.EVT_MENU, self.actionList.getAction("EditCut")["func"], item)

		item = wx.MenuItem(self, -1, "&Copy\tCtrl+C", "Copy selected text")
		item.SetBitmap(dIcons.getIconBitmap("copy"))
		self.AppendItem(item)
		mainForm.Bind(wx.EVT_MENU, self.actionList.getAction("EditCopy")["func"], item)

		item = wx.MenuItem(self, -1, "&Paste\tCtrl+V", "Paste text from clipboard")
		item.SetBitmap(dIcons.getIconBitmap("paste"))
		self.AppendItem(item)
		mainForm.Bind(wx.EVT_MENU, self.actionList.getAction("EditPaste")["func"], item)

		self.AppendSeparator()

		item = wx.MenuItem(self, -1, "&Find\tCtrl+F", "Find text in the active window")
		item.SetBitmap(dIcons.getIconBitmap("find"))
		self.AppendItem(item)
		mainForm.Bind(wx.EVT_MENU, self.actionList.getAction("EditFind")["func"], item)

		item = wx.MenuItem(self, -1, "Find Again\tCtrl+G", "Repeat the last search")
		self.AppendItem(item)
		mainForm.Bind(wx.EVT_MENU, self.actionList.getAction("EditFindAgain")["func"], item)
		
		self.AppendSeparator()

		item = wx.MenuItem(self, -1, "Preferences", "Set user preferences")
		item.SetBitmap(dIcons.getIconBitmap("configure"))
		self.AppendItem(item)
		wx.App_SetMacPreferencesMenuItemId(item.GetId())   # Put the prefs item in the App Menu on Mac
		mainForm.Bind(wx.EVT_MENU, self.actionList.getAction("EditPreferences")["func"], item)


class ViewMenu(m.dMenu):
	def __init__(self, mainForm):
		ViewMenu.doDefault(mainForm)



class HelpMenu(m.dMenu):
	def __init__(self, mainForm):
		HelpMenu.doDefault(mainForm)

		item = wx.MenuItem(self, -1, "&About", "About this application")
		item.SetBitmap(dIcons.getIconBitmap("apply"))
		self.AppendItem(item)
		wx.App_SetMacAboutMenuItemId(item.GetId())   # Put the about menu in the App Menu on Mac
		mainForm.Bind(wx.EVT_MENU, self.actionList.getAction("HelpAbout")["func"], item)


class dMainMenuBar(mb.dMenuBar):
	def __init__(self, mainForm):
		super(dMainMenuBar, self).__init__()
		self.Append(FileMenu(mainForm), "&File")
		self.Append(EditMenu(mainForm), "&Edit")
		self.Append(ViewMenu(mainForm), "&View")
		self.Append(HelpMenu(mainForm), "&Help")
		wx.App_SetMacHelpMenuTitleName("&Help")

