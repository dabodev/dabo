#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dabo
dabo.ui.loadUI("wx")
from dabo.dLocalize import _
from dabo.lib.propertyHelperMixin import _DynamicList
from dabo.lib.utils import ustr
import dabo.lib.xmltodict as xtd
from MenuDesignerComponents import MenuSaverMixin


SEPARATOR_CAPTION = "-" * 16



class MenuPanel(dabo.ui.dPanel):
	def __init__(self, *args, **kwargs):
		kwargs["BackColor"] = "lightgrey"
		kwargs["BorderWidth"] = 2
		super(MenuPanel, self).__init__(*args, **kwargs)


class AbstractMenuHyperLink(MenuSaverMixin, dabo.ui.dHyperLink):
	"""Handles all the interactions with the user as they create
	and modify menu designs.
	"""
	def __init__(self, parent, *args, **kwargs):
		kwargs["ShowInBrowser"] = False
		kwargs["HoverUnderline"] = False
		kwargs["LinkUnderline"] = False
		kwargs["VisitedUnderline"] = False
		kwargs["ShowHover"] = False
		kwargs["LinkColor"] = "darkblue"
		kwargs["HoverColor"] = "blue"
		kwargs["VisitedColor"] = "darkblue"
		kwargs["BackColor"] = "lightgrey"
		self._menuParent = None
		self._MRU = False
		self._selected = False
		self._isMenuItem = False
		self._isSeparator = False
		self._isMenuBarLink = False
		self._inUpdate = False
		self._helpText = ""
		# The text string representing the HotKey
		self._hotKeyText = ""
		# Minimum number of spaces between the caption and hot key
		self._minCaptionHotKeySpacing = 4
		# Base width of the text for the menu
		self._textWidth = 40
		# The image associated with a menu item.
		self._icon = ""
		# Function to be called when a menu item is selected. This
		# is a string representation that will be eval'd at runtime
		self._action = ""
		# The optional ItemID
		self._itemID = None
		# The following underlie the HotKey property and its components
		self._hotKey = ""
		self._hotKeyAlt = False
		self._hotKeyChar = ""
		self._hotKeyControl = False
		self._hotKeyShift = False
		self._children = []
		super(AbstractMenuHyperLink, self).__init__(parent, *args, **kwargs)
		self._baseClass = self.__class__
		self.FontSize += 1


	def onHit(self, evt):
		raise NotImplementedError


	def onContextMenu(self, evt):
		raise NotImplementedError


	def getDesignerDict(self):
		ret = {}
		ret["name"] = self.getClass()
		ret["attributes"] = ra = {}
		for prop in self.DesignerProps:
			if prop.startswith("HotKey") and prop != "HotKey":
				# This is one of the derivative props.
				continue
			ra[prop] = getattr(self, prop)
		ret["children"] = [kid.getDesignerDict() for kid in self.Children]
		return ret


	def _updateHotKey(self):
		"""Called when the user changes any component of the hotkey combo."""
		if not self._inUpdate:
			self._inUpdate = True
			currHK = self.HotKey
			ctlTxt = {True: "Ctrl+", False: ""}[self.HotKeyControl]
			shiftTxt = {True: "Shift+", False: ""}[self.HotKeyShift]
			altTxt = {True: "Alt+", False: ""}[self.HotKeyAlt]
			newHK = ctlTxt + altTxt + shiftTxt + self.HotKeyChar
			if newHK != currHK:
				self.HotKey = newHK
				self.refresh()
			self._inUpdate = False


	def _calcCaption(self):
		if self._isSeparator:
			self.Caption = "-" * self._textWidth
		else:
			# This will force the re-evaluation of the HotKey text.
			self.Caption = self.Caption


	def _updateHotKeyProps(self, val=None):
		"""Called when the user changes the hotkey combo to reset the components."""
		if not self._inUpdate:
			self._inUpdate = True
			if val is None:
				val = self.HotKey
			self.HotKeyControl = ("Ctrl+" in val)
			self.HotKeyShift = ("Shift+" in val)
			self.HotKeyAlt = ("Alt+" in val)
			self.HotKeyChar = val.split("+")[-1]
			self._inUpdate = False


	def _getAbbreviatedHotKey(self):
		ctlTxt = {True: "C", False: ""}[self.HotKeyControl]
		shiftTxt = {True: "S", False: ""}[self.HotKeyShift]
		altTxt = {True: "A", False: ""}[self.HotKeyAlt]
		prefix = ctlTxt + altTxt + shiftTxt
		if prefix:
			prefix += "+"
		return prefix + self.HotKeyChar


	def select(self):
		self.Controller.Selection = self
		# Customize behavior here
		self.afterSelect()


	def getClass(self):
		"""Return a string representing the item's class. Can
		be overridden by subclasses.
		"""
		return ustr(self.BaseClass).split("'")[1].split(".")[-1]


	def afterSelect(self):
		pass


	def displayedCaption(self):
		return super(AbstractMenuHyperLink, self)._getCaption()


	## Begin property definitions ##
	def _getAction(self):
		return self._action

	def _setAction(self, val):
		if self._constructed():
			self._action = val
		else:
			self._properties["Action"] = val


	def _getCaption(self):
		cap = super(AbstractMenuHyperLink, self)._getCaption()
		return cap.rstrip(self._hotKeyText).rstrip()


	def _setCaption(self, val):
		txt = val
		if self._hotKeyText:
			if self.MenuParent:
				txtwd = self.MenuParent._textWidth
			else:
				txtwd = self._textWidth
			padWidth = txtwd - len(val) - len(self._hotKeyText)
			padding = " " * padWidth
			txt = "".join((val, padding, self._hotKeyText))
		super(AbstractMenuHyperLink, self)._setCaption(txt)


	def _getChildren(self):
		try:
			_children = self._children
		except AttributeError:
			_children = self._children = []
		return _DynamicList(_children, self, "Children")

	def _setChildren(self, val):
		self._children = val


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


	def _getDesignerProps(self):
		ret = {"Caption": {"type" : unicode, "readonly" : (self._isSeparator or self._isMenuBarLink)},
				"HelpText" : {"type" : unicode, "readonly" : self._isSeparator},
				"ItemID" : {"type" : unicode, "readonly" : False},
				"MRU": {"type" : bool, "readonly" : False}}
		if self._isMenuItem:
			ret.update({
					"HotKey": {"type" : unicode, "readonly" : False,
						"customEditor": "editHotKey"},
					"HotKeyAlt": {"type" : bool, "readonly" : False},
					"HotKeyChar": {"type" : unicode, "readonly" : False},
					"HotKeyControl": {"type" : bool, "readonly" : False},
					"HotKeyShift": {"type" : bool, "readonly" : False},
					"Action": {"type" : unicode, "readonly" : False},
					"Icon": {"type" : unicode, "readonly" : False,
						"customEditor": "editStdPicture"}})
			del ret["MRU"]
		return ret


	def _getHelpText(self):
		return self._helpText

	def _setHelpText(self, val):
		if self._constructed():
			self._helpText = self.ToolTipText = val
		else:
			self._properties["HelpText"] = val


	def _getHotKey(self):
		return self._hotKey

	def _setHotKey(self, val):
		if self._constructed():
			self._hotKey = val
			self._updateHotKeyProps(val)
			self._hotKeyText = self._getAbbreviatedHotKey()
			# Force an update
			self.Caption = self.Caption
		else:
			self._properties["HotKey"] = val


	def _getHotKeyAlt(self):
		return self._hotKeyAlt

	def _setHotKeyAlt(self, val):
		if self._constructed():
			self._hotKeyAlt = val
			self._updateHotKey()
		else:
			self._properties["HotKeyAlt"] = val


	def _getHotKeyChar(self):
		return self._hotKeyChar

	def _setHotKeyChar(self, val):
		if self._constructed():
			self._hotKeyChar = val
			self._updateHotKey()
		else:
			self._properties["HotKeyChar"] = val


	def _getHotKeyControl(self):
		return self._hotKeyControl

	def _setHotKeyControl(self, val):
		if self._constructed():
			self._hotKeyControl = val
			self._updateHotKey()
		else:
			self._properties["HotKeyControl"] = val


	def _getHotKeyShift(self):
		return self._hotKeyShift

	def _setHotKeyShift(self, val):
		if self._constructed():
			self._hotKeyShift = val
			self._updateHotKey()
		else:
			self._properties["HotKeyShift"] = val


	def _getIcon(self):
		return self._icon

	def _setIcon(self, val):
		if self._constructed():
			self._icon = val
		else:
			self._properties["Icon"] = val


	def _getItemID(self):
		return self._itemID

	def _setItemID(self, val):
		if self._constructed():
			self._itemID = val
		else:
			self._properties["ItemID"] = val


	def _getMenuParent(self):
		return self._menuParent

	def _setMenuParent(self, val):
		self._menuParent = val


	def _getMRU(self):
		return self._MRU

	def _setMRU(self, val):
		self._MRU = val


	def _getSelected(self):
		return self._selected

	def _setSelected(self, val):
		if self._constructed():
			self._selected = val
			self.BackColor = {True: "white", False: "lightgrey"}[val]
			self.Parent.refresh()
		else:
			self._properties["Selected"] = val


	Action = property(_getAction, _setAction, None,
			_("""Action (method/handler) to be called when a menu item is
			selected. To specify a method on the associated form, use
			'form.onSomeMethod'; likewise, you can specify an application
			method using 'app.onSomeMethod'.  (str)"""))

	Caption = property(_getCaption, _setCaption, None,
			_("The caption displayed on the hyperlink, minus any hot key.  (str)"))	

	Children = property(_getChildren, _setChildren, None,
			_("""The links representing menus, menuitems, etc., that are logically
			'contained' by this object.  (list)"""))

	Controller = property(_getController, _setController, None,
			_("Object to which this one reports events  (object (varies))"))

	DesignerProps = property(_getDesignerProps, None, None,
			_("Properties exposed in the Menu Designer (read-only) (dict)"))

	HelpText = property(_getHelpText, _setHelpText, None,
			_("Help string displayed when the menu item is selected.  (str)"))

	HotKey = property(_getHotKey, _setHotKey, None,
			_("Displayed version of the hotkey combination  (str)"))

	HotKeyAlt = property(_getHotKeyAlt, _setHotKeyAlt, None,
			_("Is the Alt key part of the hotkey combo?  (bool)"))

	HotKeyChar = property(_getHotKeyChar, _setHotKeyChar, None,
			_("Character part of the hot key for this menu  (str)"))

	HotKeyControl = property(_getHotKeyControl, _setHotKeyControl, None,
			_("Is the Control key part of the hotkey combo?  (bool)"))

	HotKeyShift = property(_getHotKeyShift, _setHotKeyShift, None,
			_("Is the Shift key part of the hotkey combo?  (bool)"))

	Icon = property(_getIcon, _setIcon, None,
			_("Specifies the icon for the menu item.  (str)"))

	ItemID = property(_getItemID, _setItemID, None,
			_("""Identifying value for this menuitem. NOTE: there is no checking for
			duplicate values; it is the responsibility to ensure that ItemID values
			are unique within a menu.  (varies)"""))

	MenuParent = property(_getMenuParent, _setMenuParent, None,
			_("The logical 'parent' for this item (not the panel container it sits in.)"))

	MRU = property(_getMRU, _setMRU, None,
			_("Should this menu be tracked for MRU lists  (bool)"))

	Selected = property(_getSelected, _setSelected, None,
			_("Is this the currently selected item?  (bool)"))



