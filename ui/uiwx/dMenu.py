""" dMenu.py """
import wx
import dPemMixin as pm
import dMenuItem
import dIcons
from dabo.dLocalize import _
import dabo.dEvents as dEvents


# wx constants for styles
dNormalItem = wx.ITEM_NORMAL
dCheckItem =  wx.ITEM_CHECK
dRadioItem = wx.ITEM_RADIO


class dMenu(wx.Menu, pm.dPemMixin):
	"""Creates a menu, which can contain submenus, menu items, and separators.
	"""
	_IsContainer = False

	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dMenu
		preClass = wx.Menu
		self.Parent = parent
		pm.dPemMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def appendItem(self, item):
		"""Insert a dMenuItem at the bottom of the menu."""
		self.AppendItem(item)
		item.Parent = self

	def insertItem(self, pos, item):
		"""Insert a dMenuItem before the specified position in the menu."""
		self.InsertItem(pos, item)
		item.Parent = self

	def prependItem(self, item):
		"""Insert a dMenuItem at the top of the menu."""
		self.PrependItem(item)
		item.Parent = self


	def appendMenu(self, menu):
		"""Insert a dMenu at the bottom of the menu."""
		self.AppendMenu(-1, menu.Caption, menu, help=menu.HelpText)
		menu.Parent = self

	def insertMenu(self, pos, menu):
		"""Insert a dMenu before the specified position in the menu."""
		self.InsertMenu(-1, pos, menu.Caption, menu, help=menu.HelpText)
		menu.Parent = self

	def prependMenu(self, menu):
		"""Insert a dMenu at the top of the menu."""
		self.PrependMenu(-1, menu.Caption, menu, help=menu.HelpText)
		menu.Parent = self


	def appendSeparator(self):
		"""Insert a separator at the bottom of the menu."""
		self.AppendSeparator()

	def insertSeparator(self, pos):
		"""Insert a separator before the specified position in the menu."""
		self.InsertSeparator(pos)

	def prependSeparator(self):
		"""Insert a separator at the top of the menu."""
		self.PrependSeparator()
	

	def append(self, caption, bindfunc=None, help="", bmp=None, menutype=""):
		"""Append a dMenuItem with the specified properties.

		This is a convenient way to add a dMenuItem to a dMenu, give it a caption,
		help string, bitmap, and also bind it to a function, all in one call.
		"""
		item = self._getItem(caption, bindfunc, help, bmp, menutype)
		self.appendItem(item)
		return item
	
	def insert(self, pos, caption, bindfunc=None, help="", bmp=None, menutype=""):
		"""Insert a dMenuItem at the given position with the specified properties.

		This is a convenient way to add a dMenuItem to a dMenu, give it a caption,
		help string, bitmap, and also bind it to a function, all in one call.
		"""
		item = self._getItem(caption, bindfunc, help, bmp, menutype)
		self.insertItem(item)
		return item

	def prepend(self, caption, bindfunc=None, help="", bmp=None, menutype=""):
		"""Prepend a dMenuItem with the specified properties.

		This is a convenient way to add a dMenuItem to a dMenu, give it a caption,
		help string, bitmap, and also bind it to a function, all in one call.
		"""
		item = self._getItem(caption, bindfunc, help, bmp, menutype)
		self.prependItem(item)
		return item
		
	def _getItem(self, prompt, bindfunc, help, icon, menutype):
		itmtyp = self._getItemType(menutype)
		itm = dMenuItem.dMenuItem(self, Caption=prompt, HelpText=help, Icon=icon, 
		                          kind=itmtyp)
		if bindfunc:
			itm.bindEvent(dEvents.Hit, bindfunc)
		return itm

	def _getItemType(self, typ):
		typ = str(typ).lower()[:3]
		ret = dNormalItem
		if typ in ("che", "chk"):
			ret = dCheckItem
		elif typ == "rad":
			# Currently only implemented under Windows and GTK, 
			# use #if wxHAS_RADIO_MENU_ITEMS to test for 
			# availability of this feature.
			ret = dRadioItem
		return ret

	
	def _isPopupMenu(self):
		## TODO: Make dMenu work as a submenu, a child of dMenuBar, or as a popup.
		return False


	def _getCaption(self):
		try:
			v = self._caption
		except:
			v = self._caption = ""
		return v

	def _setCaption(self, val):
		self._caption = val
		if self._isPopupMenu():
			self.SetTitle(val)

	def _getEnabled(self):
		return self.IsEnabled()

	def _setEnabled(self, val):
		self.Enable(bool(val))


	def _getForm(self):
		return self.Parent.Form

	def _getHelpText(self):
		try:
			v = self._helpText
		except AttributeError:
			v = self._helpText = ""
		return v

	def _setHelpText(self, val):
		self._helpText = val


	def _getParent(self):
		try:
			v = self._parent
		except AttributeError:
			v = self._parent = None
		return v

	def _setParent(self, val):
		self._parent = val

		
	Caption = property(_getCaption, _setCaption, None,
		_("Specifies the text of the menu."))

	Enabled = property(_getEnabled, _setEnabled, None,
		_("Specifies whether the menu can be interacted with."))

	Form = property(_getForm, None, None,
		_("Specifies the form that contains the menu."))

	HelpText = property(_getHelpText, _setHelpText, None,
		_("Specifies the help text associated with this menu. (str)"))

	Parent = property(_getParent, _setParent, None, 
		_("Specifies the parent menu or menubar."))
