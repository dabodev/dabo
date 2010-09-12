# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class TestPanel(dabo.ui.dPanel):
	def afterInit(self):
		sz = self.Sizer = dabo.ui.dSizer("v", DefaultBorder=20,
				DefaultBorderLeft=True)
		sz.appendSpacer(25)

		btn = dabo.ui.dToggleButton(self, Caption="Toggle Me", Name="togg",
				Picture="boolRendererUnchecked", DownPicture="boolRendererChecked",
				Width=100, Height=100)
		btn.bindEvent(dEvents.Hit, self.onButtonHit)
		sz.append(btn, halign="center")
		sz.appendSpacer(40)

		gs = dabo.ui.dGridSizer(MaxCols=2)
		lbl = dabo.ui.dLabel(self, Caption="BezelWidth")
		spn = dabo.ui.dSpinner(self, Min=0, Max=25, DataSource="self.Parent.togg",
				DataField="BezelWidth")
		gs.append(lbl, halign="right")
		gs.append(spn)

		lbl = dabo.ui.dLabel(self, Caption="Caption")
		txt = dabo.ui.dTextBox(self, DataSource="self.Parent.togg",
				DataField="Caption")
		gs.append(lbl, halign="right")
		gs.append(txt)

		sz.append(gs, halign="center")
		self.update()
		self.layout()


	def onButtonHit(self, evt):
		obj = evt.EventObject
		self.Form.logit(_("Hit; Value=%s") % obj.Value )


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
