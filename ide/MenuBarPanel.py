#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from MenuDesignerComponents import MenuSaverMixin
from MenuPanel import MenuPanel
from dabo.lib.utils import dictStringify


class MenuBarPanel(MenuSaverMixin, dabo.ui.dPanel):
	"""This panel represents the menu bar. It contains the
	top-level menus.
	"""
	def afterInit(self):
		# Name for the saved mnxml file
		self._className = "MenuBarPanel"
		# Displayed name
		self._commonName = "Menu Bar"
		sz = self.Sizer = dabo.ui.dSizer("H")
		sz.DefaultBorder = 10
		sz.DefaultBorderRight = True
		self.Height = 24
		self.BackColor = "white"
		# We don't need a real property here, so just create an
		# attribute that looks like the required prop.
		self.DesignerProps = {}


	def appendMenu(self, caption, useMRU=False):
		mn = MenuPanel(self, Caption=caption, MRU=useMRU, Visible=True)
		self.Sizer.append(mn)
#		dabo.ui.callAfterInterval(500, self._setNewMenu, mn)
		self.fit()
		self.Controller.updateLayout()
		return mn


	def insertMenu(self, pos, caption, useMRU=False):
		mn = MenuPanel(self, Caption=caption, MRU=useMRU)
		self.Sizer.insert(pos, mn)
		self.fit()
		self.Controller.updateLayout()
		return mn


	def menuClick(self, menu):
		self.select(menu)


	def select(self, menu):
		self.Controller.Selection = menu
		menu.PanelVisible = True


	def fit(self):
		self.layout(resetMin=True)
		self.Width = reduce(lambda x, y: x+y, [ch.Width for ch in self.Children])


	def processContextMenu(self, obj, evt):
		self._contextObj = obj
		pop = dabo.ui.dMenu()
		pop.append("Append Item", OnHit=self.onAppendItem)
		pop.append("Append Separator", OnHit=self.onAppendSep)
		pop.appendSeparator()
		pop.append("Edit", OnHit=self.onEdit)
		pop.appendSeparator()
		pop.append("Add Menu to the Left", OnHit=self.onAddLeft)
		pop.append("Add Menu to the Right", OnHit=self.onAddRight)
		if obj.getPositionInSizer() != 0:
			pop.append("Move Left", OnHit=self.onMoveLeft)
		if obj.getPositionInSizer() != len(obj.ControllingSizer.Children)-1:
			pop.append("Move Right", OnHit=self.onMoveRight)
		pop.appendSeparator()
		pop.append("Delete", OnHit=self.onDelete)
		self.showContextMenu(pop)


	def onAppendItem(self, evt):
		obj = self._contextObj
		self._contextObj = None
		cap = dabo.ui.getString("Caption for new menu item?")
		if cap:
			itm = obj.append(cap)
			obj.PanelVisible = True
			self.Controller.Selection = itm


	def onAppendSep(self, evt):
		obj = self._contextObj
		self._contextObj = None
		itm = obj.appendSeparator()
		obj.PanelVisible = True
		self.Controller.Selection = itm


	def onEdit(self, evt):
		obj = self._contextObj
		txt = self.capText = dabo.ui.dTextBox(self, Value=obj.Caption,
				Position=obj.Position, Size=obj.Size)
		txt.bindEvent(dEvents.LostFocus, self.onEndEdit)
		txt.bindEvent(dEvents.KeyChar, self.onTextCapChar)
		obj.hide()
		txt.setFocus()


	def onTextCapChar(self, evt):
		if evt.keyCode == 13:
			self.onEndEdit(evt)


	def onEndEdit(self, evt):
		cap = self.capText.Value
		self.capText.release()
		if cap:
			self._contextObj.Caption = cap
		self._contextObj.show()
		self.Controller.Selection = self._contextObj
		self._contextObj = None
		self.Controller.updateLayout()
		self.fit()


	def onAddLeft(self, evt):
		pos = self._contextObj.getPositionInSizer()
		itm = self.addItem(pos)
		self.Controller.Selection = itm


	def onAddRight(self, evt):
		pos = self._contextObj.getPositionInSizer() + 1
		itm = self.addItem(pos)
		self.Controller.Selection = itm


	def addItem(self, pos):
		cap = dabo.ui.getString("Caption for new menu?")
		if cap:
			return self.insertMenu(pos, cap)
		return None


	def onMoveRight(self, evt):
		obj = self._contextObj
		pos = obj.getPositionInSizer()
		sz = obj.ControllingSizer
		sz.remove(obj)
		sz.insert(pos+1, obj)
		sz.layout()
		self.Controller.updateLayout()


	def onMoveLeft(self, evt):
		obj = self._contextObj
		pos = obj.getPositionInSizer()
		sz = obj.ControllingSizer
		sz.remove(obj)
		sz.insert(pos-1, obj)
		sz.layout()
		self.Controller.updateLayout()


	def onDelete(self, evt):
		obj = self._contextObj
		if not obj:
			return
		obj.ControllingSizer.remove(obj)
		obj.release()
		self.fit()
		self.Controller.updateLayout()


	def update(self):
		super(MenuBarPanel, self).update()
		dabo.ui.callAfter(self.fitToSizer)


	def hideAllBut(self, menu=None):
		for mn in self.Menus:
			if not mn is menu and mn.PanelVisible:
				mn.PanelVisible = False


	def hideAll(self):
		"""Hides 'em all"""
		self.hideAllBut()


	def restore(self, dct):
		"""Takes a dictionary created by xmltodict from a saved .mnxml file,
		and re-creates the saved menu.
		"""
		self.clear()
		self.Form.lockDisplay()
		for kid in dct["children"]:
			atts = kid["attributes"]
			mn = self.appendMenu(atts["Caption"], atts["MRU"])
			mitems = kid["children"]
			for mitem in mitems:
				if mitem["name"] == "SeparatorPanel":
					mn.appendSeparator()
				else:
					itm = mn.append("xx")
					itm.Visible = False
					itmAtts = dictStringify(mitem["attributes"])
					for att, val in itmAtts.items():
						setattr(itm, att, val)
		for kid in self.Children:
			kid.Visible = True
		self.layout()
		self.fitToSizer()
		self.Form.unlockDisplay()


	def quickMenu(self):
		"""This creates a base menu."""
		self.Form.lockDisplay()
		fm = self.appendMenu(_("File"), True)
		fm.append("New", key="Ctrl-N", picture="new")
		fm.append("Open", key="Ctrl-O", picture="open")
		fm.append("Close", key="Ctrl-W", picture="close")
		fm.append("Save", key="Ctrl-S", picture="save")
		fm.append("SaveAs", key="Ctrl-Shift-S", picture="saveas")
		fm.appendSeparator()
		fm.append("Command Window", key="Ctrl-D", picture="")

		em = self.appendMenu(_("Edit"), False)
		em.append("Undo", key="Ctrl-Z", picture="undo")
		em.append("Redo", key="Ctrl-R", picture="redo")
		em.appendSeparator()
		em.append("Cut", key="Ctrl-X", picture="cut")
		em.append("Copy", key="Ctrl-C", picture="copy")
		em.append("Paste", key="Ctrl-V", picture="paste")
		em.appendSeparator()
		em.append("Find / Replace", key="Ctrl-F", picture="find")
		em.append("Find Again", key="Ctrl-G", picture="")
		self.appendMenu(_("View"), False)
		self.appendMenu(_("Help"), False)

		for kid in self.Children:
			kid.Visible = True
		self.layout()
		self.fitToSizer()

		self.select(fm)
		self.Form.unlockDisplay()
		self.Form.refresh()


