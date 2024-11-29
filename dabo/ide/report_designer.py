#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import copy
from .. import icons
from .. import ui
from ..application import dApp
from .. import events
from ..dReportWriter import dReportWriter
from ..lib.reportWriter import *
from ..dLocalize import _
from ..lib.utils import ustr
from . import class_designer_prop_sheet

from ..ui import dEditor
from ..ui import dFont
from ..ui import dForm
from ..ui import dImage
from ..ui import dKeys
from ..ui import dLabel
from ..ui import dMenu
from ..ui import dPageFrame
from ..ui import dPageFrame
from ..ui import dPanel
from ..ui import dScrollPanel
from ..ui import dTreeView

NEW_FILE_CAPTION = "< New >"
SHORTEN_EXPRESSIONS_FOR_DISPLAY = False

rdc = None

iconPath = os.path.dirname(icons.__file__)  # + r'/themes/tango/16x16'


def DesignerController():
    # Wrapper function to enforce singleton class instance
    class DesignerController(dApp):
        def initProperties(self):
            self.BasePrefKey = "dabo.ide.reportdesigner"
            self.setAppInfo("appName", "Dabo Report Designer")
            self.MainFormClass = None

        def beforeInit(self):
            self._inSelection = False

        def afterInit(self):
            if sys.platform == "darwin":
                self.bindEvent(events.KeyDown, self._onKeyDown)

        def startPropEdit(self):
            ## Class Designer uses this; don't think it's necessary here.
            pass

        def endPropEdit(self):
            ## Class Designer uses this; don't think it's necessary here.
            pass

        def _onKeyDown(self, evt):
            # Mac-specific behavior
            self.ActiveEditor.onKeyDown(evt)

        def onFileExit(self, evt):
            ret = self.ActiveEditor.closeFile()
            if ret is not None:
                self.finish()

        def getShortExpr(self, expr):
            """Given an expression, return a shortened version for display in designer."""
            if not SHORTEN_EXPRESSIONS_FOR_DISPLAY:
                expr = expr.strip()
                if len(expr) > 1 and expr[0] == expr[-1] and expr[0] in ("'", '"'):
                    expr = expr[1:-1]
                return expr
            if expr is None:
                return "None"
            if len(expr) < 3:
                return expr

            def isVariable(name):
                for v in rdc.ReportForm["Variables"]:
                    if v.get("Name", None) == name:
                        return True
                return False

            def isRecord(name):
                if (
                    name
                    and ("TestCursor" in rdc.ReportForm)
                    and rdc.ReportForm["TestCursor"]
                    and (name in rdc.ReportForm["TestCursor"][0])
                ):
                    return True
                return False

            import re

            c = re.compile("self.(?P<type>Record|Variables)\[(?P<name>.*)\]")
            m = c.match(expr)
            if m:
                name = m.group("name")
                name = name[1:-1]  ## (remove outer quotes)
            else:
                if "." in expr:
                    name = expr.split(".")[-1]
                else:
                    # No record or variable found: leave alone
                    name = None

            if not isVariable(name) and not isRecord(name):
                # This isn't a record or variable: don't shortcut the name as a
                # visual cue to the developer.
                name = None

            if name is None:
                quotes = ('"', "'")
                if expr[0] in quotes and expr[-1] in quotes:
                    # Remove outer quotes
                    name = expr[1:-1]
                else:
                    for quote in quotes:
                        if expr.count(quote) >= 2:
                            name_candidate = expr[expr.find(quote) + 1 :]
                            name_candidate = name_candidate[: name_candidate.find(quote)]
                            if name_candidate.strip():
                                name = name_candidate
                            break
            if name:
                expr = name
            return expr

        def objectDoubleClicked(self, obj, evt=None):
            """A report object was double-clicked: edit its major property in the propsheet."""
            editProp = obj.MajorProperty
            if evt.EventData["shiftDown"]:
                editProp = None
            rdc.editProperty(editProp)

        def editProperty(self, prop=None):
            """Display the property dialog, and bring it to top.

            If a valid propname is passed, start the editor for that property.
            After the property is edited, send focus back to the designer or
            object tree.
            """
            activeForm = self.ActiveForm
            self.showPropSheet(bringToTop=True, prop=prop, enableEditor=True, focusBack=activeForm)

        def newObject(self, typ, mousePosition):
            """Add a new object of the passed type to the selected band."""
            rf = self.ReportForm
            parents = []
            objects = []

            defaultProps = {}

            if typ == Variable:
                parents.append(rf["Variables"])
            elif typ == Group:
                parents.append(rf["Groups"])
            else:
                # Normal report object. Place it in all selected bands.
                if isinstance(typ, str):
                    if typ[:7] == "Field: ":
                        # Testcursor field. Create string object with expr of this field.
                        defaultProps["expr"] = "self.%s" % typ[7:].strip()
                        typ = String
                    elif typ[:10] == "Variable: ":
                        # Report Variable: Create string object with expr of this variable.
                        defaultProps["expr"] = "self.%s" % typ[10:].strip()
                        typ = String

                ## Want to put the object where the mouse was, however there are things to
                ## consider such as zoom factor, and that the mouse position is absolute
                ## screen position. Also, we only want to do this if we were dealing with the
                ## context menu from the designer, as opposed to the one in the object tree.
                #                defaultProps["x"] = "%s" % mousePosition[0]
                #                defaultProps["y"] = "%s" % mousePosition[1]

                for selObj in self.SelectedObjects:
                    if isinstance(selObj, Band):
                        parents.append(selObj)

            for parent in parents:
                obj = parent.addObject(typ)
                obj.update(defaultProps.copy())
                objects.append(obj)

            if objects:
                self.SelectedObjects = objects

            dabo.ui.callAfter(self.ActiveEditor.Form.Raise)

        def getGroupBandByExpr(self, expr):
            for g in self.ReportForm["Groups"]:
                if g["expr"] == expr:
                    return g
            return None

        def getContextMenu(self, mousePosition):
            def onNewObject(evt):
                """Called from the context menu."""
                tag = evt.EventObject.Tag
                self.newObject(tag, mousePosition)

            def onSelectAll(evt):
                self.selectAllObjects()

            def onCopy(evt):
                self.copy()

            def onPaste(evt):
                self.paste()

            def onCut(evt):
                self.cut()

            def onDelete(evt):
                self.delete()

            def onMoveToTop(evt):
                self.ActiveEditor.sendToBack()

            def onMoveUp(evt):
                self.ActiveEditor.sendBackwards()

            def onMoveDown(evt):
                self.ActiveEditor.sendUpwards()

            def onMoveToBottom(evt):
                self.ActiveEditor.bringToFront()

            menu = dMenu()
            newObjectMenuCreated = False
            newVariableMenuCreated = False
            newGroupMenuCreated = False
            variableSelected, groupSelected = False, False

            for robj in self.SelectedObjects:
                if isinstance(robj, Variable):
                    variableSelected = True
                if isinstance(robj, Group):
                    groupSelected = True
                if not newVariableMenuCreated and isinstance(robj, (Variables, Variable)):
                    menu.append("New variable", OnHit=onNewObject, Tag=Variable)
                    newVariableMenuCreated = True
                if not newGroupMenuCreated and isinstance(robj, (Groups, Group)):
                    menu.append("New group", OnHit=onNewObject, Tag=Group)
                    newGroupMenuCreated = True
                if not newObjectMenuCreated and isinstance(robj, Band):
                    newObjectMenuCreated = True
                    objectChoices = dMenu(Caption="New object")
                    for choice in (Image, Line, Rectangle, String, Memo):
                        objectChoices.append(choice.__name__, OnHit=onNewObject, Tag=choice)
                    objectChoices.appendSeparator()
                    for choice in (SpanningLine, SpanningRectangle):
                        objectChoices.append(choice.__name__, OnHit=onNewObject, Tag=choice)
                    tc = self.ReportForm.get("TestCursor", [])
                    var = self.ReportForm.get("Variables", [])
                    if tc or var:
                        objectChoices.appendSeparator()

                    for typ, cap in ((tc, "Field"), (var, "Variable")):
                        if typ:
                            submenu = dMenu(Caption=cap)
                            fields = []
                            if typ == tc:
                                if tc:
                                    fields = list(tc[0].keys())
                            elif typ == var:
                                for v in var:
                                    try:
                                        fields.append(v["Name"])
                                    except KeyError:
                                        # variable not given a name
                                        pass
                            fields.sort()
                            for field in fields:
                                submenu.append(
                                    field,
                                    OnHit=onNewObject,
                                    Tag="%s: %s" % (cap, field),
                                )
                            objectChoices.appendMenu(submenu)
                    menu.appendMenu(objectChoices)

            if len(menu.Children) > 0:
                menu.appendSeparator()

            menu.append(_("Select All"), HotKey="Ctrl+A", OnHit=onSelectAll)
            menu.appendSeparator()
            menu.append(_("Copy"), HotKey="Ctrl+C", OnHit=onCopy)
            menu.append(_("Cut"), HotKey="Ctrl+X", OnHit=onCut)
            menu.append(_("Paste"), HotKey="Ctrl+V", OnHit=onPaste)
            menu.appendSeparator()
            menu.append(_("Delete"), HotKey="Del", OnHit=onDelete)

            if variableSelected or groupSelected:
                menu.appendSeparator()
                menu.append(_("Move to top"), HotKey="Ctrl+Shift+H", OnHit=onMoveToTop)
                menu.append(_("Move up"), HotKey="Ctrl+H", OnHit=onMoveUp)
                menu.append(_("Move down"), HotKey="Ctrl+J", OnHit=onMoveDown)
                menu.append(_("Move to bottom"), HotKey="Ctrl+Shift+J", OnHit=onMoveToBottom)

            return menu

        def selectAllObjects(self):
            """Select all objects in the selected band(s)."""
            selection = []
            for band in self.getSelectedBands():
                for obj in band["Objects"]:
                    selection.append(obj)
            self.SelectedObjects = selection

        def showObjectTree(self, bringToTop=False, refresh=False):
            ot = self.ObjectTree
            if ot is None:
                refresh = True
                ot = self.loadObjectTree()
                self.refreshTree()

            ot.Form.Visible = True
            if refresh:
                ot.refreshSelection()
            if bringToTop:
                ot.Raise()

        def hideObjectTree(self):
            ot = self.ObjectTree
            if ot is not None and ot.Form.Visible:
                ot.Form.Visible = False

        def loadObjectTree(self):
            otf = ObjectTreeForm()
            ot = self.ObjectTree = otf.Editor
            otf.bindEvent(events.Close, self._onObjectTreeFormClose)
            # Allow the activate to fire so that position is set:
            otf.Visible = True
            otf.Raise()
            self.ActiveEditor.Form.Raise()
            return ot

        def showPropSheet(
            self,
            bringToTop=False,
            refresh=False,
            prop=None,
            enableEditor=False,
            focusBack=None,
        ):
            ps = self.PropSheet
            if ps is None:
                refresh = True
                ps = self.loadPropSheet()
            ps.Form.Visible = True

            if refresh:
                ps.refreshSelection()

            pg = ps.propGrid
            ds = pg.DataSet

            if enableEditor:
                # Select the value column and enable the editor for the prop. Note:
                # This needs to be done before changing rows, for some reason, or the
                # editor column isn't activated.
                pg.CurrentColumn = 1

            pg._focusBack = focusBack
            if prop:
                # Put the propsheet on the row for the passed prop.
                for idx, record in enumerate(ds):
                    if record["prop"].lower() == prop.lower():
                        pg.CurrentRow = idx
                        break
            else:
                pg.CurrentRow = pg.CurrentRow
            if bringToTop:
                ps.Form.Raise()

        def hidePropSheet(self):
            ps = self.PropSheet
            if ps is not None and ps.Form.Visible:
                ps.Form.Visible = False

        def loadPropSheet(self):
            psf = PropSheetForm()
            ps = self.PropSheet = psf.Editor
            psf.bindEvent(events.Close, self._onPropSheetFormClose)
            psf.Visible = True
            psf.Raise()
            self.ActiveEditor.Form.Raise()
            return ps

        def refreshTree(self):
            if self.ObjectTree:
                self.ObjectTree.refreshTree()
                self.ObjectTree.refreshSelection()

        def refreshProps(self, refreshEditor=True):
            if refreshEditor and self.ActiveEditor:
                self.ActiveEditor.refresh()
            if self.PropSheet and self.PropSheet.Form.Visible:
                self.PropSheet.refreshSelection()

        def refreshSelection(self, refreshEditor=False):
            self._inSelection = True
            for obj in (self.PropSheet, self.ObjectTree):
                if obj is not None:
                    obj.refreshSelection()
            if refreshEditor:
                self.ActiveEditor.refresh()
            self._inSelection = False

        def isSelected(self, obj):
            """Return True if the object is selected."""
            for selObj in self.SelectedObjects:
                if id(selObj) == id(obj):
                    return True
            return False

        def getNextDrawable(self, obj):
            """Return the next drawable after the passed obj."""
            collection = self.getParentBand(obj)["Objects"]
            idx = collection.index(obj) + 1
            if len(collection) <= idx:
                idx = 0
            return collection[idx]

        def getPriorDrawable(self, obj):
            """Return the prior drawable before the passed obj."""
            collection = self.getParentBand(obj)["Objects"]
            idx = collection.index(obj) - 1
            if len(collection) <= idx:
                idx = len(collection) - 1
            return collection[idx]

        def ReportObjectSelection(self):
            import pickle
            import wx

            rw = self.ActiveEditor._rw

            class ReportObjectSelection(wx.CustomDataObject):
                def __init__(self):
                    # wx.CustomDataObject.__init__(self, wx.CustomDataFormat("ReportObjectSelection"))
                    # self.SetFormat(wx.DataFormat("my data format"))
                    wx.CustomDataObject.__init__(self, wx.DataFormat("ReportObjectSelection"))
                    self.setObject([])

                def setObject(self, objs):
                    # We are receiving a sequence of selected objects. Convert to a list of
                    # new dicts representing the object properties.
                    copyObjs = []
                    for obj in objs:
                        copyObj = obj.getMemento()
                        if obj.__class__.__name__ == "Group":
                            parentBandInfo = ["Groups", None]
                        elif obj.__class__.__name__ == "Variable":
                            parentBandInfo = ["Variables", None]
                        else:
                            parentBand = rdc.getParentBand(obj)
                            parentBandInfo = [
                                ustr(type(parentBand)).split(".")[-1][:-2],
                                None,
                            ]
                            if "Group" in parentBandInfo[0]:
                                group = parentBand.parent
                                parentBandInfo[1] = group.get("expr")
                        copyObj["_parentBandInfo_"] = parentBandInfo
                        copyObjs.append(copyObj)
                    self.SetData(pickle.dumps(copyObjs))

                def getObject(self):
                    # We need to convert the representative object dicts back into report
                    # objects
                    copyObjs = pickle.loads(self.GetData())
                    objs = []
                    for copyObj in copyObjs:
                        obj = self.getReportObjectFromMemento(copyObj)
                        objs.append(obj)
                    return objs

                def getReportObjectFromMemento(self, memento, parent=None):
                    try:
                        parentInfo = memento.pop("_parentBandInfo_")
                    except KeyError:
                        parentInfo = None

                    if parentInfo:
                        if parentInfo[0] == "Groups":
                            parent = rdc.ReportForm["Groups"]
                        elif parentInfo[0] == "Variables":
                            parent = rdc.ReportForm["Variables"]
                        elif "Group" in parentInfo[0]:
                            parent = rdc.getGroupBandByExpr(parentInfo[1])[parentInfo[0]]
                        else:
                            parent = rdc.ReportForm[parentInfo[0]]
                    obj = rw._getReportObject(memento["type"], parent)
                    del memento["type"]
                    for k, v in list(memento.items()):
                        if isinstance(v, dict):
                            obj[k] = self.getReportObjectFromMemento(v, obj)
                        elif isinstance(v, list):
                            obj[k] = rw._getReportObject(k, obj)
                            for c in v:
                                obj[k].append(self.getReportObjectFromMemento(c, obj))
                        else:
                            obj[k] = v
                    return obj

            return ReportObjectSelection()

        def getSelectedBands(self):
            """Return the list of bands that are currently selected."""
            selBands = []
            for selObj in self.SelectedObjects:
                if (
                    not isinstance(selObj, Band)
                    and selObj.parent is not None
                    and isinstance(selObj.parent.parent, Band)
                ):
                    selObj = selObj.parent.parent
                if isinstance(selObj, Band):
                    if selObj not in selBands:
                        selBands.append(selObj)
            return selBands

        def copy(self, cut=False):
            import wx

            do = self.ReportObjectSelection()
            copyObjs = [
                selObj
                for selObj in self.SelectedObjects
                if not isinstance(selObj, (Report, Band, list))
            ]
            if not copyObjs:
                # don't override the current clipboard with an empty clipboard
                return
            do.setObject(copyObjs)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(do)
                wx.TheClipboard.Close()
            if cut:
                self.delete()

        def delete(self):
            objs = [
                obj for obj in self.SelectedObjects if not isinstance(obj, (Report, Band, list))
            ]
            if not objs:
                return
            parent = None
            reInit = False
            for obj in objs:
                parent = obj.parent
                removeNode = False
                if isinstance(parent, dict):
                    for typ in ("Objects", "Variables", "Groups"):
                        if typ in parent:
                            if obj in parent[typ]:
                                parent[typ].remove(obj)
                                removeNode = True
                elif isinstance(parent, list):
                    parent.remove(obj)
                    removeNode = True
                if removeNode:
                    ot = self.ObjectTree
                    if ot:
                        nd = ot.removeNode(ot.nodeForObject(obj))
                    if isinstance(obj, Group):
                        reInit = True
            self.ActiveEditor.propsChanged(reinit=reInit)

        def cut(self):
            self.copy(cut=True)

        def paste(self):
            import wx

            success = False
            do = self.ReportObjectSelection()
            if wx.TheClipboard.Open():
                success = wx.TheClipboard.GetData(do)
                wx.TheClipboard.Close()

            if success:
                objs = do.getObject()
            else:
                # nothing valid in the clipboard
                return

            # Figure out the band to paste the obj(s) into. If the objects are from multiple
            # bands, then paste the new objects into the same bands. If the objects are all
            # from the same band, paste the new objects into the currently-selected band.
            parents = []
            selBand = None
            for obj in objs:
                if obj.parent not in parents:
                    parents.append(obj.parent)

            if len(parents) > 1:
                # keep pasted objects in the same parents
                pass
            else:
                selBands = self.getSelectedBands()

                if len(selBands) > 0:
                    # paste into the first selected band
                    selBand = selBands[-1]
                else:
                    if len(self.SelectedObjects) > 0:
                        # paste into the parent band of the first selected object:
                        selBand = self.getParentBand(self.SelectedObjects[-1])

            reInit = False
            selectedObjects = []
            max_y_needed = 0  # resize band if needed to show any objects
            for obj in objs:
                if isinstance(obj, Variable):
                    # paste into Variables whether or not Variables selected
                    pfObjects = self.ReportForm.setdefault("Variables", Variables(self.ReportForm))
                    obj.parent = pfObjects
                elif isinstance(obj, Group):
                    # paste into Groups whether or not Groups selected
                    pfObjects = self.ReportForm.setdefault("Groups", Groups(self.ReportForm))
                    obj.parent = pfObjects
                    reInit = True
                else:
                    if selBand is not None:
                        max_y_needed = max(max_y_needed, obj.getTopPt())
                        pfObjects = selBand.setdefault("Objects", [])
                        obj.parent = selBand
                    else:
                        pfObjects = obj.parent.setdefault("Objects", [])
                pfObjects.append(obj)
                selectedObjects.append(obj)

            if selBand and selBand.getProp("Height") is not None:
                # Resize the pasted-into band to accomodate the new object, if necessary:
                selBand.setProp("Height", ustr(max(selBand.getProp("Height"), max_y_needed)))

            self.ActiveEditor.propsChanged(reinit=reInit)
            self.SelectedObjects = selectedObjects

        def getParentBand(self, obj):
            """Return the band that the obj is a member of."""
            parent = obj
            while parent is not None:
                if isinstance(parent, Band):
                    return parent
                parent = parent.parent
            return None

        def _onObjectTreeFormClose(self, evt):
            self.ObjectTree = None

        def _onPropSheetFormClose(self, evt):
            self.PropSheet = None

        def _getActiveEditor(self):
            return getattr(self, "_activeEditor", None)

        def _setActiveEditor(self, val):
            changed = val != self.ActiveEditor
            if changed:
                self._activeEditor = val
                self.refreshTree()
                self.refreshProps()

        def _getObjectTree(self):
            try:
                val = self._objectTree
            except AttributeError:
                val = self._objectTree = None
            return val

        def _setObjectTree(self, val):
            self._objectTree = val

        def _getPropSheet(self):
            try:
                val = self._propSheet
            except AttributeError:
                val = self._propSheet = None
            return val

        def _setPropSheet(self, val):
            self._propSheet = val

        def _getReportForm(self):
            return self.ActiveEditor.ReportForm

        def _getSelectedObjects(self):
            return getattr(self.ActiveEditor, "_selectedObjects", [])

        def _setSelectedObjects(self, val):
            self.ActiveEditor._selectedObjects = val
            self.refreshSelection(refreshEditor=True)

        ActiveEditor = property(_getActiveEditor, _setActiveEditor)
        ObjectTree = property(_getObjectTree, _setObjectTree)
        PropSheet = property(_getPropSheet, _setPropSheet)
        ReportForm = property(_getReportForm)
        SelectedObjects = property(_getSelectedObjects, _setSelectedObjects)
        Selection = SelectedObjects  ## compatability with ClassDesignerPropSheet

    global rdc
    if rdc is None:
        rdc = DesignerController()
    return rdc


