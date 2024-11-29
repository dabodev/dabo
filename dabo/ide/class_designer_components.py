# -*- coding: utf-8 -*-
import os

from .. import ui
from .. import dColors
from ..dLocalize import _
from ..lib.utils import ustr
from ..lib import utils as libutils
from ..dObject import dObject
from .. import events
from .. import application
from ..lib.xmltodict import xmltodict
from ..lib.DesignerUtils import addSizerDefaults
from .class_designer_exceptions import PropertyUpdateException
from .drag_handle import DragHandle

from ..ui import dBorderSizer
from ..ui import dBox
from ..ui import dColumn
from ..ui import dDialog
from ..ui import dForm
from ..ui import dFormMain
from ..ui import dGrid
from ..ui import dGridSizer
from ..ui import dImage
from ..ui import dLabel
from ..ui import dMenu
from ..ui import dPage
from ..ui import dPageFrame
from ..ui import dPageFrameNoTabs
from ..ui import dPageList
from ..ui import dPageSelect
from ..ui import dPageStyled
from ..ui import dPanel
from ..ui import dRadioList
from ..ui import dSizer
from ..ui import dSpinner
from ..ui import dSplitter
from ..ui import dTreeView
from ..ui.dialogs import Wizard
from ..ui.dialogs import WizardPage

dabo_module = settings.get_dabo_package()


# Defaults for sizer items
szItemDefaults = {
    1: {
        "BorderSides": ["All"],
        "Proportion": 0,
        "HAlign": "Left",
        "VAlign": "Top",
        "Border": 0,
        "Expand": False,
    },
    2: {
        "RowSpan": 1,
        "BorderSides": ["All"],
        "ColSpan": 1,
        "Proportion": 1,
        "HAlign": "Left",
        "VAlign": "Top",
        "Border": 0,
    },
}
# This odd attribute name is given to any object that is added
# to a design as a class. We handle them differently; only the
# changes are saved in the design they are added to.
classFlagProp = "_CLASS_PATH_"


