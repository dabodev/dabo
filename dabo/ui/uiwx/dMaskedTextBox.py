# -*- coding: utf-8 -*-
import wx
import wx.lib.masked as masked
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dTextBox import dTextBox
from dabo.ui import makeDynamicProperty
import dTextBoxMixin as tbm



class dMaskedTextBox(tbm.dTextBoxMixin, masked.TextCtrl):
	""" This is a specialized textbox class that supports a Mask property. The
	mask determines what characters are allowed in the textbox, and can also
	include formatting characters that are not part of the control's Value.
	"""
	_formatMap = {"phone-us": "USPHONEFULL",
			"phone-us-ext": "USPHONEFULLEXT",
			"ssn-us": "USSOCIALSEC",
			"zip-us": "USZIP",
			"zipplus4-us": "USZIPPLUS4",
			"date-us": "USDATEMMDDYYYY/",
			"date-us-slash": "USDATEMMDDYYYY/",
			"date-us-dash": "USDATEMMDDYYYY-",
			"date-us-yy": "USDATEMMDDYY/",
			"date-eu": "EUDATEDDMMYYYY.",
			"date-eu-slash": "EUDATEDDMMYYYY/",
			"date-eu-month": "EUDATEDDMMMYYYY.",
			"date-eu-month-slash": "EUDATEDDMMMYYYY/",
			"datetime-us": "USDATETIMEMMDDYYYY/HHMMSS",
			"datetime-us-dash": "USDATETIMEMMDDYYYY-HHMMSS",
			"datetime-us-24": "USDATE24HRTIMEMMDDYYYY/HHMMSS",
			"datetime-us-24-dash": "USDATE24HRTIMEMMDDYYYY-HHMMSS",
			"datetime-us-nosec": "USDATETIMEMMDDYYYY/HHMM",
			"datetime-us-dash-nosec": "USDATETIMEMMDDYYYY-HHMM",
			"datetime-us-24-nosec": "USDATE24HRTIMEMMDDYYYY/HHMM",
			"datetime-us-24-dash-nosec": "USDATE24HRTIMEMMDDYYYY-HHMM",
			"datetime-eu": "EUDATETIMEYYYYMMDD.HHMMSS",
			"datetime-eu-slash": "EUDATETIMEYYYYMMDD/HHMMSS",
			"datetime-eu-nosec": "EUDATETIMEYYYYMMDD.HHMM",
			"datetime-eu-slash-nosec": "EUDATETIMEYYYYMMDD/HHMM",
			"datetime-eu-24": "EUDATE24HRTIMEYYYYMMDD.HHMMSS",
			"datetime-eu-24-slash": "EUDATE24HRTIMEYYYYMMDD/HHMMSS",
			"datetime-eu-24-nosec": "EUDATE24HRTIMEYYYYMMDD.HHMM",
			"datetime-eu-24-slash-nosec": "EUDATE24HRTIMEYYYYMMDD/HHMM",
			"datetime-eu-dmy": "EUDATETIMEDDMMYYYY.HHMMSS",
			"datetime-eu-dmy-slash": "EUDATETIMEDDMMYYYY/HHMMSS",
			"datetime-eu-dmy-nosec": "EUDATETIMEDDMMYYYY.HHMM",
			"datetime-eu-dmy-slash-nosec": "EUDATETIMEDDMMYYYY/HHMM",
			"datetime-eu-dmy-24": "EUDATE24HRTIMEDDMMYYYY.HHMMSS",
			"datetime-eu-dmy-24-slash": "EUDATE24HRTIMEDDMMYYYY/HHMMSS",
			"datetime-eu-dmy-24-nosec": "EUDATE24HRTIMEDDMMYYYY.HHMM",
			"datetime-eu-dmy-24-slash-nosec": "EUDATE24HRTIMEDDMMYYYY/HHMM",
			"time": "TIMEHHMMSS",
			"time-nosec": "TIMEHHMM",
			"time-24": "24HRTIMEHHMMSS",
			"time-24-nosec": "24HRTIMEHHMM",
			"date-expiration": "EXPDATEMMYY",
			"email": "EMAIL",
			"ip": "IPADDR"}


	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):	
		self._baseClass = dMaskedTextBox
		self._mask = self._extractKey((properties, attProperties, kwargs), "Mask", "")
		self._format = self._extractKey((properties, attProperties, kwargs), "Format", "")
		kwargs["mask"] = self._mask
		kwargs["formatcodes"] = "_"
		if self._format:
			code = self._formatMap.get(self._format.lower(), "")
			if code:
				kwargs["autoformat"] = code
				kwargs["mask"] = ""
		#kwargs["useFixedWidthFont"] = bool(self._mask)
		kwargs["useFixedWidthFont"] = False
		
		preClass = wx.lib.masked.TextCtrl
		tbm.dTextBoxMixin.__init__(self, preClass, parent, properties, attProperties, 
				*args, **kwargs)


	def getFormats(cls):
		"""Return a list of available format codes."""
		return cls._formatMap.keys()
	getFormats = classmethod(getFormats)


	# property get/set functions
	def _getFormat(self):
		return self._format

	def _setFormat(self, val):
		if self._constructed():
			try:
				self.SetAutoformat(self._formatMap.get(val))
				self._format = val
			except AttributeError:
				dabo.errorLog.write(_("Invalid Format value: %s") % val)
		else:
			self._properties["Format"] = val


	def _getMask(self):
		return self.GetMask()

	def _setMask(self, val):
		if self._constructed():
			if self.GetAutoformat() and val:
				# Cannot have both a mask and a format
				dabo.errorLog.write(_("Cannot set a Mask when a Format has been set"))
			else:
				self._mask = val
				self.SetMask(val)
		else:
			self._properties["Mask"] = val


	def _getMaskedValue(self):
		return self.GetValue()


	# Property definitions:
	Format = property(_getFormat, _setFormat, None,
			_("""Several pre-defined formats are available. When you set the Format 
			property, any Mask setting is ignored, and the specified Format is 
			used instead. The format codes are NOT case-sensitive.  (str)
			
			Formats are available in several categories:
				Date (US and European)
				DateTime (US and European)
				Time
				Email
				IP Address
				SSN (US)
				Zip Code (US)
				Phone (US)
				"""))
	
	Mask = property(_getMask, _setMask, None,
			_("""Display Mask for the control.  (str)
			
			These are the allowed mask characters and their function:
			===============================================
			Character   Function
			===============================================
				#       Allow numeric only (0-9)
				N       Allow letters and numbers (0-9)
				A       Allow uppercase letters only
				a       Allow lowercase letters only
				C       Allow any letter, upper or lower
				X       Allow string.letters, string.punctuation, string.digits
				&       Allow string.punctuation only (doesn't include all unicode symbols)
				*       Allow any visible character
				|       explicit field boundary (takes no space in the control; allows mix
						of adjacent mask characters to be treated as separate fields,
						eg: '&|###' means "field 0 = '&', field 1 = '###'", but there's
						no fixed characters in between.
			===============================================
			
			Repetitions of the same mask code can be represented by placing the number
			of repetitions in curly braces after the code. E.g.: CCCCCCCC = C{6} """))
	
	MaskedValue = property(_getMaskedValue, None, None,
			_("Value of the control, including mask characters, if any. (read-only) (str)"))
	

	

