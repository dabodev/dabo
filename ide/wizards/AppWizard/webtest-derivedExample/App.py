# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import ui
from __version__ import version


class App(dabo.dApp):

	def initProperties(self):
		self.BasePrefKey = "AppWizard.webtest-derived.example"

		if dabo.settings.MDI:
			self.MainFormClass = ui.FrmMain
		else:
			# no need for main form in SDI mode:
			self.MainFormClass = None

		## The following information can be used in various places in your app:
		self.setAppInfo("appShortName", "Webtest")
		self.setAppInfo("appName", "Webtest")
		self.setAppInfo("companyName", "Your company name")
		self.setAppInfo("companyAddress1", "Your company address")
		self.setAppInfo("companyAddress2", "Your company CSZ")
		self.setAppInfo("companyPhone", "Your company phone")
		self.setAppInfo("companyEmail", "Your company email")
		self.setAppInfo("companyUrl", "Your company url")

		self.setAppInfo("appDescription", "")

		## Information about the developer of the software:
		self.setAppInfo("authorName", "")
		self.setAppInfo("authorEmail", "")
		self.setAppInfo("authorURL", "")

		## Set appVersion and appRevision from __version__.py:
		self.setAppInfo("appVersion", version["version"])
		self.setAppInfo("appRevision", version["revision"])