class MenuBarHyperLink(AbstractMenuHyperLink):
	"""Used for the top-level menu bar."""
	def __init__(self, parent, *args, **kwargs):
		super(MenuBarHyperLink, self).__init__(parent, *args, **kwargs)
		self._isMenuBarLink = True


	def onHit(self, evt):
		self.select()


	def afterSelect(self):
		self.Controller.makeMenuBar()


	def onContextMenu(self, evt):
		pop = dabo.ui.dMenu()
		pop.append(_("Create Base Menu"), OnHit=self.onCreateBaseMenu, Help="BASE")
		pop.append(_("Add Menu"), OnHit=self.onAddMenu)
		self.showContextMenu(pop)


	def showTopLevel(self):
		self.showMenu(None)

		
	def createMenuFromDict(self, menu_dict):
		"""Create the menu objects from the supplied dict."""
		cont = self.Controller
		mbp = cont.menubarPanel
		msz = mbp.menuSizer
		msz.clear(destroy=True)
		self.clearMenus()
		for att, val in  menu_dict.get("attributes", {}).items():
			setattr(self, att, val)
		for dct in menu_dict.get("children", []):
			mn = self._createMenuFromDict(dct)
			msz.append(mn, border=10)
			self.Children.append(mn)
			mbp.menus.append(mn)
		mbp.layout()


	def _createMenuFromDict(self, menu_dict):
		atts = menu_dict["attributes"]
		atts["Caption"] = atts.get("Caption", SEPARATOR_CAPTION)
		mn = MenuHyperLink(self.Controller.menubarPanel, attProperties=atts)
		mn.MenuBar = mn.MenuParent = self
		mn.Controller = self.Controller
		mn.addItemsFromDictList(menu_dict.get("children", []))
		return mn


	def addMenu(self, menu, side, caption):
		"""Add a menu to either the right or left of the specified menu."""
		mn = self._createBlankMenu(caption)
		cont = self.Controller
		mbp = cont.menubarPanel
		msz = mbp.menuSizer
		pos = self.Children.index(menu)
		if side.lower().startswith("r"):
			pos = pos + 1
		msz.insert(pos, mn, border=10)
		self.Children.insert(pos, mn)
		mbp.menus.insert(pos, mn)
		self.Parent.layout()
		mn.select()


	def moveMenu(self, menu, direction):
		currPos = self.Children.index(menu)
		newPos = currPos + direction


	def deleteMenu(self, menu):
		self.Children.remove(menu)
		mbp = self.Controller.menubarPanel
		mbp.menus.remove(menu)
		menu.release()
		self.Parent.layout()


	def clearMenus(self):
		for mn in self.Children[::-1]:
			try:
				mn.release()
			except dabo.ui.deadObjectException:
				# Already deleted
				pass
		self.Children = []
		self.Controller.clearMenus()


	def showMenu(self, menu):
		"""Show the specified menu, hiding others."""
		for mn in self.Children:
			isShown = (mn is menu)
			mn.menu_panel.Visible = isShown
			if isShown:
				mn.menu_panel.Left = mn.Left
				mn.menu_panel.Top = mn.Bottom + 5
		self.refresh()


	def _createBlankMenu(self, caption=None):
		if caption is None:
			caption = "BLANK"
		blank = {"attributes": {"Caption": caption,
				"HelpText": "",
				"MRU": False},
				"children": [],
				"name": "MenuHyperLink"}
		return self._createMenuFromDict(blank)


	def onCreateBaseMenu(self, evt):
		menuExists = bool(self.Children)
		if menuExists:
			if not dabo.ui.areYouSure(_("Proceeding will destroy the exising menu. "
					"Do you really want to do that?"), "Menu Exists", defaultNo=True,
					cancelButton=False):
				return
		self.Controller.createBaseMenu()


	def onAddMenu(self, evt):
		cap = dabo.ui.getString(_("Caption?"))
		mn = self._createBlankMenu(cap)
		cont = self.Controller
		mbp = cont.menubarPanel
		msz = mbp.menuSizer
		msz.append(mn, border=10)
		self.Children.append(mn)
		mbp.menus.append(mn)
		mn.select()
		self.Parent.layout()



