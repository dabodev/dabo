import wx, dabo
import dPage, dTextBox, dLabel, dEditBox, dCheckBox, dSpinner, dMessageBox, dIcons, dCommandButton
import dPanel, dGridDataNav, dCommandButton, dMessageBox, dEvents, dDateControl
import dabo.dException as dException
from dabo.dLocalize import _


class SelectOptionsPanel(dPanel.dPanel):
	""" Base class for the select options panel.
	"""
	def initProperties(self):
		self.Name = "selectOptionsPanel"
		# selectOptions is a list of dictionaries
		self.selectOptions = []
		
	def initEnabled(self):
		for optionRow in self.selectOptions:
			self.setEnabled(self.FindWindowById(optionRow["cbId"]))
		self.setEnabled(self.chkSelectLimit)

	def setEnabled(self, cb):
		# Get reference(s) to the associated input control(s)
		if cb.Name == "chkSelectLimit":
			user1, user2 = self.spnSelectLimit, None
		else:
			user1, user2 = None, None
			for optionRow in self.selectOptionsPanel.selectOptions:
				if cb and optionRow["cbId"] == cb.GetId():
					user1Id = optionRow["user1Id"]
					user2Id = optionRow["user2Id"]
					user1 = self.FindWindowById(user1Id)
					user2 = self.FindWindowById(user2Id)
					dataType = optionRow["dataType"]
					break            

		# enable/disable the associated input control(s) based
		# on the value of cb. Set Focus to the first control if
		# the checkbox is enabled.
		try:
			user1.Enable(cb.Value)
			if cb.Value:
				user1.SetFocus()
		except AttributeError: 
			pass

		try:
			user2.Enable(cb.Value)
		except AttributeError: 
			pass

		
class SelectOptionsCheckBox(dCheckBox.dCheckBox):
	""" Base class for the checkboxes used in the select page.
	"""
	def afterInit(self):
		EVT_VALUECHANGED = wx.PyEventBinder(dEvents.EVT_VALUECHANGED, 0)
		self.Bind(EVT_VALUECHANGED, self.OnValueChanged)

	def initProperties(self):
		self.SaveRestoreValue = True
	
	def OnValueChanged(self, evt):
		self.Parent.setEnabled(self)
		

class SelectOptionsTextBox(dTextBox.dTextBox):
	""" Base class for the textboxes used in the select page.
	"""
	def initProperties(self):
		self.SaveRestoreValue = True
		

class SelectOptionsSpinner(dSpinner.dSpinner):
	""" Base class for the dSpinner used in the select page.
	"""
	def initProperties(self):
		self.SaveRestoreValue = True
		self.Min = 0
		self.Max = 5000
		
				
