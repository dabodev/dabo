# -*- coding: utf-8 -*-
import sys
import wx
import dabo
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dPemMixin as pm
import dIcons
from dabo.dLocalize import _
from dabo.lib.utils import ustr
import dabo.dEvents as dEvents
from dabo.lib.utils import cleanMenuCaption

# wx constants for styles
NormalItemType = wx.ITEM_NORMAL
CheckItemType =  wx.ITEM_CHECK
RadioItemType = wx.ITEM_RADIO
SeparatorItemType = wx.ITEM_SEPARATOR


class dMenu(pm.dPemMixin, wx.Menu):
	"""
	Creates a menu, which can contain submenus, menu items,
	and separators.
	"""
	def __init__(self, parent=None, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dMenu
		preClass = wx.Menu
		self.Parent = parent
		self._useMRU = self._extractKey(attProperties, "MRU", None)
		if self._useMRU is not None:
			self._useMRU = (self._useMRU == "True")
		else:
			self._useMRU = self._extractKey((properties, kwargs), "MRU", False)
		self._mruSeparator = None
		# Identifying attribute that can be used to locate the menu
		# independent of its Caption or index.
		self._menuID = None

		## pkm: When a dMenuItem is added to a dMenu, the wx functions only
		##      add the C++ portion, not the mixed-in dabo dMenuItem object.
		##      To work around this, we maintain an internal dictionary that
		##      maps the id of the wxMenuItem to the dMenuItem object.
		self._daboChildren = {}
		pm.dPemMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def __onMenuOpenMRU(self, evt):
		if self.Application:
			self.Application.onMenuOpenMRU(self)


	def _initEvents(self):
		"""
		See self._setId(), which is where the binding of wxEvents needs to take
		place.
		"""
		self.bindEvent(dEvents.MenuOpen, self.__onMenuHighlight)
		self.bindEvent(dEvents.MenuHighlight, self.__onMenuHighlight)
		if self._useMRU:
			self._setMRUBindings()


	def _setMRUBindings(self):
		"""
		If the menu is not top-level (i.e., directly opened from the MenuBar),
		the MenuOpen event will not be raised, so trigger on the MenuHighlight
		event instead.
		"""
		if isinstance(self.Parent, dabo.ui.dMenuBar):
			self.bindEvent(dEvents.MenuOpen, self.__onMenuOpenMRU)
		else:
			self.bindEvent(dEvents.MenuHighlight, self.__onMenuOpenMRU)


	def _clearMRUBindings(self):
		"""
		See the _setMRUBindings method for an explanation. This uses
		the same logic to unbind MRU events.
		"""
		if isinstance(self.Parent, dabo.ui.dMenuBar):
			self.unbindEvent(dEvents.MenuOpen, self.__onMenuOpenMRU)
		else:
			self.unbindEvent(dEvents.MenuHighlight, self.__onMenuOpenMRU)


	def __onMenuHighlight(self, evt):
		"""
		Note that this code is here in a dabo binding instead of in the wx binding
		because of the way we've worked around wx limitations: dMenu as a top-level
		menu in a menu bar doesn't send wx events.
		"""
		self._setDynamicEnabled()


	def _setDynamicEnabled(self):
		"""For each dMenuItem, set Enabled per the item's DynamicEnabled prop."""
		for item in self.Children:
			# separators haven't been abstracted yet, so there are still pure wx items.
			try:
				de = item.DynamicEnabled
			except AttributeError:
				de = None
			if de is not None:
				if callable(de):
					item.Enabled = de()
			if isinstance(item, dMenu):
				item._setDynamicEnabled()


	def __onWxMenuHighlight(self, evt):
		self.raiseEvent(dEvents.MenuHighlight)
		evt.Skip()


	def _getWxItem(self, wxFunc, dMenuItemInstance, pos=None):
		if pos is not None:
			wxItem = wxFunc(pos, dMenuItemInstance)
		else:
			wxItem = wxFunc(dMenuItemInstance)
		dMenuItemInstance.Parent = self
		self._daboChildren[wxItem.GetId()] = dMenuItemInstance
		self._processNewItem(wxItem, dMenuItemInstance)
		return wxItem


	def _processNewItem(self, itm, daboItem):
		"""After a menu item is created, perform any platform-specific handling."""
		id_ = itm.GetId()
		if id_ == wx.ID_ABOUT:
			# Put the about menu in the App Menu on Mac
			wx.App_SetMacAboutMenuItemId(id_)
			cap = daboItem.Parent.Caption
			wx.App_SetMacHelpMenuTitleName(cap)

		# Process any 'special' menus
		try:
			special = daboItem._special
		except AttributeError:
			return
		if special == "pref":
			# Put the prefs item in the App Menu on Mac
			self.Parent._mac_pref_menu_item_id = id_
			wx.App_SetMacPreferencesMenuItemId(id_)


	def appendItem(self, item):
		"""Insert a dMenuItem at the bottom of the menu."""
		wxItem = self._getWxItem(self.AppendItem, item)
		return item


	def insertItem(self, pos, item):
		"""Insert a dMenuItem before the specified position in the menu."""
		wxItem = self._getWxItem(self.InsertItem, item, pos)
		return item


	def prependItem(self, item):
		"""Insert a dMenuItem at the top of the menu."""
		wxItem = self._getWxItem(self.PrependItem, item)
		return item


	def appendMenu(self, menu):
		"""Insert a dMenu at the bottom of the menu."""
		dummySpacer = None
		if not self.Children:
			dummySpacer = self.append(" ")
		wxMenuItem = self.AppendMenu(-1, menu.Caption, menu, help=menu.HelpText)
#- 		wxMenuItem = self.AppendSubMenu(menu, menu.Caption, help=menu.HelpText)
		menu._setId(wxMenuItem.GetId())
		menu.Parent = self
		self._daboChildren[wxMenuItem.GetId()] = menu
		if dummySpacer:
			self.remove(dummySpacer)
		return menu


	def insertMenu(self, pos, menu):
		"""Insert a dMenu before the specified position in the menu."""
		wxMenuItem = self.InsertMenu(pos, -1, menu.Caption, menu, help=menu.HelpText)
		menu._setId(wxMenuItem.GetId())
		menu.Parent = self
		self._daboChildren[wxMenuItem.GetId()] = menu
		return menu


	def prependMenu(self, menu):
		"""Insert a dMenu at the top of the menu."""
		wxMenuItem = self.PrependMenu(-1, menu.Caption, menu, help=menu.HelpText)
		menu._setId(wxMenuItem.GetId())
		menu.Parent = self
		self._daboChildren[wxMenuItem.GetId()] = menu
		return menu


	def appendSeparator(self):
		"""Insert a separator at the bottom of the menu."""
		return self._createMenuItem(None, caption=None, help=None, bmp=None, picture=None,
				menutype="separator")


	def insertSeparator(self, pos):
		"""Insert a separator before the specified position in the menu."""
		return self.InsertSeparator(pos)


	def prependSeparator(self):
		"""Insert a separator at the top of the menu."""
		return self.PrependSeparator()


	def _createMenuItem(self, pos, caption, help, bmp, picture, menutype, *args, **kwargs):
		"""Handles the menu item creation for append(), insert() and prepend()."""
		if pos is None:
			pos = len(self.Children)
		if picture is None:
			picture = bmp
		def _actualCreation(caption, help, picture, menutype, *args, **kwargs):
			if caption:
				hk = kwargs.get("HotKey", "")
				if hk:
					cap = caption + "\t" + hk
				else:
					cap = caption
				kwargs["text"] = cap
			_item = self._getItem(help, picture, menutype, *args, **kwargs)
			self.insertItem(pos, _item)
			_item.Caption = caption
			return _item
		dummySpacer = None
		if not self.Children:
			dummySpacer = _actualCreation(" ", "", None, "")
			dabo.ui.callAfter(self.remove, dummySpacer)
		item = _actualCreation(caption, help, picture, menutype, *args, **kwargs)
		return item


	def append(self, caption, help="", bmp=None, picture=None,
			menutype="", *args, **kwargs):
		"""
		Append a dMenuItem with the specified properties.

		This is a convenient way to add a dMenuItem to a dMenu, give it a caption,
		help string, bitmap, and also bind it to a function, all in one call.

		Any additional keyword arguments passed will be interpreted as properties
		of the dMenuItem: if valid property names/values, the dMenuItem will take
		them on; if not valid, an exception will be raised.
		"""
		return self._createMenuItem(None, caption=caption, help=help, bmp=bmp, picture=picture,
				menutype=menutype, *args, **kwargs)


	def insert(self, pos, caption, help="", bmp=None, picture=None,
			menutype="", *args, **kwargs):
		"""
		Insert a dMenuItem at the given position with the specified properties.

		This is a convenient way to add a dMenuItem to a dMenu, give it a caption,
		help string, bitmap, and also bind it to a function, all in one call.

		Any additional keyword arguments passed will be interpreted as properties
		of the dMenuItem: if valid property names/values, the dMenuItem will take
		them on; if not valid, an exception will be raised.
		"""
		return self._createMenuItem(pos, caption, help=help, bmp=bmp, picture=picture,
				menutype=menutype, *args, **kwargs)


	def prepend(self, caption, help="", bmp=None, picture=None,
			menutype="", *args, **kwargs):
		"""
		Prepend a dMenuItem with the specified properties.

		This is a convenient way to add a dMenuItem to a dMenu, give it a caption,
		help string, bitmap, and also bind it to a function, all in one call.

		Any additional keyword arguments passed will be interpreted as properties
		of the dMenuItem: if valid property names/values, the dMenuItem will take
		them on; if not valid, an exception will be raised.
		"""
		return self._createMenuItem(0, caption, help=help, bmp=bmp, picture=picture,
				menutype=menutype, *args, **kwargs)


	def _resolveItem(self, capIdxOrItem):
		"""
		Returns the menu item specified by either its index or caption. In the
		case that an actual menu item is passed, simply returns that item.
		"""
		if isinstance(capIdxOrItem, basestring):
			ret = self.getItem(capIdxOrItem)
		elif isinstance(capIdxOrItem, int):
			ret = self.Children[capIdxOrItem]
		else:
			ret = capIdxOrItem
		return ret


	def remove(self, capIdxOrItem, release=True):
		"""
		Removes the specified item from the menu. You may specify the item by
		passing its index, its Caption, or by passing the item itself. If release is
		True (the default), the item is destroyed as well. If release is False, a reference
		to the object will be returned, and the caller is responsible for destroying it.
		"""
		if not self:
			# Menu has already been destroyed.
			return
		item = self._resolveItem(capIdxOrItem)
		id_ = item.GetId()
		try:
			del self._daboChildren[id_]
		except KeyError:
			pass

		if wx.VERSION >= (2,7):
			# Needed to keep dPemMixin mixed-in in wxPython 2.8
			val = wx.Menu.RemoveItem(self, item)
			item.this.own(val.this.own())
			val.this.disown()
		else:
			self.RemoveItem(item)

		if release:
			item.Destroy()
			item = None
		return item


	def clear(self):
		"""Removes all items in this menu."""
		while self.Children:
			self.remove(0)


	def setItemCheck(self, itm, val):
		"""
		Pass a menu item and a boolean value, and the checked
		state of that menu item will be set accordingly.
		"""
		itm.Check(val)


	def setCheck(self, capIdxOrItem, unCheckOthers=True):
		"""
		When using checkmark-type menus, passing either the item
		itself, or the index or caption of the item you want checked to
		this method will check that item. If unCheckOthers is True, non-
		matching items will be unchecked.
		"""
		target = self._resolveItem(capIdxOrItem)
		for itm in self.Children:
			if itm is target:
				try:
					itm.Checked =True
				except AttributeError:
					pass
			else:
				if unCheckOthers:
					try:
						itm.Checked = False
					except AttributeError:
						pass


	def clearChecks(self):
		"""Unchecks any checkmark-type menu items."""
		self.setCheck(None)


	def isItemChecked(self, capIdxOrItem):
		itm = self._resolveItem(capIdxOrItem)
		if itm is not None and itm.IsCheckable():
			ret = itm.Checked
		else:
			ret = None
		return ret


	def _getItem(self, help, icon, menutype, *args, **kwargs):
		itmtyp = self._getItemType(menutype)
		itmid = self._getItemID(menutype)
		if itmid != wx.ID_DEFAULT:
			kwargs["id"] = itmid
		try:
			itmSpecial = kwargs.pop("special")
		except KeyError:
			itmSpecial = None
		cls = {NormalItemType: dabo.ui.dMenuItem,
				CheckItemType: dabo.ui.dCheckMenuItem,
				RadioItemType: dabo.ui.dRadioMenuItem,
				SeparatorItemType: dabo.ui.dSeparatorMenuItem}[itmtyp]
		itm = cls(self, HelpText=help, Icon=icon, kind=itmtyp, *args, **kwargs)
		if itmSpecial:
			itm._special = itmSpecial
		return itm


	def _getItemID(self,typ):
		typ = ustr(typ).lower()
		ret = wx.ID_DEFAULT
		if typ == "exit":
			ret = wx.ID_EXIT
		elif typ == "about":
			ret = wx.ID_ABOUT
		elif typ in ("pref", "prefs"):
			ret = wx.ID_PREFERENCES
		return ret


	def _getItemType(self, typ):
		typ = ustr(typ).lower()[:3]
		ret = NormalItemType
		if typ in ("che", "chk"):
			ret = CheckItemType
		elif typ == "rad":
			# Currently only implemented under Windows and GTK,
			# use #if wxHAS_RADIO_MENU_ITEMS to test for
			# availability of this feature.
			ret = RadioItemType
		elif typ == "sep":
			ret = SeparatorItemType
		return ret


	def _setId(self, id_):
		"""
		wxMenus don't have ids of their own - they only get set when the
		menu gets added as a submenu - and then it becomes a wxMenuItem with a
		special submenu flag. This hook, called from append|insert|prependMenu(),
		allows the menu event bindings to take place.
		"""
		## MenuOpen and MenuClose don't appear to be working on Linux. Need
		## to test on Mac and Win.
		self._wxMenuItemId = id_

		if self.Application is not None:
			# Set up a mechanism to catch menu events and re-raise Dabo events.
			# If Application is None, however, this won't work because of wx
			# limitations.
			self.Application.uiApp.Bind(wx.EVT_MENU_HIGHLIGHT,
					self.__onWxMenuHighlight, id=id_)


	def _itemByCaption(self, cap, returnPos=False):
		"""
		Common method for locating a menu item by its caption, ignoring
		all the 'special' characters for acceleration. If 'returnPos' is
		True, the position of the found item is returned instead of the
		item itself.
		"""
		cap = cleanMenuCaption(cap, "&_")
		for pos in xrange(self.GetMenuItemCount()):
			itm = self.FindItemByPosition(pos)
			itmCap = cleanMenuCaption(itm.GetLabel(), "&_")
			if itmCap == cap:
				if returnPos:
					return pos
				else:
					return self._daboChildren.get(itm.GetId(), None)
		return None


	def getItemIndex(self, captionOrItem):
		"""
		Returns the index of the item with the specified caption; you can
		optionally pass in a reference to the menu item itself. If the item
		isn't found, None is returned.
		"""
		try:
			return self.Children.index(captionOrItem)
		except ValueError:
			# Not a menu item
			return self._itemByCaption(captionOrItem, True)


	def getItem(self, idOrCaption):
		"""
		Returns a reference to the menu item with the specified ItemID or Caption.
		The ItemID property is checked first; then the Caption. If no match is found,
		None is returned.
		"""
		menuitems = (itm for itm in self.Children
				if hasattr(itm, "ItemID"))
		try:
			ret = [mn for mn in menuitems
					if mn.ItemID == idOrCaption][0]
		except IndexError:
			ret = None
			# Try the Caption
			ret = self._itemByCaption(idOrCaption)
		return ret


	def GetChildren(self):
		"""
		wx doesn't provide GetChildren() for menubars or menus, but dPemMixin
		calls it in _getChildren(). The Dabo developer wants the submenus and
		items in this menu, but is using the consistent Children property to
		do it. The Children property will thus return both menu items and separators.
		"""
		children = self.GetMenuItems()
		daboChildren = [self._daboChildren.get(c.GetId(), c) for c in children]
		return daboChildren


	def _getCaption(self):
		try:
			v = self._caption
		except AttributeError:
			v = self._caption = ""
		return v

	def _setCaption(self, val):
		if self._constructed():
			prnt = self.Parent
			if isinstance(prnt, wx.MenuBar):
				pos = prnt.FindMenu(self._caption)
				if pos >= 0:
					prnt.SetLabelTop(pos, val)
			else:
				isPopup = False
				while prnt:
					if isinstance(prnt, wx.MenuBar):
						isPopup = True
						break
					prnt = prnt.Parent
				if isPopup:
					# This is only needed for popups
					self.SetTitle(val)
			self._caption = val
		else:
			self._properties["Caption"] = val


	def _getEnabled(self):
		return self.Parent.IsEnabled(self._wxMenuItemId)

	def _setEnabled(self, val):
		if self._constructed():
			self.Parent.Enable(self._wxMenuItemId, bool(val))
		else:
			self._properties["Enabled"] = val


	def _getForm(self):
		if self.Parent:
			return self.Parent.Form
		return None


	def _getHelpText(self):
		try:
			v = self._helpText
		except AttributeError:
			v = self._helpText = ""
		return v

	def _setHelpText(self, val):
		self._helpText = val


	def _getMenuID(self):
		return self._menuID

	def _setMenuID(self, val):
		if self._constructed():
			self._menuID = val
		else:
			self._properties["MenuID"] = val


	def _getMRU(self):
		return self._useMRU

	def _setMRU(self, val):
		if self._constructed():
			self._useMRU = val
			if val:
				self._setMRUBindings()
			else:
				self._clearMRUBindings()
		else:
			self._properties["MRU"] = val


	def _getParent(self):
		try:
			v = self._parent
		except AttributeError:
			v = self._parent = None
		return v

	def _setParent(self, val):
		self._parent = val


	Caption = property(_getCaption, _setCaption, None,
			_("Specifies the text of the menu.  (str)"))

	Enabled = property(_getEnabled, _setEnabled, None,
			_("Specifies whether the menu can be interacted with. Default=True  (bool)"))

	Form = property(_getForm, None, None,
			_("Specifies the form that contains the menu.  (dForm)"))

	HelpText = property(_getHelpText, _setHelpText, None,
			_("Specifies the help text associated with this menu.  (str)"))

	MenuID = property(_getMenuID, _setMenuID, None,
			_("""Identifying value for this menu. NOTE: there is no checking for
			duplicate values; it is the responsibility to ensure that MenuID values
			are unique.  (varies)"""))

	MRU = property(_getMRU, _setMRU, None,
			_("Determines if this menu uses Most Recently Used behavior. Default=False  (bool)"))

	Parent = property(_getParent, _setParent, None,
			_("Specifies the parent menu or menubar.  (varies)"))


	DynamicCaption = makeDynamicProperty(Caption)
	DynamicEnabled = makeDynamicProperty(Enabled)
	DynamicHelpText = makeDynamicProperty(HelpText)

