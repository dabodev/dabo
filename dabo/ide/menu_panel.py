#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .. import ui
from .. import events
from ..dLocalize import _
from dabo.lib.propertyHelperMixin import _DynamicList
from ..lib.utils import ustr
import dabo.lib.xmltodict as xtd
from .menu_designer_components import MenuSaverMixin

from ..ui import dLabel
from ..ui import dLine
from ..ui import dMenu
from ..ui import dPanel
from ..ui import dSizerH
from ..ui import dSizerV

FONT_SIZE_DIFF = 2
VBASE_BACKCOLOR = "#eeeeee"


class MenuItemContainer(dPanel):
    """
    This is the container used to hold menu items for a given
    menu. It can be shown/hidden as needed to reflect the user's
    current selection.
    """

    def __init__(self, *args, **kwargs):
        kwargs["AlwaysResetSizer"] = True
        super(MenuItemContainer, self).__init__(*args, **kwargs)
        self.Sizer = dSizerV(DefaultBorder=8, DefaultBorderLeft=True, DefaultBorderRight=True)


class AbstractMenuPanel(MenuSaverMixin, dPanel):
    """
    Handles all the interactions with the user as they create
    and modify menu designs.
    """

    def __init__(self, parent, *args, **kwargs):
        self._menuParent = None
        self._MRU = False
        self._selected = False
        self._isMenuItem = False
        self._isSeparator = False
        self._isMenuBarLink = False
        self._inUpdate = False
        self._helpText = ""
        # Minimum amount of space between the caption and hot key
        self._minCaptionHotKeySpacing = 5
        # The image associated with a menu item.
        self._icon = ""
        # Function to be called when a menu item is selected. This
        # is a string representation that will be eval'd at runtime
        self._action = ""
        # The optional ItemID
        self._itemID = None
        # The following underlie the HotKey property and its components
        self._hotKey = ""
        self._hotKeyAlt = False
        self._hotKeyChar = ""
        self._hotKeyControl = False
        self._hotKeyShift = False
        # Collection of contained sub-items
        self.childItems = []
        kwargs["BackColor"] = BASE_BACKCOLOR
        super(AbstractMenuPanel, self).__init__(parent, *args, **kwargs)
        self._baseClass = self.__class__
        self.Sizer = dSizerV()
        self.FontSize += FONT_SIZE_DIFF
        self._initCaptions()
        self.layout()
        self.bindEvent(events.MouseMove, self.Controller.handleMouseMove)
        self.bindEvent(events.MouseLeftUp, self.onMouseLeftUp)

    def _initCaptions(self):
        """Customize for each subclass as needed."""
        pass

    def onMouseLeftClick(self, evt):
        raise NotImplementedError

    def onMouseLeftUp(self, evt):
        self.Controller.processLeftUp(self, evt)

    def onContextMenu(self, evt):
        raise NotImplementedError

    def getDesignerDict(self):
        ret = {}
        ret["name"] = self.getClass()
        ret["attributes"] = ra = {}
        for prop in self.DesignerProps:
            if prop.startswith("HotKey") and prop != "HotKey":
                # This is one of the derivative props.
                continue
            ra[prop] = getattr(self, prop)
        ret["children"] = [kid.getDesignerDict() for kid in self.childItems]
        return ret

    def _updateHotKey(self):
        """Called when the user changes any component of the hotkey combo."""
        if not self._inUpdate:
            self._inUpdate = True
            currHK = self.HotKey
            ctlTxt = {True: "Ctrl+", False: ""}[self.HotKeyControl]
            shiftTxt = {True: "Shift+", False: ""}[self.HotKeyShift]
            altTxt = {True: "Alt+", False: ""}[self.HotKeyAlt]
            newHK = ctlTxt + altTxt + shiftTxt + self.HotKeyChar
            if newHK != currHK:
                self.HotKey = newHK
                self.refresh()
            self._inUpdate = False

    def _updateHotKeyProps(self, val=None):
        """Called when the user changes the hotkey combo to reset the components."""
        if not self._inUpdate:
            self._inUpdate = True
            if val is None:
                val = self.HotKey
            self.HotKeyControl = "Ctrl+" in val
            self.HotKeyShift = "Shift+" in val
            self.HotKeyAlt = "Alt+" in val
            self.HotKeyChar = val.split("+")[-1]
            self._inUpdate = False

    def _getAbbreviatedHotKey(self):
        ctlTxt = {True: "C", False: ""}[self.HotKeyControl]
        shiftTxt = {True: "S", False: ""}[self.HotKeyShift]
        altTxt = {True: "A", False: ""}[self.HotKeyAlt]
        prefix = ctlTxt + altTxt + shiftTxt
        if prefix:
            prefix += "+"
        return prefix + self.HotKeyChar

    def select(self):
        self.Controller.Selection = self
        # Customize behavior here
        self.afterSelect()

    def afterSelect(self):
        pass

    def getClass(self):
        """
        Return a string representing the item's class. Can
        be overridden by subclasses.
        """
        return ustr(self.BaseClass).split("'")[1].split(".")[-1]

    ## Begin property definitions ##
    def _getAction(self):
        return self._action

    def _setAction(self, val):
        if self._constructed():
            self._action = val
        else:
            self._properties["Action"] = val

    def _getCaption(self):
        return super(AbstractMenuPanel, self)._getCaption()

    def _setCaption(self, val):
        if self._constructed():
            super(AbstractMenuPanel, self)._setCaption(val)

            def _deferCaption():
                try:
                    self.lblCaption.Caption = val
                except AttributeError:
                    # Separators won't have lblCaption
                    pass
                self.Parent.layout()
                self.Parent.fitToSizer()

            dabo.ui.callAfter(_deferCaption)
        else:
            self._properties["Caption"] = val

    def _getController(self):
        try:
            return self._controller
        except AttributeError:
            self._controller = self.Form
            return self._controller

    def _setController(self, val):
        if self._constructed():
            self._controller = val
        else:
            self._properties["Controller"] = val

    def _getDesignerProps(self):
        ret = {
            "Caption": {
                "type": str,
                "readonly": (self._isSeparator or self._isMenuBarLink),
            },
            "HelpText": {"type": str, "readonly": self._isSeparator},
            "ItemID": {"type": str, "readonly": False},
            "MRU": {"type": bool, "readonly": False},
        }
        if self._isMenuItem:
            ret.update(
                {
                    "HotKey": {
                        "type": str,
                        "readonly": False,
                        "customEditor": "editHotKey",
                    },
                    "HotKeyAlt": {"type": bool, "readonly": False},
                    "HotKeyChar": {"type": str, "readonly": False},
                    "HotKeyControl": {"type": bool, "readonly": False},
                    "HotKeyShift": {"type": bool, "readonly": False},
                    "Action": {"type": str, "readonly": False},
                    "Icon": {
                        "type": str,
                        "readonly": False,
                        "customEditor": "editStdPicture",
                    },
                }
            )
            del ret["MRU"]
        return ret

    def _getHelpText(self):
        return self._helpText

    def _setHelpText(self, val):
        if self._constructed():
            self._helpText = self.ToolTipText = val
        else:
            self._properties["HelpText"] = val

    def _getHotKey(self):
        return self._hotKey

    def _setHotKey(self, val):
        if self._constructed():
            if val is None:
                val = ""
            self._hotKey = val
            self._updateHotKeyProps(val)

            def _deferHotKey():
                self.lblHotKey.Caption = val
                self.Parent.layout()
                self.Parent.fitToSizer()

            dabo.ui.callAfter(_deferHotKey)
        else:
            self._properties["HotKey"] = val

    def _getHotKeyAlt(self):
        return self._hotKeyAlt

    def _setHotKeyAlt(self, val):
        if self._constructed():
            self._hotKeyAlt = val
            self._updateHotKey()
        else:
            self._properties["HotKeyAlt"] = val

    def _getHotKeyChar(self):
        return self._hotKeyChar

    def _setHotKeyChar(self, val):
        if self._constructed():
            self._hotKeyChar = val
            self._updateHotKey()
        else:
            self._properties["HotKeyChar"] = val

    def _getHotKeyControl(self):
        return self._hotKeyControl

    def _setHotKeyControl(self, val):
        if self._constructed():
            self._hotKeyControl = val
            self._updateHotKey()
        else:
            self._properties["HotKeyControl"] = val

    def _getHotKeyShift(self):
        return self._hotKeyShift

    def _setHotKeyShift(self, val):
        if self._constructed():
            self._hotKeyShift = val
            self._updateHotKey()
        else:
            self._properties["HotKeyShift"] = val

    def _getIcon(self):
        return self._icon

    def _setIcon(self, val):
        if self._constructed():
            self._icon = val
        else:
            self._properties["Icon"] = val

    def _getItemID(self):
        return self._itemID

    def _setItemID(self, val):
        if self._constructed():
            self._itemID = val
        else:
            self._properties["ItemID"] = val

    def _getMenuParent(self):
        return self._menuParent

    def _setMenuParent(self, val):
        self._menuParent = val

    def _getMRU(self):
        return self._MRU

    def _setMRU(self, val):
        self._MRU = val

    def _getSelected(self):
        return self._selected

    def _setSelected(self, val):
        if self._constructed():
            self._selected = val
            self.BackColor = {True: "white", False: BASE_BACKCOLOR}[val]
            self.Parent.refresh()
        else:
            self._properties["Selected"] = val

    Action = property(
        _getAction,
        _setAction,
        None,
        _(
            """Action (method/handler) to be called when a menu item is
            selected. To specify a method on the associated form, use
            'form.onSomeMethod'; likewise, you can specify an application
            method using 'app.onSomeMethod'.  (str)"""
        ),
    )

    Caption = property(
        _getCaption,
        _setCaption,
        None,
        _("The caption displayed on the menu panel, minus any hot key.  (str)"),
    )

    Controller = property(
        _getController,
        _setController,
        None,
        _("Object to which this one reports events  (object (varies))"),
    )

    DesignerProps = property(
        _getDesignerProps,
        None,
        None,
        _("Properties exposed in the Menu Designer (read-only) (dict)"),
    )

    HelpText = property(
        _getHelpText,
        _setHelpText,
        None,
        _("Help string displayed when the menu item is selected.  (str)"),
    )

    HotKey = property(
        _getHotKey,
        _setHotKey,
        None,
        _("Displayed version of the hotkey combination  (str)"),
    )

    HotKeyAlt = property(
        _getHotKeyAlt,
        _setHotKeyAlt,
        None,
        _("Is the Alt key part of the hotkey combo?  (bool)"),
    )

    HotKeyChar = property(
        _getHotKeyChar,
        _setHotKeyChar,
        None,
        _("Character part of the hot key for this menu  (str)"),
    )

    HotKeyControl = property(
        _getHotKeyControl,
        _setHotKeyControl,
        None,
        _("Is the Control key part of the hotkey combo?  (bool)"),
    )

    HotKeyShift = property(
        _getHotKeyShift,
        _setHotKeyShift,
        None,
        _("Is the Shift key part of the hotkey combo?  (bool)"),
    )

    Icon = property(_getIcon, _setIcon, None, _("Specifies the icon for the menu item.  (str)"))

    ItemID = property(
        _getItemID,
        _setItemID,
        None,
        _(
            """Identifying value for this menuitem. NOTE: there is no checking for
            duplicate values; it is the responsibility to ensure that ItemID values
            are unique within a menu.  (varies)"""
        ),
    )

    MenuParent = property(
        _getMenuParent,
        _setMenuParent,
        None,
        _("The logical 'parent' for this item (not the panel container it sits in.)"),
    )

    MRU = property(_getMRU, _setMRU, None, _("Should this menu be tracked for MRU lists  (bool)"))

    Selected = property(
        _getSelected,
        _setSelected,
        None,
        _("Is this the currently selected item?  (bool)"),
    )


