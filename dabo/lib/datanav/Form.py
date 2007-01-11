import os
import random
import traceback
import wx
import dabo.dEvents as dEvents
import dabo.ui
from dabo.lib.specParser import importRelationSpecs, importFieldSpecs
from dabo.dLocalize import _, n_
import dabo.lib.reportUtils as reportUtils
import PageFrame
import Page
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
		# We want the status bar showing record information
		self._autoUpdateStatusText = True
		# The list of _tempfiles will be deleted when the form is destroyed:
		self._tempFiles = []
		# Do we automatically add edit pages for child bizobjs?
		self._addChildEditPages = True
	

	def _initEvents(self):
		self.bindEvent(dEvents.Close, self._onClose)
		self.super()


	def __init__(self, parent=None, previewMode=False, tbl="", *args, **kwargs):
		self.preview = previewMode
		self.previewDataSource = tbl
		super(Form, self).__init__(parent, *args, **kwargs)
		# We will need to set these separated if in Preview mode.
		self.rowNumber = 0
		self.rowCount = 0
		# Set a default size
		self.Size = (640, 480)


	def _afterInit(self):
		super(Form, self)._afterInit()
		if self.FormType == 'PickList':
			# The form is a picklist, which pops up so the user can choose a record,
			# and then hides itself afterwards. In addition, the picklist should hide
			# itself when other certain conditions are met.
			def _onHide(evt):
				dabo.ui.callAfter(self.hide)

			# Pressing Esc hides the form
			self.bindKey("esc", _onHide)
	
			# Deactivating hides the form
			self.bindEvent(dEvents.Deactivate, _onHide)


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
		## The bizobj may have made some changes to the data during the save, so 
		## make sure it is reflected on screen by calling update() afterwards.
		ret = super(Form, self).save(dataSource)
		self.update()
		return ret
	
	
	def cancel(self, dataSource=None):
		if dataSource is None:
			if self.saveCancelRequeryAll:
				dataSource = self._mainTable
		return self.super(dataSource)
	
	def requery(self, dataSource=None):
		if dataSource is None:
			if self.saveCancelRequeryAll:
				dataSource = self._mainTable
		return self.super(dataSource)
	
	def confirmChanges(self):
		if self.preview:
			# Nothing to check
			return True
		else:
			return self.super()
	
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
		if tb.Children:
			# It's already been set up
			return
		tb.MaxWidth = 16
		tb.MaxHeight = 16
		
		if self.FormType != 'Edit':
			self.appendToolBarButton("First", "leftArrows", OnHit=self.onFirst, 
					tip=_("First"), help=_("Go to the first record"))
			self.appendToolBarButton("Prior", "leftArrow", OnHit=self.onPrior, 
					tip=_("Prior"), help=_("Go to the prior record"))
			self.appendToolBarButton("Requery", "requery", OnHit=self.onRequery, 
					tip=_("Requery"), help=_("Requery dataset"))
			self.appendToolBarButton("Next", "rightArrow", OnHit=self.onNext, 
					tip=_("Next"), help=_("Go to the next record"))
			self.appendToolBarButton("Last", "rightArrows", OnHit=self.onLast, 
					tip=_("Last"), help=_("Go to the last record"))
			tb.appendSeparator()

		if self.FormType == 'Normal':
			self.appendToolBarButton("New", "blank", OnHit=self.onNew, 
					tip=_("New"), help=_("Add a new record"))
			self.appendToolBarButton("Delete", "delete", OnHit=self.onDelete, 
					tip=_("Delete"), help=_("Delete this record"))
			tb.appendSeparator()

		if self.FormType != 'PickList':
			self.appendToolBarButton("Save", "save", OnHit=self.onSave, 
					tip=_("Save"), help=_("Save changes"))
			self.appendToolBarButton("Cancel", "revert", OnHit=self.onCancel, 
					tip=_("Cancel"), help=_("Cancel changes"))
			tb.appendSeparator()

		if self.FormType != "Edit":
			self.appendToolBarButton("SQL", "zoomNormal", OnHit=self.onShowSQL, 
					tip=_("Show SQL"), help=_("Show the last executed SQL statement"))

		if self.FormType == "Normal":
			self.appendToolBarButton(_("Quick Report"), "print",
					OnHit=self.onQuickReport, tip=_("Quick Report"),
					help=_("Run a Quick Report on the current dataset"))


	def getMenu(self):
		menu = super(Form, self).getMenu()
		menu.Caption = _("&Actions")

		menu.append(_("Set Selection &Criteria")+"\tAlt+1", 
				OnHit=self.onSetSelectionCriteria, bmp="checkMark",
				help=_("Set the selection criteria for the recordset."))

		menu.append(_("&Browse Records")+"\tAlt+2", 
				OnHit=self.onBrowseRecords, bmp="browse",
				help=_("Browse the records in the current recordset."))

		# Add one edit menu item for every edit page (every page past the second)
		if self.FormType != "PickList":
			for index in range(2, self.pageFrame.PageCount):

				if index == 2:

					title = "&%s\tAlt+3" % (_(self.pageFrame.Pages[index].Caption))

				else:

					title = "%s\tAlt+%d" % (_(self.pageFrame.Pages[index].Caption),

							index+1)

				menu.append(title, OnHit=self.onEditCurrentRecord, bmp="edit",
						help=_("Edit the fields of the currently selected record."),
						Tag=self.pageFrame.Pages[index].DataSource)
				menu.appendSeparator()

		if self.FormType != "Edit":
			menu.append(_("&Requery")+"\tCtrl+R", OnHit=self.onRequery, bmp="requery",
					help=_("Get a new recordset from the backend."), menutype="check")		
	
		if self.FormType != "PickList":
			menu.append(_("&Save Changes")+"\tCtrl+S", OnHit=self.onSave, bmp="save",
					help=_("Save any changes made to the records."))	
			menu.append(_("&Cancel Changes"), OnHit=self.onCancel, bmp="revert",
					help=_("Cancel any changes made to the records."))
			menu.appendSeparator()
		
			# On Mac, altKey is "Ctrl", which translates to "Command". On other
			# platforms, altKey is "Alt". This lets us use the arrow keys for 
			# navigation without conflicting with native text editing functions.
			altKey = "Alt"
			if self.Application.Platform.lower() == "mac":
				altKey = "Ctrl"

			menu.append(_("Select &First Record")+"\t%s+UP" % altKey, 
					OnHit=self.onFirst, bmp="leftArrows", 
					help=_("Go to the first record in the set.")) 
			menu.append(_("Select &Prior Record")+"\t%s+LEFT" % altKey, 
					OnHit=self.onPrior,bmp="leftArrow", 
					help=_("Go to the prior record in the set."))	
			menu.append(_("Select Ne&xt Record")+"\t%s+RIGHT" % altKey, 
					OnHit=self.onNext, bmp="rightArrow", 
					help=_("Go to the next record in the set."))
			menu.append(_("Select &Last Record")+"\t%s+DOWN" % altKey, 
					OnHit=self.onLast, bmp="rightArrows", 
					help=_("Go to the last record in the set."))
			menu.appendSeparator()
		
		if self.FormType == "Normal":
			menu.append(_("&New Record")+"\tCtrl+N", OnHit=self.onNew, bmp="blank",
					help=_("Add a new record to the dataset."))
			menu.append(_("&Delete Current Record"), OnHit=self.onDelete, bmp="delete",
					help=_("Delete the current record from the dataset."))
			menu.appendSeparator()

		if self.FormType != "Edit":
			menu.append(_("Show S&QL"), OnHit=self.onShowSQL, bmp="zoomNormal")

		if self.FormType == "Normal":
			menu.append(_("Quick &Report"), OnHit=self.onQuickReport, bmp="print",
					DynamicEnabled=self.enableQuickReport)

		return menu


	def onDelete(self, evt):
		super(Form, self).onDelete(evt)
		# Make sure that the grid is properly updated.
		self.PageFrame.Pages[1].BrowseGrid.refresh()


	def enableQuickReport(self):
		## Can't enable quick report unless the dataset has been requeried once and
		## the browse grid exists (because it gets the layout from the browse grid).
		ret = True
		try:
			self.PageFrame.Pages[1].BrowseGrid
		except AttributeError:
			ret = False
		return ret


	def setupMenu(self):
		""" Set up the action menu for this frame.

		Called when the form is created and also when the fieldspecs are set.
		"""
		mb = self.MenuBar
		menuIndex = mb.getMenuIndex(_("Actions"))
		
		if menuIndex is not None:
			mb.remove(menuIndex)

		# We want the action menu right after the view menu:
		menuIndex = mb.getMenuIndex(_("View"))
		if menuIndex is None:
			# punt:
			menuIndex = 2
		menuIndex += 1

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
			self.pageFrame.unbindEvent()
			self.pageFrame.release()
			del self.__dict__["PageFrame"]
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
			if self.FormType != "PickList":
				self.addEditPages(ds)
			self.pageFrame.SelectedpageNum = currPage
			self.afterSetupPageFrame()
			self.Sizer.layout()
			self.refresh()

	def beforeSetupPageFrame(self): return True
	def afterSetupPageFrame(self): pass
	
	def addEditPages(self, ds):
		biz = self.getBizobj(ds)
		if biz:
			title = _("Edit") + " " + _(biz.Caption)
		else:
			title = _("Edit")
		self.addEditPage(ds, title)
		if biz and self.AddChildEditPages:
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
		sql = self.PrimaryBizobj.LastSQL
		if sql is None:
			sql = "-Nothing executed yet-"
		dlg = dabo.ui.dDialog(self, Caption=_("Last SQL"))
		eb = dlg.addObject(dabo.ui.dEditBox, ReadOnly=True, Value=sql, 
				FontFace="Monospace", Size=(400, 400))
		dlg.Sizer.append1x(eb)
		dlg.show()
		dlg.release()


	def onQuickReport(self, evt):
		# May not have records if called via toolbar button
		if not self.enableQuickReport():
			dabo.ui.exclaim(_("Sorry, there are no records to report on."), title=_("No Records"))
			return
		if self.preview:
			# Just previewing 
			dabo.ui.info(message="Not available in preview mode", 
					title = "Preview Mode")
			return

		class ReportFormatDialog(dabo.ui.dOkCancelDialog):
			def initProperties(self):
				self.Caption = "Quick Report"
				self.mode = None
				self.records = None
				self.saveNamedReportForm = False

			def addControls(self):
				self.addObject(dabo.ui.dRadioList, RegID="radMode", 
						Caption="Mode",
						Orientation="Row", 
						Choices=["List Format", "Expanded Format"],
						ValueMode="Key",
						Keys={"list":0, "expanded":1},
						SaveRestoreValue=True)
				self.Sizer.append1x(self.radMode)
				self.Sizer.appendSpacer(12)

				self.addObject(dabo.ui.dRadioList, RegID="radRecords", 
						Caption="Report On",
						Orientation="Row", 
						Choices=["All records in dataset", 
								"Just current record"],
						ValueMode="Key",
						Keys={"all":0, "one":1},
						SaveRestoreValue=True)
				self.Sizer.append1x(self.radRecords)
				self.Sizer.appendSpacer(12)

				self.addObject(dabo.ui.dButton, RegID="btnAdvanced", Caption="Advanced")
				self.Sizer.append(self.btnAdvanced, halign="center")
				self.btnAdvanced.bindEvent(dEvents.Hit, self.onAdvanced)

			def onAdvanced(self, evt):
				if dabo.ui.areYouSure("Would you like to save the report form xml "
						"(rfxml) to your application's reports directory? If you say "
						"'yes', you'll be able to modify the file and it will be used "
						"as the Quick Report from now on (it will no longer be auto-"
						"generated). The file will be generated when you click 'Yes'."
						"\n\nGenerate the report form file?", cancelButton=False):
					self.saveNamedReportForm = True

			def onOK(self, evt):
				self.mode = self.radMode.Value
				self.records = self.radRecords.Value

		# Name the dialog unique to the active page, so that the user's settings
		# will save and restore uniquely. They may want to usually print just the
		# current record in expanded format when on the edit page, and a list 
		# format otherwise, for example.
		name = "FrmQuickReport_%s" % self.PageFrame.SelectedPage.Caption
		d = ReportFormatDialog(self, NameBase=name)
		d.show()
		mode = d.mode
		records = d.records
		saveNamedReportForm = d.saveNamedReportForm
		d.release()

		if mode is not None:
			# Run the report
			biz = self.getBizobj()
			rfxml = self.getReportForm(mode)

			if saveNamedReportForm:
				filename = os.path.join(self.Application.HomeDirectory, "reports",
						"datanav-%s-%s.rfxml" % (biz.DataSource, mode))
				if not os.path.exists(os.path.join(self.Application.HomeDirectory, "reports")):
					os.mkdir(os.path.join(self.Application.HomeDirectory, "reports"))
				open(filename, "w").write(rfxml)

			if records == "all":
				cursor = biz.getDataSet()
			else:
				cursor = biz.getDataSet(rowStart=biz.RowNumber, rows=1)
			outputfile = reportUtils.getTempFile()

			try:
				import dabo.dReportWriter as drw
			except ImportError:
				dabo.ui.stop("Error importing dReportWriter. Check your terminal output.")
				return
				
			rw = drw.dReportWriter(OutputFile=outputfile, 
					ReportFormXML=rfxml, 
					Cursor=cursor,
					Encoding=biz.Encoding)
			try:
				rw.write()
			except (UnicodeDecodeError,), e:
				#error_string = traceback.format_exc()
				error_string = str(e)
				row_number = rw.RecordNumber
				dabo.ui.stop("There was a problem having to do with the Unicode encoding "
						"of your table, and ReportLab's inability to deal with any encoding "
						"other than UTF-8. Sorry, but currently we don't have a resolution to "
						"the problem, other than to recommend that you convert your data to "
						"UTF-8 encoding. Here's the exact error message received:\n\n%s" 
						"\n\nThis occurred in Record %s of your cursor." % (str(e), row_number))
				return 

			# Now, preview using the platform's default pdf viewer:
			reportUtils.previewPDF(outputfile)


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
			ret = importRelationSpecs(xml)
		else:
			ret = importFieldSpecs(xml)
		return ret
		
		
	def creation(self):
		""" Creates the menu, toolbar, and pageframe for the form.

		This must be called by the subclass, probably at the end of afterInit(),
		after the fieldSpecs and relationSpecs have been set.
		"""
		errMsg = self.beforeCreation()
		if errMsg:
			raise dException.dException, errMsg

		self.setupPageFrame()
		self.setupToolBar()
		if not self.preview:
			self.setupMenu()
		else:
			self.ToolBar.Enabled = False
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
			try:
				mainTable = self._mainTable
			except AttributeError:
				mainTable = ds
			if ds != mainTable:
				# Don't reset if it it's already the main bizobj
				# Note: we can send the data source, and the form will
				# correctly set the matching bizobj.
				self.PrimaryBizobj = mainTable
		
	
	def getBizobjsToCheck(self):
		""" The primary bizobj may be for one of the child pages.
		Therefore, we should return the main bizobj here
		"""
		try:
			return [self.getBizobj(dataSource=self._mainTable)]
		except AttributeError:
			return [self.PrimaryBizobj]
		
	
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
		# Raise Hit event so the originating form can act
		self.raiseEvent(dEvents.Hit)

	
	def getEditClassForField(self, fieldName):
		"""Hook: User code can supply a class of control to use on the edit page."""
		return None


	def getSelectOptionsForField(self, fieldName):
		"""Hook: User code can supply a list of select options.

		Return a sequence of options to use for this field in the select page, eg:

		("Equals", "Contains", "Less than", "Is")
		"""
		return None


	def getSelectControlClassForField(self, fieldName):
		"""Hook: User code can supply a class to use on the select page."""
		return None


	def getReportForm(self, mode):
		"""Returns the rfxml to generate a report for the dataset.

		The mode is one of "list" or "expanded", and determines the format of the 
		report output. "list" basically mimics the browse grid, with one line per
		record, and the columns as specified in the browse grid. "expanded" mimics
		the edit page, with any number of lines for each record.

		The rfxml can come from a few places, in descending precedence:
			1) if self.ReportForm["list"] or self.ReportForm["expanded"] exists,
			   that will be used.    *** NOT IMPLEMENTED YET ***

			2) if self.ReportFormFile["list"] or self.ReportFormFile["expanded"] exists,
			   that will be used.    *** NOT IMPLEMENTED YET ***

			3) if self.Application.HomeDirectory/reports/datanav-<cursorname>-(list|expanded).rfxml
			   exists, that will be used. IOW, drop in a properly named rfxml file into 
			   the reports directory underneath your application home, and it will be used
			   automatically.

			4) a generic report form will be generated. If mode=="list", the fields displayed
			   will be as defined in the browse page. If mode=="expanded", the fields displayed
			   will be as defined in the edit page.
		"""
		def getNamedReportForm(mode):
			fileName = os.path.join(self.Application.HomeDirectory, "reports", 
					"datanav-%s-%s.rfxml" % (self.getBizobj().DataSource, mode))
			if os.path.exists(fileName):
				return open(fileName).read()
			return None

		form = getNamedReportForm(mode)
		if form is not None:
			return form
		
		if mode.lower() == "list":
			return self.getAutoReportForm_list()
		elif mode.lower() == "expanded":
			return self.getAutoReportForm_expanded()
		else:
			raise ValueError, "'list' or 'expanded' are the only choices."


	def getAutoReportForm_list(self):
		from dabo.lib.reportWriter import Report, Page, TestCursor, TestRecord, String, Rectangle
		from dabo.lib.reportWriter import ReportWriter
		grid = self.PageFrame.Pages[1].BrowseGrid
		rw = ReportWriter()
		rf = rw.ReportForm = Report(reportWriter=rw, parent=None)
		rf["Title"] = "Quick Report: %s" % self.Caption
		rf["PageHeader"]["Height"] = '''"0.75 in"'''

		# Page Header Columns:
		x = 0
		reportWidth = 0
		horBuffer = 3
		vertBuffer = 5
		for col in grid.Columns:
			hAlign = col.HeaderHorizontalAlignment
			if hAlign is None:
				hAlign = grid.HeaderHorizontalAlignment

			vAlign = col.HeaderVerticalAlignment	
			if vAlign is None:
				vAlign = grid.HeaderHorizontalAlignment
			vAlign = vAlign[:3]
			if vAlign == "Cen":
				textY = (grid.HeaderHeight / 2) - (col.HeaderFontSize / 2)
			elif vAlign == "Top":
				textY = grid.HeaderHeight - col.HeaderFontSize
			else:
				textY = vertBuffer

			rectWidth = col.Width + (2 * horBuffer)

			if x + rectWidth > 720:
				# We'll run off the edge of the page, ignore the rest:
				break

			rect = rf["PageHeader"].addObject(Rectangle)
			rect["Width"] = repr(rectWidth)
			rect["Height"] = repr(grid.HeaderHeight)
			rect["StrokeWidth"] = "0.25"
			rect["FillColor"] = "(0.9, 0.9, 0.9)"
			rect["x"] = repr(x)
			rect["y"] = "0"
			
			string = rf["PageHeader"].addObject(String)
			string["Width"] = repr(col.Width)
			string["Height"] = repr(col.HeaderFontSize)
			string["FontSize"] = repr(col.HeaderFontSize)
			string["expr"] = repr(col.Caption)
			string["align"] = "'%s'" % hAlign.lower().split(" ")[0]
			string["x"] = repr(x+horBuffer)
			string["y"] = repr(textY)

			x += rectWidth

		reportWidth = x

		# Page Header Title:
		string = rf["PageHeader"].addObject(String)
		string["Width"] = repr(reportWidth)
		string["Height"] = '''15.96'''
		string["FontSize"] = '''14'''
		string["expr"] = "self.ReportForm['title']"
		string["align"] = '''"center"'''
		string["hAnchor"] = '''"center"'''
		string["BorderWidth"] = '''"0 pt"'''
		string["x"] = repr(reportWidth/2)
		string["y"] = '''"0.6 in"'''

		# Detail Band:	
		rf["Detail"]["Height"] = "None"
		x = 0
		horBuffer = 3
		vertBuffer = 5
		for col in grid.Columns:
			rectWidth = col.Width + (2 * horBuffer)
			textHorAlignment = "'%s'" % col.HorizontalAlignment.lower().split(" ")[0]

			if x + rectWidth > 720:
				# We'll run off the edge of the page, ignore the rest:
				break

			vAlign = col.VerticalAlignment[:3]
			if vAlign == "Cen":
				textY = (grid.RowHeight / 2) - (col.FontSize / 2)
			elif vAlign == "Top":
				textY = grid.RowHeight - col.FontSize
			else:
				textY = vertBuffer

			rect = rf["Detail"].addObject(Rectangle)
			string = rf["Detail"].addObject(String)

			rect["Width"] = repr(rectWidth)
			rect["Height"] = repr(grid.RowHeight)
			rect["StrokeWidth"] = "0.25"
			rect["x"] = repr(x)
			rect["y"] = "0"

			string["expr"] = "self.Record['%s']" % col.DataField
			string["Height"] = repr(col.FontSize)
			string["Align"] = textHorAlignment
			string["FontSize"] = repr(col.FontSize)
			string["Width"] = repr(col.Width)
			string["x"] = repr(x+horBuffer)
			string["y"] = repr(textY)

			x += rectWidth
	
		# Page settings:	
		orientation = "portrait"
		if x > 504:
			# switch to landscape
			orientation = "landscape"

		rf["Page"]["MarginBottom"] = '''".5 in"'''
		rf["Page"]["MarginLeft"] = '''".5 in"'''
		rf["Page"]["MarginRight"] = '''".5 in"'''
		rf["Page"]["MarginTop"] = '''".25 in"'''
		rf["Page"]["Size"] = '''"letter"'''
		rf["Page"]["Orientation"] = repr(orientation)

		testCursor = rf.addElement(TestCursor)
		for rec in self.getBizobj().getDataSet(rows=10):
			tRec = {}
			for fld, val in rec.items():
				tRec[fld] = repr(val)
			testCursor.addRecord(tRec)
		return rw._getXMLFromForm(rf)


	def _getAllChildObjects(self, container, objects=None, currentY=0):
		"""Get all child objects recursively."""
		if objects is None:
			objects = []

		for c in container.Children:
			if isinstance(c, dabo.ui.dPanel):
				objects = self._getAllChildObjects(c, objects, c.Top)
				continue
			try:
				c.Alignment
			except:
				continue
			objects.append(((c.Left, c.Top + currentY), c))
		return objects

		
	def getAutoReportForm_expanded(self):
		ep = self.PageFrame.Pages[2]
		objects = self._getAllChildObjects(ep)

		rfxml = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>

