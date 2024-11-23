# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import codecs

from .. import ui
from ..dLocalize import _
from ..lib.utils import ustr
from ..lib import xmltodict as xtd
from ..lib import DesignerUtils
from .. import events
from . import class_designer_menu
from .drag_handle import DragHandle
from .wizards.quick_layout_wizard import QuickLayoutWizard
from .class_designer_control_mixin import ClassDesignerControlMixin as dcm
from .class_designer_components import LayoutPanel
from .class_designer_components import LayoutBasePanel
from .class_designer_components import LayoutSpacerPanel
from .class_designer_components import LayoutSizer
from .class_designer_components import LayoutBorderSizer
from .class_designer_components import LayoutGridSizer
from .class_designer_components import LayoutSaverMixin
from .class_designer_components import NoSizerBasePanel
from .class_designer_components import classFlagProp

from ..ui import dKeys
from ..ui import dButton
from ..ui import dCheckBox
from ..ui import dComboBox
from ..ui import dDialog
from ..ui import dDockForm
from ..ui import dForm
from ..ui import dGridSizer
from ..ui import dLabel
from ..ui import dListControl
from ..ui import dMenu
from ..ui import dOkCancelDialog
from ..ui import dPanel
from ..ui import dRadioList
from ..ui import dSizer
from ..ui import dSpinner
from ..ui import dSplitter
from ..ui import dStandardButtonDialog
from ..ui import dStatusBar
from ..ui import dTextBox
from ..ui import dToolForm
from ..ui import dTreeView
from ..ui.dialogs import Wizard


