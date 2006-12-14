import os
import sys
import wx
import dabo
import dabo.dException as dException
import dabo.dEvents as dEvents
from dabo.dLocalize import _, n_
from dabo.lib.utils import padl
from dabo.dObject import dObject

dabo.ui.loadUI("wx")

from dabo.ui import dPanel
import Grid

IGNORE_STRING, CHOICE_TRUE, CHOICE_FALSE = (n_("-ignore-"),
		n_("Is True"),
		n_("Is False") )

ASC, DESC = (n_("asc"), n_("desc"))

# Controls for the select page:
class SelectControlMixin(dObject):
	def initProperties(self):
		self.super()
		self.SaveRestoreValue = True

class SelectTextBox(SelectControlMixin, dabo.ui.dTextBox): pass
class SelectCheckBox(SelectControlMixin, dabo.ui.dCheckBox): pass
class SelectLabel(SelectControlMixin, dabo.ui.dLabel):
	def afterInit(self):
		# Basically, we don't want anything to display, but it's 
		# easier if every selector has a matching control.
		self.Caption = ""
class SelectDateTextBox(SelectControlMixin, dabo.ui.dDateTextBox): pass
class SelectSpinner(SelectControlMixin, dabo.ui.dSpinner): pass

class SelectionOpDropdown(dabo.ui.dDropdownList):
	def initProperties(self):
		self.super()
		self.SaveRestoreValue = True
		
	def initEvents(self):
		self.super()
		self.bindEvent(dEvents.Hit, self.onChoiceMade)
		self.bindEvent(dEvents.ValueChanged, self.onValueChanged)
		
	def onValueChanged(self, evt):
		# italicize if we are ignoring the field:
		self.FontItalic = (IGNORE_STRING in self.Value)
		if self.Target:
			self.Target.FontItalic = self.FontItalic
		
	def onChoiceMade(self, evt):
		if IGNORE_STRING not in self.StringValue:
			# A comparison op was selected; let 'em enter a value
			self.Target.setFocus()
		
	def _getTarget(self):
		try:
			_target = self._target
		except AttributeError:
			_target = self._target = None
		return _target
			
	def _setTarget(self, tgt):
		self._target = tgt
		if self.Target:
			self.Target.FontItalic = self.FontItalic
		
	Target = property(_getTarget, _setTarget, None, "Holds a reference to the edit control.")
	
				
class Page(dabo.ui.dPage):
	def newRecord(self, ds=None):
		""" Called by a browse grid when the user wants to add a new row. 
		"""
		if ds is None:
			self.Form.new()
			self.editRecord()
		else:
			self.Parent.newByDataSource(ds)
	
		
	def deleteRecord(self, ds=None):
		""" Called by a browse grid when the user wants to delete the current row. 
		"""
		if ds is None:
			self.Form.delete()
		else:
			self.Parent.deleteByDataSource(ds)


	def editRecord(self, ds=None):
		""" Called by a browse grid when the user wants to edit the current row. 
		"""
		if ds is None:
			self.Parent.SetSelection(2)
		else:
			self.Parent.editByDataSource(ds)

		
class SelectOptionsPanel(dPanel):
	""" Base class for the select options panel.
	"""
	def initProperties(self):
		self.Name = "selectOptionsPanel"
		

class SortLabel(dabo.ui.dLabel):
	def initEvents(self):
		super(SortLabel, self).initEvents()
		self.bindEvent(dEvents.MouseRightClick, self.Parent.Parent.onSortLabelRClick)
		# Add a property for the related field
		self.relatedDataField = ""