class MenuHyperLink(AbstractMenuHyperLink):
	"""Used for the menus in the menu bar."""
	def onHit(self, evt):
		self.select()


	def afterSelect(self):
		self.MenuBar.showMenu(self)
		self.Parent.layout()


	def release(self):
		"""Augment this to also release the child menus."""
		for itm in self.Children:
			print "RELEASING", itm.Caption
			itm.release()
		super(MenuHyperLink, self).release()


	def onContextMenu(self, evt):
		pop = dabo.ui.dMenu()
		pos = self.getPositionInSizer()
		isFirst = (pos == 0)
		isLast = (pos == (len(self.MenuBar.Children) - 1))
		pop.append(_("Append MenuItem"), OnHit=self.onAppendMenuItem)
		pop.append(_("Append Separator"), OnHit=self.onAppendSeparator)
		pop.append(_("Add Menu Left"), OnHit=self.onAddMenuLeft)
		pop.append(_("Add Menu Right"), OnHit=self.onAddMenuRight)
		if not isFirst:
			pop.append(_("Move Left"), OnHit=self.onMoveLeft)
		if not isLast:
			pop.append(_("Move Right"), OnHit=self.onMoveRight)
		pop.append(_("Delete"), OnHit=self.onDelete)
		self.showContextMenu(pop)


	def addItemsFromDictList(self, dctlst):
		"""Create the menu item links from the supplied list of menuitem dicts."""
		try:
			self.menu_panel.release()
		except AttributeError:
			pass
		cont = self.Controller
		mp = self.menu_panel = MenuPanel(self.Parent)
		sz = mp.Sizer = dabo.ui.dSizerV(DefaultBorder=5)
		seps = []
		max_cap = 0
		for itm_dct in dctlst:
			atts = itm_dct["attributes"]
			if itm_dct["name"] == "SeparatorHyperLink":
				itm = SeparatorHyperLink(mp)
				seps.append(itm)
			else:
				itm = MenuItemHyperLink(mp, attProperties=atts)
				max_cap = max(max_cap, len(itm.Caption))
			self.Children.append(itm)
			itm.Menu = itm.MenuParent = self
			itm.Controller = cont
			sz.append(itm)
		# Set the sizing for this panel
		self._sizeMenuPanel()


	def _sizeMenuPanel(self):
		if not self.Children:
			return
		maxCapLen = max([len(itm.Caption) for itm in self.Children
				if not itm._isSeparator])
		maxHotKeyLen = max([len(itm.HotKey) for itm in self.Children
				if not itm._isSeparator])
		# The width is the max caption length, plus the minimum
		# caption/hotkey spacing, plus the width of the longest hot key.
		self._textWidth = maxCapLen + maxHotKeyLen + self._minCaptionHotKeySpacing
		for itm in self.Children:
			itm._calcCaption()
		self.menu_panel.layout()
		self._fixMenuPanelSize(self.menu_panel)
		self.menu_panel.Visible = False


	def _createMenuItemFromDict(self, itm_dct, parent):
		atts = itm_dct["attributes"]
		if itm_dct["name"] == "Separator":
			itm = SeparatorHyperLink(parent)
		else:
			itm = MenuItemHyperLink(parent, Caption=atts.get("Caption", SEPARATOR_CAPTION),
					HotKey=atts.get("HotKey", ""), HelpText=atts.get("HelpText", ""))
		itm.Menu = itm.MenuParent = self
		return itm


	def makeMenuLinks(self):
		"""Display the menuitem links associated with this menu."""
		cont = self.Controller
		cont.clearMenus()
		mp = cont.current_menu = MenuPanel(self.Parent)
		sz = mp.Sizer = dabo.ui.dSizerV()
		seps = []
		max_cap = 0
		for itm_dct in self.menu_items:
			itm = self._createMenuItemFromDict(itm_dct, mp)
			if isinstance(itm, SeparatorHyperLink):
				seps.append(itm)
			else:
				max_cap = max(max_cap, len(itm.Caption))
			self.Children.append(itm)
			itm.Menu = self
			itm.Controller = cont
			sz.append(itm)
		# set the separator captions
		for sep in seps:
			sep.Caption = "-" * max_cap
		mp.layout()
		self._fixMenuPanelSize(mp)


	def _fixMenuPanelSize(self, mp):
		# Sucks that I have to do this, but it won't pick up the size otherwise
		mp.Size = mp.GetMinSize()
		mp.Top = self.Bottom + 10
		mp.Left = self.Left
		self.Parent.layout()


	def onDelete(self, evt):
		self.MenuBar.deleteMenu(self)


	def onAppendMenuItem(self, evt):
		cap = dabo.ui.getString(_("Caption?"))
		pos = len(self.Children)
		itm = self._createBlankMenuItem(cap)
		self._appendToMenu(itm)
		itm.select()
		return itm


	def onAppendSeparator(self, evt):
		itm = SeparatorHyperLink(self.menu_panel)
		itm.Menu = self
		itm._calcCaption()
		self._appendToMenu(itm)
		itm.select()
		return itm

	def _appendToMenu(self, itm, pos=None):
		if pos is None:
			pos = len(self.Children)
		mp = self.menu_panel
		mp.Sizer.insert(pos, itm)
		self.Children.insert(pos, itm)
		mp.layout()
		self._fixMenuPanelSize(mp)


	def onAddMenuLeft(self, evt):
		self._addMenu("left")


	def onAddMenuRight(self, evt):
		self._addMenu("right")


	def _addMenu(self, side):
		cap = dabo.ui.getString(_("Caption?"))
		self.MenuBar.addMenu(self, side, cap)


	def onMoveLeft(self, evt):
		self._moveMenu(-1)


	def onMoveRight(self, evt):
		self._moveMenu(1)


	def _moveMenu(self, direction):
		self.MenuBar.moveMenu(self, direction)


	def moveItem(self, obj, amount):
		"""Changes the relative position of an item."""
		curr = obj.getPositionInSizer()
		newpos = curr + amount
		obj.setPositionInSizer(newpos)
		self.Children.remove(obj)
		self.Children.insert(newpos, obj)
		self.menu_panel.layout()


	def _createBlankMenuItem(self, caption=None):
		if caption is None:
			caption = "<blank>"
		dct = {"attributes": {"Action": "",
				"Caption": caption,
				"HelpText": "",
				"HotKey": "",
				"Icon": ""},
				"children": [],
				"name": "MenuItemHyperLink"}
		itm = self._createMenuItemFromDict(dct, self.menu_panel)
		itm.Menu = self
		return itm


	def addMenuItem(self, menuItem, side, caption=None):
		mp = self.menu_panel
		pos = self.Children.index(menuItem)
		if side.lower().startswith("b"):
			pos = pos + 1
		mitm = self._createBlankMenuItem(caption)
		mp.Sizer.insert(pos, mitm)
		self.Children.insert(pos, mitm)
		mp.layout()
		self._fixMenuPanelSize(mp)
		mitm.select()


	def deleteMenuItem(self, itm):
		cont = self.Controller
		mp = self.menu_panel
		msz = mp.Sizer
		pos = self.Children.index(itm)
		self.Children.remove(itm)
		msz.remove(itm, destroy=True)
		mp.layout()



