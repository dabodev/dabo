import wx, dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as cm
import dPage
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class dPageFrame(wx.Notebook, cm.dControlMixin):
	""" Create a container for an unlimited number of pages.
	"""
	_IsContainer = True
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dPageFrame
		preClass = wx.PreNotebook
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		# Dictionary for tracking images by key value
		self.__imageList = {}	


	def _initEvents(self):
		super(dPageFrame, self)._initEvents()
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.__onPageChanged)
		self.bindEvent(dEvents.Create, self.__onCreate)
	
		
	def __onCreate(self, evt):
		# Make sure the PageEnter fires for the current page on 
		# pageframe instantiation, as this doesn't happen automatically.
		# Putting this code in afterInit() results in a segfault on Linux, btw.
		dabo.ui.callAfter(self.__pageChanged, 0, None)

				
	def __onPageChanged(self, evt):
		evt.Skip()
		evt.StopPropagation()

		newPageNum = evt.GetSelection()
		try:
			oldPageNum = self._lastPage
		except AttributeError:
			# _lastPage hasn't been defined yet.
			oldPageNum = None
		self.__pageChanged(newPageNum, oldPageNum)

		
	def __pageChanged(self, newPageNum, oldPageNum):		
		self._lastPage = newPageNum
		if oldPageNum is not None:
			if oldPageNum >=0:
				self.GetPage(oldPageNum).raiseEvent(dEvents.PageLeave)

		if newPageNum >= 0 and self.PageCount > newPageNum:
			self.GetPage(newPageNum).raiseEvent(dEvents.PageEnter)
		
	
	# Image-handling function
	def addImage(self, img, key=None):
		""" Adds the passed image to the control's ImageList, and maintains
		a reference to it that is retrievable via the key value.
		"""
		if key is None:
			key = str(img)
		if type(img) in (str, unicode):
			img = dabo.ui.dIcons.getIconBitmap(img)
		il = self.GetImageList()
		if not il:
			il = wx.ImageList(16, 16, initialCount=0)
			self.AssignImageList(il)
		idx = il.Add(img)
		self.__imageList[key] = idx
	
	
	def setPageImg(self, pg, imgKey):
		""" Sets the specified page's image to the image corresponding
		to the specified key. May also optionally pass the index of the 
		image in the ImageList rather than the key.
		"""
		pgIdx = self._getPageIndex(pg)
		if pgIdx is not None:
			if type(imgKey) == int:
				imgIdx = imgKey
			else:
				imgIdx = self.__imageList[imgKey]
			self.SetPageImage(pgIdx, imgIdx)

	
	def getPageImg(self, pg):
		""" Returns the index of the specified page's image in the 
		current image list, or -1 if no image is set for the page.
		"""
		ret = -1
		pgIdx = self._getPageIndex(pg)
		if pgIdx is not None:
			ret = self.GetPageImage(pgIdx)
		return ret
		
	
	def appendPage(self, pg, caption="", imgKey=None):
		""" Appends the page to the pageframe, and optionally sets
		the page caption and image. The image should have already
		been added to the pageframe if it is going to be set here.
		"""
		idx = None
		if imgKey:
			idx = self.__imageList[imgKey]
		self.AddPage(pg, text=caption, imageId=idx)
		
	
	def insertPage(self, pos, pg, caption="", imgKey=None):
		""" Insert the page into the pageframe at the specified position, 
		and optionally sets the page caption and image. The image 
		should have already been added to the pageframe if it is 
		going to be set here.
		"""
		idx = None
		if imgKey:
			idx = self.__imageList[imgKey]
		self.InsertPage(pos, pg, text=caption, imageId=idx)

		
	def _getPageIndex(self, pg):	
		""" Resolves page references to the page index, which is what
		is needed by most methods that act on pages.
		"""
		ret = None
		if type(pg) == int:
			ret = pg
		else:
			# Most likely a page instance was passed. Find its index
			for i in range(self.PageCount):
				if self.GetPage(i) == pg:
					ret = i
					break
		return ret
		
	
	
	
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
			raise TypeError, "PageClass must descend from a Dabo base class."
			
			
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
	
	def _getSelPage(self):
		return self.GetPage(self.GetSelection())
	def _setSelPage(self, pg):
		idx = self._getPageIndex(pg)
		self.SetSelection(idx)
		
	def _getTabPosition(self):
		if self.hasWindowStyleFlag(wx.NB_BOTTOM):
			return "Bottom"
		elif self.hasWindowStyleFlag(wx.NB_RIGHT):
			return "Right"
		elif self.hasWindowStyleFlag(wx.NB_LEFT):
			return "Left"
		else:
			return "Top"

	def _getTabPositionEditorInfo(self):
		return {"editor": "list", "values": ["Top", "Left", "Right", "Bottom"]}

	def _setTabPosition(self, value):
		value = str(value)

		self.delWindowStyleFlag(wx.NB_BOTTOM)
		self.delWindowStyleFlag(wx.NB_RIGHT)
		self.delWindowStyleFlag(wx.NB_LEFT)

		if value == "Top":
			pass
		elif value == "Left":
			self.addWindowStyleFlag(wx.NB_LEFT)
		elif value == "Right":
			self.addWindowStyleFlag(wx.NB_RIGHT)
		elif value == "Bottom":
			self.addWindowStyleFlag(wx.NB_BOTTOM)
		else:
			raise ValueError, ("The only possible values are "
						"'Top', 'Left', 'Right', and 'Bottom'")

	# Property definitions:
	PageClass = property(_getPageClass, _setPageClass, None,
			_("""Specifies the class of control to use for pages by default. (classRef) 
			This really only applies when using the PageCount property to set the
			number of pages. If you instead use AddPage() you still need to send 
			an instance as usual. Class must descend from a dabo base class.""") )
						
	PageCount = property(_getPageCount, _setPageCount, None, 
			_("""Specifies the number of pages in the pageframe. (int) 
			When using this to increase the number of pages, PageClass 
			will be queried as the object to use as the page object.""") )
	
	SelectedPage = property(_getSelPage, _setSelPage, None,
			_("References the current frontmost page.  (dPage)") )
						
	TabPosition = property(_getTabPosition, _setTabPosition, None, 
			_("""Specifies where the page tabs are located. (int) 
			    Top (default) 
			    Left 
			    Right 
			    Bottom""") )

