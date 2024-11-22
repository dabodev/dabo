# -*- coding: utf-8 -*-
import wx

from .. import dColors
from .. import ui
from ..dLocalize import _
from . import dDataPanel


class dLed(dDataPanel):
    def __init__(self, *args, **kwargs):
        self._offColor = "darkred"
        self._onColor = "green"
        self._on = False
        self._inUpdate = False
        super(dLed, self).__init__(*args, **kwargs)

    def _afterInit(self):
        self._baseClass = dLed
        self.led = self.drawCircle(1, 1, 1)
        self.led.DynamicXpos = lambda: self.Width / 2
        self.led.DynamicYpos = lambda: self.Height / 2
        self.led.DynamicRadius = lambda: min(self.Width, self.Height) / 2
        self.led.DynamicFillColor = lambda: self.Color
        super(dLed, self)._afterInit()
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
        super(dLed, self).update()
        self._inUpdate = False

    # Getters and Setters
    def _getColor(self):
        if self._on:
            return self._onColor
        else:
            return self._offColor

    def _getOffColor(self):
        return self._offColor

    def _setOffColor(self, val):
        if self._constructed():
            self._offColor = val
            self.update()
        else:
            self._properties["OffColor"] = val

    def _getOn(self):
        return self._on

    def _setOn(self, val):
        if self._constructed():
            self._on = val
            self.update()
        else:
            self._properties["On"] = val

    def _getOnColor(self):
        return self._onColor

    def _setOnColor(self, val):
        if self._constructed():
            self._onColor = val
            self.update()
        else:
            self._properties["OnColor"] = val

    # Property Definitions
    Color = property(_getColor, None, None, _("The current color of the LED (color)"))

    OffColor = property(
        _getOffColor,
        _setOffColor,
        None,
        _("The color of the LED when it is off.  (color)"),
    )

    On = property(_getOn, _setOn, None, _("Is the LED is on? Default=False  (bool)"))

    OnColor = property(
        _getOnColor,
        _setOnColor,
        None,
        _("The color of the LED when it is on.  (color)"),
    )

    # To make this data-aware, we need a Value property. However,
    # we already have the 'On' property that does the exact same thing.
    Value = On


ui.dLed = dLed


if __name__ == "__main__":
    from .. import dApp
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
                Choices=dColors.colors,
                DataSource=self.LED,
                DataField="OnColor",
                Value="mediumseagreen",
            )
            vs.append(dd)
            vs.appendSpacer(12)
            vs.append(dLabel(mp, Caption="Off Color:"))
            dd = dDropdownList(
                mp,
                Choices=dColors.colors,
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
