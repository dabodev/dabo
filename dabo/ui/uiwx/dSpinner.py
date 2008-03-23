# -*- coding: utf-8 -*-
import locale
try:
	from decimal import Decimal as decimal
except ImportError:
	 decimal = float
import wx
import dabo

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty
from dabo.ui import makeProxyProperty


class dSpinButton(dcm.dDataControlMixin, wx.SpinButton):
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dSpinButton
		preClass = wx.PreSpinButton
		kwargs["style"] = kwargs.get("style", 0) | wx.SP_ARROW_KEYS
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, attProperties, 
				*args, **kwargs)


class dSpinner(dabo.ui.dDataPanel):
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self.__constructed = False
		self._spinWrap = False
		self._min = 0
		self._max = 100
		self._increment = 1
		val = self._extractKey((properties, attProperties, kwargs), "Value", 0)
		val = self._numericStringVal(val)
		super(dSpinner, self).__init__(parent=parent, properties=properties, 
				attProperties=attProperties, *args, **kwargs)
		self._baseClass = dSpinner
		# Create the child controls
		self._proxy_textbox = dabo.ui.dTextBox(self, Value=val, Width=32, 
				StrictNumericEntry=False, _EventTarget=self)
		self._proxy_spinner = dSpinButton(parent=self, _EventTarget=self)
		self.__constructed = True
		self.Sizer = dabo.ui.dSizer("h")
		self.Sizer.append(self._proxy_textbox, 1, valign="middle")
		self.Sizer.appendSpacer(2)
		self.Sizer.append(self._proxy_spinner, valign="middle")
		self.fitToSizer()
		# Because several properties could not be set until after the child
		# objects were created, we need to manually call _setProperties() here.
		self._setProperties(self._properties)
		
		ps = self._proxy_spinner
		pt = self._proxy_textbox
		ps.Bind(wx.EVT_SPIN_UP, self.__onWxSpinUp)
		ps.Bind(wx.EVT_SPIN_DOWN, self.__onWxSpinDown)
		ps.Bind(wx.EVT_SPIN, self._onWxHit)
		self.bindEvent(dEvents.KeyChar, self._onChar)
		self.bindEvent(dEvents.LostFocus, self._onLostFocus)


	def _constructed(self):
		"""Returns True if the ui object has been fully created yet, False otherwise."""
		return self.__constructed
	

	def __onWxSpinUp(self, evt):
		evt.Veto()
		self._spinUp()
		self.raiseEvent(dEvents.SpinUp, spinType="button")
		self.raiseEvent(dEvents.Spinner, spinType="button")


	def __onWxSpinDown(self, evt):
		evt.Veto()
		self._spinDown()
		self.raiseEvent(dEvents.SpinDown, spinType="button")
		self.raiseEvent(dEvents.Spinner, spinType="button")
	
	
	def _spinUp(self):
		curr = self._proxy_textbox.Value
		new = curr + self.Increment
		if new <= self.Max:
			self._proxy_textbox.Value = new
		elif self._spinWrap:
			xs = new - self.Max
			self._proxy_textbox.Value = self.Min + xs
		self.flushValue()


	def _spinDown(self):
		curr = self._proxy_textbox.Value
		new = curr - self.Increment
		if new >= self.Min:
			self._proxy_textbox.Value = new
		elif self._spinWrap:
			xs = self.Min - new
			self._proxy_textbox.Value = self.Max - xs
		self.flushValue()
		

	def _onWxHit(self, evt):
		# Flush the data on each hit, not just when focus is lost.
		self.flushValue()
		super(dSpinner, self)._onWxHit(evt)


	def _onChar(self, evt):
		keys = dabo.ui.dKeys
		kc = evt.keyCode
		if kc in (keys.key_Up, keys.key_Numpad_up):
			self._spinUp()
			self.raiseEvent(dEvents.SpinUp, spinType="key")
			self.raiseEvent(dEvents.Spinner, spinType="key")
			self._onWxHit(None)
		elif kc in (keys.key_Down, keys.key_Numpad_down):
			self._spinDown()
			self.raiseEvent(dEvents.SpinDown, spinType="key")
			self.raiseEvent(dEvents.Spinner, spinType="key")
			self._onWxHit(None)


	def _onLostFocus(self, evt):
		val = self.Value
		pt = self._proxy_textbox
		if (val > self.Max) or (val < self.Min):
			self.Value = pt._oldVal
		pt._oldVal = self.Value


	def _numericStringVal(self, val):
		"""If passed a string, attempts to convert it to the appropriate numeric
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
			except:
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
			self._proxy_spinner.SetRange(self.Min, val)
		else:
			self._properties["Max"] = val


	def _getMin(self):
		return self._min

	def _setMin(self, val):
		if self._constructed():
			self._min = val
			self._proxy_spinner.SetRange(val, self.Max)
		else:
			self._properties["Min"] = val


	def _getSpinnerWrap(self):
		try:
			return self._proxy_spinner._hasWindowStyleFlag(wx.SP_WRAP)
		except AttributeError:
			return self._spinWrap

	def _setSpinnerWrap(self, val):
		if self._constructed():
			self._spinWrap = val
			self._proxy_spinner._delWindowStyleFlag(wx.SP_WRAP)
			if val:
				self._proxy_spinner._addWindowStyleFlag(wx.SP_WRAP)
		else:
			self._properties["SpinnerWrap"] = val


	def _getValue(self):
		try:
			return self._proxy_textbox.Value
		except AttributeError:
			return None

	def _setValue(self, val):
		if self._constructed():
			if isinstance(val, (int, long, float, decimal)):
				self._proxy_textbox.Value = val
			else:
				numVal = self._numericStringVal(val)
				if numVal is None:
					dabo.errorLog.write(_("Spinner values must be numeric. Invalid:'%s'") % val)
				else:
					self._proxy_textbox.Value = val
		else:
			self._properties["Value"] = val



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
	Alignment = makeProxyProperty(_proxyDict, "Alignment", "_proxy_textbox", )
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
		self.Max = 10
		self.Min = 0
		self.Value = 0
		self.Increment = 1
		self.SpinnerWrap = True
		self.FontSize = 10
		self.Width = 80
		
	def onHit(self, evt):
		print "HIT!", self.Value
	
	def onSpinUp(self, evt):
		print "Spin up event."
	
	def onSpinDown(self, evt):
		print "Spin down event."
	
	def onSpinner(self, evt):
		print "Spinner event."


if __name__ == '__main__':
	class TestForm(dabo.ui.dForm):
		def afterInit(self):
			pnl = dabo.ui.dPanel(self)
			self.Sizer.append1x(pnl)
			sz = pnl.Sizer = dabo.ui.dSizer("v")
			
			spn = self.spinner = _dSpinner_test(pnl)
			sz.append(spn, border=10, halign="center")
			
			lbl = dabo.ui.dLabel(pnl, Caption=_("Spinner Properties"), FontSize=18,
					FontBold=True)
			sz.appendSpacer(10)
			sz.append(lbl, halign="center")
			sz.appendSpacer(4)
			
			gsz = dabo.ui.dGridSizer(MaxCols=2, HGap=4, VGap=6)
			lbl = dabo.ui.dLabel(pnl, Caption="Min")
			txt = dabo.ui.dTextBox(pnl, DataSource=spn, DataField="Min", StrictNumericEntry=False)
			gsz.append(lbl, halign="right")
			gsz.append(txt)
			lbl = dabo.ui.dLabel(pnl, Caption="Max")
			txt = dabo.ui.dTextBox(pnl, DataSource=spn, DataField="Max", StrictNumericEntry=False)
			gsz.append(lbl, halign="right")
			gsz.append(txt)
			lbl = dabo.ui.dLabel(pnl, Caption="Increment")
			txt = dabo.ui.dTextBox(pnl, DataSource=spn, DataField="Increment", StrictNumericEntry=False)
			gsz.append(lbl, halign="right")
			gsz.append(txt)
			lbl = dabo.ui.dLabel(pnl, Caption="SpinnerWrap")
			chk = dabo.ui.dCheckBox(pnl, DataSource=spn, DataField="SpinnerWrap")
			gsz.append(lbl, halign="right")
			gsz.append(chk)
			lbl = dabo.ui.dLabel(pnl, Caption="FontSize")
			txt = dabo.ui.dTextBox(pnl, DataSource=spn, DataField="FontSize")
			gsz.append(lbl, halign="right")
			gsz.append(txt)
			lbl = dabo.ui.dLabel(pnl, Caption="Height")
			txt = dabo.ui.dTextBox(pnl, DataSource=spn, DataField="Height")
			gsz.append(lbl, halign="right")
			gsz.append(txt)
			lbl = dabo.ui.dLabel(pnl, Caption="ForeColor")
			txt = dabo.ui.dTextBox(pnl, ReadOnly=True, DataSource=spn, DataField="ForeColor")
			btn = dabo.ui.dButton(pnl, Caption="...", OnHit=self.onColor, Width=36)
			hsz = dabo.ui.dSizer("h")
			hsz.append(txt, 1)
			hsz.append(btn)
			gsz.append(lbl, halign="right")
			gsz.append(hsz)
			lbl = dabo.ui.dLabel(pnl, Caption="Enabled")
			chk = dabo.ui.dCheckBox(pnl, DataSource=spn, DataField="Enabled")
			gsz.append(lbl, halign="right")
			gsz.append(chk)
			
			sz.append(gsz, halign="center")
			self.update()
			self.layout()

		def onColor(self, evt):
			color = dabo.ui.getColor(self.spinner.ForeColor)
			if color is not None:
				self.spinner.ForeColor = color
				self.update()

	app = dabo.dApp(MainFormClass=TestForm)
	app.start()
