# -*- coding: utf-8 -*-
import datetime
import decimal
import locale
import re
import time

import wx
import wx.lib.masked as masked

from .. import application
from .. import events
from .. import settings
from .. import ui
from ..lib import dates
from ..lib.utils import ustr
from ..localization import _
# pyrefly: ignore  # missing-module-attribute
from ..ui import dDataControlMixin
from ..ui import dKeys
from ..ui import makeDynamicProperty

dabo_module = settings.get_dabo_package()

numericTypes = (int, int, decimal.Decimal, float)
valueErrors = (ValueError, decimal.InvalidOperation)

# Make this locale-independent
# JK: We can't set this up on module load because locale
# is set not until dApp is completely setup.
decimalPoint = None


# pyrefly: ignore  # invalid-inheritance
class dTextBoxMixinBase(dDataControlMixin):
    def __init__(self, preClass, parent, properties=None, attProperties=None, *args, **kwargs):
        global decimalPoint
        if decimalPoint is None:
            decimalPoint = locale.localeconv()["decimal_point"]
        self._oldVal = ""
        self._forceCase = None
        self._inForceCase = False
        self._inFlush = False
        self._textLength = None
        self._inTextLength = False
        self._flushOnLostFocus = True  ## see ui.dDataControlMixinBase::flushValue()
        self._auto_resize_type = None
        ui.callAfter(self._autosize)

        dDataControlMixin.__init__(
            # pyrefly: ignore  # bad-argument-type
            self,
            preClass,
            parent,
            # pyrefly: ignore  # unexpected-keyword
            properties=properties,
            # pyrefly: ignore  # unexpected-keyword
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def _initEvents(self):
        super()._initEvents()
        self.Bind(wx.EVT_TEXT, self._onWxHit)

    def _onWxHit(self, evt):
        super()._onWxHit(evt)
        if self.AutoResizeType:
            self._autosize()

    def flushValue(self):
        # Call the wx SetValue() directly to reset the string value displayed to the user.
        # This resets the value to the string representation as Python shows it. Also, we
        # must save and restore the InsertionPosition because wxGtk at least resets it to
        # 0 upon SetValue().
        if self._inFlush:
            return
        self._inFlush = True
        self._updateStringDisplay()
        ret = super().flushValue()
        self._inFlush = False
        return ret

    def _updateStringDisplay(self):
        insPos = self.InsertionPosition
        startPos = self.SelectionStart
        endPos = self.SelectionEnd
        setter = self.SetValue
        if hasattr(self, "ChangeValue"):
            setter = self.ChangeValue
        setter(self.getStringValue(self.Value))
        self.InsertionPosition = insPos
        self.SelectionStart = startPos
        self.SelectionEnd = endPos

    def getStringValue(self, val):
        """Hook function if you want to implement dataTypes other than str"""
        return val

    def selectAll(self):
        """
        Each subclass must define their own selectAll method. This will
        be called if SelectOnEntry is True when the control gets focus.
        """
        self.SetSelection(-1, -1)

    def getBlankValue(self):
        return ""

    def __onKeyChar(self, evt):
        """This handles KeyChar events when ForceCase is set to a non-empty value."""
        if not self:
            # The control is being destroyed
            return
        keyCode = evt.keyCode
        # pyrefly: ignore  # missing-attribute
        if keyCode >= dKeys.key_Space:
            ui.callAfter(self._checkForceCase)
            ui.callAfter(self._checkTextLength)

    def _checkTextLength(self):
        """
        If the TextLength property is set, checks the current value of the control
        and truncates it if too long
        """
        if not self:
            # The control is being destroyed
            return
        if not isinstance(self.Value, str):
            # Don't bother if it isn't a string type
            return
        length = self.TextLength
        if not length:
            return

        insPos = self.InsertionPosition
        self._inTextLength = True
        if len(self.Value) > length:
            self.Value = self.Value[:length]
            if insPos > length:
                self.InsertionPosition = length
            else:
                self.InsertionPosition = insPos
        self._inTextLength = False

    def _checkForceCase(self):
        """
        If the ForceCase property is set, casts the current value of the control
        to the specified case.
        """
        if not self:
            # The control is being destroyed
            return
        currVal = self.Value
        if not isinstance(currVal, str):
            # Don't bother if it isn't a string type
            return
        case = self.ForceCase
        if not case:
            return
        insPos = self.InsertionPosition
        selLen = self.SelectionLength
        self._inForceCase = True
        if case == "upper":
            newValue = currVal.upper()
        elif case == "lower":
            newValue = currVal.lower()
        elif case == "title":
            newValue = currVal.title()
        else:
            newValue = currVal
        if currVal != newValue:
            self.Value = newValue
            self.InsertionPosition = insPos
            self.SelectionLength = selLen
        self._inForceCase = False

    def charsBeforeCursor(self, num=None, includeSelectedText=False):
        """
        Returns the characters immediately before the current InsertionPoint,
        or, if there is selected text, before the beginning of the current
        selection. By default, it will return one character, but you can specify
        a greater number to be returned. If there is selected text, and
        includeSelectedText is True, this will return the string consisting of
        the characters before plus the selected text.
        """
        if num is None:
            num = 1
        return self._substringByRange(before=num, includeSelectedText=includeSelectedText)

    def charsAfterCursor(self, num=None, includeSelectedText=False):
        """
        Returns the characters immediately after the current InsertionPoint,
        or, if there is selected text, before the end of the current selection.
        By default, it will return one character, but you can specify a greater
        number to be returned.
        """
        if num is None:
            num = 1
        return self._substringByRange(after=num, includeSelectedText=includeSelectedText)

    def _substringByRange(self, before=0, after=0, includeSelectedText=False):
        """
        Handles the substring calculation for the chars[Before|After]Cursor()
        methods.
        """
        start, end = self.GetSelection()
        ret = ""
        if before:
            if includeSelectedText:
                ret = self.GetRange(max(0, start - before), end)
            else:
                ret = self.GetRange(max(0, start - before), start)
        else:
            if includeSelectedText:
                ret = self.GetRange(start, end + after)
            else:
                ret = self.GetRange(end, end + after)
        return ret

    def _autosize(self):
        if self._auto_resize_type is None:
            return
        sz_typ = self._auto_resize_type
        best_width = self.DoGetBestSize()[0]
        need_resize = sz_typ == "All"
        if not need_resize:
            # Grow
            need_resize = self.Width < best_width
        if need_resize:
            print("Sz", self.Size)
            # pyrefly: ignore  # implicitly-defined-attribute
            self.Width = best_width
            print("Sz", self.Size)
            self.Parent.layout()

    # Property Definitions
    @property
    def Alignment(self):
        """
        Specifies the alignment of the text. (str)
           Left (default)
           Center
           Right
        """
        if self._hasWindowStyleFlag(wx.TE_RIGHT):
            return "Right"
        elif self._hasWindowStyleFlag(wx.TE_CENTRE):
            return "Center"
        else:
            return "Left"

    @Alignment.setter
    def Alignment(self, val):
        if self._constructed():
            # Note: alignment doesn't seem to work, at least on GTK2
            # Second note: setting the Alignment flag seems to change
            # the control to Read-Write if it had previously been set to
            # ReadOnly=True.
            rw = self.IsEditable()
            self._delWindowStyleFlag(wx.TE_LEFT)
            self._delWindowStyleFlag(wx.TE_CENTRE)
            self._delWindowStyleFlag(wx.TE_RIGHT)
            val = val[0].lower()
            if val == "l":
                self._addWindowStyleFlag(wx.TE_LEFT)
            elif val == "c":
                self._addWindowStyleFlag(wx.TE_CENTRE)
            elif val == "r":
                self._addWindowStyleFlag(wx.TE_RIGHT)
            else:
                raise ValueError(_("The only possible values are 'Left', 'Center', and 'Right'"))
            self.SetEditable(rw)
        else:
            self._properties["Alignment"] = val

    @property
    def AutoResizeType(self):
        """
        Determines if a textbox's Width changes to match its content.

        Possible values:
            None (default) - No size changes based on content
            All            - Each change of content resizes the textbox's Width
            Grow           - Only increase the Width if the text doesn't fit
        """
        return self._auto_resize_type

    @AutoResizeType.setter
    def AutoResizeType(self, val):
        if self._constructed():
            if val is None:
                self._auto_resize_type = None
                return
            first_char = val.lower()[0]
            if not first_char in ("a", "g"):
                raise ValueError(
                    f"Invalid AutoResizeType received: '{val}'. Must be one of (None, 'All', or "
                    "'Grow'."
                )
            # pyrefly: ignore  # bad-assignment
            self._auto_resize_type = "All" if first_char == "a" else "Grow"
            self._autosize()
        else:
            self._properties["AutoResizeType"] = val

    @property
    def ForceCase(self):
        """
        Determines if we change the case of entered text. Possible values are:

            ===========  =====================
            None or ""   No changes made (default)
            "Upper"      FORCE TO UPPER CASE
            "Lower"      Force to lower case
            "Title"      Force To Title Case
            ===========  =====================

        These can be abbreviated to "u", "l" or "t"  (str)
        """
        return self._forceCase

    @ForceCase.setter
    def ForceCase(self, val):
        if self._constructed():
            if val is None:
                valKey = None
            else:
                valKey = val[0].upper()
            # pyrefly: ignore  # bad-assignment
            self._forceCase = {
                "U": "upper",
                "L": "lower",
                "T": "title",
                None: None,
                "None": None,
            }.get(valKey)
            self._checkForceCase()
            self.unbindEvent(events.KeyChar, self.__onKeyChar)
            if self._forceCase or self._textLength:
                self.bindEvent(events.KeyChar, self.__onKeyChar)
        else:
            self._properties["ForceCase"] = val

    @property
    def InsertionPosition(self):
        """Position of the insertion point within the control  (int)"""
        return self.GetInsertionPoint()

    @InsertionPosition.setter
    def InsertionPosition(self, val):
        self.SetInsertionPoint(val)

    @property
    def NoneDisplay(self):
        """
        Specifies the string displayed if Value is None  (str or None)

        If None, `self.Application.NoneDisplay` will be used.
        """
        ret = getattr(self, "_noneDisplay", None)
        if ret is None:
            ret = self.Application.NoneDisplay
        return ret

    @NoneDisplay.setter
    def NoneDisplay(self, val):
        # pyrefly: ignore  # implicitly-defined-attribute
        self._noneDisplay = val

    @property
    def ReadOnly(self):
        """Specifies whether or not the text can be edited. (bool)"""
        return not self.IsEditable()

    @ReadOnly.setter
    def ReadOnly(self, val):
        if self._constructed():
            self.SetEditable(not bool(val))
        else:
            self._properties["ReadOnly"] = val

    @property
    def SelectedText(self):
        """Currently selected text. Returns the empty string if nothing is selected  (str)"""
        return self.GetStringSelection()

    @property
    def SelectionEnd(self):
        """
        Position of the end of the selected text. If no text is selected, returns the Position of
        the insertion cursor.  (int)
        """
        return self.GetSelection()[1]

    @SelectionEnd.setter
    def SelectionEnd(self, val):
        start, end = self.GetSelection()
        self.SetSelection(start, val)

    @property
    def SelectionLength(self):
        """Length of the selected text, or 0 if nothing is selected.  (int)"""
        start, end = self.GetSelection()
        return end - start

    @SelectionLength.setter
    def SelectionLength(self, val):
        start = self.GetSelection()[0]
        self.SetSelection(start, start + val)

    @property
    def SelectionStart(self):
        """
        Position of the beginning of the selected text. If no text is selected, returns
        the Position of the insertion cursor.  (int)
        """
        return self.GetSelection()[0]

    @SelectionStart.setter
    def SelectionStart(self, val):
        start, end = self.GetSelection()
        self.SetSelection(val, end)

    @property
    def SelectOnEntry(self):
        """Specifies whether all text gets selected upon receiving focus. (bool)"""
        try:
            return self._SelectOnEntry
        except AttributeError:
            # pyrefly: ignore  # missing-attribute
            ret = not isinstance(self, ui.dEditBox)
            self._SelectOnEntry = ret
            return ret

    @SelectOnEntry.setter
    def SelectOnEntry(self, val):
        # pyrefly: ignore  # implicitly-defined-attribute
        self._SelectOnEntry = bool(val)

    @property
    def TextLength(self):
        """The maximum length the entered text can be. (int)"""
        return self._textLength

    @TextLength.setter
    def TextLength(self, val):
        if self._constructed():
            if val == None:
                self._textLength = None
            else:
                val = int(val)
                if val < 1:
                    raise ValueError(_("TextLength must be a positve Integer"))
                # pyrefly: ignore  # bad-assignment
                self._textLength = val
            self._checkTextLength()

            self.unbindEvent(events.KeyChar, self.__onKeyChar)
            if self._forceCase or self._textLength:
                self.bindEvent(events.KeyChar, self.__onKeyChar)
        else:
            self._properties["TextLength"] = val

    @property
    def Value(self):
        """Specifies the current state of the control (the value of the field). (string)"""
        try:
            _value = self._value
        except AttributeError:
            _value = self._value = ustr("")

        # Get the string value as reported by wx, which is the up-to-date
        # string value of the control:
        strVal = self.GetValue()

        if _value is None:
            if strVal == self.NoneDisplay:
                # Keep the value None
                return None
        return strVal

    @Value.setter
    def Value(self, val):
        if self._constructed():
            setter = self.SetValue
            if hasattr(self, "ChangeValue"):
                setter = self.ChangeValue
            if self._inForceCase:
                # Value is changing internally. Don't update the oldval
                # setting or change the type; just set the value.
                setter(val)
                return
            else:
                ui.callAfter(self._checkForceCase)

            if self._inTextLength:
                # Value is changing internally. Don't update the oldval
                # setting or change the type; just set the value.
                setter(val)
                return
            else:
                ui.callAfter(self._checkTextLength)

            if val is None:
                strVal = self.NoneDisplay
            else:
                strVal = val
            _oldVal = self.Value

            # save the actual value for return by _getValue:
            # pyrefly: ignore  # implicitly-defined-attribute
            self._value = val

            # Update the display no matter what:
            setter(strVal)

            if type(_oldVal) != type(val) or _oldVal != val:
                self._afterValueChanged()
        else:
            self._properties["Value"] = val

    # Dynamic property declarations
    DynamicAlignment = makeDynamicProperty(Alignment)
    DynamicInsertionPosition = makeDynamicProperty(InsertionPosition)
    DynamicReadOnly = makeDynamicProperty(ReadOnly)
    DynamicSelectionEnd = makeDynamicProperty(SelectionEnd)
    DynamicSelectionLength = makeDynamicProperty(SelectionLength)
    DynamicSelectionStart = makeDynamicProperty(SelectionStart)
    DynamicSelectOnEntry = makeDynamicProperty(SelectOnEntry)
    DynamicValue = makeDynamicProperty(Value)


class dTextBoxMixin(dTextBoxMixinBase):
    def __init__(self, preClass, parent, properties=None, attProperties=None, *args, **kwargs):
        self._dregex = {}
        self._lastDataType = str

        dTextBoxMixinBase.__init__(
            self,
            preClass,
            parent,
            # pyrefly: ignore  # bad-keyword-argument
            properties=properties,
            # pyrefly: ignore  # bad-keyword-argument
            attProperties=attProperties,
            *args,
            **kwargs,
        )

        # Keep passwords, etc., from being written to disk
        if self.PasswordEntry:
            self.IsSecret = True

    def convertStringValueToDataType(self, strVal, dataType):
        """
        Given a string value and a type, return an appropriate value of that type.
        If the value can't be converted, a ValueError will be raised.
        """
        if dataType == bool:
            # Bools can't convert from string representations, because a zero-
            # length denotes False, and anything else denotes True.
            if strVal == "True":
                return True
            return False
        elif dataType in (datetime.date, datetime.datetime, datetime.time):
            # We expect the string to be in ISO 8601 format.
            if dataType == datetime.date:
                retVal = self._getDateFromString(strVal)
            elif dataType == datetime.datetime:
                retVal = self._getDateTimeFromString(strVal)
            elif dataType == datetime.time:
                retVal = self._getTimeFromString(strVal)
            if retVal is None:
                raise ValueError(_("String not in ISO 8601 format."))
            return retVal
        elif ustr(dataType) in ("<type 'DateTime'>", "<type 'mx.DateTime.DateTime'>"):
            try:
                # pyrefly: ignore  # import-error
                import mx.DateTime

                return mx.DateTime.DateTimeFrom(ustr(strVal))
            except ImportError:
                raise ValueError(_("Can't import mx.DateTime"))
        elif ustr(dataType) in (
            "<type 'datetime.timedelta'>",
            "<type 'DateTimeDelta'>",
            "<type 'mx.DateTime.DateTimeDelta'>",
        ):
            try:
                # pyrefly: ignore  # import-error
                import mx.DateTime

                return mx.DateTime.TimeFrom(ustr(strVal))
            except ImportError:
                raise ValueError(_("Can't import mx.DateTime"))
        elif (dataType == decimal.Decimal) and self.StrictNumericEntry:
            try:
                _oldVal = self._oldVal
            except AttributeError:
                _oldVal = None
            strVal = strVal.strip()
            if not strVal and self.NumericBlankToZero:
                if type(_oldVal) == decimal.Decimal:
                    # pyrefly: ignore  # bad-argument-type
                    return decimal.DefaultContext.quantize(decimal.Decimal("0"), _oldVal)
                return decimal.Decimal("0")

            try:
                if type(_oldVal) == decimal.Decimal:
                    # Enforce the precision as previously set programatically
                    # pyrefly: ignore  # bad-argument-type
                    return decimal.DefaultContext.quantize(decimal.Decimal(strVal), _oldVal)
                return decimal.Decimal(strVal)
            except (ValueError, decimal.InvalidOperation):
                raise ValueError(_("Invalid decimal value."))
        elif dataType in (tuple, list):
            return eval(strVal)
        elif not self.StrictNumericEntry and (dataType in numericTypes):
            isint = (strVal.count(decimalPoint) == 0) and (strVal.lower().count("e") == 0)
            strVal = strVal.strip()
            if not strVal and self.NumericBlankToZero:
                return 0
            try:
                if isint:
                    if strVal.endswith("L"):
                        return int(strVal)
                    return int(strVal)
                else:
                    try:
                        return decimal.Decimal(strVal.strip())
                    except decimal.InvalidOperation:
                        raise ValueError(_("Invalid decimal value."))
            except valueErrors:
                raise ValueError(_("Invalid Numeric Value: %s") % strVal)
        elif dataType in numericTypes and self.NumericBlankToZero and not strVal.strip():
            # strict:
            if dataType == decimal.Decimal:
                oldVal = getattr(self, "_oldVal", None)
                if type(oldVal) == decimal.Decimal:
                    # pyrefly: ignore  # bad-argument-type
                    return decimal.DefaultContext.quantize("0", oldVal)
                return decimal.Decimal("0")
            return dataType(0)
        else:
            # Other types can convert directly.
            if dataType == str:
                dataType = str
            try:
                return dataType(strVal)
            except ValueError:
                # The Python object couldn't convert it. Our validator, once
                # implemented, won't let the user get this far. Just keep the
                # old value.
                raise ValueError(_("Can't convert."))

    # pyrefly: ignore  # bad-override
    def getStringValue(self, value):
        """
        Given a value of any data type, return a string rendition.

        Used internally by _setValue and flushValue, but also exposed to subclasses
        in case they need specialized behavior. The value returned from this
        function will be what is displayed in the UI textbox.
        """
        if isinstance(value, str):
            # keep it unicode instead of converting to str
            strVal = value
        elif isinstance(value, datetime.datetime):
            strVal = dates.getStringFromDateTime(value)
        elif isinstance(value, datetime.date):
            strVal = dates.getStringFromDate(value)
        elif isinstance(value, datetime.time):
            # Use the ISO 8601 time string format
            strVal = value.isoformat()
        elif value is None:
            strVal = self.NoneDisplay
        else:
            # convert all other data types to string:
            strVal = ustr(value)  # (floats look like 25.55)
            # strVal = repr(value) # (floats look like 25.55000000000001)
        return strVal

    def _getDateFromString(self, strVal):
        """
        Given a string in an accepted date format, return a
        datetime.date object, or None.
        """
        formats = ["ISO8601"]
        if not self.StrictDateEntry:
            # Add some less strict date-entry formats:
            formats.append("YYYYMMDD")
            formats.append("YYMMDD")
            formats.append("MMDD")
            formats.append("MMDDYYYY")
            formats.append("M/DD/YYYY")
            # (define more formats in lib.dates._getDateRegex, and enter
            # them above in more explicit -> less explicit order.)
        return dates.getDateFromString(strVal, formats)

    def _getDateTimeFromString(self, strVal):
        """
        Given a string in ISO 8601 datetime format, return a
        datetime.datetime object.
        """
        formats = ["ISO8601"]
        if not self.StrictDateEntry:
            # Add some less strict date-entry formats:
            formats.append("YYYYMMDDHHMMSS")
            formats.append("YYMMDDHHMMSS")
            formats.append("YYYYMMDD")
            formats.append("YYMMDD")
            # (define more formats in lib.dates._getDateTimeRegex, and enter
            # them above in more explicit -> less explicit order.)
        return dates.getDateTimeFromString(strVal, formats)

    def _getTimeFromString(self, strVal):
        """
        Given a string in ISO 8601 time format, return a
        datetime.time object.
        """
        formats = ["ISO8601"]
        return dates.getTimeFromString(strVal, formats)

    # Property definitions:
    @property
    def NumericBlankToZero(self):
        """
        Specifies whether a blank textbox gets interpreted as 0.

        When True, if the user clears the textbox value, such as by selecting all and pressing the
        space bar or delete, the value will become 0 when the control loses focus.

        When False, the value will revert back to the last numeric value when the control loses
        focus.

        The default comes from dTextBox_NumericBlankToZero, which defaults to False.
        """
        return getattr(self, "_numericBlankToZero", settings.dTextBox_NumericBlankToZero)

    @NumericBlankToZero.setter
    def NumericBlankToZero(self, val):
        # pyrefly: ignore  # implicitly-defined-attribute
        self._numericBlankToZero = bool(val)

    @property
    def PasswordEntry(self):
        """Specifies whether plain-text or asterisks are echoed. (bool)"""
        return self._hasWindowStyleFlag(wx.TE_PASSWORD)

    @PasswordEntry.setter
    def PasswordEntry(self, val):
        self._delWindowStyleFlag(wx.TE_PASSWORD)
        if val:
            self._addWindowStyleFlag(wx.TE_PASSWORD)
            self.IsSecret = True

    @property
    def StrictDateEntry(self):
        """
        Specifies whether date values must be entered in strict ISO8601 format. Default=False.

        If not strict, dates can be accepted in YYYYMMDD, YYMMDD, and MMDD format, which will be
        coerced into sensible date values automatically.
        """
        try:
            ret = self._strictDateEntry
        except AttributeError:
            ret = self._strictDateEntry = False
        return ret

    @StrictDateEntry.setter
    def StrictDateEntry(self, val):
        # pyrefly: ignore  # implicitly-defined-attribute
        self._strictDateEntry = bool(val)

    @property
    def StrictNumericEntry(self):
        """
        When True, the DataType will be preserved across numeric types. When False, the DataType
        will respond to user input to convert to the 'obvious' numeric type. Default=True. (bool)
        """
        try:
            ret = self._strictNumericEntry
        except AttributeError:
            ret = self._strictNumericEntry = True
        return ret

    @StrictNumericEntry.setter
    def StrictNumericEntry(self, val):
        if self._constructed():
            # pyrefly: ignore  # implicitly-defined-attribute
            self._strictNumericEntry = val
        else:
            self._properties["StrictNumericEntry"] = val

    @property
    def Value(self):
        """
        Specifies the current state of the control (the value of the field). (varies)

        Overrides the dTextBoxMixinBase property because of the data conversion introduced
        in this class
        """
        # Return the value as reported by wx, but convert it to the data type as
        # reported by self._value.
        try:
            _value = self._value
        except AttributeError:
            _value = self._value = ustr("")
        dataType = type(_value)

        # Get the string value as reported by wx, which is the up-to-date
        # string value of the control:
        if isinstance(self, masked.TextCtrl) and hasattr(self, "_template"):
            if self.ValueMode == "Unmasked":  # No such property UsePlainValue?
                strVal = self.GetPlainValue()
            else:
                strVal = self.GetValue()
        else:
            try:
                strVal = self.GetValue()
            except RuntimeError:
                # The underlying wx object has been destroyed
                strVal = self._value

        # Convert the current string value of the control, as entered by the
        # user, into the proper data type.
        skipConversion = False
        if _value is None:
            if strVal == self.NoneDisplay:
                # Keep the value None
                convertedVal = None
                skipConversion = True
            else:
                # User changed the None value to something else, convert to the last
                # known real datatype.
                dataType = self._lastDataType

        if not skipConversion:
            # Make sure the underlying wx object still exists
            if self:
                try:
                    convertedVal = self.convertStringValueToDataType(strVal, dataType)
                    if self.getStringValue(convertedVal) != self.GetValue():
                        pass
                        ## pkm, for a long time, we had:
                        ##  self._updateStringDisplay  (without the ())
                        ## and everything seemed to work. Then we added the () in r5431 and
                        ## I started seeing recursion problems. I'm commenting it out but if
                        ## needed, we should experiment with:
                        # ui.callAfter(self._updateStringDisplay)
                except ValueError:
                    # It couldn't convert; return the previous value.
                    convertedVal = self._value
            else:
                # Control has been released; just use the underlying att
                convertedVal = _value

        return convertedVal

    @Value.setter
    def Value(self, val):
        if self._constructed():
            # Must convert all to string for sending to wx, but our internal
            # _value will always retain the correct type.

            # TextCtrls in wxPython since 2.7 have a ChangeValue() method that is to
            # be used instead of the old SetValue().
            setter = self.SetValue
            if hasattr(self, "ChangeValue"):
                setter = self.ChangeValue

            # Todo: set up validators based on the type of data we are editing,
            # so the user can't, for example, enter a letter "p" in a textbox
            # that is currently showing numeric data.

            if self._inForceCase:
                # Value is changing internally. Don't update the oldval
                # setting or change the type; just set the value.
                setter(val)
                return
            else:
                ui.callAfter(self._checkForceCase)

            if self._inTextLength:
                # Value is changing internally. Don't update the oldval
                # setting or change the type; just set the value.
                setter(val)
                return
            else:
                ui.callAfter(self._checkTextLength)

            strVal = self.getStringValue(val)
            _oldVal = self.Value

            # save the actual value for return by _getValue:
            # pyrefly: ignore  # implicitly-defined-attribute
            self._value = val

            if val is not None:
                # Save the type of the value, so that in the case of actual None
                # assignments, we know the datatype to expect.
                self._lastDataType = type(val)

            # Update the display if it is different from what is already displayed
            # (note that if we did it unconditionally, the user's selection could
            # be reset, which isn't very nice):
            if strVal != _oldVal:
                try:
                    setter(strVal)
                except ValueError as e:
                    # PVG: maskedtextedit sometimes fails, on value error..allow the code
                    # to continue
                    uv = ustr(strVal)
                    ue = ustr(e)
                    dabo_module.error(_("Error setting value to '%(uv)s': %(ue)s") % locals())

            if type(_oldVal) != type(val) or _oldVal != val:
                self._afterValueChanged()
        else:
            self._properties["Value"] = val

    # Dynamic property declarations
    DynamicPasswordEntry = makeDynamicProperty(PasswordEntry)
    DynamicStrictDateEntry = makeDynamicProperty(StrictDateEntry)
    DynamicValue = makeDynamicProperty(Value)


# pyrefly: ignore  # missing-attribute
ui.dTextBoxMixinBase = dTextBoxMixinBase
# pyrefly: ignore  # missing-attribute
ui.dTextBoxMixin = dTextBoxMixin
