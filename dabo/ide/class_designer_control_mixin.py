# -*- coding: utf-8 -*-
import os

from .. import ui
from ..lib import utils as libutils
from ..dLocalize import _
from ..lib.utils import ustr
from .. import events
from .. import application
from .. import dColors
from ..ui import dKeys
from ..ui import dialogs
from ..ui import dBitmap
from ..ui import dBitmapButton
from ..ui import dButton
from ..ui import dCheckBox
from ..ui import dCheckList
from ..ui import dColumn
from ..ui import dComboBox
from ..ui import dDataControlMixin
from ..ui import dDialog
from ..ui import dDropdownList
from ..ui import dEditBox
from ..ui import dEditor
from ..ui import dForm
from ..ui import dFormMain
from ..ui import dGauge
from ..ui import dGrid
from ..ui import dHtmlBox
from ..ui import dImage
from ..ui import dLabel
from ..ui import dLed
from ..ui import dLine
from ..ui import dListBox
from ..ui import dListControl
from ..ui import dMaskedTextBox
from ..ui import dMediaControl
from ..ui import dMenu
from ..ui import dMenuBar
from ..ui import dMenuItem
from ..ui import dPage
from ..ui import dPageFrame
from ..ui import dPageFrameMixin
from ..ui import dPageFrameNoTabs
from ..ui import dPageList
from ..ui import dPageSelect
from ..ui import dPageStyled
from ..ui import dPanel
from ..ui import dRadioList
from ..ui import dScrollPanel
from ..ui import dShell
from ..ui import dSlidePanel
from ..ui import dSlidePanelControl
from ..ui import dSlider
from ..ui import dSpinner
from ..ui import dSplitter
from ..ui import dStatusBar
from ..ui import dTextBox
from ..ui import dTimer
from ..ui import dToggleButton
from ..ui import dTreeView
from .class_designer_components import LayoutPanel
from .class_designer_components import LayoutSizer
from .class_designer_components import LayoutBorderSizer
from .class_designer_components import LayoutGridSizer
from .class_designer_components import LayoutSaverMixin
from .class_designer_components import classFlagProp
from .class_designer_exceptions import PropertyUpdateException

dabo_module = settings.get_dabo_package()


