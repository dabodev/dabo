# -*- coding: utf-8 -*-
import datetime
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class TestPanel(dabo.ui.dPanel):
	def afterInit(self):
		sz = self.Sizer = dabo.ui.dSizer("v")
		sz.appendSpacer(20)

		lbl = dabo.ui.dLabel(self, FontItalic=True,
				WordWrap=True, Caption="Click on the link below to launch the URL in your default browser.")
		lbl.FontSize += 2
		sz.append(lbl, halign="center")
		sz.appendSpacer(5)

		bs = dabo.ui.dBorderSizer(self)
		lnk = self.link = dabo.ui.dHyperLink(self, Caption="The Dabo Wiki", FontSize=24,
				URL="http://wiki.dabodev.com/", LinkColor="olive",
				VisitedColor="maroon", HoverColor="crimson", LinkUnderline=True,
				HoverUnderline=False, VisitedUnderline=True)
		bs.append(lnk, border=20)
		sz.append(bs, halign="center")
		sz.appendSpacer(20)

		bs = dabo.ui.dBorderSizer(self, "v", Caption="Hyperlink Properties",
				DefaultSpacing=8)

		class ColorPropPanel(dabo.ui.dPanel):
			def beforeInit(self):
				self._colorProp = ""

			def afterInit(self):
				hs = self.Sizer = dabo.ui.dSizer("h", DefaultSpacing=4)
				pnl = dabo.ui.dPanel(self, Size=(25,15), BorderWidth=1, BorderColor="black",
						DynamicBackColor=self.getColor)
				lbl = self.lbl = dabo.ui.dLabel(self, Width=100,
						DynamicCaption=lambda:self._colorProp)
				txt = dabo.ui.dTextBox(self, DynamicValue=self.getColor)
				btn = dabo.ui.dButton(self, Width=30, Caption="...", OnHit=self.changeColor)
				hs.append(lbl, valign="middle")
				hs.append(pnl, valign="middle")
				hs.append(txt, valign="middle")
				hs.append(btn, valign="middle")
				self.layout()

			def changeColor(self, evt):
				self.Parent.changeColor(self.ColorProp)

			def getColor(self):
				return self.Parent.getColor(self.ColorProp)

			def _getColorProp(self):
				return self._colorProp

			def _setColorProp(self, val):
				if self._constructed():
					self._colorProp = val
					dabo.ui.callAfter(self.update)
				else:
					self._properties["ColorProp"] = val

			ColorProp = property(_getColorProp, _setColorProp, None,
					_("Name of property managed by this panel  (str)"))
		#--------- end of ColorPropPanel class definition --------------


		lbl = dabo.ui.dLabel(self, Caption="Caption:")
		txt = dabo.ui.dTextBox(self, DataSource=self.link, DataField="Caption",
				ToolTipText="The text that appears in the hyperlink",
				OnValueChanged=self.Parent.layout)
		hs = dabo.ui.dSizer("h")
		hs.append(lbl)
		hs.appendSpacer(3)
		hs.append(txt, 1)
		bs.append(hs, "x")

		lbl = dabo.ui.dLabel(self, Caption="URL:")
		txt = dabo.ui.dTextBox(self, DataSource=self.link, DataField="URL",
				ToolTipText="The address that your browser will open when the link is clicked")
		hs = dabo.ui.dSizer("h")
		hs.append(lbl)
		hs.appendSpacer(3)
		hs.append(txt, 1)
		bs.append(hs, "x")

		pnl = ColorPropPanel(self, ColorProp="LinkColor")
		bs.append(pnl)
		chk = dabo.ui.dCheckBox(self, Caption="LinkUnderline", DataSource=self.link,
				DataField="LinkUnderline")
		bs.append(chk)
		pnl = ColorPropPanel(self, ColorProp="VisitedColor")
		bs.append(pnl)
		chk = dabo.ui.dCheckBox(self, Caption="VisitedUnderline", DataSource=self.link,
				DataField="VisitedUnderline")
		bs.append(chk)
		pnl = ColorPropPanel(self, ColorProp="HoverColor")
		bs.append(pnl)
		chk = dabo.ui.dCheckBox(self, Caption="HoverUnderline", DataSource=self.link,
				DataField="HoverUnderline")
		bs.append(chk)
		sz.append(bs, halign="center")
		sz.appendSpacer(5)

		self.Form.update()
		self.layout()
		self.refresh()

	def changeColor(self, prop):
		color = self.getColor(prop)
		newColor = dabo.ui.getColor(color)
		if newColor:
			self.link.__setattr__(prop, newColor)
			self.update()

	def getColor(self, prop):
		return self.link.__getattribute__(prop)


category = "Controls.dHyperLink"

overview = """
<b>dHyperLink</b> creates a text link that, when clicked, launches the
specified URL in the user's default browser (if the <b>ShowInBrowser</b> property
is True), or raises a Hit event for your code to respond to (if the <b>ShowInBrowser</b>
property is False). You can control the appearance of the link through its various properties.
"""
