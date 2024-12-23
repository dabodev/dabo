# -*- coding: utf-8 -*-
import wx
import wx.lib.agw.aui as aui

PaneInfo = aui.AuiPaneInfo

from .. import events, settings, ui
from ..localization import _
from . import dButton, dCheckBox, dForm, dPanel, dShellForm, dSizer, dStatusBar, makeDynamicProperty

dabo_module = settings.get_dabo_package()

flag_allow_float = aui.AUI_MGR_ALLOW_FLOATING
flag_show_active = aui.AUI_MGR_ALLOW_ACTIVE_PANE
flag_transparent_drag = aui.AUI_MGR_TRANSPARENT_DRAG
flag_rectangle_hint = aui.AUI_MGR_RECTANGLE_HINT
flag_transparent_hint = aui.AUI_MGR_TRANSPARENT_HINT
flag_venetian_blinds_hint = aui.AUI_MGR_VENETIAN_BLINDS_HINT
flag_no_venetian_blinds_fade = aui.AUI_MGR_NO_VENETIAN_BLINDS_FADE
flag_hint_fade = aui.AUI_MGR_HINT_FADE


class _dDockManager(aui.AuiManager):
    def __init__(self, win):
        self._managedWindow = win
        flags = (
            flag_allow_float | flag_transparent_drag | flag_rectangle_hint | flag_transparent_hint
        )
        try:
            super().__init__(win, flags=flags)
        except TypeError:
            # Later AGW version
            super().__init__(win, agwFlags=flags)
        self.Bind(aui.EVT_AUI_RENDER, self.aui_render)

    def aui_render(self, evt):
        evt.Skip()
        ui.callAfterInterval(100, self._managedWindow.update)

    def addPane(self, win, name=None, typ=None, caption=None, toolbar=None):
        pi = PaneInfo()
        if toolbar:
            pi.ToolbarPane()
        if name is not None:
            pi = pi.Name(name)
        if caption is not None:
            pi = pi.Caption(caption)
        if typ:
            lt = typ[0].lower()
            if lt == "c":
                # Center
                pi = pi.CenterPane()
            elif lt == "t":
                # Toolbar
                pi = pi.ToolbarPane()
        self.AddPane(win, pi)
        ret = self.GetAllPanes()[-1]
        ui.callAfterInterval(100, self.Update)
        return ret

    def runUpdate(self):
        win = self.GetManagedWindow()
        if not win or win._finito:
            return
        self.Update()


