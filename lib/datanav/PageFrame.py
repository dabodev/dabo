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
		self.addImage("checkMark")
		self.addImage("browse")
		self.addImage("edit")
		self.addImage("childview")


	def initProperties(self):
		self.PageCount = 0
		# Dict to track the edit page for each data source
		self.dsEditPages = {}
		if self.DefaultPagesOnLoad:
			self.addDefaultPages()

		#super(self.__class__, self).initProperties()
		self._pageStyleClass.initProperties(self)
		
		
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
							child.Caption, imgKey="childview")


	def addSelectPage(self, title=_("Select")):
		self.appendPage(self.SelectPageClass, caption=title, imgKey="checkMark")
	
	def addBrowsePage(self, title=_("Browse")):
		self.appendPage(self.BrowsePageClass, caption=title, imgKey="browse")
	
	def addEditPage(self, ds=None, title=_("Edit"), pageClass=None):
		if pageClass is None:
			pageClass = self.EditPageClass
		edPg = self.appendPage(pageClass, caption=title, imgKey="edit")
		edPg.DataSource = ds
		# The page number will be the PageCount minus one.
		self.dsEditPages[ds] = self.PageCount - 1
	
	def editByDataSource(self, ds):
		self.SelectedPage = self.dsEditPages[ds]

	def newByDataSource(self, ds):
		self.Form.new(ds)
		self.SelectedPage = self.dsEditPages[ds]
		self.SelectedPage.raiseEvent(dEvents.ValueRefresh)
		
	def deleteByDataSource(self, ds):
		self.Form.delete(ds)
		
	def _getSelectPageClass(self):
		try:
			return self._selectPageClass
		except AttributeError:
			return pag.SelectPage
		
	def _setSelectPageClass(self, value):
		if issubclass(value, dabo.ui.dPage):
			self._selectPageClass = value
		else:
			raise TypeError, "SelectPageClass must descend from dPage."

		
	def _getBrowsePageClass(self):
		try:
			return self._browsePageClass
		except AttributeError:
			return pag.BrowsePage
		
	def _setBrowsePageClass(self, value):
		if issubclass(value, dabo.ui.dPage):
			self._browsePageClass = value
		else:
			raise TypeError, "BrowsePageClass must descend from dPage."
	
	
	def _getEditPageClass(self):
		try:
			return self._editPageClass
		except AttributeError:
			return pag.EditPage
		
	def _setEditPageClass(self, value):
		if issubclass(value, dabo.ui.dPage):
			self._editPageClass = value
		else:
			raise TypeError, "EditPageClass must descend from dPage."

	
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
		
			
	SelectPageClass = property(_getSelectPageClass, _setSelectPageClass, None, 
						"The class to use as the select page.")
						
	BrowsePageClass = property(_getBrowsePageClass, _setBrowsePageClass, None,
						"The class to use as the browse page.")
						
	EditPageClass = property(_getEditPageClass, _setEditPageClass, None,
						"The class to use as the main edit page.")
						
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
