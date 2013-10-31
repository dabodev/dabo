# -*- coding: utf-8 -*-
import datetime
import wx
import wx.lib.masked as masked
import dabo
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dabo.dLocalize import _
import dTextBoxMixin as tbm



class dMaskedTextBox(tbm.dTextBoxMixin, masked.TextCtrl):
	"""
	This is a specialized textbox class that supports a Mask property. The
	mask determines what characters are allowed in the textbox, and can also
	include formatting characters that are not part of the control's Value.
	"""
	_allowedInputCodes = ("_", "!", "^", "R", "r", "<", ">", ",", "-", "0", "D", "T", "F", "V", "S")
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
		self._valueMode = None
		self._mask = self._extractKey((properties, attProperties, kwargs), "Mask", "")
		self._format = self._extractKey((properties, attProperties, kwargs), "Format", "")
		self._validregex = self._extractKey((properties, attProperties, kwargs), "ValidRegex", "")
		self._inputCodes = self._uniqueCodes(self._extractKey((properties, attProperties, kwargs),
				"InputCodes", "_>"))
		kwargs["mask"] = self._mask
		kwargs["formatcodes"] = self._inputCodes
		kwargs["validRegex"] = self._validregex
		if self._format:
			code = self._formatMap.get(self._format.lower(), "")
			if code:
				kwargs["autoformat"] = code
				kwargs.pop("mask")
				kwargs.pop("formatcodes")
				kwargs.pop("validRegex")
		kwargs["useFixedWidthFont"] = False

		preClass = wx.lib.masked.TextCtrl
		tbm.dTextBoxMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def getFormats(cls):
		"""Return a list of available format codes."""
		return cls._formatMap.keys()
	getFormats = classmethod(getFormats)


	def _uniqueCodes(self, codes):
		"""
		Take a string and return the same string with any duplicate characters removed.
		The order of the characters is not preserved.
		"""
		return "".join(dict.fromkeys(codes).keys())


	def _onWxHit(self, evt, *args, **kwargs):
		# This fixes wx masked control issue firing multiple EVT_TEXT events.
		if self._value != self.Value:
			super(dMaskedTextBox, self)._onWxHit(evt, *args, **kwargs)


	# property get/set functions
	def _getFormat(self):
		return self._format

	def _setFormat(self, val):
		if self._constructed():
			try:
				self.SetAutoformat(self._formatMap.get(val))
			except AttributeError:
				dabo.log.error(_("Invalid Format value: %s") % val)
				return
			self._format = val
			if not val:
				self.SetMask("")
				self.ClearValue()
		else:
			self._properties["Format"] = val


	def _getInputCodes(self):
		return self.GetFormatcodes()

	def _setInputCodes(self, val):
		if self._constructed():
			if self.GetAutoformat() and val:
				# Cannot have both a mask and a format
				dabo.log.error(_("Cannot set InputCodes when a Format has been set"))
			elif [cd for cd in val if cd not in self._allowedInputCodes]:
				# Illegal codes
				bad = "".join([cd for cd in val if cd not in self._allowedInputCodes])
				dabo.log.error(_("Invalid InputCodes: %s") % bad)
			else:
				val = self._uniqueCodes(val)
				self._inputCodes = val
				self.SetFormatcodes(val)
		else:
			self._properties["InputCodes"] = val


	def _getMask(self):
		return self.GetMask()

	def _setMask(self, val):
		if self._constructed():
			if self.GetAutoformat() and val:
				# Cannot have both a mask and a format
				raise RuntimeError(_("Cannot set a Mask when a Format has been set"))
			else:
				self._mask = val
				self.SetMask(val)
		else:
			self._properties["Mask"] = val


	def _getMaskedValue(self):
		return self.GetValue()


	def _getUnmaskedValue(self):
		return self.GetPlainValue()


	def _getValue(self):
		if self.ValueMode == "Masked":
			ret = self.GetValue()
		else:
			ret = self.GetPlainValue()
		return ret

	def _setValue(self, val):
		if val is None:
			val = ''
			
		super(dMaskedTextBox, self)._setValue(val)


	def _getValueMode(self):
		try:
			if self._valueMode.lower().startswith("m"):
				return "Masked"
			else:
				return "Unmasked"
		except (TypeError, AttributeError):
			return "Unmasked"

	def _setValueMode(self, val):
		if self._constructed():
			self._valueMode = val
		else:
			self._properties["ValueMode"] = val




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

	InputCodes = property(_getInputCodes, _setInputCodes, None,
			_("""Characters that define the type of input that the control will accept.  (str)

			These are the available input codes and their meaning:

			+-----------+---------------------------------------------------------------+
			|Character  |Meaning                                                        |
			+===========+===============================================================+
			|   #       |Allow numeric only (0-9)                                       |
			+-----------+---------------------------------------------------------------+
			|   _       |Allow spaces                                                   |
			+-----------+---------------------------------------------------------------+
			|   !       |Force upper                                                    |
			+-----------+---------------------------------------------------------------+
			|   ^       |Force lower                                                    |
			+-----------+---------------------------------------------------------------+
			|   R       |Right-align field(s)                                           |
			+-----------+---------------------------------------------------------------+
			|   r       |Right-insert in field(s) (implies R)                           |
			+-----------+---------------------------------------------------------------+
			|   <       |Stay in field until explicit navigation out of it              |
			+-----------+---------------------------------------------------------------+
			|   >       |Allow insert/delete within partially filled fields (as         |
			|           |opposed to the default "overwrite" mode for fixed-width        |
			|           |masked edit controls.)  This allows single-field controls      |
			|           |or each field within a multi-field control to optionally       |
			|           |behave more like standard text controls.                       |
			|           |(See EMAIL or phone number autoformat examples.)               |
			|           |                                                               |
			|           |Note: This also governs whether backspace/delete operations    |
			|           |shift contents of field to right of cursor, or just blank the  |
			|           |erased section.                                                |
			|           |                                                               |
			|           |Also, when combined with 'r', this indicates that the field    |
			|           |or control allows right insert anywhere within the current     |
			|           |non-empty value in the field.(Otherwise right-insert behavior  |
			|           |is only performed to when the entire right-insertable field    |
			|           |is selected or the cursor is at the right edge of the field.   |
			+-----------+---------------------------------------------------------------+
			|   ,       |Allow grouping character in integer fields of numeric controls |
			|           |and auto-group/regroup digits (if the result fits) when leaving|
			|           |such a field.  (If specified, .SetValue() will attempt to      |
			|           |auto-group as well.)                                           |
			|           |',' is also the default grouping character.  To change the     |
			|           |grouping character and/or decimal character, use the groupChar |
			|           |and decimalChar parameters, respectively.                      |
			|           |                                                               |
			|           |Note: typing the "decimal point" character in such fields will |
			|           |clip the value to that left of the cursor for integer          |
			|           |fields of controls with "integer" or "floating point" masks.   |
			|           |If the ',' format code is specified, this will also cause the  |
			|           |resulting digits to be regrouped properly, using the current   |
			|           |grouping character.                                            |
			+-----------+---------------------------------------------------------------+
			|   -       |Prepend and reserve leading space for sign to mask and allow   |
			|           |signed values (negative #s shown in red by default.) Can be    |
			|           |used with argument useParensForNegatives (see below.)          |
			+-----------+---------------------------------------------------------------+
			|   0       |integer fields get leading zeros                               |
			+-----------+---------------------------------------------------------------+
			|   D       |Date[/time] field                                              |
			+-----------+---------------------------------------------------------------+
			|   T       |Time field                                                     |
			+-----------+---------------------------------------------------------------+
			|   F       |Auto-Fit: the control calulates its size from                  |
			|           |the length of the template mask                                |
			+-----------+---------------------------------------------------------------+
			|   V       |validate entered chars against validRegex before allowing them |
			|           |to be entered vs. being allowed by basic mask and then having  |
			|           |the resulting value just colored as invalid.                   |
			|           |(See USSTATE autoformat demo for how this can be used.)        |
			+-----------+---------------------------------------------------------------+
			|   S       |select entire field when navigating to new field               |
			+-----------+---------------------------------------------------------------+


			"""))

	Mask = property(_getMask, _setMask, None,
			_("""Display Mask for the control.  (str)

			These are the allowed mask characters and their function:

			+-----------+-------------------------------------------------------------------+
			|Character  |Function                                                           +
			+===========+===================================================================+
			|   #       |Allow numeric only (0-9)                                           |
			+-----------+-------------------------------------------------------------------+
			|   N       |Allow letters and numbers (0-9)                                    |
			+-----------+-------------------------------------------------------------------+
			|   A       |Allow uppercase letters only                                       |
			+-----------+-------------------------------------------------------------------+
			|   a       |Allow lowercase letters only                                       |
			+-----------+-------------------------------------------------------------------+
			|   C       |Allow any letter, upper or lower                                   |
			+-----------+-------------------------------------------------------------------+
			|   X       |Allow string.letters, string.punctuation, string.digits            |
			+-----------+-------------------------------------------------------------------+
			|   &       |Allow string.punctuation only (doesn't include all unicode symbols)|
			+-----------+-------------------------------------------------------------------+
			|   \*      |Allow any visible character                                        |
			+-----------+-------------------------------------------------------------------+
			|   |       |explicit field boundary (takes no space in the control; allows mix |
			|           |of adjacent mask characters to be treated as separate fields,      |
			|           |eg: '&|###' means "field 0 = '&', field 1 = '###'", but there's    |
			|           |no fixed characters in between.                                    |
			+-----------+-------------------------------------------------------------------+

			Repetitions of the same mask code can be represented by placing the number
			of repetitions in curly braces after the code. E.g.: CCCCCCCC = C{6} """))

	MaskedValue = property(_getMaskedValue, None, None,
			_("Value of the control, including mask characters, if any. (read-only) (str)"))

	UnmaskedValue = property(_getUnmaskedValue, None, None,
			_("Value of the control, removing mask characters, if any. (read-only) (str)"))

	Value = property(_getValue, _setValue, None,
			_("""Specifies the content of this control. (str) If ValueMode is set to 'Masked',
			this will include the mask characters. Otherwise it will be the contents without
			any mask characters."""))

	ValueMode = property(_getValueMode, _setValueMode, None,
			_("""Specifies the information that the Value property refers to. (str)
			If it is set to 'Masked' (or anything that begins with the letter 'm'), the
			Value property will return the contents of the control, including any mask
			characters. If this is set to anything other than a string that begins with 'm',
			Value will return the control's contents without the mask characters.
			NOTE: This only affects the results of \*reading\* the Value property. Setting
			Value is not affected in any way."""))



