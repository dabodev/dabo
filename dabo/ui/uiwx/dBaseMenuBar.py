# -*- coding: utf-8 -*-
"""
This module contains the class definitions and logic to build
a basic menu for all platforms. There are special needs for
complying with Apple's Human Interface Guidelines, for instance.

Typical usage would be to subclass this class, and then use the
append() methods of the menubar and menus to add the specific
menu items that your app needs.
"""
import os
import wx
import dabo
from dMenu import dMenu
from dMenuBar import dMenuBar
import dIcons
from dabo.dLocalize import _, n_

iconPath = "themes/tango/16x16"

class FileMenu(dMenu):

	def __init__(self, *args, **kwargs):
		if "MRU" not in kwargs:
			kwargs["MRU"] = True
		super(FileMenu, self).__init__(*args, **kwargs)


	def _afterInit(self):
		super(FileMenu, self)._afterInit()
		app = self.Application
		self.Caption = _("&File")

		if self.Application.ShowCommandWindowMenu:
			self.Parent.commandWinMenuItem = self.append(_("Command Win&dow"), HotKey="Ctrl+D",
					OnHit=app.onCmdWin, bmp="%s/apps/utilities-terminal.png" % iconPath,
					ItemID="file_commandwin",
					help=_("Open up a command window for debugging"))

			self.Parent.debugMenuItem = self.append(_("De&bug Output Window"), menutype="check",
					bmp="%s/apps/utilities-terminal.png" % iconPath, HotKey="Ctrl+B",
					OnHit=app.onDebugWin, ItemID="file_debugwin",
					help=_("Open up a debug output window"))
			self.Parent.debugMenuItem.Checked = True

			self.Parent.inspectorMenuItem = self.append(_("Object &Inspector"), HotKey="Ctrl+Shift+I",
					OnHit=app.onObjectInspectorWin, bmp="%s/apps/system-search.png" % iconPath,
					ItemID="file_inspectorwin", menutype="check",
					help=_("Open up the object inspector"))

		prmpt = _("Close Windo&w")
		self.Parent.closeWindowMenuItem = self.append(prmpt, HotKey="Ctrl+W", OnHit=app.onWinClose,
				ItemID="file_close",
				help=_("Close the current window"))

		self.appendSeparator()

		prmpt = _("&Quit")
		self.Parent.quitMenuItem = self.append(prmpt, HotKey="Ctrl+Q", id=wx.ID_EXIT, OnHit=app.onFileExit,
				bmp="%s/actions/system-log-out.png" % iconPath,
				ItemID="file_quit",
				help=_("Exit the application"))



class EditMenu(dMenu):
	def _afterInit(self):
		super(EditMenu, self)._afterInit()
		app = self.Application
		self.Caption = _("&Edit")

		self.Parent.undoMenuItem = self.append(_("&Undo"), HotKey="Ctrl+Z", OnHit=app.onEditUndo,
				bmp="%s/actions/edit-undo.png" % iconPath,
				ItemID="edit_undo",
				help=_("Undo last action"))

		self.Parent.redoMenuItem = self.append(_("&Redo"), HotKey="Ctrl+Shift+Z", OnHit=app.onEditRedo,
				bmp="%s/actions/edit-redo.png" % iconPath,
				ItemID="edit_redo",
				help=_("Undo last undo"))

		self.appendSeparator()

		self.Parent.cutMenuItem = self.append(_("Cu&t"), HotKey="Ctrl+X", OnHit=app.onEditCut,
				bmp="%s/actions/edit-cut.png" % iconPath,
				ItemID="edit_cut",
				help=_("Cut selected text"))

		self.Parent.copyMenuItem = self.append(_("&Copy"), HotKey="Ctrl+C", OnHit=app.onEditCopy,
				bmp="%s/actions/edit-copy.png" % iconPath,
				ItemID="edit_copy",
				help=_("Copy selected text"))

		self.Parent.pasteMenuItem = self.append(_("&Paste"), HotKey="Ctrl+V", OnHit=app.onEditPaste,
				bmp="%s/actions/edit-paste.png" % iconPath,
				ItemID="edit_paste",
				help=_("Paste text from clipboard"))

		self.Parent.selectAllMenuItem = self.append(_("Select &All"), HotKey="Ctrl+A", OnHit=app.onEditSelectAll,
				bmp="%s/actions/edit-select-all.png" % iconPath,
				ItemID="edit_selectall",
				help=_("Select all text"))

		self.appendSeparator()

		# By default, the Find and Replace functions use a single dialog. The
		# commented lines below this enable the plain Find dialog call.
		self.Parent.findReplaceMenuItem = self.append(_("&Find / Replace"), HotKey="Ctrl+F", OnHit=app.onEditFind,
				bmp="%s/actions/edit-find-replace.png" % iconPath,
				ItemID="edit_findreplace",
				help=_("Find or Replace text in the active window"))

		self.Parent.findAgainMenuItem = self.append(_("Find A&gain"), HotKey="Ctrl+G", OnHit=app.onEditFindAgain, bmp="",
				ItemID="edit_findagain",
				help=_("Repeat the last search"))

		self.appendSeparator()

		self.Parent.preferencesMenuItem = self.append(_("Pr&eferences"), OnHit=app.onEditPreferences,
				bmp="%s/categories/preferences-system.png" % iconPath,
				ItemID="edit_preferences",
				help=_("Set user preferences"), special="pref" )



