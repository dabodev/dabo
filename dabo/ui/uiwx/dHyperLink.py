# -*- coding: utf-8 -*-
import wx
import wx.lib.hyperlink as hyperlink
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
import dabo.dColors as dColors
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dHyperLink(dcm.dControlMixin, hyperlink.HyperLinkCtrl):
	"""Creates a hyperlink that, when clicked, launches the specified
	URL in the user's default browser.
	"""
	def __init__(self, parent, properties=None, attProperties=None,
			*args, **kwargs):
		self._baseClass = dHyperLink
		preClass = hyperlink.HyperLinkCtrl
		self._hoverColor = None
		self._linkColor = None
		self._visitedColor = None
		self._hoverUnderline = None
		self._linkUnderline = None
		self._visitedUnderline = None
		
		# Make the rollover effect the default, unless it was specified as False.
		self._showHover = self._extractKey(attProperties, "ShowHover", None)
		if self._showHover is not None:
			self._showHover = (self._showHover == "True")
		else:
			self._showHover = self._extractKey((kwargs, properties, attProperties), 
					"ShowHover", True)
		kwargs["ShowHover"] = self._showHover

		dcm.dControlMixin.__init__(self, preClass, parent, properties, 
				attProperties, *args, **kwargs)
		
		# Initialize the local atts to match the control.
		self._linkColor, self._visitedColor, self._hoverColor = self.GetColours()
		self._linkUnderline, self._visitedUnderline, self._hoverUnderline = self.GetUnderlines()
		
		
	def refresh(self):
		super(dHyperLink, self).refresh()
		self.UpdateLink(True)
	
	
	def _setColors(self):
		"""Updated the link with the specified colors."""
		lc, vc, rc = self._linkColor, self._visitedColor, self._hoverColor
		if isinstance(lc, basestring):
			try:
				lc = dColors.colorTupleFromName(lc)
			except: pass
		if isinstance(vc, basestring):
			try:
				vc = dColors.colorTupleFromName(vc)
			except: pass
		if isinstance(rc, basestring):
			try:
				rc = dColors.colorTupleFromName(rc)
			except: pass
		self.SetColours(lc, vc, rc)
		self.UpdateLink(True)
		
	
	def _setUnderlines(self):
		"""Updated the link with the specified underline settings."""
		self.SetUnderlines(self._linkUnderline, self._visitedUnderline, 
				self._hoverUnderline)
		self.UpdateLink(True)
		
	
	def _getHoverColor(self):
		return self._hoverColor

	def _setHoverColor(self, val):
		self._hoverColor = val
		self._setColors()


	def _getHoverUnderline(self):
		return self._hoverUnderline

	def _setHoverUnderline(self, val):
		self._hoverUnderline = val
		self._setUnderlines()


	def _getLinkColor(self):
		return self._linkColor

	def _setLinkColor(self, val):
		self._linkColor = val
		self._setColors()


	def _getLinkUnderline(self):
		return self._linkUnderline

	def _setLinkUnderline(self, val):
		self._linkUnderline = val
		self._setUnderlines()


	def _getShowHover(self):
		return self._showHover

	def _setShowHover(self, val):
		self._showHover = val
		self.EnableRollover(val)


	def _getURL(self):
		return self.GetURL()

	def _setURL(self, val):
		self.SetURL(val)


	def _getVisited(self):
		return self.GetVisited()

	def _setVisited(self, val):
		self.SetVisited(val)
		self.UpdateLink(True)


	def _getVisitedColor(self):
		return self._visitedColor

	def _setVisitedColor(self, val):
		self._visitedColor = val
		self._setColors()


	def _getVisitedUnderline(self):
		return self._visitedUnderline

	def _setVisitedUnderline(self, val):
		self._visitedUnderline = val
		self._setUnderlines()


	HoverColor = property(_getHoverColor, _setHoverColor, None,
			_("Color of the link when the mouse passes over it.  (str or tuple)"))
	
	HoverUnderline = property(_getHoverUnderline, _setHoverUnderline, None,
			_("Is the link underlined when the mouse passes over it?  (bool)"))
	
	LinkColor = property(_getLinkColor, _setLinkColor, None,
			_("Normal (unvisited) link text color.  (str or tuple)"))
	
	LinkUnderline = property(_getLinkUnderline, _setLinkUnderline, None,
			_("Is the link underlined in the normal state?  (bool)"))
	
	ShowHover = property(_getShowHover, _setShowHover, None,
			_("Does the link show the hover effect?  (bool)"))
	
	URL = property(_getURL, _setURL, None,
			_("URL for this link  (str)"))
	
	Visited = property(_getVisited, _setVisited, None,
			_("Has this link been visited?  (bool)"))
	
	VisitedColor = property(_getVisitedColor, _setVisitedColor, None,
			_("Color of visited links  (str or tuple)"))
	
	VisitedUnderline = property(_getVisitedUnderline, _setVisitedUnderline, None,
			_("Is the link underlined in the visited state?  (bool)"))



class _dHyperLink_test(dHyperLink):
	def afterInit(self):
		self.Caption = "The Dabo Wiki"
		self.FontSize = 24
		self.URL = "http://dabodev.com/wiki/"
		self.LinkColor = "olive"
		self.VisitedColor = "maroon"
		self.HoverColor = "crimson"
		self.LinkUnderline = True
		self.HoverUnderline = False
		self.VisitedUnderline = True


if __name__ == "__main__":
	import test
	test.Test().runTest(_dHyperLink_test)
