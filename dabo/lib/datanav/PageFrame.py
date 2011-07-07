# -*- coding: utf-8 -*-
import dabo.ui
import dabo.dEvents as dEvents
import Page as pag
from dabo.dLocalize import _


class PageFrameMixin(object):
	def __init__(self, parent, Name="PageFrame", *args, **kwargs):
		self._pageStyleClass.__init__(self, parent, Name=Name, *args, **kwargs)
		# Add the images for the various pages.
		iconPath = "themes/tango/16x16"
		self.addImage("%s/actions/system-search.png" % iconPath, key="select")
		self.addImage("%s/actions/format-justify-fill.png" % iconPath, key="browse")
		self.addImage("%s/apps/accessories-text-editor.png" % iconPath, key="edit")

		self.dsEditPages = {}


	def beforePageChange(self, fromPage, toPage):
		"""If there are no records, don't let them go to Pages 1 or 2."""
		if fromPage == 0:
			biz = self.Form.PrimaryBizobj
			if biz and biz.RowCount == 0:
				self.SelectedPageNumber = 0
				self.Form.StatusText = _("No records available")
				return False


	def addPage(self, pageClass, caption="", imgKey=None):
		page = self.appendPage(pageClass, imgKey=imgKey)
		if not page.Caption and caption:
			# Only set the caption to the default if the page class didn't define it.
			page.Caption = caption
		return page


	def addSelectPage(self, caption=_("Select")):
		self.addPage(self.Form.SelectPageClass, caption, "select")

	def addBrowsePage(self, caption=_("Browse")):
		self.addPage(self.Form.BrowsePageClass, caption, "browse")

	def addEditPage(self, ds=None, caption=_("Edit")):
		page = self.addPage(self.Form.EditPageClass, caption, "edit")
		page.DataSource = ds
		self.dsEditPages[ds] = self.PageCount - 1


	def editByDataSource(self, ds):
		if isinstance(ds, dabo.biz.dBizobj):
			ds = ds.DataSource
		self.SelectedPage = self.dsEditPages[ds]


	def newByDataSource(self, ds):
		if isinstance(ds, dabo.biz.dBizobj):
			ds = ds.DataSource
		self.Form.new(ds)
		self.SelectedPage = self.dsEditPages[ds]


	def deleteByDataSource(self, ds):
		if isinstance(ds, dabo.biz.dBizobj):
			ds = ds.DataSource
		self.Form.delete(ds)


def PageFrame(parent, tabStyle="tabs", *args, **kwargs):
	try:
		tabStyles = {"Tabs": dabo.ui.dPageFrame,
				"Frame": dabo.ui.dPageFrame,
				"List": dabo.ui.dPageList,
				"Select": dabo.ui.dPageSelect
		}
		pageStyleClass = tabStyles[tabStyle.title()]
	except KeyError:
		raise KeyError(
				"tabStyle must be one of %s" % tabStyles.keys())

	class DataNavPageFrame(PageFrameMixin, pageStyleClass):
		_pageStyleClass = property(lambda self: pageStyleClass)
		def __init__(*args, **kwargs):
			PageFrameMixin.__init__(*args, **kwargs)

	return DataNavPageFrame(parent, *args, **kwargs)