class dDockPanel(dPanel):
    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        nmU = self._extractKey((properties, kwargs), "Name", "")
        nb = self._extractKey((properties, kwargs), "NameBase", "")
        nmL = self._extractKey((properties, kwargs), "name", "")
        kwargs["NameBase"] = [txt for txt in (nmU, nb, nmL, "dDockPanel") if txt][0]
        pcapUp = self._extractKey(kwargs, "Caption", "")
        pcap = self._extractKey(kwargs, "caption", "")
        ptype = self._extractKey(kwargs, "typ", "")
        if pcapUp:
            kwargs["Caption"] = pcapUp
        else:
            kwargs["Caption"] = pcap
        self._paramType = ptype
        self._toolbar = self._extractKey(kwargs, "Toolbar", False)

        # Initialize attributes that underly properties
        self._bottomDockable = True
        self._leftDockable = True
        self._rightDockable = True
        self._topDockable = True
        self._floatable = True
        self._floatingPosition = (0, 0)
        self._floatingSize = (100, 100)
        self._gripperPosition = "Left"
        self._destroyOnClose = False
        self._movable = True
        self._resizable = True
        self._showBorder = True
        self._showCaption = True
        self._showCloseButton = True
        self._showGripper = False
        self._showMaximizeButton = False
        self._showMinimizeButton = False
        self._showPinButton = True
        super().__init__(
            parent, properties=properties, attProperties=attProperties, *args, **kwargs
        )
        if self.Floating:
            self._floatingPosition = self.GetParent().GetPosition().Get()
            self._floatingSize = self.GetParent().GetSize().Get()

    def _uniqueNameForParent(self, name, parent=None):
        """
        We need to check the AUI manager's PaneInfo name value, too, as that has to be unique
        there as well as the form.
        """
        changed = True
        try:
            mgr = parent._mgr
        except AttributeError:
            mgr = self._Manager
        while changed:
            i = 0
            auiOK = False
            while not auiOK:
                auiOK = True
                candidate = name
                if i:
                    candidate = "%s%s" % (name, i)
                mtch = [pi.name for pi in mgr.GetAllPanes() if pi.name == candidate]
                if mtch:
                    auiOK = False
                    i += 1
            changed = changed and (candidate != name)
            name = candidate

            candidate = super()._uniqueNameForParent(name, parent)
            changed = changed and (candidate != name)
            name = candidate
        return name

    def float(self):
        """Float the panel if it isn't already floating."""
        if self.Floating or not self.Floatable:
            return
        self._PaneInfo.Float()
        self._updateAUI()

    def dock(self, side=None):
        """
        Dock the panel. If side is specified, it is docked on that side of the
        form. If no side is specified, it is docked in its default location.
        """
        if self.Docked or not self.Dockable:
            return
        inf = self._PaneInfo
        if side is not None:
            s = side[0].lower()
            func = {"l": inf.Left, "r": inf.Right, "t": inf.Top, "b": inf.Bottom}.get(s, None)
            if func:
                func()
            else:
                dabo_module.error(_("Invalid dock position: '%s'.") % side)
        inf.Dock()
        self._updateAUI()

    def _beforeSetProperties(self, props):
        """
        Some properties of Floating panels cannot be set at the usual
        point in the process, since the panel will still be docked, and you
        can't change dimensions/location of a docked panel. So extract
        them now, and then set them afterwards.
        """
        self._propDelayDict = {}
        props2Delay = (
            "Bottom",
            "BottomDockable",
            "Caption",
            "DestroyOnClose",
            "Dockable",
            "Docked",
            "DockSide",
            "Floatable",
            "Floating",
            "FloatingBottom",
            "FloatingHeight",
            "FloatingLeft",
            "FloatingPosition",
            "FloatingRight",
            "FloatingSize",
            "FloatingTop",
            "FloatingWidth",
            "GripperPosition",
            "Height",
            "Left",
            "LeftDockable",
            "Movable",
            "Resizable",
            "Right",
            "RightDockable",
            "ShowBorder",
            "ShowCaption",
            "ShowCloseButton",
            "ShowGripper",
            "ShowMaximizeButton",
            "ShowMinimizeButton",
            "ShowPinButton",
            "Top",
            "TopDockable",
            "Visible",
            "Width",
        )
        for delayed in props2Delay:
            val = self._extractKey(props, delayed, None)
            if val is not None:
                self._propDelayDict[delayed] = val
        return super()._beforeSetProperties(props)

    def _afterSetProperties(self):
        nm = self.Name
        frm = self.Form
        self._Manager.addPane(
            self,
            name=nm,
            typ=self._paramType,
            caption=self._propDelayDict.get("Caption", "dDockPanel"),
        )
        del self._paramType
        self._PaneInfo.MinSize((50, 50))
        if self._propDelayDict:
            self.setProperties(self._propDelayDict)
        del self._propDelayDict

    def getState(self):
        """
        Returns the local name and a string that can be used to restore the state of this pane.
        """
        inf = self._Manager.SavePaneInfo(self._PaneInfo)
        try:
            infPairs = (qq.split("=") for qq in inf.split(";"))
            nm = dict(infPairs)["name"]
        except KeyError:
            # For some reason a name was not returned
            return ""
        return (nm, inf.replace("name=%s;" % nm, ""))

    def _updateAUI(self):
        frm = self.Form
        if frm is not None:
            frm._refreshState()
        else:
            try:
                self._Manager.runUpdate()
            except AttributeError:
                pass

    def __getPosition(self):
        if self.Floating:
            obj = self.GetParent()
        else:
            obj = self
        return obj.GetPosition().Get()

    def __getSize(self):
        if self.Floating:
            obj = self.GetParent()
        else:
            obj = self
        return obj.GetSize().Get()

    # Property definitions
    @property
    def Bottom(self):
        """
        Position in pixels of the bottom side of the panel. Read-only when docked; read-write when
        floating  (int)
        """
        return self.__getPosition()[1] + self.__getSize()[1]

    @Bottom.setter
    def Bottom(self, val):
        if self._constructed():
            if self.Floating:
                self.FloatingBottom = val
            else:
                dabo_module.error(_("Cannot set the position of a docked panel"))
        else:
            self._properties["Bottom"] = val

    @property
    def BottomDockable(self):
        """Can the panel be docked to the bottom edge of the form? Default=True  (bool)"""
        return self._bottomDockable

    @BottomDockable.setter
    def BottomDockable(self, val):
        if self._constructed():
            self._PaneInfo.BottomDockable(val)
            self._updateAUI()
        else:
            self._properties["BottomDockable"] = val

    @property
    def Caption(self):
        """Text that appears in the title bar  (str)"""
        try:
            return self._caption
        except AttributeError:
            self._caption = ""
            return self._caption

    @Caption.setter
    def Caption(self, val):
        if self._constructed():
            self._caption = val
            self._PaneInfo.Caption(val)
            self._updateAUI()
        else:
            self._properties["Caption"] = val

    @property
    def DestroyOnClose(self):
        """
        When the panel's Close button is clicked, does the panel get destroyed (True) or just hidden
        (False, default)  (bool)
        """
        return self._destroyOnClose

    @DestroyOnClose.setter
    def DestroyOnClose(self, val):
        if self._constructed():
            self._destroyOnClose = val
            self._PaneInfo.DestroyOnClose(val)
            self._updateAUI()
        else:
            self._properties["DestroyOnClose"] = val

    @property
    def Dockable(self):
        """Can the panel be docked to the form? Default=True  (bool)"""
        return (
            self._bottomDockable or self._leftDockable or self._rightDockable or self._topDockable
        )

    @Dockable.setter
    def Dockable(self, val):
        if self._constructed():
            self._dockable = self._bottomDockable = self._leftDockable = self._rightDockable = (
                self._topDockable
            ) = val
            self._PaneInfo.Dockable(val)
            if self.Docked:
                self.Docked = val
            self._updateAUI()
        else:
            self._properties["Dockable"] = val

    @property
    def Docked(self):
        """Determines whether the pane is floating (False) or docked (True)  (bool)"""
        return self._PaneInfo.IsDocked()

    @Docked.setter
    def Docked(self, val):
        if self._constructed():
            curr = self._PaneInfo.IsDocked()
            chg = False
            if val and not curr:
                self._PaneInfo.Dock()
                chg = True
            elif not val and curr:
                self._PaneInfo.Float()
                chg = True
            if chg:
                self._updateAUI()
        else:
            self._properties["Docked"] = val

    @property
    def DockSide(self):
        """
        Side of the form that the panel is either currently docked to, or would be if dock() were to
        be called. Possible values are 'Left', 'Right', 'Top' and 'Bottom'.  (str)
        """
        return {1: "Top", 2: "Right", 3: "Bottom", 4: "Left"}[self._PaneInfo.dock_direction]

    @DockSide.setter
    def DockSide(self, val):
        if self._constructed():
            vUp = val[0].upper()
            self._PaneInfo.dock_direction = {"T": 1, "R": 2, "B": 3, "L": 4}[vUp]
            self._updateAUI()
        else:
            self._properties["DockSide"] = val

    @property
    def Floatable(self):
        """Can the panel be undocked from the form and float independently? Default=True  (bool)"""
        return self._floatable

    @Floatable.setter
    def Floatable(self, val):
        if self._constructed():
            self._floatable = val
            self._PaneInfo.Floatable(val)
            self._updateAUI()
        else:
            self._properties["Floatable"] = val

    @property
    def Floating(self):
        """Determines whether the pane is floating (True) or docked (False)  (bool)"""
        return self._PaneInfo.IsFloating()

    @Floating.setter
    def Floating(self, val):
        if self._constructed():
            curr = self._PaneInfo.IsFloating()
            chg = False
            if val and not curr:
                self._PaneInfo.Float()
                chg = True
            elif not val and curr:
                self._PaneInfo.Dock()
                chg = True
            if chg:
                self._updateAUI()
        else:
            self._properties["Floating"] = val

    @property
    def FloatingBottom(self):
        """Bottom coordinate of the panel when floating  (int)"""
        return self.FloatingPosition[1] + self.FloatingSize[1]

    @FloatingBottom.setter
    def FloatingBottom(self, val):
        if self._constructed():
            ht = self.FloatingSize[1]
            self._floatingPosition = (self.FloatingPosition[0], val - ht)
            self._PaneInfo.FloatingPosition(self._floatingPosition)
            self.Form._refreshState(0)
        else:
            self._properties["FloatingBottom"] = val

    @property
    def FloatingHeight(self):
        """Height of the panel when floating  (int)"""
        return self.FloatingSize[1]

    @FloatingHeight.setter
    def FloatingHeight(self, val):
        if self._constructed():
            self._floatingSize = (self.FloatingSize[0], val)
            if self._PaneInfo.IsFloating():
                self.GetParent().SetSize(self._floatingSize)
            else:
                self._PaneInfo.FloatingSize(self._floatingSize)
            self.Form._refreshState(0)
        else:
            self._properties["FloatingHeight"] = val

    @property
    def FloatingLeft(self):
        """Left coordinate of the panel when floating  (int)"""
        return self.FloatingPosition[0]

    @FloatingLeft.setter
    def FloatingLeft(self, val):
        if self._constructed():
            self._floatingPosition = (val, self.FloatingPosition[1])
            self._PaneInfo.FloatingPosition(self._floatingPosition)
            self.Form._refreshState(0)
        else:
            self._properties["FloatingLeft"] = val

    @property
    def FloatingPosition(self):
        """Position of the panel when floating  (2-tuple of ints)"""
        return self._PaneInfo.floating_pos.Get()

    @FloatingPosition.setter
    def FloatingPosition(self, val):
        if self._constructed():
            self._PaneInfo.FloatingPosition(val)
            self.Form._refreshState(0)
        else:
            self._properties["FloatingPosition"] = val

    @property
    def FloatingRight(self):
        """Right coordinate of the panel when floating  (int)"""
        return self.FloatingPosition[0] + self.FloatingSize[0]

    @FloatingRight.setter
    def FloatingRight(self, val):
        if self._constructed():
            wd = self.FloatingSize[0]
            self._floatingPosition = (val - wd, self.FloatingPosition[1])
            self._PaneInfo.FloatingPosition(self._floatingPosition)
            self.Form._refreshState(0)
        else:
            self._properties["FloatingRight"] = val

    @property
    def FloatingSize(self):
        """Size of the panel when floating  (2-tuple of ints)"""
        return self._PaneInfo.floating_size.Get()

    @FloatingSize.setter
    def FloatingSize(self, val):
        if self._constructed():
            self._PaneInfo.FloatingSize(val)
            self.Form._refreshState(0)
        else:
            self._properties["FloatingSize"] = val

    @property
    def FloatingTop(self):
        """Top coordinate of the panel when floating  (int)"""
        return self.FloatingPosition[1]

    @FloatingTop.setter
    def FloatingTop(self, val):
        if self._constructed():
            self._floatingPosition = (self.FloatingPosition[0], val)
            self._PaneInfo.FloatingPosition(self._floatingPosition)
            self.Form._refreshState(0)
        else:
            self._properties["FloatingTop"] = val

    @property
    def FloatingWidth(self):
        """Width of the panel when floating  (int)"""
        return self.FloatingSize[0]

    @FloatingWidth.setter
    def FloatingWidth(self, val):
        if self._constructed():
            self._floatingSize = (val, self.FloatingSize[1])
            if self._PaneInfo.IsFloating():
                self.GetParent().SetSize(self._floatingSize)
            else:
                self._PaneInfo.FloatingSize(self._floatingSize)
            self.Form._refreshState(0)
        else:
            self._properties["FloatingWidth"] = val

    @property
    def GripperPosition(self):
        """
        If a gripper is shown, is it on the Top or Left side? Default = 'Left' ('Top' or 'Left')
        """
        return self._gripperPosition

    @GripperPosition.setter
    def GripperPosition(self, val):
        if self._constructed():
            val = val[0].lower()
            if not val in ("l", "t"):
                raise ValueError(_("Only valid GripperPosition values are 'Top' or 'Left'."))
            self._gripperPosition = {"l": "Left", "t": "Top"}[val]
            self._PaneInfo.GripperTop(val == "t")
            self._updateAUI()
        else:
            self._properties["GripperPosition"] = val

    @property
    def Height(self):
        """
        Position in pixels of the height of the panel. Read-only when docked; read-write when
        floating  (int)
        """
        return self.__getSize()[1]

    @Height.setter
    def Height(self, val):
        if self._constructed():
            if self.Floating:
                self.FloatingHeight = val
            else:
                dabo_module.error(_("Cannot set the Size of a docked panel"))
        else:
            self._properties["Height"] = val

    @property
    def Left(self):
        """
        Position in pixels of the left side of the panel. Read-only when docked; read-write when
        floating  (int)
        """
        return self.__getPosition()[0]

    @Left.setter
    def Left(self, val):
        if self._constructed():
            if self.Floating:
                self.FloatingLeft = val
            else:
                dabo_module.error(_("Cannot set the position of a docked panel"))
        else:
            self._properties["Left"] = val

    @property
    def LeftDockable(self):
        """Can the panel be docked to the left edge of the form? Default=True  (bool)"""
        return self._leftDockable

    @LeftDockable.setter
    def LeftDockable(self, val):
        if self._constructed():
            self._PaneInfo.LeftDockable(val)
            self._updateAUI()
        else:
            self._properties["LeftDockable"] = val

    @property
    def Manager(self):
        """Reference to the AUI manager (for internal use only).  (_dDockManager)"""
        try:
            mgr = self._mgr
        except AttributeError:
            mgr = self._mgr = self.Form._mgr
        return mgr

    @property
    def Movable(self):
        """Can the panel be moved (True, default), or is it in a fixed position (False).  (bool)"""
        return self._movable

    @Movable.setter
    def Movable(self, val):
        if self._constructed():
            self._movable = val
            self._PaneInfo.Movable(val)
            self._updateAUI()
        else:
            self._properties["Movable"] = val

    @property
    def PaneInfo(self):
        """Reference to the AUI PaneInfo object (for internal use only).  (wx.aui.PaneInfo)"""
        try:
            mgr = self._mgr
        except AttributeError:
            mgr = self._mgr = self.Form._mgr
        return mgr.GetPane(self)

    @property
    def Resizable(self):
        """Can the panel be resized? Default=True  (bool)"""
        return self._resizable

    @Resizable.setter
    def Resizable(self, val):
        if self._constructed():
            self._resizable = val
            self._PaneInfo.Resizable(val)
            self._updateAUI()
        else:
            self._properties["Resizable"] = val

    @property
    def Right(self):
        """
        Position in pixels of the right side of the panel. Read-only when docked; read-write when
        floating  (int)
        """
        return self.__getPosition()[0] + self.__getSize()[0]

    @Right.setter
    def Right(self, val):
        if self._constructed():
            if self.Floating:
                self.FloatingRight = val
            else:
                dabo_module.error(_("Cannot set the position of a docked panel"))
        else:
            self._properties["Right"] = val

    @property
    def RightDockable(self):
        """Can the panel be docked to the right edge of the form? Default=True  (bool)"""
        return self._rightDockable

    @RightDockable.setter
    def RightDockable(self, val):
        if self._constructed():
            self._PaneInfo.RightDockable(val)
            self._updateAUI()
        else:
            self._properties["RightDockable"] = val

    @property
    def ShowBorder(self):
        """Should the panel's border be shown when floating?  (bool)"""
        return self._showBorder

    @ShowBorder.setter
    def ShowBorder(self, val):
        if self._constructed():
            self._showBorder = val
            self._PaneInfo.PaneBorder(val)
            self._updateAUI()
        else:
            self._properties["ShowBorder"] = val

    @property
    def ShowCaption(self):
        """Should the panel's Caption be shown when it is docked? Default=True  (bool)"""
        return self._showCaption

    @ShowCaption.setter
    def ShowCaption(self, val):
        if self._constructed():
            self._showCaption = val
            self._PaneInfo.CaptionVisible(val)
            self._updateAUI()
        else:
            self._properties["ShowCaption"] = val

    @property
    def ShowCloseButton(self):
        """Does the panel display a close button when floating? Default=True  (bool)"""
        return self._showCloseButton

    @ShowCloseButton.setter
    def ShowCloseButton(self, val):
        if self._constructed():
            self._showCloseButton = val
            self._PaneInfo.CloseButton(val)
            self.Form._refreshState(0)
            self.Form.lockDisplay()
            self.Docked = not self.Docked
            ui.setAfterInterval(100, self, "Docked", not self.Docked)
            ui.callAfterInterval(150, self.Form.unlockDisplay)
        else:
            self._properties["ShowCloseButton"] = val

    @property
    def ShowGripper(self):
        """Does the panel display a draggable gripper? Default=False  (bool)"""
        return self._showGripper

    @ShowGripper.setter
    def ShowGripper(self, val):
        if self._constructed():
            if val == self._showGripper:
                return
            self._showGripper = val
            self._PaneInfo.Gripper(val)
            self._updateAUI()
        else:
            self._properties["ShowGripper"] = val

    @property
    def ShowMaximizeButton(self):
        """Does the panel display a maximize button when floating? Default=False  (bool)"""
        return self._showMaximizeButton

    @ShowMaximizeButton.setter
    def ShowMaximizeButton(self, val):
        if self._constructed():
            self._showMaximizeButton = val
            self._PaneInfo.MaximizeButton(val)
            self._updateAUI()
        else:
            self._properties["ShowMaximizeButton"] = val

    @property
    def ShowMinimizeButton(self):
        """Does the panel display a minimize button when floating? Default=False  (bool)"""
        return self._showMinimizeButton

    @ShowMinimizeButton.setter
    def ShowMinimizeButton(self, val):
        if self._constructed():
            self._showMinimizeButton = val
            self._PaneInfo.MinimizeButton(val)
            self._updateAUI()
        else:
            self._properties["ShowMinimizeButton"] = val

    @property
    def ShowPinButton(self):
        """Does the panel display a pin button when floating? Default=False  (bool)"""
        return self._showPinButton

    @ShowPinButton.setter
    def ShowPinButton(self, val):
        if self._constructed():
            self._showPinButton = val
            self._PaneInfo.PinButton(val)
            self._updateAUI()
        else:
            self._properties["ShowPinButton"] = val

    @property
    def Toolbar(self):
        """Returns True if this is a Toolbar pane. Default=False  (bool)"""
        return self._toolbar

    @property
    def Top(self):
        """
        Position in pixels of the top side of the panel. Read-only when docked; read-write when
        floating  (int)
        """
        return self.__getPosition()[1]

    @Top.setter
    def Top(self, val):
        if self._constructed():
            if self.Floating:
                self.FloatingTop = val
            else:
                dabo_module.error(_("Cannot set the position of a docked panel"))
        else:
            self._properties["Top"] = val

    @property
    def TopDockable(self):
        """Can the panel be docked to the top edge of the form? Default=True  (bool)"""
        return self._topDockable

    @TopDockable.setter
    def TopDockable(self, val):
        if self._constructed():
            self._PaneInfo.TopDockable(val)
            self._updateAUI()
        else:
            self._properties["TopDockable"] = val

    @property
    def Visible(self):
        """Is the panel shown?  (bool)"""
        return self._PaneInfo.IsShown()

    @Visible.setter
    def Visible(self, val):
        if self._constructed():
            self._PaneInfo.Show(val)
            self._updateAUI()
        else:
            self._properties["Visible"] = val

    @property
    def Width(self):
        """
        Position in pixels of the width of the panel. Read-only when docked; read-write when
        floating  (int)
        """
        return self.__getSize()[0]

    @Width.setter
    def Width(self, val):
        if self._constructed():
            if self.Floating:
                self.FloatingWidth = val
            else:
                dabo_module.error(_("Cannot set the Size of a docked panel"))
        else:
            self._properties["Width"] = val

    DynamicCaption = makeDynamicProperty(Caption)


