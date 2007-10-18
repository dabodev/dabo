# -*- coding: utf-8 -*-

import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _, n_
from PagSelectBase import PagSelectBase, IGNORE_STRING, SelectTextBox, \
		SelectCheckBox, SelectLabel, SelectDateTextBox, SelectSpinner, \
		SelectionOpDropdown, SortLabel


class PagSelectCustomer(PagSelectBase):
	def getSelectOptionsPanel(self):
		"""Return the panel to contain all the select options."""
		# The base behavior will build the panel automatically from the fieldspecs,
		# if available. If fieldspecs isn't available, all the base behavior will
		# give you is the limit clause.

		panel = dabo.ui.dPanel(self)
		gsz = dabo.ui.dGridSizer(VGap=5, HGap=10)
		gsz.MaxCols = 3
		label = dabo.ui.dLabel(panel)
		label.Caption = _("Please enter your record selection criteria:")
		label.FontSize = label.FontSize + 2
		label.FontBold = True
		gsz.append(label, colSpan=3, alignment="center")

		##
		## Field customer.company
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Company:"
		lbl.relatedDataField = "company"

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
				opList.StringValue = opList.GetString(0)
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["company"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'company'.")
			lbl.release()
			opList.release()


		##
		## Field customer.city
		##
		lbl = SortLabel(panel)
		lbl.Caption = "City:"
		lbl.relatedDataField = "city"

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
				opList.StringValue = opList.GetString(0)
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["city"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'city'.")
			lbl.release()
			opList.release()


		##
		## Field customer.postalcode
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Postal Code:"
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
				opList.StringValue = opList.GetString(0)
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
		## Field customer.country
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Country:"
		lbl.relatedDataField = "country"

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
				opList.StringValue = opList.GetString(0)
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["country"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "char"
					}
		else:
			dabo.errorLog.write("No control class found for field 'country'.")
			lbl.release()
			opList.release()


		##
		## Field customer.maxordamt
		##
		lbl = SortLabel(panel)
		lbl.Caption = "Max. Order Amt.:"
		lbl.relatedDataField = "maxordamt"

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
				opList.StringValue = opList.GetString(0)
			opList.Target = ctrl
				
			gsz.append(lbl, halign="right")
			gsz.append(opList, halign="left")
			gsz.append(ctrl, "expand")
				
			# Store the info for later use when constructing the query
			self.selectFields["maxordamt"] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": "float"
					}
		else:
			dabo.errorLog.write("No control class found for field 'maxordamt'.")
			lbl.release()
			opList.release()

		# Now add the limit field
		lbl = dabo.ui.dLabel(panel)
		lbl.Caption =  _("&Limit:")
		limTxt = SelectTextBox(panel)
		if len(limTxt.Value) == 0:
			limTxt.Value = "1000"
		self.selectFields["limit"] = {"ctrl" : limTxt	}
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
		panel.SetSizerAndFit(gsz)
		
		vsz = dabo.ui.dSizer("v")
		vsz.append(gsz, 1, "expand")

		return panel

