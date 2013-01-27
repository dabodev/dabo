# -*- coding: utf-8 -*-
import sys
import dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class About(dabo.ui.dDialog):
	def initProperties(self):
		self.AutoSize = True
		self.Centered = True
		self.Caption = _("About")


	def initEvents(self):
		self.bindKey("space", self.onClear)
		self.bindKey("enter", self.onClear)


	def addControls(self):
		app = self.Application
		caption = "Dabo"
		if app:
			caption = "%s %s" % (app.getAppInfo("appName"),
					app.getAppInfo("appVersion"))

		pnlBack = dabo.ui.dPanel(self, BackColor="White")
		self.Sizer.append(pnlBack, 1, "x")
		pnlBack.Sizer = sz = dabo.ui.dSizer("v")

		pnlHead = dabo.ui.dPanel(pnlBack, BackColor="White")
		pnlHead.Sizer = ps = dabo.ui.dSizer("h")

		ps.DefaultBorder = 0
		lblHead = dabo.ui.dLabel(pnlHead, Caption=caption, FontSize=24,
								FontBold=True)

		ps.append(lblHead, 3, "x", halign="left", valign="middle")

		sz.DefaultSpacing = 20
		sz.DefaultBorder = 20
		sz.DefaultBorderTop = sz.DefaultBorderLeft = sz.DefaultBorderRight = True
		sz.append(pnlHead, 0, "x")

		eg = dabo.ui.dGrid(pnlBack, DataSet=dabo.ui.getSystemInfo("dataset"),
				ShowHeaders=False, ShowCellBorders=False,
				CellHighlightWidth=0)
		eg.addColumn(dabo.ui.dColumn(eg, Name="Name", DataField="name",
				Sortable=False, Searchable=False, HorizontalAlignment="Right"))
		eg.addColumn(dabo.ui.dColumn(eg, Name="Name", DataField="value",
				Sortable=False, Searchable=False, FontBold=True))
		eg.autoSizeCol("all")
		eg.sizeToColumns()
		eg.sizeToRows()
		eg.HorizontalScrolling = False
		eg.VerticalScrolling = False
		sz.append1x(eg)

		# Copy info
		btnCopy = dabo.ui.dButton(pnlBack, Caption=_("Copy Info"),
				OnHit=self.onCopyInfo)
		btnClose = dabo.ui.dButton(pnlBack, Caption=_("OK"),
				OnHit=self.onClose)
		hsz = dabo.ui.dSizer("H")
		hsz.append(btnCopy)
		hsz.appendSpacer(20)
		hsz.append(btnClose)
		sz.append(hsz, halign="right")
		sz.append((0,20))
		self.Layout()
		pnlBack.Fit()


	def onCopyInfo(self, evt):
		"""Copy the system information to the Clipboard"""
		self.Application.copyToClipboard(dabo.ui.getSystemInfo())


	def onClear(self, evt):
		self.Close()


	def onClose(self, evt=None):
		self.release()


def main():
	from dabo.dApp import dApp
	app = dApp()
	app.MainFormClass = None
	app.setup()
	app.MainForm = About(None)
	app.MainForm.show()
	app.start()

if __name__ == '__main__':
	main()


