import wx, dIcons
import dPageFrame as pgf
import dPageDataNav as pag
import dPage
import dabo.dEvents as dEvents


class dPageFrameDataNav(pgf.dPageFrame):

	def __init__(self, parent, name='dPageFrameDataNav'):
		#dPageFrameDataNav.doDefault(parent, name=name)
		super(dPageFrameDataNav, self).__init__(parent, name=name)

	
	def afterInit(self):
		#dPageFrameDataNav.doDefault()
		super(dPageFrameDataNav, self).afterInit()
		self.PageCount = 0
		if self.DefaultPagesOnLoad:
			self.addDefaultPages()
		
		
	def addDefaultPages(self):
		""" Add the standard pages to the pageframe.

		Subclasses may override or extend.
		"""
		il = wx.ImageList(16, 16, initialCount=0)
		il.Add(dIcons.getIconBitmap('checkMark'))
		il.Add(dIcons.getIconBitmap('browse'))
		il.Add(dIcons.getIconBitmap('edit'))
		il.Add(dIcons.getIconBitmap('childview'))

		self.AssignImageList(il)
		
		if self.Form.FormType != 'Edit':
			self.AddPage(self.SelectPageClass(self), 'Select', imageId=0)
			self.AddPage(self.BrowsePageClass(self), 'Browse', imageId=1)
		
		if self.Form.FormType != 'PickList':
			self.AddPage(self.EditPageClass(self), 'Edit', imageId=2)

			bizobj = self.Parent.getBizobj()
			for child in bizobj.getChildren():
				self.AddPage(self.ChildPageClass(self, child.DataSource), child.Caption, imageId=3)

				
	def _getSelectPageClass(self):
		try:
			return self._selectPageClass
		except AttributeError:
			return pag.dSelectPage
		
	def _setSelectPageClass(self, value):
		if issubclass(value, dPage.dPage):
			self._selectPageClass = value
		else:
			raise TypeError, "SelectPageClass must descend from dPage."

		
	def _getBrowsePageClass(self):
		try:
			return self._browsePageClass
		except AttributeError:
			return pag.dBrowsePage
		
	def _setBrowsePageClass(self, value):
		if issubclass(value, dPage.dPage):
			self._browsePageClass = value
		else:
			raise TypeError, "BrowsePageClass must descend from dPage."
	
	
	def _getEditPageClass(self):
		try:
			return self._editPageClass
		except AttributeError:
			return pag.dEditPage
		
	def _setEditPageClass(self, value):
		if issubclass(value, dPage.dPage):
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
						'The class to use as the select page.')
						
	BrowsePageClass = property(_getBrowsePageClass, _setBrowsePageClass, None,
						'The class to use as the browse page.')
						
	EditPageClass = property(_getEditPageClass, _setEditPageClass, None,
						'The class to use as the main edit page.')
						
	ChildPageClass = property(_getChildPageClass, _setChildPageClass, None,
						'The class to use for child pages.')
						
	DefaultPagesOnLoad = property(_getDefaultPagesOnLoad, _setDefaultPagesOnLoad, None,
						'Specifies whether the default Select/Browse/Edit pages should be '
						'automatically set up at instantiation.')
