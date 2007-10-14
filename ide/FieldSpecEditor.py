#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" FieldSpecEditor.py

This application will read in a field spec XML file and allow the user
to edit any of the fields in it. 
"""

import os
import sys
import re
import dabo
from dabo.lib.specParser import importFieldSpecs
import dabo.dEvents as dEvents
import dabo.dConstants as k
import dabo.lib.datanav as datanav
dabo.ui.loadUI("wx")


class FieldSpecGrid(dabo.ui.dGrid):
	""" This grid is responsible for displaying the current settings of the 
	fieldSpecs.xml file for a table in the current app. Each row in the grid
	will contain the settings for a field in the table, which control how the
	field is displayed in the app, or whether it is displayed at all.
	
	This grid is also responsible for reversing the process when requested
	by its form: given the current state of its cell contents, it will generate
	a dictionary like the one it was created from. The form will use this 
	generated dict to save the modified settings back into XML form.
	"""
	def __init__(self, parent, tblDict=None):
		self.tblDict = tblDict

		FieldSpecGrid.doDefault(parent)
		
		self.SetColMinimalAcceptableWidth(0)


	def afterInit(self):
		# We want the users to be able to edit!
		self.Editable = True
		# Create the columns for the grid
		colClass = dabo.ui.dColumn
		# Set the custom list for the 'type' field
		
		self.colTypes = {"editReadOnly": bool, "editInclude": bool, 
				"searchInclude": bool, "wordSearch": bool, "listInclude": bool, 
				"listOrder": int, "listColWidth": int, "searchOrder": int, "editOrder": int, 
				"type": str, "caption": str}

		col = colClass(self, Caption="Field\nType", DataType="list", Editable=True,
				Name="col_FieldType", Order=10, DataField="type", Width=75,
				ListEditorChoices=["char", "memo", "int", "float", "bool", "date", "datetime"])
		self.addColumn(col)
		col = colClass(self, Caption="\nCaption", DataType="string",  Editable=True,
				Name="col_Caption", Order=20, DataField="caption", Width=150)
		self.addColumn(col)
		col = colClass(self, Caption="Search\nPage?", DataType="bool",  Editable=True,
				Name="col_searchInclude", Order=30, DataField="searchInclude", Width=75)
		self.addColumn(col)
		col = colClass(self, Caption="Search\nOrder", DataType="int",  Editable=True,
				Name="col_searchOrder", Order=40, DataField="searchOrder", Width=75)
		self.addColumn(col)
		col = colClass(self, Caption="Word\nSearch?", DataType="bool",  Editable=True,
				Name="col_wordSearch", Order=50, DataField="wordSearch", Width=75)
		self.addColumn(col)
		col = colClass(self, Caption="List\nWidth", DataType="int",  Editable=True,
				Name="col_listColWidth", Order=60, DataField="listColWidth", Width=75)
		self.addColumn(col)
		col = colClass(self, Caption="List\nPage?", DataType="bool",  Editable=True,
				Name="col_listInclude", Order=70, DataField="listInclude", Width=75)
		self.addColumn(col)
		col = colClass(self, Caption="List\nOrder", DataType="int",  Editable=True,
				Name="col_listOrder", Order=80, DataField="listOrder", Width=75)
		self.addColumn(col)
		col = colClass(self, Caption="Edit\nPage?", DataType="bool",  Editable=True,
				Name="col_editInclude", Order=90, DataField="editInclude", Width=75)
		self.addColumn(col)
		col = colClass(self, Caption="Edit\nOrder", DataType="int",  Editable=True,
				Name="col_editOrder", Order=100, DataField="editOrder", Width=75)
		self.addColumn(col)
		col = colClass(self, Caption="Read\nOnly?", DataType="bool",  Editable=True,
				Name="col_editReadOnly", Order=110, DataField="editReadOnly", Width=75)
		self.addColumn(col)
		
		# We want the row labels to be visible
		self.ShowRowLabels = True
		# Headers need to be a bit bigger than the default
		self.HeaderHeight += 10
		
		td = self.tblDict
		if td is not None:
			self.RowLabels = []
			self.DataSet = []

			for fld in td.keys():
				self.RowLabels.append(fld)
				rec = td[fld]
				recVals = {}
				for att in rec.keys():
					typ = self.colTypes[att]
					if typ == bool:
						recVals[att] = (rec[att] != "0")
					elif typ == int:
						recVals[att] = int(rec[att])
					else:
						recVals[att] = rec[att]

				self.DataSet.append(recVals)
		self.fillGrid()
		
	
	def getCurrentValues(self):
		""" Returns a dictionary containing the current state of the edited values
		for each field in the grid.
		"""
		ret = {}
		boolConv = {True : u"1", False : u"0"}
		# Cycle through all of the fields
		for row in range(self.RowCount):
			fld = self.GetRowLabelValue(row)
			ret[fld] = {}
			for colNum in range(self.ColumnCount):
				prop = self.Columns[colNum].DataField
				val = self.GetCellValue(row, colNum)
				if type(val) == bool:
					val = boolConv[val]
				else:
					val = unicode(val)
				ret[fld][prop] = val
		return ret
		

	def onGridHeaderMouseLeftDoubleClick(self, evt):
		evt.stop()
		x,y = evt.EventData["mousePosition"]
		orderCol = self.getColNumByX(x)
		colLabel = self.Columns[orderCol].Caption.replace("\n", " ")
		
		# If the user just changed something, the change might still
		# be buffered in the cell editor. Force it to flush.
		self.SetGridCursor(self.GetGridCursorRow(), self.GetGridCursorCol())
		
		attr = ""
		if colLabel == "Search Order":
			attr = "searchOrder"
		elif colLabel == "List Order":
			attr = "listOrder"
		elif colLabel == "Edit Order":
			attr = "editOrder"
		if not attr:
			# Some column we don't care about
			return
		# There is a corresponding attribute that determines if the field
		# is included in the search at all.
		incl = attr.replace("Order", "Include")
		inclCol = [col for col in self.Columns
				if col.DataField == incl]
		rowNums = {}
		for row in range(self.RowCount):
			rowNums[self.RowLabels[row]] = row
		
		cv = self.getCurrentValues()
		sortList = [ (cv[ky]["caption"] + " (" + ky + ")", int(cv[ky][attr])) 
				for ky in cv.keys()
				if cv[ky][incl] == "1" ]
		notIncluded = [ ky for ky in cv.keys() if cv[ky][incl] != "1" ]

		# Sort on current ordering, which is the second element.
		sortList.sort(lambda x,y: x[1] - y[1])
		# Now create the list of fields
		origFlds = [ f[0] for f in sortList ]
		# Run the ordering form. It will return a new list with the new order
		# unless the user canceled.
		newFlds = dabo.ui.sortList(origFlds, Caption="Change " + colLabel)
		if newFlds != origFlds:
			# The user made changes and then clicked 'OK'
			fldPat = re.compile("[^\(]+\(([^\)]+)\)")
			currOrder = 0
			for fldData in newFlds:
				fld = fldPat.search(fldData).groups()[0]
				if rowNums.has_key(fld):
					self.cell(rowNums[fld], orderCol).Value = currOrder
				currOrder += 10
			# Now set the non-included fields to high values
			currOrder = 999
			for fld in notIncluded:
				if rowNums.has_key(fld):
					self.cell(rowNums[fld], orderCol).Value = currOrder
				currOrder -= 1


class EditorForm(dabo.ui.dForm):
	def initProperties(self):
		EditorForm.doDefault()
		self.Caption = "Dabo Field Spec Editor: <Filename here> [*]"
		self.debug = True  # output verbose 
		self.specFile = None
		# Dict of available preview forms
		self.previewForms = {}
		# See if we've checked if the user wants to save their changes
		self.askedToSave = False
		
		self.Width = 950
		self.Height = 440
		
		# temp hack to be polymorphic with dEditor:
		self.editor = self
		
		# This is the main dictionary that holds all the field spec data.
		# There will be an element for each table in the app. Each of those
		# elements will be a dictionary, with one element for each field.
		# Each field will have several properties that affect how it appears
		# (or doesn't appear) on each part of the form. 
		self.mainDict = {}
		
		# As the user selects different tables and fields, these will be 
		# updated to reflect the current selection.
		self.currTableDict = {}
		self.currFieldDict = {}
		
	def openFile(self, specFile=None):
		self.specFile = specFile
		# Read in the field spec file

		if self.specFile:
			# Make sure that the passed file exists!
			if not os.path.exists(self.specFile):
				dabo.errorLog.write("The spec file '%s' does not exist." % self.specFile)
				self.specFile = None
				
		if self.specFile is None:
			f = dabo.ui.getFile("fsxml", "*", defaultPath=os.getcwd())
			if f is not None:
				self.specFile = f
			
		if self.specFile is not None:
			## pkm: OpenDlg.GetPath() returns Unicode, which on my machine  
			##	results in the importFieldSpecs failing.
			self.specFile = str(self.specFile)
			
			# Read the XML into a local dictionary
			self.mainDict = importFieldSpecs(self.specFile)
		
			# Create the form controls. The design will be one page per table.
			# Each page will contain a list/grid with a summary for each field.
			# Selecting a row in the grid updates a set of editable controls so
			# that a user can change the settings for any field.
			self.instantiateControls()
			self.Caption = "Dabo Field Spec Editor: %s" % self.specFile
			return True
		else:
			return False
		
		
	def initEvents(self):
		EditorForm.doDefault()
		self.bindEvent(dEvents.Close, self.__onClose)
	
		
	def __onClose(self, evt):
		if not self.askedToSave:
			currDict = self.getCurrentValues()
			if currDict != self.mainDict:
				resp = dabo.ui.areYouSure(message="Do you want to save your changes?", 
						title = "Save Changes")
				if resp is None:
					# User pressed 'Cancel'
					evt.Continue = False
					return
				if resp:
					self.save(currDict)
				self.askedToSave = True
	
	
	def getCurrentValues(self):
		ret = {}
		for pgNum in range(self.pgf.PageCount):
			pg = self.pgf.GetPage(pgNum)
			tbl = pg.Caption
			grd = [k for k in pg.GetChildren() if isinstance(k, dabo.ui.dGrid)][0]
			grd.SaveEditControlValue()
			ret[tbl] = grd.getCurrentValues()
		return ret
	

	def saveTmp(self, filename):
		holdSpecFile = self.specFile
		self.specFile = filename
		self.save()
		self.specFile = holdSpecFile
		
	
	def save(self, vals=None):
		if vals is None:
			vals = self.getCurrentValues()
			
		tblTemplate = self.getTableTemplate()
		fldTemplate = self.getFieldTemplate()
		
		tableXML = ""
		for tbl in vals.keys():
			tblData = vals[tbl]
			flds = tblData.keys()
			fieldXML = ""
			for fld in flds:
				fldData = tblData[fld]
				# Make these record zeros for False instead of the default ""
				sInc = fldData["searchInclude"]
				if not sInc:
					sInc = "0"
				eInc = fldData["editInclude"]
				if not eInc:
					eInc = "0"
				lInc = fldData["listInclude"]
				if not lInc:
					lInc = "0"
				wInc = fldData["wordSearch"]
				if not wInc:
					wInc = "0"
				fldVals = (fld, fldData["type"], fldData["caption"], sInc, 
						fldData["searchOrder"], wInc, lInc, 
						fldData["listColWidth"], fldData["listOrder"], eInc, 
						fldData["editReadOnly"], fldData["editOrder"])
				fieldXML += fldTemplate % fldVals
			tableXML += tblTemplate % (tbl, fieldXML)
			
		xml = self.getBaseXML() % tableXML
		open(self.specFile, "w").write(xml)
		return


	def instantiateControls(self):
		labelWidth = 150
		labelAlignment = "right"
		
		# Create the pageframe
		self.pgf = dabo.ui.dPageFrame(self)
		tbls = self.mainDict.keys()
		tbls.sort()
		self.pgf.PageCount = len(tbls)
		pgNum = 0
		# Small defaults
		self.minHt = 10
		self.minWd = 10
		
		for tbl in tbls:
			pg = self.pgf.GetPage(pgNum)
			pg.Caption = tbl
			pgNum += 1
			
			lbl = dabo.ui.dLabel(pg, Caption="Editing Form for table: " + tbl, 
					FontSize=14, FontBold=True, ForeColor="darkblue")
			
			lblOrd = dabo.ui.dLabel(pg, 
					Caption="Double-click the headers of the Order columns to edit",
					FontSize=9, FontItalic=True)
			
			hsz = dabo.ui.dSizer("h")
			hsz.append(lbl, 1, halign="left")
			hsz.append(lblOrd, halign="right", valign="bottom")
			
			grd = FieldSpecGrid(pg, self.mainDict[tbl])
			pgsz = pg.Sizer
			pgsz.append(hsz, 0, "expand", halign="center",
					valign="bottom", border=20, borderSides=("top", "left", "right") )
			pgsz.appendSpacer(10)
			pgsz.append(grd, 1, "expand" )
			pg.layout()
			
		
		btn = dabo.ui.dButton(self, Caption="  Preview Form  ", 
				RegID="PreviewButton")
		
		sz = dabo.ui.dSizer("vertical")
		sz.append(self.pgf, 5, "expand")
		sz.append(btn, 0, halign="centre" )
		self.Sizer = sz
		# Need to do this to force the layout
		self.Width += 1
		sz.layout()


	def onHit_PreviewButton(self, evt):
		evt.stop()
		tbl = self.pgf.GetPageText(self.pgf.GetSelection())
		tmpSpecFile = "./.tmpSpec.xml"
		self.saveTmp(tmpSpecFile)
		
		create = True
		if self.previewForms.has_key(tbl):
			if isinstance(self.previewForms[tbl], datanav.Form):
				create = False
		if create:
			self.previewForms[tbl] = datanav.Form(self, previewMode=True, tbl=tbl)
		prev = self.previewForms[tbl]

		prev.Caption = tbl + " - Preview"
		prev.setFieldSpecs(tmpSpecFile, tbl)
		prev.creation()
		prev.Show(True)
		
		prev.Raise()
		
		os.remove(tmpSpecFile)
		

	def getBaseXML(self):
		ret = """<?xml version="1.0" encoding="%s" standalone="no"?>
<daboAppSpecs>
%s
</daboAppSpecs>
""" % (dabo.defaultEncoding, "%s")
		return ret
		
	def getTableTemplate(self):
		return """	<table name="%s">
		<fields>
%s
		</fields>
	</table>
"""

	def getFieldTemplate(self):
		return """			<field name="%s" type="%s" caption="%s" 
				searchInclude="%s" searchOrder="%s" wordSearch="%s"
				listInclude="%s" listColWidth="%s" listOrder="%s"
				editInclude="%s" editReadOnly="%s" editOrder="%s"  />
"""






if __name__ == "__main__":
	files = sys.argv[1:]
	app = dabo.dApp()
	app.MainFormClass = None
	app.setup()

	for file in files:
		o = EditorForm()
		o.openFile(file)
		if o.specFile:
			o.Show()
		else:
			o.Close()
			
	if len(files) == 0:
		# The form has code to prompt the user for a file to edit
		o = EditorForm()
		o.openFile(None)
		if o.specFile:
			o.Show()
		else:
			o.Close()
			
	app.start()
	
