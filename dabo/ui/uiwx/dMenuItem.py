# -*- coding: utf-8 -*-
import types
import wx
import dPemMixin as pm
import dIcons
import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from dabo.ui import makeDynamicProperty
from dabo.lib.utils import ustr


class dMenuItem(pm.dPemMixin, wx.MenuItem):
	"""Creates a menu item, which is usually represented as a string."""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dMenuItem
		preClass = wx.MenuItem
		self.Parent = parent

		## see comments in _setCaption for explanation of below:
		text = kwargs.get("text", "")
		if not text:
			text = "dMenuItem"
		kwargs["text"] = text
		# Main text of the menu item
		self._caption = ""
		# Holds the key combination used to trigger the menu
		self._hotKey = None
		# Holds the unique ID, if any
		self._itemID = None

		pm.dPemMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _initEvents(self):
		## wx.MenuItems don't have a Bind() of their own, so this serves to
		## override the base behavior in dPemMixin._initEvents() which has
		## a bunch of wx Events that don't exist for menu items (IOW, don't
		## call the superclass method!).

		if self.Application is not None:
			# Set up a mechanism to catch menu selected events
			# and re-raise Dabo dEvents.Hit events. If Application
			# is None, however, this won't work because of wx limitations.
			self.Application.uiApp.Bind(wx.EVT_MENU, self.__onWxHit, self)
			self.Application.uiApp.Bind(wx.EVT_MENU_HIGHLIGHT,
					self.__onWxMenuHighlight, self)
		# Handle delayed event bindings
		if self._delayedEventBindings:
			dabo.ui.callAfter(self._bindDelayed)


	def __onWxMenuHighlight(self, evt):
		self.raiseEvent(dEvents.MenuHighlight)
		evt.Skip()

	def __onWxHit(self, evt):
		self.raiseEvent(dEvents.Hit, evt)
		evt.Skip(False)


	def _redefine(self):
		"""Combine the Caption and HotKey into the format needed by wxPython."""
		cap = self.Caption
		hk = self.HotKey
		if not cap:
			return
		if hk:
			cap = "%s\t%s" % (cap, hk)
		curr = self.GetItemLabel()
		## pkm: On Windows at least, setting the Icon needs to happen before setting the caption.
		self.SetBitmap(self.Icon)

		if ustr(cap) != ustr(curr):
			## Win32 seems to need to clear the caption first, or funkiness
			## can arise. And win32 in wx2.8 needs for the caption to never be
			## an empty string, or you'll get an invalid stock id assertion.
			self.SetItemLabel(" ")
			if cap == "":
				cap = " "
			self.SetItemLabel(cap)


	def _getCaption(self):
		return self._caption

	def _setCaption(self, val):
		if self._constructed():
			tabsplit = val.split("\t")
			if len(tabsplit) > 1:
				# They're using the technique of caption + tab + hotkey
				# Override any prior setting of self.HotKey with the new one.
				self._hotKey = tabsplit[1]
			self._caption = tabsplit[0]
			self._redefine()
		else:
			self._properties["Caption"] = val


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


	def _getHotKey(self):
		return self._hotKey

	def _setHotKey(self, val):
		if self._constructed():
			self._hotKey = val
			self._redefine()
		else:
			self._properties["HotKey"] = val


	def _getIcon(self):
		return self.GetBitmap()

	def _setIcon(self, val):
		if self._constructed():
			if val in (None, ""):
				return
			if isinstance(val, basestring):
				# Icon name was passed; get the actual bitmap
				val = dabo.ui.strToBmp(val)
			self.SetBitmap(val)

			# Win32 at least needs the following line, or the caption
			# will look really funky, but Linux can't have this line or
			# the underlined hotkeys will get messed up. I don't know about
			# Mac so I'll leave that alone for now:
			if wx.PlatformInfo[0] == "__WXMSW__":
#			if self.Application.Platform in ("Win",):
				self.Caption = self.Caption
		else:
			self._properties["Icon"] = val


	def _getItemID(self):
		return self._itemID

	def _setItemID(self, val):
		if self._constructed():
			self._itemID = val
		else:
			self._properties["ItemID"] = val


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

	Enabled = property(_getEnabled, _setEnabled, None,
			_("Specifies whether the menu item can be interacted with."))

	Form = property(_getForm, None, None,
			_("Specifies the containing form."))

	HelpText = property(_getHelpText, _setHelpText, None,
			_("Specifies the help text associated with this menu. (str)"))

	HotKey = property(_getHotKey, _setHotKey, None,
			_("Key combination that will trigger the menu  (str)"))

	Icon = property(_getIcon, _setIcon, None,
			_("Specifies the icon for the menu item."))

	ItemID = property(_getItemID, _setItemID, None,
			_("""Identifying value for this menuitem. NOTE: there is no checking for
			duplicate values; it is the responsibility to ensure that ItemID values
			are unique within a menu.  (varies)"""))

	Parent = property(_getParent, _setParent, None,
			_("Specifies the parent menu."))


	DynamicCaption = makeDynamicProperty(Caption)
	DynamicEnabled = makeDynamicProperty(Enabled)
	DynamicIcon = makeDynamicProperty(Icon)
	DynamicHelpText = makeDynamicProperty(HelpText)



class dSeparatorMenuItem(pm.dPemMixin, wx.MenuItem):
	"""Creates a menu separator."""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		self._baseClass = dSeparatorMenuItem
		preClass = wx.MenuItem
		self.Parent = parent
		# Holds the unique ID, if any
		self._itemID = None
		pm.dPemMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	# The following are methods designed to make separators work like other menu items.
	def GetParent(self):
		return self.Parent
	def _dummy(self, *args, **kwargs):
		pass
	Bind = SetLabel = _dummy


	def _getItemID(self):
		return self._itemID

	def _setItemID(self, val):
		if self._constructed():
			self._itemID = val
		else:
			self._properties["ItemID"] = val


	def _getParent(self):
		try:
			ret = self._parent
		except AttributeError:
			ret = self._parent = None
		return ret

	def _setParent(self, val):
		self._parent = val


	ItemID = property(_getItemID, _setItemID, None,
			_("""Identifying value for this menuitem. NOTE: there is no checking for
			duplicate values; it is the responsibility to ensure that ItemID values
			are unique within a menu.  (varies)"""))

	Parent = property(_getParent, _setParent, None,
			_("Specifies the parent menu."))



class _AbstractExtendedMenuItem(dMenuItem):
	"""Creates a checkbox-like item in a menu."""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		# Remove the 'Icon' property, as it interferes with the 'selected' display
		if self.__class__ is _AbstractExtendedMenuItem:
			raise dabo.dException.dException(
				"dAbstractExtendedMenuItem class should not be instantiated directly.")
		# Remove the 'Icon' property, as it interferes with the 'selected' display
		self._extractKey((properties, kwargs), "Icon")
		super(_AbstractExtendedMenuItem, self).__init__(parent=parent,
			properties=properties, *args, **kwargs)


	def _getChecked(self):
		return self.IsChecked()

	def _setChecked(self, val):
		if self._constructed():
			self.Check(val)
		else:
			self._properties["Checked"] = val


	Checked = property(_getChecked, _setChecked, None,
			_("Is this menu item checked?  (bool)"))


class dCheckMenuItem(_AbstractExtendedMenuItem):
	"""Creates a checkbox-like item in a menu."""
	pass


class dRadioMenuItem(_AbstractExtendedMenuItem):
	"""Creates a radiobox-like item in a menu."""
	pass

