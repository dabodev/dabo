import wx
import dabo.ui
import dabo.dEvents as dEvents
import Page as pag
from dabo.dLocalize import _, n_

dabo.ui.loadUI("wx")


class PageFrameMixin(object):
	def __init__(self, parent, Name="PageFrame", defaultPages=False,
			*args, **kwargs):
		self._defaultPagesOnLoad = defaultPages
		#super(self.__class__, self).__init__(parent, Name=Name)
		self._pageStyleClass.__init__(self, parent, Name=Name, *args, **kwargs)
		# Add the images for the various pages.
		iconPath = "themes/tango/16x16"
		self.addImage("%s/actions/system-search.png" % iconPath, key="select")
		self.addImage("%s/actions/format-justify-fill.png" % iconPath, key="browse")
		self.addImage("%s/apps/accessories-text-editor.png" % iconPath, key="edit")


	def initProperties(self):
		self.PageCount = 0
		# Dict to track the edit page for each data source
		self.dsEditPages = {}
		if self.DefaultPagesOnLoad:
			self.addDefaultPages()

		#super(self.__class__, self).initProperties()
		self._pageStyleClass.initProperties(self)
		
	
	def beforePageChange(self, fromPage, toPage):
		"""If there are no records, don't let them go to Pages 1 or 2."""
		if toPage != 0:
			if self.Form.PrimaryBizobj.RowCount == 0:
				self.SelectedPageNumber = 0
				self.Form.StatusText = "No records available"
				return False		
		
		
	def addDefaultPages(self):
		""" Add the standard pages to the pageframe.

		Subclasses may override or extend.
		"""
		if self.Form.FormType != "Edit":
			self.addSelectPage()
			self.addBrowsePage()
		
		if self.Form.FormType != "PickList":
			self.addEditPage()

			if not self.Parent.preview:
				bizobj = self.Parent.getBizobj()
				for child in bizobj.getChildren():
					self.appendPage(self.ChildPageClass(self, child.DataSource), 
							child.Caption)


	def addSelectPage(self, title=_("Select")):
		self.appendPage(self.Form.SelectPageClass, caption=title, imgKey="select")
	
	def addBrowsePage(self, title=_("Browse")):
		self.appendPage(self.Form.BrowsePageClass, caption=title, imgKey="browse")
	
	def addEditPage(self, ds=None, title=_("Edit"), pageClass=None):
		if pageClass is None:
			pageClass = self.Form.EditPageClass
		edPg = self.appendPage(pageClass, caption="", imgKey="edit")
		edPg.DataSource = ds
		if not edPg.Caption:
			# If the edit page class defined its own caption, don't override it with
			# the automatically generated caption.
			edPg.Caption = title
		# The page number will be the PageCount minus one.
		self.dsEditPages[ds] = self.PageCount - 1
	
	def editByDataSource(self, ds):
		self.SelectedPage = self.dsEditPages[ds]

	def newByDataSource(self, ds):
		self.Form.new(ds)
		self.SelectedPage = self.dsEditPages[ds]
		self.SelectedPage.update()
		
	def deleteByDataSource(self, ds):
		self.Form.delete(ds)
		
	def _getChildPageClass(self):
		try:
			return self._childPageClass
		except AttributeError:
			return pag.dChildViewPage
		
	def _setChildPageClass(self, value):
		if issubclass(value, pag.dChildViewPage):
			self._childPageClass = value
		else:
			raise TypeError, "ChildPageClass must descend from dChildPage."

			
	def _getDefaultPagesOnLoad(self):
		try:
			return self._defaultPagesOnLoad
		except AttributeError:
			return True
			
	def _setDefaultPagesOnLoad(self, value):
		self._defaultPagesOnLoad = bool(value)
		
			
	ChildPageClass = property(_getChildPageClass, _setChildPageClass, None,
						"The class to use for child pages.")
						
	DefaultPagesOnLoad = property(_getDefaultPagesOnLoad, _setDefaultPagesOnLoad, None,
						"Specifies whether the default Select/Browse/Edit pages should be "
						"automatically set up at instantiation.")



def PageFrame(parent, tabStyle="tabs", tabPosition="Top", 
		mixin=PageFrameMixin, *args, **kwargs):
	try:
		tabStyles = {"tabs": dabo.ui.dPageFrame,
				"frame": dabo.ui.dPageFrame,
				"list": dabo.ui.dPageList,
				"select": dabo.ui.dPageSelect
		}
		pageStyleClass = tabStyles[tabStyle.lower()]
	except KeyError:
		raise KeyError, \
				"tabStyle must be one of %s" % tabStyles.keys()

	class DataNavFrame(mixin, pageStyleClass):
		_pageStyleClass = property(lambda self: pageStyleClass)
		def __init__(*args, **kwargs):
			mixin.__init__(*args, **kwargs)

	return DataNavFrame(parent, *args, **kwargs)