class MenuBarPanel(AbstractMenuPanel):
    """Used for the top-level menu bar."""

    def __init__(self, parent, *args, **kwargs):
        super(MenuBarPanel, self).__init__(parent, *args, **kwargs)
        self._isMenuBarLink = True

    def _initCaptions(self):
        self.unbindEvent(events.MouseLeftClick)
        self.unbindEvent(events.ContextMenu)
        self.lblCaption = None
        # Create the container for the menus
        mc = self.menuContainer = MenuItemContainer(self, MinSizerHeight=24)
        mc.Sizer.Orientation = "H"
        self.Sizer.appendSpacer(22)
        self.Sizer.append(mc, "x")

    def onMouseLeftClick(self, evt):
        self.select()

    def afterSelect(self):
        self.Controller.makeMenuBar()

    def onContextMenu(self, evt):
        pop = dMenu()
        pop.append(_("Create Base Menu"), OnHit=self.onCreateBaseMenu, Help="BASE")
        pop.append(_("Add Menu"), OnHit=self.onAddMenu)
        self.showContextMenu(pop)

    def showTopLevel(self):
        self.showMenu(None)

    def createMenuFromDict(self, menu_dict):
        """Create the menu objects from the supplied dict."""
        sz = self.menuContainer.Sizer
        sz.clear(destroy=True)
        self.clearMenus()
        for att, val in list(menu_dict.get("attributes", {}).items()):
            setattr(self, att, val)
        for dct in menu_dict.get("children", []):
            mn = self._createMenuFromDict(dct)
            sz.append(mn, border=6)
            self.childItems.append(mn)
        self.Parent.layout()

    #        dabo.ui.callAfter(self.sizeMenuContainer)

    def _createMenuFromDict(self, menu_dict):
        atts = menu_dict["attributes"]
        mn = MenuPanel(self.menuContainer, attProperties=atts)
        mn.MenuBar = mn.MenuParent = self
        mn.Controller = self.Controller
        mn.addItemsFromDictList(menu_dict.get("children", []))
        return mn

    def appendMenu(self, caption):
        """Add a menu at the end of the menu bar."""
        lastMenu = self.childItems[-1]
        return self.addMenu(lastMenu, "right", caption)

    def addMenu(self, menu, side, caption):
        """Add a menu to either the right or left of the specified menu."""
        mn = self._createBlankMenu(caption)
        sz = self.menuContainer.Sizer
        pos = menu.getPositionInSizer()
        if side.lower().startswith("r"):
            pos = pos + 1
        sz.insert(pos, mn, border=6)
        self.childItems.insert(pos, mn)
        self.Parent.layout()
        dabo.ui.callAfter(self.sizeMenuContainer)
        mn.select()
        return mn

    def moveMenu(self, menu, direction):
        currPos = menu.getPositionInSizer()
        newPos = currPos + direction
        menu.setPositionInSizer(newPos)

    def deleteMenu(self, menu):
        self.childItems.remove(menu)
        menu.release()
        self.Parent.layout()

    def clearMenus(self):
        for mn in self.childItems[::-1]:
            try:
                mn.release()
            except Exception:
                # Already deleted
                pass
        self.childItems = []
        self.Controller.clearMenus()

    def showMenu(self, menu):
        """Show the specified menu, hiding others."""
        for mn in self.childItems:
            isShown = mn is menu
            mn.showMenu(isShown)
        self.refresh()

    def _createBlankMenu(self, caption=None):
        if caption is None:
            caption = "BLANK"
        blank = {
            "attributes": {"Caption": caption, "HelpText": "", "MRU": False},
            "children": [],
            "name": "MenuPanel",
        }
        return self._createMenuFromDict(blank)

    def onCreateBaseMenu(self, evt):
        menuExists = bool(self.Children)
        if menuExists:
            if not dabo.ui.areYouSure(
                _("Proceeding will destroy the exising menu. " "Do you really want to do that?"),
                "Menu Exists",
                defaultNo=True,
                cancelButton=False,
            ):
                return
        self.Controller.createBaseMenu()

    def onAddMenu(self, evt):
        cap = dabo.ui.getString(_("Caption?"))
        if not cap:
            return
        mn = self._createBlankMenu(cap)
        sz = self.menuContainer.Sizer
        sz.append(mn, border=10)
        self.childItems.append(mn)
        mn.select()
        self.Parent.layout()
        dabo.ui.callAfter(self.sizeMenuContainer)

    def sizeMenuContainer(self):
        mc = self.menuContainer
        mc.layout()
        mc.fitToSizer()