class dSelectPage(dPage.dPage):

	def __init__(self, parent):
		dSelectPage.doDefault(parent, name="pageSelect")
		

	def createItems(self):
		self.selectOptionsPanel = self._getSelectOptionsPanel()
		self.selectOptionsPanel.initEnabled()
		self.GetSizer().Add(self.selectOptionsPanel, 0, wx.GROW|wx.ALL, 5)
		self.selectOptionsPanel.SetFocus()
		dSelectPage.doDefault()

	
	def getWhere(self, biz):
		# for each checked selection item, get the where clause:
		user1, user2 = None, None
		whereClause = ""

		for optionRow in self.selectOptionsPanel.selectOptions:
			cb = self.FindWindowById(optionRow["cbId"])
			if cb.IsChecked():
				user1Val = self.FindWindowById(optionRow["user1Id"]).GetValue()
				try:
					user2Val = self.FindWindowById(optionRow["user2Id"]).GetValue()
				except AttributeError:
					user2Val = None

				whereStub = biz.prepareWhere(optionRow["where"])
				whereStub = whereStub.replace("?(user1)", user1Val)
				if user2Val is not None:
					whereStub = whereStub.replace("?(user2)", user2Val)

				if len(whereClause) > 0:
					whereClause = "".join((whereClause, "\n     AND "))
				whereClause = "".join((whereClause, "(", whereStub, ")"))
		return whereClause
	
	def onRequery(self, evt):
		self.requery()
		evt.Skip()

	def requery(self):
		bizobj = self.Form.getBizobj()
		where = self.getWhere(bizobj)
		bizobj.setWhereClause(where)
		
		if self.selectOptionsPanel.chkSelectLimit.Value == True:
			limit = "%s" % self.selectOptionsPanel.spnSelectLimit.Value
		else:
			limit = None
		bizobj.setLimitClause(limit)
		
		# The bizobj will get the SQL from the sql builder:
		sql = bizobj.getSQL()

		dabo.infoLog.write("\n%s\n" % sql)
		
		# But it won't automatically use that sql, so we set it here:
		bizobj.setSQL(sql)

		self.Form.requery()

		if self.GetParent().GetSelection() == 0:
			# If the select page is active, now make the browse page active
			self.GetParent().SetSelection(1)


	def _getSelectOptionsPanel(self):
		dataSource = self.Form.getBizobj().DataSource
		columnDefs = self.Form.getColumnDefs(dataSource)
		panel = SelectOptionsPanel(self)
		
		stringMatchAll = []

		sizer = wx.BoxSizer(wx.VERTICAL)

		label = dLabel.dLabel(panel)
		label.Caption = _("Please enter your record selection criteria:")
		sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

		for column in columnDefs:

			for selectType in column["selectTypes"]:
				where = None
				# Ids for the UI input elements:
				cbId = wx.NewId()
				user1Id = wx.NewId()
				user2Id = wx.NewId()

				box = wx.BoxSizer(wx.HORIZONTAL)

				if selectType == "range":
					where =     "%s.%s BETWEEN '?(user1)' AND '?(user2)'" % (
								column["tableName"], column["fieldName"])

					cb = SelectOptionsCheckBox(panel, id=cbId, 
							name="chkSelectRange%s" % column["fieldName"])
					cb.Caption = "%s %s:" % (column["caption"], _("is in the range of"))
					cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23


					box.Add(cb, 0, wx.ALL, 5)

					text = SelectOptionsTextBox(panel, id=user1Id)
					box.Add(text, 1, wx.ALL, 5)

					label = dLabel.dLabel(panel)
					label.Caption = "and"
					box.Add(label, 0, wx.ALL, 5)

					text = SelectOptionsTextBox(panel, id=user2Id)
					box.Add(text, 1, wx.ALL, 5)

				elif selectType == "value":
					where = "%s.%s = '?(user1)'" % (
								column["tableName"], column["fieldName"])

					cb = SelectOptionsCheckBox(panel, id=cbId, 
							name="chkSelectValue%s" % column["fieldName"])
					cb.Caption = "%s %s:" % (column["caption"], _("is equal to"))
					cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23

					box.Add(cb, 0, wx.ALL, 5)

					text = SelectOptionsTextBox(panel, id=user1Id)
					box.Add(text, 1, wx.ALL, 5)

				elif selectType == "stringMatch":
					where = "%s.%s LIKE '%c?(user1)%c'" % (
							column["tableName"], column["fieldName"], "%", "%")    

					cb = SelectOptionsCheckBox(panel, id=cbId, 
							name="chkSelectStringMatch%s" % column["fieldName"])
					cb.Caption = "%s %s:" % (column["caption"], _("contains"))
					cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23

					box.Add(cb, 0, wx.ALL, 5)

					text = SelectOptionsTextBox(panel, id=user1Id)
					box.Add(text, 1, wx.ALL, 5)

				elif selectType == "stringMatchAll":
					stringMatchAll.append(column)

				else:
					where = None


				if where != None:
					panel.selectOptions.append({"dataType": column["type"],
												"cbId": cbId,
												"user1Id": user1Id,
												"user2Id": user2Id})    

					sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
					panel.selectOptions[len(panel.selectOptions) - 1]["where"] = where

		# Any fielddef encountered in the above block with type of 'stringMatchAll'
		# got appended to the stringMatchAll list. Take this list, and define
		# one selectOptions control that will operate on all these fields.
		if len(stringMatchAll) > 0:
			cbId, user1Id, user2Id = wx.NewId(), wx.NewId(), wx.NewId()
			where = ""

			cb = SelectOptionsCheckBox(panel, id=cbId, name="chkSelectStringMatchAll")
			cb.Caption = "%s:" % _("String Match")
			cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23

			box.Add(cb, 0, wx.ALL, 5)

			text = SelectOptionsTextBox(panel, id=user1Id)
			box.Add(text, 1, wx.ALL, 5)

			for column in stringMatchAll:
				if len(where) > 0:
					char = " OR "
				else:
					char = ""
				where = "".join((where,char,"%s.%s LIKE '%c?(user1)%c'" % (
							column["tableName"], column["fieldName"], "%", "%")))    

			panel.selectOptions.append({"dataType": column["type"],
										"cbId": cbId,
										"user1Id": user1Id,
										"user2Id": user2Id})    

			sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
			panel.selectOptions[len(panel.selectOptions) - 1]["where"] = where

		line = wx.StaticLine(panel, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

		box = wx.BoxSizer(wx.HORIZONTAL)
		
		cb = SelectOptionsCheckBox(panel, name="chkSelectLimit")
		cb.Caption = "Limit:"
		cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23
		box.Add(cb, 0, wx.ALL, 5)
		
		limitSpinner = SelectOptionsSpinner(panel, name="spnSelectLimit")
		box.Add(limitSpinner, 1, wx.ALL, 5)
		

		requeryButton = dCommandButton.dCommandButton(panel)
		requeryButton.Caption = "&%s" % _("Requery")
		requeryButton.Default = True             # Doesn't work on Linux, but test on win/mac
		requeryButton.Bind(wx.EVT_BUTTON, self.onRequery)

		box.Add(requeryButton, 0)
		sizer.Add(box, 0, wx.GROW, 5)

		panel.SetSizer(sizer)
		panel.SetAutoLayout(True)
		sizer.Fit(panel)

		return panel


class dBrowsePage(dPage.dPage):

	def __init__(self, parent):
		dBrowsePage.doDefault(parent, "pageBrowse")


	def onRowNumChanged(self, event):
		# If RowNumChanged is received AND we are the active page, select
		# the row in the grid.
		
		# If we aren't the active page, strange things can happen if we
		# don't explicitly SetFocus back to the active page. 
		activePage = self.GetParent().GetPage(self.GetParent().GetSelection())
		if activePage == self:
			self.updateGrid()
		else:
			activePage.SetFocus()
		event.Skip()


	def updateGrid(self):
		bizobj = self.Form.getBizobj()
		justCreated = False
		if bizobj and bizobj.RowCount >= 0:
			if not self.itemsCreated:
				self.createItems()
				justCreated = True
			if self.itemsCreated:
				self.fillGrid()

			row = self.Form.getBizobj().RowNumber
			col = self.BrowseGrid.GetGridCursorCol()
			
			if col < 0:
				col = 0
			self.BrowseGrid.SetGridCursor(row, col)
			
			if not justCreated and not self.BrowseGrid.IsVisible(row, col):
				self.BrowseGrid.MakeCellVisible(row, col)

		
	def onEnterPage(self):
		self.updateGrid()
		dBrowsePage.doDefault()


	def createItems(self):
		bizobj = self.Form.getBizobj()
		grid = self.addObject(dGridDataNav.dGridDataNav, "BrowseGrid")
		grid.DataSource = bizobj.DataSource
		self.GetSizer().Add(grid, 1, wx.EXPAND)
		grid.columnDefs = self.Form.getColumnDefs(bizobj.DataSource)
		
		preview = self.addObject(dCommandButton.dCommandButton, "cmdPreview")
		preview.Caption = "Preview"
		preview.Bind(wx.EVT_BUTTON, self.onPreview)
		self.GetSizer().Add(preview, 0, 0)
		
		self.itemsCreated = True


	def fillGrid(self):
		bizobj = self.Form.getBizobj()
		self.BrowseGrid.fillGrid()
		self.GetSizer().Layout()
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

		
	def onPreview(self, event):
		if self.itemsCreated:
			html = self.grid.getHTML(justStub=False)
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

			
class dEditPage(dPage.dPage):

	def __init__(self, parent):
		dEditPage.doDefault(parent, "pageEdit")


	def onEnterPage(self):
		self.onValueRefresh()
		dEditPage.doDefault()


	def onValueRefresh(self, event=None):
		form = self.Form
		bizobj = form.getBizobj()
		if bizobj and bizobj.RowCount >= 0:
			self.Enable(True)
		else:
			self.Enable(False)
		if event:
			event.Skip()


	def createItems(self):
		dataSource = self.Form.getBizobj().DataSource
		columnDefs = self.Form.getColumnDefs(dataSource)

		for column in columnDefs:

			if column["showEdit"] == True:
				fieldName = column["fieldName"]
				fieldType = column["type"]
				fieldEnabled = column["editEdit"]

				bs = wx.BoxSizer(wx.HORIZONTAL)
				
				labelWidth = 150

				labelStyle = wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE

				label = dLabel.dLabel(self, style=labelStyle)
				label.Name="lbl%s" % fieldName 
				label.Width = labelWidth
				
				if fieldType in ["M",]:
					classRef = dEditBox.dEditBox
				elif fieldType in ["I",]:
					classRef = dSpinner.dSpinner
				elif fieldType in ["L",]:
					classRef = dCheckBox.dCheckBox
				elif fieldType in ["D",]:
					classRef = dDateControl.dDateControl
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
					objectRef.Caption = column["caption"]
				else:
					label.Caption = "%s:" % column["caption"]

				if self.Form.getBizobj().RowCount >= 0:
					objectRef.refresh()

				if fieldType in ["M",]:
					expandFlags = wx.EXPAND
				else:
					expandFlags = 0
				bs.Add(label)
				bs.Add(objectRef, 1, expandFlags|wx.ALL, 0)

				if fieldType in ["M",]:
					self.GetSizer().Add(bs, 1, wx.EXPAND)
				else:
					self.GetSizer().Add(bs, 0, wx.EXPAND)

		self.GetSizer().Layout()
		self.itemsCreated = True
		self.SetFocus()


class dChildViewPage(dPage.dPage):

	def __init__(self, parent, dataSource):
		dChildViewPage.doDefault(parent, "pageChildView")
		self.dataSource = dataSource
		self.bizobj = self.Form.getBizobj().getChildByDataSource(self.dataSource)
		self.pickListRef = None
	
	def onEnterPage(self):
		if self.bizobj and self.bizobj.RowCount >= 0:
			if not self.itemsCreated:
				self.createItems()
		if self.itemsCreated:
			self.fillGrid()
		dChildViewPage.doDefault()
	
	
	def onLeavePage(self):
		if self.pickListRef:
			self.pickListRef.Close()
	
			
	def onRowNumChanged(self, event):
		# If RowNumChanged (in the parent bizobj) is received AND we are the
		# active page, the child bizobj has already been requeried
		# but the grid needs to be filled to reflect that.
		self.onEnterPage()
		event.Skip()


	def createItems(self):
		cb = self.Form.getChildBehavior(self.dataSource)
		if cb["EnableNew"]:
			nb = self.addObject(dCommandButton.dCommandButton, "cmdNew")
			nb.Caption = "Add new child record"
			nb.Bind(wx.EVT_BUTTON, self.newRecord)
			self.GetSizer().Add(nb, 0, wx.EXPAND)
		grid = self.addObject(dGridDataNav.dGridDataNav, "ChildViewGrid")
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
						
							EVT_ITEMPICKED = wx.PyEventBinder(dEvents.EVT_ITEMPICKED, 0)    
							ref.Bind(EVT_ITEMPICKED, self.newItemPicked)
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

		
