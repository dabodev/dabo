IGNORE_STRING = "-ignore-"
CHOICE_TRUE = "Is True"
CHOICE_FALSE = "Is False"

import wx
import dabo
import dabo.ui
import dabo.dException as dException
import dabo.dEvents as dEvents
from dabo.dLocalize import _, n_

dabo.ui.loadUI("wx")

from dabo.ui import dPanel
import Grid

IGNORE_STRING, CHOICE_TRUE, CHOICE_FALSE = (n_("-ignore-"),
					    n_("Is True"),
					    n_("Is False")
					    )

# Controls for the select page:
class SelectControlMixin(dabo.common.dObject):
	def initProperties(self):
		SelectControlMixin.doDefault()
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
		SelectionOpDropdown.doDefault()
		self.SaveRestoreValue = True
		
	def initEvents(self):
		SelectionOpDropdown.doDefault()
		self.bindEvent(dEvents.Hit, self.onChoiceMade)
		self.bindEvent(dEvents.ValueChanged, self.onValueChanged)
		
	def onValueChanged(self, evt):
		# italicize if we are ignoring the field:
		self.FontItalic = (IGNORE_STRING in self.StringValue)
		if self.Target:
			self.Target.FontItalic = self.FontItalic
		
	def onChoiceMade(self, evt):
		if IGNORE_STRING not in self.StringValue:
			# A comparison op was selected; let 'em enter a value
			self.Target.SetFocus()
		
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
	def afterInit(self):
		super(Page, self).afterInit()
		# Needed for drawing sizer outlines
		self.redrawOutlines = False
		self.bindEvent(dEvents.Resize, self.onResize)
		self.bindEvent(dEvents.Paint, self.onResize)
		self.bindEvent(dEvents.Idle, self.onIdle)

	def editRecord(self, ds=None):
		""" Called by a browse grid when the user wants 
		to edit the current row. 
		"""
		if ds is None:
			# Old code; default to the first editing page
			self.Parent.SetSelection(2)
		else:
			self.Parent.editByDataSource(ds)

		
	def onResize(self, evt):
		self.redrawOutlines = self.Form.drawSizerOutlines
		
	def onIdle(self, evt):
		if self.redrawOutlines:
			self.redrawOutlines = False
			self.drawOutline(self, self.GetSizer(), 0)

	def drawOutline(self, win, sz, level):
		if sz is None:
			return
		x, y = sz.GetPosition()
		w, h = sz.GetSize()
		off = 1
		
		if isinstance(sz, wx.NotebookSizer):
			nb = sz.GetNotebook()
			for i in range(nb.GetPageCount()):
				pg = nb.GetPage(i)
				self.drawOutline(pg, pg.GetSizer(), level+1)
		else:
			chil = sz.GetChildren()
			for c in chil:
				if c.IsSizer():
					self.drawOutline(win, c.GetSizer(), level+1)
# 				elif c.IsSpacer():
# 					self.drawOutline(win, c.GetSpacer(), level+1)
				else:
					# Window
					subwin = c.GetWindow()
					if subwin is not None:
						self.drawOutline(subwin, subwin.GetSizer(), level+1) 

		# Initialize the draw client
		dc = wx.ClientDC(win)
		if isinstance(sz, wx.NotebookSizer):
			dc.SetPen(wx.Pen("green", 1, wx.SOLID))
		if isinstance(sz, wx.NotebookSizer):
			dc.SetPen(wx.Pen("green", 1, wx.SOLID))
		else:
			if isinstance(sz, wx.GridBagSizer):
				# This is necessary due to a bug in the subclassing of the
				# wx.GridBagSizer class.
				self.drawGridBagSizerOutline(win, sz)
			else:
				sz.drawOutline(win)


	def drawGridBagSizerOutline(self, win, sz):
		""" This is a hack to get around the bug in wxPython where
		subclasses of wx.GridBagSizer added to another sizer lose their 
		subclass info, and revert to the base wx.GridBagSizer class.
		"""
		dc = wx.ClientDC(win)
		dc.SetBrush(wx.TRANSPARENT_BRUSH)
		dc.SetLogicalFunction(wx.COPY)
		x, y = sz.GetPosition()
		w, h = sz.GetSize()
		rows = sz.GetRows()
		cols = sz.GetCols()
		vgap = sz.GetVGap()
		hgap = sz.GetHGap()
		x2,y2 = x,y
		rhts = sz.GetRowHeights()
		dc.SetPen(wx.Pen("blue", 1, wx.SOLID))
		for hh in rhts:
			dc.DrawRectangle(x2, y2, w, hh)
			y2 += hh+vgap
		x2 = x
		y2 = y
		cwds = sz.GetColWidths()
		dc.SetPen(wx.Pen("red", 1, wx.SOLID))
		for ww in cwds:
			dc.DrawRectangle(x2, y2, ww, h)
			x2 += ww+hgap
		dc.SetPen(wx.Pen("green", 3, wx.LONG_DASH))
		dc.DrawRectangle(x,y,w,h)