class LayoutSaverMixin(dObject):
    """Contains the basic code for generating the dict required
    to save the ClassDesigner item's contents.
    """

    def __init__(self, *args, **kwargs):
        super(LayoutSaverMixin, self).__init__(*args, **kwargs)

    def getDesignerDict(
        self,
        itemNum=0,
        allProps=False,
        classID=None,
        classDict=None,
        propsToExclude=None,
    ):
        app = self.Controller
        ret = {}
        if not app:
            return ret
        if not allProps:
            # Can be set globally by the save routine
            allProps = app.saveAllProps
        #             if isinstance(self, dColumn):
        #                 # We need all props for this class.
        #                 allProps = True
        ret["attributes"] = ra = {}
        isClass = hasattr(self, classFlagProp)

        isWiz = isinstance(self, Wizard)
        insideClass = isClass or (len(app._classStack) > 0)
        if isClass:
            clsPath = self.__getattribute__(classFlagProp)
            app._classStack.append(clsPath)
            if os.path.exists(clsPath):
                classDict = xmltodict(open(clsPath).read())
            else:
                # New file
                classDict = {}
            if classID is None:
                # Use the attribute.
                ra["classID"] = self.classID
            else:
                ra["classID"] = classID
                self.classID = classID
        else:
            if insideClass:
                try:
                    myID = self.classID.split("-")[1]
                except (AttributeError, IndexError):
                    myID = abs(self.__hash__())
                if classID is None:
                    # First-time save. Get the classID of the parent
                    try:
                        classID = self.Parent.classID.split("-")[0]
                    except (IndexError, AttributeError):
                        # Try the sizer
                        try:
                            classID = self.ControllingSizer.classID.split("-")[0]
                        except (IndexError, AttributeError):
                            classID = "?????"
                ra["classID"] = "%s-%s" % (classID, myID)
                self.classID = ra["classID"]
            else:
                if hasattr(self, "classID"):
                    ra["classID"] = self.classID
        ret["name"] = self.getClass()
        ret["cdata"] = ""
        if insideClass and classDict:
            if hasattr(self, "Form") and self.Form._formMode:
                ret["code"] = self.diffClassCode(classDict.get("code", {}))
            else:
                ret["code"] = self.getCode()
        else:
            ret["code"] = self.getCode()

        defVals = self.Controller.getDefaultValues(self)
        if insideClass:
            if classDict:
                defVals.update(classDict.get("attributes", {}))
        if isClass:
            clsRef = os.path.abspath(clsPath)
            if isinstance(self, (dForm, dFormMain)):
                relPath = self._classFile
            else:
                relPath = self.Form._classFile
            if not relPath:
                relPath = os.path.split(relPath)[0]
            if clsRef == relPath:
                rp = clsRef
            else:
                rp = libutils.relativePath(clsRef, relPath)
            ra["designerClass"] = libutils.getPathAttributePrefix() + rp
            ra["savedClass"] = True
        else:
            ra["designerClass"] = self.getClassName()

        hasSizer = bool(hasattr(self, "ControllingSizerItem") and self.ControllingSizerItem)
        # We want to include some props whether they are the
        # default or not.
        if insideClass:
            propsToInclude = ("classID", "SlotCount")
        else:
            propsToInclude = (
                "Caption",
                "Choices",
                "ColumnCount",
                "Orientation",
                "PageCount",
                "SashPosition",
                "ScaleMode",
                "SlotCount",
                "Split",
            )
        # We want to exclude some props, since they are derived from
        # other props or are settable via other props (fonts).
        if propsToExclude is None:
            propsToExclude = tuple()
        elif isinstance(propsToExclude, list):
            propsToExclude = tuple(propsToExclude)
        propsToExclude += ("Right", "Bottom", "Font", "HeaderFont")
        isSplitPanel = isinstance(self, dPanel) and isinstance(self.Parent, dSplitter)
        desProps = list(self.DesignerProps.keys())
        if isinstance(self, (dForm, dFormMain)) and hasattr(self, "UseSizers"):
            desProps += ["UseSizers"]
        elif isinstance(self, self.Controller.pagedControls) and isinstance(self.PageClass, str):
            desProps += ["PageClass"]
        elif isinstance(self, Wizard):
            desProps += ["PageCount"]
        for prop in desProps:
            if prop.startswith("Sizer_"):
                continue
            if prop in propsToExclude:
                continue
            if (hasSizer or isinstance(self, dPage) or isSplitPanel) and prop in (
                "Left",
                "Right",
                "Top",
                "Bottom",
            ):  # , "Width", "Height"
                ##"Right", "Top", "Bottom", "Width", "Height"):
                ## Note: there may be additional cases where we might have to fine-tune
                ## which if these parameters are skipped/included.
                continue
            try:
                csz = self.ControllingSizer
            except AttributeError:
                csz = None
            if (
                (hasSizer or isinstance(self, dPage) or isSplitPanel)
                and prop in ("Width", "Height")
                and ((csz is not None) and csz.getItemProp(self, "Expand"))
            ):
                continue
            if isinstance(self, dLabel) and prop in ("Width", "Height") and csz is not None:
                # If the width/height is controlled by the sizer, don't save it.
                szornt = csz.Orientation
                exp = csz.getItemProp(self, "Expand")
                prptn = csz.getItemProp(self, "Proportion")
                if szornt == "Horizontal":
                    if (prop == "Width") and (prptn > 0):
                        continue
                    elif (prop == "Height") and exp:
                        continue
                elif szornt == "Vertical":
                    if (prop == "Width") and exp:
                        continue
                    elif (prop == "Height") and (prptn > 0):
                        continue
                # Don't copy the size if AutoSize=True and the width is close to the default size.
                if self.AutoResize:
                    defWd, defHt = ui.fontMetric(wind=self)
                    isDefaultSize = False
                    if prop == "Width":
                        isDefaultSize = abs(self.Width - defWd) <= 1
                    elif prop == "Height":
                        isDefaultSize = abs(self.Height - defHt) <= 1
                    if isDefaultSize:
                        # ignore it
                        continue
            if prop == "BackColor" and isinstance(self, (LayoutPanel, LayoutSpacerPanel)):
                continue
            if isinstance(self, dImage) and (prop == "Value") and self.Picture:
                # Don't save the byte stream if there is an image path
                continue

            if hasattr(self, prop):
                val = eval("self.%s" % prop)
            else:
                # Custom-defined property; that's saved elsewhere
                continue
            if prop == "RegID" and not val:
                continue

            # Convert any paths, but ignore the string properties that may
            # accidentally contain a legal path but which do not represent paths.
            if not prop in (
                "Alignment",
                "Caption",
                "CxnName",
                "DataField",
                "DataSource",
                "FontFace",
                "HAlign",
                "Name",
                "RegID",
                "SelectionMode",
                "ToolTipText",
                "VAlign",
                "Value",
            ) and (
                not prop.startswith("Border")
                and not prop.startswith("Header")
                and not prop.startswith("Sizer_")
            ):
                if isinstance(val, str) and os.path.exists(val):
                    # It's a path; convert it to a relative path
                    if isinstance(self, (dForm, dFormMain, dDialog)):
                        ref = self._classFile
                    else:
                        ref = self.Form._classFile
                    ref = os.path.abspath(ref)
                    if not os.path.isdir(ref):
                        # Can't test for 'isfile' since the file may not have been saved yet.
                        ref = os.path.split(ref)[0]
                    val = os.path.join(
                        libutils.getPathAttributePrefix(),
                        libutils.relativePath(val, ref),
                    )

            # If it hasn't changed from the default, skip it
            if not allProps:
                try:
                    defVals[prop]
                except KeyError:
                    continue
                if prop not in propsToInclude:
                    dv = defVals[prop]
                    if not isinstance(val, str) and isinstance(dv, str):
                        # Try to convert
                        if isinstance(val, bool):
                            dv = dv.lower() == "true"
                        elif isinstance(val, int):
                            dv = int(dv)
                        elif isinstance(val, int):
                            dv = int(dv)
                        elif isinstance(val, float):
                            dv = float(dv)
                        elif dv in dColors.colors:
                            dv = dColors.colorDict[dv]
                        elif isinstance(val, (list, tuple, dict)):
                            dv = eval(dv)
                        elif dv == "None":
                            dv = None
                    if dv == val:
                        continue

            if isinstance(val, str):
                strval = val
            else:
                strval = str(val)
            ra[prop] = strval
        # Add the controlling sizer item properties, if applicable
        try:
            itmProps = self.ControllingSizer.getItemProps(self.ControllingSizerItem)
            if insideClass:
                itmDiffProps = self._diffSizerItemProps(itmProps, classDict, direct=True)
            else:
                itmDiffProps = self._diffSizerItemProps(itmProps, self.ControllingSizer)
            ret["attributes"]["sizerInfo"] = itmDiffProps
        except AttributeError:
            # Not controlled by a sizer.
            pass

        propDefs = self.getPropDefs()
        if propDefs:
            ret["properties"] = propDefs

        # Add the child objects. This will vary depending on the
        # class of the item
        ret["children"] = self.getChildrenPropDict(classDict)
        if isClass:
            # Remove this class from the processing stack
            app._classStack.pop()
        return ret

    def _diffSizerItemProps(self, dct, szOrDict, direct=False):
        """Remove all of the default values from the sizer item props."""
        if direct:
            defaults = szOrDict
        else:
            # First, what type of sizer is it?
            try:
                cls = self.superControl
            except AttributeError:
                cls = self.__class__
            if isinstance(szOrDict, dGridSizer):
                typ = "G"
            else:
                typ = szOrDict.Orientation.upper()[0]
            defaults = self.Controller.getDefaultSizerProps(cls, typ).copy()
        if isinstance(self, LayoutPanel) and not isinstance(self, LayoutSpacerPanel):
            defaults["Expand"] = True
            defaults["Proportion"] = 1
        for key, val in list(dct.items()):
            if val == defaults.get(key, None):
                dct.pop(key)
        return dct

    def diffClassCode(self, clsCode):
        """See what code, if any, has been changed between the code
        in the defined class and the current object.
        """
        ret = {}
        currCode = self.getCode()
        if currCode and (currCode != clsCode):
            # Need to find all changed methods
            for mthd, cd in list(currCode.items()):
                clscd = clsCode.get(mthd, "")
                if cd != clscd:
                    ret[mthd] = cd
            # See if there are any cleared methods
            if list(clsCode.keys()) != list(currCode.keys()):
                currK = list(currCode.keys())
                for clsK in list(clsCode.keys()):
                    if clsK not in currK:
                        ret[clsK] = ""
        return ret

    def getCode(self):
        """Return the code for the object in a method:code
        dictionary.
        """
        ret = {}
        objCode = self.Controller.getCodeForObject(self)
        if objCode is not None:
            # Check for empty methods
            emptyKeys = [kk for kk, vv in list(objCode.items()) if not vv]
            for emp in emptyKeys:
                del objCode[emp]
            ret.update(objCode)
        return ret

    def getPropDefs(self):
        """Get a dict containing any defined properties for this object."""
        ret = self.Controller.getPropDictForObject(self)
        #         if ret:
        #             # Need to escape any single quotes in the comments
        #             sqt = "'"
        #             sqtReplacement = r"\&apos;"
        #             for prop, settings in ret.items():
        #                 if sqt in settings["comment"]:
        #                     settings["comment"] = settings["comment"].replace(sqt, sqtReplacement)
        return ret

    def serialName(self, nm, numItems=0):
        """Prepends a three-digit string to the beginning
        of the passed string. This string starts at '000', and
        is incremented for each object listed in the 'keys'
        list. This enables us to maintain object order within
        a dictionary, which is otherwise unordered.
        """
        return "d%s%s" % (strl(numItems).zfill(3), nm)

    def getChildrenPropDict(self, clsChildren=None):
        """Iterate through the children. For controls, this will
        go through the containership hierarchy. Sizers will have
        to override this method. If this is being called inside of a
        class definition, 'clsChildren' will be a dict containing the
        saved class definition for the child objects.
        """
        ret = []
        try:
            kids = self.zChildren
        except AttributeError:
            # Use the normal Children prop
            try:
                if isinstance(self, dTreeView):
                    kids = self.BaseNodes
                else:
                    kids = self.Children
            except AttributeError:
                # Object does not have a Children prop
                return ret

        # Are we inside a class definition?
        insideClass = clsChildren is not None
        if insideClass:
            childDict = clsChildren.get("children", [])
        if isinstance(self, (dPageFrame, dPageList, dPageSelect, dPageStyled, dPageFrameNoTabs)):
            nonSizerKids = kids
        elif isinstance(self, dGrid):
            # Grid children are Columns
            nonSizerKids = self.Columns
        elif isinstance(self, dSplitter):
            nonSizerKids = [self.Panel1, self.Panel2]
        elif isinstance(self, Wizard):
            nonSizerKids = self._pages
        elif isinstance(self, (dForm, dFormMain)) and not self.UseSizers:
            nonSizerKids = kids
        elif isinstance(self, (dRadioList, dSpinner)):
            nonSizerKids = []
        else:
            nonSizerKids = [
                kk
                for kk in kids
                if not hasattr(kk, "ControllingSizerItem") or kk.ControllingSizerItem is None
            ]

        for kid in nonSizerKids:
            numItems = len(ret)
            if isinstance(kid, (dForm, dFormMain)):
                # This is a child window; most likely part of the
                # ClassDesigner interface, but certainly not part of
                # the class defintion. Sklp it!
                continue
            if not hasattr(kid, "getDesignerDict"):
                # This is some non-ClassDesigner control, such as a
                # Status Bar, that we don't need to save
                continue

            # If we are inside of a class defintion, we need to
            # get the dict specific to this child. If it has a classID,
            # we can find the matching entry in our child dict.
            # Otherwise, we have to assume that it is a new object
            # added to the class.
            kidDict = None
            if insideClass:
                try:
                    kidID = kid.classID
                    try:
                        kidDict = [cd for cd in childDict if cd["attributes"]["classID"] == kidID][
                            0
                        ]
                    except Exception as e:
                        kidDict = {}
                except AttributeError:
                    kidDict = {}

            ret.append(kid.getDesignerDict(itemNum=numItems, classDict=kidDict))

        if isinstance(self, Wizard):
            # All the children have been processed
            return ret
        if hasattr(self, "_superBase"):
            if isinstance(self, WizardPage):
                sz = self.Sizer
            else:
                try:
                    sz = self.mainPanel.Sizer
                except AttributeError:
                    sz = None
        else:
            if isinstance(self, dPageFrameNoTabs):
                sz = None
            else:
                if isinstance(
                    self,
                    (
                        dRadioList,
                        dSpinner,
                        dPageSelect,
                        dPageStyled,
                        dColumn,
                        dTreeView.getBaseNodeClass(),
                    ),
                ):
                    sz = None
                else:
                    try:
                        sz = self.Sizer
                    except AttributeError:
                        dabo_module.error(_("No sizer information available for %s") % self)
                        sz = None
        if sz:
            szDict = None
            if insideClass:
                try:
                    szID = sz.classID
                    try:
                        szDict = [cd for cd in childDict if cd["attributes"]["classID"] == szID][0]
                    except Exception as e:
                        szDict = {}
                except AttributeError:
                    szDict = {}
            ret.append(sz.getDesignerDict(itemNum=len(ret), classDict=szDict))
        return ret

    def getClass(self):
        """Return a string representing the item's class. Can
        be overridden by subclasses.
        """
        return ustr(self.BaseClass).split("'")[1].split(".")[-1]

    def getClassName(self):
        """Return a string representing the item's class name. Can
        be overridden by subclasses.
        """
        return ustr(self.__class__).split("'")[1].split(".")[-1]


