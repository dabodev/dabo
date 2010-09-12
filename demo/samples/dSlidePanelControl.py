# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class TestPanel(dabo.ui.dPanel):
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer('v')

		self.slideControl = dabo.ui.dSlidePanelControl(self, ExpandContent=False, SingleClick=True)
		self.Sizer.append1x(self.slideControl)

		self.slidePanel1 = dabo.ui.dSlidePanel(self.slideControl, Caption="First", BackColor="orange")
		self.slidePanel2 = dabo.ui.dSlidePanel(self.slideControl, Caption="Second", BarStyle="HorizontalFill", BarColor1="lightgreen", BarColor2="ForestGreen", BackColor="wheat")
		self.slidePanel3 = dabo.ui.dSlidePanel(self.slideControl, Caption="Third", BarStyle="BorderOnly", BackColor="powderblue")

		self.slidePanel1.Sizer = sz = dabo.ui.dSizer("v")
		self.slidePanel1.Sizer.append(dabo.ui.dButton(self.slidePanel1, Caption="Change Bar 1 Style", OnHit=self.changeSlidePanel1BarStyle), border=25)

		self.slidePanel2.Sizer = dabo.ui.dSizer("v")
		self.slidePanel2.Sizer.append(dabo.ui.dLabel(self.slidePanel2, Caption="Tea For Two", FontItalic=True, FontSize=24))

		def collapse3(evt):
			mc = self.slideControl
			if mc.Singleton:
				mc.expand(self.slidePanel2)
			else:
				mc.collapse(self.slidePanel3)

		self.slidePanel3.Sizer = dabo.ui.dSizer('v')
		self.slidePanel3.Sizer.appendSpacer(25)
		hs = dabo.ui.dSizer('h')
		hs.appendSpacer(25)
		hs.append(dabo.ui.dLabel(self.slidePanel3, Caption="Three Strikes"), valign="Middle")
		hs.appendSpacer(5)
		hs.append(dabo.ui.dButton(self.slidePanel3, Caption="Collapse Me", OnHit=collapse3))
		self.slidePanel3.Sizer.append(hs)
		self.slidePanel3.Sizer.appendSpacer(25)

		hs = dabo.ui.dSizer("h")
		hs.append(dabo.ui.dButton(self, Caption="Collapse All", OnHit=self.collapseAllPanels))
		hs.appendSpacer(10)
		hs.append(dabo.ui.dButton(self, Caption="Expand All", OnHit=self.expandAllPanels))
		hs.appendSpacer(10)

		vs = dabo.ui.dSizer("v")
		vs.append(dabo.ui.dCheckBox(self, Caption="Singleton Style", DataSource=self.slideControl, DataField="Singleton"))
		vs.append(dabo.ui.dCheckBox(self, Caption="Single Click to Toggle", DataSource=self.slideControl, DataField="SingleClick"))
		vs.append(dabo.ui.dCheckBox(self, Caption="Collapsed Panels To Bottom", DataSource=self.slideControl, DataField="CollapseToBottom"))
		vs.append(dabo.ui.dCheckBox(self, Caption="Expand Content to Full Size", DataSource=self.slideControl, DataField="ExpandContent"))
		hs.append(vs)

		self.Sizer.appendSpacer(10)
		self.Sizer.append(hs, 0, halign="center", border=10)

		self.layout()


	def changeSlidePanel1BarStyle(self, evt):
		import random
		style = random.choice(self.slidePanel1._barStyles)
		self.slidePanel1.BarStyle = style
		color1 = dabo.dColors.randomColorName()
		color2 = dabo.dColors.randomColorName()
		self.slidePanel1.BarColor1 = color1
		self.slidePanel1.BarColor2 = color2

		if style in ("VerticalFill", "HorizontalFill"):
			cap = "Style: %s; Colors: %s, %s" % (style, color1, color2)
		elif style in ("BorderOnly", ):
			cap = "Style: %s" % style
		else:
			cap = "Style: %s; Color: %s" % (style, color1)
		self.Form.logit(cap)


	def collapseAllPanels(self, evt):
		self.slideControl.collapseAll()
		self.Form.logit("Collapsed All Panels")


	def expandAllPanels(self, evt):
		self.slideControl.expandAll()
		self.Form.logit("Expanded All Panels")


category = "Layout.dSlidePanelControl"

overview = """
<p><b>dSlidePanelControl</b> is a control which can maintain a list of collapsable panels.
When a panel is collapsed, the only thing visible to the User is its Caption Bar.
This action is used to provide more space for other panels, which allows the user
to close panels which are not used often to get the most out of the work area.</p>

<p>The control is very to use.  Panels in the control should be instances of Dabo's
dPanel class.  When they are created, simply set the parent of the panel to the
dSlidePanelControl instance and dabo will automatically handle the rest.</p>
"""