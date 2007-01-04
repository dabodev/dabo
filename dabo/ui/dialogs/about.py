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
		pnlBack = dabo.ui.dPanel(self, BackColor="White")
		self.Sizer.append(pnlBack, 1, "x")
		pnlBack.Sizer = sz = dabo.ui.dSizer("v")

		pnlHead = dabo.ui.dPanel(pnlBack, BackColor="White")
		pnlHead.Sizer = ps = dabo.ui.dSizer("h")

		ps.DefaultBorder = 0
		lblHead = dabo.ui.dLabel(pnlHead, Caption="Dabo", FontSize=24, 
								FontBold=True)

		ps.append(lblHead, 3, "x", halign="left", valign="middle")

		sz.DefaultSpacing = 20
		sz.DefaultBorder = 20
		sz.DefaultBorderTop = sz.DefaultBorderLeft = sz.DefaultBorderRight = True
		sz.append(pnlHead, 0, "x")
		
		eg = dabo.ui.dGrid(pnlBack, DataSet=self.getInfoDataSet(), 
				ShowColumnLabels=False, ShowCellBorders=False,
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
		btnCopy = dabo.ui.dButton(pnlBack, Caption=_("Copy Info"))
		btnCopy.bindEvent(dEvents.Hit, self.onCopyInfo)
		sz.append(btnCopy, 0, halign="right")

		sz.append((0,20))		

		self.Layout()
		pnlBack.Fit()
	

	def getInfoDataSet(self):
		"""Return Application Information in a sequence of dicts."""
		# Get all the version info, etc.
		app = self.Application

		ds = []
		if app:
			plat = app.Platform
		else:
			plat = sys.platform
		ds.append({"name": "Platform:", "value": plat})
		ds.append({"name": "Python Version:", "value": "%s on %s" 
				% (sys.version.split()[0], sys.platform)})
		if app:
			appVersion = app.getAppInfo("appVersion")
			appName = app.getAppInfo("appName")
		else:
			appVersion = "?"
			appName = "Dabo"
		ds.append({"name": "Dabo Version:", "value": "Version %s; Revision %s" 
				% (dabo.version["version"], dabo.version["revision"])})

#		uiName = dabo.ui.uiType["longName"]

		ds.append({"name": "UI Version:", "value": "%s on %s" % (dabo.ui.uiType["version"], 
				dabo.ui.uiType["platform"])})
		
		if app:
			appSpecific = app.addToAbout()
			if appSpecific:
				ds.append(appSpecific)
		return ds


	def getInfoString(self):
		"""Return app information as a string."""
		ds = self.getInfoDataSet()
		lines = []
		for r in ds:
			lines.append("%s %s" % (r["name"], r["value"]))

		if self.Application.Platform == "Win":
			eol = "\r\n"
		else:
			eol = "\n"

		return eol.join(lines)
	

	def onCopyInfo(self, evt):
		"""Copy the system information to the Clipboard"""
		self.Application.copyToClipboard(self.getInfoString())


	def onClear(self, evt):
		self.Close()
	
	def onClose(self, evt=None):
		self.release()
	

def main():
	app = dabo.dApp()
	app.MainFormClass = None
	app.setup()
	app.MainForm = About(None)
	app.MainForm.show()
	app.start()

if __name__ == '__main__':
	main()


