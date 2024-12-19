# -*- coding: utf-8 -*-
from ... import events, ui
from ...dLocalize import _
from .. import dKeys, dOkCancelDialog


class HotKeyEditor(dOkCancelDialog):
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
        sz.append(
            dLabel(self, Caption=_("Press the desired key combination")),
            border=10,
            halign="center",
        )
        sz.append(
            dLabel(self, Caption=_("Press Ctrl-Delete to clear the key")),
            border=10,
            halign="center",
        )
        sz.appendSpacer(10)
        bsz = dBorderSizer(self, "v")
        self.hkLabel = dLabel(self, Caption=" " * 80, FontSize=16, FontBold=True)
        bsz.append1x(self.hkLabel, halign="center", border=10)
        sz.append(bsz, halign="center")
        # Pass key events from the OK/Cancel buttons up to the form
        self.CancelButton.bindEvent(events.KeyUp, self.onKeyUp)
        self.OKButton.bindEvent(events.KeyUp, self.onKeyUp)

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
        self._ctrl = ui.isControlDown() or ui.isCommandDown()
        self._shift = ui.isShiftDown()
        self._alt = ui.isAltDown()
        keyStrings = {
            dKeys.key_Back: "Back",
            dKeys.key_Delete: "Del",
            dKeys.key_Pageup: "PgUp",
            dKeys.key_Pagedown: "PgDn",
            dKeys.key_Insert: "Ins",
            dKeys.key_Home: "Home",
            dKeys.key_End: "End",
            dKeys.key_Left: "Left",
            dKeys.key_Right: "Right",
            dKeys.key_Up: "Up",
            dKeys.key_Down: "Down",
        }
        if 340 <= kcd <= 354:
            # Function keys
            self._keyChar = kcr = "F%s" % ((kcd - 339),)
        elif kcd == dKeys.key_Delete and self._ctrl:
            # Ctrl-Delete was pressed
            kcr = None
        elif kcd in list(keyStrings.keys()):
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

    # Property definitions
    @property
    def Alt(self):
        """Reflects the presence of the Alt key in the selected key combo. Default=False.  (bool)"""
        return self._alt

    @property
    def Changed(self):
        """
        Returns True only if the current key is different than the starting value. (read-only)
        (bool)
        """
        orig = self._originalKeyString
        return orig is not None and (orig != self._keyText)

    @property
    def Ctrl(self):
        """
        Reflects the presence of the Ctrl key in the selected key combo. Default=False.  (read-only)
        (bool)
        """
        return self._ctrl

    @property
    def KeyChar(self):
        """The non-modifier key in the selected key combo. Default="""
        return self._keyChar

    @property
    def KeyCode(self):
        """Underlying key code of the key/modifier combo. Default=-1 (read-only) (int)"""
        return self._keyCode

    @property
    def KeyText(self):
        """The displayed text for the key/modifier combo. Default="""
        return self._keyText

    @property
    def Shift(self):
        """
        Reflects the presence of the Alt key in the selected key combo. Default=False.  (read-only)
        (bool)
        """
        return self._shift
