import wx
import dIcons
import dabo.dEvents as dEvents
import dForm, dDataNavPageFrame
import dabo.ui
from dabo.common import specParser
import os, random

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
		# When Save/Cancel/Requery are called, do we check the 
		# current primary bizobj, or do we use the main bizobj for
		# the form? Default is to only affect the current bizobj
		self.saveCancelRequeryAll = False
		# Used for turning sizer outline drawing on pages
		self._drawSizerOutlines = False
	
	
	def __init__(self, parent=None, previewMode=False, tbl=""):
		self.preview = previewMode
		self.previewDataSource = tbl
		dDataNavForm.doDefault(parent)
		# We will need to set these separated if in Preview mode.
		self.rowNumber = 0
		self.rowCount = 0
		

	def _afterInit(self):
		dDataNavForm.doDefault()
		if self.FormType == 'PickList':
			# Map escape key to close the form
			anId = wx.NewId()
			self.acceleratorTable.append((wx.ACCEL_NORMAL, wx.WXK_ESCAPE, anId))
			self.Bind(wx.EVT_MENU, self.Close, id=anId)

			
	def __onActivate(self, evt):
		dDataNavForm.doDefault(evt)
		if self.RequeryOnLoad and not self._requeried:
			self._requeried = True
			self.pageFrame.GetPage(0).requery()
		
	
	def save(self, dataSource=None):
		if dataSource is None:
			if self.saveCancelRequeryAll:
				dataSource = self._mainTable
		return dDataNavForm.doDefault(dataSource)
	
	
	def cancel(self, dataSource=None):
		if dataSource is None:
			if self.saveCancelRequeryAll:
				dataSource = self._mainTable
		return dDataNavForm.doDefault(dataSource)
	
	
	def requery(self, dataSource=None):
		if dataSource is None:
			if self.saveCancelRequeryAll:
				dataSource = self._mainTable
		return dDataNavForm.doDefault(dataSource)
	
	
	def confirmChanges(self):
		if self.preview:
			# Nothing to check
			return True
		else:
			return dDataNavForm.doDefault()
	
	
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



		toolBar.AddSeparator()
		self._appendToToolBar(toolBar, "Show SQL", dIcons.getIconBitmap("zoomOut"),
					self.onShowSQL, "Show the last executed SQL statement")


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

# 		if self.FormType != 'PickList':
# 			print "PICKLIST"
# 			i = 4
# 			for child in self.childViews:
# 				self._appendToMenu(menu, "View %s\tAlt+%s" % (child['caption'], i) ,
# 								self.onChildView, 
# 								bitmap=dIcons.getIconBitmap("childview"),
# 								menuId = child['menuId'])
# 				i += 1
			
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
			self.pageFrame.addSelectPage()
			self.pageFrame.addBrowsePage()
			if self.preview:
				ds = self.previewDataSource
			else:
				ds = self.getBizobj().DataSource
			self.addEditPages(ds)
			self.pageFrame.SetSelection(currPage)
			self.afterSetupPageFrame()
			self.Thaw()
			self.Sizer.layout()
			self.Refresh()

			
	def beforeSetupPageFrame(self): return True
	def afterSetupPageFrame(self): pass
	
	def addEditPages(self, ds):
		title = "Edit: " + ds.title()
		self.pageFrame.addEditPage(ds, title)
		biz = self.getBizobj(ds)
		if biz:
			for child in biz.getChildren():
				self.addEditPages(child.DataSource)

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


	def onShowSQL(self, evt):
		sql = self.getPrimaryBizobj().getSQL()
		if sql is None:
			sql = "-Nothing executed yet-"
		mb = dabo.ui.dMessageBox.info(sql, "Last SQL")

	def setFieldSpecs(self, xml, tbl):
		""" Reads in the field spec file and creates the appropriate
		controls in the form. 
		"""
		self._allFieldSpecs = self.parseXML(xml, "Field")
		self._mainTable = tbl


	def setRelationSpecs(self, xml, bizModule):
		""" Creates any child bizobjs used by the form, and establishes
		the relations with the parent bizobj
		"""
		self.RelationSpecs = self.parseXML(xml, "Relation")
		primaryBizobj = self.getPrimaryBizobj()
		# This will make sure all relations and sub-relations are set.
		newBizobjs = primaryBizobj.addChildByRelationDict(self.RelationSpecs, 
				bizModule)
		# If we added any bizobjs, add them to the form's collection, too
		for biz in newBizobjs:
			self.addBizobj(biz)

	
	def parseXML(self, xml, specType):
		""" Accepts either a file or raw XML, and handles talking with the 
		specParser class. Since that class requires a file, this method will
		create a temp file if raw XML is passed.
		"""
		# See if we were passed a file reference, or raw XML.
		raw = not os.path.exists(xml)
		if raw:
			fname = "tmp" + str(random.randint(100000,1000000)) + ".fsxml"
			open(fname, "w").write(xml)
		else:
			# A file reference was passed
			fname = xml
		
		if specType.lower() == "relation":
			ret = specParser.importRelationSpecs(fname)
		else:
			ret = specParser.importFieldSpecs(fname)
		if raw:
			os.remove(fname)
		return ret
		
		
	def creation(self):
		""" Called after all the specs for the form have been set, and
		after any other settings that need to be made have been made.
		It initializes the SQL Builder, and creates the menu, toolbar  and
		pageframe for the form.
		"""
		errMsg = self.beforeCreation()
		if errMsg:
			raise dException.dException, errMsg
		if not self.preview:
			# Set up the SQL Builder in the bizobj:
			tbl = self._mainTable
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
		self.afterCreation()
	
	
	def setPrimaryBizobjToDefault(self, ds):
		""" This method is called when we leave an editing page. The
		intent is that if we move to another editing page, it will set the
		form's primary bizobj to the appropriate one for that page, 
		so we don't need to do anything. But if they switch to the 
		browse or select page, we want to set the primary bizobj back
		to the one for the form's main table.
		"""
		biz = self.getBizobj()
		bizDS = biz.DataSource
		if bizDS == ds:
			# We didn't switch to another editing page, so reset it back
			# to the main bizobj
			if ds != self._mainTable:
				# Don't reset if it it's already the main bizobj
				self.setPrimaryBizobj(self._mainTable)
		
	
	def getBizobjsToCheck(self):
		""" The primary bizobj may be for one of the child pages.
		Therefore, we should return the main bizobj here
		"""
		return [self.getBizobj(dataSource=self._mainTable)]
		
	
	def beforeCreation(self):
		""" Hook method available to customize form creation settings
		before anything on the form, its toolbar, or its menu is created.
		Returning any string from this method will prevent form creation
		from happening, and raise an error.
		"""
		pass
		
	def afterCreation(self):
		""" Hook method available to customize the form after all its
		components have been created.
		"""
		pass
	
	
	def getFieldSpecsForTable(self, tbl):
		""" Returns the field specs for the given table. If there is no entry
		for the requested table, it returns None.
		"""
		ret = None
		try:
			ret = self._allFieldSpecs[tbl]
		except: pass
		return ret
		
	
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
		return self._allFieldSpecs[self._mainTable]
	def _setFieldSpecs(self, val):
		self._allFieldSpecs[self._mainTable] = val
		
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
