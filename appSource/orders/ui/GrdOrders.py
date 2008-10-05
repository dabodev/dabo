# -*- coding: utf-8 -*-

import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from GrdBase import GrdBase


class GrdOrders(GrdBase):

	def afterInit(self):
		self.super()

		# Delete or comment out any columns you don't want...
		self.addColumn(dabo.ui.dColumn(self, DataField="pkid", Caption="Pkid", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="cust_fk", Caption="Cust_Fk", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="employee_fk", Caption="Employee_Fk", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="order_id", Caption="Order_Id", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="cust_id", Caption="Cust_Id", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="emp_id", Caption="Emp_Id", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="to_name", Caption="To_Name", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="to_address", Caption="To_Address", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="to_city", Caption="To_City", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="to_region", Caption="To_Region", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="postalcode", Caption="Postalcode", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="to_country", Caption="To_Country", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="ship_count", Caption="Ship_Count", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="ship_via", Caption="Ship_Via", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="order_date", Caption="Order_Date", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="order_amt", Caption="Order_Amt", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="order_dsc", Caption="Order_Dsc", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="order_net", Caption="Order_Net", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="require_by", Caption="Require_By", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="shipped_on", Caption="Shipped_On", 
				Sortable=True, Searchable=True, Editable=False))

		self.addColumn(dabo.ui.dColumn(self, DataField="freight", Caption="Freight", 
				Sortable=True, Searchable=True, Editable=False))



if __name__ == "__main__":
	from FrmOrders import FrmOrders
	app = dabo.dApp(MainFormClass=None)
	app.setup()
	class TestForm(FrmOrders):
		def afterInit(self): pass
	frm = TestForm(Caption="Test Of GrdOrders", Testing=True)
	test = frm.addObject(GrdOrders)
	frm.Sizer.append1x(test)
	frm.show()
	app.start()
