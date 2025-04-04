# -*- coding: utf-8 -*-
import wx
import wx.lib.agw.pycollapsiblepane as pcp

from .. import ui
from ..localization import _
from . import dControlMixin
from . import dPanel


class dCollapsiblePanel(dControlMixin, pcp.PyCollapsiblePane):
    """
    A collapsible pane is a container with an embedded button-like control which can
    be used by the user to collapse or expand the pane's contents.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        val = self._extractKey((kwargs, properties, attProperties), "PanelStyle", "Label")
        try:
            agwStyle = {"l": wx.CP_GTK_EXPANDER, "b": 0}[val[:1].lower()]
        except (KeyError, TypeError):
            raise ValueError("The only possible values are 'Label' or 'Button'.")
        kwargs["agwStyle"] = wx.CP_NO_TLW_RESIZE | agwStyle
        kwargs["style"] = (
            self._extractKey((kwargs, properties, attProperties), "style", 0) | wx.CLIP_CHILDREN
        )
        self.itemsCreated = False
        self._baseClass = dCollapsiblePanel
        preClass = pcp.PyCollapsiblePane
        dControlMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
        self._pPane = dPanel(self, Visible=False, BorderStyle="None")

    def _initEvents(self):
        super()._initEvents()
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._onWxHit)

    def _initProperties(self):
        self.ExpanderDimensions = (4, 8)
        super()._initProperties()

    def _onWxHit(self, evt):
        parent = self.Parent
        parent.lockDisplay()
        parent.layout()
        parent.unlockDisplay()
        super()._onWxHit(evt)

    def Collapse(self, collapse=True):
        if collapse:
            self.collapse()
        else:
            self.expand()

    def _createItems(self):
        self.itemsCreated = True
        self.lockDisplay()
        self.createItems()
        self.layout()
        ui.callAfter(self.unlockDisplay)

    def createItems(self):
        """Create the controls in the pane.

        Called when the pane is expanded for the first time, allowing subclasses
        to delay-populate the pane.
        """
        pass

    def collapse(self):
        pcp.PyCollapsiblePane.Collapse(self, True)

    def expand(self):
        if not self.itemsCreated:
            self._createItems()
        pcp.PyCollapsiblePane.Collapse(self, False)

    def Layout(self):
        self.layout()

    def layout(self):
        pcp.PyCollapsiblePane.Layout(self)
        pnl = self.Panel
        if pnl:
            try:
                pnl.layout()
            except AttributeError:
                pnl.Layout()

    # Property definitions
    @property
    def ExpanderDimensions(self):
        """Dimensions of the visible expander control."""
        return self.GetExpanderDimensions()

    @ExpanderDimensions.setter
    def ExpanderDimensions(self, val):
        if self._constructed():
            self.SetExpanderDimensions(*val)
        else:
            self._properties["ExpanderDimensions"] = val

    @property
    def Panel(self):
        """Return panel object reference."""
        return self.GetPane()

    @property
    def PanelStyle(self):
        """Specifies pane style and can be 'Label' (default) or 'Button'."""
        return getattr(self, "_paneStyle", "Label")


ui.dCollapsiblePanel = dCollapsiblePanel


class _CollapsiblePanelTest(dCollapsiblePanel):
    def initProperties(self):
        self.Caption = "Collapsible Panel Test"

    def createItems(self):
        panel = self.Panel
        gs = ui.dGridSizer(MaxCols=2)
        gs.append(ui.dTextBox(panel), "expand")
        gs.append(ui.dButton(panel, Caption="Test"), "expand")
        gs.setColExpand(True, (0, 1))
        panel.Sizer = gs


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_CollapsiblePanelTest)