# All the classes below will use the singleton DesignerController instance:
rdc = DesignerController()


class DesignerControllerForm(dForm):
    def initProperties(self):
        self.Caption = "DesignerController Form"
        self.TinyTitleBar = True
        self.ShowMaxButton = False
        self.ShowStatusBar = False
        self.ShowMinButton = False
        self.ShowSystemMenu = False
        self.ShowInTaskBar = False
        self.ShowMenuBar = False

    def afterInit(self):
        sz = self.Sizer
        sz.Orientation = "h"

        self.Editor = self.addObject(self.EditorClass)
        sz.append(self.Editor, 2, "x")
        self.layout()

    def _getEditor(self):
        if hasattr(self, "_editor"):
            val = self._editor
        else:
            val = self._editor = None
        return val

    def _setEditor(self, val):
        self._editor = val

    def _getEditorClass(self):
        if hasattr(self, "_editorClass"):
            val = self._editorClass
        else:
            val = self._editorClass = None
        return val

    def _setEditorClass(self, val):
        self._editorClass = val

    Editor = property(_getEditor, _setEditor)
    EditorClass = property(_getEditorClass, _setEditorClass)


class ReportObjectTree(dTreeView):
    def initProperties(self):
        self.MultipleSelect = True
        self.ShowButtons = True

    def initEvents(self):
        self.bindKey("ctrl+c", self.onCopy)
        self.bindKey("ctrl+x", self.onCut)
        self.bindKey("ctrl+v", self.onPaste)

    def onCopy(self, evt):
        rdc.copy()

    def onCut(self, evt):
        rdc.cut()

    def onPaste(self, evt):
        rdc.paste()

    def syncSelected(self):
        """Sync the treeview's selection to the rdc."""
        if not rdc._inSelection:
            rdc.SelectedObjects = [obj.Object for obj in self.Selection]

    def onHit(self, evt):
        self.syncSelected()

    def onMouseLeftDoubleClick(self, evt):
        node = evt.EventData["selectedNode"][0]
        rdc.objectDoubleClicked(node.Object, evt)

    def onContextMenu(self, evt):
        evt.stop()
        self.syncSelected()
        self.showContextMenu(rdc.getContextMenu(mousePosition=evt.EventData["mousePosition"]))

    def refreshTree(self):
        """Constructs the tree of report objects."""
        self.clear()
        self.recurseLayout()
        self.expandAll()

    def recurseLayout(self, frm=None, parentNode=None):
        rd = rdc.ActiveEditor
        rw = rd._rw
        rf = rdc.ReportForm

        if rf is None:
            # No form to recurse
            return

        fontSize = 8

        if frm is None:
            frm = rf
            parentNode = self.setRootNode(frm.__class__.__name__)
            parentNode.FontSize = fontSize
            parentNode.Object = frm
            elements = list(frm.keys())
            # elements.sort(rw._elementSort)
            elements.sort()
            for name in elements:
                self.recurseLayout(frm=frm[name], parentNode=parentNode)
            return

        if isinstance(frm, dict):
            node = parentNode.appendChild(self.getNodeCaption(frm))
            node.Object = frm
            node.FontSize = fontSize
            for child in frm.get("Objects", []):
                self.recurseLayout(frm=child, parentNode=node)
            for band in ("GroupHeader", "GroupFooter"):
                if band in frm:
                    self.recurseLayout(frm=frm[band], parentNode=node)

        elif frm.__class__.__name__ in ("Variables", "Groups", "TestCursor"):
            node = parentNode.appendChild(self.getNodeCaption(frm))
            node.Object = frm
            node.FontSize = fontSize
            for child in frm:
                self.recurseLayout(frm=child, parentNode=node)

    def getNodeCaption(self, frm):
        caption = frm.__class__.__name__
        if not frm.__class__.__name__ in ("Variables", "Groups", "TestCursor"):
            expr = rdc.getShortExpr(frm.get("expr", ""))
            if expr:
                if caption.lower() in ("group",):
                    caption = expr
                elif caption.lower() in ("variable",):
                    caption = frm.getProp("Name", evaluate=False)
                else:
                    expr = ": %s" % expr
                    caption = "%s%s" % (frm.__class__.__name__, expr)
        return caption

    def refreshSelection(self):
        """Iterate through the nodes, and set their Selected status
        to match if they are in the current selection of controls.
        """
        objList = rdc.SelectedObjects
        # First, make sure all selected objects are represented:
        for obj in objList:
            rep = False
            for node in self.nodes:
                if id(node.Object) == id(obj):
                    rep = True
                    break
            if not rep:
                # Nope, the object isn't in the tree yet.
                self.refreshTree()
                break

        # Now select the proper nodes:
        selNodes = []
        for obj in objList:
            for node in self.nodes:
                if id(node.Object) == id(obj):
                    selNodes.append(node)

        self.Selection = selNodes

    def refreshCaption(self):
        """Iterate the Selection, and refresh the Caption."""
        for node in self.Selection:
            node.Caption = self.getNodeCaption(node.Object)


