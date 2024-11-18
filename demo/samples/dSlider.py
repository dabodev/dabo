# -*- coding: utf-8 -*-
import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dCheckBox
from dabo.ui import dSpinner

dSlider = dabo.ui.dSlider


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v")
        sz.appendSpacer(25)
        self.demoBox = dPanel(self, Height=50, BackColor="orange")
        sz.append(self.demoBox, border=30, borderSides=("Left", "Right"))
        sz.appendSpacer(10)

        self.slider = dSlider(self, Min=0, Max=88, Value=42, ShowLabels=True)
        self.slider.bindEvent(dEvents.Hit, self.onSliderHit)
        sz.append(self.slider, "x", border=30, borderSides=("Left", "Right"))
        sz.appendSpacer(25)

        lbl = dLabel(self, Caption="Min:")
        spn = dSpinner(
            self,
            Max=1000000,
            DataSource=self.slider,
            DataField="Min",
            OnValueChanged=self.updtBox,
        )
        hsz = dSizer("h")
        hsz.append(lbl, valign="middle")
        hsz.append(spn, valign="middle")
        hsz.appendSpacer(40)

        lbl = dLabel(self, Caption="Max:")
        spn = dSpinner(
            self,
            Max=1000000,
            DataSource=self.slider,
            DataField="Max",
            OnValueChanged=self.updtBox,
        )
        hsz.append(lbl, valign="middle")
        hsz.append(spn, valign="middle")
        sz.append(hsz, halign="center")

        sz.appendSpacer(25)
        chk = dCheckBox(
            self,
            Caption="Continuous Update",
            DataSource=self.slider,
            DataField="Continuous",
        )
        sz.append(chk, halign="center")

        self.update()
        dabo.ui.callAfter(self.updtBox)
        self.layout()

    def onSliderHit(self, evt):
        self.Form.logit(_("Hit: Value=%s") % self.slider.Value)
        self.updtBox()

    def updtBox(self, evt=None):
        try:
            self.demoBox
        except Exception:
            # Not yet constructed
            return
        sld = self.slider
        val, smin, smax = sld.Value, float(sld.Min), float(sld.Max)
        pct = (val - smin) / (smax - smin)
        self.demoBox.Width = sld.Width * pct


category = "Controls.dSlider"

overview = """
<p>The <b>dSlider</b> class is a handy UI tool to display a value in relation
to a range of possible values.</p>

<p>You control the range of the slider using the <b>Min</b> and <b>Max</b>
properties, and set its value with the <b>Value</b> property. The slider will then
display its 'thumb control' in a position proportional to its value in relation to the Min and
Max values. Dragging the 'thumb control' changes the Value property, and also generates
a <b>Hit event</b>.</p>

<p>There are two modes for generating Hit events in a slider, and this is controlled
by the <b>Continuous</b> property. When Continuous is False (<i>default</i>), Hit events
are only raised when the thumb control is released. With Continuous set to True, however,
Hit events are generated continuously as the thumb control is dragged.</p>

<p>If the <b>ShowLabels</b> property is True, then the slider will also display
its Min and Max values, as well as its current Value. Please note that this is must be
set when the control is created; it has no effect once the control exists.</p>
"""
