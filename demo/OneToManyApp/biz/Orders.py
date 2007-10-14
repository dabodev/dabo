# -*- coding: utf-8 -*-

from Base import Base


class Orders(Base):
	def initProperties(self):
		self.super()
		self.Caption = "Orders"
		self.DataSource = "orders"
		self.KeyField = "pkid"
		self.DataStructure = (
				# (field_alias, field_type, pk, table_name, field_name, field_scale)
				("pkid", "I", True, "orders", "pkid"),
				("to_name", "C", False, "orders", "to_name"),
				("order_date", "D", False, "orders", "order_date"),
				("order_amt", "N", False, "orders", "order_amt"),
				)


	def setBaseSQL(self):
		self.addFrom("orders")
		self.setLimitClause("500")
		self.addFieldsFromDataStructure()				
