# -*- coding: utf-8 -*-
import random

import dabo
import dabo.ui
from dabo.dApp import dApp
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dBorderSizer

dGauge = dabo.ui.dGauge


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v")
        sz.appendSpacer(25)

        bsz = dBorderSizer(self, "v", Caption="Horizontal Gauge")
        self.gaugeH = dGauge(self)
        bsz.append(self.gaugeH, "x", border=30, borderSides=("Left", "Right"))

        self.lblH = dLabel(self)
        bsz.append(self.lblH, halign="center")
        sz.append(bsz, "x", halign="center", border=20, borderSides=("Left", "Right"))
        sz.appendSpacer(50)

        hsz = dBorderSizer(self, "h", Caption="Vertical Gauge")
        self.gaugeV = dGauge(self, Orientation="v")
        hsz.append(self.gaugeV, "x", border=30, borderSides=("Left", "Right"), halign="center")
        hsz.appendSpacer(10)

        self.lblV = dLabel(self)
        hsz.append(self.lblV, valign="middle")
        sz.append(hsz, 1, halign="center")

        self.tmr = dabo.ui.callEvery(500, self.updateGauges)
        self.update()
        self.layout()

    @dabo.ui.deadCheck
    def updateGauges(self):
        increase = random.randrange(3, 10)
        gh = self.gaugeH
        val = gh.Value + increase
        if val > gh.Range:
            val -= gh.Range
        gh.Value = val
        self.lblH.Caption = "%s%% complete" % int(gh.Percentage)

        increase = random.randrange(3, 10)
        gv = self.gaugeV
        val = gv.Value + increase
        if val > gv.Range:
            val -= gv.Range
        gv.Value = val
        self.lblV.Caption = "%s%% complete" % int(gv.Percentage)
        self.layout()

    def onDestroy(self, evt):
        self.tmr.stop()


category = "Controls.dGauge"

overview = """
<p>A <b>dGauge</b> is a horizontal or vertical bar which shows a quantity in a graphical
fashion. It is often used to indicate progress through lengthy tasks, such as file copying or
data analysis.</p>

<p>You set the Range property of dGauge to set the 'total' for the task, and then update it
by setting the <b>Value</b> property to the current value; the gauge then updates to
reflect the percentage of the total for that value. You can alternately set the <b>Percentage</b>
property, and the appropriate Value for that Percentage will be set.</p>

<p>Gauges do not raise any events, or respond to user interaction. They are simply a convenient way to display the progress of a task or process.</p>
"""

if __name__ == "__main__":
    app = dApp(MainFormClass=None)
    app.setup()
    frm = dabo.ui.dForm()
    pan = TestPanel(frm)
    frm.Sizer.append1x(pan)
    frm.show()
    app.start()
