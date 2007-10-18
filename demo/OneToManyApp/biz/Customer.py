# -*- coding: utf-8 -*-

from Base import Base


class Customer(Base):
	
	def initProperties(self):
		self.super()
		self.Caption = "Customer"
		self.DataSource = "customer"
		self.KeyField = "pkid"

	def setBaseSQL(self):
		self.addFrom("customer")
		self.setLimitClause("500")
		self.addField("customer.pkid as pkid")
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
				
