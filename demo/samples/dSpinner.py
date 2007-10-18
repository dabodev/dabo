# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class TestPanel(dabo.ui.dPanel):
	def afterInit(self):
		sz = self.Sizer = dabo.ui.dSizer("v")
		
		lbl = dabo.ui.dLabel(self, Alignment="Center", WordWrap=True, Width=400,
				Caption=_("Both of these spinners have a range from 0 to 10. The only "
						"difference is that the top spinner has its SpinnerWrap property set to "
						"True, which cycles it around when it reaches one of its limits."))
				
		lbl.FontSize += 3
		lbl.ForeColor = "darkBlue"
		sz.appendSpacer(25)
		sz.append(lbl, halign="center")
		sz.appendSpacer(10)
		
		lbl = dabo.ui.dLabel(self, Caption=_("Spinner with wrapping"))
		spn = dabo.ui.dSpinner(self, Value=5, Max=10,
				Min=0, SpinnerWrap=True, Name="wrapSpinner")
		spn.bindEvent(dEvents.Hit, self.onSpinnerHit)
		sz.append(lbl, halign="center")
		sz.append(spn, halign="center")
		sz.appendSpacer(20)

		lbl = dabo.ui.dLabel(self, Caption=_("Spinner without wrapping"))
		spn = dabo.ui.dSpinner(self, Value=5, Max=10,
				Min=0, SpinnerWrap=False, Name="nowrapSpinner")
		spn.bindEvent(dEvents.Hit, self.onSpinnerHit)
		sz.append(lbl, halign="center")
		sz.append(spn, halign="center")
		
	def onSpinnerHit(self, evt):
		obj = evt.EventObject
		self.Form.logit("%s Hit; Value=%s" % (obj.Name, obj.Value))



category = "Controls.dSpinner"

overview = """
<p>The <b>dSpinner</b> class is optimal for displaying integer values that vary
within a moderate range. The value can be changed by editing the text 
portion of the control, or by clicking the up/down arrows to increase or
decrease the value.</p>

<p>Besides changing the value, clicking the buttons fires the spinner's 
<b>Hit</b> event, which you can trap and respond to in your code.</p>
"""