# 		dabo.ui.callAfterInterval(100, self._cleanupQuickMenu, fm)
# 	def _cleanupQuickMenu(self, itm):
# 		self.Form.select(itm)
# 		dabo.ui.callAfterInterval(100, self.Form.refresh)


	# Property definitions
	def _getController(self):
		try:
			return self._controller
		except AttributeError:
			self._controller = self.Form
			return self._controller

	def _setController(self, val):
		if self._constructed():
			self._controller = val
		else:
			self._properties["Controller"] = val


	def _getDisplayedMenu(self):
		vis = [mn for mn in self.Menus
				if mn.PanelVisible]
		if vis:
			return vis[0]
		else:
			return None


	def _getDisplayText(self):
		return self._commonName


	def _getMenus(self):
		return [ch for ch in self.Children
				if isinstance(ch, MenuPanel)]


	Controller = property(_getController, _setController, None,
			_("Object to which this one reports events  (object (varies))"))

	DisplayedMenu = property(_getDisplayedMenu, None, None,
			_("Reference to the menu that is currently 'open' (read-only) (MenuPanel)"))

	DisplayText = property(_getDisplayText, None, None,
			_("Text used in the prop sheet to identify this object (read-only) (str)"))

	Menus = property(_getMenus, None, None,
			_("List of all menus in this menubar  (list of MenuPanels)"))