class SelectOptionsPanel(dPanel):
	""" Base class for the select options panel.
	"""
	def initProperties(self):
		self.Name = "selectOptionsPanel"
		# selectOptions is a list of dictionaries
		self.selectOptions = []
		

class SortLabel(dabo.ui.dLabel):
	def initEvents(self):
		super(SortLabel, self).initEvents()
		self.bindEvent(dEvents.MouseRightClick, self.Parent.Parent.onSortLabelRClick)
		# Add a property for the related field
		self.relatedDataField = ""
		
		
class SelectPage(Page):
	def afterInit(self):
		super(SelectPage, self).afterInit()
		# Holds info which will be used to create the dynamic
		# WHERE clause based on user input
		self.selectFields = {}
		self.sortFields = {}
		self.sortIndex = 0


	def onSortLabelRClick(self, evt):
		self.sortDS = evt.EventObject.relatedDataField
		self.sortCap = evt.EventObject.Caption
		self.sortObj = evt.GetEventObject()
		mn = dMenu.dMenu()
		if self.sortFields.has_key(self.sortDS):
			mn.append("Remove sort on " + self.sortCap, 
			          bindfunc=self.handleSortRemove)

		mn.append("Sort Ascending", bindfunc=self.handleSortAsc)
		mn.append("Sort Descending", bindfunc=self.handleSortDesc)
		self.PopupMenu(mn, self.ClientToScreen(evt.GetPosition()) )
		mn.release()

	def handleSortRemove(self, evt): 
		self.handleSort(evt.GetId(), "remove")
	def handleSortAsc(self, evt): 
		self.handleSort(evt.GetId(), "asc")
	def handleSortDesc(self, evt):
		self.handleSort(evt.GetId(), "desc")
	def handleSort(self, id, action):
		if action == "remove":
			try:
				del self.sortFields[self.sortDS]
			except:
				pass
		else:
			if self.sortFields.has_key(self.sortDS):
				self.sortFields[self.sortDS] = (self.sortFields[self.sortDS][0], 
						action, self.sortCap)
			else:
				self.sortFields[self.sortDS] = (self.sortIndex, action, self.sortCap)
				self.sortIndex += 1
		self.sortCap = self.sortDS = ""
		displayList = [(self.sortFields[k][0], 
				self.sortFields[k][2] + " " + self.sortFields[k][1].upper())
				for k in self.sortFields.keys()]
		displayList.sort()
		display = [ k[1] for k in displayList ]
		dabo.ui.dMessageBox.info("\n".join(display))
		
		
		
	def createItems(self):
		self.selectOptionsPanel = self._getSelectOptionsPanel()
		self.GetSizer().append(self.selectOptionsPanel, "expand", 1, border=20)
		self.selectOptionsPanel.SetFocus()
		#SelectPage.doDefault()
		super(SelectPage, self).createItems()
		if self.Form.RequeryOnLoad:
			self.requery()

	
	def setOrderBy(self, biz):
		flds = self.selectFields.keys()
		clause = ""
		for fld in flds:
			break
			if fld == "limit":
				# Not used
				continue
			orderVal = self.selectFields[fld]["order"].Value
			if orderVal:
				if clause:
					clause += ", "
				clause += fld + " " + orderVal
		biz.setOrderByClause(clause)
		

	def setWhere(self, biz):
		biz.setWhereClause("")
		flds = self.selectFields.keys()
		whr = ""
		for fld in flds:
			if fld == "limit":
				# Handled elsewhere
				continue
			
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
				matchStr = str(matchVal)
				useStdFormat = True

				if fldType in ("char", "memo"):
					if opVal == "Equals":
						opStr = "="
						matchStr = biz.escQuote(matchVal)
					elif opVal == "Matches Words":
						useStdFormat = False
						whrMatches = []
						for word in matchVal.split():
							mtch = {"field":fld, "value":word}
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
						dt = "%s-%s-%s" % (dtTuple[0], padl(dtTuple[1], 2, "0"), 
								padl(dtTuple[2], 2, "0") )
					else:
						dt = matchVal
					matchStr = biz.formatDateTime(dt)
					if opVal == "Equals":
						opStr = "="
					elif opVal == "On or Before":
						opStr = "<="
					elif opVal == "On or After":
						opStr = ">="
					elif opVal == "Before":
						opStr = "<"
					elif opVal == "After":
						opStr = ">"

				elif fldType in ("int", "float"):
					if opVal == "Equals":
						opStr = "="
					elif opVal == "Less than/Equal to":
						opStr = "<="
					elif opVal == "Greater than/Equal to":
						opStr = ">="
					elif opVal == "Less than":
						opStr = "<"
					elif opVal == "Greater than":
						opStr = ">"
						
				elif fldType == "bool":
					opStr = "="
					if opVal == CHOICE_TRUE:
						matchStr = "True"
					else:
						matchStr = "False"
				
				# We have the pieces of the clause; assemble them together
				if useStdFormat:
					whr = "%s %s %s" % (fld, opStr, matchStr)
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
			self.setWhere(bizobj)
			self.setOrderBy(bizobj)
			self.setLimit(bizobj)
			
			# The bizobj will get the SQL from the sql builder:
			sql = bizobj.getSQL()
	
			# But it won't automatically use that sql, so we set it here:
			bizobj.setSQL(sql)
	
			ret = frm.requery()

		if ret:
			if self.GetParent().GetSelection() == 0:
				# If the select page is active, now make the browse page active
				self.GetParent().SetSelection(1)
	
	
	def getSelectorOptions(self, typ, ws):
		if typ in ("char", "memo"):
			if typ == "char":
				chcList = [n_("Equals"), 
					   n_("Begins With"),
					   n_("Contains")
					   ]
			elif typ == "memo":
				chcList = [n_("Begins With"),
					   n_("Contains")
					   ]
			if ws != "0":
				chcList.append(n_("Matches Words"))
			chc = tuple(chcList)
		elif typ in ("date", "datetime"):
			chc = (n_("Equals"),
			       n_("On or Before"),
			       n_("On or After"),
			       n_("Before"),
			       n_("After")
			       )
		elif typ in ("int", "float", "decimal"):
			chc = (n_("Equals"), 
			       n_("Greater than"),
			       n_("Greater than/Equal to"),
			       n_("Less than"),
			       n_("Less than/Equal to")
			       )
		elif typ == "bool":
			chc = (CHOICE_TRUE, CHOICE_FALSE)
		else:
			dabo.errorLog.write("Type '%s' not recognized." % typ)
			chc = ()
		# Add the blank choice
		chc = (IGNORE_STRING,) + chc
		return chc


	def _getSelectOptionsPanel(self):
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
			
			opt = self.getSelectorOptions(fldInfo["type"], fldInfo["wordSearch"])
			opList = SelectionOpDropdown(panel, choices=opt)
			
			ctrl = self.getSearchCtrl(fldInfo["type"], panel)
			if ctrl is not None:
				if not opList.StringValue:
					opList.StringValue = opList.GetString(0)
				opList.Target = ctrl
				
				gsz.append(lbl, alignment="right")
				gsz.append(opList, alignment="left")
				gsz.append(ctrl, "expand")
				
				# Store the info for later use when constructing the query
				self.selectFields[fld] = {
						"ctrl" : ctrl,
						"op" : opList,
						"type": fldInfo["type"]
						}
			else:
				dabo.errorLog.write("No control found for type '%s'." % fldInfo["type"])
				lbl.release()
				opList.release()

				
		# Now add the limit field
		lbl = dabo.ui.dLabel(panel)
		lbl.Caption =  _("&Limit")
		limTxt = SelectTextBox(panel)
		if len(limTxt.Value) == 0:
			limTxt.Value = "1000"
		self.selectFields["limit"] = {"ctrl" : limTxt	}
		requeryButton = dabo.ui.dButton(panel)
		requeryButton.Caption =  _("&Requery")
		requeryButton.DefaultButton = True
		requeryButton.bindEvent(dEvents.Hit, self.onRequery)
		
		gsz.append(lbl, alignment="right")
		gsz.append(limTxt)
		btnRow = gsz.findFirstEmptyCell()[0] + 1
		gsz.append(requeryButton, "expand", row=btnRow, col=1, 
				alignment="right")
		
		# Make the last column growable
		gsz.setColExpand(True, 2)
		panel.SetSizerAndFit(gsz)
		
		vsz = dabo.ui.dSizer("v")
		vsz.append(gsz, 1, "expand")

		return panel


	
	def getSearchCtrl(self, typ, parent):
		"""Returns the appropriate editing control for the given data type.
		"""
		if typ in ("char", "memo", "float", "int", "decimal", "datetime"):
			ret = SelectTextBox(parent)
		elif typ == "bool":
			#ret = SelectCheckBox(parent)
			ret = SelectLabel(parent)
		elif typ == "date":
			ret = SelectDateTextBox(parent)
		else:
			ret = None
		return ret
	
	
