import wx, dabo
import dPage, dTextBox, dLabel, dEditBox, dCheckBox, dSpinner
import dMessageBox, dIcons, dCommandButton, dDropdownList
import dPanel, dDataNavGrid, dDateTextBox
import dabo.dException as dException
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class OutlineBoxSizer(wx.BoxSizer):
	def __init__(self, win, *args, **kwargs):
		wx.BoxSizer.__init__(self, *args, **kwargs)
		self.win = win
# 		win.Bind(wx.EVT_SIZE, self.onSize)
	
	def onSize(self, evt):
		evt.Skip()
		self.win.drawOutline(self.GetPosition(), self.GetSize() )
		

class DataNavPage(dPage.dPage):
	def afterInit(self):
		DataNavPage.doDefault()
		# Needed for drawing sizer outlines
		self.redrawOutlines = self.drawSizerOutlines = False
		self.Bind(wx.EVT_SIZE, self.onSize)
		self.Bind(wx.EVT_IDLE, self.onIdle)


	def onSize(self, evt):
		self.redrawOutlines = self.drawSizerOutlines
		evt.Skip()
		
	def onIdle(self, evt):
		if self.redrawOutlines:
			self.redrawOutlines = False
			self.drawOutline(self, self.GetSizer(), 0)
	
	def onPaint(self, evt):
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
		elif isinstance(sz, wx.BoxSizer):
			if sz.GetOrientation() == wx.HORIZONTAL:
				dc.SetPen(wx.Pen("red", 1, wx.SHORT_DASH))
			else:
				dc.SetPen(wx.Pen("blue", 1, wx.SHORT_DASH))
		else:
			dc.SetPen(wx.Pen("cyan", 1, wx.TRANSPARENT))
		dc.SetBrush(wx.TRANSPARENT_BRUSH)
		dc.SetLogicalFunction(wx.COPY)
		# Draw the outline
		dc.DrawRectangle( x+off, y+off, w-(2*off), h-(2*off) )
		# If this is a GridBag Sizer, draw the cells
		if isinstance(sz, wx.GridBagSizer):
			import random
			rows = sz.GetRows()
			cols = sz.GetCols()
			colors = ["red","blue","green", "cyan"]
			dc.SetPen(wx.Pen("blue", 1, wx.SOLID))
			vgap = sz.GetVGap()
			hgap = sz.GetHGap()
			y2 = y
			rhts = sz.GetRowHeights()
 			for hh in rhts:
 				x2 = x
 				for ww in sz.GetColWidths():
 					dc.DrawRectangle(x2, y2, ww, hh)
 					x2 += ww+hgap
 				y2 += hh+vgap
 				clr = random.choice(colors)
 				dc.SetPen(wx.Pen(clr, 1, wx.SOLID))
 
		
class SelectOptionsPanel(dPanel.dPanel):
	""" Base class for the select options panel.
	"""
	def initProperties(self):
		self.Name = "selectOptionsPanel"
		# selectOptions is a list of dictionaries
		self.selectOptions = []
		

class SelectionOpDropdown(dDropdownList.dDropdownList):
	def __init__(self, *args, **kwargs):
		SelectionOpDropdown.doDefault(*args, **kwargs)
		self.target = None
		self.Bind(wx.EVT_CHOICE, self.onChoiceMade)
	
	def setTarget(self, tgt):
		""" Sets the reference to the object that will receive focus
		after a choice is made with this control.
		"""
		self.target = tgt
		
	def onChoiceMade(self, evt):
		if self.target is not None:
			try:
				# If this has been cleared, clear the target field, too
				if not self.GetStringSelection():
					valtype = type(self.target.Value)
					if valtype == type(""):
						self.target.Value = ""
					if valtype == type(u""):
						self.target.Value = u""
					elif valtype == type(True):
						self.target.Value = False
					if valtype == type(0):
						self.target.Value = 0
					if valtype == type(0.0):
						self.target.Value = 0.0
				else:
					# A comparison op was selected; let 'em enter a value
					self.target.SetFocus()
			except: pass


