import dPage, dTextBox, dLabel, dEditBox, dCheckBox, dSpinner, dMessageBox, dIcons, dCommandButton
import dPanel, dGrid, dCommandButton, dMessageBox, dEvents
import wx
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
			self.setEnabled(self.FindWindowById(optionRow['cbId']))
		self.setEnabled(self.chkSelectLimit)

	def setEnabled(self, cb):
		# Get reference(s) to the associated input control(s)
		if cb.Name == 'chkSelectLimit':
			user1, user2 = self.spnSelectLimit, None
		else:
			user1, user2 = None, None
			for optionRow in self.selectOptionsPanel.selectOptions:
				if cb and optionRow['cbId'] == cb.GetId():
					user1Id = optionRow['user1Id']
					user2Id = optionRow['user2Id']
					user1 = self.FindWindowById(user1Id)
					user2 = self.FindWindowById(user2Id)
					dataType = optionRow['dataType']
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
		dSelectPage.doDefault(parent, name='pageSelect')

	def createItems(self):
		self.selectOptionsPanel = self._getSelectOptionsPanel()
		self.selectOptionsPanel.initEnabled()
		self.GetSizer().Add(self.selectOptionsPanel, 0, wx.GROW|wx.ALL, 5)
		self.selectOptionsPanel.SetFocus()
		dSelectPage.doDefault()


	def getWhere(self):
		# for each checked selection item, get the where clause:
		user1, user2 = None, None
		whereClause = ""

		for optionRow in self.selectOptionsPanel.selectOptions:
			cb = self.FindWindowById(optionRow['cbId'])
			if cb.IsChecked():
				user1Val = self.FindWindowById(optionRow['user1Id']).GetValue()
				try:
					user2Val = self.FindWindowById(optionRow['user2Id']).GetValue()
				except AttributeError:
					user2Val = None

				whereStub = optionRow['where']
				whereStub = whereStub.replace('?(user1)', user1Val)
				if user2Val <> None:
					whereStub = whereStub.replace('?(user2)', user2Val)

				if len(whereClause) > 0:
					whereClause = ''.join((whereClause, '\n     AND '))
				whereClause = ''.join((whereClause, '(', whereStub, ')'))

		return whereClause

	def onRequery(self, evt):
		self.requery()
		evt.Skip()

	def requery(self):
		bizobj = self.getDform().getBizobj()
		where = self.getWhere()
		bizobj.setWhereClause(where)
		
		if self.selectOptionsPanel.chkSelectLimit.Value == True:
			limit = "%s" % self.selectOptionsPanel.spnSelectLimit.Value
		else:
			limit = None
		bizobj.setLimitClause(limit)
		
		# The bizobj will get the SQL from the sql builder:
		sql = bizobj.getSQL()

		print '\n%s\n' % sql
		
		# But it won't automatically use that sql, so we set it here:
		bizobj.setSQL(sql)

		self.getDform().requery()

		if self.GetParent().GetSelection() == 0:
			# If the select page is active, now make the browse page active
			self.GetParent().SetSelection(1)


	def _getSelectOptionsPanel(self):
		dataSource = self.getDform().getBizobj().DataSource
		columnDefs = self.getDform().getColumnDefs(dataSource)
		panel = SelectOptionsPanel(self)
		
		stringMatchAll = []

		sizer = wx.BoxSizer(wx.VERTICAL)

		label = dLabel.dLabel(panel)
		label.Caption = _('Please enter your record selection criteria:')
		sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

		for column in columnDefs:

			for selectType in column['selectTypes']:
				where = None
				# Id's for the UI input elements:
				cbId = wx.NewId()
				user1Id = wx.NewId()
				user2Id = wx.NewId()

				box = wx.BoxSizer(wx.HORIZONTAL)

				if selectType == 'range':
					where =     "%s.%s BETWEEN '?(user1)' AND '?(user2)'" % (
								column['tableName'], column['fieldName'])

					cb = SelectOptionsCheckBox(panel, id=cbId, 
							name='chkSelectRange%s' % column['fieldName'])
					cb.Caption = '%s %s:' % (column['caption'], _('is in the range of'))
					cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23


					box.Add(cb, 0, wx.ALL, 5)

					text = SelectOptionsTextBox(panel, id=user1Id)
					box.Add(text, 1, wx.ALL, 5)

					label = dLabel.dLabel(panel)
					label.Caption = 'and'
					box.Add(label, 0, wx.ALL, 5)

					text = SelectOptionsTextBox(panel, id=user2Id)
					box.Add(text, 1, wx.ALL, 5)

				elif selectType == 'value':
					where = "%s.%s = '?(user1)'" % (
								column["tableName"], column["fieldName"])

					cb = SelectOptionsCheckBox(panel, id=cbId, 
							name='chkSelectValue%s' % column['fieldName'])
					cb.Caption = '%s %s:' % (column['caption'], _('is equal to'))
					cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23

					box.Add(cb, 0, wx.ALL, 5)

					text = SelectOptionsTextBox(panel, id=user1Id)
					box.Add(text, 1, wx.ALL, 5)

				elif selectType == 'stringMatch':
					where = "%s.%s LIKE '%c?(user1)%c'" % (
							column['tableName'], column['fieldName'], "%", "%")    

					cb = SelectOptionsCheckBox(panel, id=cbId, 
							name='chkSelectStringMatch%s' % column['fieldName'])
					cb.Caption = '%s %s:' % (column['caption'], _('contains'))
					cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23

					box.Add(cb, 0, wx.ALL, 5)

					text = SelectOptionsTextBox(panel, id=user1Id)
					box.Add(text, 1, wx.ALL, 5)

				elif selectType == 'stringMatchAll':
					stringMatchAll.append(column)

				else:
					where = None


				if where != None:
					panel.selectOptions.append({'dataType': column['type'],
												'cbId': cbId,
												'user1Id': user1Id,
												'user2Id': user2Id})    

					sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
					panel.selectOptions[len(panel.selectOptions) - 1]['where'] = where

		# Any fielddef encountered in the above block with type of 'stringMatchAll'
		# got appended to the stringMatchAll list. Take this list, and define
		# one selectOptions control that will operate on all these fields.
		if len(stringMatchAll) > 0:
			cbId, user1Id, user2Id = wx.NewId(), wx.NewId(), wx.NewId()
			where = ''

			cb = SelectOptionsCheckBox(panel, id=cbId, name='chkSelectStringMatchAll')
			cb.Caption = '%s:' % _('String Match')
			cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23

			box.Add(cb, 0, wx.ALL, 5)

			text = SelectOptionsTextBox(panel, id=user1Id)
			box.Add(text, 1, wx.ALL, 5)

			for column in stringMatchAll:
				if len(where) > 0:
					char = ' OR '
				else:
					char = ''
				where = ''.join((where,char,"%s.%s LIKE '%c?(user1)%c'" % (
							column['tableName'], column['fieldName'], '%', '%')))    

			panel.selectOptions.append({'dataType': column['type'],
										'cbId': cbId,
										'user1Id': user1Id,
										'user2Id': user2Id})    

			sizer.AddSizer(box, 0, wx.GROW|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)
			panel.selectOptions[len(panel.selectOptions) - 1]['where'] = where

		line = wx.StaticLine(panel, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
		sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

		box = wx.BoxSizer(wx.HORIZONTAL)
		
		cb = SelectOptionsCheckBox(panel, name='chkSelectLimit')
		cb.Caption = 'Limit:'
		cb.Width = cb.GetTextExtent(cb.Caption)[0] + 23
		box.Add(cb, 0, wx.ALL, 5)
		
		limitSpinner = SelectOptionsSpinner(panel, name='spnSelectLimit')
		box.Add(limitSpinner, 1, wx.ALL, 5)
		

		requeryButton = dCommandButton.dCommandButton(panel)
		requeryButton.Caption = '&%s' % _('Requery')
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
		dBrowsePage.doDefault(parent, 'pageBrowse')


	def onRowNumChanged(self, event):
		# If RowNumChanged is received AND we are the
		# active page, select the row in the grid
		pf = self.GetParent()
		if not self.itemsCreated:
			self.createItems()
		if self.itemsCreated and pf.GetPage(pf.GetSelection()) == self:
			self.fillGrid()

		row = self.getDform().getBizobj().getRowNumber()
		col = self.grid.GetGridCursorCol()
		self.grid.SetGridCursor(row, col)
		self.grid.MakeCellVisible(row, col)

		event.Skip()


	def onEnterPage(self):
		bizobj = self.getDform().getBizobj()
		if bizobj and bizobj.getRowCount() >= 0:
			if not self.itemsCreated:
				self.createItems()
		if self.itemsCreated:
			self.fillGrid()


	def createItems(self):
		form = self.getDform()
		bizobj = form.getBizobj()
		self.grid = dGrid.dGrid(self, bizobj, form)
		self.grid.SetName('BrowseGrid')
		self.GetSizer().Add(self.grid, 1, wx.EXPAND)
		self.grid.columnDefs = form.getColumnDefs(bizobj.DataSource)
		
		self.addObject(dCommandButton.dCommandButton, 'cmdPreview')
		self.cmdPreview.Caption = "Preview"
		self.cmdPreview.Bind(wx.EVT_BUTTON, self.onPreview)
		self.GetSizer().Add(self.cmdPreview, 0, 0)
		
		self.GetSizer().Layout()
		self.itemsCreated = True


	def fillGrid(self):
		form = self.getDform()
		bizobj = form.getBizobj()
		self.grid.fillGrid()
		self.GetSizer().Layout()
		for window in self.grid.GetChildren():
			window.SetFocus()


	def newRecord(self):
		self.getDform().new()
		self.editRecord()
	
		
	def deleteRecord(self):
		self.GetParent().getDform().delete()

	
	def editRecord(self):
		# Called by the grid: user wants to edit the current row
		self.GetParent().SetSelection(2)

		
	def onPreview(self, event):
		if self.itemsCreated:
			html = self.grid.getHTML(justStub=False)
			win = wx.html.HtmlEasyPrinting("Dabo Quick Print", self.getDform())
			printData = win.GetPrintData()
			setupData = win.GetPageSetupData()
			#printData.SetPaperId(wx.PAPER_LETTER)
			setupData.SetPaperId(wx.PAPER_LETTER)
			if self.grid.GetNumberCols() > 20:
				printData.SetOrientation(wx.LANDSCAPE)
			else:
				printData.SetOrientation(wx.PORTRAIT)
			#setupData.SetMarginTopLeft((17,7))
			#s#etupData.SetMarginBottomRight((17,5))
	#       # setupData.SetOrientation(wx.LANDSCAPE)
			win.SetHeader("<B>%s</B>" % (self.getDform().Caption,))
			win.SetFooter("<CENTER>Page @PAGENUM@ of @PAGESCNT@</CENTER>")
			#win.PageSetup()
			win.PreviewText(html)

			
class dEditPage(dPage.dPage):

	def __init__(self, parent):
		dEditPage.doDefault(parent, 'pageEdit')


	def onEnterPage(self):
		dEditPage.doDefault()
		self.onValueRefresh()


	def onValueRefresh(self, event=None):
		form = self.getDform()
		bizobj = form.getBizobj()
		if bizobj and bizobj.getRowCount() >= 0:
			self.Enable(True)
		else:
			self.Enable(False)
		if event:
			event.Skip()


	def createItems(self):
		dataSource = self.getDform().getBizobj().DataSource
		columnDefs = self.getDform().getColumnDefs(dataSource)

		for column in columnDefs:

			if column['showEdit'] == True:
				fieldName = column['fieldName']
				fieldType = column['type']
				fieldEnabled = column['editEdit']

				bs = wx.BoxSizer(wx.HORIZONTAL)
				
				labelWidth = 150

				labelStyle = wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE

				label = dLabel.dLabel(self, style=labelStyle)
				label.Name='lbl%s' % fieldName 
				label.Width = labelWidth
				
				if fieldType in ['M',]:
					classRef = dEditBox.dEditBox
				elif fieldType in ['I',]:
					classRef = dSpinner.dSpinner
				elif fieldType in ['L',]:
					classRef = dCheckBox.dCheckBox
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
					label.Caption = ''
					objectRef.Caption = column['caption']
				else:
					label.Caption = '%s:' % column['caption']

				if self.getDform().getBizobj().getRowCount() >= 0:
					objectRef.refresh()

				if fieldType in ['M',]:
					expandFlags = wx.EXPAND
				else:
					expandFlags = 0
				bs.Add(label)
				bs.Add(objectRef, 1, expandFlags|wx.ALL, 0)

				if fieldType in ['M',]:
					self.GetSizer().Add(bs, 1, wx.EXPAND)
				else:
					self.GetSizer().Add(bs, 0, wx.EXPAND)

		self.GetSizer().Layout()
		self.itemsCreated = True


class dChildViewPage(dPage.dPage):

	def __init__(self, parent, dataSource):
		dChildViewPage.doDefault(parent, 'pageChildView')
		self.dataSource = dataSource
		self.bizobj = self.getDform().getBizobj().getChildByDataSource(self.dataSource)
	
	def onEnterPage(self):
		if self.bizobj and self.bizobj.getRowCount() >= 0:
			if not self.itemsCreated:
				self.createItems()
		if self.itemsCreated:
			self.fillGrid()
	
	
	def onRowNumChanged(self, event):
		# If RowNumChanged (in the parent bizobj) is received AND we are the
		# active page, the child bizobj has already been requeried
		# but the grid needs to be filled to reflect that.
		self.onEnterPage()
		event.Skip()


	def createItems(self):
		form = self.getDform()
		self.grid = dGrid.dGrid(self, self.bizobj, form)
		self.grid.SetName('ChildViewGrid')
		self.GetSizer().Add(self.grid, 1, wx.EXPAND)
		
		self.itemsCreated = True

		
	def fillGrid(self):
		form = self.getDform()
		self.grid.columnDefs = form.getColumnDefs(self.bizobj.DataSource)
		self.grid.fillGrid()
		self.GetSizer().Layout()
		for window in self.grid.GetChildren():
			window.SetFocus()
	
			
	def newRecord(self):
		dMessageBox.stop("Adding new childview records isn't supported yet.")
		
		
	def deleteRecord(self):
		dMessageBox.stop("Deleting childview records isn't supported yet.")

	
	def editRecord(self):
		dMessageBox.stop("Editing childview records isn't supported yet.")