class ObjectTreeForm(DesignerControllerForm):
    def initProperties(self):
        super(ObjectTreeForm, self).initProperties()
        self.Caption = "Report Object Tree"
        self.EditorClass = ReportObjectTree

    def selectAll(self):
        rdc.selectAllObjects()


class ReportPropSheet(ClassDesignerPropSheet.PropSheet):
    def beforeInit(self):
        # The ClassDesignerPropSheet appears to need a self.app reference:
        self.app = rdc

    def afterInit(self):
        super(ReportPropSheet, self).afterInit()
        self.addObject(dLabel, Name="lblType", FontBold=True)
        self.Sizer.insert(0, self.lblType, "expand", halign="left", border=10)
        self.Sizer.insertSpacer(0, 10)

    def getObjPropVal(self, obj, prop):
        return obj.getPropVal(prop)

    def getObjPropDoc(self, obj, prop):
        doc = obj.getPropDoc(prop)
        return self.formatDocString(doc)

    def updateVal(self, prop, val, typ):
        """Called from the grid to notify that the current cell's
        value has been changed. Update the corresponding
        property value.
        """
        reInit = False

        if typ == "color":
            # need to convert from rgb to reportlab rgb, and stringify.
            val = rdc.ActiveEditor._rw.getReportLabColorTuple(val)
            val = "(%.3f, %.3f, %.3f)" % (val[0], val[1], val[2])
        for obj in self._selected:
            obj.setProp(prop, val)
            if isinstance(obj, Group) and prop.lower() == "expr":
                reInit = True
        rdc.ActiveEditor.propsChanged(reinit=reInit)
        if rdc.ObjectTree:
            rdc.ObjectTree.refreshCaption()
        focusBack = getattr(self.propGrid, "_focusBack", None)
        if focusBack:
            focusBack.bringToFront()
            self.propGrid._focusBack = None

    def refreshSelection(self):
        objs = rdc.SelectedObjects
        self.select(objs)

        if len(objs) > 1:
            typ = "-multiple selection-"
        elif len(objs) == 0:
            typ = "None"
        else:
            typ = objs[0].__class__.__name__
        self.lblType.Caption = typ

    def editColor(self, objs, prop, val):
        # Override base editColor: need to convert stringified rl tuple to
        # rgb tuple.
        try:
            rgbTuple = eval(val)
        except:
            rgbTuple = None
        if rgbTuple is None:
            rgbTuple = (0, 0, 0)
        rgbTuple = rdc.ActiveEditor._rw.getColorTupleFromReportLab(rgbTuple)
        super(ReportPropSheet, self).editColor(objs, prop, val)


class PropSheetForm(DesignerControllerForm):
    def initProperties(self):
        super(PropSheetForm, self).initProperties()
        self.Caption = "Report Properties"
        self.EditorClass = ReportPropSheet
        self.Controller = (
            self.Application
        )  ## r7033 changed to allow for non-application controllers.


class DesignerPanel(dPanel):
    def onGotFocus(self, evt):
        # Microsoft Windows gives the keyboard focus to sub-panels, which
        # really sucks. This takes care of it.
        rdc.ActiveEditor.SetFocusIgnoringChildren()


# ------------------------------------------------------------------------------
#  BandLabel Class
#
class BandLabel(DesignerPanel):
    """Base class for the movable label at the bottom of each band.

    These are the bands like pageHeader, pageFooter, and detail that
    the user can drag up and down to make the band smaller or larger,
    respectively.
    """

    def afterInit(self):
        self._dragging = False
        self._dragStart = (0, 0)
        self._dragImage = None

    def copy(self):
        self.Parent.copy()

    def cut(self):
        self.Parent.cut()

    def paste(self):
        self.Parent.paste()

    def onMouseMove(self, evt):
        import wx  ## need to abstract DC and mouse cursors!!

        if self._dragging:
            self.SetCursor(wx.Cursor(wx.CURSOR_CROSS))
            pos = evt.EventData["mousePosition"]

            if pos[1] != self._dragStart[1]:
                ypos = (
                    self.Parent.Top
                    + self.Top
                    + pos[1]
                    - self._dragStart[1]  ## (correct for ypos in the band)
                    + 2
                )  ## fudge factor

                if ypos < self.Parent.Top:
                    # Don't show the band dragging above the topmost valid position:
                    ypos = self.Parent.Top

                if self._dragImage is None:
                    # Erase the band label, and instantiate the dragImage rendition of it.
                    dc = wx.WindowDC(self)
                    dc.Clear()

                    self._dragImage = wx.DragImage(self._captureBitmap, wx.Cursor(wx.CURSOR_HAND))

                    # self._dragImage.BeginDragBounded((self.Parent.Left, ypos),
                    # self, self.Parent.Parent)
                    self._dragImage.BeginDrag((self.Parent.Left, ypos), self, self.Parent.Parent)
                    self._dragImage.Show()

                self._dragImage.Move((self.Parent.Left, ypos))

    def onMouseLeftUp(self, evt):
        dragging = self._dragging
        self._dragging = False
        if dragging:
            if self._dragImage is not None:
                self._dragImage.EndDrag()
            self._dragImage = None
            pos = evt.EventData["mousePosition"]
            starty = self._dragStart[1]
            currenty = pos[1]
            yoffset = currenty - starty

            if yoffset != 0:
                z = self.Parent.Parent.ZoomFactor
                # dragging the band is changing the height of the band.
                oldHeight = self.Parent.getProp("Height")
                if oldHeight is not None:
                    oldHeight = self.Parent._rw.getPt(oldHeight)
                else:
                    # Height is None, meaning it is to stretch dynamically at runtime.
                    # However, the user just overrode that by setting it explicitly.
                    if "height_def" in self.Parent.ReportObject:
                        oldHeight = self.Parent._rw.getPt(self.Parent.getProp("Height_def"))
                    else:
                        oldHeight = 75
                newHeight = round(oldHeight + (yoffset / z), 1)
                if newHeight < 0:
                    newHeight = 0
                self.Parent.setProp("Height", newHeight)
            rdc.SelectedObjects = [self.Parent.ReportObject]

    def onMouseLeftDown(self, evt):
        if self.Application.Platform == "Mac":
            # Mac needs the following line, or LeftUp will never fire. TODO:
            # figure out how to abstract this into dPemMixin (if possible).
            # I posted a message to wxPython-mac regarding this - not sure if
            # it is a bug or a "by design" platform inconsistency.
            evt.stop()
        if not self.Parent.getProp("designerLock"):
            self._dragging = True
            self._dragStart = evt.EventData["mousePosition"]
            self._captureBitmap = self.getCaptureBitmap()

    def onMouseEnter(self, evt):
        import wx  ## need to abstract mouse cursor

        if self.Parent.getProp("designerLock"):
            self.SetCursor(wx.NullCursor)
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_SIZENS))

    def onMouseLeftDoubleClick(self, evt):
        rdc.objectDoubleClicked(self.Parent.ReportObject, evt)

    def onPaint(self, evt):
        import wx  ## (need to abstract DC drawing)

        dc = wx.PaintDC(self)
        rect = self.GetClientRect()
        font = self.Font

        dc.SetTextForeground(self.ForeColor)
        dc.SetBrush(wx.Brush(self.BackColor, wx.BRUSHSTYLE_SOLID))
        dc.SetFont(font._nativeFont)
        dc.DrawRectangle(rect[0], rect[1], rect[2], rect[3])
        rect[0] = rect[0] + 5
        rect[1] = rect[1] + 1
        dc.DrawLabel(self.Caption, rect, wx.ALIGN_LEFT)

    def _getCaption(self):
        return self.Parent.Caption

    def _setCaption(self, val):
        self.Parent.Caption = val

    Caption = property(_getCaption, _setCaption)