class BrowsePage(Page):
	def __init__(self, parent):
		super(BrowsePage, self).__init__(parent, Name="pageBrowse")
		self._doneLayout = False

	def initEvents(self):
		super(BrowsePage, self).initEvents()
		self.Form.bindEvent(dEvents.RowNumChanged, self.__onRowNumChanged)
		self.bindEvent(dEvents.PageEnter, self.__onPageEnter)
		

	def __onRowNumChanged(self, evt):
		# If RowNumChanged is received AND we are the active page, select
		# the row in the grid.
		
		# If we aren't the active page, strange things can happen if we
		# don't explicitly SetFocus back to the active page. 
		activePage = self.Parent.GetPage(self.Parent.GetSelection())
		if activePage == self:
			self.updateGrid()
		else:
			activePage.SetFocus()


	def updateGrid(self):
		bizobj = self.Form.getBizobj()
		justCreated = False
		
		if not self.itemsCreated:
			self.createItems()
			justCreated = True
		if self.Form.preview:
			if self.itemsCreated:
				self.fillGrid(True)
		else:
			if bizobj and bizobj.RowCount >= 0:
				if self.itemsCreated:
					self.fillGrid(True)

		
	def __onPageEnter(self, evt):
		self.updateGrid()
		if not self._doneLayout:
			self._doneLayout = True
			self.Form.Height += 1
			self.Layout()
			self.Form.Height -= 1


	def createItems(self):
		bizobj = self.Form.getBizobj()
		grid = self.addObject(Grid.Grid, "BrowseGrid")
		grid.fieldSpecs = self.Form.FieldSpecs
		if not self.Form.preview:
			grid.setBizobj(bizobj)
			grid.DataSource = bizobj.DataSource
		else:
			grid.DataSource = self.Form.previewDataSource
		self.GetSizer().append(grid, 2, "expand")
		
		preview = self.addObject(dabo.ui.dButton, "cmdPreview")
		preview.Caption = _("Print Preview")
		preview.bindEvent(dEvents.Hit, self.onPreview)
		self.GetSizer().append(preview, 0)		
		self.itemsCreated = True
	

	def fillGrid(self, redraw=False):
		self.BrowseGrid.fillGrid(redraw)
		self.Layout()
		for window in self.BrowseGrid.GetChildren():
			window.SetFocus()


	def newRecord(self):
		self.Form.new()
		self.editRecord()
	
		
	def deleteRecord(self):
		self.Form.delete()

	
	def onPreview(self, evt):
		if self.itemsCreated:
			if self.Form.preview:
				# Just previewing 
				dabo.ui.dMessageBox.info(message="Not available in preview mode", 
						title = "Preview Mode")
				return
			import wx.html
			html = self.BrowseGrid.getHTML(justStub=False)
			win = wx.html.HtmlEasyPrinting("Dabo Quick Print", self.Form)
			printData = win.GetPrintData()
			setupData = win.GetPageSetupData()
			#printData.SetPaperId(wx.PAPER_LETTER)
			setupData.SetPaperId(wx.PAPER_LETTER)
			if self.BrowseGrid.GetNumberCols() > 20:
				printData.SetOrientation(wx.LANDSCAPE)
			else:
				printData.SetOrientation(wx.PORTRAIT)
			#setupData.SetMarginTopLeft((17,7))
			#s#etupData.SetMarginBottomRight((17,5))
	#       # setupData.SetOrientation(wx.LANDSCAPE)
			win.SetHeader("<B>%s</B>" % (self.Form.Caption,))
			win.SetFooter("<CENTER>Page @PAGENUM@ of @PAGESCNT@</CENTER>")
			#win.PageSetup()
			win.PreviewText(html)

			
