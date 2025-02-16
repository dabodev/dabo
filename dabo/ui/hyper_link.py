# -*- coding: utf-8 -*-
import wx
import wx.lib.agw.hyperlink as hyperlink

from .. import color_tools
from .. import events
from .. import ui
from ..localization import _
from . import AlignmentMixin
from . import dControlMixin
from . import makeDynamicProperty


class dHyperLink(dControlMixin, AlignmentMixin, hyperlink.HyperLinkCtrl):
    """
    Creates a hyperlink that, when clicked, launches the specified
    URL in the user's default browser, or raises a Hit event for your
    code to catch and take the appropriate action.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dHyperLink
        preClass = hyperlink.HyperLinkCtrl

        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

        # Make the rollover effect the default, unless it was specified as False.
        self.ShowHover = self.ShowHover
        self.Bind(
            hyperlink.EVT_HYPERLINK_LEFT, self._onWxHit
        )  ## only called if ShowInBrowser False
        self.DoPopup(False)

    def onResize(self, evt):
        if self.Application.Platform == "Win":
            self.refresh()

    def refresh(self):
        super().refresh()
        self.UpdateLink(True)

    def _setColors(self):
        """Updated the link with the specified colors."""
        lc, vc, rc = self.LinkColor, self.VisitedColor, self.HoverColor
        if isinstance(lc, str):
            lc = color_tools.colorTupleFromName(lc)
        if isinstance(vc, str):
            vc = color_tools.colorTupleFromName(vc)
        if isinstance(rc, str):
            rc = color_tools.colorTupleFromName(rc)
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

    @property
    def HoverColor(self):
        """Color of the link when the mouse passes over it.  (str or tuple)"""
        return getattr(self, "_hoverColor", self.GetColours()[2])

    @HoverColor.setter
    def HoverColor(self, val):
        if self._constructed():
            if val != self.HoverColor:
                self._hoverColor = val
                self._setColors()
        else:
            self._properties["HoverColor"] = val

    @property
    def HoverUnderline(self):
        """Is the link underlined when the mouse passes over it?  (bool)"""
        return self._getUnderlines("hover")

    @HoverUnderline.setter
    def HoverUnderline(self, val):
        if self._constructed():
            if val != self.HoverUnderline:
                self._setUnderlines(self.LinkUnderline, self.VisitedUnderline, bool(val))
        else:
            self._properties["HoverUnderline"] = val

    @property
    def LinkColor(self):
        """Normal (unvisited) link text color.  (str or tuple)"""
        return getattr(self, "_linkColor", self.GetColours()[0])

    @LinkColor.setter
    def LinkColor(self, val):
        if self._constructed():
            if val != self.LinkColor:
                self._linkColor = val
                self._setColors()
        else:
            self._properties["LinkColor"] = val

    @property
    def LinkUnderline(self):
        """Is the link underlined in the normal state?  (bool)"""
        return self._getUnderlines("link")

    @LinkUnderline.setter
    def LinkUnderline(self, val):
        if self._constructed():
            if val != self.LinkUnderline:
                self._setUnderlines(bool(val), self.VisitedUnderline, self.HoverUnderline)
        else:
            self._properties["LinkUnderline"] = val

    @property
    def ShowInBrowser(self):
        """
        Specifies the behavior of clicking on the hyperlink:
            True: open URL in user's default web browser (default)
            False: raise Hit event for your code to handle
        """
        return getattr(self, "_showInBrowser", True)

    @ShowInBrowser.setter
    def ShowInBrowser(self, val):
        if self._constructed():
            self._showInBrowser = bool(val)
            self.AutoBrowse(val)
        else:
            self._properties["ShowInBrowser"] = val

    @property
    def ShowHover(self):
        """Does the link show the hover effect?  (bool)"""
        return getattr(self, "_showHover", True)

    @ShowHover.setter
    def ShowHover(self, val):
        if self._constructed():
            self._showHover = bool(val)
            self.EnableRollover(val)
        else:
            self._properties["ShowHover"] = val

    @property
    def URL(self):
        """URL for this link  (str)"""
        return self.GetURL()

    @URL.setter
    def URL(self, val):
        self.SetURL(val)

    @property
    def Visited(self):
        """Has this link been visited?  (bool)"""
        return self.GetVisited()

    @Visited.setter
    def Visited(self, val):
        self.SetVisited(val)
        self.UpdateLink(True)

    @property
    def VisitedColor(self):
        """Color of visited links  (str or tuple)"""
        return getattr(self, "_visitedColor", self.GetColours()[1])

    @VisitedColor.setter
    def VisitedColor(self, val):
        if self._constructed():
            if val != self.VisitedColor:
                self._visitedColor = val
                self._setColors()
        else:
            self._properties["VisitedColor"] = val

    @property
    def VisitedUnderline(self):
        """Is the link underlined in the visited state?  (bool)"""
        return self._getUnderlines("visited")

    @VisitedUnderline.setter
    def VisitedUnderline(self, val):
        if self._constructed():
            if val != self.VisitedUnderline:
                self._setUnderlines(self.LinkUnderline, bool(val), self.HoverUnderline)
        else:
            self._properties["VisitedUnderline"] = val

    ForeColor = LinkColor


ui.dHyperLink = dHyperLink


class _dHyperLink_test(dHyperLink):
    def _onHit(self, evt):
        print("hit")

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
        self.bindEvent(events.Hit, self._onHit)
        # self.ShowInBrowser = False


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dHyperLink_test)
