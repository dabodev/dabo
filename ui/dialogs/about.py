import sys
import dabo
if dabo.ui.getUIType() is None:
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class About(dabo.ui.dDialog):
	def initProperties(self):
		self.AutoSize = True
		self.Centered = True
		self.Caption = _("About")
		
	def initEvents(self):
		# Destroy the window when deactivated:
		self.bindEvent(dEvents.Deactivate, self.onClear)
		self.bindEvent(dEvents.Close, self.onClose)
		self.bindKey("space", self.onClear)
		self.bindKey("enter", self.onClear)
		self.bindKey("d", self.onEasterEgg)

	def addControls(self):
		# Catch mousedown in every control, but define the binding once:
		clickBinding = (dEvents.MouseLeftDown, self.onClear)

		pnlBack = dabo.ui.dPanel(self, BackColor="Peru")
		pnlBack.bindEvent(*clickBinding)
 		self.Sizer.append(pnlBack, 1, "x")
		pnlBack.Sizer = sz = dabo.ui.dSizer("v")

		pnlHead = dabo.ui.dPanel(pnlBack, BackColor="PeachPuff")
		pnlHead.bindEvent(*clickBinding)
		pnlHead.Sizer = ps = dabo.ui.dSizer("h")

		ps.Border = 32
		lblHead = dabo.ui.dLabel(pnlHead, Caption="Dabo", FontSize=36, 
		                         FontBold=True)
		lblHead.bindEvent(*clickBinding)

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
		uiVersion = "%s on %s" % (dabo.ui.uiType["version"], 
		                          dabo.ui.uiType["platform"])

		# Define the style dicts for the labels
		fntBase = 10
		if self.Application.Platform == "Mac":
			fntBase += 4
		labelStyle = {"FontSize" : fntBase, "FontBold" : False}
		valStyle = {"FontSize" : fntBase+2, "FontBold" : True, "BackColor" : "gold"}

		# Add a grid sizer for the rest of the info
		gs = dabo.ui.dGridSizer(maxCols=2, hgap=5, vgap=10)
		gs.setColExpand(True, "all")
		gs.append(dabo.ui.dLabel(pnlBack, Caption=_("Dabo Version:"), 
		                         properties=labelStyle), alignment="right")
		gs.append(dabo.ui.dLabel(pnlBack, Caption=daboVersion, properties=valStyle))
		gs.append(dabo.ui.dLabel(pnlBack, Caption=_("UI Version:"), 
		                         properties=labelStyle), alignment="right")
		gs.append(dabo.ui.dLabel(pnlBack, Caption=uiVersion, properties=valStyle))
		gs.append(dabo.ui.dLabel(pnlBack, Caption=_("Python Version:"), 
		                         properties=labelStyle), alignment="right")
		gs.append(dabo.ui.dLabel(pnlBack, Caption=pyVersion, properties=valStyle))

		for child in pnlBack.Children:
				child.bindEvent(*clickBinding)

		sz.append(gs, 1, "x", alignment="right")
		sz.BorderBottom = True
		btn = dabo.ui.dButton(pnlBack, Caption=_("OK"), CancelButton=True)
		btn.bindEvent(dEvents.Hit, self.onClear)
		sz.append(btn, 0, alignment="center")
		
		self.Layout()
		pnlBack.Fit()


	def onClear(self, evt):
		self.Close()
	
	def onClose(self, evt=None):
		self.release()
	
	def onEasterEgg(self, evt):
		try:
			ee = self._ee
		except AttributeError:
			ee = self._ee = ""
		if ee == "":
			ee = "d"
			self.unbindKey("d")
			self.bindKey("a", self.onEasterEgg)
		elif ee == "d":
			ee = "da"
			self.unbindKey("a")
			self.bindKey("b", self.onEasterEgg)
		elif ee == "da":
			ee = "dab"
			self.unbindKey("b")
			self.bindKey("o", self.onEasterEgg)
		elif ee == "dab":
			ee = "dabo"
			self.unbindKey("o")
		if ee == "dabo":
			dabo.ui.dMessageBox.info("""
Working for a rise, better my station
Take my baby to sophistication
She's seen the ads, she thinks it's nice
Better work hard - I seen the price
Never mind that it's time for the bus
We got to work - an' you're one of us
Clocks go slow in a place of work
Minutes drag and the hours jerk

You lot! What?
Don't stop! Give it all you got!
You lot! What?
Don't stop! Yeah!
""")
		self._ee = ee

def main():
	app = dabo.dApp()
	app.MainFormClass = None
	app.setup()
	app.MainForm = About(None)
	app.MainForm.show()
	app.start()

if __name__ == '__main__':
	main()


