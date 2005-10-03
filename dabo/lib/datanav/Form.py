import os
import random
import wx
import dabo.dEvents as dEvents
import dabo.ui
from dabo.common import specParser
from dabo.dLocalize import _, n_
import PageFrame
import Grid

dabo.ui.loadUI("wx")

class Form(dabo.ui.dForm):
	""" This is a dForm but with the following added controls:
		+ Navigation Menu
		+ Navigation ToolBar
		+ PageFrame with 3 pages by default:
			+ Select : Enter sql-select criteria.
			+ Browse : Browse the result set and pick an item to edit.
			+ Edit	 : Edit the current record in the result set.
	"""
	def beforeInit(self):
		super(Form, self).beforeInit()
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
		# What sort of pageframe style do we want?
		# Choices are "tabs", "list" or "select"
		self.pageFrameStyle = "tabs"
		# Where do the pageframe tabs/selector go?
		# Choices = Top (default), Bottom, Left or Right
		self.tabPosition = "Top"
		# We want a toolbar
		self.ShowToolBar = True
		# The list of _tempfiles will be deleted when the form is destroyed:
		self._tempFiles = []
	

	def _initEvents(self):
		self.bindEvent(dEvents.Close, self._onClose)
		Form.doDefault()


	def __init__(self, parent=None, previewMode=False, tbl="", *args, **kwargs):
		self.preview = previewMode
		self.previewDataSource = tbl
		super(Form, self).__init__(parent, *args, **kwargs)
		# We will need to set these separated if in Preview mode.
		self.rowNumber = 0
		self.rowCount = 0

	def _afterInit(self):
		#Form.doDefault()
		super(Form, self)._afterInit()
		if self.FormType == 'PickList':
			# Map escape key to close the form
			self.bindKey("esc", self.Close)

		
	def _onClose(self, evt):
		for f in self._tempFiles:
			try:
				os.remove(f)
			except:
				# perhaps it is already gone, removed explicitly.
				pass

	
	def save(self, dataSource=None):
		if dataSource is None:
			if self.saveCancelRequeryAll:
				dataSource = self._mainTable
		#return Form.doDefault(dataSource)
		return super(Form, self).save(dataSource)
	
	
	def cancel(self, dataSource=None):
		if dataSource is None:
			if self.saveCancelRequeryAll:
				dataSource = self._mainTable
		#return Form.doDefault(dataSource)
		return super(Form, self).cancel(dataSource)
	
	
	def requery(self, dataSource=None):
		if dataSource is None:
			if self.saveCancelRequeryAll:
				dataSource = self._mainTable
		#return Form.doDefault(dataSource)
		return super(Form, self).requery(dataSource)
	
	
	def confirmChanges(self):
		if self.preview:
			# Nothing to check
			return True
		else:
			#return Form.doDefault()
			return super(Form, self).confirmChanges()
	
	
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
		tb = self.ToolBar
		tb.MaxWidth = 16
		tb.MaxHeight = 16
		
		if self.FormType != 'Edit':
			self.appendToolBarButton("First", "leftArrows", bindfunc=self.onFirst, 
					tip=_("First"), help=_("Go to the first record"))
			self.appendToolBarButton("Prior", "leftArrow", bindfunc=self.onPrior, 
					tip=_("Prior"), help=_("Go to the prior record"))
			self.appendToolBarButton("Requery", "requery", bindfunc=self.onRequery, 
					tip=_("Requery"), help=_("Requery dataset"))
			self.appendToolBarButton("Next", "rightArrow", bindfunc=self.onNext, 
					tip=_("Next"), help=_("Go to the next record"))
			self.appendToolBarButton("Last", "rightArrows", bindfunc=self.onLast, 
					tip=_("Last"), help=_("Go to the last record"))
			tb.appendSeparator()

		if self.FormType == 'Normal':
			self.appendToolBarButton("New", "blank", bindfunc=self.onNew, 
					tip=_("New"), help=_("Add a new record"))
			self.appendToolBarButton("Delete", "delete", bindfunc=self.onDelete, 
					tip=_("Delete"), help=_("Delete this record"))
			tb.appendSeparator()

		if self.FormType != 'PickList':
			self.appendToolBarButton("Save", "save", bindfunc=self.onSave, 
					tip=_("Save"), help=_("Save changes"))
			self.appendToolBarButton("Cancel", "revert", bindfunc=self.onCancel, 
					tip=_("Cancel"), help=_("Cancel changes"))
			tb.appendSeparator()
			self.appendToolBarButton("SQL", "zoomOut", bindfunc=self.onShowSQL, 
					tip=_("Show SQL"), help=_("Show the last executed SQL statement"))


	def getMenu(self):
		menu = super(Form, self).getMenu()
		menu.Caption = _("&Navigation")
  
		menu.append(_("Set Selection Criteria")+"\tAlt+1", 
				bindfunc=self.onSetSelectionCriteria, bmp="checkMark",
				help=_("Set the selection criteria for the recordset."))
		menu.append(_("Browse Records")+"\tAlt+2", 
				bindfunc=self.onBrowseRecords, bmp="browse",
				help=_("Browse the records in the current recordset."))
  
		# Add one edit menu item for every edit page (every page past the second)
		for index in range(2, self.pageFrame.PageCount):
			title = "%s\tAlt+%d" % (_(self.pageFrame.Pages[index].Caption),
					index+1)
			menu.append(title, bindfunc=self.onEditCurrentRecord, bmp="edit",
					help=_("Edit the fields of the currently selected record."),
					Tag=self.pageFrame.Pages[index].DataSource)
			menu.appendSeparator()
  
		if self.FormType != "Edit":
			menu.append(_("Requery")+"\tCtrl+R", bindfunc=self.onRequery, bmp="requery",
					help=_("Get a new recordset from the backend."), menutype="check")		
		if self.FormType != "PickList":
			menu.append(_("Save Changes")+"\tCtrl+S", bindfunc=self.onSave, bmp="save",
					help=_("Save any changes made to the records."))	
			menu.append(_("Cancel Changes"), bindfunc=self.onCancel, bmp="revert",
					help=_("Cancel any changes made to the records."))
			menu.appendSeparator()
  
		
		if self.FormType != "Edit":
			menu.append(_("Select First Record"), bindfunc=self.onFirst, 
					bmp="leftArrows", help=_("Go to the first record in the set.")) 
			menu.append(_("Select Prior Record")+"\tCtrl+,", bindfunc=self.onPrior, 
					bmp="leftArrow", help=_("Go to the prior record in the set."))	
			menu.append(_("Select Next Record")+"\tCtrl+.", bindfunc=self.onNext, 
					bmp="rightArrow", help=_("Go to the next record in the set."))
			menu.append(_("Select Last Record"), bindfunc=self.onLast, 
					bmp="rightArrows", help=_("Go to the last record in the set."))
			menu.appendSeparator()
		
		if self.FormType == "Normal":
			menu.append(_("New Record")+"\tCtrl+N", bindfunc=self.onNew, bmp="blank",
					help=_("Add a new record to the dataset."))
			menu.append(_("Delete Current Record"), bindfunc=self.onDelete, bmp="delete",
					help=_("Delete the current record from the dataset."))
			menu.appendSeparator()

		return menu


	def setupMenu(self):
		""" Set up the navigation menu for this frame.

		Called whenever the primary bizobj is set or whenever this
		frame receives the focus.
		"""
		mb = self.MenuBar
		menuIndex = mb.FindMenu(_("&Navigation"))
		
		if menuIndex < 0:
			menuIndex = mb.GetMenuCount()-1
			if menuIndex < 0:
				menuIndex = 0

			### The intent is for the Navigation menu to be positioned before
			### the Help menu, but it isn't working. No matter what I set for
			### menuIndex, the nav menu always appears at the end on Linux, but
			### appears correctly on Mac and Win.
			mb.insertMenu(menuIndex, self.getMenu())


	def setupPageFrame(self):
		""" Set up the select/browse/edit/n pageframe.

		Default behavior is to set up a 3-page pageframe with 'Select', 
		'Browse', and 'Edit' pages. User may override and/or extend in 
		subclasses and overriding self.beforeSetupPageFrame(), 
		self.setupPageFrame, and/or self.afterSetupPageFrame().
		"""
		currPage = 0
		biz = self.getBizobj()
		try:
			currPage = self.pageFrame.SelectedPage
			self.pageFrame.release()
			chld = self.Sizer.Children
			for c in chld:
				if c.IsSizer():
					if isinstance(c.Sizer, wx.NotebookSizer):
						self.Sizer.Detach(c.Sizer)
		except: pass
		
		if self.beforeSetupPageFrame():
			self.pageFrame = PageFrame.PageFrame(self, tabStyle=self.pageFrameStyle,
					TabPosition=self.tabPosition)
			self.Sizer.append(self.pageFrame, "expand", 1)
			self.pageFrame.addSelectPage()
			self.pageFrame.addBrowsePage()
			if self.preview:
				ds = self.previewDataSource
			else:
				ds = biz.DataSource
			self.addEditPages(ds)
			self.pageFrame.SelectedpageNum = currPage
			self.afterSetupPageFrame()
			self.Sizer.layout()
			self.refresh()

		if self.RequeryOnLoad:
			dabo.ui.callAfter(self.PageFrame.Pages[0].requery)
			
	def beforeSetupPageFrame(self): return True
	def afterSetupPageFrame(self): pass
	
	def addEditPages(self, ds):
		biz = self.getBizobj(ds)
		if biz:
			title = _("Edit") + " " + _(biz.Caption)
		else:
			title = _("Edit")
		self.addEditPage(ds, title)
		if biz:
			for child in biz.getChildren():
				self.addEditPages(child.DataSource)


	def addEditPage(self, ds, title, pageClass=None):
		"""Called when it is time to add the edit page for the passed datasource.

		Subclasses may override, or send their own pageClass.
		"""
		self.pageFrame.addEditPage(ds, title, pageClass)


	def onSetSelectionCriteria(self, evt):
		""" Occurs when the user chooses to set the selection criteria.
		"""
		self.pageFrame.SelectedPage = 0

		
	def onBrowseRecords(self, evt):
		""" Occurs when the user chooses to browse the record set.
		"""
		self.pageFrame.SelectedPage = 1

		
	def onEditCurrentRecord(self, evt):
		""" Occurs when the user chooses to edit the current record.
		"""
		# We stored the datasource in the menu item's Tag property when
		# the menu was created.
		self.pageFrame.editByDataSource(evt.EventObject.Tag)


	def onShowSQL(self, evt):
		sql = self.PrimaryBizobj.getSQL()
		if sql is None:
			sql = "-Nothing executed yet-"
			mb = dabo.ui.info(sql, _("Last SQL"))
			return
		dlg = dabo.ui.dDialog(self, Caption=_("Last SQL"))
		eb = dlg.addObject(dabo.ui.dEditBox, ReadOnly=True, Value=sql, Size=(400, 400))
		dlg.Sizer.append1x(eb)
		dlg.show()
		dlg.release()


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
		primaryBizobj = self.PrimaryBizobj
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
		if specType.lower() == "relation":
			ret = specParser.importRelationSpecs(xml)
		else:
			ret = specParser.importFieldSpecs(xml)
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
			## pkm: no, that is in the bizobj now.
			"""
				tbl = self._mainTable
				biz = self.getBizobj()
				biz.setFieldClause("")
				fromClause = tbl
				for fld in self.FieldSpecs.keys():
					fldInfo = self.FieldSpecs[fld]
					#if int(fldInfo["editInclude"]) or int(fldInfo["listInclude"]):
					## pkm: No! If the field is included in the fieldSpec file, it needs to
					##		be part of the SQL fields clause, whether or not it is to be
					##		included in in the browse or edit pages. Consider, for example,
					##		the pk field: That needs to be included but you most likely don't
					##		want to show it in the UI. There could be plenty of fields that
					##		the developer wants to grab but not show the user.
					
					expression = "%s.%s" % (tbl, fld)
					biz.addField("%s as %s" % (expression, fld) )
				
				biz.setFromClause(fromClause)
		
				self.childViews = []
				for child in self.getBizobj().getChildren():
					self.childViews.append({"dataSource": child.DataSource,
							"caption": child.Caption,
							"menuId": wx.NewId()})
			"""
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
				# Note: we can send the data source, and the form will
				# correctly set the matching bizobj.
				self.PrimaryBizobj = self._mainTable
		
	
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


	def onNew(self, evt):
		self.pageFrame.newByDataSource(self.getBizobj().DataSource)


	def pickRecord(self):
		""" This form is a picklist, and the user chose a record in the grid.
		"""
		# Raise EVT_ITEMPICKED so the originating form can act
		self.raiseEvent(dEvents.ItemPicked)

	
	def getEditClassForField(self, fieldName):
		"""Hook: User code can supply a class of control to use on the edit page."""
		return None


	def getReportForm(self, mode):
		"""Returns the rfxml to generate a report for the dataset.

		The mode is one of "all" or "one", and determines if the entire recordset
		is printed, or just the current record. This allows for different report
		formats for each case.

		The rfxml can come from a few places, in descending precedence:
			1) if self.ReportForm["all"] or self.ReportForm["one"] exists,
			   that will be used.    *** NOT IMPLEMENTED YET ***

			2) if self.ReportFormFile["all"] or self.ReportFormFile["one"] exists,
			   that will be used.    *** NOT IMPLEMENTED YET ***

			3) if self.Application.HomeDirectory/reports/datanav-<cursorname>-(all|one).rfxml
			   exists, that will be used. IOW, drop in a properly named rfxml file into 
			   the reports directory underneath your application home, and it will be used
			   automatically.        *** NOT IMPLEMENTED YET ***

			4) a generic report form will be generated. If mode=="all", the fields displayed
			   will be as defined in the browse page. If mode=="one", the fields displayed
			   will be as defined in the edit page.   *** PARTIALLY IMPLEMENTED ***
		"""
		grid = self.PageFrame.Pages[1].BrowseGrid

		rfxml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>

