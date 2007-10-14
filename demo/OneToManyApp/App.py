# -*- coding: utf-8 -*-

import dabo
dabo.ui.loadUI("wx")
import ui


class App(dabo.dApp):
	def initProperties(self):
		# Manages how preferences are saved
		self.BasePrefKey = "dabo.app.OneToManyApp"
		if dabo.settings.MDI:
			self.MainFormClass = ui.FrmMain
		else:
			# no need for main form in SDI mode:
			self.MainFormClass = None

		## The following information can be used in various places in your app:
		self.setAppInfo("appShortName", "OneToManyDemo")
		self.setAppInfo("appName", "One-To-Many Application Demo")

