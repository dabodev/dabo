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

		chk = dabo.ui.dCheckBox(self, Caption="Left-Aligned Check Box",
			Alignment="Left", Name="LeftCheck")
		chk.bindEvent(dEvents.Hit, self.onCheckHit)
		sz.append(chk, halign="center")
		sz.appendSpacer(10)

		chk = dabo.ui.dCheckBox(self, Caption="Right-Aligned Check Box",
			Alignment="Right", Name="RightCheck")
		chk.bindEvent(dEvents.Hit, self.onCheckHit)
		sz.append(chk, halign="center")
		if self.Application.Platform == "Mac":
			sz.append(dabo.ui.dLabel(self, FontSize=8, FontItalic=True,
					Caption="(currently not supported on the Mac)"), halign="center")
		sz.appendSpacer(10)

		chk = dabo.ui.dCheckBox(self, Caption="Three State Check Box",
			Alignment="Left", ThreeState=True, UserThreeState=True,
			Name="3Check")
		chk.bindEvent(dEvents.Hit, self.onCheckHit)
		sz.append(chk, halign="center")
		sz.appendSpacer(10)


	def onCheckHit(self, evt):
		obj = evt.EventObject
		nm, val = obj.Name, obj.Value
		self.Form.logit(_("Hit: %(nm)s; Value=%(val)s") % locals())


category = "Controls.dCheckBox"

overview = """
<p>The <b>dCheckBox</b> class is used to indicate boolean values: yes/no,
enabled/disabled, True/False, etc. It has its own Caption property,
which means you commonly don't need a separate dLabel control to
let your users know what it represents. You can use the Alignment
property to control whether the box appears to the left of the Caption
(default), or on the right. (Right-alignment currently does not work
under OS X).</p>

<p>Checkboxes also optionally support three-state operation, which
corresponds to Yes/No/Unknown, or True/False/None.</p>

<p>Clicking the control to change its value raises a <b>Hit</b> event, which
you can trap and handle as needed.</p>
"""
