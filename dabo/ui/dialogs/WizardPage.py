# -*- coding: utf-8 -*-
import dabo.ui
dabo.ui.loadUI("wx")
from dabo.dLocalize import _
import dabo.dEvents as dEvents
import dabo.dConstants as k



class WizardPage(dabo.ui.dScrollPanel):
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._titleLabel = None
		self._caption = _("Wizard Page")
		self._titleFontFace = ""
		self._titleFontSize = 18
		self._picture = None

		super(WizardPage, self).__init__(parent=parent,
				properties=properties, *args, **kwargs)

		self._baseClass = WizardPage
		self._wizard = None
		self._nextPage = self._prevPage = None
		self.setup()
		self.layout()


	def setup(self):
		self.makeSizer()
		self._titleLabel = dabo.ui.dLabel(self, Caption=self.Caption, FontSize=self.TitleSize,
				FontFace=self.TitleFace)
		ln = dabo.ui.dLine(self)
		sz = self.Sizer
		sz.prepend(ln, "x")
		sz.prependSpacer(16)
		sz.prepend(self._titleLabel, alignment="center")
		sz.DefaultSpacing = 0
		self._createBody()


	def _createBody(self):
		# Call the user-customizable code first
		self.createBody()
		# Now make it look nice
		self.layout()


	def createBody(self):
		"""
		This is the method to override in subclasses to add any text
		or other controls for this page.
		"""
		pass


	def makeSizer(self):
		"""
		Create a simple sizer. This can be overridden in subclasses
		if specific sizer configurations are needed.
		"""
		sz = self.Sizer = dabo.ui.dSizer("v")
		sz.DefaultSpacing = 5
		sz.DefaultBorder = 12
		sz.DefaultBorderLeft = sz.DefaultBorderRight = True


	def onLeavePage(self, direction):
		"""
		This method is called before the wizard changes pages.
		Returning False will prevent the page from changing. Use
		it to make sure that the user has completed all the required
		actions before proceeding to the next step of the wizard.
		The direction passed to this method will either be 'forward'
		or 'back'.
		"""
		return True


	def onEnterPage(self, direction):
		"""
		This method will be called just as the page is about to
		be made visible. You cannot prevent this from happening,
		as you can with onLeavePage(), but you can use this event
		to do whatever preliminary work that page needs before it
		is displayed. The 'direction' parameter is the same as for
		onLeavePage().
		"""
		pass


	def nextPage(self):
		"""
		This method can be overridden in subclasses to provide
		conditional navigation through the wizard. By default, it returns
		the integer 1, meaning move one page forward in the wizards page
		collection. If you wish to skip the next page in order, you can simply
		return 2, and the wizard will jump forward to the second page in
		its page collection after the current one.
		"""
		return 1


	def prevPage(self):
		"""
		Like nextPage, you can override this method to conditionally
		navigate through the wizard pages. Default = -1
		"""
		return -1


	# Property definitions.
	def _getCaption(self):
		return self._caption

	def _setCaption(self, val):
		if self._constructed():
			self._caption = val
			if self._titleLabel:
				self._titleLabel.Caption = val
				self.layout()
		else:
			self._properties["Caption"] = val


	def _getPicture(self):
		return self._picture

	def _setPicture(self, val):
		if self._constructed():
			self._picture = val
		else:
			self._properties["Picture"] = val


	def _getTitleBold(self):
		try:
			return self._titleFontBold
		except AttributeError:
			self._titleFontBold = self.FontBold
			return self._titleFontBold

	def _setTitleBold(self, val):
		self._titleFontBold = val
		if self._titleLabel:
			self._titleLabel.FontBold = val
			self.layout()


	def _getTitleFace(self):
		try:
			return self._titleFontFace
		except AttributeError:
			self._titleFontFace = self.FontFace
			return self._titleFontFace

	def _setTitleFace(self, val):
		self._titleFontFace = val
		if self._titleLabel:
			self._titleLabel.FontFace = val
			self.layout()


	def _getTitleItalic(self):
		try:
			return self._titleFontItalic
		except AttributeError:
			self._titleFontItalic = self.FontItalic
			return self._titleFontItalic

	def _setTitleItalic(self, val):
		self._titleFontItalic = val
		if self._titleLabel:
			self._titleLabel.FontItalic = val
			self.layout()


	def _getTitleSize(self):
		return self._titleFontSize

	def _setTitleSize(self, val):
		self._titleFontSize = val
		if self._titleLabel:
			self._titleLabel.FontSize = val
			self.layout()


	def _getWizard(self):
		ret = self._wizard
		if ret is None:
			ret = self.Form
		return ret

	def _setWizard(self, val):
		self._wizard = val



	Caption = property(_getCaption, _setCaption, None,
			_("The text that appears as the title of the page  (str)"))

	Picture = property(_getPicture, _setPicture, None,
			_("""Normally None, but you can set it to some other image to have the wizard display
			a different picture for this page  (None or image path)"""))

	TitleBold = property(_getTitleBold, _setTitleBold, None,
			_("Controls whether the title text is bold.  (bool)") )

	TitleFace = property(_getTitleFace, _setTitleFace, None,
			_("Name of the font face used for the Title.  (string)") )

	TitleItalic = property(_getTitleItalic, _setTitleItalic, None,
			_("Controls whether the title text is italic.  (bool)") )

	TitleSize = property(_getTitleSize, _setTitleSize, None,
			_("Size in points for the Title (default=18).  (int)") )

	Wizard = property(_getWizard, _setWizard, None,
			_("Reference to the wizard form this page is in  (Wizard object)"))
