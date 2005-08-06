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
	def _afterInit(self):
		super(FileMenu, self)._afterInit()
		app = self.Application
		self.Caption = "&File"

		self.append("Command Window\tCtrl+D", bindfunc=app.onCmdWin, 
				help="Open up a command window for debugging" )
		
		prmpt = "Close Windo&w\tCtrl+W"
		self.append(prmpt, bindfunc=app.onWinClose,
				help="Close the current window" )

		self.appendSeparator()

		prmpt = "E&xit\tAlt+F4"
		if wx.Platform == '__WXMAC__':
			prmpt = "&Quit\tCtrl+Q"
		self.append(prmpt, bindfunc=app.onFileExit, bmp="close",
				help="Exit the application" )


class EditMenu(dMenu):
	def _afterInit(self):
		super(EditMenu, self)._afterInit()
		app = self.Application
		self.Caption = "&Edit"

		self.append("Undo\tCtrl+Z", bindfunc=app.onEditUndo, bmp="undo",
				help="Undo last action" )

		self.append("Redo\tCtrl+R", bindfunc=app.onEditRedo, bmp="redo",
				help="Undo last undo" )

		self.appendSeparator()

		self.append("Cut\tCtrl+X", bindfunc=app.onEditCut, bmp="cut",
				help="Cut selected text" )

		self.append("&Copy\tCtrl+C", bindfunc=app.onEditCopy, bmp="copy",
				help="Copy selected text" )

		self.append("&Paste\tCtrl+V", bindfunc=app.onEditPaste, bmp="paste",
				help="Paste text from clipboard" )

		self.appendSeparator()

		self.append("&Find\tCtrl+F", bindfunc=app.onEditFind, bmp="find",
				help="Find text in the active window" )

		self.append("Find Again\tCtrl+G", bindfunc=app.onEditFindAgain, bmp="",
				help="Repeat the last search" )

		self.appendSeparator()

		itm = self.append("Preferences", bindfunc=app.onEditPreferences, bmp="configure",
				help="Set user preferences" )
		# Put the prefs item in the App Menu on Mac
		wx.App_SetMacPreferencesMenuItemId(itm.GetId())



class ViewMenu(dMenu):
	def _afterInit(self):
		super(ViewMenu, self)._afterInit()
		self.Caption = "&View"

class HelpMenu(dMenu):
	def _afterInit(self):
		super(HelpMenu, self)._afterInit()
		app = self.Application
		self.Caption = "&Help"

		itm = self.append("&About", bindfunc=app.onHelpAbout, bmp="apply",
				help="About this application" )
		# Put the about menu in the App Menu on Mac
		wx.App_SetMacAboutMenuItemId(itm.GetId())
		wx.App_SetMacHelpMenuTitleName(self.Caption)


class dBaseMenuBar(dMenuBar):
	def _afterInit(self):
		super(dBaseMenuBar, self)._afterInit()
		self.appendMenu(FileMenu(self))
		self.appendMenu(EditMenu(self))
		self.appendMenu(ViewMenu(self))
		self.appendMenu(HelpMenu(self))
