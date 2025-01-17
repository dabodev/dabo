# -*- coding: utf-8 -*-
import datetime
import re

import wx

from .. import ui
from .text_box_mixin import dTextBoxMixin


class dTextBox(dTextBoxMixin, wx.TextCtrl):
    """Creates a text box for editing one line of string data."""

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dTextBox
        preClass = wx.TextCtrl

        dTextBoxMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )


ui.dTextBox = dTextBox


if __name__ == "__main__":
    import datetime

    from . import test

    # This test sets up several textboxes, each editing different data types.
    class TestBase(dTextBox):
        def initProperties(self):
            self.SelectOnEntry = True
            super().initProperties()
            self.LogEvents = [
                "ValueChanged",
            ]

        def onValueChanged(self, evt):
            if self.IsSecret:
                print("%s changed, but the new value is a secret! " % self.Name)
            else:
                print("%s.onValueChanged:" % self.Name, self.Value, type(self.Value))

    class IntText(TestBase):
        def afterInit(self):
            self.Value = 23

    class LongText(TestBase):
        def afterInit(self):
            self.Value = int(23)

    class FloatText(TestBase):
        def afterInit(self):
            self.Value = 23.5

    class BoolText(TestBase):
        def afterInit(self):
            self.Value = False

    class StrText(TestBase):
        def afterInit(self):
            self.Value = "Lunchtime"

    class PWText(TestBase):
        def __init__(self, *args, **kwargs):
            kwargs["PasswordEntry"] = True
            super().__init__(*args, **kwargs)

        def afterInit(self):
            self.Value = "TopSecret!"

    class DateText(TestBase):
        def afterInit(self):
            self.Value = datetime.date.today()

    class DateTimeText(TestBase):
        def afterInit(self):
            self.Value = datetime.datetime.now()

    testParms = [
        IntText,
        LongText,
        FloatText,
        StrText,
        PWText,
        BoolText,
        DateText,
        DateTimeText,
    ]

    try:
        import mx.DateTime

        class MxDateTimeText(TestBase):
            def afterInit(self):
                self.Value = mx.DateTime.now()

        testParms.append(MxDateTimeText)
    except ImportError:
        # skip it: mx may not be available
        pass

    import decimal

    class DecimalText(TestBase):
        def afterInit(self):
            self.Value = decimal.Decimal("23.42")

    testParms.append(DecimalText)

    test.Test().runTest(testParms)
