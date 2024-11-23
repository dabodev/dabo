# -*- coding: utf-8 -*-
from .. import ui
from ..dLocalize import _
from .. import events
from .class_designer_prop_sheet import PropSheet
from .class_designer_tree_sheet import TreeSheet
from ..ui import dForm
from ..ui import dPageFrameNoTabs
from ..ui import dPanel
from ..ui import dSizer
from ..ui import dTextBox
from ..ui import dToggleButton


class MenuPropForm(dForm):
    """This form contains the PropSheet for the Menu Designer."""

    def afterSetMenuBar(self):
        self.ShowStatusBar = False

    #         ClassDesignerMenu.mkDesignerMenu(self)

    def onMenuOpen(self, evt):
        try:
            self.Controller.menuUpdate(evt, self.MenuBar)
        except AttributeError:
            # Not finished initializing
            pass

    def afterInit(self):
        self.Caption = _("Properties")
        pnl = dPanel(self)
        self.Sizer.append1x(pnl)
        sz = pnl.Sizer = dSizer("v")

        txt = dTextBox(pnl, ReadOnly=True, RegID="txtObj")
        hsz = dSizer("h")
        hsz.append1x(txt)
        self.treeBtn = dToggleButton(
            pnl,
            Height=txt.Height,
            Width=txt.Height,
            Caption="",
            Picture="downTriangleBlack",
            DownPicture="upTriangleBlack",
        )
        self.treeBtn.bindEvent(events.Hit, self.onToggleTree)
        hsz.append(self.treeBtn)

        brdr = 10
        sz.appendSpacer(brdr)
        sz.DefaultBorderLeft = sz.DefaultBorderRight = True
        sz.DefaultBorder = brdr
        sz.append(hsz, "x")
        sz.appendSpacer(5)

        self.mainPager = mp = dPageFrameNoTabs(pnl, PageClass=dPanel)
        mp.PageCount = 2
        mp.bindEvent(events.PageChanged, self.onMainPageChanged)
        sz.append1x(mp)
        sz.appendSpacer(brdr)
        self.propPage = pp = mp.Pages[0]
        self.treePage = tp = mp.Pages[1]
        psz = pp.Sizer = dSizer("v")
        tsz = tp.Sizer = dSizer("v")

        # Add the PropSheet
        ps = PropSheet(self.propPage, RegID="_propSheet", Controller=self.Controller)
        self.propPage.Sizer = dSizer("v")
        self.propPage.Sizer.append1x(ps)

        # Create the tree
        self._tree = TreeSheet(tp, MultipleSelect=False, Controller=self.Controller)
        self._tree.MultipleSelect = False
        dabo.ui.callAfterInterval(500, self._tree.expandAll)
        tp.Sizer.append1x(self._tree, border=10)
        mp.SelectedPage = pp
        self.layout()

    def updatePropGrid(self, propDict=None):
        self.PropSheet.updatePropGrid(propDict=propDict)

    def updateLayout(self):
        self._tree.updateDisplay(self.Controller)

    def onToggleTree(self, evt):
        self.mainPager.nextPage()

    def onMainPageChanged(self, evt):
        self.treeBtn.Value = self.mainPager.SelectedPage is self.treePage

    def hideTree(self):
        self.mainPager.SelectedPage = self.propPage

    def onPanelChange(self, evt):
        if evt.expanded:
            pnl = evt.panel
            if pnl is None or len(pnl.Children) < 2:
                return

    def showPropPage(self):
        self.mainPager.SelectedPage = self.propPage
        self.refresh()
        self.propPage.Expanded = True
        self.bringToFront()

    def showTreePage(self):
        self.mainPager.SelectedPage = self.treePage
        self.bringToFront()

    def select(self, obj):
        """Called when the selected object changes. 'obj' will be a single object.
        We then need to update the components of this form appropriately.
        """
        if obj is None:
            lbl = ""
        else:
            lbl = obj.Caption
        self.txtObj.Value = lbl
        self.PropSheet.select(obj)
        self.Tree.select(obj)
        self.refresh()
        self.layout()

    def _getController(self):
        try:
            return self._controller
        except AttributeError:
            self._controller = self
            return self._controller

    def _setController(self, val):
        if self._constructed():
            self._controller = val
        else:
            self._properties["Controller"] = val

    def _getMethodList(self):
        return self._methodList

    def _setMethodList(self, val):
        self._methodList = val

    def _getMethodSheet(self):
        return self._methodSheet

    def _setMethodSheet(self, val):
        self._methodSheet = val

    def _getObjectPropertySheet(self):
        return self._objPropSheet

    def _setObjectPropertySheet(self, val):
        self._objPropSheet = val

    def _getPropSheet(self):
        return self._propSheet

    def _setPropSheet(self, val):
        self._propSheet = val

    def _getTree(self):
        return self._tree

    def _setTree(self, val):
        self._tree = val

    Controller = property(
        _getController,
        _setController,
        None,
        _("Object to which this one reports events  (object (varies))"),
    )

    MethodList = property(
        _getMethodList,
        _setMethodList,
        None,
        _(
            """List control containing all available methods for the
            selected object  (dListControl)"""
        ),
    )

    MethodSheet = property(
        _getMethodSheet,
        _setMethodSheet,
        None,
        _("Reference to the panel containing the MethodList  (MethodSheet)"),
    )

    ObjectPropertySheet = property(
        _getObjectPropertySheet,
        _setObjectPropertySheet,
        None,
        _(
            """Reference to the panel
            containing the ObjectPropertySheet  (ObjectPropertySheet)"""
        ),
    )

    Tree = property(
        _getTree,
        _setTree,
        None,
        _("Reference to the contained object tree  (TreeSheet)"),
    )

    PropSheet = property(
        _getPropSheet,
        _setPropSheet,
        None,
        _("Reference to the contained prop sheet  (PropSheet)"),
    )
