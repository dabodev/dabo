# -*- coding: utf-8 -*-
import sys
import wx
import dabo
import dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as cm
from dPage import dPage
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.ui import makeDynamicProperty


MSG_SMART_FOCUS_ABUSE = _("The '%s' control must inherit from dPage to use the UseSmartFocus feature.")


class dPageFrameMixin(cm.dControlMixin):
	"""Creates a container for an unlimited number of pages."""

	def __init__(self, preClass, parent, properties=None, attProperties=None, *args, **kwargs):
		kwargs["style"] = self._extractKey((properties, kwargs), "style", 0) | wx.CLIP_CHILDREN
		super(dPageFrameMixin, self).__init__(preClass, parent, properties=properties,
			attProperties=attProperties, *args, **kwargs)


	def _beforeInit(self, pre):
		self._imageList = {}
		self._pageSizerClass = dabo.ui.dSizer
		super(dPageFrameMixin, self)._beforeInit(pre)


	def _initEvents(self):
		super(dPageFrameMixin, self)._initEvents()
		self.Bind(self._evtPageChanged, self.__onPageChanged)
		self.Bind(self._evtPageChanging, self.__onPageChanging)
		self.bindEvent(dEvents.Create, self.__onCreate)


	def __onPageChanging(self, evt):
		"""The page has not yet been changed, so we can veto it if conditions call for it."""
		# Avoid event propagated from child frames.
		evt.StopPropagation()
		oldPageNum = evt.GetOldSelection()
		newPageNum = evt.GetSelection()
		if self._beforePageChange(oldPageNum, newPageNum) is False:
			evt.Veto()
		else:
			evt.Skip()
		if oldPageNum >= 0 and self.PageCount > oldPageNum and self.UseSmartFocus:
			try:
				self.Pages[oldPageNum]._saveLastActiveControl()
			except AttributeError:
				dabo.log.error(MSG_SMART_FOCUS_ABUSE % self.Name)
		self.raiseEvent(dEvents.PageChanging, oldPageNum=oldPageNum,
				newPageNum=newPageNum)


	def _beforePageChange(self, old, new):
		return self.beforePageChange(old, new)


	def beforePageChange(self, fromPage, toPage):
		"""Return False from this method to prevent the page from changing."""
		pass


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
			if oldPageNum >= 0:
				try:
					oldPage = self.Pages[oldPageNum]
					dabo.ui.callAfter(oldPage.raiseEvent, dEvents.PageLeave)
				except IndexError:
					# Page has already been released
					return

		if newPageNum >= 0 and self.PageCount > newPageNum:
			newPage = self.Pages[newPageNum]
			dabo.ui.callAfter(newPage.raiseEvent, dEvents.PageEnter)
			dabo.ui.callAfter(self.raiseEvent, dEvents.PageChanged,
					oldPageNum=oldPageNum, newPageNum=newPageNum)
			if self.UseSmartFocus:
				try:
					newPage._restoreLastActiveControl()
				except AttributeError:
					dabo.log.warn(MSG_SMART_FOCUS_ABUSE % self.Name)


	# Image-handling function
	def addImage(self, img, key=None):
		"""
		Adds the passed image to the control's ImageList, and maintains
		a reference to it that is retrievable via the key value.
		"""
		if key is None:
			key = ustr(img)
		if isinstance(img, basestring):
			img = dabo.ui.strToBmp(img)
		il = self.GetImageList()
		if not il:
			il = wx.ImageList(img.GetWidth(), img.GetHeight(), initialCount=0)
			self.AssignImageList(il)
		idx = il.Add(img)
		self._imageList[key] = idx


	def setPageImage(self, pg, imgKey):
		"""
		Sets the specified page's image to the image corresponding
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
			self.Pages[pgIdx].imgKey = imgKey


	def getPageImage(self, pg):
		"""
		Returns the index of the specified page's image in the
		current image list, or -1 if no image is set for the page.
		"""
		ret = -1
		pgIdx = self._getPageIndex(pg)
		if pgIdx is not None:
			ret = self.GetPageImage(pgIdx)
		return ret


	def appendPage(self, pgCls=None, caption="", imgKey=None, **kwargs):
		"""
		Appends the page to the pageframe, and optionally sets
		the page caption and image. The image should have already
		been added to the pageframe if it is going to be set here.

		Any kwargs sent will be passed on to the constructor of the
		page class.
		"""
		return self.insertPage(self.GetPageCount(), pgCls, caption, imgKey, **kwargs)


	def insertPage(self, pos, pgCls=None, caption="", imgKey=None,
			ignoreOverride=False, **kwargs):
		"""
		Insert the page into the pageframe at the specified position,
		and optionally sets the page caption and image. The image
		should have already been added to the pageframe if it is
		going to be set here.

		Any kwargs sent will be passed on to the constructor of the
		page class.
		"""
		# Allow subclasses to potentially override this behavior. This will
		# enable them to handle page creation in their own way. If overridden,
		# the method will return the new page.
		ret = None
		if not ignoreOverride:
			ret = self._insertPageOverride(pos, pgCls, caption, imgKey)
		if ret:
			return ret
		if pgCls is None:
			pgCls = self.PageClass
		if isinstance(pgCls, dPage):
			pg = pgCls
		else:
			# See if the 'pgCls' is either some XML or the path of an XML file
			if isinstance(pgCls, basestring):
				xml = pgCls
				from dabo.lib.DesignerClassConverter import DesignerClassConverter
				conv = DesignerClassConverter()
				pgCls = conv.classFromText(xml)
			pg = pgCls(self, **kwargs)
		if not caption:
			# Page could have its own default caption
			caption = pg._caption
		if caption.count("&") == 1 and caption[-1] != "&":
			hotkey = "alt+%s" % (caption[caption.index("&")+1],)
			self.Form.bindKey(hotkey, self._onHK)
			pg._rawCaption = caption
			if sys.platform.startswith("darwin"):
				# Other platforms underline the character after the &; Mac just
				# shows the &.
				caption = caption.replace("&", "")
		if imgKey:
			idx = self._imageList[imgKey]
			self.InsertPage(pos, pg, text=caption, select=False, imageId=idx)
		else:
			self.InsertPage(pos, pg, text=caption, select=False)
		self.Pages[pos].imgKey = imgKey
		self.layout()
		insertedPage = self.Pages[pos]
		insertedPage.Caption = caption
		return insertedPage
	def _insertPageOverride(self, pos, pgCls, caption, imgKey): pass


	def removePage(self, pgOrPos, delPage=True):
		"""
		Removes the specified page. You can specify a page by either
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
		"""
		Moves the specified 'old' page to the new position and
		optionally selects it. If an invalid page number is passed,
		it returns False without changing anything.
		"""
		self.Parent.lockDisplay()
		pos = oldPgOrPos
		if isinstance(oldPgOrPos, int):
			if oldPgOrPos > self.PageCount - 1:
				return False
			pg = self.Pages[oldPgOrPos]
		else:
			pg = oldPgOrPos
			pos = self.Pages.index(pg)
		# Make sure that the new position is valid
		newPos = max(0, newPos)
		newPos = min(self.PageCount - 1, newPos)
		if newPos == pos:
			# No change
			return
		cap = pg.Caption
		self.RemovePage(pos)
		self.insertPage(newPos, pg, caption=cap, imgKey=pg.imgKey)
		if selecting:
			self.SelectedPage = pg
		self.Parent.unlockDisplay()
		return True


	def cyclePages(self, num):
		"""
		Moves through the pages by the specified amount, wrapping
		around the ends. Negative values move to previous pages; positive
		move through the next pages.
		"""
		self.SelectedPageNumber = (self.SelectedPageNumber + num) % self.PageCount


	def layout(self):
		"""Wrap the wx version of the call, if possible."""
		self.Layout()
		try:
			# Call the Dabo version, if present
			self.Sizer.layout()
		except AttributeError:
			pass
		for pg in self.Pages:
			try:
				pg.layout()
			except AttributeError:
				# could be that the page is a single control, not a container
				pass
		if self.Application.Platform == "Win":
			self.refresh()


	def _getPageIndex(self, pg):
		"""
		Resolves page references to the page index, which is what
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


	def _onHK(self, evt):
		char = chr(evt.EventData["keyCode"]).lower()
		for page in self.Pages:
			if "&%s" % char in getattr(page, "_rawCaption", "").lower():
				self.SelectedPage = page
				page.setFocus()
				return
		# raise ValueError, "Caption for hotkey not found."  ## unsure if wise



	# property get/set functions:
	def _getPageClass(self):
		try:
			return self._pageClass
		except AttributeError:
			return dPage

	def _setPageClass(self, val):
		self._pageClass = val


	def _getPageCount(self):
		return int(self.GetPageCount())

	def _setPageCount(self, val):
		if self._constructed():
			val = int(val)
			pageCount = self.GetPageCount()
			pageClass = self.PageClass
			if val < 0:
				raise ValueError(_("Cannot set PageCount to less than zero."))

			if val > pageCount:
				for i in range(pageCount, val):
					pg = self.appendPage(pageClass)
					if not pg.Caption:
						pg.Caption = _("Page %s") % (i + 1,)
			elif val < pageCount:
				for i in range(pageCount, val, -1):
					self.DeletePage(i - 1)
		else:
			self._properties["PageCount"] = val


	def _getPages(self):
		## pkm: It is possible for pages to not be instances of dPage
		##      (such as in the AppWizard), resulting in self.PageCount > len(self.Pages)
		##      if using the commented code below.
		#return [pg for pg in self.Children	if isinstance(pg, dabo.ui.dPage) ]
		return [self.GetPage(pg) for pg in range(self.PageCount)]


	def _getPageSizerClass(self):
		return self._pageSizerClass

	def _setPageSizerClass(self, val):
		if self._constructed():
			self._pageSizerClass = val
		else:
			self._properties["PageSizerClass"] = val


	def _getSelectedPage(self):
		try:
			sel = self.GetSelection()
			if sel < 0:
				ret = None
			else:
				ret = self.GetPage(sel)
		except AttributeError:
			ret = None
		return ret

	@dabo.ui.deadCheck
	def _setSelectedPage(self, pg):
		if self._constructed():
			idx = self._getPageIndex(pg)
			self.SetSelection(idx)
		else:
			self._properties["SelectedPage"] = pg


	def _getSelectedPageNumber(self):
		return self.GetSelection()

	@dabo.ui.deadCheck
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

	def _setTabPosition(self, val):
		val = ustr(val)

		self._delWindowStyleFlag(self._tabposTop)
		self._delWindowStyleFlag(self._tabposBottom)
		self._delWindowStyleFlag(self._tabposRight)
		self._delWindowStyleFlag(self._tabposLeft)

		if val == "Top":
			self._addWindowStyleFlag(self._tabposTop)
		elif val == "Left":
			self._addWindowStyleFlag(self._tabposLeft)
		elif val == "Right":
			self._addWindowStyleFlag(self._tabposRight)
		elif val == "Bottom":
			self._addWindowStyleFlag(self._tabposBottom)
		else:
			raise ValueError(_("The only possible values are 'Top', 'Left', 'Right', and 'Bottom'"))


	def _getUpdateInactivePages(self):
		return getattr(self, "_updateInactivePages", True)

	def _setUpdateInactivePages(self, val):
		self._updateInactivePages = val


	def _getUseSmartFocus(self):
		return getattr(self, "_useSmartFocus", False)

	def _setUseSmartFocus(self, val):
		self._useSmartFocus = val


	# Property definitions:
	PageClass = property(_getPageClass, _setPageClass, None,
			_("""Specifies the class of control to use for pages by default. (classRef)
			This really only applies when using the PageCount property to set the
			number of pages. If you instead use AddPage() you still need to send
			an instance as usual. Class must descend from a dabo base class."""))

	PageCount = property(_getPageCount, _setPageCount, None,
			_("""Specifies the number of pages in the pageframe. (int)
			When using this to increase the number of pages, PageClass
			will be queried as the object to use as the page object."""))

	Pages = property(_getPages, None, None,
			_("Returns a list of the contained pages.  (list)"))

	PageSizerClass = property(_getPageSizerClass, _setPageSizerClass, None,
			_("""Default sizer class for pages added automatically to this control. Set
			this to None to prevent sizers from being automatically added to child
			pages. (dSizer or None)"""))

	SelectedPage = property(_getSelectedPage, _setSelectedPage, None,
			_("References the current frontmost page.  (dPage)"))

	SelectedPageNumber = property(_getSelectedPageNumber, _setSelectedPageNumber,
			None,
			_("Returns the index of the current frontmost page.  (int)"))

	TabPosition = property(_getTabPosition, _setTabPosition, None,
			_("""Specifies where the page tabs are located. (int)
				Top (default)
				Left
				Right
				Bottom"""))

	UpdateInactivePages = property(_getUpdateInactivePages, _setUpdateInactivePages, None,
			_("""Determines if the inactive pages are updated too. (bool)
			Setting it to False can significantly improve update performance
			of multipage forms. Default=True."""))

	UseSmartFocus = property(_getUseSmartFocus, _setUseSmartFocus, None,
			_("""Determines if focus has to be restored to the last active
			control on page when it become selected. (bool) Default=False.
			"""))


	DynamicPageClass = makeDynamicProperty(PageClass)
	DynamicPageCount = makeDynamicProperty(PageCount)
	DynamicSelectedPage = makeDynamicProperty(SelectedPage)
	DynamicSelectedPageNumber = makeDynamicProperty(SelectedPageNumber)
	DynamicTabPosition = makeDynamicProperty(TabPosition)
	DynamicUpdateInactivePages = makeDynamicProperty(UpdateInactivePages)
