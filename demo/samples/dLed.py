# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _

dBorderSizer = dabo.import_ui_name("dBorderSizer")
dDropdownList = dabo.import_ui_name("dDropdownList")
dGridSizer = dabo.import_ui_name("dGridSizer")
dLabel = dabo.import_ui_name("dLabel")
dLed = dabo.import_ui_name("dLed")
dPanel = dabo.import_ui_name("dPanel")
dSizer = dabo.import_ui_name("dSizer")
dToggleButton = dabo.import_ui_name("dToggleButton")


class TestPanel(dPanel):
    def afterInit(self):
        self.Sizer = dSizer('v')
        self.Sizer.appendSpacer(50)
        hs = dSizer('h')
        self.Sizer.append(hs)

        self.LED = dLed(self, Height=100, Width=100)
        hs.appendSpacer(50)
        hs.append(self.LED)
        hs.appendSpacer(25)

        bs = dBorderSizer(self, Caption="LED Options", DefaultBorder=5)
        gs = dGridSizer(MaxCols=2, VGap=5, HGap=5)
        gs.setColExpand(1, 0)
        bs.append1x(gs)
        gs.append(dToggleButton(self, Caption="Toggle LED", DataSource=self.LED, DataField="On", Value=True, OnHit=self.toggleLED), "expand", colSpan=2)
        gs.append(dLabel(self, Caption="On Color:"))
        gs.append(dDropdownList(self, Choices=dabo.dColors.colors, DataSource=self.LED, DataField="OnColor", Value="green", OnHit=self.changeOnColor))
        gs.append(dLabel(self, Caption="Off Color:"))
        gs.append(dDropdownList(self, Choices=dabo.dColors.colors, DataSource=self.LED, DataField="OffColor", Value="darkred", OnHit=self.changeOffColor))
        hs.append(bs)

        self.LED.On = True
        self.update()
        self.layout()

    def toggleLED(self, evt):
        self.Form.logit("LED Toggled to %s" % {True:"On", False:"Off"}[self.LED.On])

    def changeOnColor(self, evt):
        self.Form.logit("LED Color when on was changed to %s" % self.LED.OnColor)

    def changeOffColor(self, evt):
        self.Form.logit("LED Color whenn off was changed to %s" % self.LED.OffColor)

category = "Controls.dLed"

overview = _("""
<p>The <b>dLed</b> class is used to display a boolean status.  The control is designed
for displaying read only status, unlike the dCheckBox which is designed to allow
the user to make a boolean choice.  You can change the On and Off colors to suit
your particular applications needs, but the defaults of dark red when off and green
when on should work well enough.</p>
""")