<report>
	<title>"""
		rfxml += "Quick Report: %s" % self.Caption
		rfxml += """</title>
	<pageHeader>
		<height>"0.75 in"</height>
		<objects>
"""
		x = 0
		reportWidth = 0
		horBuffer = 3
		vertBuffer = 5
		for col in grid.Columns:
			coldict = {"caption": col.Caption, "fontSize": col.HeaderFontSize,
			           "width": col.Width, "x": x+horBuffer}
			coldict["horBuffer"] = horBuffer
			coldict["vertBuffer"] = vertBuffer
			coldict["rectWidth"] = coldict["width"] + (2*horBuffer)
			coldict["rectHeight"] = grid.HeaderHeight
			hAlign = col.HeaderHorizontalAlignment
			if hAlign is None:
				hAlign = grid.HeaderHorizontalAlignment
			coldict["textHorAlignment"] = "'%s'" % hAlign.lower().split(" ")[0]
			coldict["rectX"] = x
			vAlign = col.HeaderVerticalAlignment	
			if vAlign is None:
				vAlign = grid.HeaderHorizontalAlignment
			vAlign = vAlign[:3]
			if vAlign == "Cen":
				textY = (coldict["rectHeight"] / 2) - (coldict["fontSize"]/2)
			elif vAlign == "Top":
				textY = coldict["rectHeight"] - coldict["fontSize"]
			else:
				textY = vertBuffer
			coldict["textY"] = textY

			x += coldict["rectWidth"]
			if x > 720:
				# We'll run off the edge of the page, ignore the rest:
				break

			reportWidth = x

			rfxml += """
			<rect>
				<width>%(rectWidth)s</width>
				<height>%(rectHeight)s</height>
				<strokeWidth>0.25</strokeWidth>
				<fillColor>(0.9,0.9,0.9)</fillColor>
				<x>%(rectX)s</x>
				<y>0</y>
			</rect>
			<string>
				<expr>"%(caption)s"</expr>
				<height>%(fontSize)s</height>
				<align>%(textHorAlignment)s</align>
				<fontSize>%(fontSize)s</fontSize>
				<width>%(width)s</width>
				<x>%(x)s</x>
				<y>%(textY)s</y>
			</string>""" % coldict

		rfxml += """
			<string>
				<align>"center"</align>
				<valign>"top"</valign>
				<borderWidth>"0 pt"</borderWidth>
				<expr>self.ReportForm["title"]</expr>
				<fontName>"Helvetica"</fontName>
				<fontSize>14</fontSize>
				<hAnchor>"center"</hAnchor>
				<height>15.96</height>
				<name>title</name>
				<width>%s</width>
				<x>%s</x>
				<y>"0.6 in"</y>
			</string>""" % (reportWidth, reportWidth/2)
				
		rfxml += """
		</objects>
	</pageHeader>

	<detail>
		<height>None</height>
		<objects>"""
		x = 0
		horBuffer = 3
		vertBuffer = 5
		for col in grid.Columns:
			coldict = {"caption": col.Caption, "field": col.DataField, 
			           "width": col.Width, "fontSize": col.FontSize,
			           "x": x+horBuffer}
			coldict["horBuffer"] = horBuffer
			coldict["vertBuffer"] = vertBuffer
			coldict["rectWidth"] = coldict["width"] + (2*horBuffer)
			coldict["rectHeight"] = col.Parent.RowHeight
			coldict["textHorAlignment"] = "'%s'" % col.HorizontalAlignment.lower().split(" ")[0]
			coldict["rectX"] = x
			vAlign = col.VerticalAlignment	[:3]
			if vAlign == "Cen":
				textY = (coldict["rectHeight"] / 2) - (coldict["fontSize"]/2)
			elif vAlign == "Top":
				textY = coldict["rectHeight"] - coldict["fontSize"]
			else:
				textY = vertBuffer
			coldict["textY"] = textY

			x += coldict["rectWidth"]
			if x > 720:
				# We'll run off the edge of the page, ignore the rest:
				break

			rfxml += """
			<rect>
				<width>%(rectWidth)s</width>
				<height>%(rectHeight)s</height>
				<strokeWidth>0.25</strokeWidth>
				<x>%(rectX)s</x>
				<y>0</y>
			</rect>
			<string>
				<expr>str(self.Record["%(field)s"])</expr>
				<height>%(fontSize)s</height>
				<align>%(textHorAlignment)s</align>
				<fontSize>%(fontSize)s</fontSize>
				<width>%(width)s</width>
				<x>%(x)s</x>
				<y>%(textY)s</y>
			</string>""" % coldict

		orientation = "portrait"
		if x > 504:
			# switch to landscape
			orientation = "landscape"
		
		rfxml += """
		</objects>
	</detail>

	<page>
		<marginBottom>".5 in"</marginBottom>
		<marginLeft>".5 in"</marginLeft>
		<marginRight>".5 in"</marginRight>
		<marginTop>".25 in"</marginTop>
		<orientation>"%s"</orientation>
		<size>"letter"</size>
	</page>

