# -*- coding: utf-8 -*-
from .. import ui
from .. import events
from ..dLocalize import _
from ..lib.utils import ustr
from ..ui import dKeys
from .class_designer_components import LayoutPanel
from .class_designer_components import LayoutBasePanel
from .class_designer_components import LayoutSpacerPanel
from .class_designer_components import LayoutSizer
from .class_designer_components import LayoutGridSizer
from .class_designer_components import NoSizerBasePanel
from .drag_handle import DragHandle
from .menu_panel import MenuPanel
from .menu_designer_components import SeparatorPanel
from . import class_designer_menu

from .. import ui
from ..ui import makeProxyProperty
from ..ui import dBorderSizer
from ..ui import dBox
from ..ui import dColumn
from ..ui import dComboBox
from ..ui import dDialog
from ..ui import dForm
from ..ui import dGrid
from ..ui import dGridSizer
from ..ui import dListControl
from ..ui import dPageFrameNoTabs
from ..ui import dPanel
from ..ui import dRadioList
from ..ui import dSizer
from ..ui import dSpinner
from ..ui import dStatusBar
from ..ui import dTextBox
from ..ui import dToolForm
from ..ui import dTreeView
from ..ui.dialogs import Wizard
from ..ui.dialogs import WizardPage


class TreeSheet(dPanel):
    def _initProperties(self):
        self.tree = None
        return super(TreeSheet, self)._initProperties()

    def _constructed(self):
        return hasattr(self, "tree") and isinstance(self.tree, dTreeView)

    def afterInit(self):
        self._slotCaption = _("Empty Sizer Slot")
        self._spacerCaption = _("Spacer")
        self.tree = dTreeView(self, ShowButtons=True)
        plat = self.Application.Platform
        if plat == "Mac":
            self.tree.FontSize -= 3
        elif plat == "Win":
            self.tree.FontSize += 1
        else:
            self.tree.FontSize -= 1

        self.tree.bindEvent(events.TreeSelection, self.onTreeSel)
        self.tree.bindEvent(events.TreeItemContextMenu, self.onTreeContextMenu)
        self.tree.bindEvent(events.MouseLeftDoubleClick, self.onTreeAction)
        self.tree.bindKey("enter", self.onTreeAction)
        self.tree.bindKey("numpad_enter", self.onTreeAction)
        #         self.tree.bindEvent(events.TreeBeginDrag, self.onTreeBeginDrag)
        #         self.tree.bindEvent(events.TreeEndDrag, self.onTreeEndDrag)
        self.Sizer = dSizer("v")
        self.Sizer.append1x(self.tree)
        # Flag for determining if the user or the app is selecting
        self._inAppSelection = False

    def onTreeAction(self, evt):
        self.Form.hideTree()

    #     def onTreeBeginDrag(self, evt):
    #         print "BEGIN DRAG"
    #         print "ALLOWED?",evt._uiEvent.IsAllowed()
    #         print evt.EventData
    #         print evt.selectedCaption
    #
    #
    #     def onTreeEndDrag(self, evt):
    #         print "End DRAG"
    #         print evt.EventData
    #         print evt.selectedCaption

    def onTreeSel(self, evt):
        if self._inAppSelection:
            # Otherwise, this would be infinite recursion
            return
        ui.callAfter(self.Controller.treeSelect)

    def onTreeContextMenu(self, evt):
        evt.stop()
        try:
            obj = self.tree.find(evt.itemID)[0].Object
            # See if there is a context menu for this object
            menu = self.Controller.getTreeContextMenu(obj)
            if menu:
                ui.callAfter(self.showContextMenu, menu)
        except IndexError:
            pass

    def expandAll(self):
        self.tree.expandAll()

    def collapseAll(self):
        self.tree.collapseAll()

    def getSelection(self):
        if self.MultipleSelect:
            nds = self.tree.Selection
            ret = []
            for nd in nds:
                ob = nd.Object
                if ob not in ret:
                    ret.append(ob)
        else:
            ret = self.tree.Selection.Object
        return ret

    def select(self, ctls):
        """Iterate through the nodes, and set their Selected status
        to match if they are in the current selection of controls.
        """
        if self._inAppSelection:
            return
        if not isinstance(ctls, (tuple, list)):
            ctls = [ctls]
        self._inAppSelection = True
        selNodes = [nn for nn in self.tree.nodes if nn.Object in ctls]
        self.tree.Selection = selNodes
        self._inAppSelection = False

    def priorObj(self):
        """Return the next node up from the current selection"""
        ret = None
        nx = self.tree.priorNode()
        if nx is not None:
            ret = nx._object
        return ret

    def nextObj(self):
        """Return the next node down from the current selection"""
        ret = None
        nx = self.tree.nextNode()
        if nx is not None:
            ret = nx._object
        return ret

    def getNodeFor(self, obj):
        """Return the node whose Object property is the passed object."""
        return self.tree.nodeForObject(obj)

    def updateDisplay(self, frm):
        """Constructs the tree for the form's layout."""
        sel = self.tree.Selection
        if sel:
            if self.MultipleSelect:
                selObjs = [nn.Object for nn in sel]
        # Preserve the expand/collapse state if possible.
        expState = [(nn.Object, nn.Expanded) for nn in self.tree.nodes]

        self.tree.clear()
        topObj = frm.getObjectHierarchy()[0][1]
        self.recurseLayout(topObj, None)
        self.tree.expandAll()
        if sel:
            if self.MultipleSelect:
                self.select(selObjs)
            else:
                self.select(sel)
        # Restore the expand/collapse state if possible.
        for obj, expand in expState:
            nn = self.tree.nodeForObject(obj)
            if nn:
                nn.Expanded = expand

    def updateNames(self, frm):
        """Refreshes the object names without changing the layout."""
        sel = self.tree.Selection
        if not isinstance(sel, (list, tuple)):
            sel = (sel,)
        for nd in sel:
            obj = nd.Object
            nd.Caption = self._getDisplayName(obj)

    def _getDisplayName(self, obj):
        """Create the name displayed on the tree for a given object."""
        ret = ustr(obj)
        if isinstance(obj, (dSizer, dBorderSizer, dGridSizer)):
            ornt = obj.Orientation
            if ornt in ("r", "c"):
                ornt = {"r": "Row", "c": "Column"}[ornt]
                ret = _("Grid Sizer")
            else:
                if isinstance(obj, dBorderSizer):
                    itmCap = obj.Caption
                    if itmCap:
                        ret = _("BorderSizer ('%(itmCap)s'): %(ornt)s") % locals()
                    else:
                        ret = _("BorderSizer: %s") % ornt
                else:
                    ret = _("Sizer: %s") % ornt

        elif isinstance(obj, LayoutSpacerPanel):
            ret = self._slotCaption
            if isinstance(obj.ControllingSizer, LayoutGridSizer):
                # Add the row,col info to the caption
                r, c = obj.ControllingSizer.getGridPos(obj)
                ret = "%s r:%s, c:%s" % (self._slotCaption, r, c)
            else:
                ret = "%s - (%s)" % (self._spacerCaption, obj.Spacing)

        elif isinstance(obj, SeparatorPanel):
            return " (Separator) "
        else:
            if hasattr(obj, "TreeDisplayCaption"):
                dsp = obj.TreeDisplayCaption
                if isinstance(dsp[1], type):
                    dsp = (dsp[0], self._getClassName(dsp[1]))
            elif isinstance(obj, dColumn):
                dsp = "Column", obj.DataField
            elif isinstance(obj, Wizard):
                dsp = "Wizard", obj.Caption
            elif hasattr(obj, "Name"):
                dsp = (obj.Name, self._getClassName(obj._baseClass))
            else:
                dsp = ("", self._getClassName(obj.__class__))
            try:
                if isinstance(obj.ControllingSizer, LayoutGridSizer):
                    r, c = obj.ControllingSizer.getGridPos(obj)
                    dsp = ("%s r:%s, c:%s" % (dsp[0], r, c), dsp[1])
            except:
                pass
            ret = "%s (%s)" % dsp
        return ret

    def _getClassName(self, cls):
        """Takes a string representation of the form:
            <class 'ui.dTextBox.dTextBox'>
        and returns just the actual class name (i.e., in this
        case, 'dTextBox').
        """
        ret = ustr(cls)
        if ret.startswith("<class 'dabo."):
            # Just include the class name
            ret = ret.split("'")[1].split(".")[-1]
        return ret

    def onTreeItemContextMenu(self, evt):
        print(evt.itemID)

    def recurseLayout(self, itm, node, noDisplay=False, sz=None):
        ## Is this good to do? Or am I masking problems?
        if itm is None:
            return

        if isinstance(itm, (dSizer, dBorderSizer, dGridSizer)):
            if isinstance(itm.Parent, self.Controller.getFormClass()):
                noDisplay = True
            if noDisplay:
                childNode = node
            else:
                cap = self._getDisplayName(itm)
                childNode = node.appendChild(cap)
                childNode.Object = itm
            if isinstance(itm, dGridSizer):
                # Grid Sizer children are in the order they are added;
                # instead, get items into r,c order
                kids = [
                    itm.getItemByRowCol(rr, cc, False)
                    for rr in range(itm._rows)
                    for cc in range(itm._cols)
                ]
            else:
                kids = itm.Children
            for kid in kids:
                self.recurseLayout(kid, childNode, noDisplay=noDisplay, sz=itm)

        elif isinstance(itm, (dSizer.SizerItem, dSizer.GridSizerItem)):
            if itm.IsWindow():
                recurse = True
                noDisplay = False
                win = itm.GetWindow()

                if isinstance(win, LayoutSpacerPanel):
                    cap = self._getDisplayName(win)
                    childNode = node.appendChild(cap)
                    childNode.Object = win

                elif isinstance(win, LayoutPanel):
                    cap = self._getDisplayName(win)
                    sz = win.Sizer
                    if sz is None or not isinstance(sz, LayoutSizer):
                        # Empty slot; display it in the tree.
                        childNode = node.appendChild(cap)
                        childNode.Object = win
                        recurse = False
                    if isinstance(sz, LayoutSizer) and sz.SlotCount == 0:
                        # Empty slot; display it in the tree.
                        childNode = node.appendChild(cap)
                        childNode.Object = win
                    else:
                        childNode = node
                    if hasattr(win, "_hideInTree"):
                        noDisplay = win._hideInTree
                elif isinstance(win, LayoutBasePanel):
                    childNode = node
                    noDisplay = True
                else:
                    # A non-ClassDesigner control
                    childNode = node
                if recurse:
                    self.recurseLayout(win, childNode, noDisplay=noDisplay)

            elif itm.IsSizer():
                sz = itm.GetSizer()
                childNode = node
                self.recurseLayout(sz, childNode)
        else:
            # Not a sizer; see if it an empty slot, an actual control,
            # a sub-sizer, the form's Status Bar, or some other child
            # form such as the PropSheet.
            if isinstance(itm, (dStatusBar, ui.nativeScrollBar, DragHandle)):
                # ignore
                return
            elif isinstance(itm, (dForm, dToolForm, dDialog)) and node:  # is not None:
                # This is a child form; ignore it
                return
            elif itm.__module__.startswith("wx"):
                # A native wx control; skip it
                return
            elif isinstance(itm, LayoutPanel) and not isinstance(itm.Parent, WizardPage):
                return
            elif isinstance(itm, NoSizerBasePanel):
                self._recurseChildren(itm.Children, node, noDisplay=False)

            elif isinstance(itm, LayoutBasePanel):
                return self.recurseLayout(itm.Sizer, node, noDisplay=False)

            cap = self._getDisplayName(itm)
            if hasattr(itm, "_hideInTree"):
                if itm._hideInTree:
                    # Don't continue to drill into object
                    return
            if noDisplay:
                childNode = node
            else:
                if node is None:
                    self.tree.clear()
                    childNode = self.tree.setRootNode(cap)
                else:
                    childNode = node.appendChild(cap)
                childNode.Object = itm

            if not isinstance(itm, (SeparatorPanel, MenuPanel)):
                if hasattr(itm, "Sizer") and itm.Sizer:
                    if isinstance(itm, WizardPage):
                        self._recurseChildren(itm.Children, childNode, noDisplay)
                        return
                    if not isinstance(
                        itm,
                        (dPageFrameNoTabs, dRadioList, dSpinner, Wizard, WizardPage),
                    ):
                        self.recurseLayout(itm.Sizer, childNode, noDisplay=noDisplay)
            if isinstance(itm, dGrid):
                children = itm.Columns
            elif isinstance(itm, dTreeView):
                # Can change this to BaseNode property post-0.7
                children = itm.BaseNodes
            elif isinstance(itm, (dComboBox, dSpinner, dListControl, dRadioList)):
                # These compound controls don't need their parts listed
                children = None
            elif isinstance(itm, SeparatorPanel):
                children = None
            else:
                try:
                    children = itm.Children
                except:
                    children = None
            if children:
                self._recurseChildren(children, childNode, noDisplay)

    def _recurseChildren(self, children, childNode, noDisplay):
        for chil in children:
            if chil is self:
                continue
            # BorderSizers add dBox instances to the parent object. They
            # mark these with a '_belongsToBorderSizer' property. We
            # want to skip them here.
            if isinstance(chil, dBox):
                if hasattr(chil, "_belongsToBorderSizer"):
                    # Skip it
                    continue
            # See if it has already been added via recursive calls
            chilNode = self.getNodeFor(chil)
            if chilNode is None:
                # Child item wasn't already listed by the sizer
                noDisplay = False
                self.recurseLayout(chil, childNode, noDisplay=noDisplay)

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

    #     def _getMultipleSelect(self):
    #         try:
    #             ret = self._multipleSelect
    #         except AttributeError:
    #             ret = self._multipleSelect = True
    #         return ret
    #
    #     def _setMultipleSelect(self, val):
    #         if self._constructed():
    #             self._multipleSelect = val
    #             try:
    #                 self.tree.MultipleSelect = val
    #             except AttributeError:
    #                 # tree isn't constructed yet
    #                 ui.setAfter(self.tree, "MultipleSelect", val)
    #         else:
    #             self._properties["MultipleSelect"] = val

    Controller = property(
        _getController,
        _setController,
        None,
        _("Object to which this one reports events  (object (varies))"),
    )

    #     MultipleSelect = property(_getMultipleSelect, _setMultipleSelect, None,
    #             _("Determines if the tree supports multiple selection  (bool)"))

    _proxyDict = {}
    MultipleSelect = makeProxyProperty(
        _proxyDict,
        "MultipleSelect",
        "tree",
    )
