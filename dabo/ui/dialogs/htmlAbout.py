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
		pnlBack = dabo.ui.dPanel(self, BackColor="#DEDEF5")
		self.Sizer.append1x(pnlBack)
		pnlBack.Sizer = sz = dabo.ui.dSizer("v")

		self.htmlBox = dabo.ui.dHtmlBox(self)
		self.htmlBox.Size = (400,300)
		sz.append1x(self.htmlBox, halign="center", valign="center")

		# Copy info
		btnCopy = dabo.ui.dButton(pnlBack, Caption=_("Copy Info"))
		btnCopy.bindEvent(dEvents.Hit, self.onCopyInfo)
		sz.append(btnCopy, 0, halign="right")

		sz.append((0,20))

		self.Layout()
		pnlBack.Fit()

		self.htmlBox.Source = self.writeHtmlPage()


	def writeHtmlPage(self):
		return self.pageData().replace("[DocString]", self.getAppSpecificString()).replace("[AppInfo]", self.getInfoString())


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
		self.release()

	def onClose(self, evt=None):
		self.release()

	def pageData(self):
		"""Basic Template structure of the About box."""
		return """<html>
	<body bgcolor="#DEDEF5">
		<h1>
		<b>Dabo</b>
		</h1>

		<p>
		[AppInfo]
		</p>

		<p>
		[DocString]
		</p>
	</body>
</html>"""


def main():
	app = dabo.dApp()
	app.MainFormClass = None
	app.setup()
	app.MainForm = HtmlAbout(None)
	app.MainForm.show()
	app.start()

if __name__ == '__main__':
	main()