class dSelectPage(DataNavPage):
	def __init__(self, parent):
		dSelectPage.doDefault(parent, name="pageSelect")
		# Holds info which will be used to create the dynamic
		# WHERE clause based on user input
		self.selectFields = {}


	def createItems(self):
		self.selectOptionsPanel = self._getSelectOptionsPanel()
		self.GetSizer().Add(self.selectOptionsPanel, 0, wx.GROW|wx.ALL, 20)
		self.selectOptionsPanel.SetFocus()
		dSelectPage.doDefault()

	
	def setWhere(self, biz):
		biz.setWhereClause("")
		flds = self.selectFields.keys()
		for fld in flds:
			if fld == "limit":
				# Handled elsewhere
				continue
			opVal = self.selectFields[fld]["op"].Value
			opStr = opVal
			if opVal:
				fldType = self.selectFields[fld]["type"]
				ctrl = self.selectFields[fld]["ctrl"]
				matchVal = ctrl.Value
				matchStr = str(matchVal)
				
				if fldType in ("char", "memo"):
					if opVal == "Equals":
						opStr = "="
						matchStr = biz.escQuote(matchVal)
					else:
						# "Begins With" or "Contains"
						opStr = "LIKE"
						if opVal[:1] == "B":
							matchStr = biz.escQuote(matchVal + "%")
						else:
							matchStr = biz.escQuote("%" + matchVal + "%")
							
				elif fldType in ("date", "datetime"):
					dtTuple = ctrl.getDateTuple()
					dt = "%s-%s-%s" % (dtTuple[0], padl(dtTuple[1], 2, "0"), 
							padl(dtTuple[2], 2, "0") )
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
					matchStr = "True"
					if opVal == "Is False":
						opStr = "False"
				
				# We have the pieces of the clause; assemble them together
				whr = "%s %s %s" % (fld, opStr, matchStr)
				biz.addWhere(whr)
		return

	
	def onRequery(self, evt):
		self.requery()
		evt.Skip()
	
	
	def setLimit(self, biz):
		biz.setLimitClause(self.selectFields["limit"]["ctrl"].Value)
		

	def requery(self):
		bizobj = self.Form.getBizobj()
		if bizobj is not None:
			self.setWhere(bizobj)
			self.setLimit(bizobj)
			
			# The bizobj will get the SQL from the sql builder:
			sql = bizobj.getSQL()
	
			if self.debug:
				dabo.infoLog.write("\n%s\n" % sql)
			
			# But it won't automatically use that sql, so we set it here:
			bizobj.setSQL(sql)
	
			self.Form.requery()

		if self.GetParent().GetSelection() == 0:
			# If the select page is active, now make the browse page active
			self.GetParent().SetSelection(1)
	
	
	def getSelectorOptions(self, typ):
		if typ == "char":
			chc = ("Equals", 
					"Begins With",
					"Contains")
		elif typ == "memo":
			chc = ("Begins With",
					"Contains")
		elif typ in ("date", "datetime"):
			chc = ("Equals",
					"On or Before",
					"On or After",
					"Before",
					"After")
		elif typ in ("int", "float"):
			chc = ("Equals", 
					"Greater than",
					"Greater than/Equal to",
					"Less than",
					"Less than/Equal to")
		elif typ == "bool":
			chc = ("Is True",
					"Is False")
		# Add the blank choice
		chc = ("",) + chc
		return chc


	def _getSelectOptionsPanel(self):
		if not self.Form.preview:
			dataSource = self.Form.getBizobj().DataSource
		else:
			dataSource = self.Form.previewDataSource
		fs = self.Form.FieldSpecs
		panel = dPanel.dPanel(self)
		gsz = wx.GridBagSizer(vgap=5, hgap=10)

		label = dLabel.dLabel(panel)
		label.Caption = _("Please enter your record selection criteria:")
		label.FontSize = label.FontSize + 2
		gsz.Add(label, (0,0), (1,3), wx.ALIGN_CENTER | wx.ALL, 5)

		# Get all the fields that should be included into a list. Order them
		# into the order specified in the specs.
		fldList = []
		for fld in fs.keys():
			if int(fs[fld]["searchInclude"]):
				fldList.append( (fld, int(fs[fld]["searchOrder"])) )
		fldList.sort(lambda x, y: cmp(x[1], y[1]))
		gridRow = 0
		for fldOrd in fldList:
			gridRow += 1
			fld = fldOrd[0]
			fldInfo = fs[fld]
			lbl = dLabel.dLabel(panel)
			lbl.Caption = fldInfo["caption"]
			ctrl = self.getSearchCtrl(fldInfo["type"], panel)
			
			opt = self.getSelectorOptions(fldInfo["type"])
			opList = SelectionOpDropdown(panel, choices=opt)
			opList.setTarget(ctrl)
			
			gsz.Add(lbl, (gridRow, 0), flag=wx.RIGHT )
			gsz.Add(opList, (gridRow, 1), flag=wx.CENTRE )
			gsz.Add(ctrl, (gridRow, 2), flag=wx.EXPAND )
			# Store the info for later use when constructing the query
			self.selectFields[fld] = {
					"ctrl" : ctrl,
					"op" : opList,
					"type": fldInfo["type"]
					}
		# Now add the limit field
		lbl = dLabel.dLabel(panel)
		lbl.Caption = "Limit:"
		limTxt = dTextBox.dTextBox(panel)
		limTxt.Value = "1000"
		self.selectFields["limit"] = {"ctrl" : limTxt	}
		requeryButton = dCommandButton.dCommandButton(panel)
		requeryButton.Caption = "&%s" % _("Requery")
		requeryButton.Default = True             # Doesn't work on Linux, but test on win/mac
		requeryButton.Bind(wx.EVT_BUTTON, self.onRequery)
		gridRow += 1
		gsz.Add(lbl, (gridRow, 0), flag=wx.RIGHT )
		gsz.Add(limTxt, (gridRow, 1), flag=wx.EXPAND )
		gridRow += 1
		gsz.Add(requeryButton, (gridRow, 2), flag=wx.RIGHT )
		
		# Make the last column growable
		gsz.AddGrowableCol(2)
		panel.SetSizerAndFit(gsz)