class SelectPage(Page):
	def _createItems(self):
		self.super()

		## The following line is needed to get the Select page scrollbars to lay
		## out without the user having to resize manually. I tried putting it in
		## dPage but that caused problems with the Class Designer. We need to 
		## figure out the best way to abstract this wx call, or find a different
		## way to get the scrollbars.
		self.Sizer.FitInside(self)


	def afterInit(self):
		super(SelectPage, self).afterInit()
		# Holds info which will be used to create the dynamic
		# WHERE clause based on user input
		self.selectFields = {}
		self.sortFields = {}
		self.sortIndex = 0


	def onSortLabelRClick(self, evt):
		obj = self.sortObj = evt.EventObject
		self.sortDS = obj.relatedDataField
		self.sortCap = obj.Caption
		mn = dabo.ui.dMenu()
		if self.sortFields:
			mn.append(_("Show sort order"), bindfunc=self.handleSortOrder)
		if self.sortFields.has_key(self.sortDS):
			mn.append(_("Remove sort on ") + self.sortCap, 
					bindfunc=self.handleSortRemove)

		mn.append(_("Sort Ascending"), bindfunc=self.handleSortAsc)
		mn.append(_("Sort Descending"), bindfunc=self.handleSortDesc)
		self.PopupMenu(mn, obj.formCoordinates(evt.EventData["mousePosition"]) )
		mn.release()

	def handleSortOrder(self, evt): 
		self.handleSort(evt, "show")
	def handleSortRemove(self, evt): 
		self.handleSort(evt, "remove")
	def handleSortAsc(self, evt):
		self.handleSort(evt, ASC)
	def handleSortDesc(self, evt):
		self.handleSort(evt, DESC)
	def handleSort(self, evt, action):
		if action == "remove":
			try:
				del self.sortFields[self.sortDS]
			except:
				pass
		elif action== "show":
			# Get the descrips and order
			sf = self.sortFields
			sfk = sf.keys()
			dd = [(sf[kk][0], kk, "%s %s" % (sf[kk][2], sf[kk][1]))
					for kk in sfk ]
			dd.sort()
			sortDesc = [itm[2] for itm in dd]
			sortedList = dabo.ui.sortList(sortDesc)
			newPos = 0
			for itm in sortedList:
				origPos = sortDesc.index(itm)
				key = dd[origPos][1]
				self.sortFields[key] = (newPos, self.sortFields[key][1], self.sortFields[key][2])
				newPos += 1
		elif action != "show":
			if self.sortFields.has_key(self.sortDS):
				self.sortFields[self.sortDS] = (self.sortFields[self.sortDS][0], 
						action, self.sortCap)
			else:
				self.sortFields[self.sortDS] = (self.sortIndex, action, self.sortCap)
				self.sortIndex += 1
		self.sortCap = self.sortDS = ""
				
			
		
	def createItems(self):
		self.selectOptionsPanel = self.getSelectOptionsPanel()
		self.GetSizer().append(self.selectOptionsPanel, "expand", 1, border=20)
		self.selectOptionsPanel.setFocus()
		super(SelectPage, self).createItems()
		if self.Form.RequeryOnLoad:
			dabo.ui.callAfter(self.requery)
			

	def setFrom(self, biz):
		"""Subclass hook."""
		pass
	

	def setOrderBy(self, biz):
		biz.setOrderByClause(self._orderByClause())

	def _orderByClause(self, infoOnly=False):
		sf = self.sortFields
		if infoOnly: parts = lambda (k): (sf[k][2], _(sf[k][1]))
		else:        parts = lambda (k): (k, sf[k][1].upper())

		flds = [(self.sortFields[k][0], k, " ".join(parts(k)))
			for k in self.sortFields.keys()]
		flds.sort()
		if infoOnly:
			return [e[1:] for e in flds]
		else:
			return ",".join([ k[2] for k in flds])


	def setWhere(self, biz):
		try:
			baseWhere = biz.getBaseWhereClause()
		except AttributeError:
			# prior datanav apps inherited from dBizobj directly,
			# and dBizobj doesn't define getBaseWhereClause. 
			baseWhere = ""
		biz.setWhereClause(baseWhere)
		tbl = biz.DataSource
		flds = self.selectFields.keys()
		whr = ""
		for fld in flds:
			if fld == "limit":
				# Handled elsewhere
				continue
			
			try:
				## the datanav bizobj has an optional dict that contains
				## mappings from the fld to the actual names of the backend
				## table and field, so that you can have fields in your where
				## clause that aren't members of the "main" table.
				table, field = biz.BackendTableFields[fld]
			except (AttributeError, KeyError):
				table, field = tbl, fld

			opVal = self.selectFields[fld]["op"].Value
			opStr = opVal
			if not IGNORE_STRING in opVal:
				fldType = self.selectFields[fld]["type"]
				ctrl = self.selectFields[fld]["ctrl"]
				if fldType == "bool":
					# boolean fields won't have a control; opVal will
					# be either 'Is True' or 'Is False'
					matchVal = (opVal == CHOICE_TRUE)
				else:
					matchVal = ctrl.Value
				matchStr = "%s" % matchVal
				useStdFormat = True

				if fldType in ("char", "memo"):
					if opVal.lower() in ("equals", "is"):
						opStr = "="
						matchStr = biz.escQuote(matchVal)
					elif opVal.lower() == "matches words":
						useStdFormat = False
						whrMatches = []
						for word in matchVal.split():
							mtch = {"table": table, "field": field, "value": word}
							whrMatches.append( biz.getWordMatchFormat() % mtch )
						if len(whrMatches) > 0:
							whr = " and ".join(whrMatches)
					else:
						# "Begins With" or "Contains"
						opStr = "LIKE"
						if opVal[:1] == "B":
							matchStr = biz.escQuote(matchVal + "%")
						else:
							matchStr = biz.escQuote("%" + matchVal + "%")
							
				elif fldType in ("date", "datetime"):
					if isinstance(ctrl, dabo.ui.dDateTextBox):
						dtTuple = ctrl.getDateTuple()
						dt = "%s-%s-%s" % (dtTuple[0], padl(dtTuple[1]+1, 2, "0"), 
								padl(dtTuple[2], 2, "0") )
					else:
						dt = matchVal
					matchStr = biz.formatDateTime(dt)
					if opVal.lower() in ("equals", "is"):
						opStr = "="
					elif opVal.lower() == "on or before":
						opStr = "<="
					elif opVal.lower() == "on or after":
						opStr = ">="
					elif opVal.lower() == "before":
						opStr = "<"
					elif opVal.lower() == "after":
						opStr = ">"

				elif fldType in ("int", "float"):
					if opVal.lower() in ("equals", "is"):
						opStr = "="
					elif opVal.lower() == "less than/equal to":
						opStr = "<="
					elif opVal.lower() == "greater than/equal to":
						opStr = ">="
					elif opVal.lower() == "less than":
						opStr = "<"
					elif opVal.lower() == "greater than":
						opStr = ">"
						
				elif fldType == "bool":
					opStr = "="
					if opVal == CHOICE_TRUE:
						matchStr = "True"
					else:
						matchStr = "False"
				
				# We have the pieces of the clause; assemble them together
				if useStdFormat:
					whr = "%s.%s %s %s" % (table, field, opStr, matchStr)
				if len(whr) > 0:
					biz.addWhere(whr)
		return

	
	def onRequery(self, evt):
		self.requery()
	
	
	def setLimit(self, biz):
		biz.setLimitClause(self.selectFields["limit"]["ctrl"].Value)
		

	def requery(self):
		frm = self.Form
		bizobj = frm.getBizobj()
		ret = False
		if bizobj is not None:
			sql = frm.CustomSQL
			if sql is not None:
				bizobj.UserSQL = sql
			else:
				# CustomSQL is not defined. Get it from the select page settings:
				bizobj.UserSQL = None
				self.setFrom(bizobj)
				self.setWhere(bizobj)
				self.setOrderBy(bizobj)
				self.setLimit(bizobj)
			
				sql = bizobj.getSQL()
				bizobj.setSQL(sql)
	
			ret = frm.requery()

		if ret:
			if self.Parent.SelectedPageNumber == 0:
				# If the select page is active, now make the browse page active
				self.Parent.SelectedPageNumber = 1
	
	
	def getSelectorOptions(self, typ, wordSearch=False):
		# The fieldspecs version sends the wordSearch parameter as a "1" or "0"
		# string. The following conversion should work no matter what:
		wordSearch = bool(int(wordSearch))
		if typ in ("char", "memo"):
			if typ == "char":
				chcList = [n_("Equals"), 
						n_("Begins With"),
						n_("Contains")]
			elif typ == "memo":
				chcList = [n_("Begins With"),
						n_("Contains")]
			if wordSearch:
				chcList.append(n_("Matches Words"))
			chc = tuple(chcList)
		elif typ in ("date", "datetime"):
			chc = (n_("Equals"),
					n_("On or Before"),
					n_("On or After"),
					n_("Before"),
					n_("After") )
		elif typ in ("int", "float", "decimal"):
			chc = (n_("Equals"), 
					n_("Greater than"),
					n_("Greater than/Equal to"),
					n_("Less than"),
					n_("Less than/Equal to"))
		elif typ == "bool":
			chc = (CHOICE_TRUE, CHOICE_FALSE)
		else:
			dabo.errorLog.write("Type '%s' not recognized." % typ)
			chc = ()
		return chc


	def getSelectOptionsPanel(self):
		if not self.Form.preview:
			dataSource = self.Form.getBizobj().DataSource
		else:
			dataSource = self.Form.previewDataSource
		fs = self.Form.FieldSpecs
		panel = dPanel(self)
		gsz = dabo.ui.dGridSizer(vgap=5, hgap=10)
		gsz.MaxCols = 3
		label = dabo.ui.dLabel(panel)
		label.Caption = _("Please enter your record selection criteria:")
		label.FontSize = label.FontSize + 2
		label.FontBold = True
		gsz.append(label, colSpan=3, alignment="center")
		
		if fs is not None:
			# Get all the fields that should be included into a list. Order them
			# into the order specified in the specs.
			fldList = []
			for fld in fs.keys():
				if int(fs[fld]["searchInclude"]):
					fldList.append( (fld, int(fs[fld]["searchOrder"])) )
			fldList.sort(lambda x, y: cmp(x[1], y[1]))
		
			for fldOrd in fldList:
				fld = fldOrd[0]
				fldInfo = fs[fld]
				lbl = SortLabel(panel)
				lbl.Caption = "%s:" % fldInfo["caption"]
				lbl.relatedDataField = fld
			
				# First try getting the selector options from the user hook:
				opt = self.Form.getSelectOptionsForField(fld)
			
				if opt is None:
					# Automatically get the selector options based on the field type:
					opt = self.getSelectorOptions(fldInfo["type"], fldInfo["wordSearch"])

				# Add the blank choice and create the dropdown:
				opt = (IGNORE_STRING,) + tuple(opt)
				opList = SelectionOpDropdown(panel, choices=opt)
			
				# First try getting the control class from the user hook:
				ctrlClass = self.Form.getSelectControlClassForField(fld)

				if ctrlClass is None:
					# Automatically get the control class based on the field type:
					ctrlClass = self.getSearchCtrlClass(fldInfo["type"])

				if ctrlClass is not None:
					ctrl = ctrlClass(panel)
					if not opList.StringValue:
						opList.StringValue = opList.GetString(0)
					opList.Target = ctrl
				
					gsz.append(lbl, halign="right")
					gsz.append(opList, halign="left")
					gsz.append(ctrl, "expand")
				
					# Store the info for later use when constructing the query
					self.selectFields[fld] = {
							"ctrl" : ctrl,
							"op" : opList,
							"type": fldInfo["type"]
							}
				else:
					dabo.errorLog.write("No control class found for field '%s'." % fld)
					lbl.release()
					opList.release()

				
		# Now add the limit field
		lbl = dabo.ui.dLabel(panel)
		lbl.Caption =  _("&Limit")
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
		gsz.append(requeryButton, row=btnRow, col=1, 
				halign="right", border=3)
		
		# Make the last column growable
		gsz.setColExpand(True, 2)
		panel.SetSizerAndFit(gsz)
		
		vsz = dabo.ui.dSizer("v")
		vsz.append(gsz, 1, "expand")

		return panel


	def onCustomSQL(self, evt):
		cb = evt.EventObject
		bizobj = self.Form.getBizobj()
		if cb.Value:
			# Get default SQL, display to user, and then use whatever the user enters
			sql = self.Form.CustomSQL
			if sql is None:
				# CustomSQL is not defined. Get it from the select page settings:
				bizobj.UserSQL = None
				self.setWhere(bizobj)
				self.setOrderBy(bizobj)
				self.setLimit(bizobj)
			
				sql = bizobj.getSQL()

			dlg = dabo.ui.dDialog(self, Caption=_("Set Custom SQL"))
			eb = dlg.addObject(dabo.ui.dEditBox, Value=sql, Size=(400, 400), FontFace="Monospace")
			dlg.Sizer.append1x(eb)
			dlg.show()
			self.Form.CustomSQL = eb.Value
			dlg.release()
			
		else:
			# Clear the custom SQL
			self.Form.CustomSQL = None

	
	def getSearchCtrlClass(self, typ):
		"""Returns the appropriate editing control class for the given data type.
		"""
		if typ in ("char", "memo", "float", "int", "decimal", "datetime"):
			return SelectTextBox
		elif typ == "bool":
			return SelectLabel
		elif typ == "date":
			return SelectDateTextBox
		return None
	
	
