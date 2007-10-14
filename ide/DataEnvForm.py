# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from DataEnvWizard import DataEnvWizard


class DEForm(dabo.ui.dForm):
	def __init__(self, parent, de={}, *args, **kwargs):
		super(DEForm, self).__init__(parent=parent, panel=True, *args, **kwargs)
		self.Caption = "Data Environment"
		sz = self.Sizer
		sz.Orientation = "v"
		sz.DefaultSpacing = 4
		sz.DefaultBorder = 20
		sz.DefaultBorderLeft = sz.DefaultBorderRight = True
		self.tblSelector = None
		self.lstFields = None		
		self._tables = None
		self._currTable = None
		self._DE = {}
		if de:
			self.setDE(de)
				
	
	def setDE(self, de):
		self._DE = de
		self._tables = de.keys()
		self.setControls()
	
	
	def setControls(self):
		""" Create a dropdown selector for the various tables 
		in the DE. Below that will be a list control that will be refreshed 
		with the field info for the selected table. It will be multi-select, 
		so that the user may only select certain fields to add to the form. 
		In any case, clicking on the 'Add to Form' button will bring up 
		a dialog/wizard where the user will finalize their selections, 
		setting captions, control type, order, etc.
		"""
		sz = self.Sizer
		tb = self.tblSelector
		if not tb:
			tb = self.tblSelector = dabo.ui.dDropdownList(self)
			sz.prepend(tb, alignment="center")
			# Add a label
			lbl = dabo.ui.dLabel(self, Caption="Tables")
			sz.prepend(lbl, alignment="center")
			tb.bindEvent(dabo.dEvents.Hit, self.onTableSelection)
			sz.prependSpacer(20)
		tb.Choices = self. _tables
		tb.PositionValue = 0
		
		# Now create the field list if needed, and populate it with the 
		# selected table's fields
		if not self.lstFields:
			lbl = dabo.ui.dLabel(self, Caption="Fields")
			sz.append(lbl, 0, alignment="center")
			lst = self.lstFields = dabo.ui.dListControl(self, MultiSelect=True)
			lst.setColumns( ("PK", "Type", "Name") )
			lst.setColumnWidth(0, 30)
			sz.append(lst, 1, "x")
			btnSz = dabo.ui.dSizer("h")
			btnSz.DefaultSpacing = 10
			btnAll = dabo.ui.dButton(self, Caption="Select All")
			btnAll.bindEvent(dEvents.Hit, self.onSelectAll)
			btnSz.append(btnAll, 1, "x")
			btnNone = dabo.ui.dButton(self, Caption="Select None")
			btnNone.bindEvent(dEvents.Hit, self.onSelectNone)
			btnSz.append(btnNone, 1, "x")
			sz.append(btnSz, 0, "x")
			sz.appendSpacer(20)
		
		self.onTableSelection(None)
		btn = dabo.ui.dButton(self, Caption="Add ... ")
		sz.append(btn, alignment="center")
		btn.bindEvent(dEvents.Hit, self.onAdd)
	
	
	def onTableSelection(self, evt):
		"""Populate the field list control with a list of the fields in the 
		selected table.
		"""
		self._currTable = self.tblSelector.Value
		self.lstFields.clear()
		# Create the items for the list
		fldDict = self._DE[self._currTable]
		flds = fldDict.keys()
		flds.sort()
		pktext={True:"X", False:""}
		typeText = {"C" : "char", "I": "int", "M" : "text", "D" : "date", 
				"T" : "datetime", "B" : "bool", "N" : "float", "E" : "enum"}
		fldInfo = [ (pktext[fldDict[p]["pk"]], typeText[fldDict[p]["type"]], p ) for p in flds]
		self.lstFields.appendRows(fldInfo)

	
	def onAdd(self, evt):
		"""Run the wizard for adding fields"""
		wiz = DataEnvWizard()
		wiz.DE = self._DE
		
		wiz.start()
	
	def onSelectAll(self, evt):
		self.lstFields.selectAll()
		
		
	def onSelectNone(self, evt):
		self.lstFields.unselectAll()
