# -*- coding: utf-8 -*-
import dabo.ui
import dabo.dEvents as dEvents
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dabo.ui import dKeys as dKeys
from dabo.dLocalize import _


class HotKeyEditor(dabo.ui.dOkCancelDialog):
	def addControls(self):
		self.Caption = _("HotKey Editor")
		self._alt = False
		self._changed = None
		self._ctrl = False
		self._keyChar = ""
		self._keyCode = -1
		self._keyText = ""
		self._shift = False
		self._originalKeyString = None

		sz = self.Sizer
		sz.append(dabo.ui.dLabel(self, Caption=_("Press the desired key combination")),
				border=10, halign="center")
		sz.append(dabo.ui.dLabel(self, Caption=_("Press Ctrl-Delete to clear the key")),
				border=10, halign="center")
		sz.appendSpacer(10)
		bsz = dabo.ui.dBorderSizer(self, "v")
		self.hkLabel = dabo.ui.dLabel(self, Caption=" "*80, FontSize=16, FontBold=True)
		bsz.append1x(self.hkLabel, halign="center", border=10)
		sz.append(bsz, halign="center")
		# Pass key events from the OK/Cancel buttons up to the form
		self.CancelButton.bindEvent(dEvents.KeyUp, self.onKeyUp)
		self.OKButton.bindEvent(dEvents.KeyUp, self.onKeyUp)


	def setKey(self, key):
		self._originalKeyString = self._keyText = self.hkLabel.Caption = key


	def onKeyUp(self, evt):
		self._keyCode = kcd = evt.keyCode
		if kcd in (306, 307, 308, 396, 400):
			# Just the modifier keys being released
			return
		if kcd in (dKeys.key_Tab, dKeys.key_Escape, dKeys.key_Return):
			# Navigation keys; ignore
			return
		self._keyChar = kcr = evt.keyChar
		self._ctrl = dabo.ui.isControlDown() or dabo.ui.isCommandDown()
		self._shift = dabo.ui.isShiftDown()
		self._alt = dabo.ui.isAltDown()
		keyStrings = {dKeys.key_Back: "Back", dKeys.key_Delete: "Del", dKeys.key_Pageup: "PgUp",
				dKeys.key_Pagedown: "PgDn", dKeys.key_Insert: "Ins", dKeys.key_Home: "Home",
				dKeys.key_End: "End", dKeys.key_Left: "Left", dKeys.key_Right: "Right",
				dKeys.key_Up: "Up", dKeys.key_Down: "Down"}
		if 340 <= kcd <= 354:
			# Function keys
			self._keyChar = kcr = "F%s" % ((kcd-339), )
		elif kcd == dKeys.key_Delete and self._ctrl:
			# Ctrl-Delete was pressed
			kcr = None
		elif kcd in keyStrings.keys():
			self._keyChar = kcr = keyStrings[kcd]
		if kcr is not None:
			ctlTxt = {True: "Ctrl+", False: ""}[self._ctrl]
			shiftTxt = {True: "Shift+", False: ""}[self._shift]
			altTxt = {True: "Alt+", False: ""}[self._alt]
			self._keyText = ctlTxt + altTxt + shiftTxt + kcr.upper()
		else:
			self._keyText = None
			self._keyChar = None
		self.hkLabel.Caption = self._keyText
		self.layout()
		self.fitToSizer()


	# Property definitions start here
	def _getAlt(self):
		return self._alt


	def _getChanged(self):
		orig = self._originalKeyString
		return orig is not None and (orig != self._keyText)


	def _getCtrl(self):
		return self._ctrl


	def _getKeyChar(self):
		return self._keyChar


	def _getKeyCode(self):
		return self._keyCode


	def _getKeyText(self):
		return self._keyText


	def _getShift(self):
		return self._shift


	Alt = property(_getAlt, None, None,
			_("Reflects the presence of the Alt key in the selected key combo. Default=False.  (bool)"))

	Changed = property(_getChanged, None, None,
			_("Returns True only if the current key is different than the starting value. (read-only) (bool)"))

	Ctrl = property(_getCtrl, None, None,
			_("Reflects the presence of the Ctrl key in the selected key combo. Default=False. (read-only) (bool)"))

	KeyChar = property(_getKeyChar, None, None,
			_("The non-modifier key in the selected key combo. Default="". (read-only) (str)"))

	KeyCode = property(_getKeyCode, None, None,
			_("Underlying key code of the key/modifier combo. Default=-1 (read-only) (int)"))

	KeyText = property(_getKeyText, None, None,
			_("The displayed text for the key/modifier combo. Default="" (read-only) (str)"))

	Shift = property(_getShift, None, None,
			_("Reflects the presence of the Alt key in the selected key combo. Default=False. (read-only) (bool)"))

