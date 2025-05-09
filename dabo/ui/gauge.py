# -*- coding: utf-8 -*-
import wx

from .. import events
from .. import ui
from ..localization import _
from . import dControlMixin
from . import makeDynamicProperty


class dGauge(dControlMixin, wx.Gauge):
    """Creates a gauge, which can be used as a progress bar."""

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dGauge
        preClass = wx.Gauge
        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )
        self._pulsing = False
        self._last_value = 0

    def _initEvents(self):
        super()._initEvents()

    # Property definitions:
    @property
    def Orientation(self):
        """Specifies whether the gauge is displayed as Horizontal or Vertical.  (str)"""
        if self.IsVertical():
            return "Vertical"
        else:
            return "Horizontal"

    @Orientation.setter
    def Orientation(self, value):
        self._delWindowStyleFlag(wx.GA_HORIZONTAL)
        self._delWindowStyleFlag(wx.GA_VERTICAL)
        if value.lower()[:1] == "h":
            self._addWindowStyleFlag(wx.GA_HORIZONTAL)
        else:
            self._addWindowStyleFlag(wx.GA_VERTICAL)

    @property
    def Percentage(self):
        """Alternate way of setting/getting the Value, using percentage of the Range.  (float)"""
        return round(100 * (float(self.Value) / self.Range), 2)

    @Percentage.setter
    def Percentage(self, val):
        if self._constructed():
            self.Value = round(self.Range * (val / 100.0))
        else:
            self._properties["Percentage"] = val

    @property
    def Pulsing(self):
        """
        Determines if the gauge uses its Value to form a full line, or if the gauge just shows a
        pulsing display. Default=False  (bool)
        """
        return self._pulsing

    @Pulsing.setter
    def Pulsing(self, val):
        if not self._pulsing:
            # GetValue() is undefined when pulsing, so store the previous value
            self._last_value = self.Value
        self._pulsing = bool(val)
        if self._pulsing:
            self.Pulse()
        else:
            # Stop the pulsing be explicitly setting the value
            self.SetValue(self._last_value)

    @property
    def Range(self):
        """Specifies the maximum value for the gauge.  (int)"""
        return self.GetRange()

    @Range.setter
    def Range(self, value):
        if self._constructed():
            self.SetRange(value)
        else:
            self._properties["Range"] = value

    @property
    def Value(self):
        """Specifies the state of the gauge, relative to max value."""
        if self._pulsing:
            # GetValue() is indeterminate when pulsing
            return self._last_value
        return self.GetValue()

    @Value.setter
    def Value(self, value):
        if self._constructed():
            self.SetValue(value)
        else:
            self._properties["Value"] = value

    DynamicOrientation = makeDynamicProperty(Orientation)
    DynamicRange = makeDynamicProperty(Range)
    DynamicValue = makeDynamicProperty(Value)


ui.dGauge = dGauge


class _dGauge_test(dGauge):
    def afterInit(self):
        self._timer = ui.dTimer()
        self._timer.bindEvent(events.Hit, self.onTimer)
        self._timer.Interval = 23
        self._timer.start()

    def initProperties(self):
        self.Range = 1000
        self.Value = 0
        self.Height = 300
        self.Orientation = "Vertical"

    def onTimer(self, evt):
        if not self:
            return
        if self.Value < self.Range:
            self.Value += 1
        else:
            self._timer.stop()
            self.Value = 0
            self._timer.start()


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dGauge_test)