#		panel.SetAutoLayout(True)
#		gsz.Fit(panel)

		return panel


	
	def getSearchCtrl(self, typ, parent):
		""" Returns the appropriate editing control for the 
		given data type.
		"""
		if typ in ("char", "memo", "float", "int"):
			ret = dTextBox.dTextBox(parent)
			ret.Value = ""
		elif typ == "bool":
			ret = dCheckBox.dCheckBox(parent)
			ret.Caption = ""
		elif typ == "date":
			ret = dDateTextBox.dDateTextBox(parent)
		return ret


		
class dBrowsePage(DataNavPage):
	def __init__(self, parent):
		dBrowsePage.doDefault(parent, "pageBrowse")


	def initEvents(self):
		dBrowsePage.doDefault()
		self.Form.bindEvent(dEvents.RowNumChanged, self.onRowNumChanged)
		

	def onRowNumChanged(self, evt):
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
		row = col = 0
		
		if self.Form.preview:
			if not self.itemsCreated:
				self.createItems()
				justCreated = True
			if self.itemsCreated:
				self.fillGrid()
		else:
			if bizobj and bizobj.RowCount >= 0:
				if not self.itemsCreated:
					self.createItems()
					justCreated = True
				if self.itemsCreated:
					self.fillGrid()

			row = self.Form.getBizobj().RowNumber
			col = self.BrowseGrid.GetGridCursorCol()
			
		col = max(0, col)
		
		# Needed on Linux to get the grid to have the focus:
		for window in self.BrowseGrid.GetChildren():
			window.SetFocus()
		
		# Needed on win and mac to get the grid to have the focus:
		self.BrowseGrid.GetGridWindow().SetFocus()
		
		if  not self.BrowseGrid.IsVisible(row, col):
			self.BrowseGrid.MakeCellVisible(row, col)
			self.BrowseGrid.MakeCellVisible(row, col)
		self.BrowseGrid.SetGridCursor(row, col)

		
	def onPageEnter(self, evt):
		self.updateGrid()
		dBrowsePage.doDefault(evt)


	def createItems(self):
		bizobj = self.Form.getBizobj()
		grid = self.addObject(dDataNavGrid.dDataNavGrid, "BrowseGrid")
		grid.fieldSpecs = self.Form.FieldSpecs
		if not self.Form.preview:
			grid.DataSource = bizobj.DataSource
		else:
			grid.DataSource = self.Form.previewDataSource
		self.GetSizer().Add(grid, 1, wx.EXPAND)
		preview = self.addObject(dCommandButton.dCommandButton, "cmdPreview")
		preview.Caption = "Print Preview"
		preview.Bind(wx.EVT_BUTTON, self.onPreview)
		self.GetSizer().Add(preview, 0, 0)
		
		self.itemsCreated = True


	def fillGrid(self):
		bizobj = self.Form.getBizobj()
		self.BrowseGrid.fillGrid()
		self.Layout()
		for window in self.BrowseGrid.GetChildren():
			window.SetFocus()


	def newRecord(self):
		self.Form.new()
		self.editRecord()
	
		
	def deleteRecord(self):
		self.Form.delete()

	
	def editRecord(self):
		# Called by the grid: user wants to edit the current row
		self.GetParent().SetSelection(2)

		
	def onPreview(self, evt):
		if self.itemsCreated:
			if self.Form.preview:
				# Just previewing 
				dMessageBox.info(message="Not available in preview mode", 
						title = "Preview Mode")
				return
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

			
class dEditPage(DataNavPage):
	def __init__(self, parent):
		dEditPage.doDefault(parent, "pageEdit")


	def onPageEnter(self, evt):
		self.onValueRefresh()
		dEditPage.doDefault(evt)


	def onValueRefresh(self, evt=None):
		form = self.Form
		bizobj = form.getBizobj()
		if bizobj and bizobj.RowCount >= 0:
			self.Enable(True)
		else:
			self.Enable(False)
	
	
	def createItems(self):
		if not self.Form.preview:
			dataSource = self.Form.getBizobj().DataSource
		else:
			dataSource = ""
		fieldSpecs = self.Form.FieldSpecs
		
		showEdit = [ (fld, fieldSpecs[fld]["editOrder"]) 
				for fld in fieldSpecs
				if fieldSpecs[fld]["editInclude"] == "1"]
		showEdit.sort(lambda x, y: cmp(x[1], y[1]))
		mainSizer = self.GetSizer()
		
		for fld in showEdit:
			fieldName = fld[0]
			fldInfo = fieldSpecs[fieldName]
			fieldType = fldInfo["type"]
			cap = fldInfo["caption"]
			fieldEnabled = (fldInfo["editReadOnly"] != "1")

			bs = wx.BoxSizer(wx.HORIZONTAL)
			labelWidth = 150
			labelStyle = wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE
			label = dLabel.dLabel(self, style=labelStyle)
			label.Name="lbl%s" % fieldName 
			label.Width = labelWidth
			
			if fieldType in ["memo",]:
				classRef = dEditBox.dEditBox
			elif fieldType in ["bool",]:
				classRef = dCheckBox.dCheckBox
			elif fieldType in ["date",]:
				classRef = dDateTextBox.dDateTextBox
			else:
				classRef = dTextBox.dTextBox

			objectRef = classRef(self)
			objectRef.Name = fieldName
			objectRef.DataSource = dataSource
			objectRef.DataField = fieldName
			objectRef.enabled = fieldEnabled
			
			if classRef == dCheckBox.dCheckBox:
				# Use the label for a spacer, but don't set the 
				# caption because checkboxes have their own caption.
				label.Caption = ""
				objectRef.Caption = cap
			else:
				label.Caption = "%s:" % cap

			if not self.Form.preview:
				if self.Form.getBizobj().RowCount >= 0:
					objectRef.refresh()

			if fieldType in ["memo",]:
				expandFlags = wx.EXPAND
			else:
				expandFlags = 0
			bs.Add(label, 0, wx.ALIGN_CENTER_VERTICAL, 2)
			bs.Add(objectRef, 1, expandFlags|wx.ALL, 2)
			bs.Add( (25, -1), 0)
			
			if fieldType in ["memo",]:
				mainSizer.Add(bs, 1, wx.EXPAND)
			else:
				mainSizer.Add(bs, 0, wx.EXPAND)

		# Add top and bottom margins
		mainSizer.Insert( 0, (-1, 20), 0)
		mainSizer.Add( (-1, 30), 0)

		self.GetSizer().Layout()
		self.itemsCreated = True
		self.SetFocus()


