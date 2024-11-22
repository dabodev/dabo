# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dLed
from dabo.ui import dGridSizer
from dabo.ui import dSpinner
from dabo.ui import dTextBox

dToggleButton = dabo.ui.dToggleButton


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v", DefaultBorder=20, DefaultBorderLeft=True)
        sz.appendSpacer(25)

        btn = dToggleButton(
            self,
            Caption="Toggle Me",
            Name="togg",
            Picture="boolRendererUnchecked",
            DownPicture="boolRendererChecked",
            Width=100,
            Height=100,
        )
        btn.bindEvent(dEvents.Hit, self.onButtonHit)
        sz.append(btn, halign="center")
        sz.appendSpacer(40)

        gs = dGridSizer(MaxCols=2)
        lbl = dLabel(self, Caption="BezelWidth")
        spn = dSpinner(self, Min=0, Max=25, DataSource="self.Parent.togg", DataField="BezelWidth")
        gs.append(lbl, halign="right")
        gs.append(spn)

        lbl = dLabel(self, Caption="Caption")
        txt = dTextBox(self, DataSource="self.Parent.togg", DataField="Caption")
        gs.append(lbl, halign="right")
        gs.append(txt)

        sz.append(gs, halign="center")
        self.update()
        self.layout()

    def onButtonHit(self, evt):
        obj = evt.EventObject
        self.Form.logit(_("Hit; Value=%s") % obj.Value)


category = "Controls.dToggleButton"

overview = """
<p>The <b>dToggleButton</b> class, despite its name, is not for situations that
you might use <b>dButton</b>; instead, it is used like a <b>dCheckbox</b>.
It represents a boolean value: On/Off, True/False, Active/Inactive, etc.</p>

<p>It can display a text <b>Caption</b>, and can also display different images depending on
its state. These are specified in the <b>Picture</b> and <b>DownPicture</b> properties.
You can also affect the control's appearance with its <b>BezelWidth</b> property, which determines
how wide the 3D edge is drawn.
</p>
"""
