# -*- coding: utf-8 -*-
from Base import Base


class Customer(Base):
	
	def initProperties(self):
		Customer.doDefault()
		self.Caption = "Customer"
		self.DataSource = "customer"
		self.KeyField = "pkid"

		# Set the default values for new records added:
		self.DefaultValues = {}

		# Default encoding is set to utf8, but if your backend db encodes in 
		# something else, you need to set that encoding here (or in each 
		# bizobj individually. A very common encoding for the Americas and
		# Western Europe is "latin-1", so if you are getting errors but are
		# unsure what encoding to pick, try uncommenting the following line:
		self.Encoding = "latin-1"
	

	def afterInit(self):
		Customer.doDefault()
		

	def setBaseSQL(self):
		# Set up the base SQL (the fields clause, the from clause, etc.) The
		# UI refresh() will probably modify the where clause and maybe the
		# limit clause, depending on what the runtime user chooses in the
		# select page.
		self.addFrom("customer")
		self.setLimitClause("500")
		self.addField("customer.pkid as pkid")
		self.addField("customer.cust_id as cust_id")
		self.addField("customer.company as company")
		self.addField("customer.contact as contact")
		self.addField("customer.title as title")
		self.addField("customer.address as address")
		self.addField("customer.city as city")
		self.addField("customer.region as region")
		self.addField("customer.postalcode as postalcode")
		self.addField("customer.country as country")
		self.addField("customer.phone as phone")
		self.addField("customer.fax as fax")
		self.addField("customer.maxordamt as maxordamt")
				
