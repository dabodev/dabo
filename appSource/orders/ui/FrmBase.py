# -*- coding: utf-8 -*-

import dabo.ui
import dabo.lib.datanav2 as datanav
from MenFileOpen import MenFileOpen
from MenReports import MenReports


class FrmBase(datanav.Form):

	def initProperties(self):
		self.super()
		# Setting RequeryOnLoad to True will result in an automatic requery upon
		# form load, which may be appropriate for your app (if it is reasonably
		# certain that the dataset will be small no matter what).
		self.RequeryOnLoad = False
		self.Icon = "daboIcon.ico"


	def setupMenu(self):
		self.super()
		self.fillFileOpenMenu()
		self.fillReportsMenu()


	def fillFileOpenMenu(self):
		"""Add the File|Open menu, with menu items for opening each form."""
		app = self.Application
		fileMenu = self.MenuBar.getMenu("File")
		fileMenu.prependMenu(MenFileOpen(fileMenu))


	def fillReportsMenu(self):
		"""Add the Reports menu."""
		app = self.Application
		menReports = MenReports()

		# We want the reports menu right after the Actions menu:
		idx = self.MenuBar.getMenuIndex("Actions")
		if idx is None:
			# punt:
			idx = 3
		idx += 1
		self.MenuBar.insertMenu(idx, menReports)

		# The datanav form puts a Quick Report option at the end of the Actions
		# menu, but let's move it over to the Reports menu instead.
		menu = self.MenuBar.getMenu("Actions")
		idx = menu.getItemIndex("Quick Report")
		if idx is not None:
			qrItem = menu.remove(idx, False)
			menReports = self.MenuBar.getMenu("Reports")
			menReports.prependSeparator()
			menReports.prependItem(qrItem)


