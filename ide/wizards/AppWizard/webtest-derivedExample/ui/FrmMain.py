# -*- coding: utf-8 -*-
import dabo.ui


class FrmMain(dabo.ui.dFormMain):

	def afterInit(self):
		FrmMain.doDefault()
		self.fillFileOpenMenu()


	def initProperties(self):
		self.Icon = "daboIcon.ico"


	def fillFileOpenMenu(self):
		"""Add the File|Open menu, with menu items for opening each form."""
		app = self.Application
		fileMenu = self.MenuBar.getMenu("File")
		fileMenu.prependMenu(app.ui.MenFileOpen(fileMenu))