class EditPage(Page):
	def __init__(self, parent, ds=None):
		super(EditPage, self).__init__(parent)		#, Name="pageEdit")
		self.dataSource = ds
		self.childGrids = []
		self.childrenAdded = False
		if ds is None:
			self.fieldSpecs = self.Form.FieldSpecs
			if not self.Form.preview:
				self.dataSource = self.Form.getBizobj().DataSource
			else:
				self.dataSource = ""
		else:
			self.fieldSpecs = self.Form.getFieldSpecsForTable(ds)
		self.createItems()

	def initEvents(self):
		super(EditPage, self).initEvents()
		self.bindEvent(dEvents.PageEnter, self.__onPageEnter)
		self.bindEvent(dEvents.PageLeave, self.__onPageLeave)
		self.bindEvent(dEvents.ValueRefresh, self.__onValueRefresh)
		self.Form.bindEvent(dEvents.RowNumChanged, self.__onRowNumChanged)
		
	def __onRowNumChanged(self, evt):
		for cg in self.childGrids:
			cg.fillGrid(True)

	def __onPageLeave(self, evt):
		self.Form.setPrimaryBizobjToDefault(self.dataSource)
		
	def __onPageEnter(self, evt):
		self.Form.setPrimaryBizobj(self.dataSource)

		
		self.__onValueRefresh()
		# The current row may have changed. Make sure that the
		# values are current
		self.__onRowNumChanged(None)

	def __onValueRefresh(self, evt=None):
		form = self.Form
		bizobj = form.getBizobj(self.dataSource)
		if bizobj and bizobj.RowCount >= 0:
			self.Enable(True)
		else:
			self.Enable(False)

	
	def createItems(self):
		fs = self.fieldSpecs
		relationSpecs = self.Form.RelationSpecs
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
			label.Name="lbl%s" % fieldName 

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
					classRef = dabo.ui.dDateTextBox
				else:
					classRef = dabo.ui.dTextBox

			objectRef = classRef(self)
			objectRef.Name = fieldName
			objectRef.DataSource = self.dataSource
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
					objectRef.refresh()

			gs.append(label, alignment=("top", "right") )
			if fieldType in ["memo",]:
				# Get the row that these will be added
				currRow = gs.findFirstEmptyCell()[0]
				gs.setRowExpand(True, currRow)
			gs.append(objectRef, "expand")
			gs.append( (25, 1) )
		
		gs.setColExpand(True, 1)
		mainSizer.append(gs, "expand", 1, border=20)

		if not self.childrenAdded:
			self.childrenAdded = True
			# If there is a child table, add it
			for rkey in relationSpecs.keys():
				rs = relationSpecs[rkey]
				if rs["source"].lower() == self.dataSource.lower():
					child = rs["target"]
					childBiz = self.Form.getBizobj(child)
					grdLabel = self.addObject(dabo.ui.dLabel, "lblChild" + child)
					grdLabel.Caption = child.title()
					grdLabel.FontSize = 14
					grdLabel.FontBold = True
					mainSizer.append( (10, -1) )
					mainSizer.append(grdLabel, 0, "expand", alignment="center", 
							border=10, borderFlags=("left", "right") )
					grid = self.addObject(Grid.Grid, "BrowseGrid")
					grid.fieldSpecs = self.Form.getFieldSpecsForTable(child)
					grid.DataSource = child
					grid.setBizobj(childBiz)
					self.childGrids.append(grid)
					grid.fillGrid()
					grid.Height = 100
					for window in grid.GetChildren():
						window.SetFocus()
					mainSizer.append(grid, 2, "expand", border=10,
							borderFlags=("left", "right") )
			
		# Add top and bottom margins
		mainSizer.insert( 0, (-1, 10), 0)
		mainSizer.append( (-1, 20), 0)

		self.GetSizer().Layout()
		self.itemsCreated = True
		if firstControl is not None:
			firstControl.SetFocus()



# For convenience		
def padl(string, length, fill=" "):
	string = str(string)[:length]
	return (fill * (length-len(string)) ) + string
		

