# -*- coding: utf-8 -*-
# myBizobjs.py
# Created with the Dabo AppWizard on Fri Jan 21 17:43:30 2005.

# Treat this as boilerplate code, and edit as needed.

import dabo.biz as biz
import dabo.dException as dException
from dabo.dLocalize import _


# Each table has been assigned a bizobj, but it is up to 
# you to provide any needed business rules. By default, 
# every change to the data will be allowed.

class BizRecipes(biz.dBizobj):
	
	def initProperties(self):
		self.Caption = "Recipes"
		self.DataSource = "recipes"
		self.KeyField = "iid"
		self.RequeryOnLoad = False
		# Set the default values for new records added:
		self.DefaultValues = {"ctitle":"< New Recipe >"}
		self.Encoding = "latin-1"
	
	def afterInit(self):
		self.setBaseSQL()

		
	def setBaseSQL(self):
		# Set up the base SQL (the fields clause, the from clause, etc.) The
		# UI refresh() will probably modify the where clause and maybe the
		# limit clause, depending on what the runtime user chooses in the
		# select page.
		self.addFrom("recipes")
		self.setLimitClause("500")
		self.addField("recipes.iid as iid")
		self.addField("recipes.ctitle as ctitle")
		self.addField("recipes.msubtitle as msubtitle")
		self.addField("recipes.mingred as mingred")
		self.addField("recipes.mproced as mproced")
		self.addField("recipes.ddate as ddate")
		self.addField("recipes.cimage as cimage")
		self.addField("recipes.ldeleted as ldeleted")
		self.addField("recipes.cid as cid")


	def validateRecord(self):
		# Initially set the error message to an empty string. If this method 
		# makes it all the way through with no biz rule violations, the string will
		# still be empty and the bizobj will let the commit happen.
		errorText = ""

		# Biz rules follow. These can be as complex as necessary, the key 
		# thing is to remember to add to the error message so the user knows
		# why a failure happened.

		# Rules for ctitle:
		if self.Record.ctitle.find("< New Recipe >") >= 0:
			errorText += _("Please set the title of the recipe before saving.\n")

		# If we return an empty string, there were no validation problems.
		return errorText


class BizReccats(biz.dBizobj):
	
	def initProperties(self):
		self.Caption = "Reccats"
		self.DataSource = "reccats"
		self.KeyField = "iid"
		self.RequeryOnLoad = False
		# Set the default values for new records added:
		self.DefaultValues = {"cdescrp":"< New Category >"}
		self.Encoding = "latin-1"

	
	def afterInit(self):
		self.setBaseSQL()

		
	def setBaseSQL(self):
		# Set up the base SQL (the fields clause, the from clause, etc.) The
		# UI refresh() will probably modify the where clause and maybe the
		# limit clause, depending on what the runtime user chooses in the
		# select page.
		self.addFrom("reccats")
		self.setLimitClause("500")
		self.addField("reccats.iid as iid")
		self.addField("reccats.cdescrp as cdescrp")
		self.addField("reccats.mhtml as mhtml")
		self.addField("reccats.cimage as cimage")
		self.addField("reccats.ldeleted as ldeleted")
		self.addField("reccats.cid as cid")


	def validateRecord(self):
		# Initially set the error message to an empty string. If this method 
		# makes it all the way through with no biz rule violations, the string will
		# still be empty and the bizobj will let the commit happen.
		errorText = ""

		# Biz rules follow. These can be as complex as necessary, the key 
		# thing is to remember to add to the error message so the user knows
		# why a failure happened.

		# Rules for ctitle:
		if self.Record.cdescrp.find("< New Category >") >= 0:
			errorText += _("Please set the name of the category before saving.\n")

		# If we return an empty string, there were no validation problems.
		return errorText


