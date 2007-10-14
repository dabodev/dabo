# -*- coding: utf-8 -*-
from Base import Base


class Zipcodes(Base):
	
	def initProperties(self):
		Zipcodes.doDefault()
		self.Caption = "Zipcodes"
		self.DataSource = "zipcodes"
		self.KeyField = "iid"

		# Set the default values for new records added:
		self.DefaultValues = {}

		# Default encoding is set to utf8, but if your backend db encodes in 
		# something else, you need to set that encoding here (or in each 
		# bizobj individually. A very common encoding for the Americas and
		# Western Europe is "latin-1", so if you are getting errors but are
		# unsure what encoding to pick, try uncommenting the following line:
		#self.Encoding = "latin-1"
	

	def afterInit(self):
		Zipcodes.doDefault()
		

	def setBaseSQL(self):
		# Set up the base SQL (the fields clause, the from clause, etc.) The
		# UI refresh() will probably modify the where clause and maybe the
		# limit clause, depending on what the runtime user chooses in the
		# select page.
		self.addFrom("zipcodes")
		self.setLimitClause("500")
		self.addField("zipcodes.iid as iid")
		self.addField("zipcodes.ccity as ccity")
		self.addField("zipcodes.cstateprov as cstateprov")
		self.addField("zipcodes.czip as czip")
		self.addField("zipcodes.ccounty as ccounty")
		self.addField("zipcodes.careacode as careacode")
		self.addField("zipcodes.clatitude as clatitude")
		self.addField("zipcodes.clongitude as clongitude")
		self.addField("zipcodes.ctimezonediff as ctimezonediff")
				
