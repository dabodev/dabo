import wx, dControlMixin
import dPage

class dPageFrame(wx.Notebook, dControlMixin.dControlMixin):
	""" Create a container for an unlimited number of pages.
	"""
	def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
			size=wx.DefaultSize, style=0, name='dPageFrame'):

		self._baseClass = dPageFrame

		pre = wx.PreNotebook()
		self._beforeInit(pre)                  # defined in dPemMixin
		style = style | pre.GetWindowStyle()
		pre.Create(parent, id, pos, size, style, name)

		self.PostCreate(pre)
		
		dControlMixin.dControlMixin.__init__(self, name)
		
		self.lastSelection = 0
		self.PageCount = 3
		
		self._afterInit()                      # defined in dPemMixin
		
	
	def afterInit(self):
		dPageFrame.doDefault()


	def initEvents(self):
		dControlMixin.dControlMixin.initEvents(self)
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)


	def OnPageChanged(self, event):
		ls = self.lastSelection
		cs = event.GetSelection()

		### EGL: commented this out, since it was messing up the case where 
		###  there was a pageframe inside another pageframe. Changing the 
		###  inner pageframe was sending the page changing event to the outer
		###  pageframe, which isn't correct.
		#event.Skip()    # This must happen before onLeave/EnterPage below

		newPage = self.GetPage(cs)
		oldPage = self.GetPage(ls)    

		oldPage.onLeavePage()
		newPage.onEnterPage()

		self.lastSelection = cs

	# property get/set functions:
	def _getPageClass(self):
		try:
			return self._pemObject._pageClass
		except AttributeError:
			return dPage.dPage
			
	def _setPageClass(self, value):
		if issubclass(value, dControlMixin.dControlMixin):
			self.pemObject._pageClass = value
		else:
			raise TypeError, 'PageClass must descend from a Dabo base class.'
			
			
	def _getPageCount(self):
		return int(self._pemObject.GetPageCount())
		
	def _setPageCount(self, value):
		value = int(value)
		pageCount = self._pemObject.GetPageCount()
		pageClass = self.PageClass
		
		if value < 0:
			raise ValueError, "Cannot set PageCount to less than zero."
		
		if value > pageCount:
			for i in range(pageCount, value):
				self._pemObject.AddPage(pageClass(self), "Page %s" % (i+1,))
		elif value < pageCount:
			for i in range(pageCount, value, -1):
				self._pemObject.DeletePage(i-1)
				self._pemObject.Refresh()
		
		
	def _getTabPosition(self):
		if self.hasWindowStyleFlag(wx.NB_BOTTOM):
			return 'Bottom'
		elif self.hasWindowStyleFlag(wx.NB_RIGHT):
			return 'Right'
		elif self.hasWindowStyleFlag(wx.NB_LEFT):
			return 'Left'
		else:
			return 'Top'

	def _getTabPositionEditorInfo(self):
		return {'editor': 'list', 'values': ['Top', 'Left', 'Right', 'Bottom']}

	def _setTabPosition(self, value):
		value = str(value)

		self.delWindowStyleFlag(wx.NB_BOTTOM)
		self.delWindowStyleFlag(wx.NB_RIGHT)
		self.delWindowStyleFlag(wx.NB_LEFT)

		if value == 'Top':
			pass
		elif value == 'Left':
			self.addWindowStyleFlag(wx.NB_LEFT)
		elif value == 'Right':
			self.addWindowStyleFlag(wx.NB_RIGHT)
		elif value == 'Bottom':
			self.addWindowStyleFlag(wx.NB_BOTTOM)
		else:
			raise ValueError, ("The only possible values are "
						"'Top', 'Left', 'Right', and 'Bottom'")

	# Property definitions:
	PageClass = property(_getPageClass, _setPageClass, None,
						'Specifies the class of control to use for pages by default. (classRef) \n'
						'\n'
						'This really only applies when using the PageCount property to set the\n'
						'number of pages. If you instead use AddPage() you still need to send \n'
						'an instance as usual. Class must descend from a dabo base class.')
						
	PageCount = property(_getPageCount, _setPageCount, None, 
						'Specifies the number of pages in the pageframe. (int) \n'
						'\n'
						'When using this to increase the number of pages, PageClass \n'
						'will be queried as the object to use as the page object.')
						
	TabPosition = property(_getTabPosition, _setTabPosition, None, 
						'Specifies where the page tabs are located. (int) \n'
						'    Top (default) \n'
						'    Left \n'
						'    Right \n'
						'    Bottom')

