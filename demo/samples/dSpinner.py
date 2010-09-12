# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class TestPanel(dabo.ui.dPanel):
	def afterInit(self):
		sz = self.Sizer = dabo.ui.dSizer("v")
		sz.appendSpacer(50)
		spn = self.spinner = dabo.ui.dSpinner(self, Max=25, Min=0, Value=4.75,
				Increment=1.25, SpinnerWrap=False, FontSize=12, Width=100)
		spn.bindEvent(dEvents.Hit, self.onSpinnerHit)
		spn.bindEvent(dEvents.SpinUp, self.onSpinUp)
		spn.bindEvent(dEvents.SpinDown, self.onSpinDown)
		spn.bindEvent(dEvents.Spinner, self.onSpinner)
		sz.append(spn, halign="center")

		lbl = dabo.ui.dLabel(self, Caption=_("Spinner Properties"), FontSize=18,
				FontBold=True)
		sz.appendSpacer(10)
		sz.append(lbl, halign="center")
		sz.appendSpacer(4)

		gsz = dabo.ui.dGridSizer(MaxCols=2, HGap=4, VGap=6)
		lbl = dabo.ui.dLabel(self, Caption="Min")
		txt = dabo.ui.dTextBox(self, DataSource=spn, DataField="Min", StrictNumericEntry=False)
		gsz.append(lbl, halign="right")
		gsz.append(txt)
		lbl = dabo.ui.dLabel(self, Caption="Max")
		txt = dabo.ui.dTextBox(self, DataSource=spn, DataField="Max", StrictNumericEntry=False)
		gsz.append(lbl, halign="right")
		gsz.append(txt)
		lbl = dabo.ui.dLabel(self, Caption="Increment")
		txt = dabo.ui.dTextBox(self, DataSource=spn, DataField="Increment", StrictNumericEntry=False)
		gsz.append(lbl, halign="right")
		gsz.append(txt)
		lbl = dabo.ui.dLabel(self, Caption="SpinnerWrap")
		chk = dabo.ui.dCheckBox(self, DataSource=spn, DataField="SpinnerWrap")
		gsz.append(lbl, halign="right")
		gsz.append(chk)
		lbl = dabo.ui.dLabel(self, Caption="FontSize")
		txt = dabo.ui.dTextBox(self, DataSource=spn, DataField="FontSize")
		gsz.append(lbl, halign="right")
		gsz.append(txt)
		lbl = dabo.ui.dLabel(self, Caption="Height")
		txt = dabo.ui.dTextBox(self, DataSource=spn, DataField="Height")
		gsz.append(lbl, halign="right")
		gsz.append(txt)
		lbl = dabo.ui.dLabel(self, Caption="ForeColor")
		txt = dabo.ui.dTextBox(self, ReadOnly=True, DataSource=spn, DataField="ForeColor")
		btn = dabo.ui.dButton(self, Caption="...", OnHit=self.onForeColor, Width=36)
		hsz = dabo.ui.dSizer("h")
		hsz.append(txt, 1)
		hsz.append(btn)
		gsz.append(lbl, halign="right")
		gsz.append(hsz)
		lbl = dabo.ui.dLabel(self, Caption="BackColor")
		txt = dabo.ui.dTextBox(self, ReadOnly=True, DataSource=spn, DataField="BackColor")
		btn = dabo.ui.dButton(self, Caption="...", OnHit=self.onBackColor, Width=36)
		hsz = dabo.ui.dSizer("h")
		hsz.append(txt, 1)
		hsz.append(btn)
		gsz.append(lbl, halign="right")
		gsz.append(hsz)
		lbl = dabo.ui.dLabel(self, Caption="Enabled")
		chk = dabo.ui.dCheckBox(self, DataSource=spn, DataField="Enabled")
		gsz.append(lbl, halign="right")
		gsz.append(chk)
		sz.append(gsz, halign="center")
		self.update()
		self.layout()


	def onBackColor(self, evt):
		color = dabo.ui.getColor(self.spinner.BackColor)
		if color is not None:
			self.spinner.BackColor = color
			self.update()

	def onForeColor(self, evt):
		color = dabo.ui.getColor(self.spinner.ForeColor)
		if color is not None:
			self.spinner.ForeColor = color
			self.update()
		self.layout()

	def onSpinnerHit(self, evt):
		obj = evt.EventObject
		self.Form.logit("Hit! (%s); Value=%s" % (evt.hitType, obj.Value))

	def onSpinUp(self, evt):
		self.Form.logit("Spin up event.")

	def onSpinDown(self, evt):
		self.Form.logit("Spin down event.")

	def onSpinner(self, evt):
		self.Form.logit("Spinner event.")



category = "Controls.dSpinner"

overview = """
<p>The <b>dSpinner</b> class is optimal for displaying integer values that vary
within a moderate range. The value can be changed by editing the text
portion of the control, or by clicking the up/down arrows to increase or
decrease the value.</p>

<p>Besides changing the value, clicking the buttons fires the spinner's
<b>Hit</b> event, which you can trap and respond to in your code.</p>
"""
