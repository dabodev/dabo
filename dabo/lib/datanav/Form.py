# -*- coding: utf-8 -*-
import sys
import os
import traceback
import wx
import dabo.dEvents as dEvents
import dabo.ui
from dabo.dLocalize import _
import dabo.lib.reportUtils as reportUtils
import PageFrame
import Page
import Grid
# See if the reporting libraries are present
_has_reporting_libs = True
try:
	import dabo.lib.reportWriter as lrw
except ImportError, e:
	_has_reporting_libs = False
from dabo.lib.utils import ustr

dabo.ui.loadUI("wx")


class Form(dabo.ui.dForm):
	"""
	This is a dForm but with the following added controls:

		+ Navigation Menu
		+ Navigation ToolBar
		+ PageFrame with 3 pages by default:
			+ Select : Enter sql-select criteria.
			+ Browse : Browse the result set and pick an item to edit.
			+ Edit	 : Edit the current record in the result set.

	"""
	def initProperties(self):
		self.AutoUpdateStatusText = True
		self.ShowToolBar = True
		self.Size = (640, 480)

	def afterInit(self):
		if self.FormType == 'PickList':
			# The form is a picklist, which pops up so the user can choose a record,
			# and then hides itself afterwards. In addition, the picklist should hide
			# itself when other certain conditions are met.

			def _onHide(evt):
				dabo.ui.callAfter(self.hide)
			# Pressing Esc hides the form
			self.bindKey("esc", _onHide)

		# Create the various elements:
		self.setupPageFrame()

		if self.FormType == "Edit":
			self.pageFrame.Pages[0].setFocus()
			if self.Modal:
				self.setupSaveCancelButtons()
				self.bindKey("esc", self.onCancel)

		if not self.Testing and not self.Modal:
			self.setupToolBar()
			self.setupMenu()


	def save(self, dataSource=None):
		## The bizobj may have made some changes to the data during the save, so
		## make sure it is reflected on screen by calling update() afterwards.
		ret = super(Form, self).save(dataSource)
		self.update()
		if self.FormType == "Edit" and self.Modal:
			dabo.ui.callAfter(self.hide)
		return ret

	def cancel(self, dataSource=None):
		ret = super(Form, self).cancel(dataSource)
		self.update()
		if self.FormType == "Edit" and self.Modal:
			dabo.ui.callAfter(self.hide)
		return ret

	def setupSaveCancelButtons(self):
		vs = self.Sizer
		hs = dabo.ui.dSizer("h")
		hs.append(dabo.ui.dButton(self, Caption=_("Save Changes"), DefaultButton=True, OnHit=self.onSave))
		hs.appendSpacer((3,0))
		hs.append(dabo.ui.dButton(self, Caption=_("Cancel Changes"), CancelButton=True, OnHit=self.onCancel))
		vs.append(hs, alignment="right")

	def setupToolBar(self):
		tb = self.ToolBar = dabo.ui.dToolBar(self)
		if tb.Children:
			# It's already been set up
			return

		if not self.ToolBar:
			# MDI on Linux doesn't add the toolbar in the above call
			return

		if self.Application.Platform == "Mac":
			# Toolbar looks better with larger icons on Mac. In fact, I believe HIG
			# recommends 32x32 for Mac Toolbars.
			iconSize = (32, 32)
		else:
			iconSize = (22, 22)
		tb.SetToolBitmapSize(iconSize)  ## need to abstract in dToolBar!
		iconPath = "themes/tango/%sx%s" % iconSize

		if self.FormType != 'Edit':
			self.appendToolBarButton("First", "%s/actions/go-first.png" % iconPath,
					OnHit=self.onFirst,	tip=_("First"), help=_("Go to the first record"))
			self.appendToolBarButton("Prior", "%s/actions/go-previous.png" % iconPath,
					OnHit=self.onPrior,	tip=_("Prior"), help=_("Go to the prior record"))
			self.appendToolBarButton("Requery", "%s/actions/view-refresh.png" % iconPath,
					OnHit=self.onRequery,	tip=_("Requery"), help=_("Requery dataset"))
			self.appendToolBarButton("Next", "%s/actions/go-next.png" % iconPath,
					OnHit=self.onNext, tip=_("Next"), help=_("Go to the next record"))
			self.appendToolBarButton("Last", "%s/actions/go-last.png" % iconPath,
					OnHit=self.onLast, tip=_("Last"), help=_("Go to the last record"))
			tb.appendSeparator()

		if self.FormType == 'Normal':
			self.appendToolBarButton("New", "%s/actions/document-new.png" % iconPath,
					OnHit=self.onNew,	tip=_("New"), help=_("Add a new record"))
			self.appendToolBarButton("Delete", "%s/actions/edit-delete.png" % iconPath,
					OnHit=self.onDelete, tip=_("Delete"), help=_("Delete this record"))
			tb.appendSeparator()

		if self.FormType != 'PickList':
			self.appendToolBarButton("Save", "%s/actions/document-save.png" % iconPath,
					OnHit=self.onSave, tip=_("Save"), help=_("Save changes"))
			self.appendToolBarButton("Cancel", "%s/actions/edit-undo.png" % iconPath,
					OnHit=self.onCancel, tip=_("Cancel"), help=_("Cancel changes"))
			tb.appendSeparator()

		if self.FormType == "Normal":
			self.appendToolBarButton(_("Configure Grid"), "%s/categories/preferences-system.png" % iconPath,
					OnHit=self.onConfigGrid, tip=_("Configure Grid"),
					help=_("Configure grid columns"))

			self.appendToolBarButton(_("Quick Report"), "%s/actions/document-print-preview.png" % iconPath,
					OnHit=self.onQuickReport, tip=_("Quick Report"), Enabled=_has_reporting_libs,
					help=_("Run a Quick Report on the current dataset"))

			tb.appendSeparator()
			self.appendToolBarButton(_("Close"), "%s/actions/system-log-out.png" % iconPath,
						OnHit=self.Application.onWinClose, tip=_("Close"),
						help=_("Close Form"))


	def getMenu(self):
		iconPath = "themes/tango/16x16"
		menu = super(Form, self).getMenu()
		menu.Caption = _("&Actions")
		menu.MenuID = "actions"

		menu.append(_("Set Selection &Criteria")+"\tAlt+1",
				OnHit=self.onSetSelectionCriteria, bmp="%s/actions/system-search.png" % iconPath,
				ItemID="actions_select",
				help=_("Set the selection criteria for the recordset."))

		menu.append(_("&Browse Records")+"\tAlt+2",
				OnHit=self.onBrowseRecords, bmp="%s/actions/format-justify-fill.png" % iconPath,
				ItemID="actions_browse",
				help=_("Browse the records in the current recordset."))

		def onActivatePage(evt):
			self.pageFrame.SelectedPage = evt.EventObject.Tag

		# Add an edit menu item, and an activation menu for every subsequent page
		if self.FormType != "PickList":
			for index in range(2, self.pageFrame.PageCount):
				if index == 2:
					title = "&%s\tAlt+3" % (self.pageFrame.Pages[index].Caption)
					onHit = self.onEditCurrentRecord
					tag = self.pageFrame.Pages[index].DataSource
					help = _("Edit the fields of the currently selected record.")
				else:
					title = "%s\tAlt+%d" % (self.pageFrame.Pages[index].Caption, index + 1)
					onHit = onActivatePage
					tag = self.pageFrame.Pages[index]
					help = ""

				menu.append(title, OnHit=onHit, bmp="%s/apps/accessories-text-editor.png" % iconPath,
						help=help, Tag=tag, ItemID="actions_edit")
			menu.appendSeparator()

		if self.FormType != "Edit":
			menu.append(_("&Requery")+"\tCtrl+R", OnHit=self.onRequery,
					bmp="%s/actions/view-refresh.png" % iconPath,
					ItemID="actions_requery",
					help=_("Get a new recordset from the backend."), menutype="check")

		if self.FormType != "PickList":
			menu.append(_("&Save Changes")+"\tCtrl+S", OnHit=self.onSave,
					bmp="%s/actions/document-save.png" % iconPath,
					ItemID="actions_save",
					help=_("Save any changes made to the records."))
			menu.append(_("&Cancel Changes"), OnHit=self.onCancel,
					bmp="%s/actions/edit-undo.png" % iconPath,
					ItemID="actions_cancel",
					help=_("Cancel any changes made to the records."))
			menu.appendSeparator()

			# On Mac, altKey is "Ctrl", which translates to "Command". On other
			# platforms, altKey is "Alt". This lets us use the arrow keys for
			# navigation without conflicting with native text editing functions.
			altKey = "Alt"
			if self.Application.Platform.lower() == "mac":
				altKey = "Ctrl"

			menu.append(_("Select &First Record")+"\t%s+UP" % altKey,
					OnHit=self.onFirst, bmp="%s/actions/go-first.png" % iconPath,
					ItemID="actions_first",
					help=_("Go to the first record in the set."))
			menu.append(_("Select &Prior Record")+"\t%s+LEFT" % altKey,
					OnHit=self.onPrior, bmp="%s/actions/go-previous.png" % iconPath,
					ItemID="actions_prior",
					help=_("Go to the prior record in the set."))
			menu.append(_("Select Ne&xt Record")+"\t%s+RIGHT" % altKey,
					OnHit=self.onNext, bmp="%s/actions/go-next.png" % iconPath,
					ItemID="actions_next",
					help=_("Go to the next record in the set."))
			menu.append(_("Select &Last Record")+"\t%s+DOWN" % altKey,
					OnHit=self.onLast, bmp="%s/actions/go-last.png" % iconPath,
					ItemID="actions_last",
					help=_("Go to the last record in the set."))
			menu.appendSeparator()

		if self.FormType == "Normal":
			menu.append(_("&New Record")+"\tCtrl+N", OnHit=self.onNew,
					bmp="%s/actions/document-new.png" % iconPath,
					ItemID="actions_new",
					help=_("Add a new record to the dataset."))
			menu.append(_("&Delete Current Record"), OnHit=self.onDelete,
					bmp="%s/actions/edit-delete" % iconPath,
					ItemID="actions_delete",
					help=_("Delete the current record from the dataset."))
			menu.appendSeparator()

		if self.FormType != "Edit":
			menu.append(_("Show S&QL"), OnHit=self.onShowSQL)

		if self.FormType == "Normal":
			menu.append(_("Quick &Report"), OnHit=self.onQuickReport,
					bmp="%s/actions/document-print-preview.png" % iconPath,
					ItemID="actions_quickreport",
					DynamicEnabled=self.enableQuickReport)

		return menu

	def onConfigGrid(self, evt):
		try:
			grid = self.PageFrame.Pages[1].BrowseGrid
			ds = grid.DataSet
		except:
			dabo.ui.info(_("Sorry, there are no records in the grid, please requery first."))
			return

		#cols
		cols = [col.Caption for col in grid.Columns]

		#keys
		keys = [col.DataField for col in grid.Columns]

		class GridColumnsDialog(dabo.ui.dOkCancelDialog):

			def initProperties(self):
				self.selectedColumns = None

			def addControls(self):
				self.addObject(dabo.ui.dLabel, RegID="label",
						Caption=_("You can customize grid appearence by selecting\nthe columns you wish to see bellow:"), WordWrap=True)

				self.addObject(dabo.ui.dCheckList, RegID="columns",
						Height=150, ValueMode="Key",
						Choices=cols,
						Keys=keys)

				for col in grid.Columns:
					if col.Visible:
						self.columns.setSelection(col.ColumnIndex)

				self.Sizer.DefaultBorder = 5
				self.Sizer.DefaultBorderAll = True

				self.Sizer.append(self.label, border=5)
				self.Sizer.append1x(self.columns)

			def runOK(self):
				self.selectedColumns = self.columns.Value

			def runCancel(self):
				self.selectedColumns = None

		d = GridColumnsDialog(self, Caption=_("Select Columns"))
		d.show()

		#the user has canceled, just return
		if d.selectedColumns == None:
			return

		for col in grid.Columns:
			if col.DataField in d.selectedColumns:
				col.Visible = True
			else:
				col.Visible = False

		#release the window
		d.release()


	def onDelete(self, evt):
		super(Form, self).onDelete(evt)
		self._afterDeleteOrCancel()


	def onCancel(self, evt):
		super(Form, self).onCancel(evt)
		self._afterDeleteOrCancel()


	def _afterDeleteOrCancel(self):
		# If the delete or cancel resulted in 0 records, activate the Select page
		# so that the user can't interact with any controls on the edit page.
		if self.FormType in ("Edit",):
			return
		biz = self.getBizobj()
		if biz.RowCount < 1:
			self.PageFrame.SelectedPageNumber = 0

		# Make sure that the grid is properly updated.
		try:
			self.PageFrame.Pages[1].BrowseGrid.refresh()
		except AttributeError, e:
			# Grid may not even exist yet.
			if "BrowseGrid" in ustr(e):
				pass
			else:
				raise


	def enableQuickReport(self):
		## Can't enable quick report unless the dataset has been requeried once and
		## the browse grid exists (because it gets the layout from the browse grid).
		ret = _has_reporting_libs
		try:
			self.PageFrame.Pages[1].BrowseGrid
		except AttributeError:
			ret = False
		return ret


	def setupMenu(self):
		"""
		Set up the action menu for this frame.

		Called when the form is created.
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
		"""
		Set up the select/browse/edit/n pageframe.

		Default behavior is to set up a 3-page pageframe with 'Select',
		'Browse', and 'Edit' pages. User may override and/or extend in
		subclasses and overriding self.beforeSetupPageFrame(),
		self.setupPageFrame, and/or self.afterSetupPageFrame().
		"""
		currPage = 0
		ds = None
		biz = self.getBizobj()
		if biz is not None:
			ds = biz.DataSource

		try:
			currPage = self.pageFrame.SelectedPage
			self.pageFrame.unbindEvent()
			self.pageFrame.release()
			try:
				del self.__dict__["PageFrame"]
			except KeyError:
				pass
		except AttributeError:
			pass

		if self.beforeSetupPageFrame():
			self.pageFrame = PageFrame.PageFrame(self, tabStyle=self.PageFrameStyle,
					TabPosition=self.PageTabPosition)
			border = 3
			borderSides = ("top", "left", "right")
			if sys.platform.startswith("darwin"):
				# Apple already gives enough top border, but the side needs more
				borderSides = ("left", "right")
				border = 9
			elif sys.platform.startswith("win"):
				# Windows looks best with no border
				borderSides = ()
			hs = dabo.ui.dSizer("h")
			hs.append1x(self.pageFrame, border=border, borderSides=borderSides)
			self.Sizer.append1x(hs)
			if self.FormType != "Edit":
				self.pageFrame.addSelectPage()
				self.pageFrame.addBrowsePage()
			if self.FormType != "PickList":
				self.addEditPages(ds)
			self.pageFrame.SelectedpageNum = currPage
			self.afterSetupPageFrame()
			self.Sizer.layout()
			self.refresh()

	def beforeSetupPageFrame(self): return True
	def afterSetupPageFrame(self): pass

	def addEditPages(self, ds):
		"""Called when it is time to add the edit page(s)."""
		self.addEditPage(ds, _("Edit"))

	def addEditPage(self, ds, title):
		"""Called when it is time to add the edit page for the passed datasource."""
		self.pageFrame.addEditPage(ds, title)

	def onSetSelectionCriteria(self, evt):
		"""Occurs when the user chooses to set the selection criteria."""
		self.pageFrame.SelectedPage = 0

	def onBrowseRecords(self, evt):
		"""Occurs when the user chooses to browse the record set."""
		self.pageFrame.SelectedPage = 1

	def onEditCurrentRecord(self, evt):
		"""Occurs when the user chooses to edit the current record."""
		# We stored the datasource in the menu item's Tag property when
		# the menu was created.
		self.pageFrame.editByDataSource(evt.EventObject.Tag)


	def onShowSQL(self, evt):
		sql = self.PrimaryBizobj.LastSQL
		if sql is None:
			sql = "-Nothing executed yet-"
		dlg = dabo.ui.dDialog(self, Caption=_("Last SQL"),
				SaveRestorePosition=True, BorderResizable=True)
		eb = dlg.addObject(dabo.ui.dEditBox, ReadOnly=True, Value=sql,
				Size=(400, 400))
		for ff in ["Monospace", "Monaco", "Courier New"]:
			try:
				eb.FontFace = ff
				break
			except dabo.ui.assertionException:
				continue
		dlg.Sizer.append1x(eb)
		dlg.show()
		dlg.release()


	def onQuickReport(self, evt):
		# May not have records if called via toolbar button
		if not self.enableQuickReport():
			dabo.ui.exclaim(_("Sorry, there are no records to report on."),
					title=_("No Records"))
			return

		showAdvancedQuickReport = self.ShowAdvancedQuickReport
		showExpandedQuickReport = self.ShowExpandedQuickReport

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

				if not showExpandedQuickReport:
					self.radMode.enableKey("expanded", False)
					self.radMode.Value = "list"  ## in case the setting was saved at 'expanded' previously.

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

				if showAdvancedQuickReport:
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

			def runOK(self):
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
				error_string = ustr(e)
				row_number = rw.RecordNumber
				dabo.ui.stop("There was a problem having to do with the Unicode encoding "
						"of your table, and ReportLab's inability to deal with any encoding "
						"other than UTF-8. Sorry, but currently we don't have a resolution to "
						"the problem, other than to recommend that you convert your data to "
						"UTF-8 encoding. Here's the exact error message received:\n\n%s"
						"\n\nThis occurred in Record %s of your cursor." % (ustr(e), row_number))
				return

			# Now, preview using the platform's default pdf viewer:
			reportUtils.previewPDF(outputfile)


	def setPrimaryBizobjToDefault(self, ds):
		"""
		This method is called when we leave an editing page. The
		intent is that if we move to another editing page, it will set the
		form's primary bizobj to the appropriate one for that page,
		so we don't need to do anything. But if they switch to the
		browse or select page, we want to set the primary bizobj back
		to the one for the form's main table.
		"""
		bizDS = None
		biz = self.getBizobj()
		if biz:
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
		"""
		The primary bizobj may be for one of the child pages.
		Therefore, we should return the main bizobj here
		"""
		try:
			return [self.getBizobj(dataSource=self._mainTable)]
		except AttributeError:
			return [self.PrimaryBizobj]


	def onRequery(self, evt):
		"""
		Override the dForm behavior by running the requery through the select page.
		"""
		self.requery()


	def requery(self, dataSource=None, _fromSelectPage=False):
		if not _fromSelectPage and self.FormType != "Edit":
			# re-route the form's requery through the select page's requery.
			self.pageFrame.GetPage(0).requery()
		else:
			# After the select page does its thing, it calls frm.requery():
			return super(Form, self).requery(dataSource)


	def onNew(self, evt):
		self.pageFrame.newByDataSource(self.getBizobj().DataSource)


	def pickRecord(self):
		"""This form is a picklist, and the user chose a record in the grid."""
		# Raise Hit event so the originating form can act
		self.raiseEvent(dEvents.Hit)


	def getReportForm(self, mode):
		"""
		Returns the rfxml to generate a report for the dataset.

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
			raise ValueError("'list' or 'expanded' are the only choices.")


	def getAutoReportForm_list(self):
		grid = self.PageFrame.Pages[1].BrowseGrid
		rw = lrw.ReportWriter()
		rf = rw.ReportForm = lrw.Report(reportWriter=rw, parent=None)
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

			rect = rf["PageHeader"].addObject(lrw.Rectangle)
			rect["Width"] = repr(rectWidth)
			rect["Height"] = repr(grid.HeaderHeight)
			rect["StrokeWidth"] = "0.25"
			rect["FillColor"] = "(0.9, 0.9, 0.9)"
			rect["x"] = repr(x)
			rect["y"] = "0"

			string = rf["PageHeader"].addObject(lrw.String)
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
		string = rf["PageHeader"].addObject(lrw.String)
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

			rect = rf["Detail"].addObject(lrw.Rectangle)
			string = rf["Detail"].addObject(lrw.String)

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

		testCursor = rf.addElement(lrw.TestCursor)
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
				c.DataField
			except AttributeError:
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
			alignment = o.Alignment
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
		val = getattr(self, "_addChildEditPages", None)
		if val is None:
			val = self._addChildEditPages = False
		return val

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


	def _getEnableChildRequeriesWhenBrowsing(self):
		try:
			val = self._enableChildRequeriesWhenBrowsing
		except AttributeError:
			val = self._enableChildRequeriesWhenBrowsing = True
		return val

	def _setEnableChildRequeriesWhenBrowsing(self, val):
		self._enableChildRequeriesWhenBrowsing = bool(val)


	def _getEnableChildRequeriesWhenEditing(self):
		try:
			val = self._enableChildRequeriesWhenEditing
		except AttributeError:
			val = self._enableChildRequeriesWhenEditing = True
		return val

	def _setEnableChildRequeriesWhenEditing(self, val):
		self._enableChildRequeriesWhenEditing = bool(val)


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
			raise ValueError("Form type must be 'Normal', 'PickList', or 'Edit'.")


	def _getPageFrameStyle(self):
		if hasattr(self, "_pageFrameStyle"):
			v = self._pageFrameStyle
		else:
			v = self._pageFrameStyle = "Tabs"
		return v

	def _setPageFrameStyle(self, val):
		assert val.lower() in ("tabs", "list", "select")
		self._pageFrameStyle = val


	def _getPageTabPosition(self):
		if hasattr(self, "_pageTabPosition"):
			v = self._pageTabPosition
		else:
			v = self._pageTabPosition = "Top"
		return v

	def _setPageTabPosition(self, val):
		assert val.lower() in ("top", "left", "right", "bottom")
		self._pageTabPosition = val


	def _getSetFocusToBrowseGrid(self):
		if hasattr(self, "_setFocusToBrowseGrid"):
			v = self._setFocusToBrowseGrid
		else:
			v = self._setFocusToBrowseGrid = True
		return v

	def _setSetFocusToBrowseGrid(self, val):
		self._setFocusToBrowseGrid = bool(val)


	def _getShowAdvancedQuickReport(self):
		return getattr(self, "_showAdvancedQuickReport", True)

	def _setShowAdvancedQuickReport(self, val):
		self._showAdvancedQuickReport = bool(val)


	def _getShowExpandedQuickReport(self):
		return getattr(self, "_showExpandedQuickReport", True)

	def _setShowExpandedQuickReport(self, val):
		self._showExpandedQuickReport = bool(val)


	def _getShowSortFields(self):
		return getattr(self, "_showSortFields", True)

	def _setShowSortFields(self, val):
		self._showSortFields = bool(val)


	def _getTesting(self):
		return getattr(self, "_testing", False)

	def _setTesting(self, val):
		self._testing = bool(val)



	# Property definitions:
	AddChildEditPages = property(_getAddChildEditPages, _setAddChildEditPages, None,
			_("""Should the form automatically add edit pages for child bizobjs?

			The default is False, and this property may be removed soon."""))

	BrowseGridClass = property(_getBrowseGridClass, _setBrowseGridClass, None,
			_("""Specifies the class to use for the browse grid."""))

	BrowsePageClass = property(_getBrowsePageClass, _setBrowsePageClass, None,
			_("""Specifies the class to use for the browse page."""))

	CustomSQL = property(_getCustomSQL, _setCustomSQL, None,
			_("""Specifies custom (overridden) SQL to use."""))

	EditPageClass = property(_getEditPageClass, _setEditPageClass, None,
			_("""Specifies the class to use for the edit page."""))

	EnableChildRequeriesWhenBrowsing = property(_getEnableChildRequeriesWhenBrowsing,
			_setEnableChildRequeriesWhenBrowsing, None,
			_("""Specifies whether child bizobjs are requeried automatically when the parent
			RowNumber changes, while in the browse page. Default: True

			Turning this to False will result in better performance of the browse grid when
			there are lots of child bizobjs, but it may result in unintended consequences
			which is why it is True by default."""))

	EnableChildRequeriesWhenEditing = property(_getEnableChildRequeriesWhenEditing,
			_setEnableChildRequeriesWhenEditing, None,
			_("""Specifies whether child bizobjs are requeried automatically when the parent
			RowNumber changes, while not in the browse page. Default: True"""))

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

	PageFrameStyle = property(_getPageFrameStyle, _setPageFrameStyle, None,
			_("""Specifies the style of pageframe to set up. Valid values are:

				Tabs (default)
				List (down the side)
				Select
			"""))

	PageTabPosition = property(_getPageTabPosition, _setPageTabPosition, None,
			_("""Specifies the location of the pageframe tabs. Valid values are:

				Top (default)
				Left
				Right
				Bottom

				This only applies when PageFrameStyle is set to "Tabs".
			"""))

	SelectPageClass = property(_getSelectPageClass, _setSelectPageClass, None,
			_("""Specifies the class to use for the select page."""))

	SetFocusToBrowseGrid = property(_getSetFocusToBrowseGrid,
			_setSetFocusToBrowseGrid, None,
			_("""Does the focus go to the browse grid when the browse page is entered?"""))

	ShowAdvancedQuickReport = property(_getShowAdvancedQuickReport,
			_setShowAdvancedQuickReport, None,
			_("""Does the 'Advanced' button appear in the Quick Report dialog?"""))

	ShowExpandedQuickReport = property(_getShowExpandedQuickReport,
			_setShowExpandedQuickReport, None,
			_("""Can the user choose the 'expanded' quick report?"""))

	ShowSortFields = property(_getShowSortFields, _setShowSortFields, None,
			_("""Can the user sort fields in the select page?"""))

	Testing = property(_getTesting, _setTesting, None,
			"Flag for use when testing elements of the form.")

