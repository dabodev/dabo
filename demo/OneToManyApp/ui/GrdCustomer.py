# -*- coding: utf-8 -*-

import dabo
from GrdBase import GrdBase


class GrdCustomer(GrdBase):
	def afterInit(self):
		self.super()

		self.addColumn(dabo.ui.dColumn(self, DataField="company", DataType="char",
				Caption="Company", Sortable=True,	Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="city", DataType="char",
				Caption="City", Sortable=True,	Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="country", DataType="char",
				Caption="Country", Sortable=True,	Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="phone", DataType="char",
				Caption="Phone", Sortable=True,	Searchable=True, Editable=False))

