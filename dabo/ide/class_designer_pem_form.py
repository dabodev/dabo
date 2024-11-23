# -*- coding: utf-8 -*-

from .. import ui
from ..dLocalize import _
from ..lib.utils import ustr
from .. import events
from .class_designer_prop_sheet import PropSheet
from .class_designer_tree_sheet import TreeSheet
from .class_designer_method_sheet import MethodSheet
from .class_designer_object_property_sheet import ObjectPropertySheet
from .class_designer_components import LayoutPanel
from .class_designer_components import LayoutSpacerPanel
from .class_designer_components import LayoutSizer
from .class_designer_components import LayoutGridSizer
from . import class_designer_menu

from ..ui import dBorderSizer
from ..ui import dColumn
from ..ui import dForm
from ..ui import dPageFrameNoTabs
from ..ui import dPanel
from ..ui import dSizer
from ..ui import dSizerMixin
from ..ui import dSlidePanel
from ..ui import dSlidePanelControl
from ..ui import dTextBox
from ..ui import dToggleButton
from ..ui import dTreeView


class PemForm(dForm):
    """This form contains the PropSheet, the MethodSheet, and
    the Object Tree.
    """

    def afterSetMenuBar(self):
        self.ShowStatusBar = False
        class_designer_menu.mkDesignerMenu(self)

    def onMenuOpen(self, evt):
        self.Controller.menuUpdate(evt, self.MenuBar)

    def afterInit(self):
        self._defaultLeft = 610
        self._defaultTop = 50
        self._defaultWidth = 370
        self._defaultHeight = 580

        self.Caption = _("Object Info")
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
        self.pemPage = pp = mp.Pages[0]
        self.treePage = tp = mp.Pages[1]
        psz = pp.Sizer = dSizer("v")
        tsz = tp.Sizer = dSizer("v")

        dSlidePanelControl(
            pp,
            SingleClick=True,
            Singleton=True,
            CollapseToBottom=True,
            RegID="mainContainer",
        )
        psz.append1x(self.mainContainer)
        # This helps restore the sash position on the prop grid page
        self._propSashPct = 80
        # Bind to panel changes
        self.mainContainer.bindEvent(events.SlidePanelChange, self.onPanelChange)
        dSlidePanel(
            self.mainContainer,
            Caption=_("Properties"),
            RegID="propPage",
            CaptionForeColor="blue",
        )
        dSlidePanel(
            self.mainContainer,
            Caption=_("Methods"),
            RegID="methodPage",
            CaptionForeColor="blue",
        )
        dSlidePanel(
            self.mainContainer,
            Caption=_("Custom Properties"),
            RegID="objPropPage",
            CaptionForeColor="blue",
        )

        # Add the PropSheet
        ps = PropSheet(self.propPage, RegID="_propSheet")
        self.propPage.Sizer = dSizer("v")
        self.propPage.Sizer.appendSpacer(self.propPage.CaptionHeight)
        self.propPage.Sizer.append1x(ps)

        # Create the MethodSheet
        ms = MethodSheet(self.methodPage, RegID="_methodSheet")
        self.methodPage.Sizer = dSizer("v")
        self.methodPage.Sizer.appendSpacer(self.methodPage.CaptionHeight)
        self.methodPage.Sizer.append1x(ms)
        self._methodList = ms.MethodList

        # Create the tree
        self._tree = TreeSheet(tp)
        tp.Sizer.append1x(self._tree, border=10)

        # Create the Object Properties sheet
        ops = ObjectPropertySheet(self.objPropPage, RegID="_objPropSheet")
        self.objPropPage.Sizer = dSizer("v")
        self.objPropPage.Sizer.appendSpacer(self.methodPage.CaptionHeight)
        self.objPropPage.Sizer.append1x(ops)

        mp.SelectedPage = pp

        ps.Controller = ms.Controller = self._tree.Controller = ops.Controller = self.Controller
        self.layout()
        ui.callAfter(self.mainContainer.expand, self.propPage)

    def onToggleTree(self, evt):
        self.mainPager.nextPage()

    def onMainPageChanged(self, evt):
        self.treeBtn.Value = self.mainPager.SelectedPage is self.treePage

    def hideTree(self):
        self.mainPager.SelectedPage = self.pemPage

    def onPanelChange(self, evt):
        if evt.panel is self.propPage:
            try:
                if evt.expanded:
                    ui.setAfter(
                        self._propSheet.mainSplit,
                        "SashPercent",
                        self._propSheet._sashPct,
                    )
            except:
                # Probably isn't constructed yet
                pass

    def onResize(self, evt):
        try:
            ui.callAfter(self.mainContainer.refresh)
        except:
            # 'mainContainer' might not be defined yet, so ignore
            pass

    def showPropPage(self):
        self.mainPager.SelectedPage = self.pemPage
        self.refresh()
        self.propPage.Expanded = True
        self.bringToFront()

    def showTreePage(self):
        self.mainPager.SelectedPage = self.treePage
        self.bringToFront()

    def showMethodsPage(self):
        self.mainPager.SelectedPage = self.pemPage
        self.methodPage.Expanded = True
        self.bringToFront()

    def select(self, obj):
        """Called when the selected object changes. 'obj' will
        be a list containing either a single object or multiple
        objects. We then need to update the components of this
        form appropriately.
        """
        mult = len(obj) > 1
        if len(obj) == 0:
            lbl = _(" -none- ")
            ob = None
        else:
            ob = obj[0]
            # If the selected object is an empty sizer slot, the way that this
            # is passed along is a tuple containing the sizer item and its sizer,
            # since there is no way to determine the sizer given the SizerItem.
            isSpacer = isinstance(ob, LayoutSpacerPanel)
            isSlot = isinstance(ob, LayoutPanel) and not isSpacer
            isSizer = isinstance(ob, dSizerMixin)
            isColumn = isinstance(ob, dColumn)
            isNode = isinstance(ob, dTreeView.getBaseNodeClass())
            if isSlot or isSpacer:
                szItem = ob.ControllingSizerItem
                sz = ob.ControllingSizer
            if isSizer:
                sz = ob
            obRest = obj[1:]
            # Determine the 'name' to display
            if mult:
                lbl = _(" -multiple- ")
            else:
                if isSlot or isSizer:
                    ornt = sz.Orientation[0].lower()
                    if ornt == "h":
                        lbl = _("Horizontal")
                    elif ornt == "v":
                        lbl = _("Vertical")
                    else:
                        lbl = _("Grid")
                    if isSlot:
                        lbl += _(" Sizer Slot")
                        if ornt in ("r", "c"):
                            lbl += ": (%s, %s)" % sz.getGridPos(ob)
                    else:
                        if isinstance(ob, dBorderSizer):
                            lbl += _(" BorderSizer")
                        else:
                            lbl += _(" Sizer")
                elif isSpacer:
                    spc = ob.Spacing
                    if isinstance(sz, dSizer):
                        # We want the first position for vertical; second for horiz.
                        isHoriz = sz.Orientation[0].lower() == "h"
                        typ = (_("Vertical"), _("Horizontal"))[isHoriz]
                    else:
                        # Grid spacer; use both
                        typ = _("Grid")
                    lbl = "%s Spacer - (%s)" % (typ, spc)
                elif isColumn:
                    if ob.Visible:
                        lbl = "Column %s ('%s')" % (
                            ob.Parent.Columns.index(ob) + 1,
                            ob.Caption,
                        )
                    else:
                        lbl = "Hidden Column ('%s')" % ob.Caption
                elif isNode:
                    lbl = "TreeNode: ('%s')" % (ob.Caption)
                else:
                    if hasattr(ob, "Name"):
                        lbl = ob.Name
                    else:
                        lbl = ustr(ob.__class__)
        self.txtObj.Value = lbl
        self.PropSheet.select(obj)
        self.MethodList.clear()
        self._objPropSheet.select(obj)

        if ob is not None:
            # Get the events
            evts = ob.DesignerEvents
            # Get the dict of all events that have method code defined for them.
            obEvtCode = self.Controller.getCodeForObject(ob)
            codeEvents = nonCodeEvents = []
            if obEvtCode is not None:
                codeEvents = list(obEvtCode.keys())
                codeEvents.sort()
            nonCodeEvents = [ev for ev in evts if ev not in codeEvents]
            nonCodeEvents.sort()
            # Add the events with code first
            for evt in codeEvents:
                newItem = self.MethodList.append(evt)
                self.MethodList.setItemBackColor(newItem, "lightblue")

            for evt in nonCodeEvents:
                newItem = self.MethodList.append(evt)
                self.MethodList.setItemBackColor(newItem, "lightgrey")
        self.refresh()
        self.layout()

    def _getController(self):
        try:
            return self._controller
        except AttributeError:
            self._controller = self.Application
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
