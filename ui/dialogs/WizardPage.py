import dabo
dabo.ui.loadUI("wx")
from dabo.dLocalize import _
import dabo.dEvents as dEvents
import dabo.dConstants as k



class WizardPage(dabo.ui.dPanel):
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = WizardPage
		self._titleCaption = self.extractKey(kwargs, "Title")
		
		super(WizardPage, self).__init__(parent=parent, 
				properties=properties, *args, **kwargs)
		
		self._nextPage = self._prevPage = None
		self._title = None
		self._titleFontFace = self.FontFace
		self._titleFontSize = 18
		self.setup()
		self.layout()
		
	
	def setup(self):
		self.makeSizer()
		if self.Title is None:
			self.Title = ""
		self._title = dabo.ui.dLabel(self, Caption=self.Title, FontSize=self.TitleSize,
				FontFace=self.TitleFace)
		ln = dabo.ui.dLine(self)
		self.Sizer.prepend(ln, "x")
		self.Sizer.prependSpacer(16)
		self.Sizer.prepend(self._title, alignment="center")
		self._createBody()
		
	
	def _createBody(self):
		# Call the user-customizable code first
		self.createBody()
		# Now make it look nice
		self.layout()
		
	
	def createBody(self):
		""" This is the method to override in subclasses to add any text
		or other controls for this page.
		"""
		pass
				
	
	def makeSizer(self):
		""" Create a simple sizer. This can be overridden in subclasses
		if specific sizer configurations are needed.
		"""
		sz = self.Sizer = dabo.ui.dSizer("v")
		sz.Spacing = 5
		sz.Border = 12
		sz.BorderLeft = sz.BorderRight = True


	def onLeavePage(self, direction):
		""" This method is called before the wizard changes pages.
		Returning False will prevent the page from changing. Use
		it to make sure that the user has completed all the required
		actions before proceeding to the next step of the wizard.
		The direction passed to this method will either be 'forward'
		or 'back'.
		"""
		return True
		
		
	def onEnterPage(self, direction):
		""" This method will be called just as the page is about to 
		be made visible. You cannot prevent this from happening, 
		as you can with onLeavePage(), but you can use this event
		to do whatever preliminary work that page needs before it
		is displayed. The 'direction' parameter is the same as for
		onLeavePage().
		"""
		pass
	
	
	def nextPage(self):
		""" This method can be overridden in subclasses to provide
		conditional navigation through the wizard. By default, it returns
		the integer 1, meaning move one page forward in the wizards page
		collection. If you wish to skip the next page in order, you can simply
		return 2, and the wizard will jump forward to the second page in 
		its page collection after the current one.
		"""
		return 1
	
	
	def prevPage(self):
		""" Like nextPage, you can override this method to conditionally
		navigate through the wizard pages. Default = -1
		"""
		return -1
		

	# Property definitions.
	def _getTitle(self):
		return self._titleCaption
	def _setTitle(self, val):
		self._titleCaption = val
		if self._title:
			self._title.Caption = val
			self.layout()

	def _getTitleFace(self):
		return self._titleFontFace
	def _setTitleFace(self, val):
		self._titleFontFace = val
		if self._title:
			self._title.FontFace = val
			self.layout()

	def _getTitleSize(self):
		return self._titleFontSize
	def _setTitleSize(self, val):
		self._titleFontSize = val
		if self._title:
			self._title.FontSize = val
			self.layout()


	Title = property(_getTitle, _setTitle, None,
			_("Displays a title at the top of the page.  (string)") )

	TitleFace = property(_getTitleFace, _setTitleFace, None,
			_("Name of the font face used for the Title.  (string)") )

	TitleSize = property(_getTitleSize, _setTitleSize, None,
			_("Size in points for the Title (default=18).  (int)") )
	