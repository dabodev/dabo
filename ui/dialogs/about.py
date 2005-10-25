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
		# Destroy the window when deactivated:
#		self.bindEvent(dEvents.Deactivate, self.onClear)
		self.bindEvent(dEvents.Close, self.onClose)
		self.bindKey("space", self.onClear)
		self.bindKey("enter", self.onClear)
		self.bindKey("d", self.onEasterEgg)

	def addControls(self):
		# Catch mousedown in every control, but define the binding once:
		clickBinding = (dEvents.MouseLeftDown, self.onClear)

		pnlBack = dabo.ui.dPanel(self, BackColor="Peru")
# 		pnlBack.bindEvent(*clickBinding)
		self.Sizer.append(pnlBack, 1, "x")
		pnlBack.Sizer = sz = dabo.ui.dSizer("v")

		pnlHead = dabo.ui.dPanel(pnlBack, BackColor="PeachPuff")
# 		pnlHead.bindEvent(*clickBinding)
		pnlHead.Sizer = ps = dabo.ui.dSizer("h")

		ps.Border = 32
		lblHead = dabo.ui.dLabel(pnlHead, Caption="Dabo", FontSize=36, 
								FontBold=True)
# 		lblHead.bindEvent(*clickBinding)

		ps.appendSpacer(5, 1)
		ps.append(lblHead, 3, "x", halign="center", valign="middle")
		ps.appendSpacer(5, 1)
		
		sz.Spacing = 20
		sz.Border = 40
		sz.BorderTop = sz.BorderLeft = sz.BorderRight = True
		sz.append(pnlHead, 0, "x")
		sz.BorderTop = False
		
		# Get all the version info, etc.
		app = self.Application
		self.pyVersion = "%s on %s" % (sys.version.split()[0], sys.platform)
		if app:
			appVersion = app.getAppInfo("appVersion")
			appName = app.getAppInfo("appName")
		else:
			appVersion = "?"
			appName = "Dabo"
		self.daboVersion = "Version %s; Revision %s" % (dabo.version["version"],
				dabo.version["revision"])

		uiName = dabo.ui.uiType["longName"]
		self.uiVersion = "%s on %s" % (dabo.ui.uiType["version"], 
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
					properties=labelStyle), halign="right")
		gs.append(dabo.ui.dLabel(pnlBack, Caption="%s (rev. %s)" 
					% (dabo.version["version"], dabo.version["revision"]), 
					properties=valStyle))
		gs.append(dabo.ui.dLabel(pnlBack, Caption=_("UI Version:"), 
				properties=labelStyle), halign="right")
		gs.append(dabo.ui.dLabel(pnlBack, Caption=self.uiVersion, properties=valStyle))
		gs.append(dabo.ui.dLabel(pnlBack, Caption=_("Python Version:"), 
				properties=labelStyle), halign="right")
		gs.append(dabo.ui.dLabel(pnlBack, Caption=self.pyVersion, properties=valStyle))

# 		for child in pnlBack.Children:
# 				child.bindEvent(*clickBinding)

		sz.append(gs, 1, "x", halign="right")
		
		# Copy info
		btnCopy = dabo.ui.dButton(pnlBack, Caption=_("Copy Info"))
		btnCopy.bindEvent(dEvents.Hit, self.onCopyInfo)
		sz.append(btnCopy, 0, halign="center")
		
		sz.BorderBottom = True
		btn = dabo.ui.dButton(pnlBack, Caption=_("OK"), CancelButton=True)
		btn.bindEvent(dEvents.Hit, self.onClear)
		sz.append(btn, 0, halign="center")
		
		self.Layout()
		pnlBack.Fit()
	
	
	def onCopyInfo(self, evt):
		"""Copy the system information to the Clipboard"""
		info = """Platform: %s
Dabo Version: %s
UI Version: %s (%s)
Python Version: %s
""" % (self.Application.Platform, self.daboVersion,
				self.uiVersion, self.Application.getCharset(), self.pyVersion)
		self.Application.copyToClipboard(info)		


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
			dabo.ui.info("""
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


