# -*- coding: utf-8 -*-
from Base import Base


class Orders(Base):
	
	def initProperties(self):
		Orders.doDefault()
		self.Caption = "Orders"
		self.DataSource = "orders"
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
		Orders.doDefault()
		

	def setBaseSQL(self):
		# Set up the base SQL (the fields clause, the from clause, etc.) The
		# UI refresh() will probably modify the where clause and maybe the
		# limit clause, depending on what the runtime user chooses in the
		# select page.
		self.setFromClause("orders inner join customer on customer.pkid = orders.cust_fk")
		self.setLimitClause("500")
		self.addField("orders.pkid as pkid")
		self.addField("orders.cust_fk as cust_fk")
		self.addField("orders.order_id as order_id")
		self.addField("orders.cust_id as cust_id")
		self.addField("orders.emp_id as emp_id")
		self.addField("orders.to_name as to_name")
		self.addField("orders.to_address as to_address")
		self.addField("orders.to_city as to_city")
		self.addField("orders.to_region as to_region")
		self.addField("orders.postalcode as postalcode")
		self.addField("orders.to_country as to_country")
		self.addField("orders.ship_count as ship_count")
		self.addField("orders.ship_via as ship_via")
		self.addField("orders.order_date as order_date")
		self.addField("orders.order_amt as order_amt")
		self.addField("orders.order_dsc as order_dsc")
		self.addField("orders.order_net as order_net")
		self.addField("orders.require_by as require_by")
		self.addField("orders.shipped_on as shipped_on")
		self.addField("orders.freight as freight")
		self.addField("customer.cust_id as custid")
		self.addField("customer.company as custcompany")
