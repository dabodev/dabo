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
from dabo.dLocalize import _, n_


class FileMenu(dMenu):
	def _afterInit(self):
		super(FileMenu, self)._afterInit()
		app = self.Application
		self.Caption = _("&File")

		self.append(_("Command Window") + "\tCtrl+D", bindfunc=app.onCmdWin, 
				help=_("Open up a command window for debugging") )
		
		prmpt = _("Close Windo&w") + "\tCtrl+W"
		self.append(prmpt, bindfunc=app.onWinClose,
				help=_("Close the current window") )

		self.appendSeparator()

		prmpt = _("E&xit") + "\tAlt+F4"
		if wx.Platform == '__WXMAC__':
			prmpt = _("&Quit") + "\tCtrl+Q"
		self.append(prmpt, bindfunc=app.onFileExit, bmp="close",
				help=_("Exit the application") )


class EditMenu(dMenu):
	def _afterInit(self):
		super(EditMenu, self)._afterInit()
		app = self.Application
		self.Caption = _("&Edit")

		self.append(_("Undo") + "\tCtrl+Z", bindfunc=app.onEditUndo, bmp="undo",
				help=_("Undo last action") )

		self.append(_("Redo") + "\tCtrl+R", bindfunc=app.onEditRedo, bmp="redo",
				help=_("Undo last undo") )

		self.appendSeparator()

		self.append(_("Cut") + "\tCtrl+X", bindfunc=app.onEditCut, bmp="cut",
				help=_("Cut selected text") )

		self.append(_("&Copy") + "\tCtrl+C", bindfunc=app.onEditCopy, bmp="copy",
				help=_("Copy selected text") )

		self.append(_("&Paste") + "\tCtrl+V", bindfunc=app.onEditPaste, bmp="paste",
				help=_("Paste text from clipboard") )

		self.appendSeparator()

		self.append(_("&Find") + "\tCtrl+F", bindfunc=app.onEditFind, bmp="find",
				help=_("Find text in the active window") )

		self.append(_("Find Again") + "\tCtrl+G", bindfunc=app.onEditFindAgain, bmp="",
				help=_("Repeat the last search") )

		self.appendSeparator()

		itm = self.append(_("Preferences"), bindfunc=app.onEditPreferences, bmp="configure",
				help=_("Set user preferences") )
		# Put the prefs item in the App Menu on Mac
		wx.App_SetMacPreferencesMenuItemId(itm.GetId())



class ViewMenu(dMenu):
	def _afterInit(self):
		super(ViewMenu, self)._afterInit()
		app = self.Application
		self.Caption = _("&View")
		
		itm = self.append(_("Show/Hide Sizer Lines")+"\tCtrl+L",	
				bindfunc=app.onShowSizerLines, menutype="check",
				help=_("Cool sizer visualizing feature; check it out!"))

class HelpMenu(dMenu):
	def _afterInit(self):
		super(HelpMenu, self)._afterInit()
		app = self.Application
		self.Caption = _("&Help")

		itm = self.append(_("&About"), bindfunc=app.onHelpAbout, bmp="apply",
				help=_("About this application") )
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
