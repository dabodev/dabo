import dPanel, dSizer
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dPage(dPanel.dScrollPanel):
	"""Creates a page to appear as a tab in a pageframe."""
	def __init__(self, *args, **kwargs):
		self._caption = ""
		super(dPage, self).__init__(*args, **kwargs)
		self._baseClass = dPage	
		self.SetScrollbars(10, 10, -1, -1)

		
	def _afterInit(self):
		self.initSizer()
		self.itemsCreated = False
		super(dPage, self)._afterInit()
		
		
	def _initEvents(self):
		super(dPage, self)._initEvents()
		self.bindEvent(dEvents.PageEnter, self.__onPageEnter)
		self.bindEvent(dEvents.PageLeave, self.__onPageLeave)
		

	def initSizer(self):
		""" Set up the default vertical box sizer for the page."""
		try:
			szCls = self.Parent.PageSizerClass
		except:
			# Not part of a paged control
			return
		if szCls is not None:
			self.Sizer = szCls("vertical")
		

	def _createItems(self):
		self.createItems()
		self.itemsCreated = True
		self.layout()


	def createItems(self):
		""" Create the controls in the page.

		Called when the page is entered for the first time, allowing subclasses
		to delay-populate the page.
		"""
		pass


	def __onPageEnter(self, evt):
		if not self.itemsCreated:
			self._createItems()

	
	def __onPageLeave(self, evt):
		if hasattr(self, "Form"):
			if hasattr(self.Form, "activeControlValid"):
				self.Form.activeControlValid()
			

	def _getPagePosition(self):
		""" Returns the position of this page within its parent."""
		try:
			ret = self.Parent.Pages.index(self)
		except:
			ret = -1
		return ret

	

	def _getCaption(self):
		# Need to determine which page we are
		ret = ""
		pos = self._getPagePosition()
		if pos > -1:
			ret = self.Parent.GetPageText(pos)
		return ret

	def _setCaption(self, val):
		self._caption = val
		if self._constructed():
			pos = self._getPagePosition()
			if pos > -1:
				self.Parent.SetPageText(pos, val)
		else:
			self._properties["Caption"] = val
			
	
	def _getImage(self):
		return self.Parent.getPageImage(self)

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


	DynamicCaption = makeDynamicProperty(Caption)
	DynamicImage = makeDynamicProperty(Image)