if __name__ == "__main__":
	import test

	class MaskedForm(dabo.ui.dForm):
		def afterInit(self):
			self.Caption = "dMaskedTextBox"
			pnl = dabo.ui.dScrollPanel(self)
			self.Sizer.append1x(pnl, border=20)
			sz = pnl.Sizer = dabo.ui.dGridSizer(MaxCols=2, HGap=5, VGap=5)
			
			lbl = dabo.ui.dLabel(pnl, Caption="Basic Masks")
			lbl.FontSize += 2
			sz.append(lbl, colSpan=2, halign="center")
	
			sz.append(dabo.ui.dLabel(pnl, Caption="Uppercase Letters Only:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Width=240, Mask="A{20}"))
			
			sz.append(dabo.ui.dLabel(pnl, Caption="Lowercase Letters Only:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Width=240, Mask="a{20}"))
			
			sz.append(dabo.ui.dLabel(pnl, Caption="Letters (any case) Only:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Width=240, Mask="C{20}"))
			
			sz.append(dabo.ui.dLabel(pnl, Caption="Punctuation Only:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Width=240, Mask="&{20}"))
			
			sz.append(dabo.ui.dLabel(pnl, Caption="Letter left; Numbers right:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Width=240, Mask="C{6} - #{6}"))
			
			sz.append(dabo.ui.dLabel(pnl, Caption="No Mask:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Width=240, Mask=""))
			lbl = dabo.ui.dLabel(pnl, FontItalic=True,
					Caption="The 'No Mask' value can never be valid,\nand will be cleared when the control loses focus.")
			lbl.FontSize -= 2
			sz.append(lbl, colSpan=2, halign="center")
			
			sz.appendSpacer(10, colSpan=2)
			
			lbl = dabo.ui.dLabel(pnl, Caption="Pre-defined Formats")
			lbl.FontSize += 2
			sz.append(lbl, colSpan=2, halign="center")
	
			fmts = dMaskedTextBox.getFormats()
			fmts.sort()
			for fmt in fmts:
				self.addRow(fmt, pnl)
			
			sz.setColExpand(1, True)
		
		
		def addRow(self, fmt, parent):
			sz = parent.Sizer
			sz.append(dabo.ui.dLabel(parent, Caption="%s:" % fmt), halign="right")
			sz.append(dMaskedTextBox(parent, Width=240, Format=fmt))
			
	test.Test().runTest(MaskedForm)