class ViewMenu(dMenu):
	def _afterInit(self):
		super(ViewMenu, self)._afterInit()
		app = self.Application
		self.Caption = _("&View")

		self.Parent.increaseFontSizeMenuItem = self.append(_("Increase Font Size"),
		        HotKey="Ctrl++",
		        ItemID="view_zoomin", OnHit=app.fontZoomIn,
		        help=_("Increase the font size"))
		self.Parent.decreaseFontSizeMenuItem = self.append(_("Decrease Font Size"),
		        HotKey="Ctrl+-",
		        ItemID="view_zoomout", OnHit=app.fontZoomOut,
		        help=_("Decrease the font size"))
		self.Parent.normalFontSizeMenuItem = self.append(_("Normal Font Size"),
		        HotKey="Ctrl+/",
		        ItemID="view_zoomnormal", OnHit=app.fontZoomNormal,
		        help=_("Set font size to normal"))

		if app.ShowSizerLinesMenu:
			self.appendSeparator()
			self.Parent.sizerLinesMenuItem = self.append(_("Show/Hide Sizer &Lines"), HotKey="Ctrl+L",
					OnHit=app.onShowSizerLines, menutype="check",
					ItemID="view_showsizerlines",
					help=_("Cool sizer visualizing feature; check it out!"))


class HelpMenu(dMenu):
	def _afterInit(self):
		super(HelpMenu, self)._afterInit()
		app = self.Application
		self.Caption = _("&Help")

		appName = app.getAppInfo("appName")
		caption = _("&About")
		if appName:
			caption += " %s" % appName

		self.Parent.aboutMenuItem = self.append(caption, id=wx.ID_ABOUT,
				OnHit=app.onHelpAbout,
				ItemID="help_about",
				help=_("About this application"))


class dBaseMenuBar(dMenuBar):
	"""
	Creates a basic menu bar with File, Edit, and Help menus.

	The Edit menu has standard Copy, Cut, and Paste menu items, and the Help menu
	has an About menu item. On Mac, the About menu item and Help menu are moved
	to the appropriate place in the application menu.

	Typical usage would be to instantiate dBaseMenuBar, set it to your form's
	menubar (using form.MenuBar = dabo.ui.dBaseMenuBar) and then use the
	append() methods of dMenuBar and dMenu to add the specific dMenu(s) and
	dMenuItem(s) that your application needs.
	"""
	def _afterInit(self):
		self.fileMenu = self.appendMenu(FileMenu(self, MenuID="base_file"))
		self.editMenu = self.appendMenu(EditMenu(self, MenuID="base_edit"))
		self.viewMenu = self.appendMenu(ViewMenu(self, MenuID="base_view"))
		self.helpMenu = self.appendMenu(HelpMenu(self, MenuID="base_help"))
		super(dBaseMenuBar, self)._afterInit()



if __name__ == "__main__":
	from dabo.dApp import dApp
	app = dApp()
	app.setup()
	app.MainForm.MenuBar = dBaseMenuBar()
	app.start()