class LayoutPanel(dPanel, LayoutSaverMixin):
    """Panel used to display empty sizer slots."""

    def __init__(self, parent, properties=None, *args, **kwargs):
        self._autoSizer = self._extractKey(kwargs, "AutoSizer", True)
        kwargs["Size"] = (20, 20)
        super(LayoutPanel, self).__init__(parent, properties, *args, **kwargs)
        # Let the framework know that this is just a placeholder object
        self._placeholder = True
        # Store the defaults for the various props
        self._propDefaults = {}
        self._defaultSizerProps = {}
        for prop in list(self.DesignerProps.keys()):
            self._propDefaults[prop] = eval("self.%s" % prop)

    def afterInit(self):
        self.depth = self.crawlUp(self)
        plat = self.Application.Platform
        if plat == "Win":
            self.normalColor = "cornsilk"
        else:
            self.normalColor = "azure"
        self.normalBorder = self.BorderColor = "darkgrey"
        self.hiliteColor = "white"
        self.hiliteBorder = "gold"
        self.BackColor = self.normalBorder
        self._selected = False
        self.Selected = False
        self._innerPanel = dPanel(self, BackColor=self.normalColor, _EventTarget=self)
        self.Sizer = dSizer("v")
        self.Sizer.append1x(self._innerPanel, border=1)
        # Make sure the panel allows full resizing
        self.AlwaysResetSizer = True
        # Windows has a problem with auto-clearing
        ### NOTE: seems to not flicker as much with this commented out (at least on Mac).
        # self.autoClearDrawings = (plat != "Win")
        if self._autoSizer:
            if isinstance(self.Parent.Sizer, dSizer):
                self.Parent.Sizer.append1x(self)
                szi = self.ControllingSizerItem
            ornt = "v"
            prntSz = self.ControllingSizer
            if prntSz is not None:
                if prntSz.Orientation[:1].lower() == "v":
                    ornt = "h"
                else:
                    ornt = "v"
        # Store the initial defaults
        ui.callAfter(self._setDefaultSizerProps)

    def getChildrenPropDict(self, clsChildren=None):
        """LayoutPanels cannot have children."""
        return []

    def _setDefaultSizerProps(self):
        if not self:
            return
        try:
            self._defaultSizerProps = self.ControllingSizer.getItemProps(self)
        except AttributeError:
            self._defaultSizerProps = {}

    def getDesignerDict(
        self,
        itemNum=0,
        allProps=False,
        classID=None,
        classDict=None,
        propsToExclude=None,
    ):
        # Augment the default to add non-Property values
        ret = super(LayoutPanel, self).getDesignerDict(
            itemNum, allProps=allProps, classID=classID, classDict=classDict
        )
        if self.ControllingSizer:
            itmProps = self.ControllingSizer.getItemProps(self.ControllingSizerItem)
            itmDiffProps = self._diffSizerItemProps(itmProps, self.ControllingSizer)
        else:
            itmDiffProps = {}
        ret["attributes"]["sizerInfo"] = itmDiffProps
        return ret

    def setMouseHandling(self, turnOn):
        """When turnOn is True, sets all the mouse event bindings. When
        it is False, removes the bindings.
        """
        if turnOn:
            self.bindEvent(events.MouseMove, self.handleMouseMove)
        else:
            self.unbindEvent(events.MouseMove)

    def handleMouseMove(self, evt):
        if evt.dragging:
            # Need to change the cursor
            # Let the form know
            self.Form.onMouseDrag(evt)
        else:
            self.Form.DragObject = None

    def onMouseLeftUp(self, evt):
        self.Form.processLeftUp(self, evt)
        evt.stop()

    def onMouseLeftDown(self, evt):
        evt.stop()

    #     def onMouseLeftClick(self, evt):
    #         shift = evt.EventData["shiftDown"]
    #         self.Form.objectClick(self, shift)

    def onSelect(self, evt):
        print("PANEL ON SELECT")

    def onContextMenu(self, evt):
        if isinstance(self.Parent, dPage):
            self.Parent.activePanel = self
        pop = self.createContextMenu()
        ui.callAfter(self.showContextMenu, pop)
        evt.stop()

    def createContextMenu(self):
        pop = self.Controller.getControlMenu(self)
        if isinstance(self.Parent, (dPage, dPanel)):
            if not self.Parent is self.Form.mainPanel:
                if len(self.Parent.Children) == 1:
                    sepAdded = False
                    if isinstance(self.Parent, dPage):
                        # Add option to delete the entire pageframe
                        pop.prependSeparator()
                        sepAdded = True
                        pop.prepend(
                            _("Delete the entire Paged Control"),
                            OnHit=self.onDeleteGrandParent,
                        )
                        prmpt = _("Delete this Page")
                    elif isinstance(self.Parent, dPanel):
                        prmpt = _("Delete this Panel")
                    # This is the only item
                    if not sepAdded:
                        pop.prependSeparator()
                    pop.prepend(prmpt, OnHit=self.onDeleteParent)
        if self.Controller.Clipboard:
            pop.prependSeparator()
            pop.prepend(_("Paste"), OnHit=self.onPaste)
        if not isinstance(self.ControllingSizer, LayoutGridSizer):
            pop.append(_("Delete this Slot"), OnHit=self.onDelete)

        self.Controller.addSlotOptions(self, pop, sepBefore=True)
        # Add the Sizer editing option
        pop.appendSeparator()
        pop.append(_("Edit Sizer Settings"), OnHit=self.onEditSizer)
        pop.appendSeparator()
        pop.append(_("Add Controls from Data Environment"), OnHit=self.Form.onRunLayoutWiz)
        return pop

    def onEditSizer(self, evt):
        """Called when the user selects the context menu option
        to edit this slot's sizer information.
        """
        self.Controller.editSizerSettings(self)

    def onCut(self, evt):
        """Place a copy of this control on the Controller clipboard,
        and then delete the control
        """
        self.Controller.copyObject(self)
        self.onDelete(evt)

    def onCopy(self, evt):
        """Place a copy of this control on the Controller clipboard"""
        self.Controller.copyObject(self)

    def onPaste(self, evt):
        self.Controller.pasteObject(self)

    def onDeleteParent(self, evt):
        """Called when this panel is the only object on its parent."""
        self.Parent.onDelete(evt)

    def onDeleteGrandParent(self, evt):
        """Called when the user wants to delete the control that contains
        the page that this panel is on.
        """
        self.Parent.Parent.onDelete(evt)

    def onDelete(self, evt):
        """This is called when the user wants to remove the slot
        represented by this panel. This is only allowed for
        box-type sizers, not grid sizers.
        """
        csz = self.ControllingSizer
        if csz and isinstance(csz, LayoutSizerMixin):
            csz.delete(self, refill=False)

    def crawlUp(self, obj, lev=0):
        pp = obj.Parent
        if pp is None or (pp is self.Form):
            return lev
        else:
            if isinstance(pp, LayoutPanel):
                lev += 1
            ret = self.crawlUp(pp, lev)
            return ret

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

    def _getDesEvents(self):
        return []

    def _getDesProps(self):
        return {
            "BackColor": {"type": "color", "readonly": False},
            "Visible": {"type": bool, "readonly": False},
        }

    def _getSel(self):
        return self._selected

    def _setSel(self, val):
        if self._selected != val:
            if val:
                self._innerPanel.BackColor = self.hiliteColor
                self.BackColor = self.hiliteBorder
            else:
                self._innerPanel.BackColor = self.normalColor
                self.BackColor = self.normalBorder
        self._selected = val

    def _getSzBorder(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Border")

    def _setSzBorder(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Border", val)

    def _getSzBorderSides(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "BorderSides")

    def _setSzBorderSides(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "BorderSides", val)

    def _getSzExpand(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Expand")

    def _setSzExpand(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Expand", val)

    def _getSzColExpand(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "ColExpand")

    def _setSzColExpand(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "ColExpand", val)

    def _getSzColSpan(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "ColSpan")

    def _setSzColSpan(self, val):
        if val == self._getSzColSpan():
            return
        cs = self.ControllingSizer
        try:
            cs.setItemProp(self, "ColSpan", val)
        except ui.GridSizerSpanException as e:
            raise PropertyUpdateException(ustr(e))

    def _getSzRowExpand(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "RowExpand")

    def _setSzRowExpand(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "RowExpand", val)

    def _getSzRowSpan(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "RowSpan")

    def _setSzRowSpan(self, val):
        if val == self._getSzRowSpan():
            return
        cs = self.ControllingSizer
        try:
            cs.setItemProp(self, "RowSpan", val)
        except ui.GridSizerSpanException as e:
            raise PropertyUpdateException(ustr(e))

    def _getSzProp(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Proportion")

    def _setSzProp(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Proportion", val)

    def _getSzHalign(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Halign")

    def _setSzHalign(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Halign", val)

    def _getSzValign(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Valign")

    def _setSzValign(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Valign", val)

    Controller = property(
        _getController,
        _setController,
        None,
        _("Object to which this one reports events  (object (varies))"),
    )

    DesignerEvents = property(
        _getDesEvents,
        None,
        None,
        _(
            """Returns a list of the most common events for the control.
            This will determine which events are displayed in the PropSheet
            for the developer to attach code to.  (list)"""
        ),
    )

    DesignerProps = property(
        _getDesProps,
        None,
        None,
        _(
            """Returns a dict of editable properties for the sizer, with the
            prop names as the keys, and the value for each another dict,
            containing the following keys: 'type', which controls how to display
            and edit the property, and 'readonly', which will prevent editing
            when True. (dict)"""
        ),
    )

    Selected = property(
        _getSel,
        _setSel,
        None,
        _("Denotes if this panel is selected for user interaction.  (bool)"),
    )

    Sizer_Border = property(
        _getSzBorder,
        _setSzBorder,
        None,
        _("Border setting of controlling sizer item  (int)"),
    )

    Sizer_BorderSides = property(
        _getSzBorderSides,
        _setSzBorderSides,
        None,
        _("To which sides is the border applied? (default=All  (str)"),
    )

    Sizer_Expand = property(
        _getSzExpand,
        _setSzExpand,
        None,
        _("Expand setting of controlling sizer item  (bool)"),
    )

    Sizer_ColExpand = property(
        _getSzColExpand,
        _setSzColExpand,
        None,
        _("Column Expand setting of controlling grid sizer item  (bool)"),
    )

    Sizer_ColSpan = property(
        _getSzColSpan,
        _setSzColSpan,
        None,
        _("Column Span setting of controlling grid sizer item  (int)"),
    )

    Sizer_RowExpand = property(
        _getSzRowExpand,
        _setSzRowExpand,
        None,
        _("Row Expand setting of controlling grid sizer item  (bool)"),
    )

    Sizer_RowSpan = property(
        _getSzRowSpan,
        _setSzRowSpan,
        None,
        _("Row Span setting of controlling grid sizer item  (int)"),
    )

    Sizer_Proportion = property(
        _getSzProp,
        _setSzProp,
        None,
        _("Proportion setting of controlling sizer item  (int)"),
    )

    Sizer_HAlign = property(
        _getSzHalign,
        _setSzHalign,
        None,
        _("Horiz. Alignment setting of controlling sizer item  (choice)"),
    )

    Sizer_VAlign = property(
        _getSzValign,
        _setSzValign,
        None,
        _("Vert. Alignment setting of controlling sizer item  (choice)"),
    )


class LayoutSpacerPanel(LayoutPanel):
    def __init__(self, parent, properties=None, orient=None, inGrid=False, *args, **kwargs):
        kwargs["AutoSizer"] = False
        self._spacing = 10
        self._orient = orient
        self._inGrid = inGrid
        super(LayoutSpacerPanel, self).__init__(parent, properties=properties, *args, **kwargs)

    def afterInit(self):
        super(LayoutSpacerPanel, self).afterInit()
        self.AlwaysResetSizer = False
        self.Size = self.SpacingSize
        # Change these to make them different than LayoutPanels
        self.normalColor = "antiquewhite"
        self._innerPanel.BackColor = self.normalColor
        self.normalBorder = "black"
        self.hiliteColor = "white"
        self.BackColor = self.normalBorder
        # Set up sizer defaults
        addSizerDefaults(
            {
                self.__class__: {
                    "G": {
                        "BorderSides": ["All"],
                        "Proportion": 0,
                        "HAlign": "Center",
                        "VAlign": "Middle",
                        "Border": 70,
                        "Expand": False,
                        "RowExpand": False,
                        "ColExpand": False,
                    },
                    "H": {
                        "BorderSides": ["All"],
                        "Proportion": 0,
                        "HAlign": "Left",
                        "VAlign": "Middle",
                        "Border": 80,
                        "Expand": False,
                    },
                    "V": {
                        "BorderSides": ["All"],
                        "Proportion": 0,
                        "HAlign": "Center",
                        "VAlign": "Top",
                        "Border": 90,
                        "Expand": False,
                    },
                }
            }
        )

    def onContextMenu(self, evt):
        if isinstance(self.Parent, dPage):
            self.Parent.activePanel = self
        pop = dMenu()
        pop.prepend(_("Delete"), OnHit=self.onDelete)
        pop.prepend(_("Copy"), OnHit=self.onCopy)
        pop.prepend(_("Cut"), OnHit=self.onCut)
        self.Controller.addSlotOptions(self, pop, sepBefore=True)
        # Add the Sizer editing option
        pop.appendSeparator()
        pop.append(_("Edit Sizer Settings"), OnHit=self.onEditSizer)
        ui.callAfter(self.showContextMenu, pop)
        evt.stop()

    def onDelete(self, evt):
        # The user wants to remove the spacer.
        prnt = self.Parent
        cs = self.ControllingSizer
        pos = self.getPositionInSizer()
        try:
            sizerAtts = self.getDesignerDict()["attributes"]["sizerInfo"]
        except KeyError:
            sizerAtts = None
        cs.remove(self)
        ui.callAfter(self.release)
        lp = LayoutPanel(prnt, AutoSizer=False)
        if isinstance(cs, LayoutGridSizer):
            rr, cc = pos
            cs.append(lp, row=rr, col=cc)
        else:
            cs.insert(pos, lp, 1, "x")
        csi = lp.ControllingSizerItem
        cs.setItemProps(csi, sizerAtts)
        self.Controller.select(lp)
        ui.callAfter(self.Form.updateApp)

    def _getDesProps(self):
        return {"Spacing": {"type": int, "readonly": False}}

    def _getSpacing(self):
        return self._spacing

    def _setSpacing(self, val):
        self._spacing = val
        self.Size = self.SpacingSize

    def _getSpacingSize(self):
        spc = self._spacing
        if self._inGrid or self._orient is None:
            ret = (spc, spc)
        else:
            fillerDim = min(25, spc)
            if self._orient.lower()[0] == "v":
                ret = (fillerDim, spc)
            else:
                ret = (spc, fillerDim)
        return ret

    DesignerProps = property(
        _getDesProps,
        None,
        None,
        _(
            """Returns a dict of editable properties for the sizer, with the
            prop names as the keys, and the value for each another dict,
            containing the following keys: 'type', which controls how to display
            and edit the property, and 'readonly', which will prevent editing
            when True. (dict)"""
        ),
    )

    Spacing = property(
        _getSpacing,
        _setSpacing,
        None,
        _("Allocated space for the spacer this represents  (tuple of int)"),
    )

    SpacingSize = property(
        _getSpacingSize,
        None,
        None,
        _("Size of this spacer panel, based on the spacing  (tuple)"),
    )


class LayoutSizerMixin(LayoutSaverMixin):
    def __init__(self, *args, **kwargs):
        self.isDesignerSizer = True
        self._selected = False
        super(LayoutSizerMixin, self).__init__(*args, **kwargs)

    def _afterInit(self):
        super(LayoutSizerMixin, self)._afterInit()
        # No special reason for these choices, except that they make the
        # sizer clearly visible.
        self.outlineColor = "ORCHID"
        self.outlineStyle = "solid"
        self.outlineWidth = 2

    def getItemProps(self, itm):
        """Return a dict containing the sizer item properties as keys, with
        their associated values. Must override in each subclass.
        """
        ret = {}
        for prop in list(self.ItemDesignerProps.keys()):
            ret[prop] = self.getItemProp(itm, prop)
        ret["Expand"] = self.getItemProp(itm, "Expand")
        ret["Proportion"] = self.getItemProp(itm, "Proportion")
        return ret

    def getChildrenPropDict(self, clsChildren=None):
        ret = []
        kids = self.Children
        if isinstance(self, dSizer):
            try:
                szParent = self.Parent
            except RuntimeError:
                szParent = None
            if isinstance(szParent, WizardPage):
                # Skip the built-in title and separator line.
                # The sizer contains other things, such as spacers, so we need
                # to find the sizeritem that matches an actual child object.
                actualKids = self.Parent.Children
                found = False
                for pos, szitm in enumerate(kids):
                    itm = self.getItem(szitm)
                    if (itm in actualKids) or isinstance(itm, (LayoutGridSizer, LayoutSizer)):
                        found = True
                        kids = kids[pos:]
                        break
                if not found:
                    kids = []
        # Are we inside a class definition?
        insideClass = clsChildren is not None
        if insideClass:
            childDict = clsChildren.get("children", [])
        if isinstance(self, dGridSizer):
            szType = "Grid"
        else:
            try:
                szType = self.Orientation
            except AttributeError:
                szType = None
        for kid in kids:
            isSpacer = False
            numItems = len(ret)
            itmDict = {}
            for prop in list(self.ItemDesignerProps.keys()):
                itmDict[prop] = self.getItemProp(kid, prop)
            kidItem = self.getItem(kid)
            try:
                defProps = self.Controller.getDefaultSizerProps(kidItem.superControl, szType)
                itmDiffDict = self._diffSizerItemProps(itmDict, defProps, direct=True)
            except AttributeError:
                itmDiffDict = self._diffSizerItemProps(itmDict, self)
            if kidItem in self.ChildWindows:
                winDict = None
                if insideClass:
                    try:
                        winID = kidItem.classID
                        try:
                            winDict = [
                                cd for cd in childDict if cd["attributes"]["classID"] == winID
                            ][0]
                        except Exception as e:
                            winDict = {}
                    except AttributeError:
                        winDict = {}
                kidDict = kidItem.getDesignerDict(itemNum=numItems, classDict=winDict)

            elif kidItem in self.ChildSizers:
                szrDict = None
                if insideClass:
                    try:
                        szrID = kidItem.classID
                        try:
                            szrDict = [
                                cd for cd in childDict if cd["attributes"]["classID"] == szrID
                            ][0]
                        except Exception as e:
                            szrDict = {}
                    except AttributeError:
                        szrDict = {}

                kidDict = kidItem.getDesignerDict(itemNum=numItems, classDict=szrDict)
            else:
                # Spacer
                isSpacer = True
                if self.Orientation.lower()[0] == "v":
                    pos = 1
                else:
                    pos = 0
                try:
                    spc = kidItem.Spacing
                except AttributeError:
                    spc = 0
                kidDict = {
                    "name": "Spacer",
                    "attributes": {"size": spc, "Name": "spacer"},
                    "cdata": "",
                    "children": [],
                }
            # Add the sizer item info to the item contents
            if not isSpacer and not ("sizerInfo" in kidDict["attributes"]):
                kidDict["attributes"]["sizerInfo"] = itmDiffDict
            # Add to the result
            ret.append(kidDict)
        return ret

    def createContextMenu(self):
        pop = dMenu()
        isMain = self.ControllingSizer is None and isinstance(self.Parent, (dForm, dFormMain))
        if not isMain:
            pop.append(_("Cut"), OnHit=self.Controller.onTreeCut)
        pop.append(_("Copy"), OnHit=self.Controller.onTreeCopy)
        if not isMain:
            # Don't delete the main sizer for the form.
            pop.appendSeparator()
            pop.append(_("Delete"), OnHit=self.Controller.onTreeDelete)
        if self.Orientation == "Horizontal":
            pop.append(_("Make Vertical"), OnHit=self.Controller.onSwitchOrientation)
        elif self.Orientation == "Vertical":
            pop.append(_("Make Horizontal"), OnHit=self.Controller.onSwitchOrientation)
        if isinstance(self, dBorderSizer):
            prm = _("Remove Sizer Box")
        else:
            prm = _("Add Sizer Box")
        pop.append(prm, OnHit=self.Controller.onTreeSwitchSizerType)
        pop.appendSeparator()
        pop.append(_("Edit Sizer Settings"), OnHit=self.onEditSizer)
        self.Controller.addSlotOptions(self, pop, sepBefore=True)
        return pop

    def onEditSizer(self, evt):
        """Called when the user selects the context menu option
        to edit this slot's sizer information.
        """
        self.Controller.editSizerSettings(self)

    def onCut(self, evt):
        """Place a copy of this sizer on the Controller clipboard,
        and then delete the sizer
        """
        self.Controller.copyObject(self)
        if self.ControllingSizer is not None:
            self.ControllingSizer.delete(self)
        else:
            self.release(True)
        ui.callAfter(self.Controller.updateLayout)

    def onCopy(self, evt):
        """Place a copy of this control on the Controller clipboard"""
        self.Controller.copyObject(self)

    def onPaste(self, evt):
        self.Controller.pasteObject(self)

    def delete(self, obj, refill=True):
        """Delete the specified object. Add a replacement layout
        panel unless refill is False.
        """
        itm = obj.ControllingSizerItem
        prnt = obj.Parent
        pos = obj.getPositionInSizer()
        # Store all the sizer settings
        szitVals = self.getItemProps(itm)
        self.remove(obj)
        if refill:
            lp = LayoutPanel(prnt, AutoSizer=False)
            self.insert(pos, lp, 1, "x")
        if isinstance(obj, (LayoutSizerMixin, LayoutGridSizer)):
            ui.callAfter(obj.release, True)
        else:
            ui.callAfter(obj.release)
        ui.callAfter(self.Controller.updateLayout)

    def _updateChildBorderSides(self):
        """Set the BorderSides property for each child to match the default setting."""
        val = []
        if self.DefaultBorderBottom:
            val.append("Bottom")
        if self.DefaultBorderLeft:
            val.append("Left")
        if self.DefaultBorderRight:
            val.append("Right")
        if self.DefaultBorderTop:
            val.append("Top")
        if not val:
            val = ["All"]
        for itm in self.Children:
            self.setItemProp(itm, "BorderSides", val)

    def _getDefaultBorder(self):
        return super(LayoutSizerMixin, self)._getDefaultBorder()

    def _setDefaultBorder(self, val):
        """The idea here is to propagate the DefaultBorder setting to all child
        objects, instead of just future additions.
        """
        super(LayoutSizerMixin, self)._setDefaultBorder(val)
        if self.Controller._propagateDefaultBorder:
            for itm in self.Children:
                self.setItemProp(itm, "Border", val)

    def _getDefaultBorderAll(self):
        return super(LayoutSizerMixin, self)._getDefaultBorderAll()

    def _setDefaultBorderAll(self, val):
        """The idea here is to propagate the DefaultBorderAll setting to all child
        objects, instead of just future additions.
        """
        super(LayoutSizerMixin, self)._setDefaultBorderAll(val)
        if self.Controller._propagateDefaultBorder:
            self._updateChildBorderSides()

    def _getDefaultBorderBottom(self):
        return super(LayoutSizerMixin, self)._getDefaultBorderBottom()

    def _setDefaultBorderBottom(self, val):
        """The idea here is to propagate the DefaultBorderBottom setting to all child
        objects, instead of just future additions.
        """
        super(LayoutSizerMixin, self)._setDefaultBorderBottom(val)
        if self.Controller._propagateDefaultBorder:
            self._updateChildBorderSides()

    def _getDefaultBorderLeft(self):
        return super(LayoutSizerMixin, self)._getDefaultBorderLeft()

    def _setDefaultBorderLeft(self, val):
        """The idea here is to propagate the DefaultBorderLeft setting to all child
        objects, instead of just future additions.
        """
        super(LayoutSizerMixin, self)._setDefaultBorderLeft(val)
        if self.Controller._propagateDefaultBorder:
            self._updateChildBorderSides()

    def _getDefaultBorderRight(self):
        return super(LayoutSizerMixin, self)._getDefaultBorderRight()

    def _setDefaultBorderRight(self, val):
        """The idea here is to propagate the DefaultBorderRight setting to all child
        objects, instead of just future additions.
        """
        super(LayoutSizerMixin, self)._setDefaultBorderRight(val)
        if self.Controller._propagateDefaultBorder:
            self._updateChildBorderSides()

    def _getDefaultBorderTop(self):
        return super(LayoutSizerMixin, self)._getDefaultBorderTop()

    def _setDefaultBorderTop(self, val):
        """The idea here is to propagate the DefaultBorderTop setting to all child
        objects, instead of just future additions.
        """
        super(LayoutSizerMixin, self)._setDefaultBorderTop(val)
        if self.Controller._propagateDefaultBorder:
            self._updateChildBorderSides()

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

    def _getDesEvents(self):
        return []

    def _getDesProps(self):
        ret = {
            "Orientation": {
                "type": list,
                "readonly": False,
                "values": ["Horizontal", "Vertical"],
            },
            "DefaultBorder": {"type": int, "readonly": False},
            "DefaultBorderLeft": {"type": bool, "readonly": False},
            "DefaultBorderRight": {"type": bool, "readonly": False},
            "DefaultBorderTop": {"type": bool, "readonly": False},
            "DefaultBorderBottom": {"type": bool, "readonly": False},
            "DefaultSpacing": {"type": int, "readonly": False},
            "SlotCount": {"type": int, "readonly": False},
        }
        # Add the controlling sizer props, if applicable
        if self.ControllingSizer:
            ret.update(
                {
                    "Sizer_Border": {"type": int, "readonly": False},
                    "Sizer_BorderSides": {
                        "type": list,
                        "readonly": False,
                        "values": ["All", "Top", "Bottom", "Left", "Right", "None"],
                        "customEditor": "editBorderSides",
                    },
                    "Sizer_Expand": {"type": bool, "readonly": False},
                    "Sizer_Proportion": {"type": int, "readonly": False},
                    "Sizer_HAlign": {
                        "type": list,
                        "readonly": False,
                        "values": ["Left", "Right", "Center"],
                    },
                    "Sizer_VAlign": {
                        "type": list,
                        "readonly": False,
                        "values": ["Top", "Bottom", "Middle"],
                    },
                }
            )
            if isinstance(self.ControllingSizer, dGridSizer):
                ret.update(
                    {
                        "Sizer_RowExpand": {"type": bool, "readonly": False},
                        "Sizer_ColExpand": {"type": bool, "readonly": False},
                        "Sizer_RowSpan": {"type": int, "readonly": False},
                        "Sizer_ColSpan": {"type": int, "readonly": False},
                    }
                )
        return ret

    def _getSel(self):
        return self._selected

    def _setSel(self, val):
        if self._selected != val:
            frm = None
            obj = self
            while obj.Parent:
                try:
                    frm = obj.Parent.Form
                    break
                except AttributeError:
                    pass
                obj = obj.Parent
            if frm:
                if val:
                    frm.addToOutlinedSizers(self)
                else:
                    frm.removeFromOutlinedSizers(self)
        self._selected = val

    def _getSzItmProps(self):
        return {
            "Border": {"type": int, "readonly": False},
            "BorderSides": {
                "type": list,
                "readonly": False,
                "values": ["All", "Top", "Bottom", "Left", "Right", "None"],
                "customEditor": "editBorderSides",
            },
            "Proportion": {"type": int, "readonly": False},
            "HAlign": {
                "type": list,
                "readonly": False,
                "values": ["Left", "Right", "Center"],
            },
            "VAlign": {
                "type": list,
                "readonly": False,
                "values": ["Top", "Bottom", "Middle"],
            },
            "Expand": {"type": bool, "readonly": False},
        }

    def _getSzBorder(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Border")

    def _setSzBorder(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Border", val)

    def _getSzBorderSides(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "BorderSides")

    def _setSzBorderSides(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "BorderSides", val)

    def _getSzExpand(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Expand")

    def _setSzExpand(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Expand", val)

    def _getSzColExpand(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "ColExpand")

    def _setSzColExpand(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "ColExpand", val)

    def _getSzColSpan(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "ColSpan")

    def _setSzColSpan(self, val):
        if val == self._getSzColSpan():
            return
        try:
            self.ControllingSizer.setItemProp(self, "ColSpan", val)
        except ui.GridSizerSpanException as e:
            raise PropertyUpdateException(ustr(e))

    def _getSzRowExpand(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "RowExpand")

    def _setSzRowExpand(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "RowExpand", val)

    def _getSzRowSpan(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "RowSpan")

    def _setSzRowSpan(self, val):
        if val == self._getSzRowSpan():
            return
        try:
            self.ControllingSizer.setItemProp(self, "RowSpan", val)
        except ui.GridSizerSpanException as e:
            raise PropertyUpdateException(ustr(e))

    def _getSzProp(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Proportion")

    def _setSzProp(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Proportion", val)

    def _getSzHalign(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Halign")

    def _setSzHalign(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Halign", val)

    def _getSzValign(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Valign")

    def _setSzValign(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Valign", val)

    def _getSlotCount(self):
        return len(self.Children)

    def _setSlotCount(self, val):
        cnt = len(self.Children)
        if val > cnt:
            # Need to add enough LayoutPanels to make up the difference
            for ii in range(val - cnt):
                lp = LayoutPanel(self.Parent, AutoSizer=False)
                self.append1x(lp)
            self.layout()
        elif cnt > val:
            # Remove items from the 'end' to bring the count down.
            for ii in range(cnt - val):
                obj = self.getItem(self.Children[-1])
                if obj in self.ChildWindows:
                    self.remove(obj, True)
                elif obj in self.ChildSizers:
                    self.remove(obj)
                    obj.release(True)

    Controller = property(
        _getController,
        _setController,
        None,
        _("Object to which this one reports events  (object (varies))"),
    )

    DefaultBorder = property(
        _getDefaultBorder,
        _setDefaultBorder,
        None,
        _(
            """Not only changes the current setting, but goes back and applies
            it to all existing children  (int)"""
        ),
    )

    DefaultBorderAll = property(
        _getDefaultBorderAll,
        _setDefaultBorderAll,
        None,
        _(
            """Not only changes the current setting, but goes back and applies
            it to all existing children  (bool)"""
        ),
    )

    DefaultBorderBottom = property(
        _getDefaultBorderBottom,
        _setDefaultBorderBottom,
        None,
        _(
            """Not only changes the current setting, but goes back and applies
            it to all existing children  (bool)"""
        ),
    )

    DefaultBorderLeft = property(
        _getDefaultBorderLeft,
        _setDefaultBorderLeft,
        None,
        _(
            """Not only changes the current setting, but goes back and applies
            it to all existing children  (bool)"""
        ),
    )

    DefaultBorderRight = property(
        _getDefaultBorderRight,
        _setDefaultBorderRight,
        None,
        _(
            """Not only changes the current setting, but goes back and applies
            it to all existing children  (bool)"""
        ),
    )

    DefaultBorderTop = property(
        _getDefaultBorderTop,
        _setDefaultBorderTop,
        None,
        _(
            """Not only changes the current setting, but goes back and applies
            it to all existing children  (bool)"""
        ),
    )

    DesignerEvents = property(
        _getDesEvents,
        None,
        None,
        _(
            """Returns a list of the most common events for the control.
            This will determine which events are displayed in the PropSheet
            for the developer to attach code to.  (list)"""
        ),
    )

    DesignerProps = property(
        _getDesProps,
        None,
        None,
        _(
            """Returns a dict of editable properties for the sizer, with the
            prop names as the keys, and the value for each another dict,
            containing the following keys: 'type', which controls how to display
            and edit the property, and 'readonly', which will prevent editing
            when True. (dict)"""
        ),
    )

    ItemDesignerProps = property(
        _getSzItmProps,
        None,
        None,
        _(
            """When the selected object in the ClassDesigner is a sizer item, we
            need to be able to get the items properties. Since we can't
            subclass the sizer item, custom stuff like this will always have to
            be done through the sizer class.  (dict)"""
        ),
    )

    Selected = property(
        _getSel,
        _setSel,
        None,
        _("Denotes if this sizer is selected for user interaction.  (bool)"),
    )

    Sizer_Border = property(
        _getSzBorder,
        _setSzBorder,
        None,
        _("Border setting of controlling sizer item  (int)"),
    )

    Sizer_BorderSides = property(
        _getSzBorderSides,
        _setSzBorderSides,
        None,
        _("To which sides is the border applied? (default=All  (str)"),
    )

    Sizer_Expand = property(
        _getSzExpand,
        _setSzExpand,
        None,
        _("Expand setting of controlling sizer item  (bool)"),
    )

    Sizer_ColExpand = property(
        _getSzColExpand,
        _setSzColExpand,
        None,
        _("Column Expand setting of controlling grid sizer item  (bool)"),
    )

    Sizer_ColSpan = property(
        _getSzColSpan,
        _setSzColSpan,
        None,
        _("Column Span setting of controlling grid sizer item  (int)"),
    )

    Sizer_RowExpand = property(
        _getSzRowExpand,
        _setSzRowExpand,
        None,
        _("Row Expand setting of controlling grid sizer item  (bool)"),
    )

    Sizer_RowSpan = property(
        _getSzRowSpan,
        _setSzRowSpan,
        None,
        _("Row Span setting of controlling grid sizer item  (int)"),
    )

    Sizer_Proportion = property(
        _getSzProp,
        _setSzProp,
        None,
        _("Proportion setting of controlling sizer item  (int)"),
    )

    Sizer_HAlign = property(
        _getSzHalign,
        _setSzHalign,
        None,
        _("Horiz. Alignment setting of controlling sizer item  (choice)"),
    )

    Sizer_VAlign = property(
        _getSzValign,
        _setSzValign,
        None,
        _("Vert. Alignment setting of controlling sizer item  (choice)"),
    )

    SlotCount = property(
        _getSlotCount,
        _setSlotCount,
        None,
        _("Number of slots available in this sizer.  (int)"),
    )


class LayoutSizer(LayoutSizerMixin, dSizer):
    def __init__(self, *args, **kwargs):
        super(LayoutSizer, self).__init__(*args, **kwargs)

    def getBorderedClass(self):
        """Return the class that is the border sizer version of this class."""
        return LayoutBorderSizer


class LayoutBorderSizer(LayoutSizerMixin, dBorderSizer):
    def __init__(self, box, caption=None, *args, **kwargs):
        if not isinstance(box, dBox):
            # parent passed
            boxClass = self.Controller.getControlClass(dBox)
            box = boxClass(box)
        if caption is not None:
            box.Caption = caption
        super(LayoutBorderSizer, self).__init__(box, *args, **kwargs)

    def getNonBorderedClass(self):
        """Return the class that is the non-border sizer version of this class."""
        return LayoutSizer

    def _getDesProps(self):
        ret = super(LayoutBorderSizer, self)._getDesProps()
        ret.update(
            {
                "Caption": {"type": str, "readonly": False},
                "BackColor": {
                    "type": "color",
                    "readonly": False,
                    "customEditor": "editColor",
                },
                "FontBold": {"type": bool, "readonly": False},
                "FontFace": {
                    "type": list,
                    "readonly": False,
                    "values": ui.getAvailableFonts(),
                },
                "FontItalic": {"type": bool, "readonly": False},
                "FontSize": {"type": int, "readonly": False},
                "FontUnderline": {"type": bool, "readonly": False},
            }
        )
        return ret

    DesignerProps = property(
        _getDesProps,
        None,
        None,
        _(
            """Returns a dict of editable properties for the sizer, with the
            prop names as the keys, and the value for each another dict,
            containing the following keys: 'type', which controls how to display
            and edit the property, and 'readonly', which will prevent editing
            when True. (dict)"""
        ),
    )


class LayoutGridSizer(LayoutSizerMixin, dGridSizer):
    def __init__(self, *args, **kwargs):
        super(LayoutGridSizer, self).__init__(*args, **kwargs)
        self._rows = self._cols = 0

    def setItemProps(self, itm, props):
        """This accepts a dict of properties and values, and
        applies them to the specified sizer item.
        """
        # Do the default behavior
        for prop, val in list(props.items()):
            currVal = self.getItemProp(itm, prop)
            if val != currVal:
                self.setItemProp(itm, prop, val)

    def getItemProps(self, itm):
        """Return a dict containing the sizer item properties as keys, with
        their associated values. Must override in each subclass.
        """
        ret = {}
        for prop in list(self.ItemDesignerProps.keys()):
            ret[prop] = self.getItemProp(itm, prop)
        return ret

    def switchObjects(self, obj1, obj2):
        """Swaps the location of the two objects."""
        if not obj1 or not obj2:
            dabo_module.error(_("Cannot swap with non-existent object."))
            return
        row1, col1 = self.getGridPos(obj1)
        row2, col2 = self.getGridPos(obj2)
        props = self.getItemProps(obj1)
        self.remove(obj1)
        self.moveObject(obj2, row1, col1)
        self.append(obj1, row=row2, col=col2)
        self.setItemProps(obj1, props)
        self.layout()

    def createContextMenu(self):
        pop = dMenu()
        isMain = self.ControllingSizer is None and isinstance(self.Parent, (dForm, dFormMain))
        if not isMain:
            pop.append(_("Cut"), OnHit=self.Controller.onTreeCut)
        pop.append(_("Copy"), OnHit=self.Controller.onTreeCopy)
        if not isMain:
            # Don't delete the main sizer for the form.
            pop.appendSeparator()
            pop.append(_("Delete"), OnHit=self.Controller.onTreeDelete)
            pop.appendSeparator()
            pop.append(_("Edit Sizer Settings"), OnHit=self.onEditSizer)
            self.Controller.addSlotOptions(self, pop, sepBefore=True)
        return pop

    def onEditSizer(self, evt):
        """Called when the user selects the context menu option
        to edit this slot's sizer information.
        """
        self.Controller.editSizerSettings(self)

    def getChildrenPropDict(self, clsChildren=None):
        ret = []
        kids = self.Children
        # Are we inside a class definition?
        insideClass = clsChildren is not None
        if insideClass:
            childDict = clsChildren.get("children", [])
        for kid in kids:
            numItems = len(ret)
            itmDict = {}
            clsDict = None
            if insideClass:
                clsDict = self.getChildClassDict(clsChildren, kid)

            # Make sure that the clsDict is not None.
            clsDict = clsDict or {}
            for prop in list(self.ItemDesignerProps.keys()):
                itmDict[prop] = self.getItemProp(kid, prop)
            itmDiffDict = self._diffSizerItemProps(itmDict, self)
            kidItem = self.getItem(kid)
            if not kidItem in self.ChildSpacers:
                kidDict = kidItem.getDesignerDict(itemNum=numItems, classDict=clsDict)
            else:
                # Spacer
                spc = kid.GetSpacer()
                kidDict = {
                    "name": self.serialName("Spacer", numItems),
                    "attributes": {},
                    "cdata": kidItem.Spacing,
                    "children": [],
                }
            # Save the position
            kidDict["attributes"]["rowColPos"] = self.getGridPos(kid)
            # Add the sizer item info to the item contents
            if not kidDict["attributes"].get("sizerInfo"):
                kidDict["attributes"]["sizerInfo"] = itmDiffDict
            # Add to the result
            ret.append(kidDict)
        return ret

    def getChildClassDict(self, clsChildren, itm):
        ret = None
        obj = self.getItem(itm)
        if obj in (self.ChildSpacers):
            # spacer; ignore
            return ret
        try:
            objID = obj.classID
            try:
                ret = [cd for cd in childDict if cd["attributes"]["classID"] == objID][0]
            except Exception as e:
                ret = None
        except AttributeError:
            pass
        return ret

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def onCut(self, evt):
        """Place a copy of this sizer on the Controller clipboard,
        and then delete the sizer
        """
        self.Controller.copyObject(self)
        if self.ControllingSizer is not None:
            self.ControllingSizer.delete(self)
        else:
            self.release(True)
        ui.callAfter(self.Controller.updateLayout)

    def onCopy(self, evt):
        """Place a copy of this control on the Controller clipboard"""
        self.Controller.copyObject(self)

    def onPaste(self, evt):
        self.Controller.pasteObject(self)

    def delete(self, obj, refill=True):
        """Delete the specified object. Add a replacement layout
        panel unless refill is False.
        """
        itm = obj.ControllingSizerItem
        prnt = obj.Parent
        pos = obj.getPositionInSizer()
        # Store all the sizer settings
        szitVals = self.getItemProps(itm)
        self.remove(obj)
        if refill:
            lp = LayoutPanel(prnt, AutoSizer=False)
            self.append(lp, "x", row=pos[0], col=pos[1])
        if isinstance(obj, (LayoutSizerMixin, LayoutGridSizer)):
            ui.callAfter(obj.release, True)
        else:
            ui.callAfter(obj.release)
        ui.callAfter(self.Controller.updateLayout)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getColCount(self):
        return self._cols

    def _setColCount(self, val):
        curr = self._cols
        if curr != val:
            self._cols = val
            if val > curr:
                self.MaxCols = val
                prnt = self.Parent
                for cc in range(curr, val):
                    setExpand = False
                    for rr in range(self.Rows):
                        if not self.getItemByRowCol(rr, cc):
                            lp = LayoutPanel(prnt, AutoSizer=False)
                            self.append(lp, "x", row=rr, col=cc)
                            setExpand = True
                    if setExpand:
                        self.setColExpand(True, cc)
            else:
                for cc in range(curr - 1, val - 1, -1):
                    self.removeCol(cc)
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

    def _getDesEvents(self):
        return []

    def _getDesProps(self):
        ret = {
            "MaxDimension": {
                "type": list,
                "readonly": False,
                "values": ["Rows", "Columns"],
            },
            "Rows": {"type": int, "readonly": False},
            "Columns": {"type": int, "readonly": False},
            "HGap": {"type": int, "readonly": False},
            "VGap": {"type": int, "readonly": False},
        }
        # Add the controlling sizer props, if applicable
        if self.ControllingSizer:
            ret.update(
                {
                    "Sizer_Border": {"type": int, "readonly": False},
                    "Sizer_BorderSides": {
                        "type": list,
                        "readonly": False,
                        "values": ["All", "Top", "Bottom", "Left", "Right", "None"],
                        "customEditor": "editBorderSides",
                    },
                    "Sizer_Expand": {"type": bool, "readonly": False},
                    "Sizer_Proportion": {"type": int, "readonly": False},
                    "Sizer_HAlign": {
                        "type": list,
                        "readonly": False,
                        "values": ["Left", "Right", "Center"],
                    },
                    "Sizer_VAlign": {
                        "type": list,
                        "readonly": False,
                        "values": ["Top", "Bottom", "Middle"],
                    },
                }
            )
            if isinstance(self.ControllingSizer, dGridSizer):
                ret.update(
                    {
                        "Sizer_RowExpand": {"type": bool, "readonly": False},
                        "Sizer_ColExpand": {"type": bool, "readonly": False},
                        "Sizer_RowSpan": {"type": int, "readonly": False},
                        "Sizer_ColSpan": {"type": int, "readonly": False},
                    }
                )
        return ret

    def _getSzItmProps(self):
        return {
            "Border": {"type": int, "readonly": False},
            "BorderSides": {
                "type": list,
                "readonly": False,
                "values": ["All", "Top", "Bottom", "Left", "Right", "None"],
                "customEditor": "editBorderSides",
            },
            "Expand": {"type": bool, "readonly": False},
            "RowExpand": {"type": bool, "readonly": False},
            "ColExpand": {"type": bool, "readonly": False},
            "RowSpan": {"type": int, "readonly": False},
            "ColSpan": {"type": int, "readonly": False},
            "Proportion": {"type": int, "readonly": False},
            "HAlign": {
                "type": list,
                "readonly": False,
                "values": ["Left", "Right", "Center"],
            },
            "VAlign": {
                "type": list,
                "readonly": False,
                "values": ["Top", "Bottom", "Middle"],
            },
        }

    def _getRowCount(self):
        return self._rows

    def _setRowCount(self, val):
        curr = self._rows
        if curr != val:
            self._rows = val
            if val > curr:
                self.MaxRows = val
                prnt = self.Parent
                for rr in range(curr, val):
                    setExpand = False
                    for cc in range(self.Columns):
                        if not self.getItemByRowCol(rr, cc):
                            lp = LayoutPanel(prnt, AutoSizer=False)
                            self.append(lp, "x", row=rr, col=cc)
                            setExpand = True
                    if setExpand:
                        self.setRowExpand(True, rr)
            else:
                for rr in range(curr - 1, val - 1, -1):
                    self.removeRow(rr)
            self.layout()

    def _getSzBorder(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Border")

    def _setSzBorder(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Border", val)

    def _getSzBorderSides(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "BorderSides")

    def _setSzBorderSides(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "BorderSides", val)

    def _getSzExpand(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Expand")

    def _setSzExpand(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Expand", val)

    def _getSzColExpand(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "ColExpand")

    def _setSzColExpand(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "ColExpand", val)

    def _getSzColSpan(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "ColSpan")

    def _setSzColSpan(self, val):
        if val == self._getSzColSpan():
            return
        try:
            self.ControllingSizer.setItemProp(self, "ColSpan", val)
        except ui.GridSizerSpanException as e:
            raise PropertyUpdateException(ustr(e))

    def _getSzRowExpand(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "RowExpand")

    def _setSzRowExpand(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "RowExpand", val)

    def _getSzRowSpan(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "RowSpan")

    def _setSzRowSpan(self, val):
        if val == self._getSzRowSpan():
            return
        try:
            self.ControllingSizer.setItemProp(self, "RowSpan", val)
        except ui.GridSizerSpanException as e:
            raise PropertyUpdateException(ustr(e))

    def _getSzProp(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Proportion")

    def _setSzProp(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Proportion", val)

    def _getSzHalign(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Halign")

    def _setSzHalign(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Halign", val)

    def _getSzValign(self):
        return self.ControllingSizer.getItemProp(self.ControllingSizerItem, "Valign")

    def _setSzValign(self, val):
        self.ControllingSizer.setItemProp(self.ControllingSizerItem, "Valign", val)

    Columns = property(
        _getColCount, _setColCount, None, _("Number of columns in this sizer.  (int)")
    )

    Controller = property(
        _getController,
        _setController,
        None,
        _("Object to which this one reports events  (object (varies))"),
    )

    DesignerEvents = property(
        _getDesEvents,
        None,
        None,
        _(
            """Returns a list of the most common events for the control.
            This will determine which events are displayed in the PropSheet
            for the developer to attach code to.  (list)"""
        ),
    )

    DesignerProps = property(
        _getDesProps,
        None,
        None,
        _(
            """Returns a dict of editable properties for the sizer, with the
            prop names as the keys, and the value for each another dict,
            containing the following keys: 'type', which controls how to display
            and edit the property, and 'readonly', which will prevent editing
            when True. (dict)"""
        ),
    )

    ItemDesignerProps = property(
        _getSzItmProps,
        None,
        None,
        _(
            """When the selected object in the ClassDesigner is a sizer item, we
            need to be able to get the items properties. Since we can't
            subclass the sizer item, custom stuff like this will always have to
            be done through the sizer class.  (dict)"""
        ),
    )

    Rows = property(_getRowCount, _setRowCount, None, _("Number of rows in this sizer.  (int)"))

    Sizer_Border = property(
        _getSzBorder,
        _setSzBorder,
        None,
        _("Border setting of controlling sizer item  (int)"),
    )

    Sizer_BorderSides = property(
        _getSzBorderSides,
        _setSzBorderSides,
        None,
        _("To which sides is the border applied? (default=All  (str)"),
    )

    Sizer_Expand = property(
        _getSzExpand,
        _setSzExpand,
        None,
        _("Expand setting of controlling sizer item  (bool)"),
    )

    Sizer_ColExpand = property(
        _getSzColExpand,
        _setSzColExpand,
        None,
        _("Column Expand setting of controlling grid sizer item  (bool)"),
    )

    Sizer_ColSpan = property(
        _getSzColSpan,
        _setSzColSpan,
        None,
        _("Column Span setting of controlling grid sizer item  (int)"),
    )

    Sizer_RowExpand = property(
        _getSzRowExpand,
        _setSzRowExpand,
        None,
        _("Row Expand setting of controlling grid sizer item  (bool)"),
    )

    Sizer_RowSpan = property(
        _getSzRowSpan,
        _setSzRowSpan,
        None,
        _("Row Span setting of controlling grid sizer item  (int)"),
    )

    Sizer_Proportion = property(
        _getSzProp,
        _setSzProp,
        None,
        _("Proportion setting of controlling sizer item  (int)"),
    )

    Sizer_HAlign = property(
        _getSzHalign,
        _setSzHalign,
        None,
        _("Horiz. Alignment setting of controlling sizer item  (choice)"),
    )

    Sizer_VAlign = property(
        _getSzValign,
        _setSzValign,
        None,
        _("Vert. Alignment setting of controlling sizer item  (choice)"),
    )


class LayoutBasePanel(dPanel, LayoutSaverMixin):
    def createContextMenu(self):
        """Only here for compatibility"""
        return

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

    def _getDesProps(self):
        return {"BackColor": {"type": "color", "readonly": False}}

    Controller = property(
        _getController,
        _setController,
        None,
        _("Object to which this one reports events  (object (varies))"),
    )

    DesignerProps = property(_getDesProps, None, None)


class NoSizerBasePanel(LayoutBasePanel):
    """Used in non-sizer based designs as the 'background' panel
    in which all controls are created.
    """

    def afterInit(self):
        self.IsContainer = True

    #         self.bindEvent(events.KeyChar, self.Form.onKeyChar)

    def setMouseHandling(self, turnOn):
        """When turnOn is True, sets all the mouse event bindings. When
        it is False, removes the bindings.
        """
        if turnOn:
            self.bindEvent(events.MouseMove, self.handleMouseMove)
        else:
            self.unbindEvent(events.MouseMove)

    def handleMouseMove(self, evt):
        if evt.dragging:
            # Need to change the cursor
            # Let the form know
            self.Form.onMouseDrag(evt)
        else:
            self.Form.DragObject = None

    def onMouseLeftUp(self, evt):
        self.Form.processLeftUp(self, evt)
        evt.stop()

    def onMouseLeftDown(self, evt):
        self.Form.processLeftDown(self, evt)
        evt.stop()

    def onMouseLeftDoubleClick(self, evt):
        self.Form.processLeftDoubleClick(evt)

    def onContextMenu(self, evt):
        pop = self.createContextMenu()
        ui.callAfter(self.showContextMenu, pop)
        evt.stop()

    def createContextMenu(self):
        pop = self.Controller.getControlMenu(self)
        if self.Controller.Clipboard:
            pop.prependSeparator()
            pop.prepend(_("Paste"), OnHit=self.onPaste)
        pop.appendSeparator()
        pop.append(_("Add Controls from Data Environment"), OnHit=self.Form.onRunLayoutWiz)
        return pop

    def onPaste(self, evt):
        self.Controller.pasteObject(self)

    def _getDesEvents(self):
        return []

    def _getChildren(self):
        ret = [ch for ch in self.GetChildren() if not isinstance(ch, DragHandle)]
        return ret

    Children = property(_getChildren, None, None, _("Includes all relevant child objects  (list)"))

    DesignerEvents = property(
        _getDesEvents,
        None,
        None,
        _(
            """Returns a list of the most common events for the control.
            This will determine which events are displayed in the PropSheet
            for the developer to attach code to.  (list)"""
        ),
    )
