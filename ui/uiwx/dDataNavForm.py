import wx
import dIcons
import dabo.dEvents as dEvents
import dForm, dDataNavPageFrame
from dabo.common import fieldSpecParser

class dDataNavForm(dForm.dForm):
	""" This is a dForm but with the following added controls:
		+ Navigation Menu
		+ Navigation ToolBar
		+ PageFrame with 3 pages by default:
			+ Select : Enter sql-select criteria.
			+ Browse : Browse the result set and pick an item to edit.
			+ Edit   : Edit the current record in the result set.
	"""

	def beforeInit(self, preObject):
		dDataNavForm.doDefault(preObject)
		# Determines if we are actually running the form, or just 
		# previewing it
		self._fieldSpecs = {}
		self._relationSpecs = {}
		self._childBehavior = {}
		self._requeried = False
		# Used for turning sizer outline drawing on pages
		self._drawSizerOutlines = False
	
	
	def __init__(self, parent=None, previewMode=False, tbl=""):
		self.preview = previewMode
		self.previewDataSource = tbl
		dDataNavForm.doDefault(parent)
		# We will need to set these separated if in Preview mode.
		self.rowNumber = 0
		self.rowCount = 0
		

	def afterInit(self):
		dDataNavForm.doDefault()
		if self.FormType == 'PickList':
			# Map escape key to close the form
			anId = wx.NewId()
			self.acceleratorTable.append((wx.ACCEL_NORMAL, wx.WXK_ESCAPE, anId))
			self.Bind(wx.EVT_MENU, self.Close, id=anId)

			
	def initEvents(self):
		dDataNavForm.doDefault()
		self.bindEvent(dEvents.Activate, self.__onActivate)
		
							
	def __onActivate(self, evt):
		if self.RequeryOnLoad and not self._requeried:
			self._requeried = True
			self.pageFrame.GetPage(0).requery()
		
	def afterSetPrimaryBizobj(self):        
		pass
		
		
	def afterSetFieldSpecs(self):
		self.childViews = []
		for child in self.getBizobj().getChildren():
			self.childViews.append({"dataSource": child.DataSource,
					"caption": child.Caption,
					"menuId": wx.NewId()})
		self.setupPageFrame()
		self.setupToolBar()
		self.setupMenu()
		
		
	def setupToolBar(self):
		if isinstance(self, wx.MDIChildFrame):
			# Toolbar will be attached to top-level form
			controllingFrame = self.Application.MainForm
		else:
			# Toolbar will be attached to this frame
			controllingFrame = self
		toolBar = wx.ToolBar(controllingFrame, -1)
		toolBar.SetToolBitmapSize((16,16))    # Needed on non-Linux platforms

		if self.FormType != 'Edit':
			self._appendToToolBar(toolBar, "First", dIcons.getIconBitmap("leftArrows"),
								self.onFirst, "Go to the first record")

			self._appendToToolBar(toolBar, "Prior", dIcons.getIconBitmap("leftArrow"),
								self.onPrior, "Go to the prior record")

			self._appendToToolBar(toolBar, "Requery", dIcons.getIconBitmap("requery"),
								self.onRequery, "Requery dataset")

			self._appendToToolBar(toolBar, "Next", dIcons.getIconBitmap("rightArrow"),
								self.onNext, "Go to the next record")

			self._appendToToolBar(toolBar, "Last", dIcons.getIconBitmap("rightArrows"),
								self.onLast, "Go to the last record")

			toolBar.AddSeparator()

		if self.FormType == 'Normal':
			self._appendToToolBar(toolBar, "New", dIcons.getIconBitmap("blank"),
								self.onNew, "Add a new record")

			self._appendToToolBar(toolBar, "Delete", dIcons.getIconBitmap("delete"),
								self.onDelete, "Delete this record")

			toolBar.AddSeparator()

		if self.FormType != 'PickList':
			self._appendToToolBar(toolBar, "Save", dIcons.getIconBitmap("save"),
								self.onSave, "Save changes")

			self._appendToToolBar(toolBar, "Cancel", dIcons.getIconBitmap("revert"),
								self.onCancel, "Cancel changes")

		controllingFrame.SetToolBar(toolBar)
		toolBar.Realize()                      # Needed on non-Linux platforms


	def getMenu(self):
		menu = dDataNavForm.doDefault()

		self._appendToMenu(menu, "Set Selection Criteria\tAlt+1", 
						self.onSetSelectionCriteria, 
						bitmap=dIcons.getIconBitmap("checkMark"))
		self._appendToMenu(menu, "Browse Records\tAlt+2", 
						self.onBrowseRecords, 
						bitmap=dIcons.getIconBitmap("browse"))
		self._appendToMenu(menu, "Edit Current Record\tAlt+3", 
						self.onEditCurrentRecord, 
						bitmap=dIcons.getIconBitmap("edit"))
		
		if self.FormType != 'PickList':
			i = 4
			for child in self.childViews:
				self._appendToMenu(menu, "View %s\tAlt+%s" % (child['caption'], i) ,
								self.onChildView, 
								bitmap=dIcons.getIconBitmap("childview"),
								menuId = child['menuId'])
				i += 1
			
		menu.AppendSeparator()

		if self.FormType != 'Edit':
			self._appendToMenu(menu, "Requery\tCtrl+R", 
							self.onRequery, 
							bitmap=dIcons.getIconBitmap("requery"))
		
		if self.FormType != 'PickList':
			self._appendToMenu(menu, "Save Changes\tCtrl+S", 
							self.onSave, 
							bitmap=dIcons.getIconBitmap("save"))
			self._appendToMenu(menu, "Cancel Changes", 
							self.onCancel, 
							bitmap=dIcons.getIconBitmap("revert"))
		menu.AppendSeparator()

		
		if self.FormType != 'Edit':
			self._appendToMenu(menu, "Select First Record", 
							self.onFirst, 
							bitmap=dIcons.getIconBitmap("leftArrows"))
			self._appendToMenu(menu, "Select Prior Record\tCtrl+,", 
							self.onPrior, 
							bitmap=dIcons.getIconBitmap("leftArrow"))
			self._appendToMenu(menu, "Select Next Record\tCtrl+.", 
							self.onNext, 
							bitmap=dIcons.getIconBitmap("rightArrow"))
			self._appendToMenu(menu, "Select Last Record", 
							self.onLast, 
							bitmap=dIcons.getIconBitmap("rightArrows"))
		menu.AppendSeparator()
		
		if self.FormType == 'Normal':
			self._appendToMenu(menu, "New Record\tCtrl+N", 
							self.onNew, 
							bitmap=dIcons.getIconBitmap("blank"))
			self._appendToMenu(menu, "Delete Current Record", 
							self.onDelete, 
							bitmap=dIcons.getIconBitmap("delete"))
		return menu


	def setupMenu(self):
		""" Set up the navigation menu for this frame.

		Called whenever the primary bizobj is set or whenever this
		frame receives the focus.
		"""
		mb = self.GetMenuBar()

		menuIndex = mb.FindMenu("&Navigation")
		if menuIndex < 0:
			menuIndex = mb.GetMenuCount()-1
			if menuIndex < 0:
				menuIndex = 0

			### The intent is for the Navigation menu to be positioned before
			### the Help menu, but it isn't working. No matter what I set for
			### menuIndex, the nav menu always appears at the end on Linux, but
			### appears correctly on Mac and Win.
			mb.Insert(menuIndex, self.getMenu(), "&Navigation")


	def setupPageFrame(self):
		""" Set up the select/browse/edit/n pageframe.

		Default behavior is to set up a 3-page pageframe with 'Select', 
		'Browse', and 'Edit' pages. User may override and/or extend in 
		subclasses and overriding self.beforeSetupPageFrame(), 
		self.setupPageFrame, and/or self.afterSetupPageFrame().
		"""
		currPage = 0
		try:
			currPage = self.pageFrame.GetSelection()
			self.pageFrame.Destroy()
			chld = self.GetSizer().GetChildren()
			for c in chld:
				if c.IsSizer():
					if isinstance(c.GetSizer(), wx.NotebookSizer):
						self.GetSizer().Detach(c.GetSizer())
		except: pass
			
		if self.beforeSetupPageFrame():
			self.Freeze()
			self.pageFrame = dDataNavPageFrame.dDataNavPageFrame(self)
			nbSizer = wx.NotebookSizer(self.pageFrame)
			self.Sizer.append(nbSizer, "expand", 1)
			self.pageFrame.SetSelection(currPage)
			self.afterSetupPageFrame()
			self.Thaw()
			self.Sizer.layout()
			self.Refresh()
			
	def beforeSetupPageFrame(self): return True
	def afterSetupPageFrame(self): pass

	def onSetSelectionCriteria(self, evt):
		""" Occurs when the user chooses to set the selection criteria.
		"""
		self.pageFrame.SetSelection(0)

		
	def onBrowseRecords(self, evt):
		""" Occurs when the user chooses to browse the record set.
		"""
		self.pageFrame.SetSelection(1)

		
	def onEditCurrentRecord(self, evt):
		""" Occurs when the user chooses to edits the current record.
		"""
		self.pageFrame.SetSelection(2)


	def onChildView(self, evt):
		""" Occurs when the user chooses to edit a child view page.
		"""
		evtId = evt.GetId()
		page=3
		for child in self.childViews:
			if child['menuId'] == evtId:
				break
			page += 1
		self.pageFrame.SetSelection(page)
		
		
	def getColumnDefs(self, dataSource):
		""" Get the column definitions for the given data source.

		The column definitions provide information to the data navigation
		form to smartly construct the SQL statement, the browse grid, and 
		the edit form.

		Return the column definitions for the given dataSource,
		or an empty list if not found. Each item in the list represents
		a column, with the following keys defining column behavior:

			'tableName'   : The table name that contains the field.
							(string) (required)

			'fieldName'   : The field name in the bizobj.
							(string) (required)

			'caption'     : The column header caption - used in the browse 
							grid and as a default label for the items in 
							the edit page. 
							(string) (default: 'name')

			'type'        : The data type in xBase notation (C,I,N,D,T) 
							(char) (Required)

			'showGrid'    : Show column in the browse grid?
							(boolean) (default: True)

			'showEdit'    : Show field in the edit page?
							(boolean) (default: True)

			'editEdit'    : Allow editing of the field in the edit page?
							(boolean) (default: True)

			'selectTypes' : List of types of select queries that can be run
							for the field. If supplied, the field will have
							input field(s) automatically set up in the 
							pageframe's select page, so the user can enter
							the criteria. If not supplied, the user will not
							automatically be able to enter selection criteria.
							(list) (default: fields with 'C' will get an entry
							for selectType of 'stringMatchAll')

							The currently-supported selectTypes are:

								+ range: allow user to specify a high and a
										low value.

								+ value: user sets an explicit value.

								+ stringMatch: user enters a string, and the field
											is searched for occurances of that
											string (SQL LIKE with '%' appended
											and prepended).

								+ stringMatchAll: Like stringMatch but instead of
												the data field getting its own
												input field, all data fields with
												stringMatchAll share one input
												field on the select page.

		Use dDataNavForm.setColumnDefs() to set the definitions.
		"""
		try:
			columnDefs = self._columnDefs[dataSource]
		except KeyError:
			columnDefs = []
		return columnDefs


	def setFieldSpecs(self, xmlFile, tbl):
		""" Reads in the field spec file and creates the appropriate
		controls in the form. Also initializes the SQL Builder for
		this table.
		"""
		# First, get the field spec data into a dictionary.
		rawSpecs = fieldSpecParser.importFieldSpecs(xmlFile, tbl)
		relaKeys = [k for k in rawSpecs.keys() if k.find("::") > 0]
		self.RelationSpecs = {}
		self.FieldSpecs = rawSpecs.copy()
		for rk in relaKeys:
			self.RelationSpecs[rk] = rawSpecs[rk]
			del self.FieldSpecs[rk]
		
		if not self.preview:
			# Set up the SQL Builder in the bizobj:
			biz = self.getBizobj()
			biz.setFieldClause("")
			for fld in self.FieldSpecs.keys():
				fldInfo = self.FieldSpecs[fld]
				if int(fldInfo["editInclude"]) or int(fldInfo["listInclude"]):
					biz.addField("%s.%s as %s" % (tbl, fld, fld) )
			biz.setFromClause(tbl)
	
			self.childViews = []
			for child in self.getBizobj().getChildren():
				self.childViews.append({"dataSource": child.DataSource,
						"caption": child.Caption,
						"menuId": wx.NewId()})
		self.setupPageFrame()
		self.setupToolBar()
		if not self.preview:
			self.setupMenu()
	
	
	def setColumnDefs(self, dataSource, columnDefs):
		""" Set the grid column definitions for the given data source.

		See getGridColumnDefs for more explanation.
		""" 

		# Make sure unspecified items get default values or if 
		# the item is required don't set the columndefs.
		for column in columnDefs:
			if not column.has_key('tableName'):
				raise KeyError, "Column definition must include a table name."
			if not column.has_key('fieldName'):
				raise KeyError, "Column definition must include a field name."
			if not column.has_key('caption'):
				column['caption'] = column['name']
			if not column.has_key('type'):
				raise KeyError, "Column definition must include a data type."
			if not column.has_key('showGrid'):
				column['showGrid'] = True
			if not column.has_key('showEdit'):
				column['showEdit'] = True
			if not column.has_key('editEdit'):
				column['editEdit'] = True
			if not column.has_key('selectTypes'):
				column['selectTypes'] = []
				if column['type'] in ('C', 'M'):
					# column is string: add to stringMatchAll:
					column['selectTypes'].append('stringMatchAll')

		self._columnDefs[dataSource] = tuple(columnDefs)
		if dataSource == self.getBizobj().DataSource:
			self.afterSetPrimaryColumnDef()


	def getChildBehavior(self, dataSource):
		try:
			cb = self._childBehavior[dataSource]
		except KeyError:
			self.setChildBehavior(dataSource, {})
			cb = self._childBehavior[dataSource]
		return cb
	
	
	def setChildBehavior(self, dataSource, cb):
		if not cb.has_key('EnableDelete'):
			cb['EnableDelete'] = False
		if not cb.has_key('EnableEdit'):
			cb['EnableEdit'] = False
		if not cb.has_key('EnableNew'):
			cb['EnableNew'] = False
		self._childBehavior[dataSource] = cb
	
	
	def onRequery(self, evt):
		""" Override the dForm behavior by running the requery through the select page.
		"""
		self.pageFrame.GetPage(0).requery()


	def afterNew(self):
		""" dForm will call this after a new record has been successfully added.

		Make the edit page active, as a convenience to the user.
		"""
		self.pageFrame.SetSelection(2)

		
	def pickRecord(self):
		""" This form is a picklist, and the user chose a record in the grid.
		"""
		# Raise EVT_ITEMPICKED so the originating form can act
		self.raiseEvent(dEvents.ItemPicked)

				
	def _getFormType(self):
		try:
			return self._formType
		except AttributeError:
			return "Normal"
	
	def _getFormTypeEditorInfo(self):
		return {'editor': 'list', 'values': ['Normal', 'PickList', 'Edit']}
			
	def _setFormType(self, value):
		value = value.lower()
		if value == "normal":
			self._formType = "Normal"
		elif value == "picklist":
			self._formType = "PickList"
		elif value == "edit":
			self._formType = "Edit"
		else:
			raise ValueError, "Form type must be 'Normal', 'PickList', or 'Edit'."
			
	def _getRequeryOnLoad(self):
		try:
			return self._requeryOnLoad
		except AttributeError:
			return False
	def _setRequeryOnLoad(self, value):
		self._requeryOnLoad = bool(value)

	def _getFieldSpecs(self):
		return self._fieldSpecs
	def _setFieldSpecs(self, val):
		self._fieldSpecs = val
		
	def _getRelationSpecs(self):
		return self._relationSpecs
	def _setRelationSpecs(self, val):
		self._relationSpecs = val
		
	def _setDrawSizerOutlines(self, val):
		self._drawSizerOutlines = val
		# Need to update the pages
		for i in range(self.pageFrame.PageCount):
			pg = self.pageFrame.GetPage(i)
			if hasattr(pg, "drawSizerOutlines"):
				pg.drawSizerOutlines = val
	def _getDrawSizerOutlines(self):
		return self._drawSizerOutlines		
	

	# Property definitions:
	FormType = property(_getFormType, _setFormType, None,
				"Specifies the type of form this is:\n"
				"	Normal: a normal dataNav form.\n"
				"	PickList: only select/browse pages shown, and the form\n"
				"		is modal, returning the pk of the picked record.\n"
				"	Edit: modal version of normal, with no Select/Browse pages.\n"
				"		User code sends the pk of the record to edit.")

	RequeryOnLoad = property(_getRequeryOnLoad, _setRequeryOnLoad, None,
				"Specifies whether an automatic requery happens when the form is loaded.")
	
	FieldSpecs = property(_getFieldSpecs, _setFieldSpecs, None, 
			"Reference to the dictionary containing field behavior specs")

	RelationSpecs = property(_getRelationSpecs, _setRelationSpecs, None, 
			"Reference to the dictionary containing table relation specs")

	DrawSizerOutlines = property(_getDrawSizerOutlines, _setDrawSizerOutlines, None,
			"Controls whether outlines are drawn indicating the current state of the sizers on the form.")