#  End BandLabel Class
#
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
#
#  Band Class
#
class DesignerBand(DesignerPanel):
    """Base class for report bands.

    Bands contain any number of objects, which can receive the focus and be
    acted upon. Bands also manage their own BandLabels.
    """

    def beforeInit(self):
        self._idleRefreshProps = False

    def initProperties(self):
        self.BackColor = (255, 255, 255)
        self.Top = 100

    def afterInit(self):
        self._cachedBitmaps = {}
        self._rd = self.Form.editor
        self._rw = self._rd._rw
        self.Bands = self._rw.Bands

        self._bandLabelHeight = 18
        self.addObject(
            BandLabel,
            "bandLabel",
            FontSize=9,
            BackColor=(215, 215, 215),
            ForeColor=(128, 128, 128),
            Height=self._bandLabelHeight,
        )

        self._anchorThickness = 5
        self._anchor = None
        self._mouseDown = False
        self._mousePosition = (0, 0)
        self._mouseDragMode = ""

        self._dragging = False
        self._dragStart = (0, 0)
        self._dragObject = None

        self._captureBitmap = None

    def copy(self):
        self.Parent.copy()

    def cut(self):
        self.Parent.cut()

    def paste(self):
        self.Parent.paste()

    def onContextMenu(self, evt):
        evt.stop()
        self.updateSelected()
        self.showContextMenu(rdc.getContextMenu(evt.EventData["mousePosition"]))

    def onMouseLeftDoubleClick(self, evt):
        rdc.objectDoubleClicked(self.getMouseObject(), evt)

    def onMouseMove(self, evt):
        import wx  ## need to abstract DC and mouse cursors!!

        if self._mouseDown:
            if not self._dragging:
                self._dragging = True
                self._dragStart = evt.EventData["mousePosition"]
        evt.stop()

    def onMouseLeftUp(self, evt):
        self._mouseDown = False
        dragging = self._dragging
        dragObject = self._dragObject
        self._dragging, self._dragObject = False, None

        if dragging and dragObject is not None and self._mouseDragMode == "moving":
            pos = evt.EventData["mousePosition"]

            offset = {
                "x": pos[0] - self._dragStart[0],
                "y": -1 * (pos[1] - self._dragStart[1]),
            }

            if offset["x"] != 0 or offset["y"] != 0:
                z = self.Parent.ZoomFactor
                # dragging the object is moving it to a new position.
                for propName in ("x", "y"):
                    old = dragObject.getProp(propName)

                    unit = "pt"
                    if isinstance(old, str) and len(old) > 3:
                        if old[-4] == "pica":
                            unit = "pica"
                        elif old[-2].isalpha():
                            unit = old[-2:]
                    old = self._rw.getPt(old)

                    new = round(old + (offset[propName] / z), 1)
                    if new < 0:
                        new = 0
                    new = self._rw.ptToUnit(new, unit)
                    dragObject.setProp(propName, repr(new))
            self.refresh()
            rdc.refreshProps(refreshEditor=False)

    def onMouseLeftDown(self, evt):
        self.updateSelected(evt)
        # If we let the default event handler run, self.SetFocus() will happen,
        # which we want so that we can receive keyboard focus, but SetFocus() has
        # the side-effect of also scrolling the panel in both directions, for some
        # reason. So, we need to work around this annoyance and call SetFocus()
        # manually:
        evt.stop()
        vs = self.Parent.GetViewStart()
        self.SetFocus()
        self.Parent.Scroll(*vs)

        self._mouseDown = True
        self._mousePosition = evt.EventData["mousePosition"]

    def getMouseObject(self):
        """Returns the topmost object underneath the mouse."""
        rw = self.Parent._rw
        objs = copy.copy(self.ReportObject.get("Objects", []))
        mouseObj = self.ReportObject  ## the band
        mousePos = self.getMousePosition()

        for obj in reversed(objs):
            size, position = self.getObjSizeAndPosition(obj)
            if isinstance(obj, (SpanningLine, SpanningRectangle, Line, Rectangle)):
                # Allow the object to be selected when clicked on by adding some sensitivity
                fudge = 3
                size = list(size)
                position = list(position)
                size[0] += fudge
                size[1] += fudge
                position[0] -= 0.5 * fudge
                position[1] -= 0.5 * fudge
            if (
                mousePos[0] >= position[0]
                and mousePos[0] <= position[0] + size[0]
                and mousePos[1] >= position[1]
                and mousePos[1] <= position[1] + size[1]
            ):
                mouseObj = obj
                break
        return mouseObj

    def updateSelected(self, evt=None):
        mouseObj = self.getMouseObject()
        if not isinstance(mouseObj, Band):
            self._dragObject = mouseObj

        selectedObjs = rdc.SelectedObjects

        if evt and (evt.EventData["controlDown"] or evt.EventData["shiftDown"]):
            # toggle selection of the selObj
            if id(mouseObj) in [id(s) for s in selectedObjs]:
                selectedObjs.remove(mouseObj)
            else:
                selectedObjs.append(mouseObj)
        else:
            # replace selection with the selObj
            selectedObjs = [mouseObj]

        rdc.SelectedObjects = selectedObjs

    def getObjSizeAndPosition(self, obj):
        """Return the size and position needed to draw the object at the current zoom factor."""
        rw = self._rw
        z = self.Parent.ZoomFactor
        if isinstance(obj, Paragraph):
            obj = obj.parent.parent  ## (the FrameSet)
        try:
            x = rw.getPt(obj.getProp("x"))
        except ValueError:
            x = 0
        try:
            y_ = rw.getPt(obj.getProp("y"))
        except ValueError:
            y_ = 0
        y = ((self.Height - self._bandLabelHeight) / z) - y_

        if isinstance(obj, (SpanningLine, SpanningRectangle)):
            xFooter = rw.getPt(obj.getProp("xFooter"))
            yFooter = rw.getPt(obj.getProp("yFooter"))
            width = xFooter - x
            height = (
                y_  ## currently can't draw down to the footer because painting doesn't cross panels
            )
        else:
            width = rw.getPt(obj.getProp("Width"))
            height = obj.getProp("Height")
            hAnchor = obj.getProp("hAnchor").lower()
            vAnchor = obj.getProp("vAnchor").lower()

            if height is None:
                # Dynamic height: use Height_def for the designer surface.
                height = obj.getProp("Height_def")

            height = rw.getPt(height)

            if hAnchor == "right":
                x = x - width
            elif hAnchor == "center":
                x = x - (width / 2)

            if vAnchor == "top":
                y = y + height
            elif vAnchor == "middle":
                y = y + (height / 2)

        size = (z * width, z * height)

        if isinstance(obj, (SpanningLine, SpanningRectangle)):
            position = (z * x, z * y)
        else:
            position = (z * x, (z * y) - (z * height))

        return (size, position)

    def getPositionText(self):
        if self.getProp("designerLock"):
            locktext = "(locked)"
        else:
            locktext = ""
        cap = "(%s) height:%s %s" % (
            self.ReportObject.__class__.__name__,
            self.getProp("Height"),
            locktext,
        )
        return cap

    def onPaint(self, evt):
        import wx  ## (need to abstract DC drawing)

        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush((248, 248, 248)))
        dc.Clear()

        for obj in self.ReportObject.get("Objects", []):
            self._paintObj(obj, dc)
            if isinstance(obj, Frameset):
                for fs_obj in obj["Objects"]:
                    self._paintObj(fs_obj, dc)

        dc.DestroyClippingRegion()

        columnCount = rdc.ReportForm.getProp("ColumnCount")
        columnPadding = self._rw.getPt(rdc.ReportForm.getProp("ColumnPadding"))
        if isinstance(self.ReportObject, (Detail, GroupHeader, GroupFooter)) and columnCount > 1:
            # Cover up all but the first column:
            dc.SetBrush(wx.Brush((192, 192, 192), wx.BRUSHSTYLE_SOLID))
            dc.SetPen(wx.Pen((192, 192, 192), 0, wx.PENSTYLE_SOLID))
            colWidth = self.Width / columnCount
            if columnCount > 1:
                colWidth -= columnPadding
            dc.DrawRectangle(colWidth, 0, colWidth * (columnCount - 1) + 10, self.Height)

    def _paintObj(self, obj, dc=None):
        import wx

        objType = obj.__class__.__name__
        selectColor = (128, 192, 0)

        size, position = self.getObjSizeAndPosition(obj)
        rect = [int(position[0]), int(position[1]), int(size[0]), int(size[1])]

        dc.DestroyClippingRegion()

        dc.SetBrush(wx.Brush((0, 0, 0), wx.BRUSHSTYLE_TRANSPARENT))
        # dc.SetPen(wx.Pen(selectColor, 0.1, wx.PENSTYLE_DOT))
        dc.SetPen(wx.Pen(selectColor, 1, wx.PENSTYLE_DOT))
        dc.DrawRectangle(int(position[0]), int(position[1]), int(size[0]), int(size[1]))

        obj._anchors = {}

        if objType in ("Memo", "Paragraph", "String"):
            dc.SetBackgroundMode(wx.TRANSPARENT)
            expr = rdc.getShortExpr(obj.getProp("expr", evaluate=False))
            alignments = {
                "left": wx.ALIGN_LEFT,
                "center": wx.ALIGN_CENTER,
                "right": wx.ALIGN_RIGHT,
            }

            if objType == "String":
                alignment = obj.getProp("align")
                vAlign = wx.ALIGN_BOTTOM
            else:
                alignment = "left"
                vAlign = wx.ALIGN_TOP
            fontName = obj.getProp("fontName")
            fontSize = obj.getProp("fontSize")
            rotation = obj.getProp("rotation")

            z = self.Parent.Zoom

            fontBold = "Bold" in fontName
            fontItalic = "Oblique" in fontName or "Italic" in fontName
            if "helvetica" in fontName.lower():
                fontFamily = wx.MODERN
                fontName = "Helvetica"
            elif "times" in fontName.lower():
                fontFamily = wx.ROMAN
                fontName = "Times"
            elif "courier" in fontName.lower():
                fontFamily = wx.TELETYPE
                fontName = "Courier"
            elif "symbol" in fontName.lower():
                fontFamily = wx.DEFAULT
                fontBold = False
                fontItalic = False
                fontName = "Symbol"
            elif "zapfdingbats" in fontName.lower():
                fontFamily = wx.DEFAULT
                fontBold = False
                fontItalic = False
                fontName = "ZapfDingbats"
            else:
                fontName = "Helvetica"
                fontFamily = wx.MODERN

            # Can't seem to get different faces represented
            font = dFont()
            font._nativeFont.SetFamily(fontFamily)
            font.Bold = fontBold
            font.Italic = fontItalic
            font.Face = fontName
            font.Size = fontSize * z

            dc.SetFont(font._nativeFont)
            if objType in ("Memo", "String"):
                dc.SetTextForeground(self._rw.getColorTupleFromReportLab(obj.getProp("fontColor")))

            top_fudge = 0.5  ## wx draws a tad too high
            left_fudge = 0.25  ## and a tad too far to the left
            # We need the y value to match up with the font at the baseline, but to clip
            # the entire region, including descent.
            descent = dc.GetFullTextExtent(expr)[2]
            # rect[0] += left_fudge
            # rect[2] += left_fudge
            # rect[1] += top_fudge
            # rect[3] += top_fudge + descent
            rect[3] += descent
            # dc.SetClippingRect(rect)
            dc.SetClippingRegion(rect)

            if False and rotation != 0:
                # We lose the ability to have the alignment and exact rect positioning.
                # But we get to show it rotated. The x,y values below are hacks.
                dc.DrawRotatedText(expr, rect[0] + (rect[2] / 4), rect[3] - (rect[3] / 2), rotation)
            else:
                dc.DrawLabel(
                    expr,
                    (rect[0], rect[1], rect[2], rect[3]),
                    alignments[alignment] | vAlign,
                )

                if objType in ("Memo", "Paragraph"):
                    dc.DrawLabel(
                        "↴",
                        (rect[0], rect[1], rect[2], rect[3]),
                        wx.ALIGN_RIGHT | wx.ALIGN_TOP,
                    )

        if objType in ("Rectangle", "SpanningRectangle"):
            strokeWidth = self._rw.getPt(obj.getProp("strokeWidth")) * self.Parent.Zoom
            sc = obj.getProp("strokeColor")
            if sc is None:
                sc = (0, 0, 0)
            strokeColor = self._rw.getColorTupleFromReportLab(sc)
            fillColor = obj.getProp("fillColor")
            if fillColor is not None:
                fillColor = self._rw.getColorTupleFromReportLab(fillColor)
                fillMode = wx.BRUSHSTYLE_SOLID
            else:
                fillColor = (255, 255, 255)
                fillMode = wx.BRUSHSTYLE_TRANSPARENT
            dc.SetPen(wx.Pen(strokeColor, int(strokeWidth), wx.PENSTYLE_SOLID))
            dc.SetBrush(wx.Brush(fillColor, fillMode))
            dc.DrawRectangle(rect[0], rect[1], rect[2], rect[3])

        if objType in ("Line", "SpanningLine"):
            strokeWidth = self._rw.getPt(obj.getProp("strokeWidth")) * self.Parent.Zoom
            strokeColor = self._rw.getColorTupleFromReportLab(obj.getProp("strokeColor"))
            dc.SetPen(wx.Pen(strokeColor, int(strokeWidth), wx.PENSTYLE_SOLID))

            if objType != "SpanningLine":
                lineSlant = obj.getProp("lineSlant")
                anchors = {
                    "left": rect[0],
                    "center": rect[0] + (rect[2] / 2),
                    "right": rect[0] + rect[2],
                    "top": rect[1],
                    "middle": rect[1] + (rect[3] / 2),
                    "bottom": rect[1] + rect[3],
                }

                if lineSlant == "-":
                    # draw line from (left,middle) to (right,middle) anchors
                    beg = (anchors["left"], anchors["middle"])
                    end = (anchors["right"], anchors["middle"])
                elif lineSlant == "|":
                    # draw line from (center,bottom) to (center,top) anchors
                    beg = (anchors["center"], anchors["bottom"])
                    end = (anchors["center"], anchors["top"])
                elif lineSlant == "\\":
                    # draw line from (right,bottom) to (left,top) anchors
                    beg = (anchors["right"], anchors["bottom"])
                    end = (anchors["left"], anchors["top"])
                elif lineSlant == "/":
                    # draw line from (left,bottom) to (right,top) anchors
                    beg = (anchors["left"], anchors["bottom"])
                    end = (anchors["right"], anchors["top"])
                else:
                    # don't draw the line
                    lineSlant = None

            if objType == "SpanningLine":
                rect = [rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]]
                dc.DrawLine(*rect)
            elif lineSlant:
                dc.DrawLine(int(beg[0]), int(beg[1]), int(end[0]), int(end[1]))

        if objType == "Image":
            bmp = None
            expr = obj.getProp("expr", evaluate=False)
            if expr is None:
                expr = "<< missing expression >>"
            else:
                try:
                    imageFile = eval(expr)
                except:
                    imageFile = None

                if imageFile is not None:
                    if not os.path.exists(imageFile):
                        imageFile = os.path.join(self._rw.HomeDirectory, imageFile)
                    imageFile = ustr(imageFile)

                if imageFile is not None:
                    if os.path.exists(imageFile) and not os.path.isdir(imageFile):
                        bmp = self._cachedBitmaps.get((imageFile, self.Parent.ZoomFactor), None)
                        if bmp is None:
                            import wx

                            expr = None
                            img = wx.Image(imageFile)
                            ## Whether rescaling, resizing, or nothing happens depends on the
                            ## scalemode prop. For now, we just unconditionally rescale:
                            img.Rescale(rect[2], rect[3])
                            bmp = img.ConvertToBitmap()
                            self._cachedBitmaps[(imageFile, self.Parent.ZoomFactor)] = bmp
                    else:
                        expr = "<< file not found >>"
                else:
                    expr = "<< error parsing expr >>"
            if bmp is not None:
                dc.DrawBitmap(bmp, rect[0], rect[1])
            else:
                dc.DrawLabel(expr, (rect[0] + 2, rect[1], rect[2] - 4, rect[3]), wx.ALIGN_LEFT)

        dc.SetBrush(wx.Brush((0, 0, 0), wx.BRUSHSTYLE_TRANSPARENT))

        # Draw a border around the object, if appropriate:
        if "BorderWidth" in obj:
            borderWidth = self._rw.getPt(obj.getProp("BorderWidth")) * self.Parent.Zoom
            if borderWidth > 0:
                borderColor = self._rw.getColorTupleFromReportLab(obj.getProp("BorderColor"))
                dc.SetPen(wx.Pen(borderColor, int(borderWidth), wx.PENSTYLE_SOLID))
                dc.DrawRectangle(rect[0], rect[1], rect[2], rect[3])

        if rdc.isSelected(obj):
            rect = (position[0], position[1], size[0], size[1])
            # border around selected control with sizer boxes:
            dc.SetBrush(wx.Brush((0, 0, 0), wx.BRUSHSTYLE_TRANSPARENT))
            # dc.SetPen(wx.Pen(selectColor, 0.25, wx.PENSTYLE_SOLID))
            dc.SetPen(wx.Pen(selectColor, 1, wx.PENSTYLE_SOLID))
            dc.DrawRectangle(int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3]))

            x, y = (rect[0], rect[1])
            width, height = (rect[2], rect[3])
            thickness = self._anchorThickness

            try:
                hAnchor = obj.getProp("hAnchor").lower()
            except Exception:
                hAnchor = None

            try:
                vAnchor = obj.getProp("vAnchor").lower()
            except Exception:
                vAnchor = None

            anchors = {
                "lt": ["left", "top", x - 1, y - 1],
                "lb": ["left", "bottom", x - 1, y + height - thickness + 1],
                "ct": ["center", "top", x + (0.5 * width) - (0.5 * thickness), y - 1],
                "cb": [
                    "center",
                    "bottom",
                    x + (0.5 * width) - (0.5 * thickness),
                    y + height - thickness + 1,
                ],
                "rt": ["right", "top", x + width - thickness + 1, y - 1],
                "rb": [
                    "right",
                    "bottom",
                    x + width - thickness + 1,
                    y + height - thickness + 1,
                ],
                "lm": ["left", "middle", x - 1, y + (0.5 * height) - (0.5 * thickness)],
                "rm": [
                    "right",
                    "middle",
                    x + width - thickness + 1,
                    y + (0.5 * height) - (0.5 * thickness),
                ],
            }

            obj._anchors = anchors

            for k, v in list(anchors.items()):
                dc.SetBrush(wx.Brush((0, 0, 0), wx.BRUSHSTYLE_SOLID))
                # dc.SetPen(wx.Pen((0,0,0), 0.25, wx.PENSTYLE_SOLID))
                dc.SetPen(wx.Pen((0, 0, 0), 1, wx.PENSTYLE_SOLID))
                if hAnchor == v[0] and vAnchor == v[1]:
                    dc.SetBrush(wx.Brush(selectColor, wx.BRUSHSTYLE_SOLID))
                    dc.SetPen(wx.Pen(selectColor, 1, wx.PENSTYLE_SOLID))
                dc.DrawRectangle(int(v[2]), int(v[3]), int(thickness), int(thickness))

    def getProp(self, prop, evaluate=True, fillDefault=True):
        if evaluate and fillDefault:
            # The report object can do it all:
            return self.ReportObject.getProp(prop)

        try:
            val = self.ReportObject[prop]
        except KeyError:
            if fillDefault:
                val = self.ReportObject.AvailableProps.get(prop)["default"]

        if val is not None and evaluate:
            try:
                vale = eval(val)
            except:
                vale = "?: %s" % ustr(val)
        else:
            vale = val
        return vale

    def setProp(self, prop, val, sendPropsChanged=True):
        """Set the specified object property to the specified value.

        If setting more than one property, self.setProps() is faster.
        """
        self.ReportObject.setProp(prop, ustr(val))
        if sendPropsChanged:
            self.Parent.propsChanged()

    def setProps(self, propvaldict):
        """Set the specified object properties to the specified values."""
        for p, v in list(propvaldict.items()):
            self.setProp(p, v, False)
        self.Parent.propsChanged()

    def _getCaption(self):
        try:
            v = self._caption
        except AttributeError:
            v = ""
        return v

    def _setCaption(self, val):
        self._caption = val

    Caption = property(_getCaption, _setCaption)