class ClassDesignerFormMixin(LayoutSaverMixin):
    def __init__(self, parent=None, properties=None, *args, **kwargs):
        if not self.Caption:
            self.Caption = _("Dabo Class Designer")
        self._controls = []
        self._namedConnection = ""
        self._selection = [self]
        self._classFile = ""
        self._canContain = self._isMain
        self._currContainer = None
        self._dragObject = None
        self._draggedObjects = None
        self._dragImage = None
        self._dragOrigPos = (0, 0)
        self._dragObjOffset = (0, 0)
        self._dragDrawPos = (0, 0)
        self._appNotifiedClose = False
        self._savedState = {}
        # Need to store references to handles along with a reference
        # to the control they are enclosing
        self.handles = {}
        # Name of each handle in a set. The names are abbreviations for
        # "Top Left", "Top Middle", etc.
        self.handleNames = ("TL", "TM", "TR", "ML", "MR", "BL", "BM", "BR")
        # When dragging a handle, this holds the reference to the handle
        self._handleDragged = None
        # Denotes if we are dragging to select controls
        self._selecting = False
        # Windows has some issues with drawing and control layering. In order
        # to get around this, create dummy drawing panel on top of the rest.
        self._drawSurface = None
        # When editing non-sizer designs, this holds the active container
        # for adding controls.
        self._activeContainer = None
        # The auto-binding happens too late in this case, so call
        # this method here.
        self.onActivate(None)

    def _beforeInit(self, pre):
        """Need to set this early in the process"""
        # Convenient flag for controls determining if
        # they are being modified on a design surface
        # or run interactively.
        self.isDesignerForm = True
        return super(ClassDesignerFormMixin, self)._beforeInit(pre)

    def afterInit(self):
        self._defaultLeft = 30
        self._defaultTop = 50
        self._defaultWidth = 570
        self._defaultHeight = 550
        self._alwaysDrawSizerOutlines = True
        self._drawSizerChildren = True
        self._recurseOutlinedSizers = False
        self._sizersToOutline = []

    def afterInitAll(self):
        self.refresh()

    def bringToFront(self):
        super(ClassDesignerFormMixin, self).bringToFront()

    def saveState(self):
        self._savedState = self._getSavedState()

    def restoreSizeAndPosition(self):
        super(ClassDesignerFormMixin, self).restoreSizeAndPosition()
        self.saveState()

    def _getSavedState(self):
        if self._formMode:
            # Save the whole form
            return self.getDesignerDict(propsToExclude=("Top", "Left"))
        else:
            # The main object is the child of the main panel.
            obj = self.mainPanel.Children[0]
            # Make sure it has its class flag set
            obj.__setattr__(classFlagProp, self._classFile)
            contr = self.Controller
            saveall = contr.saveAllProps
            contr.saveAllProps = True
            ret = self.getClassDesignerDict(obj, propsToExclude=("Top", "Left"))
            contr.saveAllProps = saveall
            return ret

    def onKeyChar(self, evt):
        code = evt.keyCode
        if code not in (
            dKeys.key_Left,
            dKeys.key_Right,
            dKeys.key_Up,
            dKeys.key_Down,
            dKeys.key_Back,
            dKeys.key_Delete,
        ):
            # We don't need to do anything
            return
        if self.UseSizers:
            return

        modAlt = evt.altDown
        modControl = evt.controlDown
        modShift = evt.shiftDown
        # Control modifies shifting by 10 pixels instead of just 1
        distance = 1 + (modControl * 9)
        h = v = 0
        if code == dKeys.key_Left:
            h = -1 * distance
        if code == dKeys.key_Right:
            h = distance
        if code == dKeys.key_Up:
            v = -1 * distance
        if code == dKeys.key_Down:
            v = distance
        deleting = code in (dKeys.key_Back, dKeys.key_Delete)

        for obj in self.Controller.Selection:
            if deleting:
                self.selectControl(obj, True)
                ui.callAfter(obj.release)
            elif modShift:
                obj.growControl(h, v)
            else:
                obj.nudgeControl(h, v)

    def onActivate(self, evt):
        cntrl = self.Controller
        if cntrl is not None:
            try:
                cf = cntrl.CurrentForm
                if cf is not self:
                    cntrl.CurrentForm = self
                    self._selection = [obj for obj in self._selection if obj]
                    cntrl.Selection = self._selection
                ui.callAfterInterval(200, cntrl.updateLayout)
            except:
                # no current form at the moment
                pass

    def onDeactivate(self, evt):
        if self.Controller is not None:
            self._selection = self.Controller.Selection

    def createContextMenu(self):
        """The form doesn't allow direct access in design mode. Instead, call the
        base panel, if any, and use its context menu.
        """
        if self.mainPanel:
            menu = self.mainPanel.createContextMenu()
        if not menu:
            menu = dMenu()
        if self.ToolBar is None:
            menu.append(_("Add Toolbar"), OnHit=self.onAddToolbar)
        else:
            menu.append(_("Add Toolbar Button"), OnHit=self.onAddToolbarButton)
        return menu

    def onAddToolbar(self, evt):
        self.Controller.addNewToolbar(self)

    def onAddToolbarButton(self, evt):
        class TbButtonDialog(dOkCancelDialog):
            def addControls(self):
                self.Caption = _("ToolBar Buttons")
                gsz = dGridSizer(MaxCols=2, HGap=3, VGap=10)
                lbl = dLabel(self, Caption=_("Button Name"))
                txt = dTextBox(self, RegID="button_name")
                gsz.append(lbl)
                gsz.append(txt)
                lbl = dLabel(self, Caption=_("Button Picture"))
                btn = dButton(self, Caption=_("Select..."), OnHit=self.onSelectPic)
                txt = dTextBox(self, RegID="button_picture", ReadOnly=True)
                hsz = dSizer("H")
                hsz.append(btn)
                hsz.append(txt)
                gsz.append(lbl)
                gsz.append(hsz)
                chk = dCheckBox(self, Caption=_("Toggle?"), RegID="toggle")
                gsz.appendSpacer(10)
                gsz.append(chk)
                lbl = dLabel(self, Caption=_("ToolTip Text"))
                txt = dTextBox(self, RegID="tooltip_text")
                gsz.append(lbl)
                gsz.append(txt)
                lbl = dLabel(self, Caption=_("Help Text"))
                txt = dTextBox(self, RegID="help_text")
                gsz.append(lbl)
                gsz.append(txt)
                self.Sizer.append1x(gsz)

            def onSelectPic(self, evt):
                pic = ui.getFile("png", "icn", "bmp", "jpg", "gif")
                self.button_picture.Value = pic

        dlg = TbButtonDialog(self)
        dlg.show()
        if not dlg.Accepted:
            return
        nm = dlg.button_name.Value
        pic = dlg.button_picture.Value
        tog = dlg.toggle.Value
        ttt = dlg.tooltip_text.Value
        hlp = dlg.help_text.Value
        dlg.release()
        self.Controller.addNewToolbarButton(self, name=nm, pic=pic, toggle=tog, tip=ttt, help=hlp)

    def beforeClose(self, evt):
        ret = True
        curr = self._getSavedState()
        self.Controller.flushCodeEditor()
        if curr != self._savedState:
            cf = self._classFile
            if cf:
                fname = os.path.split(cf)[1]
            else:
                fname = _("Untitled")
            saveIt = ui.areYouSure(
                _("Do you want to save the changes to '%s'?") % fname,
                _("Unsaved Changes"),
            )
            if saveIt is None:
                # They canceled
                ret = False
            elif saveIt is True:
                # They want to save
                ret = self.Controller.wrapSave(self.onSaveDesign, None)
            # Otherwise, they said 'No'
        return ret

    def closing(self, evt=None):
        if self.Controller is not None:
            if not self._appNotifiedClose:
                self._appNotifiedClose = True
                self._finito = True
                self.Controller.designerFormClosing(self)
        return True

    def _configureForDockForm(self):
        """If the form being edited is a dDockForm, we need to fake it by adding
        all the functionality to the DesignerForm.
        """
        pass

    #         from dDockForm import _dDockManager
    #         self._mgr = _dDockManager(self)
    #
    #         def addMethod(func, nm):
    #             method = new.instancemethod(func, self)
    #             setattr(self, nm, method)
    #         def _addDockPanel(self, *args, **kwargs):
    #             pnl = self._basePanelClass(self, *args, **kwargs)
    #         def _refreshState(self, interval=None):
    #             if interval is None:
    #                 interval = 100
    #             if interval == 0:
    #                 self._mgr.Update()
    #             else:
    #                 ui.callAfterInterval(interval, self._mgr.Update)
    #         addMethod(_addDockPanel, "addDockPanel")
    #         addMethod(_refreshState, "_refreshState")

    #         pc = dDockForm.getBasePanelClass()
    #         self._basePanelClass = self.Controller.getControlClass(pc)
    #         self.CenterPanel = self._basePanelClass(self, name="CenterPanel",
    #                 typ="center")
    #        self.CenterPanel = LayoutBasePanel(self)

    #         self.CenterPanel = pc(self)

    def onPageChanged(self, evt):
        """Called when a wizard page is selected"""
        pg = self._pages[evt.newPageNum]
        try:
            obj = self.Controller.Selection[0]
            if obj.isContainedBy(pg):
                # No need to do anything
                return
        except:
            pass
        self.selectControl(pg, False)
        ui.callAfter(self._refreshPage, pg)

    def _refreshPage(self, pg):
        acd = pg.autoClearDrawings
        pg.autoClearDrawings = True
        self.refresh()
        pg.autoClearDrawings = acd

    def refresh(self, interval=None):
        self.clear()
        super(ClassDesignerFormMixin, self).refresh(interval=interval)

    def onResize(self, evt):
        ui.callAfterInterval(100, self.refresh)

    def onMenuOpen(self, evt):
        self.Controller.menuUpdate(evt, self.MenuBar)

    def afterSetMenuBar(self):
        class_designer_menu.mkDesignerMenu(self)

    def onPanelCreate(self):
        self.Controller.updateLayout()

    def objectClick(self, obj, shift=False):
        """Called when the user selects an object."""
        if isinstance(obj, NoSizerBasePanel):
            self.ActiveContainer = obj
            # That's just a dummy base, so select the form instead
            obj = self
        else:
            if not self.UseSizers:
                # We need to determine if the object is a child of the active
                # container, If so, select it normally. If not, see if it is contained
                # at some level by the active container, or if it is completely
                # outside of it. If it is within, treat this as a click on the parent
                # container that is the outermost child of the ActiveContainer.
                # If it is outside of the ActiveContainer, make the new
                # ActiveContainer the first common container between the clicked
                # object and the old ActiveContainer.
                ac = self.ActiveContainer
                if obj.Parent is ac:
                    # Normal
                    pass
                elif obj is ac:
                    # Background click; deselect all objects
                    obj = []
                elif self.objectIsContainedBy(obj, ac):
                    # Find ac child that contains obj
                    obj = self.findActiveContainerChild(obj)
                else:
                    # Not contained. Find the first common container for obj and ac
                    # and select that.
                    cnt = self.firstCommonContainer(obj, ac)
                    self.ActiveContainer = cnt

        origSel = self.Controller.Selection
        self.Controller.select(obj, shift)
        newSel = self.Controller.Selection
        if newSel is origSel:
            self.redrawHandles(newSel)

    def objectIsContainedBy(self, obj, cntr):
        """Returns True if the object is contained at some level by cntr."""
        return obj.isContainedBy(cntr)

    def findActiveContainerChild(self, obj):
        """Returns the object that is a child of the ActiveContainer that
        the passed object is contained by.
        """
        ret = obj
        while ret:
            if ret.Parent is self.ActiveContainer:
                break
            ret = ret.Parent
        return ret

    def firstCommonContainer(self, o1, o2):
        """Returns the first container that contains both o1 and o2."""
        cnt1 = []
        cnt2 = []
        p1 = o1.Parent
        p2 = o2.Parent
        while p1 is not self:
            cnt1.insert(0, p1)
            p1 = p1.Parent
        while p2 is not self:
            cnt2.insert(0, p2)
            p2 = p2.Parent
        # OK, at the very least, they have the form in common.
        ret = self
        # Pop off the first object of each list until they differ.
        while cnt1 and cnt2:
            pop1 = cnt1.pop(0)
            pop2 = cnt2.pop(0)
            if pop1 is pop2:
                ret = pop1
            else:
                break
        return ret

    def selectControl(self, obj, shift=False):
        """Pass-through method when an object needs to be selected"""
        self.Controller.select(obj, shift)

    def updateApp(self):
        """Called by contained objects when their state changes
        and requires the ClassDesigner to update itself.
        """
        self.Controller.updateLayout()
        self.layout()

    def getObjectHierarchy(self):
        """Returns a list of 2-tuples representing the structure of
        the objects on this form. The first element is the nesting level,
        and the second is the object. The objects are in the order
        created, irrespective of sizer position.
        """
        if self._formMode:
            obj = self
        else:
            obj = self.Children[0]
        return self._recurseObjects(obj, 0)

    def _recurseObjects(self, obj, level):
        ret = [(level, obj)]
        kids = None
        if isinstance(obj, (dComboBox, dSpinner, dListControl, dRadioList)):
            # These compound controls don't need their parts listed
            children = None
        else:
            try:
                kids = obj.Children
            except:
                # Not an object that has a Children prop; ignore it
                kids = None
        if kids is not None:
            for ch in kids:
                if isinstance(ch, (dForm, dToolForm, dDialog, dStatusBar, LayoutPanel)):
                    continue
                elif ustr(ch).startswith("<wx."):
                    # These are low-level items, such as scrollbars, and do not need
                    # to be included.
                    continue
                ret += self._recurseObjects(ch, level + 1)
        return ret

    def editCode(self, obj):
        """Called when a object's code is to be edited."""
        self.Controller.editCode(obj=obj)

    def panelClick(self, panel, shift):
        """Called when a layout panel (for an empty sizer slot) is
        clicked by the user. Pass the sizer item up to the Controller.
        """
        sz = panel.ControllingSizer
        obj = panel.ControllingSizerItem
        self.Controller.select((obj, sz), shift)

    def setClassInfo(self, classRef=None, className=None, classFile=None):
        self._className = className
        self._classFile = classFile
        self._selectedClass = classRef
        self._selectedClassName = className
        self._classOrigCode = ""
        self._classMethods = {}

    def getClassFile(self):
        return self._classFile

    def onSaveAsDesign(self, evt):
        self._classFile = ui.getSaveAs(wildcard="cdxml")
        if not self._classFile:
            # User canceled
            return
        self._classFile = self._classFile.rstrip(".")
        if not self._classFile.endswith(".cdxml"):
            self._classFile += ".cdxml"
        self._savedState = {}
        self.onSaveDesign(evt)

    def onSaveDesign(self, evt, useTmp=False):
        currForm = self.Controller.CurrentForm
        newFile = False

        # Replace this with a setting of some sort
        self.useJSON = False
        fileExt = {True: "json", False: "cdxml"}[self.useJSON]

        if useTmp:
            osp = os.path
            if self._classFile:
                loc = os.path.split(self._classFile)[0]
            else:
                loc = os.getcwd()
            fname = self.Application.getTempFile("cdxml", directory=loc)
        else:
            if not self._classFile:
                self._classFile = ui.getSaveAs(wildcard="cdxml")
                if not self._classFile:
                    # User canceled
                    return
                else:
                    self._classFile = self._classFile.rstrip(".")
                    if not self._classFile.endswith(".cdxml"):
                        self._classFile += ".cdxml"
                newFile = True
            fname = self._classFile

        # If there is a code editing form, flush the current page
        self.Controller.flushCodeEditor()
        # Create the property dictionary
        if self._formMode:
            # Save the whole form
            propDict = self.getDesignerDict()
            propDictCompare = self.getDesignerDict(propsToExclude=("Top", "Left"))
        else:
            # The main object is the child of the main panel.
            obj = self.mainPanel.Children[0]
            # Make sure it has its class flag set
            obj.__setattr__(classFlagProp, self._classFile)
            self.Controller.saveAllProps = True
            propDict = propDictCompare = self.getClassDesignerDict(obj)
            self.Controller.saveAllProps = False

        if not useTmp and not newFile and (propDictCompare == self._savedState):
            return

        imp = self.Controller.getImportDict(self)
        if imp:
            cd = propDict.get("code", {})
            cd.update({"importStatements": imp})
            propDict["code"] = cd
        singleFile = useTmp or self.Application.getUserSetting("saveCodeInXML", False)
        if not singleFile:
            propDict, codeDict = self._extractCodeFromPropDict(propDict)
        if self.useJSON:
            textToSave = pformat(propDict)
        else:
            textToSave = xtd.dicttoxml(propDict)
        # Try opening the file. If it is read-only, it will raise an
        # IOErrorrror that the calling method can catch.
        codecs.open(fname, "wb", encoding="utf-8").write(textToSave)
        cfName = "%s-code.py" % os.path.splitext(fname)[0]
        if newFile:
            self.Controller.addMRUPath(fname)
        if singleFile:
            # Delete the code file if present.
            if os.path.exists(cfName):
                os.remove(cfName)
        else:
            # Write out the code file
            desCode = self._createDesignerCode(codeDict)
            codecs.open(cfName, "w", encoding="utf-8").write(desCode)
        if currForm:
            currForm.bringToFront()
        self.saveState()
        return fname

    def _createDesignerCode(self, cd):
        """Given a dict of code, create the Python script containing that code."""
        ret = """# -*- coding: utf-8 -*-
### Dabo Class Designer code. You many freely edit the code,
### but do not change the comments containing:
###         'Dabo Code ID: XXXX',
### as these are needed to link the code to the objects.\n\n"""
        codeHeaderTemplate = DesignerUtils.getCodeObjectSeperator() + "%s"
        body = []
        for codeKey, mthds in list(cd.items()):
            # Add the import statements first, if any
            try:
                code = mthds.pop("importStatements").strip()
                while not code.endswith("\n\n"):
                    code += "\n"
            except KeyError:
                code = ""
            if code:
                body.insert(0, code)
                code = ""
            # Sort the methods alphabetically
            mthNames = list(mthds.keys())
            mthNames.sort()
            for mthd in mthNames:
                code += mthds[mthd].strip()
                while not code.endswith("\n\n\n"):
                    code += "\n"
            hdr = codeHeaderTemplate % codeKey
            body.append("%s\n%s" % (hdr, code))
        return ret + "\n".join(body)

    def onSaveClassDesign(self, evt):
        """Save the contents of the designer, excluding the outer form,
        as a separate class that can be used in other designs.
        """

        # See if they want to save the entire contents of the form, or
        # just the current selection.
        class ClassScopeDialog(dOkCancelDialog):
            def addControls(self):
                self.Caption = _("Save as Class")
                # This is the attribute used to determine their choice
                self.saveType = 0
                lbl = dLabel(self, Caption=_("Do you want to save"))
                self.Sizer.append(lbl, halign="center")
                chc = [_("The contents of the form"), _("Just the current selection")]
                rgrp = dRadioList(
                    self,
                    Choices=chc,
                    DataSource=self,
                    DataField="saveType",
                    ValueMode="Position",
                )
                self.Sizer.append(rgrp, halign="center")

        savType = None
        dlg = ClassScopeDialog(self)
        dlg.saveType = 1
        dlg.update()
        dlg.show()
        if dlg.Accepted:
            savType = dlg.saveType
        # dlg.release()
        if savType is None:
            return
        if savType == 0:
            # Entire contents; start with the mainPanel
            topObj = self.mainPanel
        else:
            topObj = self.Controller._selection[0]

        # Saving just a part of the design, so get the new file name
        clsFile = ui.getSaveAs(wildcard="cdxml")
        if not clsFile:
            # User canceled
            return
        else:
            if not os.path.splitext(clsFile)[1] == ".cdxml":
                clsFile += ".cdxml"

        # If there is a code editing form, flush the current page
        self.Controller.flushCodeEditor()
        topObj.__setattr__(classFlagProp, clsFile)
        propDict = self.getClassDesignerDict(topObj)
        xml = xtd.dicttoxml(propDict)
        # Try opening the file. If it is read-only, it will raise an
        # IOError that the calling method can catch.
        codecs.open(clsFile, "wb", encoding="utf-8").write(xml)

    def getClass(self):
        """Returns a string representing the class's name. Default behavior
        is to return the BaseClass, but this allows for specific subclasses
        to override that behavior.
        """
        if isinstance(self, Wizard):
            ret = "ui.dialogs.Wizard"
        else:
            ret = super(ClassDesignerFormMixin, self).getClass()
        return ret

    def _extractCodeFromPropDict(self, pd, cd=None, prntName=None):
        """Extract all 'code' keys into a separate dict. Remove them from the
        passed dict. Add 'code-ID' attributes to any dicts with code.
        Return a 2-tuple of dicts: the original dict with the code extracted, and the
        code dict with each code-ID as the key.
        """
        if cd is None:
            cd = {}
        if prntName is None:
            prntName = "top"
        nm = pd.get("name", "NONAME")
        atts = pd.get("attributes", {})
        kids = pd.get("children", [])
        code = pd.get("code", {})
        pd["code"] = {}
        if code:
            # Add it to the code dict
            codeIDbase = codeID = atts.get("code-ID", "%s-%s" % (nm, prntName))
            while codeID in cd:
                codeID = "%s-%s" % (codeIDbase, random.randrange(999))
            pd["attributes"].update({"code-ID": codeID})
            cd[codeID] = code
        pd["children"] = []
        isSizer = atts["designerClass"] in (
            "LayoutGridSizer",
            "LayoutSizer",
            "LayoutBorderSizer",
        )
        if isSizer:
            # Pass the parent name instead of the sizer name
            nm = prntName
        for kid in kids:
            kd, cd = self._extractCodeFromPropDict(kid, cd, nm)
            pd["children"].append(kd)
        return (pd, cd)

    def getClassDesignerDict(self, obj, propsToExclude=None):
        """We need to generate classIDs for later management of
        contained objects. We also want to strip out sizer info.
        """
        try:
            seed = obj.classID
        except:
            # Use the hash function to generate the base for class IDs
            seed = ustr(abs(obj.__hash__()))
        # Create the property dictionary
        ret = obj.getDesignerDict(classID=seed, propsToExclude=propsToExclude)
        # We don't want to save the controlling sizer's info
        ret["attributes"]["sizerInfo"] = {}
        return ret

    def onRunDesign(self, evt):
        # First, make sure that it's been saved
        try:
            fname = self.onSaveDesign(None, useTmp=True)
        except IOError as e:
            ui.info(_("Cannot write file"), title=_("Write Error"))
        if not fname or not os.path.isfile(fname):
            # Nothing was saved
            return

        pth = os.path.split(os.path.abspath(fname))[0]
        # Set the app's HomeDirectory to the location of the cdxml file.
        self.Application.HomeDirectory = pth
        if pth not in sys.path:
            sys.path.append(pth)
        if self._formMode:
            frm = ui.createForm(fname)
        else:
            frm = dForm(None)
            obj = frm.addObject(fname)
            if frm.Sizer:
                frm.Sizer.append1x(obj)
                frm.Caption = _("Test form for: %s") % os.path.split(fname)[1]
                frm.layout()
        frm.TempForm = True
        frm.Visible = True
        if isinstance(frm, Wizard):
            frm.start()
        if isinstance(frm, dDialog):

            def __dlgRelease(evt):
                evt.EventObject.release()

            frm.bindEvent(events.Close, __dlgRelease)

    def layout(self):
        super(ClassDesignerFormMixin, self).layout()
        # This seems to clear up some ghost pixels that get left behind
        # in the top left corner of the form.
        self.ClearBackground()

    def genPropDict(self, ctl):
        ret = {}
        props = ctl.getPropertyList()
        for prop in props:
            inf = ctl.getPropertyInfo(prop)
            if not inf["readable"] or not inf["writable"]:
                continue
            if prop in ("Font", "Right", "Bottom"):
                # These are either derived or set by other props
                continue
            if prop in ("IconBundle",):
                # Cannot save this as text
                continue

            val = eval("ctl." + prop)
            ret[prop] = val
        return ret

    def openClass(self):
        """Allows the user to select a particular class from the
        module of their choice. Stores the class name, the path to the
        module, the original code of the class, and the methods
        of that class to internal attributes.
        """
        dlg = ocd.OpenClassDialog(self, className=self._className, classFile=self._classFile)
        if not dlg.ClassName:
            # User bailed
            return

        self._className = dlg.ClassName
        self._classFile = dlg.ClassFile
        self.parseInfo(dlg.ClassInfo)

    def parseClass(self):
        dir, fname = os.path.split(self._classFile)
        fbase = os.path.splitext(fname)[0]
        clsInfo = pyclbr(fbase, list(dir))
        self.parseInfo(clsInfo)

    def parseInfo(self, modInfo):
        inf = modInfo[self._className]
        self._classMethods = inf.methods
        # Adjust the line numbers for the beginning of the module
        for k, v in list(self._classMethods.items()):
            self._classMethods[k] = v - (inf.lineno - 1)

        z = [m.lineno for m in list(modInfo.values())]
        z.sort()
        # Find the index of the first line of this class, and the
        # index of the next class.
        thisClsLn = inf.lineno
        indx = z.index(thisClsLn)
        try:
            nxtClsLn = z[indx + 1]
        except IndexError:
            nxtClsLn = -1
        # Read in the file, and extract this class's code.
        f = codecs.open(inf.file, "r", encoding="utf-8")
        txt = []
        for i in range(thisClsLn - 1):
            f.readline()
        # Now read the lines up to the next class (if any)
        if nxtClsLn == -1:
            self._classOrigCode = f.read()
        else:
            numLines = nxtClsLn - thisClsLn
            for i in range(numLines):
                txt.append(f.readline())
            self._classOrigCode = "".join(txt)
        f.close()

    def onRunLayoutWiz(self, evt):
        """Run the QuickLayoutWizard, using the form's named
        connection. If none exists, ask the user to select one.
        """
        if self.UseSizers:
            pnl = self.Controller.getActivePanel()
            if pnl is None:
                ui.stop(_("Please right-click on the target slot"), _("No target"))
                return
            elif not isinstance(pnl, LayoutPanel):
                ui.stop(
                    _("Please select a target slot before running the wizard"),
                    _("No Slot Selected"),
                )
                return
        wiz = QuickLayoutWizard(self)
        wiz.ConnectionName = self.CxnName
        wiz.callback = self.addQuickLayout
        wiz.start()
        if wiz:
            wiz.hide()

    def addQuickLayout(self, layoutInfo):
        self.CxnName = layoutInfo["connectionName"]
        if layoutInfo["createBizobj"]:
            self.addBizobjCode(layoutInfo)
        self.Controller.addQuickLayout(layoutInfo)

    def addBizobjCode(self, info):
        tbl = info["table"]
        tblSafe = tbl.replace(" ", "_")
        # JFCS 01/22/07 added below to support schema.tableName by removing dot
        tblSafe = tblSafe.replace(".", "")
        tblTitle = tblSafe.title()
        lowbiz = tblSafe[0].lower() + tblSafe[1:] + "Bizobj"
        pk = info["pk"]
        flds = list(info["fldInfo"].keys())
        if pk and pk not in flds:
            # Make sure that the pk is retrieved!
            flds.append(pk)
        rep = self.Controller.getCodeDict()
        cd = rep.get(self)
        if cd is None:
            cd = {}
        currCode = cd.get("createBizobjs", "")

        bizCodeTemplate = self.getBizobjTemplate()
        loadCodeTemplate = self.getBizobjLoadTemplate()
        addFlds = []
        for fld in flds:
            addFlds.append('\t\tself.addField("%s")' % fld)
        fldDefs = "\n".join(addFlds)
        tq = '"' * 3
        bizcode = bizCodeTemplate % locals()
        # Get the biz directory
        bizdir = self.Application.getStandardAppDirectory("biz", os.path.abspath(self._classFile))
        if not bizdir:
            bizdir = ui.getDirectory(message=_("Please select your bizobj directory"))
        if not bizdir:
            if ui.areYouSure(
                message=_(
                    "Cannot create bizobj class without a directory. Do you want to copy the code to the clipboard?"
                ),
                title=_("Copy Bizobj Code"),
                cancelButton=False,
            ):
                self.Application.copyToClipboard(bizcode)
        else:
            fname = "%(tblTitle)sBizobj.py" % locals()
            codecs.open(os.path.join(bizdir, fname), "w", encoding="utf-8").write(bizcode)
            clsname = fname.strip(".py")
            codecs.open(os.path.join(bizdir, "__init__.py"), "a", encoding="utf-8").write(
                "\nfrom %(clsname)s import %(clsname)s\n" % locals()
            )

        # Now create the import code for the form.
        loadcode = loadCodeTemplate % locals()
        if currCode:
            # Add some blank lines
            currCode += "\n\n"
        else:
            # No 'def' line yet
            currCode = "def createBizobjs(self):\n"
        currCode += loadcode
        cd["createBizobjs"] = currCode
        rep[self] = cd
        self.Controller.updateCodeEditor()
        # Add the classes to the app's namespace
        self.Controller.updateNamespace(os.path.abspath(self._classFile))

    def onAddControl(self, evt):
        self.Controller.onAddControl(evt)

    def select(self, ctls):
        if ctls == self._selection:
            if not [ct for ct in ctls if hasattr(ct, "Selected") and not ct.Selected]:
                # Nothing changed; we're switching active forms
                return
        self.lockDisplay()
        if not isinstance(ctls, (list, tuple)):
            ctls = [ctls]
        for ct in ctls:
            ct.Selected = True
        # Do the handles thing if needed
        self.redrawHandles(ctls)
        if len(ctls) > 1:
            self.StatusText = _("-multiple selection-")
        elif len(ctls) == 0:
            self.StatusText = _("Selected Object: %s") % self.Name
        else:
            ct0 = ctls[0]
            if ct0:
                self.StatusText = _("Selected Object: %s") % ctls[0].Name
            else:
                self.StatusText = ""
        self.unlockDisplay()

    def ensureVisible(self, obj):
        """When selecting an object on a page, make sure that
        that page is selected.
        """
        if isinstance(obj, (list, tuple)):
            obj = obj[-1]
        if not hasattr(obj, "showContainingPage"):
            if isinstance(obj, dTreeView.getBaseNodeClass()):
                # Make sure that it is expanded in the tree
                obj.show()
                # Now make sure that the tree is visible.
                obj = obj.tree
            else:
                while obj.Parent:
                    obj = obj.Parent
                    if hasattr(obj, "showContainingPage"):
                        break
        obj.showContainingPage()

    #     def getControlClass(self, base):
    #         class controlMix(dcm, base):
    #             _superBase = base
    #             _superMixin = dcm
    #             def __init__(self, *args, **kwargs):
    #                 if hasattr(base, "__init__"):
    #                     apply(base.__init__,(self,) + args, kwargs)
    #                 parent = args[0]
    #                 dcm.__init__(self, parent, **kwargs)
    #         return controlMix

    #    def close(self):
    #         # Needed to avoid resizing errors when quitting
    #         self.Controller.isClosing = True
    #         super(ClassDesignerFormMixin, self).close()

    #    def onSizePosChg(self, evt):
    #         if self.controlPanel and self.mainControl:
    #             self.controlPanel.Size = self.mainControl.Size
    #             self.Layout()
    #         self.Controller.PropSheet.updatePropVal( ("Left", "Right", "Top", "Bottom",
    #                 "Size", "Height", "Width", "Position") )

    #    def updatePropVal(self, valNames):
    #         """Pass-through method"""
    #         self.Controller.PropSheet.updatePropVal(valNames)

    def redrawHandles(self, ctls, showEm=True):
        if self.UseSizers:
            # Not applicable
            return
        if not isinstance(ctls, (list, tuple)):
            ctls = [ctls]
        for ctl in ctls:
            if ctl is self:
                # Nothing to hilite
                self.hideAllHandles()
                return
            elif isinstance(ctl, (dSizer, LayoutPanel, LayoutBasePanel)):
                # Not an actual control
                continue

            hnds = self.createControlHandles(ctl)
            try:
                left, top = ctl.Position
            except AttributeError:
                # This is an object that doesn't have 'Position', such as a
                # grid column, so skip the handle drawing.
                return
            wid, ht = ctl.Size
            handleW, handleH = hnds["TL"].Size
            handleMid = int(handleH / 2)
            hnds["TL"].Position = left - handleW + handleMid, top - handleH + handleMid
            hnds["TM"].Position = (
                (left + (wid / 2) - handleMid),
                top - handleH + handleMid,
            )
            hnds["TR"].Position = left + wid - handleMid, top - handleH + handleMid

            hnds["ML"].Position = left - handleW + handleMid, top + (ht / 2) - handleMid
            hnds["MR"].Position = left + wid - handleMid, top + (ht / 2) - handleMid

            hnds["BL"].Position = left - handleW + handleMid, top + ht - handleMid
            hnds["BM"].Position = (left + (wid / 2) - handleMid), top + ht - handleMid
            hnds["BR"].Position = left + wid - handleMid, top + ht - handleMid

            for hnd in list(hnds.values()):
                hnd.bringToFront()
                hnd.Visible = showEm

    def createControlHandles(self, ctl):
        try:
            handleSet = self.handles[ctl]
        except:
            handleSet = {}
            for nm in self.handleNames:
                h = DragHandle(ctl.Parent, handleName=nm)
                h.ownerCtl = ctl
                handleSet[nm] = h
            self.handles[ctl] = handleSet
        return handleSet

    def startResize(self, handle, evt):
        if not handle:
            return
        ctl = handle.ownerCtl
        up, right, down, left = handle.up, handle.right, handle.down, handle.left
        ctl.startResize(evt, up, right, down, left)
        self._handleDragged = handle
        self.DragObject = ctl
        self.dragging = True
        self.hideHandles(ctl)
        self.iterateCall("setMouseHandling", True)

    def stopResize(self, handle, evt):
        if not handle:
            return
        ctl = handle.ownerCtl
        up, right, down, left = handle.up, handle.right, handle.down, handle.left
        ctl.stopResize(evt, up, right, down, left)
        self._handleDragged.dragging = False
        self._handleDragged = None
        self.redrawHandles(ctl)
        self.dragging = False
        self.iterateCall("setMouseHandling", False)

    def resizeCtrl(self, handle, evt):
        if not handle or not handle.ownerCtl:
            return
        ctl = handle.ownerCtl
        up, right, down, left = handle.up, handle.right, handle.down, handle.left
        ctl.resize(evt, up, right, down, left)

    def hideAllHandles(self):
        ks = list(self.handles.keys())
        for key in ks:
            self.hideHandles(key)

    def hideHandles(self, ctl=None, release=False):
        if ctl is None:
            return
        try:
            hnd = self.handles[ctl]
        except KeyError:
            return
        for nm, h in list(hnd.items()):
            h.Visible = False
            if release:
                h.release()
        if release:
            del self.handles[ctl]

    def alignControls(self, evt, edge):
        """Aligns the currently selected controls along the specified
        edge. Normally the alignment is to the topmost position if
        Top alignment is chosen; rightmost position if Right alignment;
        etc. However, if the control key is depressed, the opposite
        alignment is chosen. IOW, if control is down and Top alignment
        is selected, the controls are top aligned to the control whose
        Top is the closest to the bottom.
        """
        slc = self.Controller.Selection
        controlPressed = ui.isControlDown()
        if edge in ("Top", "Left"):
            memberFunc = {True: max, False: min}[controlPressed]
        else:
            memberFunc = {True: min, False: max}[controlPressed]
        newval = memberFunc([eval("ctl.%s" % edge) for ctl in slc])
        for ctl in slc:
            ui.setAfter(ctl, edge, newval)
        ui.callAfter(self.redrawHandles, slc)

    def iterateCall(self, funcName, *args, **kwargs):
        """We need to override this because of a hack that was done
        to remap the Children property, which iterateCall() relies upon,
        to the children of the 'mainPanel' object. We need to be sure that
        the mainPanel gets the call instead.
        """
        if self.mainPanel:
            # This is ignored in the Children prop
            self.mainPanel.iterateCall(funcName, *args, **kwargs)
        else:
            super(ClassDesignerFormMixin, self).iterateCall(funcName, *args, **kwargs)

    def onControlLeftDown(self, evt):
        obj = evt.EventObject
        ac = self.ActiveContainer
        self.iterateCall("setMouseHandling", True)
        if obj is ac:
            # We're clicking within the active container, so start
            # drawing the marquee.
            self.onLeftDown(evt)
            return
        elif obj.Parent is ac:
            if self.Controller.Selection:
                self.hideAllHandles()
                if obj in self.Controller.Selection:
                    self._draggedObjects = self.Controller.Selection
                else:
                    if evt.shiftDown:
                        # Add the object
                        self._draggedObjects = self.Controller.Selection
                        self._draggedObjects.append(obj)
                    else:
                        self.Controller.deselect(self.Controller.Selection)
                        self._draggedObjects = [obj]
            else:
                self._draggedObjects = [obj]

        elif self.objectIsContainedBy(obj, ac):
            # Find ac child that contains obj
            self._draggedObjects = [self.findActiveContainerChild(obj)]
            self.hideAllHandles()
        else:
            # Not contained. Find the first common container for obj and ac
            # and select that.
            cnt = self.firstCommonContainer(obj, ac)
            self.ActiveContainer = cnt
            self.onLeftDown(evt)
            return
        # Need to record the starting position for the dragged controls
        for ctl in self._draggedObjects:
            ctl._startDragPos = ctl.Position
        self._dragOrigPos = obj.absoluteCoordinates(evt.mousePosition)
        self._dragObjOffset = evt.mousePosition

    def processLeftDoubleClick(self, evt):
        """Called from an object when it is double-clicked."""
        obj = evt.EventObject
        if obj.IsContainer:
            self.ActiveContainer = obj

    def processLeftDown(self, obj, evt):
        if isinstance(obj, NoSizerBasePanel):
            self.onLeftDown(evt)

    def onLeftDown(self, evt):
        if True:
            self._selecting = True
            self._dragDrawPos = self._dragOrigPos = evt.EventObject.absoluteCoordinates(
                evt.mousePosition
            )
            if self._drawSurface is None:
                self._drawSurface = self.ActiveContainer
            self.iterateCall("setMouseHandling", True)

    ##            else:
    ##                self._drawSurface = self
    #         else:
    #             self.drawing = True
    #             self.drawX, self.drawY = self.ScreenToClient( wx.GetMousePosition() )    #(evt.m_x, evt.m_y)

    def onLeftUp(self, evt, obj=None):
        if obj is None:
            obj = evt.EventObject
            if isinstance(obj.Parent, dRadioList):
                obj = obj.Parent
        drobj = self._draggedObjects
        ui.callAfter(self._clearDraggedObjects)
        if self._selecting:
            mp = evt.mousePosition
            ac = self.ActiveContainer
            # Clear the marquee
            self.drawMarquee(self._dragDrawPos)
            self._selecting = False
            origPos = self._dragOrigPos
            if obj:
                endPos = obj.absoluteCoordinates(mp)
            else:
                endPos = mp

            relOrigPos = ac.relativeCoordinates(origPos)
            relEndPos = ac.relativeCoordinates(endPos)
            # Was there a selected class?
            cls = self.Controller.SelectedClass
            if cls is not None:
                self.Controller.addDrawnClass(cls, ac, relOrigPos, relEndPos)
            else:
                # self._drawSurface = None
                # Any selected?
                sel = [
                    ctl
                    for ctl in ac.Children
                    if self.intesects(ctl, relOrigPos, relEndPos)
                    and not isinstance(ctl, DragHandle)
                ]
                self.selectControl(sel, evt.shiftDown)
            self._dragOrigPos = self._dragDrawPos = (0, 0)
        else:
            self.objectClick(obj, evt.shiftDown)

    def intesects(self, ctl, p1, p2):
        """Returns True if any part of ctl is within the rectangle defined by p1, p2."""
        cLeft, cTop = ctl.Position
        cRight = cLeft + ctl.Width
        cBottom = cTop + ctl.Height
        pLeft = min(p1[0], p2[0])
        pTop = min(p1[1], p2[1])
        pRight = pLeft + abs(p1[0] - p2[0])
        pBottom = pTop + abs(p1[1] - p2[1])

        if (cLeft > pRight) or (cRight < pLeft) or (cTop > pBottom) or (cBottom < pTop):
            return False
        else:
            ret = ((cLeft <= pRight) or (cRight >= pLeft)) and (
                (cTop <= pBottom) or (cBottom >= pTop)
            )
            return ret

    def setMouseHandling(self, turnOn):
        """When turnOn is True, sets all the mouse event bindings. When
        it is False, removes the bindings.
        """
        if turnOn:
            self.bindEvent(events.MouseMove, self.handleMouseMove)
        else:
            self.unbindEvent(events.MouseMove)
        # This is also being passed on to the base panel, which will pass
        # it on to its child objects, so there is no need to duplicate the
        # calls.
        raise dException.StopIterationException

    def handleMouseMove(self, evt):
        if evt.dragging:
            self.onMouseDrag(evt)
        else:
            self.DragObject = None

    def onMouseDrag(self, evt):
        obj = evt.EventObject
        if isinstance(obj.Parent, dRadioList):
            obj = obj.Parent
        if evt.dragging:
            if self.UseSizers:
                return
                if not self.DragObject and not self._selecting:
                    if not isinstance(obj, dSplitter):
                        self.DragObject = obj
                if self._dragImage:
                    auto = self.autoClearDrawings
                    self.autoClearDrawings = True
                    currX, currY = self.getMousePosition()
                    drawX = currX - self._dragObjOffset[0]
                    drawY = currY - self._dragObjOffset[1]
                    self._dragImage.Xpos = drawX
                    self._dragImage.Ypos = drawY
                    self._redraw()
                    self.autoClearDrawings = auto
            else:
                # no sizers; see if we're dragging any controls
                if self._handleDragged:
                    hd = self._handleDragged
                    self.resizeCtrl(hd, evt)
                elif self._draggedObjects is not None:
                    self.moveDraggedObjects(evt)
                elif self._selecting:
                    pos = evt.EventObject.absoluteCoordinates(evt.mousePosition)
                    self.drawMarquee(self._dragDrawPos)
                    self.drawMarquee(pos)
        else:
            self.DragObject = None

    def moveDraggedObjects(self, evt):
        #         newX, newY = evt.EventObject.containerCoordinates(self.ActiveContainer,
        #                 evt.mousePosition)
        newX, newY = evt.EventObject.absoluteCoordinates(evt.mousePosition)
        oldX, oldY = self._dragOrigPos
        diffX = newX - oldX
        diffY = newY - oldY
        for ctl in self._draggedObjects:
            ctlX, ctlY = ctl._startDragPos
            ctl.Position = (ctlX + diffX, ctlY + diffY)

    def drawMarquee(self, pos):
        # Adjust the pos for the container
        offX, offY = 0, 0  # self.ActiveContainer.formCoordinates()
        x1, y1 = self._dragOrigPos
        x2, y2 = pos
        x2 -= offX
        y2 -= offY

        xpos = min(x1, x2)
        wd = abs(x1 - x2)
        ypos = min(y1, y2)
        ht = abs(y1 - y2)
        # self._drawSurface.Visible = True
        if self.Controller.SelectedClass:
            penColor = "gold"
            penWidth = 2
            lineStyle = "dash"
        else:
            penColor = "black"
            penWidth = 1
            lineStyle = "dot"

        xpos, ypos = self.ActiveContainer.relativeCoordinates((xpos, ypos))
        self.ActiveContainer.drawRectangle(
            xpos,
            ypos,
            wd,
            ht,
            lineStyle=lineStyle,
            penColor=penColor,
            penWidth=penWidth,
            mode="invert",
            persist=False,
        )
        self._dragDrawPos = pos

    def processLeftUp(self, obj, evt):
        if isinstance(obj.Parent, dRadioList):
            obj = obj.Parent
        if self.UseSizers:
            self.onLeftUp(evt, obj)
            return
        self.iterateCall("setMouseHandling", False)
        ui.callAfter(self._clearDraggedObjects)
        ox, oy = self._dragOrigPos
        nx, ny = obj.absoluteCoordinates(evt.mousePosition)
        dist = abs(nx - ox) + abs(ny - oy)
        wasSelecting = self._selecting
        if wasSelecting and (dist > 2):
            self.onLeftUp(evt, obj)
            return
        if (self._draggedObjects is not None) and (dist > 2):
            # We're finishing a drag operation
            self.Controller.Selection = self._draggedObjects
            self.redrawHandles(self._draggedObjects)
            return
        srcObj = self.DragObject
        if not srcObj:
            if obj is not self.ActiveContainer or wasSelecting:
                self.objectClick(obj, evt.shiftDown)
        else:
            # Clear the reference
            self.DragObject = None
            if self.UseSizers:
                # Make sure that the object wasn't dropped on itself.
                if srcObj is obj:
                    self._redraw()
                    return
                if isinstance(obj, dPanel) and not isinstance(
                    obj, (LayoutPanel, LayoutSpacerPanel)
                ):
                    # Make sure that it not just empty border space around
                    # child objects
                    nonLPkids = [
                        kid
                        for kid in obj.Children
                        if not isinstance(kid, (LayoutPanel, LayoutSpacerPanel))
                    ]
                    if nonLPkids:
                        # Don't allow the drop
                        self._redraw()
                        return
                # An item was dragged from somewhere else on
                # the design surface and dropped on the srcObj
                oSz = obj.ControllingSizer
                oSzIt = obj.ControllingSizerItem
                oProps = oSz.getItemProps(oSzIt)
                oPos = obj.getPositionInSizer()
                pSz = srcObj.ControllingSizer
                pSzIt = srcObj.ControllingSizerItem
                pProps = pSz.getItemProps(pSzIt)
                pPos = srcObj.getPositionInSizer()

                # Switch 'em! First, remove the objects from their sizers
                oSz.remove(obj)
                pSz.remove(srcObj)
                # Now add this panel to the object's old Sizer
                if isinstance(oSz, dGridSizer):
                    oSz.append(srcObj, "x", row=oPos[0], col=oPos[1])
                else:
                    oSz.insert(oPos, srcObj)
                newSzit = srcObj.ControllingSizerItem
                oSz.setItemProps(newSzit, oProps)

                # Now add the object to the old panel Sizer
                if isinstance(pSz, dGridSizer):
                    pSz.append(obj, "x", row=pPos[0], col=pPos[1])
                else:
                    pSz.insert(pPos, obj)
                newSzit = obj.ControllingSizerItem
                pSz.setItemProps(newSzit, pProps)
                self.Controller.updateLayout()
                self.layout()
            else:
                # Not using sizers
                self.stopResize(self._handleDragged, evt)

    def _clearDraggedObjects(self):
        self._draggedObjects = None

    def getBizobjTemplate(self):
        return """#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .. import biz

class %(tblTitle)sBizobj(biz.dBizobj):
    def afterInit(self):
        self.DataSource = "%(tbl)s"
        self.KeyField = "%(pk)s"
        self.addFrom("%(tbl)s")
%(fldDefs)s

    def validateRecord(self):
        %(tq)sReturning anything other than an empty string from
        this method will prevent the data from being saved.
        %(tq)s
        ret = ""
        # Add your business rules here.
        return ret

"""

    def getBizobjLoadTemplate(self):
        return """
    %(lowbiz)s = self.Application.biz.%(tblTitle)sBizobj(self.Connection)
    self.addBizobj(%(lowbiz)s)
"""

    def escapeQt(self, s):
        sl = "\\"
        qt = "'"
        return s.replace(sl, sl + sl).replace(qt, sl + qt)

    ### Begin Property Definitions  ###
    def _getActiveContainer(self):
        if self._activeContainer is None:
            self._activeContainer = self.mainPanel
        return self._activeContainer

    def _setActiveContainer(self, val):
        if self._constructed():
            if val is not self._activeContainer:
                # Changing! First clear any hilite
                if self._activeContainer is not None:
                    self._activeContainer.HiliteBorderWidth = 0
                self._activeContainer = val
                if val is not None:
                    self._activeContainer.HiliteBorderWidth = 2
                    self._activeContainer.HiliteBorderLineStyle = "dash"
        else:
            self._properties["ActiveContainer"] = val

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

    def _getControls(self):
        return self._controls

    def _setControls(self, ctls):
        self._controls = ctls

    def _getChildren(self):
        ret = []
        if isinstance(self, Wizard):
            ret = self._pages
        else:
            try:
                if self.mainPanel:
                    ret = self.mainPanel.Children
            except:
                pass
        return ret

    def _getDesEvents(self):
        if self.Controller:
            return self.Controller.getClassEvents(self._baseClass)
        else:
            return []

    def _getDesProps(self):
        ret = {
            "Caption": {"type": str, "readonly": False},
            "CxnName": {"type": str, "readonly": False},
            "Height": {"type": int, "readonly": False},
            "Width": {"type": int, "readonly": False},
            "Name": {"type": str, "readonly": False},
            "Left": {"type": int, "readonly": False},
            "Right": {"type": int, "readonly": False},
            "Top": {"type": int, "readonly": False},
            "Bottom": {"type": int, "readonly": False},
            "ShowCaption": {"type": bool, "readonly": False},
            "ShowMenuBar": {"type": bool, "readonly": False},
            "ShowToolBar": {"type": bool, "readonly": False},
            "MenuBarFile": {
                "type": "path",
                "readonly": False,
                "customEditor": "editMenuBarFile",
            },
            "Tag": {"type": "multi", "readonly": False},
            "Transparency": {"type": int, "readonly": False},
            "SaveRestorePosition": {"type": bool, "readonly": False},
        }
        if isinstance(self, Wizard):
            ret["Picture"] = {
                "type": "path",
                "readonly": False,
                "customEditor": "editStdPicture",
            }
            ret["PictureHeight"] = {"type": int, "readonly": False}
            ret["PictureWidth"] = {"type": int, "readonly": False}
        elif isinstance(self, dDialog):
            ret["AutoSize"] = {"type": bool, "readonly": False}
            ret["Centered"] = {"type": bool, "readonly": False}
            if isinstance(self, dStandardButtonDialog):
                ret["CancelOnEscape"] = {"type": bool, "readonly": False}
        return ret

    def _getDragObject(self):
        return self._dragObject

    def _setDragObject(self, val):
        if val is self._dragObject:
            # redundant
            return
        # If there is an existing object, make it visible again
        if self._dragObject:
            self._dragObject.Visible = True
            if self._dragImage:
                self.removeDrawnObject(self._dragImage)
                self._dragImage = None
            self._dragOrigPos = (0, 0)
        if val is not None:
            if not self._handleDragged:
                # Save the original position of the mouse down
                (formX, formY) = self._dragOrigPos = self.getMousePosition()
                (objX, objY) = self._dragObjOffset = val.getMousePosition()
                # Create an image of the control
                self._dragImage = self.drawBitmap(
                    val.getCaptureBitmap(), x=formX - objX, y=formY - objY
                )
        self._dragObject = val

    def _getIsContainer(self):
        return self._canContain

    def _getMenuBarFile(self):
        return self._menuBarFile

    def _setMenuBarFile(self, val):
        self._menuBarFile = val

    def _getSelection(self):
        return self.selectedControls

    def _setSelection(self, ctls):
        self.selectedControls = ctls

    def _getUseSizers(self):
        try:
            ret = self._useSizers
        except AttributeError:
            ret = self._useSizers = True
        return ret

    def _setUseSizers(self, val):
        if self._constructed():
            self._useSizers = val
        else:
            self._properties["UseSizers"] = val

    ActiveContainer = property(
        _getActiveContainer,
        _setActiveContainer,
        None,
        _("Container currently active for creating controls  (dPanel (usually))"),
    )

    Controller = property(
        _getController,
        _setController,
        None,
        _("Object to which this one reports events  (object (varies))"),
    )

    Controls = property(
        _getControls,
        _setControls,
        None,
        _("List of all control(s) in the designer.   (list)"),
    )

    Children = property(_getChildren, None, None, _("""Children of the main panel of this form."""))

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
            """Returns a dict of editable properties for the form, with the
            prop names as the keys, and the value for each another dict,
            containing the following keys: 'type', which controls how to display
            and edit the property, and 'readonly', which will prevent editing
            when True. (dict)"""
        ),
    )

    DragObject = property(
        _getDragObject,
        _setDragObject,
        None,
        _("Reference to the object being dragged on the form  (ClassDesignerControlMixin)"),
    )

    IsContainer = property(
        _getIsContainer, None, None, _("Can we add controls to this form?  (bool)")
    )

    MenuBarFile = property(
        _getMenuBarFile,
        _setMenuBarFile,
        None,
        _("Path to the menu designer file used for this form's MenuBarClass  (str)"),
    )

    Selection = property(
        _getSelection,
        _setSelection,
        None,
        _("List of control(s) currently selected for editing.   (list)"),
    )

    UseSizers = property(
        _getUseSizers,
        _setUseSizers,
        None,
        _("Does the this form use sizers for its layout?  (bool)"),
    )
