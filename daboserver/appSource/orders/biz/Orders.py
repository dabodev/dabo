# -*- coding: utf-8 -*-

from Base import Base


class Orders(Base):
	
	def initProperties(self):
		self.super()
		self.Caption = "Orders"
		self.DataSource = "orders"
		self.KeyField = "pkid"

		# Setting the DataStructure explicitly here is optional, but recommended as
		# it will keep Dabo from interpreting field types from the backend every 
		# time. It lets you specify what types you expect which fields to be. Also,
		# this information is used in self.setSQL() to add the fields to the query.
		# (field_alias, field_type, pk, table_name, field_name, field_scale)
		self.DataStructure = (
				("pkid", "I", True, "orders", "pkid"),
				("cust_fk", "I", False, "orders", "cust_fk"),
				("employee_fk", "I", False, "orders", "employee_fk"),
				("order_id", "C", False, "orders", "order_id"),
				("cust_id", "C", False, "orders", "cust_id"),
				("emp_id", "C", False, "orders", "emp_id"),
				("to_name", "C", False, "orders", "to_name"),
				("to_address", "C", False, "orders", "to_address"),
				("to_city", "C", False, "orders", "to_city"),
				("to_region", "C", False, "orders", "to_region"),
				("postalcode", "C", False, "orders", "postalcode"),
				("to_country", "C", False, "orders", "to_country"),
				("ship_count", "C", False, "orders", "ship_count"),
				("ship_via", "C", False, "orders", "ship_via"),
				("order_date", "D", False, "orders", "order_date"),
				("order_amt", "N", False, "orders", "order_amt"),
				("order_dsc", "I", False, "orders", "order_dsc"),
				("order_net", "N", False, "orders", "order_net"),
				("require_by", "D", False, "orders", "require_by"),
				("shipped_on", "D", False, "orders", "shipped_on"),
				("freight", "N", False, "orders", "freight"),
		)		

		# Use the DefaultValues dict to specify default field values for new 
		# records. By default DefaultValues is the empty dict, meaning that 
		# no default values will be filled in.
		#self.DefaultValues['<field_name>'] = <value_or_function_object>

		# Default encoding is set to utf8, but if your backend db encodes in 
		# something else, you need to set that encoding here (or in each 
		# bizobj individually. A very common encoding for the Americas and
		# Western Europe is "latin-1", so if you are getting errors but are
		# unsure what encoding to pick, try uncommenting the following line:
		#self.Encoding = "latin-1"
	

	def afterInit(self):
		self.super()
		

	def setBaseSQL(self):
		# Set up the base SQL (the fields clause, the from clause, etc.) The
		# UI refresh() will probably modify the where clause and maybe the
		# limit clause, depending on what the runtime user chooses in the
		# select page.
		self.addFrom("orders")
		self.setLimitClause("500")
		self.addFieldsFromDataStructure()