if __name__ == "__main__":
	import test

	class MaskedForm(dabo.ui.dForm):
		def afterInit(self):
			self.Caption = "dMaskedTextBox"
			pgf = dabo.ui.dPageFrame(self, TabPosition="Left", PageCount=3)
			self.Sizer.append1x(pgf, border=20)
			pg1, pg2, pg3 = pgf.Pages
			pg1.Caption = "Basic Masks"
			pg2.Caption = "Pre-defined Formats"
			pg3.Caption = "Input Codes"

			sz = pg1.Sizer = dabo.ui.dGridSizer(MaxCols=2, HGap=5, VGap=5)

			lbl = dabo.ui.dLabel(pg1, Caption="Basic Masks")
			lbl.FontSize += 2
			sz.append(lbl, colSpan=2, halign="center")
			"""The below code does not work in some versions of wxPython because of a bug discovered
			in wxPython 2.8.9.1 maskededit.py.  If you find that you have such a version, either upgrade
			to a newer wxPython, or you can fix it in your own wx code. Find the line in
			'lib/masked/maskededit.py' that reads:
			'if field._forcelower and key in range(97,123):'
			and replace it with
			'if field._forcelower and key in range(65,90):'  """
			sz.append(dabo.ui.dLabel(pg1, Caption="""Forced Lowercase Letters Only:
(May not work in older
versions of wxPython)"""), halign="right")
			sz.append(dMaskedTextBox(pg1, Width=240, InputCodes='^',Mask="C{20}"), valign="Top")

			sz.append(dabo.ui.dLabel(pg1, Caption="Accepts Uppercase Letters Only:"), halign="right")
			sz.append(dMaskedTextBox(pg1, Width=240, Mask="A{20}"))

			sz.append(dabo.ui.dLabel(pg1, Caption="Forced Uppercase Letters Only:"), halign="right")
			sz.append(dMaskedTextBox(pg1, Width=240,InputCodes='!>',Mask="C{20}"))

			sz.append(dabo.ui.dLabel(pg1, Caption="Lowercase Letters Only:"), halign="right")
			sz.append(dMaskedTextBox(pg1, Width=240, Mask="a{20}"))

			sz.append(dabo.ui.dLabel(pg1, Caption="Letters (any case) Only:"), halign="right")
			sz.append(dMaskedTextBox(pg1, Width=240, Mask="C{20}"))

			sz.append(dabo.ui.dLabel(pg1, Caption="Punctuation Only:"), halign="right")
			sz.append(dMaskedTextBox(pg1, Width=240, Mask="&{20}"))

			sz.append(dabo.ui.dLabel(pg1, Caption="Letter left; Numbers right:"), halign="right")
			sz.append(dMaskedTextBox(pg1, Width=240, Mask="C{6} - #{6}"))

			sz.append(dabo.ui.dLabel(pg1, Caption="No Mask:"), halign="right")
			sz.append(dMaskedTextBox(pg1, Width=240, Mask=""))
			lbl = dabo.ui.dLabel(pg1, FontItalic=True,
					Caption="The 'No Mask' value can never be valid,\nand will be cleared when the control loses focus.")
			lbl.FontSize -= 2
			sz.append(lbl, colSpan=2, halign="center")
			sz.setColExpand(1, True)

			sz = pg2.Sizer = dabo.ui.dGridSizer(MaxCols=2, HGap=5, VGap=5)

			lbl = dabo.ui.dLabel(pg2, Caption="Pre-defined Formats")
			lbl.FontSize += 2
			sz.append(lbl, colSpan=2, halign="center")

			fmts = dMaskedTextBox.getFormats()
			fmts.sort()
			for fmt in fmts:
				self.addRow(fmt, pg2)
			sz.setColExpand(1, True)

			sz = pg3.Sizer = dabo.ui.dSizer("V", DefaultBorder=10, DefaultBorderLeft=True,
					DefaultBorderRight=True)
			sz.appendSpacer(10)
			lbl = dabo.ui.dLabel(pg3, Caption="Check/Uncheck the following InputCodes to apply them\n" +
					"to the textbox below. Then type into the textbox to see\nthe effect that each code has.",
					FontBold=True, Alignment="Center")
			sz.append(lbl, "x")
			sz.appendSpacer(5)
			gsz = dabo.ui.dGridSizer(MaxCols=4, HGap=25, VGap=5)
			lbl = dabo.ui.dLabel(pg3, Caption="General Codes", FontBold=True)
			gsz.append(lbl, halign="center", colSpan=4)
			chk = dabo.ui.dCheckBox(pg3, Caption="_", ToolTipText="Allow Spaces",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption="R", ToolTipText="Right Align",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption="r", ToolTipText="Right Insert",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption="<", ToolTipText="Stay in field until explicit navigation",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption=">", ToolTipText="Insert/delete inside fields",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption="F", ToolTipText="Auto-fit field width",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption="V", ToolTipText="Validate against ValidRegex property",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption="S", ToolTipText="Select full field",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			sz.append(gsz, 1, halign="center")
			sz.appendSpacer(5)

			gsz = dabo.ui.dGridSizer(MaxCols=2, HGap=25, VGap=5)
			lbl = dabo.ui.dLabel(pg3, Caption="Character Codes", FontBold=True)
			gsz.append(lbl, halign="center", colSpan=2)
			chk = dabo.ui.dCheckBox(pg3, Caption="!", ToolTipText="Force Upper Case",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption="^", ToolTipText="Force Lower Case",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			txt = self.charText = dabo.ui.dMaskedTextBox(pg3, Value="", Mask="C{30}")
			gsz.append(txt, "x", colSpan=2)
			sz.append(gsz, 1, halign="center")
			sz.appendSpacer(5)

			gsz = dabo.ui.dGridSizer(MaxCols=2, HGap=25, VGap=5)
			lbl = dabo.ui.dLabel(pg3, Caption="Numeric Codes", FontBold=True)
			gsz.append(lbl, halign="center", colSpan=2)
			chk = dabo.ui.dCheckBox(pg3, Caption=",", ToolTipText="Allow grouping character in numeric values",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption="-", ToolTipText="Reserve space for leading sign for negatives",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption="0", ToolTipText="Leading Zeros in integer fields",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			gsz.appendSpacer(1)
			txt = self.numText = dabo.ui.dMaskedTextBox(pg3, Value="", Mask="#{30}")
			gsz.append(txt, "x", colSpan=2)
			sz.append(gsz, 1, halign="center")
			sz.appendSpacer(5)

			gsz = dabo.ui.dGridSizer(MaxCols=2, HGap=25, VGap=5)
			lbl = dabo.ui.dLabel(pg3, Caption="Date/DateTime/Time Codes", FontBold=True)
			gsz.append(lbl, halign="center", colSpan=2)
			chk = dabo.ui.dCheckBox(pg3, Caption="D", ToolTipText="Date/Datetime field",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			chk = dabo.ui.dCheckBox(pg3, Caption="T", ToolTipText="Time Field",
					OnHit=self.onCheckHit)
			gsz.append(chk)
			txt = self.dateText = dabo.ui.dMaskedTextBox(pg3, InputCodes="D", Value=datetime.date.today())
			gsz.append(txt, "x", colSpan=2)
			sz.append(gsz, 1, halign="center")

		def _lookup(self,evt):
			pass
		def onCheckHit(self, evt):
			chk = evt.EventObject
			cap = chk.Caption
			val = chk.Value
			print cap, val
			txts = (self.charText, self.numText, self.dateText)
			if cap in "!^":
				# Char
				txts = (self.charText, )
			elif cap in ",-0":
				# Num
				txts = (self.numText, )
			elif cap in "DT":
				# Num
				txts = (self.dateText, )
			for txt in txts:
				if val:
					txt.InputCodes += cap
				else:
					txt.InputCodes = txt.InputCodes.replace(chk.Caption, "")
				txt.setFocus()
				txt.refresh()


		def addRow(self, fmt, parent):
			sz = parent.Sizer
			sz.append(dabo.ui.dLabel(parent, Caption="%s:" % fmt), halign="right")
			sz.append(dMaskedTextBox(parent, Width=240, Format=fmt))

	test.Test().runTest(MaskedForm)