#  End Band Class
#
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
#
#  ReportDesigner Class
#
class ReportDesigner(dScrollPanel):
    """Main report designer panel.

    This is the main report designer panel that contains the bands and
    handles setting properties on report objects. While a given object is
    considered to be owned by a particular band, the report designer still
    controls the placement of the object because, among other things, a given
    object can cross bands (a rectangle extending from the group header to the
    group footer, for instance) or move from one band to another.
    """

    def __init__(self, *args, **kwargs):
        import wx

        kwargs["style"] = wx.WANTS_CHARS
        super(ReportDesigner, self).__init__(*args, **kwargs)

    def afterInit(self):
        self._bands = []
        self._rulers = {}
        self._zoom = self._normalZoom = 1.0
        self._clipboard = []
        self._fileName = ""
        self.BackColor = (192, 192, 192)
        self.clearReportForm()

        self.Form.bindEvent(events.Resize, self._onFormResize)

    def onMouseLeftClick(self, evt):
        rdc.SelectedObjects = [rdc.ReportForm]

    def onKeyDown(self, evt):
        # We are going to steal the arrow keys, so make sure we really have the
        # focus and there are valid drawable objects selected.
        if self.Form.pgf.SelectedPageNumber != 0:
            return

        selectedDrawables = []
        for obj in rdc.SelectedObjects:
            if isinstance(obj, Drawable):
                selectedDrawables.append(obj)

        # Now check to see that the keycode matches the keys we are interested in
        # intercepting:
        keys = {
            dKeys.key_Up: "up",
            dKeys.key_Down: "down",
            dKeys.key_Right: "right",
            dKeys.key_Left: "left",
            dKeys.key_Return: "enter",
            dKeys.key_Tab: "tab",
            396: "/",
            394: "-",
            392: "+",
        }

        keyCode = evt.EventData["keyCode"]
        if not keyCode in keys:
            return

        # Okay, we have valid item(s) selected, and it is a key we are interested in.
        shiftDown = evt.EventData["shiftDown"]
        ctrlDown = evt.EventData["controlDown"]
        altDown = evt.EventData["altDown"]
        metaDown = evt.EventData["metaDown"]
        key = keys[keyCode]

        if key == "tab" and (not ctrlDown and not altDown):
            evt.stop()
            selObj = []
            if len(selectedDrawables) > 1:
                # Multiple selected; don't tab traverse; select the first drawable.
                selObj = [
                    selectedDrawables[0],
                ]
            elif not selectedDrawables:
                # No objects selected; select first drawable in selected band,
                # or if no band selected, in the detail band:
                def getNextDrawableInBand(band):
                    objs = band.get("Objects", [])
                    for obj in objs:
                        if isinstance(obj, Drawable):
                            return obj

                if len(rdc.SelectedObjects) == 1 and isinstance(rdc.SelectedObjects[0], Band):
                    selObj = [getNextDrawableInBand(rdc.SelectedObjects[0])]
                if not selObj:
                    selObj = [getNextDrawableInBand(rdc.ReportForm["Detail"])]

            else:
                # One object selected; change selection to next/prior drawable.
                if shiftDown:
                    selObj = [rdc.getPriorDrawable(selectedDrawables[0])]
                else:
                    selObj = [rdc.getNextDrawable(selectedDrawables[0])]
            if selObj[0] is None:
                selObj = [rdc.ReportForm]

            # In order to draw quickly with the paint knowing the object is selected,
            # we manipulate the attribute instead of the property:
            rdc.ActiveEditor._selectedObjects = selObj
            if selObj[0] != rdc.ReportForm:
                rdc.getParentBand(selObj[0]).DesignerObject.refresh()

            # delay the refreshing of the property grid/position:
            rdc.refreshSelection()
            return

        if ctrlDown and not altDown and not shiftDown and not metaDown:
            ## On Windows, the accelerators set up for the zooming aren't working.
            ## I have no idea why, because in dEditor the same setup is working fine.
            ## Anyway, this code makes keyboard zooming work on Windows.
            accel = {
                "+": self.Form.onViewZoomIn,
                "-": self.Form.onViewZoomOut,
                "/": self.Form.onViewZoomNormal,
            }
            func = accel.get(key)
            if func:
                evt.stop()
                func(None)
                return

        if not selectedDrawables:
            return

        if key == "enter":
            # Bring the prop sheet to top and activate the editor for the
            # most appropriate property for the selected object(s), or if
            # shift is down, activate the editor for the current row in the
            # prop sheet.
            evt.stop()
            rdc.objectDoubleClicked(selectedDrawables[0], evt)

        else:
            ## arrow key
            evt.stop()  ## don't let the arrow key scroll the window.
            size, turbo = False, False

            if key in ["up", "right"]:
                adj = 1
            else:
                adj = -1

            if ctrlDown:
                adj = adj * 10

            parentBands = []
            for o in rdc.SelectedObjects:
                if not isinstance(o, Drawable) or o.getProp("designerLock"):
                    continue

                if shiftDown:
                    if key in ["up", "down"]:
                        propName = "height"
                    else:
                        propName = "width"
                else:
                    if key in ["up", "down"]:
                        propName = "y"
                    else:
                        propName = "x"

                propNames = [propName]
                if isinstance(o, (SpanningLine, SpanningRectangle)):
                    if propName == "x":
                        propNames.append("xFooter")
                    if propName == "width":
                        propNames = ["xFooter"]
                    if propName == "height":
                        propNames = ["yFooter"]

                for propName in propNames:
                    val = o.getProp(propName)
                    unit = "pt"

                    parentBand = rdc.getParentBand(o)
                    if parentBand not in parentBands:
                        parentBands.append(parentBand)

                    if isinstance(val, str) and len(val) > 3:
                        if val[-4] == "pica":
                            unit = "pica"
                        elif val[-2].isalpha():
                            unit = val[-2:]

                    val = self._rw.getPt(val)
                    newval = val + adj
                    newval = self._rw.ptToUnit(newval, unit)

                    if propName.lower() in ("width", "height") and self._rw.getPt(newval) < 0:
                        # don't allow width or height to be negative
                        newval = "0 pt"
                    o.setProp(propName, repr(newval))

            for bandObj in parentBands:
                # refresh the parent bands immediately to reflect the drawing:
                bandObj.DesignerObject.refresh()

            # Don't refresh() because that takes too long for no reason:
            self.showPosition()
            self.setCaption()

            # delay the refreshing of the property grid/position:
            rdc.refreshProps(refreshEditor=False)

    def refresh(self):
        super(ReportDesigner, self).refresh()
        self.showPosition()
        self.setCaption()

    def showPosition(self):
        """If one object is selected, show its position and size."""
        # selected objects could include non-visible. Filter these out.
        so = [o for o in rdc.SelectedObjects if isinstance(o, (Drawable, Band))]

        if len(so) == 1:
            so = so[0]
            if isinstance(so, Band):
                do = getattr(so, "DesignerObject", None)
                if do:
                    st = do.getPositionText()
                else:
                    st = ""
            else:
                if isinstance(so, (SpanningLine, SpanningRectangle)):
                    st = "x:%s y:%s  xFooter:%s yFooter:%s" % (
                        so.getProp("x"),
                        so.getProp("y"),
                        so.getProp("xFooter"),
                        so.getProp("yFooter"),
                    )
                else:
                    st = "x:%s y:%s  width:%s height:%s" % (
                        so.getProp("x"),
                        so.getProp("y"),
                        so.getProp("width"),
                        so.getProp("Height"),
                    )
        elif len(so) > 1:
            st = " -multiple objects selected- "
        else:
            st = ""

        st += " Zoom: %s" % self.ZoomPercent
        self.Form.setStatusText(st)

    def clearReportForm(self):
        """Called from afterInit and closeFile to clear the report form."""
        for o in list(self._rulers.values()):
            o.Destroy()
        self._rulers = {}
        for o in self._bands:
            o.release()
        self._bands = []
        if not hasattr(self, "_rw"):
            self._rw = dReportWriter()

    def objectTree(self, obj=None):
        """Display the object Tree for the passed object."""
        if obj is None:
            obj = self
        rw = self._rw

        rdc.showObjectTree(bringToTop=True, refresh=True)

    def promptToSave(self):
        """Decides whether user should be prompted to save, and whether to save."""
        result = True
        if self._rw._isModified():
            result = dabo.ui.areYouSure("Save changes to file %s?" % self._fileName)
            if result:
                self.saveFile()
        return result

    def promptForFileName(self, prompt="Select a file", saveDialog=False):
        """Prompt the user for a file name."""
        import wx  ## need to abstract getFile()

        try:
            dir_ = self._curdir
        except:
            dir_ = ""

        if saveDialog:
            style = wx.FD_SAVE
        else:
            style = wx.FD_OPEN

        dlg = wx.FileDialog(
            self,
            message=prompt,
            defaultDir=dir_,
            style=style,
            wildcard="Dabo Report Forms (*.rfxml)|*.rfxml|All Files (*)|*",
        )

        if dlg.ShowModal() == wx.ID_OK:
            fname = dlg.GetPath()
        else:
            fname = None
        dlg.Destroy()
        return fname

    def promptForSaveAs(self):
        """Prompt user for the filename to save the file as.

        If the file exists, confirm with the user that they really want to
        overwrite.
        """
        while True:
            fname = self.promptForFileName(prompt="Save As", saveDialog=True)
            if fname is None:
                break
            if os.path.exists(fname):
                r = dabo.ui.areYouSure(
                    "File '%s' already exists. " "Do you want to overwrite it?" % fname,
                    defaultNo=True,
                )

                if r is None:
                    # user canceled.
                    fname = None
                    break
                elif r == False:
                    # let user pick another file
                    pass
                else:
                    # User chose to overwrite fname
                    break
            else:
                break

        return fname

    def saveFile(self, fileSpec=None):
        if fileSpec is None:
            fileSpec = self._fileName
            if not fileSpec or fileSpec == NEW_FILE_CAPTION:
                fileSpec = self.promptForSaveAs()
                if fileSpec is None:
                    return False
        self._fileName = fileSpec
        xml = self._rw._getXMLFromForm(self._rw.ReportForm)
        with open(fileSpec, "wb") as ff:
            ff.write(xml.encode("utf-8"))
        self._rw._setMemento()
        self.setCaption()

    def closeFile(self):
        result = self.promptToSave()

        if result is not None:
            self._rw.ReportFormFile = None
            self.clearReportForm()
            self._fileName = ""
        return result

    def setCaption(self):
        """Sets the form's caption based on file name, whether modified, etc."""
        if not hasattr(self, "_rw"):
            # We simply aren't fully initialized yet.
            return

        if self._rw._isModified():
            modstr = "* "
        else:
            modstr = ""
        self.Form.Caption = "%s%s: %s" % (
            modstr,
            self.Form._captionBase,
            self._fileName,
        )

    def newFile(self):
        if self.closeFile():
            self._rw.ReportForm = self._rw._getEmptyForm()
            self.initReportForm()
            self._fileName = NEW_FILE_CAPTION
        rdc.ActiveEditor = self
        rdc.SelectedObjects = [self._rw.ReportForm]

    def openFile(self, fileSpec):
        if os.path.exists(fileSpec):
            if self.closeFile():
                self._rw.ReportFormFile = fileSpec
                self.initReportForm()
                self._fileName = fileSpec
            rdc.ActiveEditor = self
            rdc.SelectedObjects = [self._rw.ReportForm]
            frameset_count = rdc.ReportForm.getFramesetCount()
            if frameset_count == 1:
                fs_text = _("Frameset/Paragraph")
            else:
                fs_text = _("%s Frameset/Paragraphs") % frameset_count
            if frameset_count > 0 and dabo.ui.areYouSure(
                _(
                    "Frameset/Paragraph has been consolidated into a "
                    "new Memo object, which is easier to use and the recommended object for multi-line text. "
                    "You should convert to Memo, and it is easy to do: just click 'yes' below. \n\n"
                    "Would you like to convert the %s"
                    " on this report to the new Memo object?"
                )
                % fs_text,
                cancelButton=False,
            ):
                rdc.ReportForm.convertParagraphsToMemos()
        else:
            raise ValueError("File %s does not exist." % fileSpec)
        return True

    def reInitReportForm(self):
        """Clear the report form and redraw from scratch."""
        rf = self._rw.ReportForm
        self.clearReportForm()
        self._rw.ReportForm = rf
        self.initReportForm()

    def initReportForm(self):
        """Called from openFile and newFile when time to set up the Report Form."""
        rf = self.ReportForm
        self._rw.UseTestCursor = True

        self._rulers = {}
        self._rulers["top"] = self.getRuler("t")
        self._rulers["bottom"] = self.getRuler("b")

        def addBand(bandObj):
            caption = bandObj.__class__.__name__
            if isinstance(bandObj, (GroupHeader, GroupFooter)):
                caption = "%s: %s" % (caption, bandObj.parent.get("expr"))
            self._rulers["%s-left" % caption] = self.getRuler("l")
            self._rulers["%s-right" % caption] = self.getRuler("r")
            b = DesignerBand(self, Caption=caption)
            b.ReportObject = bandObj
            bandObj.DesignerObject = b
            b._rw = self._rw
            self._bands.append(b)

        addBand(rf["ReportBegin"])
        addBand(rf["PageHeader"])

        groups = copy.copy(rf["Groups"])
        for groupObj in groups:
            addBand(groupObj["GroupHeader"])

        addBand(rf["Detail"])

        groups.reverse()
        for groupObj in groups:
            addBand(groupObj["GroupFooter"])

        addBand(rf["PageFooter"])
        addBand(rf["ReportEnd"])
        addBand(rf["PageBackground"])
        addBand(rf["PageForeground"])

        # self._rw.write()  ## 12/16/2008: No need to write the report form at this time.
        self._rw.write()  ## 02/25/2009: Some cases it is needed, and could be Rodgy's problem with TestCursor.
        self.drawReportForm()

    def propsChanged(self, redraw=True, reinit=False):
        """Called by subobjects to notify the report designer that a prop has changed."""
        if reinit:
            self._rw._clearMemento = False
            self.reInitReportForm()
            self._rw._clearMemento = True
        if redraw:
            self.drawReportForm()
        self.Form.setModified(self)
        rdc.refreshProps()

    def _onFormResize(self, evt):
        self.drawReportForm()

    def drawReportForm(self):
        """Resize and position the bands accordingly, and draw the objects."""
        viewStart = self.GetViewStart()
        self.SetScrollbars(0, 0, 0, 0)
        rw = self._rw
        rf = self.ReportForm
        z = self.ZoomFactor

        if rf is None:
            return

        pointPageWidth = rw.getPageSize()[0]
        pageWidth = pointPageWidth * z
        ml = rw.getPt(rf["page"].getProp("marginLeft")) * z
        mr = rw.getPt(rf["page"].getProp("marginRight")) * z
        mt = rw.getPt(rf["page"].getProp("marginTop")) * z
        mb = rw.getPt(rf["page"].getProp("marginBottom")) * z
        bandWidth = pageWidth - ml - mr

        tr = self._rulers["top"]
        tr.Length = pageWidth
        tr.pointLength = pointPageWidth

        for index in range(len(self._bands)):
            band = self._bands[index]
            band.Width = bandWidth
            b = band.bandLabel
            b.Width = band.Width
            b.Left = 0  ## (for some reason, it defaults to -1)

            bandHeight = band.ReportObject.getProp("Height")
            if bandHeight is None:
                if "height_def" in band.ReportObject:
                    bandHeight = band.ReportObject.getProp("Height_def")
                else:
                    bandHeight = 75
            pointLength = band._rw.getPt(bandHeight)
            bandCanvasHeight = z * pointLength
            band.Height = bandCanvasHeight + b.Height
            b.Top = band.Height - b.Height

            if index == 0:
                band.Top = mt + tr.Height
            else:
                band.Top = self._bands[index - 1].Top + self._bands[index - 1].Height

            lr = self._rulers["%s-left" % band.Caption]
            lr.Length = bandCanvasHeight
            lr.pointLength = pointLength

            rr = self._rulers["%s-right" % band.Caption]
            rr.Length = bandCanvasHeight
            rr.pointLength = pointLength

            band.Left = ml + lr.Thickness
            lr.Position = (0, band.Top)
            rr.Position = (lr.Width + pageWidth, band.Top)
            totPageHeight = band.Top + band.Height

        u = 10
        totPageHeight = totPageHeight + mb

        br = self._rulers["bottom"]
        br.Length = pageWidth
        br.pointLength = pointPageWidth

        tr.Position = (lr.Width, 0)
        br.Position = (lr.Width, totPageHeight)
        totPageHeight += br.Height

        _scrollWidth = int((pageWidth + lr.Width + rr.Width) / u)
        _scrollHeight = int(totPageHeight / u)

        ## pkm: Originally, I used just a SetScrollbars() call
        ##      along with the arguments for scroll position.
        ##      But on Windows, that resulted in the report
        ##      drawing on the panel at the wrong offset.
        ##      Separating into these 2 calls fixed the issue.
        self._scrollRate = (u, u)
        self.SetScrollbars(u, u, _scrollWidth, _scrollHeight)
        self.Scroll(viewStart[0], viewStart[1])

        self.showPosition()
        self.refresh()

    def getRuler(self, pos):
        defaultThickness = 20
        defaultLength = 1

        rd = self

        class Ruler(DesignerPanel):
            def initProperties(self):
                self.BackColor = (192, 128, 192)
                self.rulerPos = pos
                self._orientation = {"t": "h", "b": "h", "l": "v", "r": "v"}[pos]
                self.pointLength = 0

            def copy(self):
                return self.Parent.copy()

            def paste(self):
                return self.Parent.paste()

            def cut(self):
                return self.Parent.cut()

            def onPaint(self, evt):
                import wx  ## (need to abstract DC drawing)

                z = rd.ZoomFactor

                ruleColor = (0, 0, 0)
                ruleSizes = {}
                ruleSizes["small"] = 5  ##self.Thickness / 4.0
                ruleSizes["medium"] = 10  ##self.Thickness / 2.0
                ruleSizes["large"] = 15  ##self.Thickness - (self.Thickness / 4)
                unit = "pt"

                size = {}
                if unit == "pt":
                    if z > 2.4:
                        smallest = 1
                    elif z > 1:
                        smallest = 5
                    else:
                        smallest = 10
                    size["small"] = 1
                    size["medium"] = 10
                    size["large"] = 100

                dc = wx.PaintDC(self)
                # jfcs changed the pen width from 0.25 to 1 because must int now
                dc.SetPen(wx.Pen(ruleColor, 1, wx.PENSTYLE_SOLID))

                length = self.Length
                pointLength = self.pointLength
                rulerPos = self.rulerPos
                for pos in range(0, int(pointLength + smallest), smallest):
                    for test in ("large", "medium", "small"):
                        if pos % size[test] == 0:
                            ruleSize = ruleSizes[test]
                            break
                    if ruleSize:
                        # jfcs DC now requires a int
                        rescaledPos = int(pos * z)
                        if rulerPos == "r":
                            dc.DrawLine(0, rescaledPos, ruleSize, rescaledPos)
                        if rulerPos == "l":
                            dc.DrawLine(
                                self.Thickness,
                                rescaledPos,
                                self.Thickness - ruleSize,
                                rescaledPos,
                            )
                        if rulerPos == "b":
                            dc.DrawLine(rescaledPos, 0, rescaledPos, ruleSize)
                        if rulerPos == "t":
                            dc.DrawLine(
                                rescaledPos,
                                self.Thickness,
                                rescaledPos,
                                self.Thickness - ruleSize,
                            )

            def _getThickness(self):
                if self._orientation == "v":
                    val = self.Width
                else:
                    val = self.Height
                return val

            def _setThickness(self, val):
                if self._orientation == "v":
                    self.Width = val
                else:
                    self.Height = val

            def _getLength(self):
                if self._orientation == "v":
                    val = self.Height
                else:
                    val = self.Width
                return val

            def _setLength(self, val):
                if self._orientation == "v":
                    self.Height = val
                else:
                    self.Width = val

            Length = property(_getLength, _setLength)
            Thickness = property(_getThickness, _setThickness)

        return Ruler(self, Length=defaultLength, Thickness=defaultThickness)

    def copy(self):
        rdc.copy()

    def cut(self):
        rdc.cut()

    def paste(self):
        rdc.paste()

    def sendToBack(self):
        self._arrange("sendToBack")

    def bringToFront(self):
        self._arrange("bringToFront")

    def sendBackwards(self):
        self._arrange("sendBackwards")

    def sendUpwards(self):
        self._arrange("sendUpwards")

    def _arrange(self, mode):
        toRedraw = []
        for selObj in rdc.SelectedObjects:
            if isinstance(selObj, Variable):
                parentObj = rdc.ReportForm
                objects = parentObj["Variables"]
            elif isinstance(selObj, Group):
                parentObj = rdc.ReportForm
                objects = parentObj["Groups"]
            else:
                parentObj = rdc.getParentBand(selObj)
                objects = parentObj["Objects"]
            curidx = None
            for idx, obj in enumerate(objects):
                if id(obj) == id(selObj):
                    curidx = idx
                    break

            if curidx is not None:
                obj = objects[idx]
                del objects[idx]
                if mode == "sendToBack":
                    objects.insert(0, obj)
                elif mode == "sendBackwards":
                    objects.insert(max(idx - 1, 0), obj)
                elif mode == "sendUpwards":
                    objects.insert(min(idx + 1, len(objects)), obj)
                else:
                    objects.append(obj)

                if parentObj not in toRedraw:
                    toRedraw.append(parentObj)

        if rdc.ReportForm in toRedraw:
            # must redraw the entire design surface (if e.g. a group changed position)
            self.propsChanged(reinit=True)
        else:
            # only need to redraw selected object(s)
            for parent in toRedraw:
                if hasattr(parent, "DesignerObject"):
                    parent.DesignerObject.refresh()

        if toRedraw:
            rdc.refreshTree()

    def _getReportForm(self):
        return self._rw.ReportForm

    def _setReportForm(self, val):
        self._rw.ReportForm = val

    def _getZoomFactor(self):
        return self._zoom * 1.515

    def _getZoomPercent(self):
        return "%s%%" % (int(self._zoom * 100),)

    def _getZoom(self):
        return self._zoom

    def _setZoom(self, val):
        self._zoom = val

    ReportForm = property(_getReportForm, _setReportForm)
    Zoom = property(_getZoom, _setZoom)
    ZoomFactor = property(_getZoomFactor)
    ZoomPercent = property(_getZoomPercent)


