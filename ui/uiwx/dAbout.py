import sys
import dabo
import dabo.dEvents as dEvents
from dForm import dForm
from dDialog import dDialog
from dLabel import dLabel
from dSizer import dSizer
from dGridSizer import dGridSizer
from dPanel import dPanel
from dButton import dButton


class dAbout(dDialog):
	def initProperties(self):
#		self.Height = 400
		self.AutoSize = True
		self.Centered = True
		self.MenuBar = None
		self.ShowStatusBar = False
		self.Caption = "About"
		
	def initEvents(self):
		# Destroy the window when deactivated:
		self.bindEvent(dEvents.Deactivate, self.onClear)
		self.bindEvent(dEvents.Close, self.onClose)

	def addControls(self):
		pnlBack = dPanel(self, BackColor="Peru")
 		self.Sizer.append(pnlBack, 1, "x")
		pnlBack.Sizer = sz = dSizer("v")
		pnlHead = dPanel(pnlBack, BackColor="PeachPuff")
		pnlHead.Sizer = ps = dSizer("h")
		ps.Border = 32
		lblHead = dLabel(pnlHead, Caption="Dabo", FontSize=36, FontBold=True)
		ps.appendSpacer(5, 1)
		ps.append(lblHead, 3, "x", alignment=("center", "middle"))
		ps.appendSpacer(5, 1)
		
		sz.Spacing = 20
		sz.Border = 40
		sz.BorderTop = sz.BorderLeft = sz.BorderRight = True
		sz.append(pnlHead, 0, "x")
		sz.BorderTop = False
		
		# Get all the version info, etc.
		app = self.Application
		pyVersion = "%s on %s" % (sys.version.split()[0], sys.platform)
		if app:
			appVersion = app.getAppInfo("appVersion")
			appName = app.getAppInfo("appName")
		else:
			appVersion = "?"
			appName = "Dabo"
		daboVersion = dabo.version["version"]
		uiName = dabo.ui.uiType["longName"]
		uiVersion = "%s on %s" % (dabo.ui.uiType["version"], dabo.ui.uiType["platform"])

		# Define the style dicts for the labels
		fntBase = 10
		if self.Application.Platform == "Mac":
			fntBase += 4
		labelStyle = {"FontSize" : fntBase, "FontBold" : False}
		valStyle = {"FontSize" : fntBase+2, "FontBold" : True, "BackColor" : "gold"}
		# Add a grid sizer for the rest of the info
		gs = dGridSizer(maxCols=2, hgap=5, vgap=10)
		gs.setColExpand(True, "all")
		gs.append(dLabel(pnlBack, Caption="Dabo Version:", properties=labelStyle), alignment="right")
		gs.append(dLabel(pnlBack, Caption=daboVersion, properties=valStyle))
		gs.append(dLabel(pnlBack, Caption="UI Version:", properties=labelStyle), alignment="right")
		gs.append(dLabel(pnlBack, Caption=uiVersion, properties=valStyle))
		gs.append(dLabel(pnlBack, Caption="Python Version:", properties=labelStyle), alignment="right")
		gs.append(dLabel(pnlBack, Caption=pyVersion, properties=valStyle))

		sz.append(gs, 1, "x", alignment="right")
		sz.BorderBottom = True
		btn = dButton(pnlBack, Caption="OK")
		btn.bindEvent(dEvents.Hit, self.onClear)
		sz.append(btn, 0, alignment="center")
		
		self.Layout()
		pnlBack.Fit()

	def onClear(self, evt):
		self.Close()
	
	
	def onClose(self, evt=None):
		self.Destroy()
	
		
def main():
	app = dabo.dApp()
	app.MainFormClass = dAbout
	app.setup()
	app.start()

if __name__ == '__main__':
	main()


