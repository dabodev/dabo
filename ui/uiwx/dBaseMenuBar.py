""" dBaseMenuBar.py

This module contains the class definitions and logic to build
a basic menu for all platforms. There are special needs for
complying with Apple's Human Interface Guidelines, for instance.

Typical usage would be to subclass this class, and then use the 
append() methods of the menubar and menus to add the specific 
menu items that your app needs.
"""
import wx, os
from dMenu import dMenu
from dMenuBar import dMenuBar
import dIcons
import dabo


class FileMenu(dMenu):
	def __init__(self):
		super(FileMenu, self).__init__()
		app = dabo.dAppRef

		self.append("Command Window\tCtrl+D", app, func=app.onCmdWin, 
				help="Open up a command window for debugging" )
		
		prmpt = "E&xit\tAlt+F4"
		if wx.Platform == '__WXMAC__':
			prmpt = "&Quit\tCtrl+Q"
		self.append(prmpt, app, func=app.onFileExit, bmp="close",
				help="Exit the application" )


class EditMenu(dMenu):
	def __init__(self):
		super(EditMenu, self).__init__()
		app = dabo.dAppRef

		self.append("Undo\tCtrl+Z", app, func=app.onEditUndo, bmp="undo",
				help="Undo last action" )

		self.append("Redo\tCtrl+R", app, func=app.onEditRedo, bmp="redo",
				help="" )

		self.appendSeparator()

		self.append("Cut\tCtrl+X", app, func=app.onEditCut, bmp="cut",
				help="Cut selected text" )

		self.append("&Copy\tCtrl+C", app, func=app.onEditCopy, bmp="copy",
				help="Copy selected text" )

		self.append("&Paste\tCtrl+V", app, func=app.onEditPaste, bmp="paste",
				help="Paste text from clipboard" )

		self.appendSeparator()

		self.append("&Find\tCtrl+F", app, func=app.onEditFind, bmp="find",
				help="Find text in the active window" )

		self.append("Find Again\tCtrl+G", app, func=app.onEditFindAgain, bmp="",
				help="Repeat the last search" )

		self.appendSeparator()

		itm = self.append("Preferences", app, func=app.onEditPreferences, bmp="configure",
				help="Set user preferences" )
		# Put the prefs item in the App Menu on Mac
		wx.App_SetMacPreferencesMenuItemId(itm.GetId())



class ViewMenu(dMenu):
	def __init__(self):
		super(ViewMenu, self).__init__()


class HelpMenu(dMenu):
	def __init__(self):
		super(HelpMenu, self).__init__()
		app = dabo.dAppRef

		itm = self.append("&About", app, func=app.onHelpAbout, bmp="apply",
				help="About this application" )
		# Put the about menu in the App Menu on Mac
		wx.App_SetMacAboutMenuItemId(itm.GetId())


class dBaseMenuBar(dMenuBar):
	def __init__(self, mainForm):
		super(dBaseMenuBar, self).__init__()
		self.Append(FileMenu(), "&File")
		self.Append(EditMenu(), "&Edit")
		self.Append(ViewMenu(), "&View")
		self.Append(HelpMenu(), "&Help")
		wx.App_SetMacHelpMenuTitleName("&Help")

