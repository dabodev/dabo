""" dMenuItem.py """
import types
import wx
import dPemMixin as pm
import dIcons
import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dMenuItem(wx.MenuItem, pm.dPemMixin):
	"""Creates an item in a menu.
	"""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dMenuItem
		preClass = wx.MenuItem
		self.Parent = parent
		pm.dPemMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _initEvents(self):
		## wx.MenuItems don't have a Bind() of their own, so this serves to 
		## override the base behavior in dPemMixin._initEvents() which has
		## a bunch of wx Events that don't exist for menu items (IOW, don't
		## call doDefault!).

		if self.Application is not None:
			# Set up a mechanism to catch menu selected events
			# and re-raise Dabo dEvents.Hit events. If Application
			# is None, however, this won't work because of wx limitations.
			self.Application.uiApp.Bind(wx.EVT_MENU, self.__onWxHit, self)
			self.Application.uiApp.Bind(wx.EVT_MENU_HIGHLIGHT, 
					self.__onWxMenuHighlight, self)


	def __onWxMenuHighlight(self, evt):
		self.raiseEvent(dEvents.MenuHighlight)
		evt.Skip()

	def __onWxHit(self, evt):
		self.raiseEvent(dEvents.Hit, evt)


	def _getCaption(self):
		return self.GetText()

	def _setCaption(self, val):
		if self._constructed():
			## Win32 seems to need to clear the caption first, or funkiness
			## can arise.
			self.SetText("")
			self.SetText(val)
		else:
			self._properties["Caption"] = val


	def _getDynamicEnabled(self):
		try:
			val = self._dynamicEnabled
		except AttributeError:
			val = self._dynamicEnabled = None
		return val

	def _setDynamicEnabled(self, val):
		assert isinstance(val, (types.FunctionType, types.MethodType))
		self._dynamicEnabled = val


	def _getEnabled(self):
		return self.IsEnabled()

	def _setEnabled(self, val):
		if self._constructed():
			self.Enable(bool(val))
		else:
			self._properties["Enabled"] = val


	def _getForm(self):
		return self.Parent.Form


	def _getHelpText(self):
		return self.GetHelp()

	def _setHelpText(self, val):
		if self._constructed():
			self.SetHelp(val)
		else:
			self._properties["HelpText"] = val


	def _getIcon(self):
		return self.GetBitmap()

	def _setIcon(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				# Icon name was passed; get the actual bitmap
				val = dabo.ui.strToBmp(val)
			if val is None:
				val = wx.EmptyBitmap(1, 1)
			self.SetBitmap(val)

			# Win32 at least needs the following line, or the caption
			# will look really funky, but Linux can't have this line or
			# the underlined hotkeys will get messed up. I don't know about
			# Mac so I'll leave that alone for now:
			if self.Application.Platform in ("Win",):
				self.Caption = self.Caption
		else:
			self._properties["Icon"] = val


	def _getParent(self):
		try:
			ret = self._parent
		except AttributeError:
			ret = self._parent = None
		return ret

	def _setParent(self, val):
		self._parent = val
		


	Caption = property(_getCaption, _setCaption, None,
			_("Specifies the text of the menu item."))

	DynamicEnabled = property(_getDynamicEnabled, _setDynamicEnabled, None,
			_("""Specifies a function to run to determine whether the item is enabled.

			The function will run when the parent menu is activated, and will set the
			menu item's Enabled property to the return value of the function.
			"""))

	Enabled = property(_getEnabled, _setEnabled, None,
			_("Specifies whether the menu item can be interacted with."))

	Icon = property(_getIcon, _setIcon, None,
			_("Specifies the icon for the menu item."))

	Form = property(_getForm, None, None,
			_("Specifies the containing form."))

	HelpText = property(_getHelpText, _setHelpText, None,
			_("Specifies the help text associated with this menu. (str)"))

	Parent = property(_getParent, _setParent, None, 
			_("Specifies the parent menu."))


class dCheckMenuItem(dMenuItem):
	"""Creates a checkbox-like item in a menu.
	"""
	pass


class dRadioMenuItem(dMenuItem):
	"""Creates a radiobox-like item in a menu.
	"""
	pass
