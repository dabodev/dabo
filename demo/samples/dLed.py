# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class TestPanel(dabo.ui.dPanel):
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer('v')
		self.Sizer.appendSpacer(50)
		hs = dabo.ui.dSizer('h')
		self.Sizer.append(hs)

		self.LED = dabo.ui.dLed(self, Height=100, Width=100)
		hs.appendSpacer(50)
		hs.append(self.LED)
		hs.appendSpacer(25)

		bs = dabo.ui.dBorderSizer(self, Caption="LED Options", DefaultBorder=5)
		gs = dabo.ui.dGridSizer(MaxCols=2, VGap=5, HGap=5)
		gs.setColExpand(1, 1)
		bs.append1x(gs)
		gs.append(dabo.ui.dToggleButton(self, Caption="Toggle LED", DataSource=self.LED, DataField="On", Value=True, OnHit=self.toggleLED), "expand", colSpan=2)
		gs.append(dabo.ui.dLabel(self, Caption="On Color:"))
		gs.append(dabo.ui.dDropdownList(self, Choices=dabo.dColors.colors, DataSource=self.LED, DataField="OnColor", Value="green", OnHit=self.changeOnColor))
		gs.append(dabo.ui.dLabel(self, Caption="Off Color:"))
		gs.append(dabo.ui.dDropdownList(self, Choices=dabo.dColors.colors, DataSource=self.LED, DataField="OffColor", Value="darkred", OnHit=self.changeOffColor))
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
