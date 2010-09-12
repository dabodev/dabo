# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.lib.utils import ustr


class TestPanel(dabo.ui.dPanel):
	def afterInit(self):
		sz = self.Sizer = dabo.ui.dSizer("v")
		sz.appendSpacer(25)
		bail = False
		try:
			self.pgf = pgf = dabo.ui.dPageStyled(self, ActiveTabColor="powderblue",
					ActiveTabTextColor="black", InactiveTabTextColor="black",
					TabAreaColor="thistle", OnPageChanged=self.onPageChanged)
		except AttributeError, e:
			bail = True
		if bail:
			lbl = dabo.ui.dLabel(self, FontSize=18, ForeColor="darkred",
					Caption=_("dPageStyled is not supported in your version of wxPython"))
			sz.append(lbl)
			return
		page0 = pgf.appendPage(caption="First", BackColor="gray")
		page1 = pgf.appendPage(caption="Second", BackColor="salmon")
		page2 = pgf.appendPage(caption="Third", BackColor="darkblue")
		page3 = pgf.appendPage(caption="Fourth", BackColor="green")
		sz.append1x(pgf, border=20)

		hsz = dabo.ui.dSizer("h")
		gsz = dabo.ui.dGridSizer(HGap=3, VGap=8)
		lbl = dabo.ui.dLabel(self, Caption="Tab Style:")
		ddStyle = dabo.ui.dDropdownList(self, Choices=["Default", "VC8", "VC71", "Fancy", "Firefox"],
				DataSource=pgf, DataField="TabStyle", OnHit=self.onStyle)
		gsz.append(lbl, row=0, col=0, halign="right")
		gsz.append(ddStyle, row=0, col=1)

		lbl = dabo.ui.dLabel(self, Caption="Tab Position:")
		ddPos = dabo.ui.dDropdownList(self, Choices=["Top", "Bottom"],
				DataSource=pgf, DataField="TabPosition")
		gsz.append(lbl, row=1, col=0, halign="right")
		gsz.append(ddPos, row=1, col=1)

		lbl = dabo.ui.dLabel(self, Caption="Tab Side Incline:",
				DynamicVisible=lambda:pgf.TabStyle=="Default")
		ddPos = dabo.ui.dSpinner(self, Min=0, Max=15,
				DynamicVisible=lambda:pgf.TabStyle=="Default",
				DataSource=pgf, DataField="TabSideIncline")
		gsz.append(lbl, row=2, col=0, halign="right")
		gsz.append(ddPos, row=2, col=1)

		hsz.append(gsz, valign="middle")
		hsz.appendSpacer(30)

		vsz = dabo.ui.dBorderSizer(self, "v", Caption="Options")
		chkDD = dabo.ui.dCheckBox(self, Caption="ShowDropdownTabList",
				DataSource=pgf, DataField="ShowDropdownTabList")
		chkMC = dabo.ui.dCheckBox(self, Caption="ShowMenuCloseButton",
				DataSource=pgf, DataField="ShowMenuCloseButton")
		chkNB = dabo.ui.dCheckBox(self, Caption="ShowNavButtons",
				DataSource=pgf, DataField="ShowNavButtons")
		chkPC = dabo.ui.dCheckBox(self, Caption="ShowPageCloseButtons",
				DataSource=pgf, DataField="ShowPageCloseButtons")
		vsz.append(chkDD)
		vsz.append(chkMC)
		vsz.append(chkNB)
		vsz.append(chkPC)
		hsz.append(vsz)
		sz.append(hsz, halign="center")
		sz.appendSpacer(8)

		bsz = dabo.ui.dBorderSizer(self, "h", Caption="Color Settings (click a box to set the color)")
		hsz = dabo.ui.dSizer("h")
		lblATC = dabo.ui.dLabel(self, Caption="ActiveTabColor:")
		pnlATC = dabo.ui.dPanel(self, BorderWidth=2, BorderColor="black", BorderStyle="Simple",
				Size=(20, 20), DynamicBackColor=lambda:self.pgf.ActiveTabColor, Name="foo",
				OnMouseLeftClick=self.onSetActiveTabColor)
		hsz.append(lblATC)
		hsz.appendSpacer(2)
		hsz.append(pnlATC)
		hsz.appendSpacer(20)

		lblTAC = dabo.ui.dLabel(self, Caption="TabAreaColor:")
		pnlTAC = dabo.ui.dPanel(self, BorderWidth=2, BorderColor="black", BorderStyle="Simple",
				Size=(20, 20), DynamicBackColor=lambda:self.pgf.TabAreaColor,
				OnMouseLeftClick=self.onSetTabAreaColor)
		hsz.append(lblTAC)
		hsz.appendSpacer(2)
		hsz.append(pnlTAC)
		hsz.appendSpacer(20)

		lblATTC = dabo.ui.dLabel(self, Caption="ActiveTabTextColor:")
		pnlITC = dabo.ui.dPanel(self, BorderWidth=2, BorderColor="black", BorderStyle="Simple",
				Size=(20, 20), DynamicBackColor=lambda:self.pgf.ActiveTabTextColor,
				OnMouseLeftClick=self.onSetActiveTabTextColor)
		sz.appendSpacer(8)
		hsz.append(lblATTC)
		hsz.appendSpacer(4)
		hsz.append(pnlITC)
		hsz.appendSpacer(20)

		lblITC = dabo.ui.dLabel(self, Caption="InactiveTabTextColor:")
		pnlITC = dabo.ui.dPanel(self, BorderWidth=2, BorderColor="black", BorderStyle="Simple",
				Size=(20, 20), DynamicBackColor=lambda:self.pgf.InactiveTabTextColor,
				OnMouseLeftClick=self.onSetInactiveTabTextColor)
		hsz.append(lblITC)
		hsz.appendSpacer(4)
		hsz.append(pnlITC)

		bsz.append(hsz, halign="center")
		sz.append(bsz, halign="center")
		sz.appendSpacer(12)


	def onPageChanged(self, evt):
		self.Form.logit("Page number changed from %s to %s" % (evt.oldPageNum, evt.newPageNum))

	def onStyle(self, evt):
		self.update()
		self.Form.logit("Style changed to '%s'" % evt.EventObject.StringValue)

	def getColorName(self, curr):
		ret = dabo.ui.getColor(curr)
		try:
			nm = dabo.dColors.colorNameFromTuple(ret, firstOnly=True)
			if nm:
				ret = nm
		except ValueError:
			# An invalid RGB 3-tuple was returned
			pass
		return ret

	def onSetActiveTabColor(self, evt):
		curr = self.pgf.ActiveTabColor
		newcolor = self.getColorName(curr)
		if newcolor:
			self.pgf.ActiveTabColor = newcolor
			self.update()
			self.Form.logit("ActiveTabColor changed to '%s'" % ustr(newcolor))

	def onSetTabAreaColor(self, evt):
		curr = self.pgf.TabAreaColor
		newcolor = self.getColorName(curr)
		if newcolor:
			self.pgf.TabAreaColor = newcolor
			self.update()
			self.Form.logit("TabAreaColor changed to '%s'" % ustr(newcolor))

	def onSetActiveTabTextColor(self, evt):
		curr = self.pgf.ActiveTabTextColor
		newcolor = self.getColorName(curr)
		if newcolor:
			self.pgf.ActiveTabTextColor = newcolor
			self.update()
			self.Form.logit("ActiveTabTextColor changed to '%s'" % ustr(newcolor))

	def onSetInactiveTabTextColor(self, evt):
		curr = self.pgf.InactiveTabTextColor
		newcolor = self.getColorName(curr)
		if newcolor:
			self.pgf.InactiveTabTextColor = newcolor
			self.update()
			self.Form.logit("InactiveTabTextColor changed to '%s'" % ustr(newcolor))



category = "Controls.dPageStyled"

overview = """
<p><b>Paged Controls</b> allow you to organize the visual presentation of
your data and UI controls onto separate 'pages' that are selected by various
means. Only one page is visible at any given time.</p>

<p>The <b>dPageStyled</b> control is not a native control, but rather one
that was created by Andrea Gavana and later incorporated into wxPython as
the <b>Flat Notebook</b> control. We wrapped it an renamed it to be consistent
with our other paged controls.</p>

<p>This control has several properties that control the appearance of the tabs,
as well as several other optional controls that can appear in the tab area. This demo
is designed to demonstrate the effect of changing these properties. Please note
that some properties only have an effect with certain TabStyle settings.</p>

<p>Unlike the other paged controls, you can change the <b>TabPosition</b>
property after the control has been created, although I can't imagine any
user-friendly interface where that would be needed. Also, you are limited
to Top and Bottom for tab positions; tabs along the sides is not supported.
You can also re-order the tabs by dragging them to their new position.</p>
"""
