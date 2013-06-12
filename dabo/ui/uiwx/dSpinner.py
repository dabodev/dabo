# -*- coding: utf-8 -*-
import sys
import locale
from decimal import Decimal as decimal
import operator
import wx
import dabo

from dabo.ui import makeDynamicProperty
from dabo.ui import makeProxyProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")


import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.lib.utils import ustr


class _dSpinButton(dcm.dDataControlMixin, wx.SpinButton):
	"""Simple wrapper around the base wx.SpinButton."""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = _dSpinButton
		preClass = wx.PreSpinButton
		kwargs["style"] = kwargs.get("style", 0) | wx.SP_ARROW_KEYS
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)
		if sys.platform.startswith("win"):
			# otherwise, the arrows are way too wide (34)
			self.Width = 17

class dSpinner(dabo.ui.dDataPanel, wx.Control):
	"""
	Control for allowing a user to increment a value by discreet steps across a range
	of valid values.
	"""
	def __init__(self, parent, properties=None, attProperties=None, TextBoxClass=None, *args, **kwargs):
		self.__constructed = False
		self._spinWrap = False
		self._min = 0
		self._max = 100
		self._increment = 1
		nm = self._extractKey((properties, attProperties, kwargs), "NameBase", "")
		if not nm:
			nm = self._extractKey((properties, attProperties, kwargs), "Name", "dSpinner")
		super(dSpinner, self).__init__(parent=parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)
		self._baseClass = dSpinner
		# Create the child controls
		if TextBoxClass is None:
			TextBoxClass = dabo.ui.dTextBox
		self._proxy_textbox = TextBoxClass(self, Value=0, Width=32,
				StrictNumericEntry=False, _EventTarget=self)
		self._proxy_spinner = _dSpinButton(parent=self, _EventTarget=self)
		self.__constructed = True
		self.Sizer = dabo.ui.dSizer("h")
		self.Sizer.append1x(self._proxy_textbox)
		self.Sizer.append(self._proxy_spinner, "expand")
		self.layout()

		self.Bind(wx.EVT_WINDOW_DESTROY, self.__onWxDestroy)

		# Because several properties could not be set until after the child
		# objects were created, we need to manually call _setProperties() here.
		self._properties["NameBase"] = nm
		self._setNameAndProperties(self._properties, **kwargs)
		ps = self._proxy_spinner
		pt = self._proxy_textbox
		# Set an essentially infinite range. We'll handle the range ourselves.
		ps.SetRange(-2 ** 30, 2 ** 30)
		# We'll also control wrapping ourselves
		self._proxy_spinner._addWindowStyleFlag(wx.SP_WRAP)
		ps.Bind(wx.EVT_SPIN_UP, self.__onWxSpinUp)
		ps.Bind(wx.EVT_SPIN_DOWN, self.__onWxSpinDown)
		#ps.Bind(wx.EVT_SPIN, self._onWxHit)
		pt.Bind(wx.EVT_TEXT, self._onWxHit)
		pt.Bind(wx.EVT_KEY_DOWN, self._onWxKeyDown)
		ps.Bind(wx.EVT_KEY_DOWN, self._onWxKeyDown)
		#self.bindEvent(dEvents.KeyChar, self._onChar)
		self._rerestoreValue()
		dabo.ui.callAfter(self.layout)

	def __onWxDestroy(self, evt):
		# This doesn't otherwise happen
		self.raiseEvent(dEvents.Destroy)

	def _rerestoreValue(self):
		# Hack because when restoreValue() was originally called in onCreate,
		# the name of the control hadn't been set yet.
		if self.SaveRestoreValue:
			self.restoreValue()
			# Additionally, if the user never changes the Value, _value will be None:
			self._value = self.Value

	def _constructed(self):
		"""Returns True if the ui object has been fully created yet, False otherwise."""
		return self.__constructed


	def _toDec(self, val):
		"""Convenience method for converting various types to decimal."""
		return decimal(ustr(val))


	def _toFloat(self, val):
		"""Convenience method for converting various types to float."""
		return float(ustr(val))


	def _coerceTypes(self, newVal, minn, maxx, margin):
		"""
		Handle the problems when min/max/increment values are
		of one type, and the edited value another.
		"""
		typN = type(newVal)
		# Only problem here is Decimal and float combinations
		if typN == decimal:
			margin = self._toDec(margin)
			if type(maxx) == float:
				maxx = self._toDec(maxx)
			if type(minn) == float:
				minn = self._toDec(minn)
		elif typN == float:
			if type(maxx) == decimal:
				maxx = float(maxx)
			if type(minn) == decimal:
				minn = float(minn)
		return minn, maxx, margin


	def _applyIncrement(self, op):
		"""
		Returns the value obtained by modifying the current value by the increment
		according to the passed operation. It expects to be passed either
		operator.add or operator.sub.
		"""
		curr = self.Value
		inc = self.Increment
		try:
			ret = op(curr, inc)
		except TypeError:
			# Usually Decimal/float problems
			tCurr = type(curr)
			if tCurr == decimal:
				ret = op(curr, self._toDec(inc))
			elif tCurr == float:
				ret = op(curr, self._toFloat(inc))
		return ret


	def _spin(self, direction, spinType=None):
		assert direction in ("up", "down")

		incrementFunc = operator.add
		margin = 0.0001
		if direction == "down":
			incrementFunc = operator.sub
			margin = -0.0001

		ret = True
		newVal = self._applyIncrement(incrementFunc)
		minn, maxx, margin = self._coerceTypes(newVal, self.Min, self.Max, margin)

		valueToSet = None

		if direction == "up":
			diff = newVal - maxx
			if diff < margin:
				valueToSet = newVal
			elif self._spinWrap:
				valueToSet = minn
			else:
				ret = False
			if ret:
				self.raiseEvent(dEvents.SpinUp, spinType=spinType)
				self.raiseEvent(dEvents.Spinner, spinType=spinType)

		else:
			diff = newVal - minn
			if diff > margin:
				valueToSet = newVal
			elif self._spinWrap:
				valueToSet = maxx
			else:
				ret = False
			if ret:
				self.raiseEvent(dEvents.SpinDown, spinType=spinType)
				self.raiseEvent(dEvents.Spinner, spinType=spinType)

		self._checkBounds()

		if ret:
			self._userChanged = True
			self.Value = valueToSet
			self._userChanged = True
			self.flushValue()
		self.raiseEvent(dEvents.Hit, hitType=spinType)
		return ret


	def __onWxSpinUp(self, evt):
		"""Respond to the wx event by raising the Dabo event."""
		self._spin("up", spinType="button")

	def __onWxSpinDown(self, evt):
		"""Respond to the wx event by raising the Dabo event."""
		self._spin("down", spinType="button")


	def _checkBounds(self):
		"""Make sure that the value is within the current Min/Max"""
		if self._proxy_textbox.Value < self.Min:
			self._proxy_textbox.Value = self._proxy_spinner.Value = self.Min
		elif self._proxy_textbox.Value > self.Max:
			self._proxy_textbox.Value = self._proxy_spinner.Value = self.Max


	def _onWxHit(self, evt):
		# Determine what type of event caused Hit to be raised.
		if evt is None:
			typ = "key"
		elif evt.GetEventObject() is self._proxy_textbox:
			typ = "text"
		else:
			typ = "spin"
		super(dSpinner, self)._onWxHit(evt, hitType=typ)


	def _onWxKeyDown(self, evt):
		"""
		Handle the case where the user presses the up/down arrows to
		activate the spinner.
		"""
		keys = dabo.ui.dKeys
		kc = evt.GetKeyCode()
		if kc in (keys.key_Up, keys.key_Numpad_up):
			self._spin("up", spinType="key")
		elif kc in (keys.key_Down, keys.key_Numpad_down):
			self._spin("down", spinType="key")
		else:
			evt.Skip()


	def flushValue(self):
		self._checkBounds()
		super(dSpinner, self).flushValue()


	def _numericStringVal(self, val):
		"""
		If passed a string, attempts to convert it to the appropriate numeric
		type. If such a conversion is not possible, returns None.
		"""
		ret = val
		if isinstance(val, basestring):
			if val.count(locale.localeconv()["decimal_point"]) > 0:
				func = decimal
			else:
				func = int
			try:
				ret = func(val)
			except ValueError:
				ret = None
		return ret


	def fontZoomIn(self, amt=1):
		"""Zoom in on the font, by setting a higher point size."""
		self._proxy_textbox._setRelativeFontZoom(amt)


	def fontZoomOut(self, amt=1):
		"""Zoom out on the font, by setting a lower point size."""
		self._proxy_textbox._setRelativeFontZoom(-amt)


	def fontZoomNormal(self):
		"""Reset the font zoom back to zero."""
		self._proxy_textbox._setAbsoluteFontZoom(0)


	def getBlankValue(self):
		return 0


	# Property get/set definitions begin here
	def _getButtonWidth(self):
		return self._proxy_spinner.Width

	def _setButtonWidth(self, val):
		if self._constructed():
			self._proxy_spinner.Width = val
		else:
			self._properties["ButtonWidth"] = val

	def _getChildren(self):
		# The native wx control will return the items that make up this composite
		# control, which our user doesn't want.
		return []


	def _getIncrement(self):
		return self._increment

	def _setIncrement(self, val):
		if self._constructed():
			self._increment = val
		else:
			self._properties["Increment"] = val


	def _getMax(self):
		return self._max

	def _setMax(self, val):
		if self._constructed():
			self._max = val
			self._checkBounds()
		else:
			self._properties["Max"] = val


	def _getMin(self):
		return self._min

	def _setMin(self, val):
		if self._constructed():
			self._min = val
			self._checkBounds()
		else:
			self._properties["Min"] = val


	def _getSpinnerWrap(self):
		return self._spinWrap

	def _setSpinnerWrap(self, val):
		if self._constructed():
			self._spinWrap = val
		else:
			self._properties["SpinnerWrap"] = val


	def _getValue(self):
		try:
			return self._proxy_textbox.Value
		except AttributeError:
			return None

	def _setValue(self, val):
		if self._constructed():
			self._proxy_textbox._inDataUpdate = self._inDataUpdate
			if isinstance(val, (int, long, float, decimal)):
				self._proxy_textbox.Value = val
			else:
				numVal = self._numericStringVal(val)
				if numVal is None:
					dabo.log.error(_("Spinner values must be numeric. Invalid:'%s'") % val)
				else:
					self._proxy_textbox.Value = val
			self._proxy_textbox._inDataUpdate = False
		else:
			self._properties["Value"] = val



	ButtonWidth = property(_getButtonWidth, _setButtonWidth, None,
			_("""Allows the developer to explicitly specify the width of the up/down buttons."""))

	Children = property(_getChildren, None, None,
			_("""Returns a list of object references to the children of
			this object. Only applies to containers. Children will be None for
			non-containers.  (list or None)"""))

	Increment = property(_getIncrement, _setIncrement, None,
			_("Amount the control's value changes when the spinner buttons are clicked  (int/float)"))

	Max = property(_getMax, _setMax, None,
			_("Maximum value for the control  (int/float)"))

	Min = property(_getMin, _setMin, None,
			_("Minimum value for the control  (int/float)"))

	SpinnerWrap = property(_getSpinnerWrap, _setSpinnerWrap, None,
			_("Specifies whether the spinner value wraps at the high/low value. (bool)"))

	Value = property(_getValue, _setValue, None,
			_("Value of the control  (int/float)"))


	DynamicIncrement = makeDynamicProperty(Increment)
	DynamicMax = makeDynamicProperty(Max)
	DynamicMin = makeDynamicProperty(Min)
	DynamicSpinnerWrap = makeDynamicProperty(SpinnerWrap)


	# Pass-through props. These are simply ways of exposing the text control's props
	# through this control
	_proxyDict = {}
	Alignment = makeProxyProperty(_proxyDict, "Alignment", "_proxy_textbox",)
	BackColor = makeProxyProperty(_proxyDict, "BackColor", ("_proxy_textbox", "self"))
	Enabled = makeProxyProperty(_proxyDict, "Enabled", ("self", "_proxy_spinner", "_proxy_textbox"))
	Font = makeProxyProperty(_proxyDict, "Font", "_proxy_textbox")
	FontInfo = makeProxyProperty(_proxyDict, "FontInfo", "_proxy_textbox")
	FontSize = makeProxyProperty(_proxyDict, "FontSize", "_proxy_textbox")
	FontFace = makeProxyProperty(_proxyDict, "FontFace", "_proxy_textbox")
	FontBold = makeProxyProperty(_proxyDict, "FontBold", "_proxy_textbox")
	FontItalic = makeProxyProperty(_proxyDict, "FontItalic", "_proxy_textbox")
	FontUnderline = makeProxyProperty(_proxyDict, "FontUnderline", "_proxy_textbox")
	ForeColor = makeProxyProperty(_proxyDict, "ForeColor", "_proxy_textbox")
	Height = makeProxyProperty(_proxyDict, "Height", ("self", "_proxy_spinner", "_proxy_textbox"))
	ReadOnly = makeProxyProperty(_proxyDict, "ReadOnly", "_proxy_textbox")
	SelectOnEntry = makeProxyProperty(_proxyDict, "SelectOnEntry", "_proxy_textbox")
	ToolTipText = makeProxyProperty(_proxyDict, "ToolTipText", ("self", "_proxy_spinner", "_proxy_textbox"))
	Visible = makeProxyProperty(_proxyDict, "Visible", ("self", "_proxy_spinner", "_proxy_textbox"))



class _dSpinner_test(dSpinner):
	def initProperties(self):
		self.Max = 55
		self.Min = 0
		self.Value = 0
		self.Increment = 8.75
		self.SpinnerWrap = True
		self.FontSize = 10
		self.Width = 80

	def onHit(self, evt):
		print "HIT!", self.Value, "Hit Type", evt.hitType

	def onValueChanged(self, evt):
		print "Value Changed", self.Value
		print "___"

	def onInteractiveChange(self, evt):
		print "Interactive Change", self.Value

	def onSpinUp(self, evt):
		print "Spin up event."

	def onSpinDown(self, evt):
		print "Spin down event."

	def onSpinner(self, evt):
		print "Spinner event."


if __name__ == "__main__":
	from dabo.dApp import dApp
	class Test(dabo.ui.dForm):
		def OH(self, evt): print "HIT"
		def afterInitAll(self):
			self.spn = _dSpinner_test(self, Value=3, OnHit=self.OH)
			self.spn2 = dSpinner(self, Value=3, Max=10, Min=1, Top=75, Width=60)
	app = dApp(MainFormClass=Test)
	app.start()
