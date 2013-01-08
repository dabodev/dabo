# -*- coding: utf-8 -*-
import wx
import dabo
import dPemMixin as pm
import dMenu
from dabo.dLocalize import _
import dabo.dEvents as dEvents


class dMenuBar(pm.dPemMixin, wx.MenuBar):
	"""
	Creates a menu bar, which can contain dMenus.

	You probably don't want to use this directly. Instead, see dBaseMenuBar
	which will give you a dMenuBar with the standard File, Edit, and Help
	menus already set up for you.
	"""
	def __init__(self, properties=None, *args, **kwargs):
		self._baseClass = dMenuBar
		preClass = wx.MenuBar
		pm.dPemMixin.__init__(self, preClass, None, properties, *args, **kwargs)


	def _initEvents(self):
		self.Application.uiApp.Bind(wx.EVT_MENU_OPEN,
				self.__onWxMenuOpen, self.Form)


	def __onWxMenuOpen(self, evt):
		## pkm: EVT_OPEN only applies to the top-level menus: those in the menubar.
		##      It seemed to me best to eliminate dEvents.MenuOpen and just call
		##      dEvents.MenuHighlight instead. EVT_MENU_HIGHLIGHT never gets called
		##      on top-level menus, so the two are mutually exclusive and kind of
		##      mean the same thing. Let's keep it simple. BTW, I've never seen
		##      a EVT_MENU_CLOSE being called, and EVT_MENU_HIGHLIGHT_ALL appears
		##      to be identical to EVT_MENU_HIGHLIGHT. Therefore, as of this writing
		##      we are exposing two menu events: dEvents.Hit and dEvents.Highlight.
		menu = evt.GetMenu()
		if menu and isinstance(menu, dMenu.dMenu):
			menu.raiseEvent(dEvents.MenuHighlight, evt)
		evt.Skip()


	def update(self):
		for menu in self.Children:
			menu._setDynamicEnabled()
		super(dMenuBar, self).update()


	def appendMenu(self, menu):
		"""
		Inserts a dMenu at the end of the dMenuBar, and returns the
		reference to that menu.
		"""
		ok = self.Append(menu, menu.Caption)
		if ok:
			menu.Parent = self
			menu._setId(menu._getID())
		return menu


	def insertMenu(self, pos, menu):
		"""
		Inserts a dMenu in the dMenuBar at the specified position, and
		returns a reference to that menu.
		"""
		pos = min(pos, self.GetMenuCount())
		ok = self.Insert(pos, menu, menu.Caption)
		if ok:
			menu.Parent = self
			menu._setId(menu._getID())
		return menu


	def prependMenu(self, menu):
		"""
		Inserts a dMenu at the beginning of the dMenuBar, and returns
		a reference to that menu.
		"""
		ok = self.PrependMenu(menu, menu.Caption)
		if ok:
			menu.Parent = self
			menu._setId(menu._getID())
		return menu


	def append(self, caption, MenuID=None):
		"""
		Appends a dMenu to the end of the dMenuBar, and returns a reference
		to that menu.

		A generic dMenu will be created with the passed caption. Also see the
		appendMenu() function, which takes a dMenu instance as an argument.
		"""
		menu = self._getGenericMenu(caption, MenuID)
		self.appendMenu(menu)
		return menu


	def insert(self, pos, caption, MenuID=None):
		"""
		Inserts a dMenu at the specified position in the dMenuBar, and returns
		a reference to that menu.

		A generic dMenu will be created with the passed caption. Also see the
		insertMenu() function, which takes a dMenu instance as an argument.
		"""
		menu = self._getGenericMenu(caption, MenuID)
		self.insertMenu(pos, menu)
		return menu


	def prepend(self, caption, MenuID=None):
		"""
		Prepends a dMenu to the beginning of the dMenuBar, and returns
		a reference to that menu.

		A generic dMenu will be created with the passed caption. Also see the
		prependMenu() function, which takes a dMenu instance as an argument.
		"""
		menu = self._getGenericMenu(caption, MenuID)
		self.prependMenu(menu)
		return menu


	def _getGenericMenu(self, caption, MenuID=None):
		"""
		Returns a dMenu instance with the passed caption.

		This is used by the append(), insert(), and prepend() functions.
		"""
		return dMenu.dMenu(self, Caption=caption, MenuID=MenuID)


	def remove(self, indexOrMenu, release=True):
		"""
		Removes the menu at the specified index from the menu bar. You may
		also pass a reference to the menu, or the menu's Caption, and it will
		find the associated index.

		If release is True (the default), the menu is deleted as well. If release
		is False, a reference to the menu object will be returned, and the caller
		is responsible for deleting it.
		"""
		if isinstance(indexOrMenu, dabo.ui.dMenu):
			index = self.getMenuIndex(indexOrMenu.Caption)
		elif isinstance(indexOrMenu, basestring):
			# They passed a caption
			index = self.getMenuIndex(indexOrMenu)
		else:
			# An index was passed.
			index = indexOrMenu
		menu = self.Remove(index)
		if release:
			menu.release()
		return menu


	def getMenu(self, idOrCaption):
		"""
		Returns a reference to the menu with the specified MenuID or Caption.
		The MenuID property is checked first; then the Caption. If no match is found,
		None is returned.
		"""
		id = caption = idOrCaption
		try:
			return [mn for mn in self.Children if mn.MenuID == id][0]
		except IndexError:
			pass

		# Finding the id failed; try the Caption
		caption = caption.replace("&", "")
		idx = self.FindMenu(caption)
		if idx is None or idx < 0:
			return None

		# The menu index was found by caption: return the menu:
		try:
			return self.GetMenu(idx)
		except (dabo.ui.assertionException, ValueError):
			return None


	def getMenuIndex(self, idOrCaption):
		"""
		Returns the index of the menu with the specified ID or caption.
		If the menu isn't found, None is returned.
		"""
		mn = self.getMenu(idOrCaption)
		if mn:
			ret = self.Children.index(mn)
		else:
			ret = None
		return ret


	def GetChildren(self):
		# wx doesn't provide GetChildren() for menubars or menus, but dPemMixin
		# calls it in _getChildren(). The Dabo developer wants the submenus of
		# the menubar, but is using the consistent Children property to do it.
		children = [self.GetMenu(index) for index in range(self.GetMenuCount())]
		return children


	## property definitions begin here.
	def _getCount(self):
		return self.GetMenuCount()


	def _getForm(self):
		return self.GetFrame()

	def _setForm(self, val):
		if self._constructed():
			if val != self.GetFrame():
				self.Detach()
				self.Attach(val)
		else:
			self._properties["Form"] = val


	Count = property(_getCount, None, None,
			_("Returns the number of child menus. Read-only.  (int)"))

	Form = property(_getForm, _setForm, None,
			_("Specifies the form that we are a member of.  (dabo.ui.dForm)"))