class dDockForm(dForm):
    def _afterInit(self):
        self._inUpdate = False
        self._mgr = mgr = _dDockManager(self)
        pc = self.getBasePanelClass()
        self._centerPanel = pc(self, name="CenterPanel", typ="center")
        self._centerPanel.Sizer = dSizer("v")
        self._panels = {}
        super()._afterInit()
        self.bindEvent(events.Destroy, self.__onDestroy)

    def __onDestroy(self, evt):
        if self._finito:
            # Need to save this here, since we can't respond to all layout changes.
            self.saveSizeAndPosition()
            self._mgr.UnInit()

    def getBasePanelClass(cls):
        return dDockPanel

    getBasePanelClass = classmethod(getBasePanelClass)

    def onChildBorn(self, evt):
        ok = isinstance(evt.child, (dDockPanel, dStatusBar, dShellForm))
        if not ok:
            # This should never happen; if so, log the error
            dabo_module.error(_("Unmanaged object added to a Dock Form: %s") % evt.child)

    def addObject(self, classRef, Name=None, *args, **kwargs):
        """
        To support the old addObject() syntax, we need to re-direct the request
        to the center panel.
        """
        self._centerPanel.addObject(classRef, Name=Name, *args, **kwargs)

    def addPanel(self, *args, **kwargs):
        """Adds a dockable panel to the form."""
        pnl = dDockPanel(self, *args, **kwargs)
        self._refreshState()
        # Store the pane info
        nm = pnl.getState()[0]
        self._panels[pnl] = nm
        return pnl

    def _refreshState(self, interval=None):
        if self._finito:
            return
        if interval is None:
            interval = 100
        if interval == 0:
            self._mgr.Update()
        else:
            ui.callAfterInterval(interval, self._mgr.runUpdate)
        if not self._inUpdate:
            ui.callAfter(self.update)

    def update(self, interval=None):
        if not self._inUpdate:
            self._inUpdate = True
            super().update(interval=interval)
            # Update the panels
            for pnl in list(self._panels.keys()):
                pnl.update()
            ui.callAfterInterval(500, self._clearInUpdate)

    def _clearInUpdate(self):
        self._inUpdate = False

    def saveSizeAndPosition(self):
        """Save the panel layout info, then call the default behavior."""
        if self.Application:
            if self.SaveRestorePosition and not self.TempForm:
                self.Application.setUserSetting("perspective", self._mgr.SavePerspective())
                if not self._finito:
                    super().saveSizeAndPosition()

    def restoreSizeAndPosition(self):
        """Restore the panel layout, if possible, then call the default behavior."""
        if self.Application and self.SaveRestorePosition:
            super().restoreSizeAndPosition()
            ps = self.Application.getUserSetting("perspective", "")
            if ps:
                self._mgr.LoadPerspective(ps)

    # Property definitions
    @property
    def CenterPanel(self):
        """Reference to the center (i.e., non-docking) panel. (read-only) (dPanel)"""
        return self._centerPanel

    @property
    def ShowActivePanel(self):
        """When True, the title bar of the active pane is highlighted. Default=False  (bool)"""
        return bool(self._mgr.GetFlags() & flag_show_active)

    @ShowActivePanel.setter
    def ShowActivePanel(self, val):
        if self._constructed():
            self._transparentDrag = val
            flags = self._mgr.GetFlags()
            if val:
                newFlags = flags | flag_show_active
            else:
                newFlags = flags & ~flag_show_active
            self._mgr.SetFlags(newFlags)
        else:
            self._properties["ShowActivePanel"] = val

    @property
    def TransparentDrag(self):
        """When dragging panes, do they appear transparent? Default=True  (bool)"""
        return bool(self._mgr.GetFlags() & flag_transparent_drag)

    @TransparentDrag.setter
    def TransparentDrag(self, val):
        if self._constructed():
            self._transparentDrag = val
            flags = self._mgr.GetFlags()
            if val:
                newFlags = flags | flag_transparent_drag
            else:
                newFlags = flags & ~flag_transparent_drag
            self._mgr.SetFlags(newFlags)
        else:
            self._properties["TransparentDrag"] = val