class BrowsePage(Page):
	def __init__(self, parent):
		super(BrowsePage, self).__init__(parent, Name="pageBrowse")
		self._doneLayout = False


	def initEvents(self):
		super(BrowsePage, self).initEvents()
		self.bindEvent(dEvents.PageEnter, self.__onPageEnter)


	def __onPageEnter(self, evt):
		self.updateGrid()
		if not self._doneLayout:
			self._doneLayout = True
			self.Form.Height += 1
			self.Layout()
			self.Form.Height -= 1
		if self.Form.SetFocusToBrowseGrid:
			self.BrowseGrid.setFocus()


	def updateGrid(self):
		bizobj = self.Form.getBizobj()
		if not self.itemsCreated:
			self.createItems()
			self.fillGrid(False)
		if self.Form.preview:
			self.fillGrid(False)
		else:
			if bizobj and bizobj.RowCount >= 0:
				self.fillGrid(False)
				self.BrowseGrid.update()

		
	def createItems(self):
		bizobj = self.Form.getBizobj()
		grid = self.Form.BrowseGridClass(self, NameBase="BrowseGrid", Size=(10,10))
		grid.FieldSpecs = self.Form.FieldSpecs
		if not self.Form.preview:
			pass
			#grid.setBizobj(bizobj)
			grid.DataSource = bizobj.DataSource
		else:
			grid.DataSource = self.Form.previewDataSource
		self.Sizer.append(grid, 2, "expand")
		self.itemsCreated = True
	

	def fillGrid(self, redraw=False):
		self.BrowseGrid.populate()
		self.layout()
		

