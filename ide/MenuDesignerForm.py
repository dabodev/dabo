#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os

import dabo
dabo.ui.loadUI("wx")

from dabo.dLocalize import _
from dabo.lib.utils import ustr
import dabo.dEvents as dEvents
import dabo.lib.xmltodict as xtd
from ClassDesignerExceptions import PropertyUpdateException
from MenuHyperLink import MenuBarHyperLink
from MenuDesignerPropForm import MenuPropForm



class MenuDesignerForm(dabo.ui.dForm):
	def __init__(self, *args, **kwargs):
		self._selection = None
		self._savedState = {}
		self._menuFile = None
		self._propForm = None
		self._propSheet = None
		self._inPropertyEditing = False
		kwargs["MenuBarFile"] = "MenuDesignerMenu.mnxml"
		self.Controller = self
		super(MenuDesignerForm, self).__init__(*args, **kwargs)
		self.Caption = "Dabo Menu Designer"
		self.mainPanel = dabo.ui.dPanel(self)
		self.Sizer.append1x(self.mainPanel)
		self.mainMenubarLink = None
		sz = self.mainPanel.Sizer = dabo.ui.dSizerV()
		self.previewButton = btn = dabo.ui.dButton(self.mainPanel,
				Caption="Preview", OnHit=self.onPreview)
		sz.append(btn, border=10, halign="center")
		sz.append(dabo.ui.dLine(self.mainPanel), "x", border=10)
		mb_link = self.initMenuBar()
		self.layout()


	def afterInitAll(self):
		self.PropSheet.Controller = self
		self.PropForm.show()
		if not self._menuFile:
			# No menu file was opened; create a base menu
			self.createBaseMenu()
		self.Selection = self.mainMenubarLink
		dabo.ui.callAfter(self.bringToFront)


	def initMenuBar(self, addBaseMenu=False):
		"""Start from scratch with a basic menu bar."""
		try:
			self.mainMenubarLink.release()
		except AttributeError:
			pass
		try:
			self.menubarPanel.release()
		except AttributeError:
			pass
		mbp = self.menubarPanel = dabo.ui.dPanel(self.mainPanel, BackColor="lightgrey")
		mbp.Controller = self
		mbp.menus = []
		self.mainPanel.Sizer.append1x(mbp, border=30)
		mbar = self.mainMenubarLink = MenuBarHyperLink(mbp, Caption="MenuBar",
				Controller=self)
		mbsz = mbp.Sizer = dabo.ui.dSizerV()
		mbsz.append(mbar)
		mbp.menuSizer = dabo.ui.dSizerH()
		mbsz.append1x(mbp.menuSizer)
		if addBaseMenu:
			self.createBaseMenu()
		return mbar


	def createBaseMenu(self):
		"""This creates a base menu."""
		menu_dict = self._createBaseMenuDict()
		self.makeMenuBar(menu_dict)
		self._savedState = self._getState()


	def makeMenuBar(self, dct=None):
		lnk = self.mainMenubarLink
		if dct is None:
			lnk.showTopLevel()
		else:
			lnk.createMenuFromDict(dct)
		self.layout()


	def clearMenus(self):
		self.menubarPanel.menus = []


	def getPropDictForObject(self, obj):
		return {}


	def saveMenu(self):
		if not self._menuFile:
			self._menuFile = dabo.ui.getSaveAs(wildcard="mnxml")
			if not self._menuFile:
				# User canceled
				return
			else:
				if not os.path.splitext(self._menuFile)[1] == ".mnxml":
					self._menuFile += ".mnxml"
		propDict = self._getState()
		xml = xtd.dicttoxml(propDict)
		fname = self._menuFile
		# Try opening the file. If it is read-only, it will raise an
		# IOErrorrror that the calling method can catch.
		codecs.open(fname, "wb", encoding="utf-8").write(xml)
		self.saveState()


	def onPreview(self, evt):
		class PreviewWindow(dabo.ui.dForm):
			def initProperties(self):
				self.Caption = "Menu Preview"
				self.ShowMenuBar = False
			def afterInit(self):
				mp = dabo.ui.dPanel(self)
				self.Sizer.append1x(mp)
				sz = mp.Sizer = dabo.ui.dSizer("v")
				sz.appendSpacer(30)
				self.lblResult = dabo.ui.dLabel(mp, Caption="Menu Selection: \n ", FontBold=True,
						ForeColor="darkred", AutoResize=True, Alignment="Center")
				self.lblResult.FontSize += 4
				sz.append(self.lblResult, "x", halign="center", border=10)
				btn = dabo.ui.dButton(mp, Caption="Close Menu Preview",
						OnHit=self.onDeactivate)
				sz.append(btn, halign="center", border=30)
				mp.fitToSizer()
			def onDeactivate(self, evt):
				self.release()
			def notify(self, evt):
				itm = evt.EventObject
				cap = "Menu Selection: %s\n" % itm.Caption
				fncText = itm._bindingText
				if fncText:
					cap = "%sFunction: %s" % (cap, fncText)
				self.lblResult.Caption = cap
				self.layout()

		propDict = self._getState()
		win = PreviewWindow(self, Centered=True)
		mb = dabo.ui.createMenuBar(propDict, win, win.notify)
		win.MenuBar = mb
		win.show()


	def _createBaseMenuDict(self):
		"""This creates the dict that represents a base menu."""
		iconPath = "themes/tango/16x16"
		sep = {"attributes": {},
				"children": [],
				"name": "SeparatorHyperLink"}

		m_new = {"attributes": {
				"Caption": _("&New"),
				"Action": "form.onNew",
				"HelpText": "",
				"HotKey": "Ctrl+N",
				"ItemID": "file_new",
				"Icon": "new"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_open = {"attributes": {
				"Caption": _("&Open"),
				"Action": "form.onOpen",
				"HelpText": "",
				"HotKey": "Ctrl+O",
				"ItemID": "file_open",
				"Icon": "open"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_close = {"attributes": {
				"Caption": _("&Close"),
				"Action": "form.onClose",
				"HelpText": "",
				"HotKey": "Ctrl+W",
				"ItemID": "file_close",
				"Icon": "close"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_save = {"attributes": {
				"Caption": _("&Save"),
				"Action": "form.onSave",
				"HelpText": "",
				"HotKey": "Ctrl+S",
				"ItemID": "file_save",
				"Icon": "save"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_saveas = {"attributes": {
				"Caption": _("Save &As"),
				"Action": "form.onSaveAs",
				"HelpText": "",
				"HotKey": "",
				"ItemID": "file_saveas",
				"Icon": "saveas"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_cmd = {"attributes": {
				"Caption": _("Command Win&dow"),
				"Action": "app.onCmdWin",
				"HelpText": "",
				"HotKey": "Ctrl+D",
				"ItemID": "file_commandwin",
				"Icon": "%s/apps/utilities-terminal.png" % iconPath},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_quit = {"attributes": {
				"Caption": _("&Quit"),
				"Action": "app.onFileExit",
				"HelpText": "",
				"HotKey": "Ctrl+Q",
				"ItemID": "file_quit",
				"Icon": "quit"},
				"children": [],
				"name": "MenuItemHyperLink"}
		file_menu = {"attributes": {
				"Caption": u"File",
				"HelpText": "",
				"MRU": True},
				"children": [m_new, m_open, m_close, m_save, m_saveas, sep, m_cmd, sep, m_quit],
				"name": "MenuHyperLink"}

		m_undo = {"attributes": {
				"Caption": _("&Undo"),
				"Action": "app.onEditUndo",
				"HelpText": "",
				"HotKey": "Ctrl+Z",
				"ItemID": "edit_",
				"Icon": "undo"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_redo = {"attributes": {
				"Caption": _("&Redo"),
				"Action": "app.onEditRedo",
				"HelpText": "",
				"HotKey": "Ctrl+Shift+Z",
				"ItemID": "edit_undo",
				"Icon": "redo"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_copy = {"attributes": {
				"Caption": _("&Copy"),
				"Action": "app.onEditCopy",
				"HelpText": "",
				"HotKey": "Ctrl+C",
				"ItemID": "edit_copy",
				"Icon": "copy"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_cut = {"attributes": {
				"Caption": _("Cu&t"),
				"Action": "app.onEditCut",
				"HelpText": "",
				"HotKey": "Ctrl+X",
				"ItemID": "edit_cut",
				"Icon": "cut"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_paste = {"attributes": {
				"Caption": _("&Paste"),
				"Action": "app.onEditPaste",
				"HelpText": "",
				"HotKey": "Ctrl+V",
				"ItemID": "edit_paste",
				"Icon": "paste"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_selectall = {"attributes": {
				"Caption": _("Select &All"),
				"Action": "app.onEditSelectAll",
				"HelpText": "",
				"HotKey": "Ctrl+A",
				"ItemID": "edit_selectall",
				"Icon": None},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_find = {"attributes": {
				"Caption": _("&Find / Replace"),
				"Action": "app.onEditFind",
				"HelpText": "",
				"HotKey": "Ctrl+F",
				"ItemID": "edit_find",
				"Icon": "find"},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_findagain = {"attributes": {
				"Caption": _("Find A&gain"),
				"Action": "app.onEditFindAgain",
				"HelpText": "",
				"HotKey": "Ctrl+G",
				"ItemID": "edit_findagain",
				"Icon": None},
				"children": [],
				"name": "MenuItemHyperLink"}
		edit_menu = {"attributes": {
				"Caption": u"Edit",
				"HelpText": "",
				"MRU": False},
				"children": [m_undo, m_redo, sep, m_cut, m_copy, m_paste, sep, m_selectall,
					sep, m_find, m_findagain],
				"name": "MenuHyperLink"}

		m_zoomin = {"attributes": {
				"Caption": _("&Increase Font Size"),
				"Action": "app.fontZoomIn",
				"HelpText": "",
				"HotKey": "Ctrl++",
				"ItemID": "view_zoomin",
				"Icon": None},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_zoomout = {"attributes": {
				"Caption": _("&Decrease Font Size"),
				"Action": "app.fontZoomOut",
				"HelpText": "",
				"HotKey": "Ctrl+r-+",
				"ItemID": "view_zoomout",
				"Icon": None},
				"children": [],
				"name": "MenuItemHyperLink"}
		m_zoomnormal = {"attributes": {
				"Caption": _("&Normal Font Size"),
				"Action": "app.fontZoomNormal",
				"HelpText": "",
				"HotKey": "Ctrl+/",
				"ItemID": "view_zoomnormal",
				"Icon": None},
				"children": [],
				"name": "MenuItemHyperLink"}
		view_menu = {"attributes": {
				"Caption": u"View",
				"HelpText": "",
				"MRU": False},
				"children": [m_zoomin, m_zoomout, m_zoomnormal],
				"name": "MenuHyperLink"}

		help_menu = {"attributes": {
				"Caption": u"Help",
				"HelpText": "",
				"MRU": False},
				"children": [],
				"name": "MenuHyperLink"}

		return {"attributes": {},
				"name": "MenuBarHyperLink",
				"children": [file_menu, edit_menu, view_menu, help_menu],
				}


	def appendMenu(self, caption, useMRU=False):
		mn = menubarPanel(self, Caption=caption, MRU=useMRU, Visible=True)
		self.Sizer.append(mn)
		self.fit()
		self.Controller.updateLayout()
		return mn


	def insertMenu(self, pos, caption, useMRU=False):
		mn = menubarPanel(self, Caption=caption, MRU=useMRU)
		self.Sizer.insert(pos, mn)
		self.fit()
		self.Controller.updateLayout()
		return mn


	def getObjectHierarchy(self, parent=None, level=0):
		"""Returns a list of 2-tuples representing the structure of
		the objects on this form. The first element is the nesting level,
		and the second is the object. The objects are in the order
		created, irrespective of sizer position.
		"""
		if parent is None:
			parent = self.menubar
		ret = [(level, parent)]
		for kid in parent.Children:
			ret += self.getObjectHierarchy(kid, level+1)
		return ret


	def updateLayout(self):
		try:
			self.PropForm.updateLayout()
		except AttributeError:
			# Prop form not yet created
			pass


	def saveState(self):
		self._savedState = self._getState()


	def _getState(self):
		return self.mainMenubarLink.getDesignerDict()


	def beforeClose(self, evt):
		return not self._isDirty()


	def _isDirty(self):
		ret = False
		curr = self._getState()
		if curr != self._savedState:
			cf = self._menuFile
			if cf:
				fname = os.path.split(cf)[1]
			else:
				fname = _("Untitled")
			saveIt = dabo.ui.areYouSure(_("Do you want to save the changes to '%s'?") % fname, _("Unsaved Changes"))
			if saveIt is None:
				# They canceled
				ret = True
			elif saveIt is True:
				# They want to save
				ret = self.saveMenu()
			# Otherwise, they said 'No'
		return ret


	def onNew(self, evt):
		if not self._isDirty():
			self.initMenuBar(addBaseMenu=True)


	def onOpen(self, evt):
		if self._isDirty():
			return
		pth = dabo.ui.getFile("mnxml")
		if not pth:
			# They canceled
			return
		self.openFile(pth)


	def onClose(self, evt):
		self.raiseEvent(dEvents.Close, evt._uiEvent)


	def onSave(self, evt):
		self.saveMenu()


	def onSaveAs(self, evt):
		print "SaveAs"


	def openFile(self, pth):
		if not os.path.exists(pth):
			dabo.ui.stop("The file '%s' does not exist" % pth)
			return
		self._menuFile = pth
		xml = open(pth).read()
		try:
			dct = xtd.xmltodict(xml)
		except:
			raise IOError(_("This does not appear to be a valid menu file."))
		self.makeMenuBar(dct)
		self.layout()
		self.saveState()


	def updatePropVal(self, prop, val, typ):
		obj = self.Selection
		if obj is None:
			return
		if typ is bool:
			val = bool(val)
		if isinstance(val, basestring):
			strVal = val
		else:
			strVal = unicode(val)
		if typ in (str, unicode) or ((typ is list) and isinstance(val, basestring)):
			# Escape any single quotes, and then enclose
			# the value in single quotes
			strVal = "u'" + self.escapeQt(strVal) + "'"
		try:
			exec("obj.%s = %s" % (prop, strVal) )
		except StandardError, e:
			raise PropertyUpdateException(ustr(e))
		self.PropForm.updatePropGrid()
		# This is necessary to force a redraw when some props change.
		self.select(obj)
		try:
			obj.setWidth()
		except AttributeError:
			pass
		self.layout()


	def onShowPanel(self, menu):
		"""Called when code makes a menu panel visible."""
		self.menubar.hideAllBut(menu)


	def select(self, obj):
		if obj is self._selection:
			return
		self.lockDisplay()
		if self._selection is not None:
			self._selection.Selected = False
		self._selection = obj
		self.PropForm.select(obj)
		obj.Selected = True
		self.ensureVisible(obj)
		dabo.ui.callAfterInterval(100, self._selectAfter)
	def _selectAfter(self):
		self.update()
		self.refresh()
		self.unlockDisplay()


	def startPropEdit(self):
		self._inPropertyEditing = True


	def endPropEdit(self):
		self._inPropertyEditing = False


	def ensureVisible(self, obj):
		"""When selecting a menu item, make sure that its menu is open."""
		if isinstance(obj, (list, tuple)):
			obj = obj[-1]


	def escapeQt(self, s):
		sl = "\\"
		qt = "\'"
		return s.replace(sl, sl+sl).replace(qt, sl+qt)


	def _getPropForm(self):
		noProp = self._propForm is None
		if not noProp:
			# Make sure it's still a live object
			try:
				junk = self._propForm.Visible
			except dabo.ui.deadObjectException:
				noProp = True
		if noProp:
			pf = self._propForm = MenuPropForm(self, Visible=False,
					Controller=self, MenuBarFile=self.MenuBarFile)
			pf.restoreSizeAndPosition()
			self.updateLayout()
			pf.Visible = True
		return self._propForm


	def _getPropSheet(self):
		if self._propSheet is None:
			self._propSheet = self.PropForm.PropSheet
		return self._propSheet


	def _getSelection(self):
		return self._selection

	def _setSelection(self, val):
		self.select(val)


	PropForm = property(_getPropForm, None, None,
			_("""Reference to the form that contains the PropSheet
			object (MenuPropForm)"""))

	PropSheet = property(_getPropSheet, None, None,
			_("Reference to the Property Sheet (PropSheet)") )

	Selection = property(_getSelection, _setSelection, None,
			_("Currently selected item  (CaptionPanel)"))

