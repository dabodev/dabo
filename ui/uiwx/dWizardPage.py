import wx
import wx.wizard as wiz
import dabo
from dabo.dLocalize import _
import dabo.dEvents as dEvents
import dabo.dConstants as k

dabo.ui.loadUI("wx")
import dControlMixin as cm


class dWizardPage(wiz.PyWizardPage, cm.dControlMixin):
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dWizardPage
		preClass = wiz.PrePyWizardPage
		self._titleCaption = self.extractKey(kwargs, "Title")
		
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

		self._nextPage = self._prevPage = None
		self._title = None
		self._titleFontFace = self.FontFace
		self._titleFontSize = 18
		self.setup()
	
	
	def setup(self):
		self.makeSizer()
		self._title = dabo.ui.dLabel(self, Caption=self.Title, FontSize=self.TitleFontSize,
				FontFace=self.TitleFontFace)
		self.Sizer.prepend(self._title, 0, "x", alignment="center")
				
	
	def makeSizer(self):
		""" Create a simple sizer. This can be overridden in subclasses
		if specific sizer configurations are needed.
		"""
		self.Sizer = dabo.ui.dSizer("v")

	def onLeavePage(self, direction):
		return True
		
	def onEnterPage(self, direction):
		return True
		

	# Property definitions.
	def _getNext(self):
		return self._nextPage
	def _setNext(self, pg):
		self._nextPage = pg

	def _getPrev(self):
		return self._prevPage
	def _setPrev(self, pg):
		self._prevPage = pg

	def _getTitle(self):
		return self._titleCaption
	def _setTitle(self, val):
		self._titleCaption = val
		if self._title:
			self._title.Caption = val

	def _getTitleFace(self):
		return self._titleFontFace
	def _setTitleFace(self, val):
		self._titleFontFace = val
		if self._title:
			self._title.FontFace = val

	def _getTitleSize(self):
		return self._titleFontSize
	def _setTitleSize(self, val):
		self._titleFontSize = val
		if self._title:
			self._title.FontSize = val


	NextPage = property(_getNext, _setNext, None,
			_("Reference to the next page in the wizard  (dWizardPage)") )

	PrevPage = property(_getPrev, _setPrev, None,
			_("Reference to the previous page in the wizard  (dWizardPage)") )

	Title = property(_getTitle, _setTitle, None,
			_("Displays a title at the top of the page.  (string)") )

	TitleFontFace = property(_getTitleFace, _setTitleFace, None,
			_("Name of the font face used for the Title.  (string)") )

	TitleSize = property(_getTitleSize, _setTitleSize, None,
			_("Size in points for the Title (default=18).  (int)") )
	