# -*- coding: utf-8 -*-
import wx

from .. import events, ui
from ..dLocalize import _
from . import dControlMixin, makeDynamicProperty


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

    def _initEvents(self):
        super(dGauge, self)._initEvents()

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
