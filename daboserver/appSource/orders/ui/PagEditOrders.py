# -*- coding: utf-8 -*-

import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from PagEditBase import PagEditBase


class PagEditOrders(PagEditBase):

	def createItems(self):
		"""Called by the datanav framework, when it is time to create the controls."""

		mainSizer = self.Sizer = dabo.ui.dSizer("v")
		gs = dabo.ui.dGridSizer(VGap=7, HGap=5, MaxCols=3)

		## Field orders.pkid
		label = self.addObject(dabo.ui.dLabel, NameBase="lblpkid", 
				Caption="pkid")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="pkid", 
				DataSource="orders", DataField="pkid")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.cust_fk
		label = self.addObject(dabo.ui.dLabel, NameBase="lblcust_fk", 
				Caption="cust_fk")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="cust_fk", 
				DataSource="orders", DataField="cust_fk")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.employee_fk
		label = self.addObject(dabo.ui.dLabel, NameBase="lblemployee_fk", 
				Caption="employee_fk")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="employee_fk", 
				DataSource="orders", DataField="employee_fk")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.order_id
		label = self.addObject(dabo.ui.dLabel, NameBase="lblorder_id", 
				Caption="order_id")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="order_id", 
				DataSource="orders", DataField="order_id")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.cust_id
		label = self.addObject(dabo.ui.dLabel, NameBase="lblcust_id", 
				Caption="cust_id")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="cust_id", 
				DataSource="orders", DataField="cust_id")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.emp_id
		label = self.addObject(dabo.ui.dLabel, NameBase="lblemp_id", 
				Caption="emp_id")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="emp_id", 
				DataSource="orders", DataField="emp_id")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.to_name
		label = self.addObject(dabo.ui.dLabel, NameBase="lblto_name", 
				Caption="to_name")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="to_name", 
				DataSource="orders", DataField="to_name")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.to_address
		label = self.addObject(dabo.ui.dLabel, NameBase="lblto_address", 
				Caption="to_address")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="to_address", 
				DataSource="orders", DataField="to_address")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.to_city
		label = self.addObject(dabo.ui.dLabel, NameBase="lblto_city", 
				Caption="to_city")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="to_city", 
				DataSource="orders", DataField="to_city")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.to_region
		label = self.addObject(dabo.ui.dLabel, NameBase="lblto_region", 
				Caption="to_region")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="to_region", 
				DataSource="orders", DataField="to_region")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.postalcode
		label = self.addObject(dabo.ui.dLabel, NameBase="lblpostalcode", 
				Caption="postalcode")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="postalcode", 
				DataSource="orders", DataField="postalcode")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.to_country
		label = self.addObject(dabo.ui.dLabel, NameBase="lblto_country", 
				Caption="to_country")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="to_country", 
				DataSource="orders", DataField="to_country")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.ship_count
		label = self.addObject(dabo.ui.dLabel, NameBase="lblship_count", 
				Caption="ship_count")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="ship_count", 
				DataSource="orders", DataField="ship_count")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.ship_via
		label = self.addObject(dabo.ui.dLabel, NameBase="lblship_via", 
				Caption="ship_via")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="ship_via", 
				DataSource="orders", DataField="ship_via")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.order_date
		label = self.addObject(dabo.ui.dLabel, NameBase="lblorder_date", 
				Caption="order_date")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="order_date", 
				DataSource="orders", DataField="order_date")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.order_amt
		label = self.addObject(dabo.ui.dLabel, NameBase="lblorder_amt", 
				Caption="order_amt")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="order_amt", 
				DataSource="orders", DataField="order_amt")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.order_dsc
		label = self.addObject(dabo.ui.dLabel, NameBase="lblorder_dsc", 
				Caption="order_dsc")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="order_dsc", 
				DataSource="orders", DataField="order_dsc")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.order_net
		label = self.addObject(dabo.ui.dLabel, NameBase="lblorder_net", 
				Caption="order_net")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="order_net", 
				DataSource="orders", DataField="order_net")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.require_by
		label = self.addObject(dabo.ui.dLabel, NameBase="lblrequire_by", 
				Caption="require_by")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="require_by", 
				DataSource="orders", DataField="require_by")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.shipped_on
		label = self.addObject(dabo.ui.dLabel, NameBase="lblshipped_on", 
				Caption="shipped_on")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="shipped_on", 
				DataSource="orders", DataField="shipped_on")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		## Field orders.freight
		label = self.addObject(dabo.ui.dLabel, NameBase="lblfreight", 
				Caption="freight")
		objectRef = self.addObject(dabo.ui.dTextBox, NameBase="freight", 
				DataSource="orders", DataField="freight")
			
		gs.append(label, alignment=("top", "right") )	
		gs.append(objectRef, "expand")
		gs.append( (25, 1) )

		gs.setColExpand(True, 1)

		mainSizer.insert(0, gs, "expand", 1, border=20)

		# Add top and bottom margins
		mainSizer.insert( 0, (-1, 10), 0)
		mainSizer.append( (-1, 20), 0)

		self.Sizer.layout()
		self.itemsCreated = True

		self.super()


if __name__ == "__main__":
	from FrmOrders import FrmOrders
	app = dabo.dApp(MainFormClass=None)
	app.setup()
	class TestForm(FrmOrders):
		def afterInit(self): pass
	frm = TestForm(Caption="Test Of PagEditOrders", Testing=True)
	test = frm.addObject(PagEditOrders)
	test.createItems()
	frm.Sizer.append1x(test)
	frm.show()
	app.start()
