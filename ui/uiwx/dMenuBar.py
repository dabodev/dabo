""" dMenuBar.py """
import wx
import dabo
import dPemMixin as pm
from dabo.dLocalize import _

class dMenuBar(wx.MenuBar, pm.dPemMixin):
	"""Creates a menu bar, which can contain dMenus.
	"""
	_IsContainer = False


	def __init__(self, properties=None, *args, **kwargs):
		self._baseClass = dMenuBar
		preClass = wx.MenuBar
		pm.dPemMixin.__init__(self, preClass, None, properties, *args, **kwargs)


	def appendMenu(self, menu):
		"""Insert a dMenu at the end of the dMenuBar."""
		self.Append(menu, menu.Caption)
		menu.Parent = self

	def insertMenu(self, pos, menu):
		"""Insert a dMenu in the dMenuBar at the specified position."""
		self.Insert(pos, menu, menu.Caption)
		menu.Parent = self

	def prependMenu(self, menu):
		"""Insert a dMenu at the beginning of the dMenuBar."""
		self.PrependMenu(menu, menu.Caption)
		menu.Parent = self


	def append(self, caption):
		"""Appends a dMenu to the end of the dMenuBar."""
		menu = _getMenu(caption)
		self.appendMenu(menu)
		return menu

	def insert(self, pos, caption):
		"""Inserts a dMenu at the specified position in the dMenuBar."""
		menu = _getMenu(caption)
		self.insertMenu(pos, menu)
		return menu

	def prepend(self, caption):
		"""Prepends a dMenu to the beginning of the dMenuBar."""
		menu = _getMenu(caption)
		self.prependMenu(menu)
		return menu

	def _getMenu(self, caption):
		return dMenu.dMenu(self, Caption=caption)
		

	def getMenu(self, caption):
		"""Returns a reference to the menu with the specified caption.
		"""
		return self.GetMenu(self.FindMenu(caption))


	def _getForm(self):
		try:
			val = self._form
		except AttributeError:
			val = self._form = None
		return val

	def _setForm(self, val):
			self._form = val


	Form = property(_getForm, _setForm, None,
		_("Specifies the form that we are a member of."))
