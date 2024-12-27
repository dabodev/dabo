# -*- coding: utf-8 -*-
import wx

from .. import color_tools, ui
from ..localization import _
from . import dDataPanel


class dLed(dDataPanel):
    def __init__(self, *args, **kwargs):
        self._offColor = "darkred"
        self._onColor = "green"
        self._on = False
        self._inUpdate = False
        super().__init__(*args, **kwargs)

    def _afterInit(self):
        self._baseClass = dLed
        self.led = self.drawCircle(1, 1, 1)
        self.led.DynamicXpos = lambda: self.Width / 2
        self.led.DynamicYpos = lambda: self.Height / 2
        self.led.DynamicRadius = lambda: min(self.Width, self.Height) / 2
        self.led.DynamicFillColor = lambda: self.Color
        super()._afterInit()
        self.layout(resetMin=True)
        self.update()

    def onResize(self, evt):
        """Update the size of the LED."""
        self.update()

    def update(self):
        # Avoid recursive calls to this method.
        if self._inUpdate:
            return
        self._inUpdate = True
        super().update()
        self._inUpdate = False

    # Property Definitions
    @property
    def Color(self):
        """The current color of the LED (color)"""
        if self._on:
            return self._onColor
        else:
            return self._offColor

    @property
    def OffColor(self):
        """The color of the LED when it is off.  (color)"""
        return self._offColor

    @OffColor.setter
    def OffColor(self, val):
        if self._constructed():
            self._offColor = val
            self.update()
        else:
            self._properties["OffColor"] = val

    @property
    def On(self):
        """Is the LED is on? Default=False  (bool)"""
        return self._on

    @On.setter
    def On(self, val):
        if self._constructed():
            self._on = val
            self.update()
        else:
            self._properties["On"] = val

    @property
    def OnColor(self):
        """The color of the LED when it is on.  (color)"""
        return self._onColor

    @OnColor.setter
    def OnColor(self, val):
        if self._constructed():
            self._onColor = val
            self.update()
        else:
            self._properties["OnColor"] = val

    # To make this data-aware, we need a Value property. However,
    # we already have the 'On' property that does the exact same thing.
    Value = On


ui.dLed = dLed


if __name__ == "__main__":
    from ..application import dApp
    from ..ui import dDropdownList, dForm, dLabel, dPanel, dSizer, dToggleButton

    class TestForm(dForm):
        def afterInit(self):
            mp = dPanel(self)
            self.Sizer.append1x(mp)
            mp.Sizer = dSizer("h")
            mp.Sizer.append1x(dLed(mp, RegID="LED"))

            vs = dSizer("v", DefaultBorder=20)
            vs.appendSpacer(20)
            vs.DefaultBorderLeft = vs.DefaultBorderRight = True
            btn = dToggleButton(
                mp,
                Caption="Toggle LED",
                DataSource=self.LED,
                DataField="On",
                Value=False,
            )
            vs.append(btn)
            vs.appendSpacer(12)
            vs.append(dLabel(mp, Caption="On Color:"))
            dd = dDropdownList(
                mp,
                Choices=color_tools.colors,
                DataSource=self.LED,
                DataField="OnColor",
                Value="mediumseagreen",
            )
            vs.append(dd)
            vs.appendSpacer(12)
            vs.append(dLabel(mp, Caption="Off Color:"))
            dd = dDropdownList(
                mp,
                Choices=color_tools.colors,
                DataSource=self.LED,
                DataField="OffColor",
                Value="orangered",
            )
            vs.append(dd)
            mp.Sizer.append(vs)

            self.LED.On = True
            self.update()

    app = dApp()
    app.MainFormClass = TestForm
    app.start()
