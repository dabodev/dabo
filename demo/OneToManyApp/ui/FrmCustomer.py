# -*- coding: utf-8 -*-

import os
from FrmBase import FrmBase
from GrdCustomer import GrdCustomer
from PagSelectCustomer import PagSelectCustomer
from PagEditCustomer import PagEditCustomer


class FrmCustomer(FrmBase):
	def initProperties(self):
		self.super()
		self.NameBase = "frmCustomer"
		self.Caption = "Customers"
		self.SelectPageClass = PagSelectCustomer
		self.BrowseGridClass = GrdCustomer
		self.EditPageClass = PagEditCustomer


	def afterInit(self):
		app = self.Application
		bizCustomer = app.biz.Customer(app.dbConnection)
		bizOrders = app.biz.Orders(app.dbConnection, LinkField="cust_fk")
		bizCustomer.addChild(bizOrders)
		self.addBizobj(bizCustomer)
		self.addBizobj(bizOrders)
		
		self.super()

