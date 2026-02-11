import sys
import time

import wx

from .. import db
from .. import events
from .. import ui
from ..base_object import dObject
from ..lib.propertyHelperMixin import PropertyHelperMixin
from ..lib.utils import ustr
from ..localization import _
from ..preference_mgr import dPref
from . import dFormMixin
from . import dSizerMixin


class ObjectTreeView(ui.dTreeView):
    def __init__(self, parent=None, attProperties={"RegID": "objectTree"}, *args, **kwargs):
        super().__init__(parent=parent, attProperties=attProperties, *args, **kwargs)

    def showObject(self, obj, displayFail=True):
        nd = self.nodeForObject(obj)
        if nd:
            nd.Selected = True
            self.showNode(nd)
        elif displayFail:
            ui.stop(_("Couldn't find object: %s") % obj)
        else:
            raise RuntimeError(_("Object '%s' not found") % obj)

    def onTreeSelection(self, evt):
        ui.callAfter(self.Form.object_selected, self.Selection.Object)

    def expandCurrentNode(self):
        self.expandBranch(self.Selection)

    def collapseCurrentNode(self):
        self.collapseBranch(self.Selection)


class ObjectInspectorForm(ui.dForm):
    def __init__(
        self,
        parent=None,
        attProperties={
            "NameBase": "ObjectInspectorForm",
            "Caption": "Dabo Object Inspector",
            "SaveRestorePosition": "False",
            "Top": "168",
            "Height": "761",
            "Width": "846",
            "Left": "537",
        },
        *args,
        **kwargs,
    ):
        super().__init__(parent=parent, attProperties=attProperties, *args, **kwargs)
        self.Sizer = None
        self._showSizers = False

        parentStack = []
        sizerDict = {}
        currParent = self
        currSizer = None
        sizerDict[currParent] = []

        obj = ui.dSizer(Orientation="Vertical")
        if currSizer:
            currSizer.append(obj)
            currSizer.setItemProps(obj, {})

        if currSizer:
            sizerDict[currParent].append(currSizer)
        currSizer = obj
        if not currParent.Sizer:
            currParent.Sizer = obj

        obj = ui.dSplitter(
            currParent,
            Name="main_splitter",
            attProperties={"Split": "False", "ShowPanelSplitMenu": "False"},
        )
        ui.setAfter(obj, "Orientation", "Horizontal")
        ui.setAfter(obj, "Split", True)
        ui.setAfter(obj, "SashPosition", 380)

        if currSizer:
            currSizer.append(obj)
            currSizer.setItemProps(
                obj,
                {
                    "BorderSides": ["All"],
                    "Proportion": 1,
                    "HAlign": "Center",
                    "VAlign": "Middle",
                    "Border": 0,
                    "Expand": True,
                },
            )

        main_splitter = obj
        main_splitter.createPanes(ui.dPanel, pane=1)
        main_splitter.createPanes(ui.dPanel, pane=2)
        for panel in main_splitter.Children:
            panel.AlwaysResetSizer = True

        parentStack.append(currParent)
        sizerDict[currParent].append(currSizer)
        currParent = obj
        currSizer = None
        if not (currParent in sizerDict):
            sizerDict[currParent] = []

        currParent = main_splitter.Panel1
        currSizer = None
        if not (currParent in sizerDict):
            sizerDict[currParent] = []

        obj = ui.dSizer(Orientation="Vertical")
        if currSizer:
            currSizer.append(obj)
            currSizer.setItemProps(obj, {})

        if currSizer:
            sizerDict[currParent].append(currSizer)
        currSizer = obj
        if not currParent.Sizer:
            currParent.Sizer = obj

        top_splitter = ui.dSplitter(
            currParent,
            Name="top_splitter",
            attProperties={"Split": "False", "ShowPanelSplitMenu": "False"},
        )
        ui.setAfter(top_splitter, "Orientation", "Vertical")
        ui.setAfter(top_splitter, "Split", True)
        ui.setAfter(top_splitter, "SashPosition", 322)

        if currSizer:
            currSizer.append(top_splitter)
            currSizer.setItemProps(
                top_splitter,
                {
                    "BorderSides": ["All"],
                    "Proportion": 1,
                    "HAlign": "Center",
                    "VAlign": "Middle",
                    "Border": 0,
                    "Expand": True,
                },
            )

        top_splitter.createPanes()
        top_splitter.Panel1.SashPercent = 33
        parentStack.append(currParent)
        sizerDict[currParent].append(currSizer)
        currParent = top_splitter
        currSizer = None
        if not (currParent in sizerDict):
            sizerDict[currParent] = []

        currParent = top_splitter.Panel1
        currSizer = None
        if not (currParent in sizerDict):
            sizerDict[currParent] = []

        obj = ui.dSizer(Orientation="Vertical")
        if currSizer:
            currSizer.append(obj)
            currSizer.setItemProps(obj, {})

        if currSizer:
            sizerDict[currParent].append(currSizer)
        currSizer = obj
        if not currParent.Sizer:
            currParent.Sizer = obj

        obj = self.getCustControlClass("ObjectTreeView")(currParent)
        if currSizer:
            currSizer.append(obj)
            currSizer.setItemProps(
                obj,
                {
                    "BorderSides": ["All"],
                    "Proportion": 1,
                    "HAlign": "Center",
                    "VAlign": "Middle",
                    "Border": 0,
                    "Expand": True,
                },
            )

        def _addDesTreeNode(_nodeParent, _nodeAtts, _kidNodes):
            _nodeCaption = self._extractKey(_nodeAtts, "Caption", "")
            if _nodeParent is None:
                obj.clear()
                _currNode = obj.setRootNode(_nodeCaption)
            else:
                _currNode = _nodeParent.appendChild(_nodeCaption)
            # Remove the name and designerClass atts
            self._extractKey(_nodeAtts, "name")
            self._extractKey(_nodeAtts, "designerClass")
            for _nodeProp, _nodeVal in _nodeAtts.items():
                setattr(_currNode, _nodeProp, _nodeVal)
                # try:
                #    exec "_currNode.%s = %s" % (_nodeProp, _nodeVal) in locals()
                # except (SyntaxError, NameError):
                #    exec "_currNode.%s = '%s'" % (_nodeProp, _nodeVal) in locals()
            for _kidNode in _kidNodes:
                _kidAtts = _kidNode.get("attributes", {})
                _kidKids = _kidNode.get("children", {})
                _addDesTreeNode(_currNode, _kidAtts, _kidKids)

        # Set the root
        _rootNode = {
            "name": "dNode",
            "attributes": {"Caption": "This is the root", "designerClass": "controlMix"},
            "children": [
                {
                    "name": "dNode",
                    "attributes": {"Caption": "First Child", "designerClass": "controlMix"},
                },
                {
                    "name": "dNode",
                    "attributes": {"Caption": "Second Child", "designerClass": "controlMix"},
                    "children": [
                        {
                            "name": "dNode",
                            "attributes": {"Caption": "Grandkid #1", "designerClass": "controlMix"},
                        },
                        {
                            "name": "dNode",
                            "attributes": {"Caption": "Grandkid #2", "designerClass": "controlMix"},
                            "children": [
                                {
                                    "name": "dNode",
                                    "attributes": {
                                        "Caption": "Great-Grandkid #1",
                                        "designerClass": "controlMix",
                                    },
                                }
                            ],
                        },
                        {
                            "name": "dNode",
                            "attributes": {"Caption": "Grandkid #3", "designerClass": "controlMix"},
                        },
                    ],
                },
                {
                    "name": "dNode",
                    "attributes": {"Caption": "Third Child", "designerClass": "controlMix"},
                },
            ],
        }
        _rootNodeAtts = _rootNode.get("attributes", {})
        _rootNodeKids = _rootNode.get("children", {})
        _addDesTreeNode(None, _rootNodeAtts, _rootNodeKids)

        if sizerDict[currParent]:
            try:
                currSizer = sizerDict[currParent].pop()
            except (KeyError, IndexError):
                pass
        else:
            currSizer = None

        currParent = top_splitter.Panel2
        currSizer = None
        if not (currParent in sizerDict):
            sizerDict[currParent] = []

        obj = ui.dSizer(Orientation="Vertical")
        if currSizer:
            currSizer.append(obj)
            currSizer.setItemProps(obj, {})

        if currSizer:
            sizerDict[currParent].append(currSizer)
        currSizer = obj
        if not currParent.Sizer:
            currParent.Sizer = obj

        def _grid_left_click(evt):
            def later():
                ds = self.DataSet
                row = ds[self.CurrentRow]
                prop = row["prop"]
                self.Form.PreferenceManager.excluded_props.setValue(prop, True)
                lds = list(ds)
                lds.remove(row)
                self.DataSet = db.dDataSet(lds)

            if evt.altDown:
                ui.callAfterInterval(250, later)

        obj = ui.dGrid(
            currParent, RegID="infoGrid", SelectionMode="Row", OnGridMouseLeftClick=_grid_left_click
        )
        if currSizer:
            currSizer.append(obj)
            currSizer.setItemProps(
                obj,
                {
                    "BorderSides": ["All"],
                    "Proportion": 1,
                    "HAlign": "Center",
                    "VAlign": "Top",
                    "Border": 0,
                    "Expand": True,
                },
            )

        parentStack.append(currParent)
        sizerDict[currParent].append(currSizer)
        currParent = obj
        sizerDict[currParent] = []

        col = ui.dColumn(
            obj,
            attProperties={
                "Width": "169",
                "Caption": "Property",
                "HorizontalAlignment": "Right",
                "DataField": "prop",
                "Order": "0",
            },
        )
        obj.addColumn(col)

        col = ui.dColumn(
            obj,
            attProperties={
                "Caption": "Value",
                "DataField": "val",
                "Editable": "True",
                "Order": "10",
                "Width": "399",
            },
        )
        obj.addColumn(col)

        currParent = parentStack.pop()
        if not (currParent in sizerDict):
            sizerDict[currParent] = []
            currSizer = None
        else:
            try:
                currSizer = sizerDict[currParent].pop()
            except (KeyError, IndexError):
                pass

        if sizerDict[currParent]:
            try:
                currSizer = sizerDict[currParent].pop()
            except (KeyError, IndexError):
                pass
        else:
            currSizer = None

        currParent = parentStack.pop()
        if not (currParent in sizerDict):
            sizerDict[currParent] = []
            currSizer = None
        else:
            try:
                currSizer = sizerDict[currParent].pop()
            except (KeyError, IndexError):
                pass

        if sizerDict[currParent]:
            try:
                currSizer = sizerDict[currParent].pop()
            except (KeyError, IndexError):
                pass
        else:
            currSizer = None

        currParent = main_splitter.Panel2
        currSizer = None
        if not (currParent in sizerDict):
            sizerDict[currParent] = []

        obj = ui.dSizer(Orientation="Vertical")
        if currSizer:
            currSizer.append(obj)
            currSizer.setItemProps(obj, {})

        if currSizer:
            sizerDict[currParent].append(currSizer)
        currSizer = obj
        if not currParent.Sizer:
            currParent.Sizer = obj

        obj = ui.dPanel(currParent, RegID="shellPanel", AlwaysResetSizer=True)
        if currSizer:
            currSizer.append(obj)
            currSizer.setItemProps(
                obj,
                {
                    "BorderSides": ["All"],
                    "Proportion": 1,
                    "HAlign": "Center",
                    "VAlign": "Middle",
                    "Border": 0,
                    "Expand": True,
                },
            )

        if sizerDict[currParent]:
            try:
                currSizer = sizerDict[currParent].pop()
            except (KeyError, IndexError):
                pass
        else:
            currSizer = None

        currParent = parentStack.pop()
        if not (currParent in sizerDict):
            sizerDict[currParent] = []
            currSizer = None
        else:
            try:
                currSizer = sizerDict[currParent].pop()
            except (KeyError, IndexError):
                pass

        if sizerDict[currParent]:
            try:
                currSizer = sizerDict[currParent].pop()
            except (KeyError, IndexError):
                pass
        else:
            currSizer = None

    def addkids(self, obj, node):
        if self._showSizers:
            try:
                kid = obj.Sizer
            except AttributeError:
                kid = None
            if kid:
                snode = node.appendChild(self.sizer_repr(kid))
                snode.Object = kid
                snode.ForeColor = "blue"
                self.addkids(kid, snode)
                return
        try:
            kids = obj.ChildObjects
        except AttributeError:
            # Not a sizer
            try:
                kids = obj.Children
            except AttributeError:
                # Not a dabo obj
                return
        if not kids:
            return
        if isinstance(obj, dFormMixin):
            if obj.ToolBar:
                kids.append(obj.ToolBar)
            if obj.StatusBar:
                kids.append(obj.StatusBar)
        for kid in kids:
            if self.exclude(kid):
                continue
            nodeColor = None
            if isinstance(kid, wx.ScrollBar):
                continue
            if isinstance(kid, dSizerMixin):
                txt = self.sizer_repr(kid)
                nodeColor = "blue"
            else:
                try:
                    txt = kid.Name
                except AttributeError:
                    if isinstance(kid, wx.Size):
                        txt = "Spacer %s" % kid
                        nodeColor = "darkred"
                    else:
                        txt = "%s" % kid
            txt = "%s (%s)" % (txt, self.cls_repr(kid.__class__))
            knode = node.appendChild(txt)
            if nodeColor is not None:
                knode.ForeColor = nodeColor
            knode.Object = kid
            self.addkids(kid, knode)

    def clearHighlight(self):
        if not self:
            return
        current = time.time()
        for expiration in self._highlights.keys():
            if expiration > current:
                continue
            toClear = self._highlights.pop(expiration)
            frm = toClear["targetForm"]
            if toClear["type"] == "drawing":
                try:
                    frm.removeDrawnObject(toClear["drawingToClear"])
                except ValueError:
                    pass
            else:
                sz = toClear["outlinedSizer"]
                frm.removeFromOutlinedSizers(sz)
                frm._alwaysDrawSizerOutlines = toClear["drawSetting"]
                sz.outlineStyle = toClear["outlineStyle"]
                sz.outlineWidth = toClear["outlineWidth"]
            frm.clear()
            frm.refresh()
            self.refresh()

    def onCollapseTree(self, evt):
        self.objectTree.collapseCurrentNode()

    def afterInit(self):
        self.BasePrefKey = "object_inspector"
        self.PreferenceManager = dPref(key=self.BasePrefKey)
        self._highlights = {}

    def formatName(self, obj):
        if not obj:
            return "< -dead object- >"
        try:
            cap = obj.Caption
        except AttributeError:
            cap = ""
        try:
            cls = obj.BaseClass
        except AttributeError:
            cls = obj.__class__
        classString = "%s" % cls
        shortClass = classString.replace("'", "").replace(">", "").split(".")[-1]
        if cap:
            ret = '%s ("%s")' % (shortClass, cap)
        else:
            try:
                ret = "%s (%s)" % (obj.Name, shortClass)
            except AttributeError:
                ret = "%s (%s)" % (obj, cls)
        return ret

    def onToggleSizers(self, evt):
        self._showSizers = not self._showSizers
        self.createObjectTree()

    def showPropVals(self, obj):
        rows = []
        props = []
        try:
            props = obj.getPropertyList(onlyDabo=True)
        except AttributeError:
            for c in obj.__class__.__mro__:
                if c is PropertyHelperMixin:
                    # Don't list properties lower down (e.g., from wxPython):
                    break
                for item in dir(c):
                    if item[0].isupper():
                        if item in c.__dict__:
                            if type(c.__dict__[item]) == property:
                                if props.count(item) == 0:
                                    props.append(item)
        if isinstance(obj, wx._core.Size):
            props = ["_controllingSizer", "_controllingSizerItem", "Spacing"]

        for prop in props:
            if prop == "ShowColumnLabels":
                # Avoid the deprecation warning
                continue
            try:
                val = getattr(obj, prop)
            except (AttributeError, TypeError, ui.assertionException):
                # write-only or otherwise unavailable
                continue
            if prop.startswith("Dynamic") and val is None:
                continue
            if val is None:
                val = self.Application.NoneDisplay
            elif isinstance(val, str):
                val = "'%s'" % val
            elif isinstance(val, dObject):
                try:
                    val = "'%s'" % self.formatName(val)
                except Exception as e:
                    pass
            rows.append({"prop": prop, "val": val})
        ds = db.dDataSet(rows)
        self.infoGrid.DataSet = ds

    def sizer_repr(self, sz):
        """Returns an informative representation for a sizer"""
        if isinstance(sz, ui.dGridSizer):
            ret = f"dGridSizer ({sz.HighRow} x {sz.HighCol})"
        elif isinstance(sz, ui.dBorderSizer):
            ret = f"dBorderSizer ({sz.Orientation}, '{sz.Caption}')"
        else:
            ret = f"dSizer ({sz.Orientation})"
        return ret

    def exclude(self, obj):
        """Skip floaing window, the object inspector itself, and any dead objects"""
        isFloat = isinstance(obj, ui.dDialog) and hasattr(obj, "Above") and hasattr(obj, "Owner")
        return isFloat or (obj is self) or not bool(obj)

    def _getHighlightInfo(self, obj, frm):
        pos = obj.ClientToScreen((0, 0))
        if self.Application.Platform == "Mac":
            pos = frm.ScreenToClient(pos)
            dc = wx.WindowDC(frm)
        else:
            dc = wx.ScreenDC()
        return pos, dc

    def setSelectedObject(self, obj, silent=False):
        try:
            self.objectTree.showObject(obj, displayFail=False)
            self.objectTree.expandCurrentNode()
        except RuntimeError as e:
            if not silent:
                ui.stop(e, "Object Inspector")

    def onFindObject(self, evt):
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.OnCaptureLost)
        self.CaptureMouse()
        self.finding = wx.BusyInfo("Click on any widget in the app...")

    def OnCaptureLost(self, evt):
        self.Unbind(wx.EVT_LEFT_DOWN)
        self.Unbind(wx.EVT_MOUSE_CAPTURE_LOST)
        del self.finding

    def afterInitAll(self):
        objnote = "NOTE: The 'obj' variable refers to the object selected in the tree."
        intro = "%s\n%s" % (ui.getSystemInfo(), objnote)
        shell_panel = self.shellPanel
        self.shell = ui.dShell(shell_panel, showInterpIntro=False, introText=intro)
        self.shell.interp.locals["self"] = self
        sz = shell_panel.Sizer = ui.dBorderSizer(shell_panel, Caption="Interactive Interpreter")
        sz.append1x(self.shell)
        ui.callEvery(250, self.clearHighlight)

        tb = self.ToolBar = ui.dToolBar(self, ShowCaptions=True)
        self.refreshButton = self.appendToolBarButton(
            name="Refresh",
            pic="refresh_tree.png",
            toggle=False,
            tip=_("Re-create the object tree"),
            OnHit=self.onRefreshTree,
        )
        self.findButton = self.appendToolBarButton(
            name="Find",
            pic="find_object.png",
            toggle=False,
            tip=_("Find an object in your app in the tree"),
            OnHit=self.onFindObject,
        )
        self.showSizersButton = self.appendToolBarButton(
            name="Show Sizers",
            pic="show_sizers.png",
            toggle=True,
            tip=_("Show/Hide sizers in the object hierarchy"),
            OnHit=self.onToggleSizers,
        )
        self.expandButton = self.appendToolBarButton(
            name="Expand",
            pic="expand_tree.png",
            toggle=False,
            tip=_("Expand this node and all nodes under it."),
            OnHit=self.onExpandTree,
        )
        self.collapseButton = self.appendToolBarButton(
            name="Collapse",
            pic="collapse_tree.png",
            toggle=False,
            tip=_("Collapse this node and all nodes under it."),
            OnHit=self.onCollapseTree,
        )
        self.highlightButton = self.appendToolBarButton(
            name="Highlight",
            pic="highlight_item.png",
            toggle=False,
            tip=_("Highlight the selected node in your app."),
            OnHit=self.onHighlightItem,
        )
        self.layout()

    def onRefreshTree(self, evt):
        self.createObjectTree()

    def onExpandTree(self, evt):
        self.objectTree.expandCurrentNode()

    def cls_repr(self, cls):
        """Returns a readable representation for a class"""
        txt = "%s" % cls
        prfx, clsname, suff = txt.split("'")
        return clsname

    def OnLeftDown(self, evt):
        self.ReleaseMouse()
        wnd, pos = wx.FindWindowAtPointer()
        if wnd is not None:
            self.objectTree.showObject(wnd)
        else:
            ui.beep()
        self.OnCaptureLost(evt)

    def onHighlightItem(self, evt):
        obj = self.objectTree.Selection.Object
        try:
            frm = obj.Form
        except AttributeError:
            return
        # Remove the highlight after 3 seconds
        expires = time.time() + 3
        entry = self._highlights[expires] = {}
        entry["targetForm"] = frm

        if isinstance(obj, ui.dSizerMixin):
            entry["type"] = "sizer"
            frm.addToOutlinedSizers(obj)
            frm.refresh()
            entry["outlinedSizer"] = obj
            entry["drawSetting"] = frm._alwaysDrawSizerOutlines
            entry["outlineStyle"] = obj.outlineStyle
            obj.outlineStyle = "dot"
            entry["outlineWidth"] = obj.outlineWidth
            obj.outlineWidth = 4
            frm._alwaysDrawSizerOutlines = True
        else:
            if isinstance(obj, ui.dFormMixin):
                # Don't highlight the form; just bring it to the foreground
                del self._highlights[expires]
                obj.bringToFront()
                return
            x, y = obj.formCoordinates()
            entry["type"] = "drawing"
            # Make sure outline is visible
            xDraw = max(0, x - 3)
            yDraw = max(0, y - 3)
            wDraw = min(frm.Width - xDraw, obj.Width + 6)
            hDraw = min(frm.Height - yDraw, obj.Height + 6)
            entry["drawingToClear"] = frm.drawRectangle(
                xDraw, yDraw, wDraw, hDraw, penWidth=3, penColor="magenta"
            )

    def object_selected(self, obj):
        self.shell.interp.locals["obj"] = obj
        self.shellPanel.Sizer.Caption = "'obj' is %s" % self.formatName(obj)
        self.showPropVals(obj)

    def createObjectTree(self):
        tree = self.objectTree
        try:
            currObj = tree.Selection.Object
            currForm = currObj.Form
        except AttributeError:
            # Nothing selected yet
            currObj = currForm = None
        tree.clear()
        root = tree.setRootNode("Top Level Windows")
        for win in self.Application.uiForms:
            if self.exclude(win):
                continue
            winNode = root.appendChild(self.formatName(win))
            winNode.Object = win
            self.addkids(win, winNode)
        root.expand()
        if currObj:
            nd = tree.nodeForObject(currObj)
            if not nd:
                nd = tree.nodeForObject(currForm)
            nd.Selected = True

    @property
    def ShowSizers(self):
        """Determines if sizers are displayed in the object hierarchy"""
        try:
            return self._showSizers
        except AttributeError:
            return None

    @ShowSizers.setter
    def ShowSizers(self, val):
        self._showSizers = val

    def getCustControlClass(self, clsName):
        # Define the classes, and return the matching class

        return eval(clsName)


ui.InspectorFormClass = ObjectInspectorForm
