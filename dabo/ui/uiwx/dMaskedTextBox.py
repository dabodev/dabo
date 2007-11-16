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

	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):	
		self._baseClass = dMaskedTextBox
		self._mask = self._extractKey((properties, attProperties, kwargs), "Mask", "")
		kwargs["mask"] = self._mask
		kwargs["formatcodes"] = "_"
		#kwargs["useFixedWidthFont"] = bool(self._mask)
		kwargs["useFixedWidthFont"] = True
		
		preClass = wx.lib.masked.TextCtrl
		tbm.dTextBoxMixin.__init__(self, preClass, parent, properties, attProperties, 
				*args, **kwargs)


	# property get/set functions
	def _getMask(self):
		return self._mask

	def _setMask(self, val):
		if self._constructed():
			self._mask = val
			try:
				self.SetMask(val)
			except AttributeError:
				raise TypeError, _("You must initialize the Mask property when the control is constructed.")
		else:
			self._properties["Mask"] = val


	def _getMaskedValue(self):
		return self.GetValue()


	# Property definitions:
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
			"""))
	
	MaskedValue = property(_getMaskedValue, None, None,
			_("Value of the control, including mask characters, if any. (read-only) (str)"))
	

	

if __name__ == "__main__":
	import test

	class TestBase(dMaskedTextBox):
		def initProperties(self):
			self.SelectOnEntry = True
			super(TestBase, self).initProperties()
			self.LogEvents = ["ValueChanged",]
			
		def onValueChanged(self, evt):
			print "%s.onValueChanged:" % self.Name, self.Value, type(self.Value),
			print "Masked Value:", self.MaskedValue

	class UsPhoneText(TestBase):
		def __init__(self, *args, **kwargs):
			kwargs["Mask"] = "(###) ###-####"
			super(UsPhoneText, self).__init__(*args, **kwargs)

	class UsSSNText(TestBase):
		def __init__(self, *args, **kwargs):
			kwargs["Mask"] = "###-##-####"
			super(UsSSNText, self).__init__(*args, **kwargs)

	class NoMaskText(TestBase):
		def __init__(self, *args, **kwargs):
			kwargs["Mask"] = ""
			super(NoMaskText, self).__init__(*args, **kwargs)


	class MaskedForm(dabo.ui.dForm):
		def afterInit(self):
			self.Caption = "dMaskedTextBox"
			pnl = dabo.ui.dPanel(self)
			self.Sizer.append1x(pnl)
			sz = pnl.Sizer = dabo.ui.dGridSizer(MaxCols=2, HGap=3, VGap=5)
			sz.append(dabo.ui.dLabel(pnl, Caption="US Phone Format:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Mask="(###) ###-####"), "x")
			
			sz.append(dabo.ui.dLabel(pnl, Caption="US SSN Format:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Mask="###-##-####"), "x")
			
			sz.append(dabo.ui.dLabel(pnl, Caption="Uppercase Letters Only:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Mask="A"*20), "x")
			
			sz.append(dabo.ui.dLabel(pnl, Caption="Lowercase Letters Only:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Mask="a"*20), "x")
			
			sz.append(dabo.ui.dLabel(pnl, Caption="Letters (any case) Only:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Mask="C"*20), "x")
			
			sz.append(dabo.ui.dLabel(pnl, Caption="Punctuation Only:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Mask="&"*20), "x")
			
			sz.append(dabo.ui.dLabel(pnl, Caption="Letter left; Numbers right:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Mask="CCCCCC - ######"), "x")
			
			sz.append(dabo.ui.dLabel(pnl, Caption="No Mask:"), halign="right")
			sz.append(dMaskedTextBox(pnl, Mask=""), "x")
			lbl = dabo.ui.dLabel(pnl, FontItalic=True,
					Caption="The 'No Mask' value can never be valid,\nand will be cleared when the control loses focus.")
			lbl.FontSize -= 2
			sz.append(lbl, colSpan=2, halign="center")
			
			sz.setColExpand(1, True)
			
	test.Test().runTest(MaskedForm)