class EditPage(Page):
	def __init__(self, parent, ds=None):
		super(EditPage, self).__init__(parent)		#, Name="pageEdit")
		self._focusToControl = None
		self.itemsCreated = False
		self._dataSource = ds
		self.childGrids = []
		self.childrenAdded = False
		if self.DataSource:
			self.buildPage()

			
	def initEvents(self):
		super(EditPage, self).initEvents()
		self.bindEvent(dEvents.PageEnter, self.__onPageEnter)
		self.bindEvent(dEvents.PageLeave, self.__onPageLeave)
		self.Form.bindEvent(dEvents.RowNumChanged, self.__onRowNumChanged)
	
	
	def buildPage(self):
		if not self.DataSource:
			return
		self.fieldSpecs = self.Form.getFieldSpecsForTable(self.DataSource)
		self.createItems()


	def __onRowNumChanged(self, evt):
		for cg in self.childGrids:
			cg.populate()


	def __onPageLeave(self, evt):
		self.Form.setPrimaryBizobjToDefault(self.DataSource)
	
	
	def __onPageEnter(self, evt):
		self.Form.PrimaryBizobj = self.DataSource
		focusToControl = self._focusToControl
		if focusToControl is not None:
			focusToControl.setFocus()
			self._focusToControl = None
		# The current row may have changed. Make sure that the
		# values are current
		self.__onRowNumChanged(None)
		

	def createItems(self):
		fs = self.fieldSpecs
		relationSpecs = self.Form.RelationSpecs
		if fs is None:
			return
		showEdit = [ (fld, int(fs[fld]["editOrder"])) 
				for fld in fs
				if (fs[fld]["editInclude"] == "1")]
		showEdit.sort(lambda x, y: cmp(x[1], y[1]))
		mainSizer = self.GetSizer()
		firstControl = None
		gs = dabo.ui.dGridSizer(vgap=5, maxCols=3)
		
		for fld in showEdit:
			fieldName = fld[0]
			fldInfo = fs[fieldName]
			fieldType = fldInfo["type"]
			cap = fldInfo["caption"]
			fieldEnabled = (fldInfo["editReadOnly"] != "1")
			
			label = dabo.ui.dLabel(self)		#, style=labelStyle)
			label.NameBase="lbl%s" % fieldName 

			# Hook into user's code in case they want to control the object displaying
			# the data:
			classRef = self.Form.getEditClassForField(fieldName)
			if classRef is None:
				# User didn't supply a class, so derive it based on field type:
				if fieldType in ["memo",]:
					classRef = dabo.ui.dEditBox
				elif fieldType in ["bool",]:
					classRef = dabo.ui.dCheckBox
				elif fieldType in ["date",]:
					#pkm: temporary: dDateTextBox is misbehaving still. So, until we get
					#     it figured out, change the type of control used for date editing
					#     to a raw dTextBox, which can handle viewing/setting dates but 
					#     doesn't have all the extra features of dDateTextBox. (2005/08/28)
					#classRef = dabo.ui.dDateTextBox
					classRef = dabo.ui.dTextBox
				else:
					classRef = dabo.ui.dTextBox

			objectRef = classRef(self)
			objectRef.NameBase = fieldName
			objectRef.DataSource = self.DataSource
			objectRef.DataField = fieldName
			objectRef.enabled = fieldEnabled
			
			if fieldEnabled and firstControl is None:
				firstControl = objectRef
			
			if classRef == dabo.ui.dCheckBox:
				# Use the label for a spacer, but don't set the 
				# caption because checkboxes have their own caption.
				label.Caption = ""
				objectRef.Caption = cap
			else:
				label.Caption = "%s:" % cap

			if not self.Form.preview:
				if self.Form.getBizobj().RowCount >= 0:
					pass

			gs.append(label, alignment=("top", "right") )
			if fieldType in ["memo",]:
				# Get the row that these will be added
				currRow = gs.findFirstEmptyCell()[0]
				gs.setRowExpand(True, currRow)
			gs.append(objectRef, "expand")
			gs.append( (25, 1) )
		gs.setColExpand(True, 1)

		childGridCount = 0

		if not self.childrenAdded:
			self.childrenAdded = True
			# If there is a child table, add it
			for rkey in relationSpecs.keys():
				rs = relationSpecs[rkey]
				if rs["source"].lower() == self.DataSource.lower():
					childGridCount += 1
					child = rs["target"]
					childBiz = self.Form.getBizobj(child)
					grdLabel = self.addObject(dabo.ui.dLabel, "lblChild" + child)
					grdLabel.Caption = _(self.Form.getBizobj(child).Caption)
					grdLabel.FontSize = 14
					grdLabel.FontBold = True
					#mainSizer.append( (10, -1) )
					mainSizer.append(grdLabel, 0, "expand", alignment="center", 
							border=10, borderSides=("left", "right") )
					grid = self.addObject(Grid.Grid, "BrowseGrid" + child)
					grid.FieldSpecs = self.Form.getFieldSpecsForTable(child)
					grid.DataSource = child
					self.childGrids.append(grid)
					grid.populate()
					#grid.Height = 100
				
					mainSizer.append(grid, 1, "expand", border=10,
							borderSides=("left", "right") )
		
		if childGridCount == 0:
			# Let the edit fields expand normally.
			gsProportion = 1
		else:
			# Each of the child grids got proportions of 1 in the above block,
			# so they'll size equally. Because the presence of even one child grid
			# is going to likely push the grid off the bottom, requiring a scroll,
			# minimize that as much as possible by not allowing the non-grid controls 
			# to expand.
			### For some reason, this is preventing the scroll panels from display
			### the grids properly. So set this back to one for now.
			gsProportion = 2	#0
		mainSizer.insert(0, gs, "expand", gsProportion, border=20)

		# Add top and bottom margins
		mainSizer.insert( 0, (-1, 10), 0)
		mainSizer.append( (-1, 20), 0)

		self.Sizer.layout()
		self.itemsCreated = True
		self._focusToControl = firstControl

	def _getDS(self):
		return self._dataSource
	def _setDS(self, val):
		self._dataSource = val
		if not self.itemsCreated:
			self.buildPage()
			
	DataSource = property(_getDS, _setDS, None,
			_("Table that is the primary source for the fields displayed on the page  (str)") )