</report>
""" % orientation
		return rfxml

				
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


	def _getBrowseGridClass(self):
		try:
			val = self._browseGridClass
		except AttributeError:
			val = Grid.Grid
		return val

	def _setBrowseGridClass(self, val):
		assert issubclass(val, Grid.Grid)
		self._browseGridClass = val		


	def _getRelationSpecs(self):
		return self._relationSpecs
	def _setRelationSpecs(self, val):
		self._relationSpecs = val
		
	# Property definitions:
	FormType = property(_getFormType, _setFormType, None,
			"Specifies the type of form this is:\n"
			"	Normal: a normal dataNav form.\n"
			"	PickList: only select/browse pages shown, and the form\n"
			"		is modal, returning the pk of the picked record.\n"
			"	Edit: modal version of normal, with no Select/Browse pages.\n"
			"		User code sends the pk of the record to edit.")

	BrowseGridClass = property(_getBrowseGridClass, _setBrowseGridClass, None,
			"""Specifies the class to use for the browse grid.""")

	RequeryOnLoad = property(_getRequeryOnLoad, _setRequeryOnLoad, None,
			"Specifies whether an automatic requery happens when the form is loaded.")
	
	FieldSpecs = property(_getFieldSpecs, _setFieldSpecs, None, 
			"Reference to the dictionary containing field behavior specs")

	RelationSpecs = property(_getRelationSpecs, _setRelationSpecs, None, 
			"Reference to the dictionary containing table relation specs")