class _dDockForm_test(dDockForm):
    def initProperties(self):
        self.SaveRestorePosition = False
        self.Size = (700, 500)

    def afterInit(self):
        self.fp = self.addPanel(
            Floating=True,
            BackColor="orange",
            Caption="Initially Floating",
            Top=70,
            Left=200,
            Size=(144, 100),
        )
        self.dp = self.addPanel(
            Floating=False,
            Caption="Initially Docked",
            BackColor="slateblue",
            ShowCaption=False,
            ShowPinButton=True,
            ShowCloseButton=False,
            ShowGripper=True,
            Size=(144, 100),
        )
        btn = dButton(self.CenterPanel, Caption="Test Orange", OnHit=self.onTestFP)
        self.CenterPanel.Sizer.append(btn)
        btn = dButton(self.CenterPanel, Caption="Test Blue", OnHit=self.onTestDP)
        self.CenterPanel.Sizer.append(btn)
        chk = dCheckBox(
            self.CenterPanel,
            Caption="Orange Dockable",
            DataSource=self.fp,
            DataField="Dockable",
        )
        self.CenterPanel.Sizer.append(chk)
        self.fp.DynamicCaption = self.capForOrange

    def capForOrange(self):
        print("ORNG CAP", self.fp.Docked)
        state = "Floating"
        if self.fp.Docked:
            state = "Docked"
        print("STATE", state)
        return "I'm %s!" % state

    def onTestFP(self, evt):
        self.printTest(self.fp)

    def onTestDP(self, evt):
        self.printTest(self.dp)

    def printTest(self, obj):
        nm = {self.fp: "OrangePanel", self.dp: "BluePanel"}[obj]
        print(nm + ".BottomDockable:", obj.BottomDockable)
        print(nm + ".Caption:", obj.Caption)
        print(nm + ".DestroyOnClose:", obj.DestroyOnClose)
        print(nm + ".Dockable:", obj.Dockable)
        print(nm + ".Docked:", obj.Docked)
        print(nm + ".Floatable:", obj.Floatable)
        print(nm + ".Floating:", obj.Floating)
        print(nm + ".FloatingBottom:", obj.FloatingBottom)
        print(nm + ".FloatingHeight:", obj.FloatingHeight)
        print(nm + ".FloatingLeft:", obj.FloatingLeft)
        print(nm + ".FloatingPosition:", obj.FloatingPosition)
        print(nm + ".FloatingRight:", obj.FloatingRight)
        print(nm + ".FloatingSize:", obj.FloatingSize)
        print(nm + ".FloatingTop:", obj.FloatingTop)
        print(nm + ".FloatingWidth:", obj.FloatingWidth)
        print(nm + ".GripperPosition:", obj.GripperPosition)
        print(nm + ".LeftDockable:", obj.LeftDockable)
        print(nm + ".Movable:", obj.Movable)
        print(nm + ".Resizable:", obj.Resizable)
        print(nm + ".RightDockable:", obj.RightDockable)
        print(nm + ".ShowBorder:", obj.ShowBorder)
        print(nm + ".ShowCaption:", obj.ShowCaption)
        print(nm + ".ShowCloseButton:", obj.ShowCloseButton)
        print(nm + ".ShowGripper:", obj.ShowGripper)
        print(nm + ".ShowMaximizeButton:", obj.ShowMaximizeButton)
        print(nm + ".ShowMinimizeButton:", obj.ShowMinimizeButton)
        print(nm + ".ShowPinButton:", obj.ShowPinButton)
        print(nm + ".TopDockable:", obj.TopDockable)
        print(nm + ".Visible:", obj.Visible)


ui.dDockPanel = dDockPanel
ui.dDockForm = dDockForm


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dDockForm_test)