class ClassDesignerControlMixin(LayoutSaverMixin):
    """The purpose of this mixin class is to add the features to the native
    controls so that they will work in the dabo form design surface.
    """

    def __init__(self, parent, *args, **kwargs):
        # Smallest dimension a control can be sized
        self.minDimension = 10
        # When creating the control without sizers, this is the default size
        self.defaultWd = self.defaultHt = 10
        # Holds the ID that identifies the control type in the designer
        self.typeID = -1
        # Are we the main control in the designer, or contained within the main?
        self._isMain = False
        # Need to hide the actual RegID property and its setter
        self._tmpRegID = None
        # Let the rest of the framework know that this is class_designer object
        self.isDesignerControl = True
        # Is this control being edited?
        self._selected = False
        # Controls the hilite when the control is selected
        self._hiliteBorderColor = "gold"
        self._hiliteBorderLineStyle = "dot"
        self._hiliteBorderWidth = 0
        # Create the actual hilite border object
        self._hiliteBorder = None
        # Caches the form's setting for 'useSizers'
        self._usingSizers = None
        # References for resizing interactively
        self._startX = self._startY = self._startWd = self._startHt = 0
        # Reference for dragging interactively
        self._startDragPos = (0, 0)

        # Turned this off in Win; it was making controls disappear
        # on that platform only.
        ### NOTE: seems to not flicker as much with this commented out (at least on Mac).
        # self.autoClearDrawings = (self.Application.Platform != "Win")

        # Store the defaults for the various props
        self._propDefaults = {}
        for prop in list(self.DesignerProps.keys()):
            try:
                self._propDefaults[prop] = getattr(self, prop)
            except Exception as e:
                nm = self.Name
                dabo_module.error(
                    _(
                        "Could not set default prop value: object: %(nm)s; property: %(prop)s; error: %(e)s"
                    )
                    % locals()
                )
        # Update bindings; do control-specific things.
        if isinstance(self, dGrid):
            coolEvents = (
                events.GridRowSize,
                events.GridColSize,
                events.GridHeaderMouseLeftDown,
                events.GridHeaderMouseMove,
                events.GridHeaderMouseLeftUp,
            )
            baevents = []
            for bnd in self._eventBindings:
                if bnd[0] not in coolEvents:
                    baevents.append(bnd)
            for bad in baevents:
                self._eventBindings.remove(bad)

            # Need to kill the sorting behavior
            def _killProcessSort(col):
                pass

            self.processSort = _killProcessSort
            # Kill cell editing
            self._vetoAllEditing = True
            self.bindEvent(events.GridCellSelected, self.Controller.onGridCellSelected)
            self.bindEvent(events.GridHeaderMouseLeftUp, self.Controller.onGridHeaderSelected)
        elif isinstance(self, dSplitter):
            pass
        elif isinstance(self, dImage):
            self.bindEvent(events.Resize, self._onResize)
        elif isinstance(self, (dSlidePanelControl, dSlidePanel)):
            coolEvents = (events.SlidePanelCaptionClick, events.SlidePanelChange)
            baevents = []
            for bnd in self._eventBindings:
                if bnd[0] not in coolEvents:
                    baevents.append(bnd)
            for bad in baevents:
                self._eventBindings.remove(bad)
        else:
            # This removes all previously-defined bindings
            self.unbindEvent(None)
        self.noUpdateForm = False

        # Set up some defaults
        if isinstance(self, dButton):
            self.defaultWd = 100
            self.defaultHt = 24
            if not self.Caption:
                self.Caption = "Button"
        elif isinstance(self, (dLabel, dTextBox)):
            self.defaultWd = 100
            self.defaultHt = 24
            if isinstance(self, dLabel) and not self.Caption:
                self.Caption = "Label"
        elif isinstance(self, dTreeView):
            self.defaultWd = 200
            self.defaultHt = 360
            self.setRootNode("Tree")
            # Bind the selected node to the current selection
            self.bindEvent(events.TreeSelection, self.desSelectNode)
        elif isinstance(self, (dPageFrame, dPageList, dPageSelect, dPageStyled, dPageFrameNoTabs)):
            self.defaultWd = 400
            self.defaultHt = 300
            # Bind the active page to the current selection
            self.bindEvent(events.PageChanged, self.desSelectPage)
        elif isinstance(self, dSlidePanel):
            self.bindEvent(events.SlidePanelChange, self.desSlidePanelChg)
        elif isinstance(self, (dPanel, dImage, dBitmap, dBitmapButton, dToggleButton)):
            self.defaultWd = 60
            self.defaultHt = 60
        else:
            self.defaultWd = self.defaultHt = 100
        #         self.MinimumSize = (self.defaultWd, self.defaultHt)

        # This seems to happen after the main autobinding, so
        # it is necessary to call this manually.
        #         self.autoBinevents()
        # Need to set the properties here to get the drawing updated.
        self.HiliteBorderColor = "gold"
        self.HiliteBorderLineStyle = "dot"
        self.HiliteBorderWidth = 0

        # If we are on a sizer-less design, create the handles for the
        # control ahead of time.
        if not self.UsingSizers:
            self.Form.createControlHandles(self)

    #         self.bindKey("left", self.Form.keyMoveLeft)

    def _insertPageOverride(
        self,
        pos,
        pgCls=None,
        caption="",
        imgKey=None,
        makeActive=False,
        ignoreOverride=False,
    ):
        if not isinstance(self, self.Controller.pagedControls):
            return

        cnt = self.Controller
        if cnt.openingClassXML or not isinstance(pgCls, str):
            tmpPgCls = self.Controller.getControlClass(dPage)
            pg = self.insertPage(pos, tmpPgCls, ignoreOverride=True)
            pg.Sizer = LayoutSizer("v")
            LayoutPanel(pg)
        else:
            dct = cnt._importClassXML(pgCls)
            atts = dct["attributes"]
            nm = self._extractKey(atts, "Name")
            atts["NameBase"] = nm
            tmpPgCls = cnt.getControlClass(dPage)
            pg = self.insertPage(pos, tmpPgCls, ignoreOverride=True)
            classID = self._extractKey(atts, "classID", "")
            pg.setPropertiesFromAtts(atts)
            pg.classID = classID
            prop = classFlagProp
            pg.__setattr__(prop, pgCls)
            pth = libutils.relativePath(pgCls)
            pth = os.path.abspath(os.path.split(pth)[0])
            cnt._basePath = pth
            # For some reason, setting DefaultBorder causes a segfault!
            # This hack turns it off.
            propBorder = self.Controller._propagateDefaultBorder
            cnt._propagateDefaultBorder = False
            # We need to set _srcObj and create a dummy layout panel
            # so that the recreateChildren() code can work properly.
            cnt._srcObj = pg
            pg.Sizer = LayoutSizer("v")
            LayoutPanel(pg)
            # OK, we can create the children of the page now.
            cnt.recreateChildren(pg, dct["children"], None, False)
            cnt._propagateDefaultBorder = propBorder
        if makeActive:
            self.SelectedPage = pg
        return pg

    def makeSizer(self):
        if isinstance(self, dialogs.WizardPage):
            self.Sizer = LayoutSizer(
                "v",
                DefaultSpacing=5,
                DefaultBorder=12,
                DefaultBorderLeft=True,
                DefaultBorderRight=True,
            )
        else:
            return super().makeSizer()

    def bringToFront(self):
        super().bringToFront()
        prn = self.Parent
        if prn is self.Form.mainPanel:
            prn = self.Form
        kids = prn.Children[:]
        kids.remove(self)
        kids.append(self)
        prn.zChildren = kids

    def sendToBack(self):
        super().sendToBack()
        prn = self.Parent
        if prn is self.Form.mainPanel:
            prn = self.Form
        kids = prn.Children[:]
        kids.remove(self)
        kids.insert(0, self)
        prn.zChildren = kids

    def onKeyChar(self, evt):
        if isinstance(self, (dPage, dColumn)):
            # The key will get processed by the container
            return
        self.Form.onKeyChar(evt)

    def _onResizeHiliteBorder(self, evt):
        """Called when the control is resized."""
        brd = self._hiliteBorder
        brd.Width, brd.Height = self.Width, self.Height

    def setMouseHandling(self, turnOn):
        """When turnOn is True, sets all the mouse event bindings. When
        it is False, removes the bindings.
        """
        if turnOn:
            self.bindEvent(events.MouseMove, self.handleMouseMove)
        else:
            self.unbindEvent(events.MouseMove)

    def handleMouseMove(self, evt):
        self.Form.onMouseDrag(evt)

    def onMouseLeftDown(self, evt):
        if isinstance(self, (dPageFrameMixin, dSplitter)):
            pass
        else:
            if not isinstance(self, dTreeView):
                evt.stop()
            if not self.UsingSizers:
                self.Form.onControlLeftDown(evt)

    def onMouseLeftUp(self, evt):
        if isinstance(self, dSplitter):
            pass
        else:
            if not isinstance(self, dTreeView):
                evt.stop()
            else:
                nd = self.getNodeUnderMouse(includeSpace=True, includeButton=False)
                if nd is not None:
                    return
            self.Form.processLeftUp(self, evt)

    def onMouseLeftDoubleClick(self, evt):
        self.Form.processLeftDoubleClick(evt)

    def onEditContainer(self, evt):
        self.Form.ActiveContainer = self

    def onMouseRightClick(self, evt):
        if isinstance(self, dTreeView):
            evt.stop()
            self.onContextMenu(evt)

    def onContextMenu(self, evt):
        # If it is a LayoutPanel or page, return - the event
        # is handled elsewhere
        evt.stop()
        if self.UsingSizers and isinstance(self, (dPage, LayoutPanel)):
            return
        if isinstance(self.Parent, dRadioList):
            self.Parent.onContextMenu(evt)
            return
        pop = self.createContextMenu(evt)
        self.showContextMenu(pop)

    def createContextMenu(self, evt=None):
        pop = None
        if self.UsingSizers:
            if isinstance(self, (dPanel, dScrollPanel, dPage)):
                pop = self.Controller.getControlMenu(self, True)
        else:
            if self is self.Form.ActiveContainer:
                # If the control can contain child objects, get that menu.
                pop = self.Controller.getControlMenu(self, False)
        if pop is None:
            pop = dMenu()
        if len(pop.Children):
            pop.prependSeparator()
        if not self.UsingSizers and self.IsContainer and not self is self.Form.ActiveContainer:
            pop.prepend(_("Edit Contents"), OnHit=self.onEditContainer)
        if len(pop.Children):
            pop.prependSeparator()
        pop.prepend(_("Edit Code"), OnHit=self.onEditCode)
        pop.prependSeparator()
        if not self.UsingSizers and self is self.Form.ActiveContainer:
            if self.Controller.Clipboard:
                pop.prepend(_("Paste"), OnHit=self.onPaste)
        else:
            pop.prepend(_("Delete"), OnHit=self.onDelete)
            pop.prepend(_("Copy"), OnHit=self.onCopy)
            pop.prepend(_("Cut"), OnHit=self.onCut)
        if isinstance(self, dPage):
            # Add option to delete the page or the entire pageframe
            pop.prependSeparator()
            sepAdded = True
            pop.prepend(_("Delete the entire Paged Control"), OnHit=self.Parent.onDelete)
            pop.prepend(_("Delete this Page"), OnHit=self.onDelete)

        if isinstance(self, dTreeView):
            self.activeNode = self.Selection
            if isinstance(self.activeNode, (list, tuple)):
                self.activeNode = self.activeNode[0]
            pop.append(_("Add Child Node"), OnHit=self.onAddChild)
            if not self.activeNode.IsRootNode:
                pop.append(_("Add Sibling Node"), OnHit=self.onAddSibling)
            if not self.Editable:
                pop.append(_("Change Node Caption"), OnHit=self.onChangeCaption)
            if not self.activeNode.IsRootNode:
                pop.append(_("Delete this node"), OnHit=self.onDelNode)
        elif isinstance(
            self,
            (
                dLabel,
                dButton,
                dCheckBox,
                dBitmapButton,
                dToggleButton,
                dPage,
                dColumn,
                dialogs.WizardPage,
            ),
        ):
            pop.append(_("Change Caption"), OnHit=self.onChangeCaption)
        if self.UsingSizers:
            if self.Controller.addSlotOptions(self, pop, sepBefore=True):
                # Add the Sizer editing option
                pop.appendSeparator()
                pop.append(_("Edit Sizer Settings"), OnHit=self.onEditSizer)
        return pop

    def getClass(self):
        """Returns a string representing the class's name. Default behavior
        is to return the BaseClass, but this allows for specific subclasses
        to override that behavior.
        """
        if isinstance(self, dialogs.WizardPage):
            ret = "dialogs.WizardPage"
        else:
            ret = super().getClass()
        return ret

    def onAddChild(self, evt):
        nd = self.activeNode
        self.activeNode = None
        txt = ui.getString(_("New Node Caption?"), _("Adding Child Node"))
        if txt is not None:
            nd.appendChild(txt)
        self.Controller.updateLayout()

    def onAddSibling(self, evt):
        nd = self.activeNode
        self.activeNode = None
        txt = ui.getString(_("New Node Caption?"), _("Adding Sibling Node"))
        if txt is not None:
            nd.parent.appendChild(txt)
        self.Controller.updateLayout()

    def onDelNode(self, evt):
        nd = self.activeNode
        self.activeNode = None
        self.removeNode(nd)
        self.Controller.updateLayout()

    def onChangeCaption(self, evt):
        if isinstance(self, dTreeView):
            nd = self.activeNode
            self.activeNode = None
            target = nd
            title = _("Changing Node")
            defVal = nd.Caption
        else:
            target = self
            title = _("Changing Caption")
            defVal = self.Caption
        txt = ui.getString(
            _("New Caption"),
            caption=title,
            defaultValue=defVal,
            Width=500,
            SelectOnEntry=True,
        )
        if txt is not None:
            target.Caption = txt
        self.Controller.updateLayout()

    def onPaste(self, evt):
        self.Controller.pasteObject(self)

    def onEditSizer(self, evt):
        """Called when the user selects the context menu option
        to edit this control's sizer information.
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

    def onEditCode(self, evt):
        """Open the editor"""
        self.Form.editCode(self)

    def onDelete(self, evt):
        # When a page in a pageframe gets this event, pass it up
        # to its parent.
        if isinstance(self, dPage):
            ui.callAfter(self.Parent.removePage, self)
            ui.callAfter(self.Controller.updateLayout)
            return
        if self.UsingSizers and hasattr(self, "ControllingSizer"):
            self.ControllingSizer.delete(self)
        else:
            self.Form.select(self.Parent)
            ui.callAfter(self.release)
            ui.callAfter(self.Controller.updateLayout)

    def isSelected(self):
        return self.Parent.isSelected(self)

    def desSelectPage(self, evt):
        """Called when a page is selected"""
        if not self.UsingSizers:
            return
        try:
            obj = self.Controller.Selection[0]
            if obj.isContainedBy(self.SelectedPage):
                # No need to do anything
                return
        except:
            pass
        self.Form.selectControl(self.SelectedPage, False)

    def desSelectNode(self, evt):
        """Called when a node in a tree is selected"""
        self.Form.selectControl(self.Selection, False)

    def desSlidePanelChg(self, evt):
        ui.callAfterInterval(100, self.Form.refresh)

    def moveControl(self, pos, shft=False):
        """Wraps the Move command with the necessary
        screen updating stuff.
        """
        self.Position = pos
        ######
        if not self.noUpdateForm:
            self.Form.redrawHandles(self)

    def resizeControl(self, sz):
        """Wraps the SetSize command with the necessary
        screen updating stuff.
        """
        self.Size = sz
        self.Form.redrawHandles(self)

    def nudgeControl(self, horiz, vert):
        """Used to move the control relative to its current position.
        Each direction is the number of pixels to move in that direction,
        with negative moving left/up.
        """
        lf, top = self.Position
        lfNew = lf + horiz
        topNew = top + vert
        self.moveControl((lfNew, topNew))

    def growControl(self, horiz, vert):
        """Used to resize the control relative to its current size.
        Each direction is the number of pixels to change the
        size in that direction
        """
        wd, ht = self.Size
        wdNew = max(wd + horiz, self.minDimension)
        htNew = max(ht + vert, self.minDimension)
        self.resizeControl((wdNew, htNew))

    def startResize(self, evt, up, right, down, left):
        """Determine the offset of the mouse, depending on the
        handle selected.
        """
        self._startX, self._startY = self.lastPos = self.Position
        self._startWd, self._startHt = self.lastSize = self.Size

    def resize(self, evt, up, right, down, left):
        self.noUpdateForm = True
        self.stopResize(evt, up, right, down, left)
        self.noUpdateForm = False
        return

    def stopResize(self, evt, up, right, down, left):
        mouseX, mouseY = evt.mousePosition
        obj = evt.EventObject
        if obj is self:
            offX, offY = self.Position
        elif obj is self.Parent:
            offX, offY = 0, 0
        else:
            fmX, fmY = obj.formCoordinates()
            fpX, fpY = self.Parent.formCoordinates()
            offX = fmX - fpX
            offY = fmY - fpY

        mouseX += offX
        mouseY += offY

        # Start assuming no change. Then change as needed
        x, y = self.Position
        wd, ht = self.Size
        origX = self._startX
        origY = self._startY
        origRt = self._startX + self._startWd
        origBot = self._startY + self._startHt

        yBot = y + ht
        xRt = x + wd
        newX = x
        newY = y
        newWd = wd
        newHt = ht

        # Check boundary conditions
        if up:
            if mouseY > origBot:
                # We've dragged the top edge below the original bottom
                newY = origBot
                newHt = max(self.minDimension, mouseY - newY)
            else:
                newY = min(mouseY, yBot - self.minDimension)
                newHt = yBot - newY

        elif down:
            if mouseY < origY:
                # We've dragged the bottom edge below the original top
                newY = mouseY
                newHt = max(self.minDimension, origY - mouseY)
            else:
                newY = y
                newHt = max(mouseY - newY, self.minDimension)

        if left:
            if mouseX > origRt:
                # We've dragged the left edge past the original right
                newX = origRt
                newWd = max(self.minDimension, mouseX - newX)
            else:
                newX = min(mouseX, xRt - self.minDimension)
                newWd = xRt - newX

        elif right:
            if mouseX < origX:
                # We've dragged the right edge past the original left
                newX = mouseX
                newWd = max(self.minDimension, origX - mouseX)
            else:
                newX = x
                newWd = max(mouseX - newX, self.minDimension)

        self.Left = newX
        self.Top = newY
        self.Size = (newWd, newHt)

        # Reset the last pos/size info
        self.lastPos = (newX, newY)
        self.lastSize = (newWd, newHt)

    def onControlSetFocus(self, evt):
        """Tries to 'eat' the focus event so that the controls
        never get focus. We don't want them 'live' during design.
        """
        evt.stop()
        pass

    def customUpdate(self, prop, val):
        """We need to check if the property being changed requires custom
        update code. If so, handle it here and return True, indicating that the
        update has already been handled by this method.
        """
        ret = False
        return ret

    ## property defs start here  ##
    def _getChildren(self):
        try:
            ret = self._superBase._getChildren(self)
        except AttributeError:
            try:
                ret = self.__class__.superControl._getChildren(self)
            except:
                print("NO SUPER CLASS FOUND!!!!!")
                ret = []
        if isinstance(self, dialogs.WizardPage):
            # Skip the title and separator line.
            ret = ret[2:]
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
        return self.Controller.getClassEvents(self._baseClass)

    def _getDesProps(self):
        useSizers = self.Controller.UseSizers
        ret = {
            "Enabled": {"type": bool, "readonly": False},
            "Name": {"type": str, "readonly": False},
            "RegID": {"type": str, "readonly": False},
            "TabStop": {"type": bool, "readonly": False},
            "Tag": {"type": "multi", "readonly": False},
            "ToolTipText": {"type": str, "readonly": False},
            "Transparency": {"type": int, "readonly": False},
            "Visible": {"type": bool, "readonly": False},
        }
        captionProps = {"Caption": {"type": str, "readonly": False}}
        choiceProps = {
            "Choices": {
                "type": "choice",
                "readonly": False,
                "customEditor": "editChoice",
            },
            "Keys": {"type": "choice", "readonly": False, "customEditor": "editKeys"},
            "ValueMode": {
                "type": list,
                "readonly": False,
                "values": ["String", "Position", "Key"],
            },
        }
        colorProps = {
            "BackColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "ForeColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
        }
        columnProps = {
            "Order": {"type": int, "readonly": False},
            "Width": {"type": int, "readonly": False},
            "DataField": {"type": str, "readonly": False},
            "HeaderBackColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "HeaderFont": {
                "type": "font",
                "readonly": False,
                "customEditor": "editHeaderFont",
            },
            "HeaderFontBold": {"type": bool, "readonly": False},
            "HeaderFontFace": {
                "type": list,
                "readonly": False,
                "values": ui.getAvailableFonts(),
            },
            "HeaderFontItalic": {"type": bool, "readonly": False},
            "HeaderFontSize": {"type": int, "readonly": False},
            "HeaderFontUnderline": {"type": bool, "readonly": False},
            "HeaderForeColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "HeaderHorizontalAlignment": {
                "type": list,
                "readonly": False,
                "values": ["Automatic", "Left", "Center", "Right"],
            },
            "HeaderVerticalAlignment": {
                "type": list,
                "readonly": False,
                "values": ["Automatic", "Top", "Middle", "Bottom"],
            },
            "ListEditorChoices": {
                "type": "choice",
                "readonly": False,
                "customEditor": "editChoice",
            },
            "HorizontalAlignment": {
                "type": list,
                "readonly": False,
                "values": ["Automatic", "Left", "Center", "Right"],
            },
            "VerticalAlignment": {
                "type": list,
                "readonly": False,
                "values": ["Top", "Center", "Bottom"],
            },
            "Editable": {"type": bool, "readonly": False},
            "Expand": {"type": bool, "readonly": False},
            "Searchable": {"type": bool, "readonly": False},
            "Sortable": {"type": bool, "readonly": False},
        }
        comboProps = {"AppendOnEnter": {"type": bool, "readonly": False}}
        dataProps = {
            "DataSource": {"type": str, "readonly": False},
            "DataField": {"type": str, "readonly": False},
            "Value": {"type": "multi", "readonly": False},
        }
        editorProps = {
            "CommentString": {"type": str, "readonly": False},
            "ShowCallTips": {"type": bool, "readonly": False},
            "ShowCodeFolding": {"type": bool, "readonly": False},
            "ShowEOL": {"type": bool, "readonly": False},
            "ShowLineNumbers": {"type": bool, "readonly": False},
            "ShowWhiteSpace": {"type": bool, "readonly": False},
            "SyntaxColoring": {"type": bool, "readonly": False},
            "TabWidth": {"type": int, "readonly": False},
            "WordWrap": {"type": bool, "readonly": False},
        }
        fontProps = {
            "Font": {"type": "font", "readonly": False, "customEditor": "editFont"},
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
        gridProps = {
            "ActivateEditorOnSelect": {"type": bool, "readonly": False},
            "AlternateRowColoring": {"type": bool, "readonly": False},
            "CellHighlightWidth": {"type": int, "readonly": False},
            "ColumnCount": {"type": int, "readonly": False},
            "DataSource": {"type": str, "readonly": False},
            "Editable": {"type": bool, "readonly": False},
            "HeaderBackColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "HeaderForeColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "HeaderHeight": {"type": int, "readonly": False},
            "HeaderHorizontalAlignment": {
                "type": list,
                "readonly": False,
                "values": ["Left", "Center", "Right"],
            },
            "HeaderVerticalAlignment": {
                "type": list,
                "readonly": False,
                "values": ["Top", "Middle", "Bottom"],
            },
            "RowColorEven": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "RowColorOdd": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "RowHeight": {"type": int, "readonly": False},
            "Searchable": {"type": bool, "readonly": False},
            "SelectionBackColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "SelectionForeColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "SelectionMode": {
                "type": list,
                "readonly": False,
                "values": ["Cell", "Row", "Column"],
            },
            "Sortable": {"type": bool, "readonly": False},
            "ShowCellBorders": {"type": bool, "readonly": False},
            "ShowHeaders": {"type": bool, "readonly": False},
            "ShowRowLabels": {"type": bool, "readonly": False},
        }
        imageProps = {
            "ScaleMode": {
                "type": list,
                "readonly": False,
                "values": ["Clip", "Proportional", "Stretch"],
            }
        }
        labelProps = {
            "Alignment": {
                "type": list,
                "readonly": False,
                "values": ["Left", "Center", "Right"],
            },
            "AutoResize": {"type": bool, "readonly": False},
        }
        ledProps = {
            "OffColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "OnColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "On": {"type": bool, "readonly": False},
        }
        listControlProps = {
            "ColumnCount": {"type": int, "readonly": False},
            "ExpandColumn": {"type": int, "readonly": False},
            "ExpandToFit": {"type": bool, "readonly": False},
            "HeaderVisible": {"type": bool, "readonly": False},
            "HorizontalRules": {"type": bool, "readonly": False},
            "RowCount": {"type": int, "readonly": True},
            "SortColumn": {"type": int, "readonly": False},
            "SortOnHeaderClick": {"type": bool, "readonly": False},
            "ValueColumn": {"type": int, "readonly": False},
            "VerticalRules": {"type": bool, "readonly": False},
        }
        maskedTextBoxProps = {
            "Format": {
                "type": list,
                "readonly": False,
                "values": [""] + dMaskedTextBox.getFormats(),
            },
            "InputCodes": {"type": str, "readonly": lambda self: bool(self.Format)},
            "Mask": {"type": str, "readonly": lambda self: bool(self.Format)},
            "ValueMode": {
                "type": list,
                "readonly": False,
                "values": ["Masked", "Unmasked"],
            },
        }
        mediaControlProps = {
            "Loop": {"type": bool, "readonly": False},
            "ShowControls": {"type": bool, "readonly": False},
            "Source": {"type": str, "readonly": False},
            "TimeInSeconds": {"type": bool, "readonly": False},
            "Volume": {"type": int, "readonly": False},
        }
        multiSelectProps = {"MultipleSelect": {"type": bool, "readonly": False}}
        nodeProps = {
            "Image": {
                "type": "path",
                "readonly": False,
                "customEditor": "editStdPicture",
            }
        }
        panelProps = {
            "AlwaysResetSizer": {"type": bool, "readonly": False},
            "Buffered": {"type": bool, "readonly": False},
            "MinSizerHeight": {"type": int, "readonly": False},
            "MinSizerWidth": {"type": int, "readonly": False},
        }
        pictureProps = {
            "Picture": {
                "type": "path",
                "readonly": False,
                "customEditor": "editStdPicture",
            }
        }
        posProps = {
            "Left": {"type": int, "readonly": useSizers},
            "Right": {"type": int, "readonly": useSizers},
            "Top": {"type": int, "readonly": useSizers},
            "Bottom": {"type": int, "readonly": useSizers},
            "Height": {"type": int, "readonly": False},
            "Width": {"type": int, "readonly": False},
        }
        radioProps = {
            "Orientation": {
                "type": list,
                "readonly": False,
                "values": ["Horizontal", "Vertical"],
            },
            "ShowBox": {"type": bool, "readonly": False},
        }
        sizerProps = {
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
        sliderProps = {
            "Max": {"type": int, "readonly": False},
            "Min": {"type": int, "readonly": False},
            "ShowLabels": {"type": bool, "readonly": False},
        }
        slidePanelControlProps = {
            "CollapseToBottom": {"type": bool, "readonly": False},
            "ExpandContent": {"type": bool, "readonly": False},
            "PanelCount": {"type": int, "readonly": True},
            "SingleClick": {"type": bool, "readonly": False},
            "Singleton": {"type": bool, "readonly": False},
        }
        slidePanelProps = {
            "BarColor1": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "BarColor2": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "BarStyle": {
                "type": list,
                "readonly": False,
                "values": [
                    "Borderless",
                    "BorderOnly",
                    "FilledBorder",
                    "HorizontalFill",
                    "VerticalFill",
                ],
            },
            "Border": {"type": int, "readonly": False},
            "CaptionForeColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "PanelPosition": {"type": int, "readonly": False},
        }
        splitterProps = {
            "CanUnsplit": {"type": bool, "readonly": False},
            "MinimumPanelSize": {"type": int, "readonly": False},
            "Orientation": {
                "type": list,
                "readonly": False,
                "values": ["Horizontal", "Vertical"],
            },
            "PanelClass": {"type": str, "readonly": False},
            "SashPosition": {"type": int, "readonly": False},
            "ShowPanelSplitMenu": {"type": bool, "readonly": False},
            "Split": {"type": bool, "readonly": False},
        }
        spinnerProps = {
            "Increment": {"type": "multi", "readonly": False},
            "Max": {"type": int, "readonly": False},
            "Min": {"type": int, "readonly": False},
            "SpinnerWrap": {"type": bool, "readonly": False},
        }
        textProps = {
            "Alignment": {
                "type": list,
                "readonly": False,
                "values": ["Left", "Center", "Right"],
            },
            "ForceCase": {
                "type": list,
                "readonly": False,
                "values": ["Upper", "Lower", "Title", "None"],
            },
            "ReadOnly": {"type": bool, "readonly": False},
        }
        htmlTextProps = {
            "Page": {"type": str, "readonly": False},
            "RespondToLinks": {"type": bool, "readonly": False},
            "ShowScrollBars": {"type": bool, "readonly": False},
            "Source": {"type": str, "readonly": False},
        }
        scrollProps = {
            "HorizontalScroll": {"type": bool, "readonly": False},
            "VerticalScroll": {"type": bool, "readonly": False},
        }
        treeProps = {
            "Editable": {"type": bool, "readonly": False},
            "MultipleSelect": {"type": bool, "readonly": False},
            "ShowButtons": {"type": bool, "readonly": False},
            "ShowLines": {"type": bool, "readonly": False},
            "ShowRootNode": {"type": bool, "readonly": False},
            "ShowRootNodeLines": {"type": bool, "readonly": False},
        }
        gridSizerProps = {
            "Sizer_RowExpand": {"type": bool, "readonly": False},
            "Sizer_ColExpand": {"type": bool, "readonly": False},
            "Sizer_RowSpan": {"type": int, "readonly": False},
            "Sizer_ColSpan": {"type": int, "readonly": False},
        }
        pageFrameProps = {
            "PageCount": {"type": int, "readonly": False},
            "TabPosition": {
                "type": list,
                "readonly": False,
                "values": ["Top", "Bottom", "Left", "Right"],
            },
        }
        pageListProps = {"ListSpacing": {"type": int, "readonly": False}}
        pageStyleProps = {
            "ActiveTabColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "ActiveTabTextColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "InactiveTabTextColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "ShowDropdownTabList": {"type": "bool", "readonly": False},
            "ShowMenuCloseButton": {"type": "bool", "readonly": False},
            "ShowMenuOnSingleTab": {"type": "bool", "readonly": False},
            "ShowPageCloseButtons": {"type": "bool", "readonly": False},
            "ShowNavButtons": {"type": "bool", "readonly": False},
            "TabAreaColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "TabPosition": {
                "type": list,
                "readonly": False,
                "values": ["Top", "Bottom"],
            },
            "TabSideIncline": {"type": int, "readonly": False},
            "TabStyle": {
                "type": list,
                "readonly": False,
                "values": ["Default", "VC8", "VC71", "Fancy", "Firefox"],
            },
        }
        borderProps = {
            "BorderColor": {
                "type": "color",
                "readonly": False,
                "customEditor": "editColor",
            },
            "BorderLineStyle": {
                "type": list,
                "readonly": False,
                "values": ["Solid", "Dot", "Dash", "DotDash"],
            },
            "BorderStyle": {
                "type": list,
                "readonly": False,
                "values": [
                    "None",
                    "Simple",
                    "Sunken",
                    "Raised",
                    "Double",
                    "Static",
                    "Default",
                ],
            },
            "BorderWidth": {"type": int, "readonly": False},
        }
        wizardPageProps = {
            "TitleBold": {"type": bool, "readonly": False},
            "TitleFace": {
                "type": list,
                "readonly": False,
                "values": ui.getAvailableFonts(),
            },
            "TitleItalic": {"type": bool, "readonly": False},
            "TitleSize": {"type": int, "readonly": False},
        }

        # Add the controlling sizer props
        if hasattr(self, "ControllingSizer"):
            csz = self.ControllingSizer
            if csz:
                ret.update(sizerProps)
            if isinstance(csz, LayoutGridSizer):
                ret.update(gridSizerProps)
        if isinstance(self, dDataControlMixin):
            ret.update(dataProps)

        # Do we want to show postions?
        ret.update(posProps)

        # All controls should have the various Border* properties
        ret.update(borderProps)

        # Add all of the class-specific properties
        if isinstance(self, dBitmap):
            pass
        elif isinstance(self, dBitmapButton):
            ret.update(captionProps)
            ret.update(pictureProps)
            ret.update(colorProps)
        elif isinstance(self, dButton):
            ret.update(colorProps)
            ret.update(captionProps)
            ret.update(fontProps)
        elif isinstance(self, dCheckBox):
            ret.update(colorProps)
            ret.update(captionProps)
            ret.update(fontProps)
        elif isinstance(self, dColumn):
            # This class is very different than the rest.
            ret = columnProps
            ret.update(captionProps)
            ret.update(fontProps)
            ret["Precision"] = {"type": int, "readonly": False}
            ret["Visible"] = {"type": bool, "readonly": False}
        elif isinstance(self, dComboBox):
            ret.update(colorProps)
            ret.update(comboProps)
            ret.update(fontProps)
            ret.update(choiceProps)
        elif isinstance(self, dDropdownList):
            ret.update(colorProps)
            ret.update(fontProps)
            ret.update(choiceProps)
        elif isinstance(self, dEditor):
            ret.update(fontProps)
            ret.update(editorProps)
        elif isinstance(self, dGauge):
            pass
        elif isinstance(self, dGrid):
            ret.update(fontProps)
            ret.update(gridProps)
        elif isinstance(self, dColumn):
            pass
        elif isinstance(self, dImage):
            ret.update(pictureProps)
            ret.update(imageProps)
        elif isinstance(self, dLabel):
            ret.update(labelProps)
            ret.update(colorProps)
            ret.update(captionProps)
            ret.update(fontProps)
            ret.update(borderProps)
        elif isinstance(self, dLine):
            pass
        elif isinstance(self, dListBox):
            ret.update(colorProps)
            ret.update(fontProps)
            ret.update(choiceProps)
            ret.update(multiSelectProps)
        elif isinstance(self, dCheckList):
            ret.update(colorProps)
            ret.update(fontProps)
            ret.update(choiceProps)
        elif isinstance(self, dListControl):
            ret.update(listControlProps)
            ret.update(colorProps)
            ret.update(fontProps)
            ret.update(multiSelectProps)
        elif isinstance(self, dMenuBar):
            pass
        elif isinstance(self, dMenu):
            pass
        elif isinstance(self, dMenuItem):
            ret.update(captionProps)
        elif isinstance(self, dTreeView.getBaseNodeClass()):
            ret = nodeProps
            ret.update(captionProps)
            ret.update(fontProps)
            ret.update(colorProps)
        elif isinstance(self, dRadioList):
            ret.update(radioProps)
            ret.update(colorProps)
            ret.update(captionProps)
            ret.update(fontProps)
            ret.update(choiceProps)
        elif isinstance(self, dPageList):
            ret.update(colorProps)
            ret.update(fontProps)
            ret.update(pageFrameProps)
            ret.update(pageListProps)
        elif isinstance(self, (dPageFrame, dPageList, dPageSelect, dPageStyled, dPageFrameNoTabs)):
            ret.update(colorProps)
            ret.update(fontProps)
            ret.update(pageFrameProps)
            if isinstance(self, dPageFrameNoTabs):
                del ret["TabPosition"]
            if isinstance(self, (dPageSelect, dPageStyled)):
                ret.update(pageStyleProps)
        elif isinstance(self, dPage):
            ret.update(captionProps)
            ret.update(colorProps)
            ret.update(panelProps)
            del ret["Width"]
            del ret["Height"]
            del ret["Buffered"]
            del ret["Visible"]
        elif isinstance(self, dialogs.WizardPage):
            ret.update(captionProps)
            ret.update(panelProps)
            ret.update(colorProps)
            ret.update(pictureProps)
            ret.update(wizardPageProps)
        elif isinstance(self, dLed):
            ret.update(ledProps)
        elif isinstance(self, dScrollPanel):
            ret.update(panelProps)
            ret.update(scrollProps)
            ret.update(colorProps)
        elif isinstance(self, dShell):
            ret.update(
                {
                    "FontFace": {
                        "type": list,
                        "readonly": False,
                        "values": ui.getAvailableFonts(),
                    },
                    "FontSize": {"type": int, "readonly": False},
                }
            )
        elif isinstance(self, dPanel):
            ret.update(panelProps)
            ret.update(colorProps)
        elif isinstance(self, dSlidePanelControl):
            ret.update(slidePanelControlProps)
        elif isinstance(self, dSlidePanel):
            ret.update(slidePanelProps)
            ret.update(captionProps)
        elif isinstance(self, dSlider):
            ret.update(sliderProps)
            ret.update(colorProps)
            ret.update(fontProps)
        elif isinstance(self, dSpinner):
            ret.update(spinnerProps)
            ret.update(colorProps)
            ret.update(fontProps)
        elif isinstance(self, dSplitter):
            ret.update(splitterProps)
        elif isinstance(self, dStatusBar):
            ret.update(fontProps)
        elif "dMediaControl" in dir(ui) and isinstance(self, dMediaControl):
            ret.update(mediaControlProps)
        elif isinstance(self, (dEditBox, dTextBox, dMaskedTextBox)):
            ret.update(colorProps)
            ret.update(fontProps)
            ret.update(textProps)
            if isinstance(self, dTextBox):
                ret.update(
                    {
                        "PasswordEntry": {"type": bool, "readonly": False},
                        "TextLength": {"type": int, "readonly": False},
                    }
                )
            elif isinstance(self, dMaskedTextBox):
                ret.update(maskedTextBoxProps)
                del ret["ForceCase"]
            elif isinstance(self, dEditBox):
                ret["WordWrap"] = {"type": bool, "readonly": False}
        elif isinstance(self, dHtmlBox):
            ret.update(htmlTextProps)
            ret.update(scrollProps)
        elif isinstance(self, dTimer):
            pass
        elif isinstance(self, dToggleButton):
            ret.update(captionProps)
            ret.update(colorProps)
            ret.update(fontProps)
        elif isinstance(self, dTreeView):
            ret.update(treeProps)
            ret.update(colorProps)
            ret.update(fontProps)
            ret.update(multiSelectProps)

        # Now see if there are any custom properties defined for this class
        custProps = self.Controller.getPropDictForObject(self)
        if custProps:
            for prop, dct in list(custProps.items()):
                val = dct.get("defaultValue", None)
                if val is None:
                    typ = "varies"
                else:
                    typ = type(val)
                ret[prop] = {"type": typ, "readonly": False}

        return ret

    def _getHiliteBorderColor(self):
        return self._hiliteBorderColor

    def _setHiliteBorderColor(self, val):
        if self._constructed():
            if isinstance(val, str):
                try:
                    val = dColors.colorTupleFromName(val)
                except:
                    pass
            self._hiliteBorderColor = val
            if self._hiliteBorder:
                self._hiliteBorder.PenColor = val
            self._needRedraw = True
        else:
            self._properties["HiliteBorderColor"] = val

    def _getHiliteBorderLineStyle(self):
        return self._hiliteBorderLineStyle

    def _setHiliteBorderLineStyle(self, val):
        if self._constructed():
            val = self._expandPropStringValue(
                val, ("Solid", "Dash", "Dashed", "Dot", "Dotted", "DotDash", "DashDot")
            )
            self._hiliteBorderLineStyle = val
            if self._hiliteBorder:
                self._hiliteBorder.LineStyle = val
            self._needRedraw = True
        else:
            self._properties["HiliteBorderLineStyle"] = val

    def _getHiliteBorderWidth(self):
        return self._hiliteBorderWidth

    def _setHiliteBorderWidth(self, val):
        if self._constructed():
            self._hiliteBorderWidth = val
            if self._hiliteBorder and (self._hiliteBorder in self._drawnObjects):
                if val == 0:
                    self._drawnObjects.remove(self._hiliteBorder)
                else:
                    self._hiliteBorder.PenWidth = val
            else:
                if val > 0:
                    if hasattr(self, "drawRectangle"):
                        self._hiliteBorder = self.drawRectangle(
                            0,
                            0,
                            self.Width,
                            self.Height,
                            penColor=self.HiliteBorderColor,
                            penWidth=val,
                        )
            if self._hiliteBorder:
                # Tie it to resizing
                self.bindEvent(events.Resize, self._onResizeHiliteBorder)
            else:
                self.unbindEvent(events.Resize, self._onResizeHiliteBorder)
        else:
            self._properties["HiliteBorderWidth"] = val

    def _getIsMain(self):
        return self._isMain

    def _setIsMain(self, val):
        self._isMain = val

    def _getContainerState(self):
        return isinstance(self, (dPanel, dScrollPanel, dPage, dForm, dFormMain, dDialog))

    def _getRegID(self):
        ret = self._tmpRegID
        if ret is None:
            # Nothing local has been set; use the native value
            ret = self._registryID
        return ret

    def _setRegID(self, val):
        if self._registryID:
            self._tmpRegID = val
        else:
            self._registryID = val

    def _getSelected(self):
        return self._selected

    def _setSelected(self, val):
        if val == self._selected:
            return
        oldval = self._selected
        self._selected = val
        if self.UsingSizers:
            self.HiliteBorderWidth = (0, 2)[val]
        else:
            self.HiliteBorderWidth = (0, 2)[self is self.Form.ActiveContainer]
        if not val:
            self.Form.hideHandles(self)
        else:
            if isinstance(self, dPage):
                self.Parent.SelectedPage = self
        if hasattr(self, "_redraw"):
            autoclear = self.autoClearDrawings
            needRefresh = False
            if not val and oldval:
                self.autoClearDrawings = True
                needRefresh = True
            self._redraw()
            self.autoClearDrawings = autoclear
            if needRefresh:
                self.refresh()

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

    def _getSzInfo(self):
        sz = self.ControllingSizer
        szit = self.ControllingSizerItem
        props = (
            ("X", "Expand"),
            ("Prop", "Proportion"),
            ("Hor", "Halign"),
            ("Vert", "Valign"),
        )
        ret = ""
        # Expand
        if sz.getItemProp(szit, "Expand"):
            ret = "Expand (weight=%s), Align=" % sz.getItemProp(szit, "Proportion")
        else:
            ret = "Fixed, Align="
        hor = sz.getItemProp(szit, "Halign")
        ver = sz.getItemProp(szit, "Valign")
        ret += "%s, %s" % (ver, hor)
        return ret

    def _getTreeDisp(self):
        if isinstance(self, dColumn):
            prfx = "Column"
            if not self.Visible:
                prfx = "Hidden Column"
            if self.DataField:
                ret = (prfx, self.DataField)
            else:
                ret = (prfx, self.Parent.Columns.index(self))
        elif isinstance(self, dLabel):
            ret = ('"%s"' % self.Caption, self._baseClass)
        elif isinstance(self, dTreeView.getBaseNodeClass()):
            ret = ('"%s"' % self.Caption, self._baseClass)
        elif isinstance(self, dialogs.WizardPage):
            ret = "WizardPage", self.Caption
        else:
            ret = (ustr(self.Name), self._baseClass)
        return ret

    def _getUsingSizers(self):
        if self._usingSizers is None:
            try:
                self._usingSizers = self.Form.UseSizers
            except AttributeError:
                return True
        return self._usingSizers

    Children = property(
        _getChildren,
        None,
        None,
        _("Returns a list of the designer-relevant child controls (read-only) (list)"),
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
            """Returns a dict of editable properties for the control, with the
            prop names as the keys, and the value for each another dict,
            containing the following keys: 'type', which controls how to display
            and edit the property, and 'readonly', which will prevent editing
            when True. (dict)"""
        ),
    )

    HiliteBorderColor = property(
        _getHiliteBorderColor,
        _setHiliteBorderColor,
        None,
        _("Color of the border when the control is selected  (str or color tuple"),
    )

    HiliteBorderLineStyle = property(
        _getHiliteBorderLineStyle,
        _setHiliteBorderLineStyle,
        None,
        _("Line style of the displayed border when the control is selected  (str"),
    )

    HiliteBorderWidth = property(
        _getHiliteBorderWidth,
        _setHiliteBorderWidth,
        None,
        _("Width of the border around the control when selected  (int"),
    )

    IsContainer = property(
        _getContainerState,
        None,
        None,
        _("Can we add controls to this control?  (bool)"),
    )

    IsMainControl = property(
        _getIsMain,
        _setIsMain,
        None,
        _(
            """Is this the main control of the designer, or contained within the
            main control?  (bool)"""
        ),
    )

    # Placeholder for the actual RegID property
    RegID = property(
        _getRegID,
        _setRegID,
        None,
        _("A unique identifier used for referencing by other objects. (str)"),
    )

    Selected = property(
        _getSelected,
        _setSelected,
        None,
        _("Is this control selected for editing?  (bool)"),
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

    TreeDisplayCaption = property(
        _getTreeDisp, None, None, _("Displayed text in the Designer Tree.  (tuple)")
    )

    UsingSizers = property(
        _getUsingSizers,
        None,
        None,
        _("Convenience property. Reflects the form's UseSizers value  (bool)"),
    )


if __name__ == "__main__":
    pass
