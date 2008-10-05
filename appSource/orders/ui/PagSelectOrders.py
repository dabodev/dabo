# -*- coding: utf-8 -*-

import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _, n_
from PagSelectBase import PagSelectBase, IGNORE_STRING, SelectTextBox, \
		SelectCheckBox, SelectLabel, SelectDateTextBox, SelectSpinner, \
		SelectionOpDropdown, SortLabel


class PagSelectOrders(PagSelectBase):


	def getSelectOptionsPanel(self):
		"""Return the panel to contain all the select options."""

		panel = dabo.ui.dPanel(self)
		gsz = dabo.ui.dGridSizer(VGap=5, HGap=10)
		gsz.MaxCols = 3
		label = dabo.ui.dLabel(panel)
		label.Caption = _("Please enter your record selection criteria:")
		label.FontSize = label.FontSize + 2
		label.FontBold = True
		gsz.append(label, colSpan=3, alignment="center")

		##
		## Field orders.to_name
		##
		lbl = SortLabel(panel)
		lbl.Caption = "To:"
		lbl.relatedDataField = "to_name"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("char", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("char")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["to_name"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'to_name'.")
			lbl.release()
			opList.release()


		##
		## Field orders.to_address
		##
		lbl = SortLabel(panel)
		lbl.Caption = "To Address:"
		lbl.relatedDataField = "to_address"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("char", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("char")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["to_address"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'to_address'.")
			lbl.release()
			opList.release()


		##
		## Field orders.to_city
		##
		lbl = SortLabel(panel)
		lbl.Caption = "To City:"
		lbl.relatedDataField = "to_city"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("char", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("char")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["to_city"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'to_city'.")
			lbl.release()
			opList.release()


		##
		## Field orders.to_region
		##
		lbl = SortLabel(panel)
		lbl.Caption = "To Region:"
		lbl.relatedDataField = "to_region"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("char", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("char")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["to_region"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'to_region'.")
			lbl.release()
			opList.release()


		##
		## Field orders.postalcode
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Postalcode:"
		lbl.relatedDataField = "postalcode"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("char", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("char")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["postalcode"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'postalcode'.")
			lbl.release()
			opList.release()


		##
		## Field orders.to_country
		##
		lbl = SortLabel(panel)
		lbl.Caption = "To Country:"
		lbl.relatedDataField = "to_country"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("char", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("char")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["to_country"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'to_country'.")
			lbl.release()
			opList.release()


		##
		## Field orders.ship_count
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Ship Count:"
		lbl.relatedDataField = "ship_count"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("char", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("char")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["ship_count"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'ship_count'.")
			lbl.release()
			opList.release()


		##
		## Field orders.ship_via
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Ship Via:"
		lbl.relatedDataField = "ship_via"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("char", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("char")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["ship_via"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'ship_via'.")
			lbl.release()
			opList.release()


		##
		## Field orders.order_date
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Order Date:"
		lbl.relatedDataField = "order_date"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("date", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("date")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["order_date"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "date"
					}
		else:
			dabo.errorLog.write("No control class found for field 'order_date'.")
			lbl.release()
			opList.release()


		##
		## Field orders.order_amt
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Amount:"
		lbl.relatedDataField = "order_amt"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("float", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("float")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["order_amt"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "float"
					}
		else:
			dabo.errorLog.write("No control class found for field 'order_amt'.")
			lbl.release()
			opList.release()


		##
		## Field orders.order_dsc
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Description:"
		lbl.relatedDataField = "order_dsc"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("int", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("int")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["order_dsc"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "int"
					}
		else:
			dabo.errorLog.write("No control class found for field 'order_dsc'.")
			lbl.release()
			opList.release()


		##
		## Field orders.order_net
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Net:"
		lbl.relatedDataField = "order_net"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("float", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("float")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["order_net"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "float"
					}
		else:
			dabo.errorLog.write("No control class found for field 'order_net'.")
			lbl.release()
			opList.release()


		##
		## Field orders.require_by
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Required Date:"
		lbl.relatedDataField = "require_by"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("date", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("date")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["require_by"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "date"
					}
		else:
			dabo.errorLog.write("No control class found for field 'require_by'.")
			lbl.release()
			opList.release()


		##
		## Field orders.shipped_on
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Ship Date:"
		lbl.relatedDataField = "shipped_on"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("date", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("date")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["shipped_on"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "date"
					}
		else:
			dabo.errorLog.write("No control class found for field 'shipped_on'.")
			lbl.release()
			opList.release()


		##
		## Field orders.freight
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Freight Charge:"
		lbl.relatedDataField = "freight"

		# Automatically get the selector options based on the field type:
		opt = self.getSelectorOptions("float", wordSearch=False)

		# Add the blank choice and create the dropdown:
		opt = (IGNORE_STRING,) + tuple(opt)
		opList = SelectionOpDropdown(panel, Choices=opt)
			
		# Automatically get the control class based on the field type:
		ctrlClass = self.getSearchCtrlClass("float")

		if ctrlClass is not None:
			ctrl = ctrlClass(panel)
			if not opList.StringValue:
				opList.PositionValue = 0
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["freight"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "float"
					}
		else:
			dabo.errorLog.write("No control class found for field 'freight'.")
			lbl.release()
			opList.release()

		# Now add the limit field
		lbl = dabo.ui.dLabel(panel)
		lbl.Caption =  _("&Limit:")
		limTxt = SelectTextBox(panel)
		if len(limTxt.Value) == 0:
			limTxt.Value = "1000"
		self.selectFields["limit"] = {"ctrl" : limTxt}
		gsz.append(lbl, alignment="right")
		gsz.append(limTxt)

		# Custom SQL checkbox:
		chkCustomSQL = panel.addObject(dabo.ui.dCheckBox, Caption="Use Custom SQL")
		chkCustomSQL.bindEvent(dEvents.Hit, self.onCustomSQL)
		gsz.append(chkCustomSQL)

		# Requery button:
		requeryButton = dabo.ui.dButton(panel)
		requeryButton.Caption =  _("&Requery")
		requeryButton.DefaultButton = True
		requeryButton.bindEvent(dEvents.Hit, self.onRequery)
		btnRow = gsz.findFirstEmptyCell()[0] + 1
		gsz.append(requeryButton, "expand", row=btnRow, col=1, 
				halign="right", border=3)
		
		# Make the last column growable
		gsz.setColExpand(True, 2)
		panel.Sizer = gsz
		
		vsz = dabo.ui.dSizer("v")
		vsz.append(gsz, 1, "expand")
		return panel





if __name__ == "__main__":
	from FrmOrders import FrmOrders
	app = dabo.dApp(MainFormClass=None)
	app.setup()
	class TestForm(FrmOrders):
		def afterInit(self): pass
	frm = TestForm(Caption="Test Of PagSelectOrders", Testing=True)
	test = frm.addObject(PagSelectOrders)
	test.createItems()
	frm.Sizer.append1x(test)
	frm.show()
	app.start()