class MenuItemHyperLink(AbstractMenuHyperLink):
	"""Used for the menu items in menus."""
	def __init__(self, *args, **kwargs):
		super(MenuItemHyperLink, self).__init__(*args, **kwargs)
		self._isMenuItem = True


	def onHit(self, evt):
		self.select()


	def onContextMenu(self, evt):
		pop = dabo.ui.dMenu()
		pos = self.getPositionInSizer()
		isFirst = (pos == 0)
		isLast = (pos == (len(self.Parent.Children) - 1))
		pop.append(_("Add Item Above"), OnHit=self.onAddItemAbove)
		pop.append(_("Add Item Below"), OnHit=self.onAddItemBelow)
		if not isFirst:
			pop.append(_("Move Up"), OnHit=self.onMoveUp)
		if not isLast:
			pop.append(_("Move Down"), OnHit=self.onMoveDown)
		pop.append(_("Delete"), OnHit=self.onDelete)
		self.showContextMenu(pop)


	def onMoveUp(self, evt):
		self.Menu.moveItem(self, -1)


	def onMoveDown(self, evt):
		self.Menu.moveItem(self, 1)


	def onDelete(self, evt):
		self.Menu.deleteMenuItem(self)


	def onAddItemAbove(self, evt):
		self._addMenuItem("above")


	def onAddItemBelow(self, evt):
		self._addMenuItem("below")


	def _addMenuItem(self, side):
		cap = dabo.ui.getString(_("Caption?"))
		self.Menu.addMenuItem(self, side, cap)



class SeparatorHyperLink(MenuItemHyperLink):
	"""Used for the menu items in menus."""
	def __init__(self, *args, **kwargs):
		super(MenuItemHyperLink, self).__init__(*args, **kwargs)
		self._isSeparator = True
		self._isMenuItem = False
		self.HoverUnderline = self.LinkUnderline = self.VisitedUnderline = False
		self.refresh()
