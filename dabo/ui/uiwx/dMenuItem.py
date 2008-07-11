# -*- coding: utf-8 -*-
import types
import wx
import dPemMixin as pm
import dIcons
import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from dabo.ui import makeDynamicProperty


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
		if hk:
			cap = "%s\t%s" % (cap, hk)
		curr = self.GetText()
		def toUni(s):
			if isinstance(s, str):
				try:
					enc = self.Application.Encoding
				except AttributeError:	
					enc = dabo.defaultEncoding
				s = unicode(s, enc)
			return s
		if toUni(cap) != toUni(curr):
			## Win32 seems to need to clear the caption first, or funkiness
			## can arise. And win32 in wx2.8 needs for the caption to never be
			## an empty string, or you'll get an invalid stock id assertion.
			self.SetText(" ")
			if cap == "":
				cap = " "
			self.SetText(cap)


	def _getCaption(self):
		return self._caption

	def _setCaption(self, val):
		if self._constructed():
			if val.count("\t"):
				# They're using the technique of caption + tab + hotkey
				raise ValueError, _("Please put HotKey combination in HotKey property.")
			else:
				self._caption = val
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
			if wx.PlatformInfo[0] == "__WXMSW__":
#			if self.Application.Platform in ("Win",):
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

	Enabled = property(_getEnabled, _setEnabled, None,
			_("Specifies whether the menu item can be interacted with."))

	HotKey = property(_getHotKey, _setHotKey, None,
			_("Key combination that will trigger the menu  (str)"))
	
	Icon = property(_getIcon, _setIcon, None,
			_("Specifies the icon for the menu item."))

	Form = property(_getForm, None, None,
			_("Specifies the containing form."))

	HelpText = property(_getHelpText, _setHelpText, None,
			_("Specifies the help text associated with this menu. (str)"))

	Parent = property(_getParent, _setParent, None, 
			_("Specifies the parent menu."))


	DynamicCaption = makeDynamicProperty(Caption)
	DynamicEnabled = makeDynamicProperty(Enabled)
	DynamicIcon = makeDynamicProperty(Icon)
	DynamicHelpText = makeDynamicProperty(HelpText)



class dCheckMenuItem(dMenuItem):
	"""Creates a checkbox-like item in a menu."""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		# Remove the 'Icon' property, as it interferes with the 'selected' display 
		self._extractKey((properties, kwargs), "Icon")
		super(dCheckMenuItem, self).__init__(parent=parent, properties=properties,
				*args, **kwargs)
				

	def _getChecked(self):
		return self.IsChecked()

	def _setChecked(self, val):
		if self._constructed():
			self.Check(val)
		else:
			self._properties["Checked"] = val


	Checked = property(_getChecked, _setChecked, None,
			_("Is this menu item checked?  (bool)"))
	


class dRadioMenuItem(dMenuItem):
	"""Creates a radiobox-like item in a menu."""
	def __init__(self, parent=None, properties=None, *args, **kwargs):
		# Remove the 'Icon' property, as it interferes with the 'selected' display 
		self._extractKey((properties, kwargs), "Icon")
		super(dRadioMenuItem, self).__init__(parent=parent, properties=properties,
				*args, **kwargs)


	def _getChecked(self):
		return self.IsChecked()

	def _setChecked(self, val):
		if self._constructed():
			self.Check(val)
		else:
			self._properties["Checked"] = val


	Checked = property(_getChecked, _setChecked, None,
			_("Is this menu item checked?  (bool)"))
	

