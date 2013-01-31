# -*- coding: utf-8 -*-
import wx
import wx.lib.hyperlink as hyperlink
import dabo
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dControlMixin as dcm
import dabo.dEvents as dEvents
import dabo.dColors as dColors
from alignmentMixin import AlignmentMixin



class dHyperLink(dcm.dControlMixin, AlignmentMixin, hyperlink.HyperLinkCtrl):
	"""
	Creates a hyperlink that, when clicked, launches the specified
	URL in the user's default browser, or raises a Hit event for your
	code to catch and take the appropriate action.
	"""
	def __init__(self, parent, properties=None, attProperties=None,
			*args, **kwargs):
		self._baseClass = dHyperLink
		preClass = hyperlink.HyperLinkCtrl

		dcm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)

		# Make the rollover effect the default, unless it was specified as False.
		self.ShowHover = self.ShowHover
		self.Bind(hyperlink.EVT_HYPERLINK_LEFT, self._onWxHit)  ## only called if ShowInBrowser False
		self.DoPopup(False)


	def onResize(self, evt):
		if self.Application.Platform == "Win":
			self.refresh()


	def refresh(self):
		super(dHyperLink, self).refresh()
		self.UpdateLink(True)


	def _setColors(self):
		"""Updated the link with the specified colors."""
		lc, vc, rc = self.LinkColor, self.VisitedColor, self.HoverColor
		if isinstance(lc, basestring):
			lc = dColors.colorTupleFromName(lc)
		if isinstance(vc, basestring):
			vc = dColors.colorTupleFromName(vc)
		if isinstance(rc, basestring):
			rc = dColors.colorTupleFromName(rc)
		self.SetColours(lc, vc, rc)
		self.UpdateLink(True)


	def _getUnderlines(self, which):
		"""Returns the status for the various underline settings."""
		types = ("link", "hover", "visited")
		return self.GetUnderlines()[types.index(which)]


	def _setUnderlines(self, link, visited, hover):
		"""Updated the link with the specified underline settings."""
		self.SetUnderlines(link, visited, hover)
		self.UpdateLink(True)


	def _getShowInBrowser(self):
		return getattr(self, "_showInBrowser", True)

	def _setShowInBrowser(self, val):
		if self._constructed():
			self._showInBrowser = bool(val)
			self.AutoBrowse(val)
		else:
			self._properties["ShowInBrowser"] = val


	def _getHoverColor(self):
		return getattr(self, "_hoverColor", self.GetColours()[2])

	def _setHoverColor(self, val):
		if self._constructed():
			if val != self.HoverColor:
				self._hoverColor = val
				self._setColors()
		else:
			self._properties["HoverColor"] = val


	def _getHoverUnderline(self):
		return self._getUnderlines("hover")

	def _setHoverUnderline(self, val):
		if self._constructed():
			if val != self.HoverUnderline:
				self._setUnderlines(self.LinkUnderline, self.VisitedUnderline, bool(val))
		else:
			self._properties["HoverUnderline"] = val


	def _getLinkColor(self):
		return getattr(self, "_linkColor", self.GetColours()[0])

	def _setLinkColor(self, val):
		if self._constructed():
			if val != self.LinkColor:
				self._linkColor = val
				self._setColors()
		else:
			self._properties["LinkColor"] = val


	def _getLinkUnderline(self):
		return self._getUnderlines("link")

	def _setLinkUnderline(self, val):
		if self._constructed():
			if val != self.LinkUnderline:
				self._setUnderlines(bool(val), self.VisitedUnderline, self.HoverUnderline)
		else:
			self._properties["LinkUnderline"] = val


	def _getShowHover(self):
		return getattr(self, "_showHover", True)

	def _setShowHover(self, val):
		if self._constructed():
			self._showHover = bool(val)
			self.EnableRollover(val)
		else:
			self._properties["ShowHover"] = val


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
		return getattr(self, "_visitedColor", self.GetColours()[1])

	def _setVisitedColor(self, val):
		if self._constructed():
			if val != self.VisitedColor:
				self._visitedColor = val
				self._setColors()
		else:
			self._properties["VisitedColor"] = val


	def _getVisitedUnderline(self):
		return self._getUnderlines("visited")

	def _setVisitedUnderline(self, val):
		if self._constructed():
			if val != self.VisitedUnderline:
				self._setUnderlines(self.LinkUnderline, bool(val), self.HoverUnderline)
		else:
			self._properties["VisitedUnderline"] = val


	ShowInBrowser = property(_getShowInBrowser, _setShowInBrowser, None,
			_("""Specifies the behavior of clicking on the hyperlink:
					True: open URL in user's default web browser (default)
					False: raise Hit event for your code to handle"""))

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

	ForeColor = LinkColor


class _dHyperLink_test(dHyperLink):
	def _onHit(self, evt):
		print "hit"


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
		self.bindEvent(dabo.dEvents.Hit, self._onHit)
		#self.ShowInBrowser = False


if __name__ == "__main__":
	import test
	test.Test().runTest(_dHyperLink_test)
