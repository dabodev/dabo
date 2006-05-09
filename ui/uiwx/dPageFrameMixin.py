import time
import wx
import dabo
import dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as cm
from dPage import dPage
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty
	

class dPageFrameMixin(cm.dControlMixin):
	"""Creates a container for an unlimited number of pages."""
	def _initEvents(self):
		super(dPageFrameMixin, self)._initEvents()
		self.Bind(self._evtPageChanged, self.__onPageChanged)
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
		## Because of platform inconsistencies, it is safer to raise the dabo
		## events in a callafter instead of directly.
		if not self:
			# JIC this object has been released
			return
		self._lastPage = newPageNum
		if oldPageNum is not None:
			if oldPageNum >=0:
				try:
					oldPage = self.Pages[oldPageNum]
					dabo.ui.callAfter(oldPage.raiseEvent, dEvents.PageLeave)
				except:
					# Page has already been released
					return

		if newPageNum >= 0 and self.PageCount > newPageNum:
			dabo.ui.callAfter(self.Pages[newPageNum].raiseEvent, dEvents.PageEnter)
			dabo.ui.callAfter(self.raiseEvent, dEvents.PageChanged, 
					oldPageNum=oldPageNum, newPageNum=newPageNum)
			
	
	# Image-handling function
	def addImage(self, img, key=None):
		""" Adds the passed image to the control's ImageList, and maintains
		a reference to it that is retrievable via the key value.
		"""
		if key is None:
			key = str(img)
		if isinstance(img, basestring):
			img = dabo.ui.strToBmp(img)
		il = self.GetImageList()
		if not il:
			il = wx.ImageList(16, 16, initialCount=0)
			self.AssignImageList(il)
		idx = il.Add(img)
		self._imageList[key] = idx
	
	
	def setPageImage(self, pg, imgKey):
		""" Sets the specified page's image to the image corresponding
		to the specified key. May also optionally pass the index of the 
		image in the ImageList rather than the key.
		"""
		pgIdx = self._getPageIndex(pg)
		if pgIdx is not None:
			if isinstance(imgKey, int):
				imgIdx = imgKey
			else:
				try:
					imgIdx = self._imageList[imgKey]
				except KeyError:
					# They may be trying to set the page's Image to an
					# image that hasn't yet been added to the image list.
					self.addImage(imgKey)
					imgIdx = self._imageList[imgKey]
			self.SetPageImage(pgIdx, imgIdx)

	
	def getPageImage(self, pg):
		""" Returns the index of the specified page's image in the 
		current image list, or -1 if no image is set for the page.
		"""
		ret = -1
		pgIdx = self._getPageIndex(pg)
		if pgIdx is not None:
			ret = self.GetPageImage(pgIdx)
		return ret
		
	
	def appendPage(self, pgCls=None, caption="", imgKey=None):
		""" Appends the page to the pageframe, and optionally sets
		the page caption and image. The image should have already
		been added to the pageframe if it is going to be set here.
		"""
		return self.insertPage(self.GetPageCount(), pgCls, caption, imgKey)
		
	
	def insertPage(self, pos, pgCls=None, caption="", imgKey=None):
		""" Insert the page into the pageframe at the specified position, 
		and optionally sets the page caption and image. The image 
		should have already been added to the pageframe if it is 
		going to be set here.
		"""
		if pgCls is None:
			pgCls = self.PageClass
		if isinstance(pgCls, dPage):
			pg = pgCls
		else:
			pg = pgCls(self)
		if imgKey:
			idx = self._imageList[imgKey]
			self.InsertPage(pos, pg, text=caption, imageId=idx)
		else:
			self.InsertPage(pos, pg, text=caption)
		return self.Pages[pos]


	def removePage(self, pgOrPos, delPage=True):
		"""Removes the specified page. You can specify a page by either
		passing the page itself, or a position. If delPage is True (default),
		the page is released, and None is returned. If delPage is
		False, the page is returned.
		"""
		pos = pgOrPos
		if isinstance(pgOrPos, int):
			pg = self.Pages[pgOrPos]
		else:
			pg = pgOrPos
			pos = self.Pages.index(pg)
		if delPage:
			self.DeletePage(pos)
			ret = None
		else:
			self.RemovePage(pos)
			ret = pg
		return ret
	
	
	def movePage(self, oldPgOrPos, newPos, selecting=True):
		"""Moves the specified 'old' page to the new position and
		optionally selects it. If an invalid page number is passed,
		it returns False without changing anything.
		"""
		self.Parent.lockDisplay()
		pos = oldPgOrPos
		if isinstance(oldPgOrPos, int):
			if oldPgOrPos > self.PageCount-1:
				return False
			pg = self.Pages[oldPgOrPos]
		else:
			pg = oldPgOrPos
			pos = self.Pages.index(pg)
		# Make sure that the new position is valid
		newPos = max(0, newPos)
		newPos = min(self.PageCount-1, newPos)
		if newPos == pos:
			# No change
			return
		cap = pg.Caption
		self.RemovePage(pos)
		self.InsertPage(newPos, pg, cap)
		if selecting:
			self.SelectedPage = pg
		self.Parent.unlockDisplay()
		return True
		
		
	def cyclePages(self, num):
		"""Moves through the pages by the specified amount, wrapping
		around the ends. Negative values move to previous pages; positive
		move through the next pages.
		"""
		fwd = num > 0
		self.lockDisplay()
		for ii in range(abs(num)):
			self.AdvanceSelection(fwd)
		self.unlockDisplay()
		
		
	def layout(self):
		""" Wrap the wx version of the call, if possible. """
		self.Layout()
		try:
			# Call the Dabo version, if present
			self.Sizer.layout()
		except:
			pass

		
	def _getPageIndex(self, pg):
		""" Resolves page references to the page index, which is what
		is needed by most methods that act on pages.
		"""
		ret = None
		if isinstance(pg, int):
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
			return self._pageClass
		except AttributeError:
			return dPage
			
	def _setPageClass(self, value):
		if issubclass(value, cm.dControlMixin):
			self._pageClass = value
		else:
			raise TypeError, "PageClass must descend from a Dabo base class."
			
			
	def _getPageCount(self):
		return int(self.GetPageCount())
		
	def _setPageCount(self, value):
		if self._constructed():
			value = int(value)
			pageCount = self.GetPageCount()
			pageClass = self.PageClass
			if value < 0:
				raise ValueError, "Cannot set PageCount to less than zero."
		
			if value > pageCount:
				for i in range(pageCount, value):
					self.appendPage(pageClass, caption="Page %s" % (i+1,))
			elif value < pageCount:
				for i in range(pageCount, value, -1):
					self.DeletePage(i-1)
		else:
			self._properties["PageCount"] = value
	
	def _getPgs(self):
		## pkm: It is possible for pages to not be instances of dPage
		##      (such as in the AppWizard), resulting in self.PageCount > len(self.Pages)
		##      if using the commented code below. 
		#return [pg for pg in self.Children	if isinstance(pg, dabo.ui.dPage) ]
		return [self.GetPage(pg) for pg in range(self.PageCount)]


	def _getSelectedPage(self):
		try:
			ret = self.GetPage(self.GetSelection())
		except:
			ret = None
		return ret		

	def _setSelectedPage(self, pg):
		if self._constructed():
			idx = self._getPageIndex(pg)
			self.SetSelection(idx)
		else:
			self._properties["SelectedPage"] = pg
		

	def _getSelectedPageNumber(self):
		return self.GetSelection()

	def _setSelectedPageNumber(self, val):
		if self._constructed():
			self.SetSelection(val)
		else:
			self._properties["SelectedPageNumber"] = val
		

	def _getTabPosition(self):
		if self._hasWindowStyleFlag(self._tabposBottom):
			return "Bottom"
		elif self._hasWindowStyleFlag(self._tabposRight):
			return "Right"
		elif self._hasWindowStyleFlag(self._tabposLeft):
			return "Left"
		else:
			return "Top"

	def _setTabPosition(self, value):
		value = str(value)

		self._delWindowStyleFlag(self._tabposBottom)
		self._delWindowStyleFlag(self._tabposRight)
		self._delWindowStyleFlag(self._tabposLeft)

		if value == "Top":
			pass
		elif value == "Left":
			self._addWindowStyleFlag(self._tabposLeft)
		elif value == "Right":
			self._addWindowStyleFlag(self._tabposRight)
		elif value == "Bottom":
			self._addWindowStyleFlag(self._tabposBottom)
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
	
	Pages = property(_getPgs, None, None,
			_("Returns a list of the contained pages.  (list)") )
	
	SelectedPage = property(_getSelectedPage, _setSelectedPage, None,
			_("References the current frontmost page.  (dPage)") )
						
	SelectedPageNumber = property(_getSelectedPageNumber, _setSelectedPageNumber, 
			None,
			_("Returns the index of the current frontmost page.  (int)") )
						
	TabPosition = property(_getTabPosition, _setTabPosition, None, 
			_("""Specifies where the page tabs are located. (int) 
				Top (default) 
				Left 
				Right 
				Bottom""") )


	DynamicPageClass = makeDynamicProperty(PageClass)
	DynamicPageCount = makeDynamicProperty(PageCount)
	DynamicSelectedPage = makeDynamicProperty(SelectedPage)
	DynamicSelectedPageNumber = makeDynamicProperty(SelectedPageNumber)
	DynamicTabPosition = makeDynamicProperty(TabPosition)