<report>
	<title>"""
		rfxml += "Quick Report: %s" % self.Caption
		rfxml += """</title>
	<pageHeader>
		<height>"0.75 in"</height>
		<objects>
			<string>
				<align>"left"</align>
				<valign>"top"</valign>
				<borderWidth>"0 pt"</borderWidth>
				<expr>self.ReportForm["title"]</expr>
				<fontName>"Helvetica"</fontName>
				<fontSize>14</fontSize>
				<hAnchor>"left"</hAnchor>
				<height>15.96</height>
				<name>title</name>
				<width>"8 in"</width>
				<x>0</x>
				<y>"0.6 in"</y>
			</string>
		</objects>
	</pageHeader>

	<groups>
		<group>
			<expr>self.RecordNumber</expr>
			<startOnNewPage>True</startOnNewPage>
		</group>
	</groups>

	<detail>
		<height>None</height>
		<objects>"""
		horBuffer = 3
		vertBuffer = 5
		maxX = 0
		for obj in objects:
			o = obj[1]
			maxX = max(maxX, (obj[0][0]+o.Width))
			obDict = {"Height": o.Height,
					"Alignment": o.Alignment.lower(),
					"FontSize": o.FontSize,
					"Width": o.Width,
					"Left": obj[0][0],
					"Top": obj[0][1]}

			if isinstance(o, dabo.ui.dLabel):
				obDict["Caption"] = o.Caption
				rfxml += """
			<string>
				<expr>"%(Caption)s"</expr>
				<height>%(Height)s</height>
				<align>"%(Alignment)s"</align>
				<fontSize>%(FontSize)s</fontSize>
				<width>%(Width)s</width>
				<x>%(Left)s</x>
				<y>self.Bands["detail"]["height"] - %(Top)s</y>
			</string>""" % obDict

			else:
				obDict["DataField"] = o.DataField
				if isinstance(o, dabo.ui.dEditBox):
					rfxml += """
			<frameset>
				<x>%(Left)s + 10</x>
				<y>self.Bands["detail"]["height"] - %(Top)s + 8 </y>
				<vAnchor>"top"</vAnchor>
				<height>None</height>
				<borderWidth>.25</borderWidth>
				<width>%(Width)s</width>
				<objects>
					<paragraph>
						<expr>self.Record["%(DataField)s"]</expr>
						<fontName>"Helvetica"</fontName>
						<fontSize>%(FontSize)s</fontSize>
						<align>"%(Alignment)s"</align>
					</paragraph>
				</objects>
			</frameset>""" % obDict
				else:
					rfxml += """
			<string>
				<expr>self.Record["%(DataField)s"]</expr>
				<height>%(FontSize)s</height>
				<borderWidth>0.25</borderWidth>
				<align>"%(Alignment)s"</align>
				<fontSize>%(FontSize)s</fontSize>
				<width>%(Width)s</width>
				<x>%(Left)s + 10</x>
				<y>self.Bands["detail"]["height"] - %(Top)s</y>
			</string>""" % obDict

		orientation = "portrait"
		if maxX > 504:
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


	## Property get/set code below
	def _getAddChildEditPages(self):
		return self._addChildEditPages

	def _setAddChildEditPages(self, val):
		if self._constructed():
			self._addChildEditPages = val
		else:
			self._properties["AddChildEditPages"] = val


	def _getBrowseGridClass(self):
		try:
			val = self._browseGridClass
		except AttributeError:
			val = Grid.Grid
		return val

	def _setBrowseGridClass(self, val):
		assert issubclass(val, Grid.Grid)
		self._browseGridClass = val		


	def _getCustomSQL(self):
		return getattr(self, "_customSQL", None)

	def _setCustomSQL(self, val):
		assert val is None or isinstance(val, basestring)
		self._customSQL = val


	def _getSelectPageClass(self):
		try:
			val = self._selectPageClass
		except AttributeError:
			val = Page.SelectPage
		return val

	def _setSelectPageClass(self, val):
		self._selectPageClass = val		


	def _getBrowsePageClass(self):
		try:
			val = self._browsePageClass
		except AttributeError:
			val = Page.BrowsePage
		return val

	def _setBrowsePageClass(self, val):
		self._browsePageClass = val		


	def _getEditPageClass(self):
		try:
			val = self._editPageClass
		except AttributeError:
			val = Page.EditPage
		return val

	def _setEditPageClass(self, val):
		self._editPageClass = val		


	def _getFieldSpecs(self):
		try:
			return self._allFieldSpecs[self._mainTable]
		except AttributeError:
			return None

	def _setFieldSpecs(self, val):
		self._allFieldSpecs[self._mainTable] = val


	def _getFormType(self):
		try:
			return self._formType
		except AttributeError:
			return "Normal"
	
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
			

	def _getRelationSpecs(self):
		return self._relationSpecs

	def _setRelationSpecs(self, val):
		self._relationSpecs = val
		

	def _getSetFocusToBrowseGrid(self):
		if hasattr(self, "_setFocusToBrowseGrid"):
			v = self._setFocusToBrowseGrid
		else:
			v = self._setFocusToBrowseGrid = True
		return v

	def _setSetFocusToBrowseGrid(self, val):
		self._setFocusToBrowseGrid = bool(val)


	# Property definitions:
	AddChildEditPages = property(_getAddChildEditPages, _setAddChildEditPages, None,
			_("""Should the form automatically add edit pages for 
			child bizobjs? (default=True)  (bool)"""))
	
	BrowseGridClass = property(_getBrowseGridClass, _setBrowseGridClass, None,
			_("""Specifies the class to use for the browse grid."""))

	BrowsePageClass = property(_getBrowsePageClass, _setBrowsePageClass, None,
			_("""Specifies the class to use for the browse page."""))

	CustomSQL = property(_getCustomSQL, _setCustomSQL, None,
			_("""Specifies custom (overridden) SQL to use."""))

	EditPageClass = property(_getEditPageClass, _setEditPageClass, None,
			_("""Specifies the class to use for the edit page."""))

	FieldSpecs = property(_getFieldSpecs, _setFieldSpecs, None, 
			_("""Reference to the dictionary containing field behavior specs"""))

	FormType = property(_getFormType, _setFormType, None,
			_("""Specifies the type of form this is.

The type of form determines the runtime behavior. FormType can be one of:
	Normal: 
		A normal dataNav form. The default.

	PickList: 
		Only select/browse pages shown, and the form is modal, returning the 
		Primary Key of the picked record.

	Edit:
		Modal version of normal, with no Select/Browse pages. User code sends
		the Primary Key of the record to edit.
"""))

	RelationSpecs = property(_getRelationSpecs, _setRelationSpecs, None, 
			_("""Reference to the dictionary containing table relation specs"""))

	SelectPageClass = property(_getSelectPageClass, _setSelectPageClass, None,
			_("""Specifies the class to use for the select page."""))

	SetFocusToBrowseGrid = property(_getSetFocusToBrowseGrid, 
			None, _setSetFocusToBrowseGrid,
			_("""Does the focus go to the browse grid when the browse page is entered?"""))
		
