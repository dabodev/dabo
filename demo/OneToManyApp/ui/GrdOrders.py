# -*- coding: utf-8 -*-

import dabo


class GrdOrders(dabo.ui.dGrid):
	def initProperties(self):
		self.super()
		self.DataSource = "orders"

	def afterInit(self):
		self.super()

		self.addColumn(dabo.ui.dColumn(self, DataField="order_date",
				Caption="Order Date", Sortable=True,	Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="order_amt",
				Caption="Order Amt", Sortable=True,	Searchable=True, Editable=False))

