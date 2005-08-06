""" dMenuBar.py """
import wx
import dabo
import dPemMixin as pm
import dMenu
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dMenuBar(wx.MenuBar, pm.dPemMixin):
	"""Creates a menu bar, which can contain dMenus.
	"""
	_IsContainer = True


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
		if menu:
			menu.raiseEvent(dEvents.MenuHighlight)
		evt.Skip()


	def appendMenu(self, menu):
		"""Insert a dMenu at the end of the dMenuBar."""
		ret = self.Append(menu, menu.Caption)
		if ret:
			menu.Parent = self
		return ret

	def insertMenu(self, pos, menu):
		"""Insert a dMenu in the dMenuBar at the specified position."""
		ret = self.Insert(pos, menu, menu.Caption)
		if ret:
			menu.Parent = self
		return ret

	def prependMenu(self, menu):
		"""Insert a dMenu at the beginning of the dMenuBar."""
		ret = self.PrependMenu(menu, menu.Caption)
		if ret:
			menu.Parent = self
		return ret


	def append(self, caption):
		"""Appends a dMenu to the end of the dMenuBar."""
		menu = self._getMenu(caption)
		self.appendMenu(menu)
		return menu

	def insert(self, pos, caption):
		"""Inserts a dMenu at the specified position in the dMenuBar."""
		menu = self._getMenu(caption)
		self.insertMenu(pos, menu)
		return menu

	def prepend(self, caption):
		"""Prepends a dMenu to the beginning of the dMenuBar."""
		menu = self._getMenu(caption)
		self.prependMenu(menu)
		return menu

	def _getMenu(self, caption):
		return dMenu.dMenu(self, Caption=caption)
		

	def getMenu(self, caption):
		"""Returns a reference to the menu with the specified caption.
		"""
		return self.GetMenu(self.FindMenu(caption))


	def GetChildren(self):
		# wx doesn't provide GetChildren() for menubars or menus, but dPemMixin
		# calls it in _getChildren(). The Dabo developer wants the submenus of
		# the menubar, but is using the consistent Children property to do it.
		children = [self.GetMenu(index) for index in range(self.GetMenuCount())]
		return children


	def _getForm(self):
		return self.GetFrame()

	def _setForm(self, val):
		if self._constructed():
			if val != self.GetFrame():
				self.Detach()
				self.Attach(val)
		else:
			self._properties["Form"] = val

	Form = property(_getForm, _setForm, None,
		_("Specifies the form that we are a member of."))