class MenuPanel(AbstractMenuPanel):
    """Used for the menus in the menu bar."""

    def afterInit(self):
        super(MenuPanel, self).afterInit()
        self.itemDict = {}
        self._menuitem_container = None
        self.childItems = []

    def _initCaptions(self):
        self.lblCaption = dLabel(self, Caption=self.Caption, _EventTarget=self)
        self.lblCaption.FontSize += FONT_SIZE_DIFF
        self.Sizer.append(self.lblCaption)

    def onMouseLeftClick(self, evt):
        self.select()

    def afterSelect(self):
        self.MenuBar.showMenu(self)
        self.Parent.layout()

    def showMenu(self, val):
        mic = self.MenuItemContainer
        mic.Visible = val
        if val:
            self.Parent.InvalidateBestSize()
            self.InvalidateBestSize()
            mic.InvalidateBestSize()
            # The panel will have 2 children by default
            if self.itemDict and not self.MenuItemContainer.Children:
                # Need to create the menu items
                self.createMenuItems()
            offsetX, offsetY = self.Parent.containerCoordinates(mic.Parent)
            mic.Left = self.Left + offsetX
            mic.Top = self.Bottom + offsetY + 5
            self.Parent.layout()

    def onContextMenu(self, evt):
        pop = dMenu()
        pos = self.getPositionInSizer()
        isFirst = pos == 0
        isLast = pos == (len(self.MenuBar.childItems) - 1)
        pop.append(_("Append MenuItem"), OnHit=self.onAppendMenuItem)
        pop.append(_("Append Separator"), OnHit=self.onAppendSeparator)
        pop.appendSeparator()
        pop.append(_("Add Menu Left"), OnHit=self.onAddMenuLeft)
        pop.append(_("Add Menu Right"), OnHit=self.onAddMenuRight)
        pop.appendSeparator()
        if not isFirst:
            pop.append(_("Move Left"), OnHit=self.onMoveLeft)
        if not isLast:
            pop.append(_("Move Right"), OnHit=self.onMoveRight)
        pop.appendSeparator()
        pop.append(_("Delete"), OnHit=self.onDelete)
        self.showContextMenu(pop)

    def addItemsFromDictList(self, dctlst):
        """Create the menu item links from the supplied list of menuitem dicts."""
        self.itemDict = dctlst
        self.createMenuItems()
        return

    def createMenuItems(self):
        sz = self.Sizer
        mic = self.MenuItemContainer
        for itemDict in self.itemDict:
            itm = self._createMenuItemFromDict(itemDict)
            mic.Sizer.append(itm, "x")

    def appendMenuItem(self, caption):
        itm = self._createBlankMenuItem(caption)
        return self._addToMenu(itm)

    def _createMenuItemFromDict(self, itemDict):
        mic = self.MenuItemContainer
        atts = itemDict["attributes"]
        if itemDict["name"] == "SeparatorPanel":
            itm = SeparatorPanel(mic)
        else:
            itm = MenuItemPanel(mic, attProperties=atts)
        self.childItems.append(itm)
        itm.Menu = itm.MenuParent = self
        itm.Controller = self.Controller
        return itm

    def onDelete(self, evt):
        mb = self.MenuBar
        self.MenuItemContainer.release()
        mb.deleteMenu(self)
        mb.select()

    def onAppendMenuItem(self, evt):
        cap = dabo.ui.getString(_("Caption?"))
        if not cap:
            return
        itm = self._createBlankMenuItem(cap)
        self._addToMenu(itm)
        itm.select()
        return itm

    def onAppendSeparator(self, evt):
        return self.appendSeparator()

    def appendSeparator(self):
        return self.insertSeparator()

    def insertSeparator(self, pos=None):
        if pos is None:
            pos = len(self.childItems)
        itm = SeparatorPanel(self.MenuItemContainer)
        itm.Menu = itm.MenuParent = self
        itm.Controller = self.Controller
        self._addToMenu(itm, pos=pos)
        itm.select()
        return itm

    def _addToMenu(self, itm, pos=None):
        mic = self.MenuItemContainer
        if pos is None:
            mic.Sizer.append(itm)
            pos = itm.getPositionInSizer()
        else:
            mic.Sizer.insert(pos, itm, "x")
        if itm in self.childItems:
            # Item may be being moved
            self.childItems.remove(itm)
        self.childItems.insert(pos, itm)
        mic.layout()
        mic.fitToSizer()

    def onAddMenuLeft(self, evt):
        self._addMenu("left")

    def onAddMenuRight(self, evt):
        self._addMenu("right")

    def _addMenu(self, side):
        cap = dabo.ui.getString(_("Caption?"))
        if cap:
            self.MenuBar.addMenu(self, side, cap)

    def onMoveLeft(self, evt):
        self._moveMenu(-1)

    def onMoveRight(self, evt):
        self._moveMenu(1)

    def _moveMenu(self, direction):
        self.MenuBar.moveMenu(self, direction)

    def moveItem(self, obj, amount):
        """Changes the relative position of an item."""
        curr = obj.getPositionInSizer()
        newpos = curr + amount
        obj.setPositionInSizer(newpos)
        self.childItems.remove(obj)
        self.childItems.insert(newpos, obj)
        self.MenuItemContainer.layout()

    def _createBlankMenuItem(self, caption=None):
        if caption is None:
            caption = "<blank>"
        dct = {
            "attributes": {
                "Action": "",
                "Caption": caption,
                "HelpText": "",
                "HotKey": "",
                "Icon": "",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        itm = self._createMenuItemFromDict(dct)
        itm.Menu = itm.MenuParent = self
        return itm

    def addMenuItem(self, baseMenuItem, side, caption=None):
        pos = baseMenuItem.getPositionInSizer()
        if side.lower().startswith("b"):
            pos += 1
        mitm = self._createBlankMenuItem(caption)
        # The item will have been appended to the end of the childItems list.
        # Move it to the correct position in the list.
        self.childItems.remove(mitm)
        self.childItems.insert(pos, mitm)
        mic = self.MenuItemContainer
        mic.Sizer.insert(pos, mitm, "x")
        mic.layout()
        mic.fitToSizer()
        mitm.select()
        return mitm

    def addSeparator(self, baseMenuItem, side):
        pos = baseMenuItem.getPositionInSizer()
        if side.lower().startswith("b"):
            pos += 1
        mic = self.MenuItemContainer
        mitm = SeparatorPanel(mic)
        mitm.Menu = mitm.MenuParent = self
        mitm.Controller = self.Controller
        self.childItems.insert(pos, mitm)
        mic.Sizer.insert(pos, mitm, "x")
        mic.layout()
        mic.fitToSizer()
        mitm.select()
        return mitm

    def deleteMenuItem(self, itm):
        mic = self.MenuItemContainer
        sz = mic.Sizer
        self.childItems.remove(itm)
        sz.remove(itm, destroy=True)
        mic.layout()
        mic.fitToSizer()

    @property
    def MenuItemContainer(self):
        ret = self._menuitem_container
        if ret is None:
            ret = self._menuitem_container = MenuItemContainer(
                self.Parent.Parent, BorderWidth=3, BorderColor="darkblue"
            )
        return ret


class MenuItemPanel(AbstractMenuPanel):
    """Used for the menu items in menus."""

    def __init__(self, *args, **kwargs):
        super(MenuItemPanel, self).__init__(*args, **kwargs)
        self._isMenuItem = True

    def _initCaptions(self):
        self.lblCaption = dLabel(self, Caption=self.Caption, _EventTarget=self)
        self.lblHotKey = dLabel(self, Caption=self.HotKey, _EventTarget=self, ForeColor="sienna")
        self.lblCaption.FontSize += FONT_SIZE_DIFF
        self.lblHotKey.FontSize += FONT_SIZE_DIFF - 2
        hsz = self.capSizer = dSizerH()
        hsz.append(self.lblCaption, valign="middle")
        spc = self._minCaptionHotKeySpacing
        hsz.appendSpacer((spc, spc), 1)
        hsz.append(self.lblHotKey, valign="middle")
        self.Sizer.append(hsz, "x")
        self.Sizer.layout()

    def onMouseLeftClick(self, evt):
        self.select()

    def onContextMenu(self, evt):
        pop = dMenu()
        pos = self.getPositionInSizer()
        isFirst = pos == 0
        isLast = pos == (len(self.Parent.Children) - 1)
        pop.append(_("Add Item Above"), OnHit=self.onAddItemAbove)
        pop.append(_("Add Item Below"), OnHit=self.onAddItemBelow)
        pop.appendSeparator()
        pop.append(_("Add Separator Above"), OnHit=self.onAddSeparatorAbove)
        pop.append(_("Add Separator Below"), OnHit=self.onAddSeparatorBelow)
        pop.appendSeparator()
        if not isFirst:
            pop.append(_("Move Up"), OnHit=self.onMoveUp)
        if not isLast:
            pop.append(_("Move Down"), OnHit=self.onMoveDown)
        pop.appendSeparator()
        pop.append(_("Delete"), OnHit=self.onDelete)
        self.showContextMenu(pop)

    def onMoveUp(self, evt):
        self.Menu.moveItem(self, -1)

    def onMoveDown(self, evt):
        self.Menu.moveItem(self, 1)

    def onDelete(self, evt):
        mn = self.Menu
        mn.deleteMenuItem(self)
        mn.select()

    def onAddItemAbove(self, evt):
        self._addMenuItem("above")

    def onAddItemBelow(self, evt):
        self._addMenuItem("below")

    def onAddSeparatorAbove(self, evt):
        self._addSeparator("above")

    def onAddSeparatorBelow(self, evt):
        self._addSeparator("below")

    def _addMenuItem(self, side):
        cap = dabo.ui.getString(_("Caption?"))
        if cap:
            self.Menu.addMenuItem(self, side, cap)

    def _addSeparator(self, side):
        self.Menu.addSeparator(self, side)


class SeparatorPanel(MenuItemPanel):
    """Used for the menu items in menus."""

    def __init__(self, *args, **kwargs):
        super(SeparatorPanel, self).__init__(*args, **kwargs)
        self.Caption = "-separator-"
        self._isSeparator = True
        self._isMenuItem = False
        self.refresh()

    def _initCaptions(self):
        self.sepline = dLine(self, _EventTarget=self)
        self.Sizer.appendSpacer(8)
        self.Sizer.append(self.sepline, "x")
        self.Sizer.appendSpacer(8)
