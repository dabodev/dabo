# -*- coding: utf-8 -*-

import os
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from FrmBase import FrmBase
from GrdOrders import GrdOrders
from PagSelectOrders import PagSelectOrders
from PagEditOrders import PagEditOrders


class FrmOrders(FrmBase):

	def initProperties(self):
		self.super()
		self.NameBase = "frmOrders"
		self.Caption = "Orders"
		self.SelectPageClass = PagSelectOrders
		self.BrowseGridClass = GrdOrders
		self.EditPageClass = PagEditOrders


	def afterInit(self):
		if not self.Testing:
			# Instantiate the bizobj and register it with dForm, and then let the 
			# superclass take over.
			app = self.Application
			bizOrders = app.biz.Orders(app.dbConnection)
			self.addBizobj(bizOrders)
		self.super()


if __name__ == "__main__":
	app = dabo.dApp(MainFormClass=None)
	app.setup()
	frm = FrmOrders(Caption="Test Of FrmOrders", Testing=True)
	frm.show()
	app.start()
