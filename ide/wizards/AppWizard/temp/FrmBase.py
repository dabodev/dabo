# -*- coding: utf-8 -*-
"""
I'm committing this script here temporarily so that Paul and Matthew are
on the same page. Drop this in as a replacement to the FrmBase as generated 
by AppWizardX, and the toolbar should do some wacky button enable/disable
tricks and the prior button should disappear when you enter the edit page
and reappear when you enter any other page.

This is working on Linux for me, and the SelectedPageNumbers are 0,1,2 for
Select/Browse/Edit, although Matthew seems to be seeing 1,0,2 on his system.
Also, he's not seeing the prior button come back and additional buttons 
disappearing.

I'm going to test this on Mac, Linux, and Windows just to see if I can 
recreate any of these inconsistencies.
"""

import dabo.ui
import dabo.lib.datanav as datanav
import dabo.dEvents as dEvents


class FrmBase(datanav.Form):

	def initProperties(self):
		# Setting RequeryOnLoad to True will result in an automatic requery upon
		# form load, which may be appropriate for your app (if it is reasonably
		# certain that the dataset will be small no matter what).
		self.RequeryOnLoad = False


	def afterCreation(self):
		# afterCreation() is a hook method called from datanav.Form
		FrmBase.doDefault()
		self.PageFrame.bindEvent(dEvents.PageChanged, self.onPageChanged)


	def setupMenu(self):
		FrmBase.doDefault()
		self.fillFileOpenMenu()
		self.fillReportsMenu()


	def fillFileOpenMenu(self):
		"""Add the File|Open menu, with menu items for opening each form."""
		app = self.Application
		fileMenu = self.MenuBar.getMenu("File")
		fileMenu.prependMenu(app.ui.MenFileOpen(fileMenu))


	def fillReportsMenu(self):
		"""Add the Reports menu."""
		app = self.Application
		menReports = app.ui.MenReports()

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

	def modifyToolBar(self):
		tb = self.ToolBar
		if self.PageFrame.SelectedPageNumber == 2:  # this is the edit page
			# if on the edit page, disable the next button
			# and remove the prior button:
			tb.getItem("Next").Enabled = False
			tb.getItem("First").Enabled = True
			tb.getItem("Last").Enabled = True
			self._holdRemoveButton = tb.remove(tb.getItemIndex("Prior"), False)

		elif self.PageFrame.SelectedPageNumber == 1: # this is the select page (pkm:? it's browse...)
			tb.getItem("Next").Enabled = True
			tb.getItem("Last").Enabled = False
			tb.getItem("First").Enabled = True
			if tb.getItem("Prior") is None:
				tb.insertItem(tb.getItemIndex("Requery"), self._holdRemoveButton)

		elif self.PageFrame.SelectedPageNumber == 0:  # this is the browse page (pkm:? it's select...)
			tb.getItem("First").Enabled = False
			tb.getItem("Next").Enabled = True
			tb.getItem("Last").Enabled = True
			if tb.getItem("Prior") is None:
				tb.insertItem(tb.getItemIndex("Requery"), self._holdRemoveButton)

	def onPageChanged(self, evt):
		self.modifyToolBar()