#  End of ReportDesigner Class
#
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
#
#  ReportDesignerForm Class
#
class ReportDesignerForm(dForm):
    """Main form, status bar, and menu for the report designer."""

    def initProperties(self):
        self._captionBase = self.Caption = "Dabo Report Designer"

    def afterInit(self):
        self.Sizer = None
        pgf = self.addObject(dPageFrame, Name="pgf")
        self.pgf.appendPage(ReportDesigner, caption="Visual Editor")
        self.pgf.appendPage(XmlEditor, caption="XML Editor")
        self.pgf.appendPage(PreviewWindow, caption="Preview")
        self.pgf.Pages[1].bindEvent(events.PageEnter, self.onEnterXmlEditorPage)
        self.pgf.Pages[1].bindEvent(events.PageLeave, self.onLeaveXmlEditorPage)
        self.fillMenu()

        self._xmlEditorUpToDate = False
        self.editor = self.pgf.Pages[0]

    def restoreSizeAndPosition(self):
        app = self.Application
        self.editor.Zoom = app.getUserSetting("ReportDesigner_zoom", 1.0)
        super(ReportDesignerForm, self).restoreSizeAndPosition()

    def saveSizeAndPosition(self):
        app = self.Application
        app.setUserSetting("ReportDesigner_zoom", self.editor.Zoom)
        super(ReportDesignerForm, self).saveSizeAndPosition()

    def onActivate(self, evt):
        rdc.ActiveEditor = self.editor

        if rdc.ReportForm:
            if not hasattr(self, "_loaded"):
                self._loaded = True
                if self.Application.getUserSetting("ReportDesigner_ShowPropSheet"):
                    rdc.showPropSheet()

                if self.Application.getUserSetting("ReportDesigner_ShowObjectTree"):
                    rdc.showObjectTree()

    def setModified(self, page):
        if isinstance(page, ReportDesigner):
            self._xmlEditorUpToDate = False

    def onEnterXmlEditorPage(self, evt):
        editBox = self.pgf.Pages[1]
        if not self._xmlEditorUpToDate:
            editor = self.editor
            editBox.Value = editor._rw._getXMLFromForm(rdc.ReportForm)
            self._xmlEditorUpToDate = True
        self._xmlEditorOldValue = editBox.Value

    def onLeaveXmlEditorPage(self, evt):
        editBox = self.pgf.Pages[1]
        if editBox.Value != self._xmlEditorOldValue:
            editor = self.editor
            editBox = self.pgf.Pages[1]
            editor.clearReportForm()
            editor._rw._clearMemento = False
            report = editor._rw._getFormFromXML(editBox.Value)
            editor._rw.ReportForm = report
            editor._rw._clearMemento = True
            editor.initReportForm()
            editor.setCaption()
            ## Force a rebuild of the object tree:
            rdc.refreshTree()
            ## Force a refresh of the propsheet:
            rdc.ActiveEditor = self.editor

    def beforeClose(self, evt):
        result = self.editor.closeFile()
        if result is None:
            return False
        else:
            othersLoaded, psLoaded, otLoaded = False, False, False
            for form in self.Application.uiForms:
                if isinstance(form, PropSheetForm):
                    psLoaded = True
                elif isinstance(form, ObjectTreeForm):
                    otLoaded = True
                elif form != self:
                    othersLoaded = True

            if psLoaded:
                psVisible = rdc.PropSheet.Form.Visible
            else:
                psVisible = False

            if otLoaded:
                otVisible = rdc.ObjectTree.Form.Visible
            else:
                otVisible = False

            if psLoaded and not othersLoaded:
                # The last report has been closed, also close the propsheet:
                rdc.PropSheet.Form.close()
            if otLoaded and not othersLoaded:
                # The last report has been closed, also close the object tree:
                rdc.ObjectTree.Form.close()

            self.Application.setUserSetting("ReportDesigner_ShowPropSheet", psVisible)
            self.Application.setUserSetting("ReportDesigner_ShowObjectTree", otVisible)

    def onEditUndo(self, evt):
        self.editor._rw.undo()
        self.editor.propsChanged()

    def onFileNew(self, evt):
        o = self.editor
        if o._rw.ReportFormFile is None and not o._rw._isModified():
            # open in this editor
            o = self
        else:
            # open in a new editor
            o = ReportDesignerForm(self.Parent)
            o.Size = self.Size
            o.Position = (self.Left + 20, self.Top + 20)
        o.editor.newFile()
        o.Show()

    def onFileOpen(self, evt):
        o = self.editor
        fileName = o.promptForFileName("Open")
        if fileName is not None:
            if o._rw.ReportFormFile is None and not o._rw._isModified():
                # open in this editor
                o = self
            else:
                # open in a new editor
                o = ReportDesignerForm(self.Parent)
                o.Size = self.Size
                o.Position = (self.Left + 20, self.Top + 20)
            o.editor.newFile()
            o.Show()
            o.editor.openFile(fileName)

    def onFileSave(self, evt):
        self.editor.saveFile()

    def onFileClose(self, evt):
        result = self.editor.closeFile()
        if result is not None:
            self.Close()

    def onFileSaveAs(self, evt):
        fname = self.editor.promptForSaveAs()
        if fname:
            self.editor.saveFile(fname)

    def onFilePreviewReport(self, evt):
        import dabo.lib.reportUtils as reportUtils

        fname = self.editor._rw.OutputFile = reportUtils.getTempFile(ext="pdf")
        self.editor._rw.write()
        reportUtils.previewPDF(fname)

    def onEditDelete(self, evt):
        rdc.delete()

    def onEditBringToFront(self, evt):
        self.editor.bringToFront()

    def onEditSendToBack(self, evt):
        self.editor.sendToBack()

    def selectAll(self):
        rdc.selectAllObjects()

    def onViewZoomIn(self, evt):
        ed = self.editor
        if ed.Zoom < 10:
            ed.Zoom *= 1.25
            ed.drawReportForm()

    def onViewZoomNormal(self, evt):
        ed = self.editor
        ed.Zoom = ed._normalZoom
        ed.drawReportForm()

    def onViewZoomOut(self, evt):
        ed = self.editor
        if ed.Zoom > 0.2:
            ed.Zoom /= 1.25
            ed.drawReportForm()

    def onViewShowObjectTree(self, evt):
        o = rdc.ObjectTree
        if o and o.Form.Visible:
            rdc.hideObjectTree()
        else:
            rdc.showObjectTree()

    def onViewShowPropertySheet(self, evt):
        o = rdc.PropSheet
        if o and o.Form.Visible:
            rdc.hidePropSheet()
        else:
            rdc.showPropSheet()

    def fillMenu(self):
        mb = self.MenuBar
        fileMenu = mb.getMenu("base_file")
        editMenu = mb.getMenu("base_edit")
        viewMenu = mb.getMenu("base_view")
        dIcons = dabo.ui.dIcons

        fileMenu.prependSeparator()

        fileMenu.prepend(
            ("Preview Report"),
            HotKey="Ctrl-P",
            OnHit=self.onFilePreviewReport,
            help=("Preview the report as a PDF"),
        )

        fileMenu.prependSeparator()

        fileMenu.prepend(
            ("Save &As"),
            OnHit=self.onFileSaveAs,
            bmp="%s/saveAs.png" % iconPath,
            help=("save"),
        )
        # saveasitem = wx.MenuItem()
        # fileMenu.prepend()

        fileMenu.prepend(
            ("&Save"),
            HotKey="Ctrl+S",
            OnHit=self.onFileSave,
            bmp="%s/save.png" % iconPath,
            help=("Save file"),
        )

        fileMenu.prepend(
            _("&Close"),
            HotKey="Ctrl+W",
            OnHit=self.onFileClose,
            bmp="%s/close.png" % iconPath,
            help=("Close file"),
        )

        fileMenu.prepend(
            _("&Open"),
            HotKey="Ctrl+O",
            OnHit=self.onFileOpen,
            bmp="%s/open.png" % iconPath,
            help=("Open file"),
        )

        fileMenu.prepend(
            _("&New"),
            HotKey="Ctrl+N",
            OnHit=self.onFileNew,
            bmp="%s/new.png" % iconPath,
            help=("New file"),
        )

        editMenu.appendSeparator()

        editMenu.append(
            _("Delete"),
            HotKey="Del",
            OnHit=self.onEditDelete,
            help=("Delete the selected object(s)."),
        )

        editMenu.appendSeparator()

        editMenu.append(
            _("Bring to &Front"),
            HotKey="Ctrl+H",
            OnHit=self.onEditBringToFront,
            help=("Bring selected object(s) to the top of the z-order"),
        )

        editMenu.append(
            _("Send to &Back"),
            HotKey="Ctrl+J",
            OnHit=self.onEditSendToBack,
            help=("Send selected object(s) to the back of the z-order"),
        )

        viewMenu.appendSeparator()

        viewMenu.append(
            _("Zoom &In"),
            HotKey="Ctrl+]",
            OnHit=self.onViewZoomIn,
            bmp="%s/zoomin.png" % iconPath,
            help=("Zoom In"),
        )

        viewMenu.append(
            _("&Normal Zoom"),
            HotKey="Ctrl+\\",
            OnHit=self.onViewZoomNormal,
            bmp="%s/zoomNormal.png" % iconPath,
            help=("Normal Zoom"),
        )

        viewMenu.append(
            _("Zoom &Out"),
            HotKey="Ctrl+[",
            OnHit=self.onViewZoomOut,
            bmp="%s/zoomOut.png" % iconPath,
            help=("Zoom Out"),
        )

        viewMenu.appendSeparator()

        viewMenu.append(
            _("Show/Hide Object Tree"),
            HotKey="Shift+Ctrl+O",
            OnHit=self.onViewShowObjectTree,
            help=("Show the object hierarchy."),
        )

        viewMenu.append(
            _("Show/Hide Property Sheet"),
            HotKey="Shift+Ctrl+P",
            OnHit=self.onViewShowPropertySheet,
            help=("Show the properties for the selected report objects."),
        )


#  End of ReportDesignerForm Class
#
# ------------------------------------------------------------------------------

# For dIDE:
EditorForm = ReportDesignerForm


class XmlEditor(dEditor):
    def initProperties(self):
        self.Language = "xml"


class PreviewWindow(dImage):
    def onPageEnter(self, evt):
        self.render()

    def render(self):
        # Eventually, a platform-independent pdf viewer window will hopefully be
        # available. Until that time, just display the report in the available
        # external viewer:
        self.Form.onFilePreviewReport(None)
        dabo.ui.callAfter(self.Form.pgf._setSelectedPageNumber, 0)


if __name__ == "__main__":
    app = DesignerController()
    app.setup()

    if len(sys.argv) > 1:
        for fileSpec in sys.argv[1:]:
            form = ReportDesignerForm()
            form.editor.openFile("%s" % fileSpec)
            form.Visible = True
    else:
        form = ReportDesignerForm()
        form.editor.newFile()
        form.Visible = True
    app.start()
