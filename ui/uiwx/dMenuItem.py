""" dMenuItem.py """
import wx
import dPemMixin as pm
import dIcons
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dMenuItem(wx.MenuItem, pm.dPemMixin):
	"""Creates an item in a menu.
	"""
	_IsContainer = False

	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dMenuItem
		preClass = wx.MenuItem
		self.Parent = parent
		pm.dPemMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	def _initEvents(self):
		## wx.MenuItems don't have a Bind() of their own, so this serves to 
		## override the base behavior in dPemMixin._initEvents() which gs
		## a bunch of wx Events that don't exist for menu items (IOW, don't
		## call doDefault!).

		if self.Application is not None:
			# Set up a mechanism to catch menu selected events
			# and re-raise Dabo dEvents.Hit events. If Application
			# is None, however, this won't work because of wx limitations.
			self.Application.uiApp.Bind(wx.EVT_MENU, self.__onWxHit, self)


	def __onWxHit(self, evt):
		# This raises a dabo event that user code can bind to.
		self.raiseEvent(dEvents.Hit)


	def _getCaption(self):
		return self.GetText()

	def _setCaption(self, val):
		self.SetText(val)


	def _getEnabled(self):
		return self.IsEnabled()

	def _setEnabled(self, val):
		self.Enable(bool(val))


	def _getForm(self):
		return self.Parent.Form


	def _getHelpText(self):
		return self.GetHelp()

	def _setHelpText(self, val):
		self.SetHelp(val)


	def _getParent(self):
		try:
			v = self._parent
		except AttributeError:
			v = self._parent = None
		return v

	def _setParent(self, val):
		self._parent = val
		


	Caption = property(_getCaption, _setCaption, None,
		_("Specifies the text of the menu item."))

	Enabled = property(_getEnabled, _setEnabled, None,
		_("Specifies whether the menu can be interacted with."))

	Form = property(_getForm, None, None,
		_("Specifies the containing form."))

	HelpText = property(_getHelpText, _setHelpText, None,
		_("Specifies the help text associated with this menu. (str)"))

	Parent = property(_getParent, _setParent, None, 
		_("Specifies the parent menu."))


class dCheckMenuItem(dMenuItem):
	"""Creates a checkbox-like item in a menu.
	"""
	_IsContainer = False
	pass


class dRadioMenuItem(dMenuItem):
	"""Creates a radiobox-like item in a menu.
	"""
	_IsContainer = False
	pass
