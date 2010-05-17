# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _


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
				Size=(20, 20), DynamicBackColor=lambda:self.pgf.ActiveTabColor,
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

	def onSetActiveTabColor(self, evt):
		curr = self.pgf.ActiveTabColor
		newcolor = dabo.ui.getColor(curr)
		if newcolor:
			self.pgf.ActiveTabColor = newcolor
			self.update()
			self.Form.logit("ActiveTabColor changed to '%s'" % newcolor)

	def onSetTabAreaColor(self, evt):
		curr = self.pgf.TabAreaColor
		newcolor = dabo.ui.getColor(curr)
		if newcolor:
			self.pgf.TabAreaColor = newcolor
			self.update()
			self.Form.logit("TabAreaColor changed to '%s'" % newcolor)

	def onSetActiveTabTextColor(self, evt):
		curr = self.pgf.ActiveTabTextColor
		newcolor = dabo.ui.getColor(curr)
		if newcolor:
			self.pgf.ActiveTabTextColor = newcolor
			self.update()
			self.Form.logit("ActiveTabTextColor changed to '%s'" % newcolor)

	def onSetInactiveTabTextColor(self, evt):
		curr = self.pgf.InactiveTabTextColor
		newcolor = dabo.ui.getColor(curr)
		if newcolor:
			self.pgf.InactiveTabTextColor = newcolor
			self.update()
			self.Form.logit("InactiveTabTextColor changed to '%s'" % newcolor)



category = "Controls.dPageStyled"

overview = """
Styled Paged Control
"""
