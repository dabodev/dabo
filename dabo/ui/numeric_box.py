# -*- coding: utf-8 -*-
import locale
from decimal import Decimal

import wx
import wx.lib.masked as masked

from .. import events, ui
from ..dLocalize import _
from . import dDataControlMixin as ddcm
from . import dTextBoxMixin, makeDynamicProperty


class dNumericBox(dTextBoxMixin, masked.NumCtrl):
    """This is a specialized textbox class that maintains numeric values."""

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        localeData = locale.localeconv()
        enc = locale.getdefaultlocale()[1]
        self._baseClass = dNumericBox
        kwargs["integerWidth"] = self._extractKey(
            (properties, attProperties, kwargs), "IntegerWidth", 10
        )
        kwargs["fractionWidth"] = self._extractKey(
            (properties, attProperties, kwargs), "DecimalWidth", 2
        )
        kwargs["Alignment"] = self._extractKey(
            (properties, attProperties, kwargs), "Alignment", "Right"
        )
        kwargs["selectOnEntry"] = self._extractKey(
            (properties, attProperties, kwargs), "SelectOnEntry", self.SelectOnEntry
        )
        # groupChar = self._extractKey((properties, attProperties, kwargs),
        # "GroupChar", localeData["thousands_sep"].decode(enc))
        groupChar = self._extractKey(
            (properties, attProperties, kwargs),
            "GroupChar",
            localeData["thousands_sep"],
        )
        # Group char can't be empty string.
        if groupChar or groupChar >= " ":
            kwargs["groupChar"] = groupChar
            kwargs["groupDigits"] = True
        else:
            kwargs["groupChar"] = " "
            kwargs["groupDigits"] = False
        kwargs["autoSize"] = self._extractKey(
            (properties, attProperties, kwargs), "AutoWidth", True
        )
        kwargs["allowNegative"] = self._extractKey(
            (properties, attProperties, kwargs), "AllowNegative", True
        )
        kwargs["useParensForNegatives"] = self._extractKey(
            (properties, attProperties, kwargs), "ParensForNegatives", False
        )
        # kwargs["decimalChar"] = self._extractKey((properties, attProperties, kwargs),
        # "DecimalChar", localeData["decimal_point"].decode(enc))

        kwargs["decimalChar"] = self._extractKey(
            (properties, attProperties, kwargs),
            "DecimalChar",
            localeData["decimal_point"],
        )
        kwargs["foregroundColour"] = self._extractKey(
            (properties, attProperties, kwargs), "ForeColor", "Black"
        )
        kwargs["validBackgroundColour"] = self._extractKey(
            (properties, attProperties, kwargs),
            "BackColor",
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
        )
        kwargs["invalidBackgroundColour"] = self._extractKey(
            (properties, attProperties, kwargs), "InvalidBackColor", "Yellow"
        )
        kwargs["signedForegroundColour"] = self._extractKey(
            (properties, attProperties, kwargs), "SignedForeColor", "Red"
        )
        kwargs["allowNone"] = self._extractKey(
            (properties, attProperties, kwargs), "AllowNoneValue", False
        )
        kwargs["max"] = self._extractKey((properties, attProperties, kwargs), "MaxValue", None)
        kwargs["min"] = self._extractKey((properties, attProperties, kwargs), "MinValue", None)
        # Base class 'limited' property is inconvenient.
        kwargs["limited"] = False
        fontFace = self._extractKey((properties, attProperties, kwargs), "FontFace", "")
        if not fontFace and self.Application.Platform in ("Win",):
            fontFace = "Tahoma"
        elif not fontFace and self.Application.Platform in ("Mac",):
            fontFace = "Lucida Grande"
        if fontFace:
            kwargs["FontFace"] = fontFace
        dTextBoxMixin.__init__(
            self, masked.NumCtrl, parent, properties, attProperties, *args, **kwargs
        )

    # --- Public interface.

    def flushValue(self):
        # Because dTextBoxMixin method is improper here,
        # we use superclass method instead.
        return ddcm.flushValue(self)

    def getBlankValue(self):
        dec = self.DecimalWidth
        if dec > 0:
            return Decimal("0.%s" % ("0" * dec))
        else:
            return 0

    def GetParensForNegatives(self):
        return self._useParensForNegatives

    def update(self):
        # Be very careful! If limits across allowed value,
        # control value will be automatically reseted to default value.
        maxVal = self.MaxValue
        self.MaxValue = None
        minVal = self.MinValue
        self.MinValue = None
        super(dNumericBox, self).update()
        if not "MaxValue" in self._dynamic:
            self.MaxValue = maxVal
        if not "MinValue" in self._dynamic:
            self.MinValue = minVal

    # --- Internal class interface.

    def _initEvents(self):
        super(dNumericBox, self)._initEvents()
        self.bindEvent(events.GotFocus, self._onGotFocusFix)
        self.bindEvent(events.LostFocus, self._onLostFocusFix)

    def _onGotFocusFix(self, evt):
        ui.callAfter(self._fixInsertionPoint)

    def _onLostFocusFix(self, evt):
        if self.LimitValue:
            max = self.MaxValue
            min = self.MinValue
            # if (max is not None and not (max >= self._value)) or \
            #        (min is not None and not (self._value >= min)):
            #    evt.stop()
            #    self.setFocus()

    def _onWxHit(self, evt, *args, **kwargs):
        # This fix wx masked controls issue firing multiple EVT_TEXT events.
        if self._value != self.Value:
            super(dNumericBox, self)._onWxHit(evt, *args, **kwargs)

    def _fixInsertionPoint(self):
        """Fixes insertion point position when value change or
        when getting focus with mouse click."""
        if self.Enabled and not self.ReadOnly:
            dw = self.DecimalWidth
            if dw > 0:
                self.InsertionPoint = self._masklength - dw - 1
            else:
                self.InsertionPoint = self._masklength
            if self.SelectOnEntry:
                ui.callAfter(self.select, 0, self.InsertionPoint)

    # --- Properties definitions.

    @property
    def AllowNegative(self):
        """Enables/disables negative numbers. Default=True  (bool)"""
        return self.GetAllowNegative()

    @AllowNegative.setter
    def AllowNegative(self, val):
        if self._constructed():
            self.SetAllowNegative(val)
        else:
            self._properties["AllowNegative"] = val

    @property
    def AllowNoneValue(self):
        """Enables/disables undefined value - None. Default=False  (bool)"""
        return self.GetAllowNone()

    @AllowNoneValue.setter
    def AllowNoneValue(self, val):
        if self._constructed():
            self.SetAllowNone(val)
        else:
            self._properties["AllowNoneValue"] = val

    @property
    def AutoWidth(self):
        """
        Indicates whether or not the control should set its own width based on the integer and
        fraction widths. Default=True  (bool)
        """
        return self.GetAutoSize()

    @AutoWidth.setter
    def AutoWidth(self, val):
        if self._constructed():
            self.SetAutoSize(val)
        else:
            self._properties["AutoWidth"] = val

    @property
    def DecimalChar(self):
        """
        Defines character that will be used to represent the decimal point. Default value
        comes from locale setting.  (str)
        """
        return self.GetDecimalChar()

    @DecimalChar.setter
    def DecimalChar(self, val):
        if self._constructed():
            self.SetDecimalChar(val)
        else:
            self._properties["DecimalChar"] = val

    @property
    def DecimalWidth(self):
        """Tells how many decimal places to show for numeric value. Default=2  (int)"""
        return self.GetFractionWidth()

    @DecimalWidth.setter
    def DecimalWidth(self, val):
        if self._constructed():
            self.SetFractionWidth(val)
        else:
            self._properties["DecimalWidth"] = val

    @property
    def GroupChar(self):
        """
        What grouping character will be used if allowed. If set to None, no grouping is allowed.
        Default value comes from locale setting. (str)
        """
        if self.GetGroupDigits():
            ret = self.GetGroupChar()
        else:
            ret = None
        return ret

    @GroupChar.setter
    def GroupChar(self, val):
        """Set GroupChar to None to avoid grouping."""
        if self._constructed():
            if val is None:
                self.SetGroupDigits(False)
            else:
                self.SetGroupChar(val)
                self.SetGroupDigits(True)
        else:
            self._properties["GroupChar"] = val

    @property
    def IntegerWidth(self):
        """
        Indicates how many places to the right of any decimal point should be allowed in the
        control. Default=10  (int)
        """
        return self.GetIntegerWidth()

    @IntegerWidth.setter
    def IntegerWidth(self, val):
        if self._constructed():
            self.SetIntegerWidth(val)
        else:
            self._properties["IntegerWidth"] = val

    @property
    def InvalidBackColor(self):
        """Color value used for illegal values or values out-of-bounds. Default='Yellow'  (str)"""
        return self.GetInvalidBackgroundColour()

    @InvalidBackColor.setter
    def InvalidBackColor(self, val):
        if self._constructed():
            self.SetInvalidBackgroundColour(val)
        else:
            self._properties["InvalidBackColor"] = val

    @property
    def LimitValue(self):
        """
        Limit control value to Min and Max bounds. When set to True, if invalid, will be
        automatically reseted to default.  When False, only background color will change.
        Default=False  (bool)
        """
        return getattr(self, "_limitValue", False)

    @LimitValue.setter
    def LimitValue(self, val):
        self._limitValue = bool(val)

    @property
    def MaxValue(self):
        """
        The maximum value that the control should allow. Set to None if limit is disabled.
        Default=None  (int, decimal)
        """
        val = self.GetMax()
        if val is not None and self._lastDataType is Decimal:
            val = Decimal(str(val))
        return val

    @MaxValue.setter
    def MaxValue(self, val):
        if self._constructed():
            if isinstance(val, Decimal):
                val = float(val)
            self.SetMax(val)
        else:
            self._properties["MaxValue"] = val

    @property
    def MinValue(self):
        """
        The minimum value that the control should allow. Set to None if limit is disabled.
        Default=None  (int, decimal)
        """
        val = self.GetMin()
        if val is not None and self._lastDataType is Decimal:
            val = Decimal(str(val))
        return val

    @MinValue.setter
    def MinValue(self, val):
        if self._constructed():
            if isinstance(val, Decimal):
                val = float(val)
            self.SetMin(val)
        else:
            self._properties["MinValue"] = val

    @property
    def ParensForNegatives(self):
        """
        If true, this will cause negative numbers to be displayed with parens rather than with sign
        mark. Default=False  (bool)
        """
        return self.GetUseParensForNegatives()

    @ParensForNegatives.setter
    def ParensForNegatives(self, val):
        if self._constructed():
            self.SetUseParensForNegatives(val)
        else:
            self._properties["ParensForNegatives"] = val

    @property
    def SelectOnEntry(self):
        """Specifies whether all text gets selected upon receiving focus. (bool)  Default=False"""
        try:
            return self.GetSelectOnEntry()
        except AttributeError:
            return False

    @SelectOnEntry.setter
    def SelectOnEntry(self, val):
        self.SetSelectOnEntry(bool(val))

    @property
    def SignedForeColor(self):
        """Color value used for negative values of the control. Default='Red'  (str)"""
        return self.GetSignedForegroundColour()

    @SignedForeColor.setter
    def SignedForeColor(self, val):
        if self._constructed():
            self.SetSignedForegroundColour(val)
        else:
            self._properties["SignedForeColor"] = val

    @property
    def Value(self):
        """Specifies the current state of the control (the value of the field).  (int, Decimal)"""
        val = ddcm.Value
        if self._lastDataType is Decimal:
            val = Decimal(str(val))
        elif self._lastDataType is type(None):
            chkVal = int(val)
            if chkVal != val:
                val = Decimal(str(val))
            elif chkVal != 0:
                val = chkVal
            else:
                val = None
        return val

    @Value.setter
    def Value(self, val):
        self._lastDataType = type(val)
        if self._lastDataType is Decimal:
            val = float(val)
        elif val is None:
            val = float(0)
        # ddcm.dDataControlMixin._setValue(self, val)
        ddcm.Value = val
        ui.callAfter(self._fixInsertionPoint)

    DynamicMaxValue = makeDynamicProperty(MaxValue)
    DynamicMinValue = makeDynamicProperty(MinValue)


ui.dNumericBox = dNumericBox


if __name__ == "__main__":
    from . import test

    class _testDecimal2(dNumericBox):
        def initProperties(self):
            self.Value = Decimal("1.23")
            self.DecimalWidth = 3

    class _testDecimal0(dNumericBox):
        def initProperties(self):
            self.Value = Decimal("23")
            self.DecimalWidth = 0

    test.Test().runTest((_testDecimal2, _testDecimal0))
