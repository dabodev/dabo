import dPanel, dSizer
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class dPage(dPanel.dScrollPanel):
	""" Create a page to appear as a tab in a dPageFrame.
	"""
	_IsContainer = True
	
	def _afterInit(self):
		self.initSizer()
		self.itemsCreated = False
		super(dPage, self)._afterInit()
		
	def _initEvents(self):
		super(dPage, self)._initEvents()
		self.bindEvent(dEvents.PageEnter, self.__onPageEnter)
		self.bindEvent(dEvents.PageLeave, self.__onPageLeave)

	def initSizer(self):
		""" Set up the default vertical box sizer for the page.
		"""
		self.Sizer = dSizer.dSizer("vertical")

	def createItems(self):
		""" Create the controls in the page.

		Called when the page is entered for the first time, allowing subclasses
		to delay-populate the page.
		"""
		pass


	def __onPageEnter(self, evt):
		if not self.itemsCreated:
			self.createItems()
			self.itemsCreated = True
			self.Sizer.layout()
			
			# Needed on Linux to get the sizer to layout:
			self.Size = (-1,-1)

						
	def __onPageLeave(self, evt):
		if hasattr(self, "Form"):
			self.Form.activeControlValid()
			

	def _getPagePosition(self):
		""" Returns the position of this page within its parent.
		"""
		parent = self.Parent
		cnt = parent.GetPageCount()
		ret = -1
		for i in range(cnt):
			if parent.GetPage(i) == self:
				ret = i
				break
		return ret
	

	def _getCaption(self):
		# Need to determine which page we are
		ret = ""
		pos = self._getPagePosition()
		if pos > -1:
			ret = self.Parent.GetPageText(pos)
		return ret
	def _setCaption(self, val):
		if self._constructed():
			pos = self._getPagePosition()
			if pos > -1:
				self.Parent.SetPageText(pos, val)
		else:
			self._properties["Caption"] = val
			
	
	def _getImage(self):
		return self.Parent.getPageImg(self)
	def _setImage(self, imgKey):
		if self._constructed():
			self.Parent.setPageImage(self, imgKey)
		else:
			self._properties["Image"] = imgKey
		
	
	Caption = property(_getCaption, _setCaption, None, 
			_("The text identifying this particular page.  (str)") )

	Image = property(_getImage, _setImage, None, 
			_("""Sets the image that is displayed on the page tab. This is
			determined by the key value passed, which must refer to an 
			image already added to the parent pageframe.
			When used to retrieve an image, it returns the index of the
			page's image in the parent pageframe's image list.   (int)""") )