class dChildViewPage(DataNavPage):
	def __init__(self, parent, dataSource):
		dChildViewPage.doDefault(parent, "pageChildView")
		self.dataSource = dataSource
		self.bizobj = self.Form.getBizobj().getChildByDataSource(self.dataSource)
		self.pickListRef = None
	
	def onPageEnter(self, evt):
		if self.bizobj and self.bizobj.RowCount >= 0:
			if not self.itemsCreated:
				self.createItems()
		if self.itemsCreated:
			self.fillGrid()
		dChildViewPage.doDefault(evt)
	
	
	def onLeavePage(self):
		if self.pickListRef:
			self.pickListRef.Close()
	
			
	def onRowNumChanged(self, evt):
		# If RowNumChanged (in the parent bizobj) is received AND we are the
		# active page, the child bizobj has already been requeried
		# but the grid needs to be filled to reflect that.
		self.onPageEnter(None)

		
	def createItems(self):
		cb = self.Form.getChildBehavior(self.dataSource)
		if cb["EnableNew"]:
			nb = self.addObject(dCommandButton.dCommandButton, "cmdNew")
			nb.Caption = "Add new child record"
			nb.Bind(wx.EVT_BUTTON, self.newRecord)
			self.GetSizer().Add(nb, 0, wx.EXPAND)
		grid = self.addObject(dDataNavGrid.dDataNavGrid, "ChildViewGrid")
		grid.DataSource = self.dataSource
		self.GetSizer().Add(grid, 1, wx.EXPAND)
		
		self.itemsCreated = True

		
	def fillGrid(self):
		self.ChildViewGrid.columnDefs = self.Form.getColumnDefs(self.dataSource)
		self.ChildViewGrid.fillGrid()
		self.GetSizer().Layout()
		for window in self.ChildViewGrid.GetChildren():
			window.SetFocus()
	
			
	def newItemPicked(self, evt):
		pickBizobj = evt.GetEventObject().getBizobj()
		pickedPK = pickBizobj.getPK()
		cb = self.Form.getChildBehavior(self.dataSource)
		try:
			fkField = cb["FK"]
		except KeyError:
			raise KeyError, "ChildBehavior dictionary does not contain needed FK value."
				
		try:
			self.bizobj.new()
			self.bizobj.setFieldVal(fkField, pickedPK)
		except dException.dException, e:
			dMessagebox.stop("Cannot add the new record:\n%s" % str(e))
		
		try:
			derivedFields = cb["DerivedFields"]
		except KeyError:
			derivedFields = {}
			
		for field in derivedFields.keys():
			self.bizobj.setFieldVal(field, pickBizobj.getFieldVal(derivedFields[field]))
		self.fillGrid()		

			
	def newRecord(self, evt=None):
		cb = self.Form.getChildBehavior(self.dataSource)
		if cb["EnableNew"]:
			try:
				newBehavior = cb["NewBehavior"]
			except KeyError:
				newBehavior = None
				
			if newBehavior:
				if newBehavior == "PickList":
					try:
						cls = cb["PickListClass"]
					except KeyError:
						cls = None
						
					if cls:
						ref = self.pickListRef
						if not ref:
							class PickList(cls):
								def initProperties(self):
									PickList.doDefault()
									self.FormType = "PickList"
								def afterInit(self):
									PickList.doDefault()
									self.Caption = "Picklist: %s" % self.Caption
									
							ref = PickList(self.Form)
							self.pickListRef = ref
						
							self.bindEvent(dEvents.ItemPicked, self.newItemPicked)
							ref.Show()
						ref.Raise()
					else:
						raise dException.dException, "No picklist class defined."
					
			else:
				raise dException.dException, "No new behavior is defined."
				
		else:
			dMessageBox.stop("Adding new records isn't allowed.")
			
		
	def deleteRecord(self):
		""" Ask the bizobj to delete the current record.
		"""
		cb = self.Form.getChildBehavior(self.dataSource)
		if cb["EnableDelete"]:
			message = _("This will delete the highlighted child record, and cannot "
							"be canceled.\n\n Are you sure you want to do this?")
			if dMessageBox.areYouSure(message, defaultNo=True):
				try:
					self.bizobj.delete()
					self.Form.setStatusText(_("Child record deleted."))
				except dException.dException, e:
					dMessageBox.stop("Delete failed with response:\n%s" % str(e))
				self.fillGrid()
		else:
			dMessageBox.stop("Deleting records isn't allowed.")
	
			
	def editRecord(self):
		cb = self.Form.getChildBehavior(self.dataSource)
		if cb["EnableEdit"]:
			dMessageBox.stop("Editing childview records isn't supported yet.")
		else:
			dMessageBox.stop("Editing records isn't allowed.")


# For convenience		
def padl(string, length, fill=" "):
	string = str(string)[:length]
	return (fill * (length-len(string)) ) + string
		

