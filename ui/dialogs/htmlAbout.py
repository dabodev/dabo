import sys
import os
import string
import dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class HtmlAbout(dabo.ui.dDialog):
	def initProperties(self):
		self.AutoSize = True
		self.Centered = True
		self.Caption = _("About")

	def initEvents(self):
		self.bindKey("space", self.onClear)
		self.bindKey("enter", self.onClear)

	def addControls(self):
		pnlBack = dabo.ui.dPanel(self, BackColor=dabo.dColors.colorTupleFromHex("#DEDEF5"))
		self.Sizer.append(pnlBack, 1, "x")
		pnlBack.Sizer = sz = dabo.ui.dSizer("v")

		basepath = os.path.split(dabo.__file__)[0]
		if self.Application.Platform == "Win":
			self.Dabopath = "%s\\ui\\dialogs\\AboutData\\about.html" % (basepath,)
		else:
			self.Dabopath = "%s/ui/dialogs/AboutData/about.html" % (basepath,)

		self.writeHtmlPage()

		self.htmlBox = dabo.ui.dHtmlBox(self)
		self.htmlBox.Page = self.Dabopath
		self.htmlBox.Size = (400,300)
		sz.append1x(self.htmlBox, halign="center", valign="center")

		# Copy info
		btnCopy = dabo.ui.dButton(pnlBack, Caption=_("Copy Info"))
		btnCopy.bindEvent(dEvents.Hit, self.onCopyInfo)
		sz.append(btnCopy, 0, halign="right")

		sz.append((0,20))

		self.Layout()
		pnlBack.Fit()


	def PageData(self):
		return """<html>
			<body bgcolor="#DEDEF5">
				<img src="dabo_lettering_250x100.gif" alt="Dabo image" width="250" height="100">
				</center>
				<p>
				[AppInfo]
				</p>

				<p>
				[DocString]
				</p>
			</body>
		</html>
		"""

	def writeHtmlPage(self):
		file = open(self.Dabopath, 'w')
		self.text = string.replace(self.PageData(), "[AppInfo]", self.getInfoString())
		self.text = string.replace(self.text, "[DocString]", self.getAppSpecificString())
		file.write(self.text)
		file.close()


	def getInfoDataSet(self):
		"""Return Application Information in a sequence of dicts."""
		# Get all the version info, etc.
		app = self.Application

		ds = []
		ds.append({"name": "Platform:", "value": app.Platform})
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

		return ds


	def getInfoString(self):
		"""Return app information as a string."""
		ds = self.getInfoDataSet()
		lines = []
		for r in ds:
			lines.append("%s %s" % (r["name"], r["value"]))

			eol = "<br>\n"

		return eol.join(lines)


	def getAppSpecificString(self):
		if self.Application:
			text = self.Application.addToAbout()
			if text:
				return text
		return ""


	def onCopyInfo(self, evt):
		"""Copy the system information to the Clipboard"""
		self.Application.copyToClipboard(self.htmlBox.Source)


	def onClear(self, evt):
		self.Close()

	def onClose(self, evt=None):
		self.release()


def main():
	app = dabo.dApp()
	app.MainFormClass = None
	app.setup()
	app.MainForm = HtmlAbout(None)
	app.MainForm.show()
	app.start()

if __name__ == '__main__':
	main()


