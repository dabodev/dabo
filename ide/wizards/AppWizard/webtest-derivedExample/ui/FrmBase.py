# -*- coding: utf-8 -*-
import dabo.ui
import dabo.lib.datanav as datanav


class FrmBase(datanav.Form):

	def initProperties(self):
		# Setting RequeryOnLoad to True will result in an automatic requery upon
		# form load, which may be appropriate for your app (if it is reasonably
		# certain that the dataset will be small no matter what).
		self.RequeryOnLoad = False
		self.Icon = "daboIcon.ico"


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


	def getEditClassForField(self, fieldName):
		"""The framework will call this when creating the edit page. 

		If you don't want the default textbox for a given field (perhaps you
		want a drop down list with choices filled from a related table), then
		override this method and return the control class you want when the
		field is passed.
		"""
		## Use the commented sample code as boilerplate, and customize to your
		## needs. Note that you probably want this at the individual form def
		## level, and not here in FrmBase. It is here only to avoid code 
		## duplication in every single form!
		pass

#		tableName = self.PrimaryBizobj.DataSource

#		if fieldName in ("iclientid", "isubclientid", "isubclient"):
#			app = self.Application
#			lookup = app.biz.Clients(app.dbConnection)
#			lookup.requery()
#			lookup.sort("ccode")
#			lookup.first()
#			choices = []
#			keys = {}
#			while True:
#				choices.append("%s: %s" % (lookup.ccode, lookup.ccompany))
#				keys[lookup.iid] = len(choices) - 1
#				try:
#					lookup.next()
#				except:
#					break

#			# append the None record:
#			choices.append("< None >")
#			keys[None] = len(choices) - 1

#			return self.getDropdownList(choices, keys, "key")


	def getSelectOptionsForField(self, fieldName):
		"""Override this to set the list of comparison operators for this field."""
		pass
## Note that you want to override this at the individual form level, not here in
## FrmBase as I've done.
#		if fieldName == "istatus":
#			return ["Is",]
#		return None


	def getSelectControlClassForField(self, fieldName):
		"""Override this to specify the control class to use for this field."""
		pass
#		tableName = self.PrimaryBizobj.DataSource
#
#		if fieldName in ("istatus",):
#			app = self.Application
#			lookup = app.biz.TimeStatusCodes(app.dbConnection)
#			lookup.requery()
#			lookup.sort("istatuscode")
#			lookup.first()
#			choices = []
#			keys = {}
#			while True:
#				choices.append(lookup.cstatusname)
#				keys[lookup.iid] = len(choices) - 1
#				try:
#					lookup.next()
#				except:
#					break
#
#			return self.getRadioList(choices, keys, "key")	


	## The following are samples of custom classes that can be returned in the
	## getEditClassForField() and getSelectControlClassForField() methods.
	## Uncomment and modify for your needs.
#	def getDropdownList(self, Choices=[], Keys={}, ValueMode="key"):
#		class C(dabo.ui.dDropdownList):
#			def initProperties(self):
#				C.doDefault()
#				self.Choices = Choices
#				self.Keys = Keys
#				self.ValueMode = "key"
#		return C
#
#
#	def getRadioList(self, Choices=[], Keys={}, ValueMode="key"):
#		class C(dabo.ui.dRadioList):
#			def initProperties(self):
#				C.doDefault()
#				self.Choices = Choices
#				self.Keys = Keys
#				self.ValueMode = "key"
#				self.Orientation = "Row"
#		return C


