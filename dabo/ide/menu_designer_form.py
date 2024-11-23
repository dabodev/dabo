#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os

from .. import ui

from ..dLocalize import _
from ..lib.utils import ustr
from .. import events
import dabo.lib.xmltodict as xtd
from ClassDesignerExceptions import PropertyUpdateException
import MenuPanel
from MenuDesignerPropForm import MenuPropForm
from ..ui import dButton
from ..ui import dForm
from ..ui import dLabel
from ..ui import dPanel
from ..ui import dSizer


class MenuDesignerForm(dForm):
    def __init__(self, *args, **kwargs):
        self._selection = None
        self._savedState = {}
        self._menuFile = None
        self._propForm = None
        self._propSheet = None
        self._inPropertyEditing = False
        appDir = self.Application.HomeDirectory
        kwargs["MenuBarFile"] = os.path.join(appDir, "MenuDesignerMenu.mnxml")
        self.Controller = self
        super(MenuDesignerForm, self).__init__(*args, **kwargs)
        self.Caption = "Dabo Menu Designer"
        self.mainPanel = dPanel(self)
        self.Sizer.append1x(self.mainPanel)
        self.topLevelMenuBar = None
        sz = self.mainPanel.Sizer = dSizer("v")
        self.initMenuBar()
        self._dragObject = None
        self._dragImage = None
        self._dragOrigPos = (0, 0)
        self._dragObjOffset = (0, 0)
        self._dragDrawPos = (0, 0)
        self.bindEvent(events.MouseMove, self.handleMouseMove)
        self.previewButton = btn = dButton(self.mainPanel, Caption="Preview", OnHit=self.onPreview)
        sz.append(btn, border=10, halign="center")
        dabo.ui.callAfter(self.layout)

    def afterInitAll(self):
        self.PropSheet.Controller = self
        self.PropForm.show()
        if not self._menuFile:
            # No menu file was opened; create a base menu
            self.createBaseMenu()
        try:
            self.topLevelMenuBar.childItems[0].select()
        except IndexError:
            self.topLevelMenuBar.select()
        dabo.ui.callAfter(self.layout)
        dabo.ui.callAfter(self.bringToFront)

    def initMenuBar(self, addBaseMenu=False):
        """Start from scratch with a basic menu bar."""
        try:
            self.topLevelMenuBar.release()
        except AttributeError:
            pass
        self.mainPanel.BackColor = "darkgrey"
        mbar = self.topLevelMenuBar = MenuPanel.MenuBarPanel(
            self.mainPanel, Caption="- MenuBar -", Controller=self
        )

        self.mainPanel.Sizer.append1x(mbar)
        if addBaseMenu:
            self.createBaseMenu()
        return mbar

    def handleMouseMove(self, evt):
        # Not implemented yet, so just return
        return
        if evt.dragging:
            self.handleMouseDrag(evt)

    def processLeftUp(self, obj, evt):
        # Not implemented yet
        return
        # When I have time to finish implementing drag n drop...
        if self.DragObject:
            drobj = self.DragObject
            cont = drobj.Parent
            print("ORIG", self._dragOrigPos)
            print("CONT TL:", cont.Position)
            print("CONT BR:", (cont.Right, cont.Bottom))
            mp = dabo.ui.getMousePosition()
            print("NOW", mp)
            print("NOW FMP", dabo.ui.getFormMousePosition())
            print("FORM MP", drobj.formCoordinates(mp))
            print("FORM CONT TL", cont.formCoordinates(cont.Position))
            print("FORM CONT BR", cont.formCoordinates((cont.Right, cont.Bottom)))

            objat = dabo.ui.getObjectAtPosition(mp)
            print("OBJ AT", objat)
            print("VIS", self._dragImage.Visible)
            print("PARENT", objat.Parent is self.DragObject.Parent)
            print("GPAR", objat.Parent.Parent is self.DragObject.Parent)
            try:
                print(objat.Caption)
            except:
                print("no cap")

            self.DragObject = None
            if self._dragImage:
                self.removeDrawnObject(self._dragImage)
                self._dragImage = None
            self.clear()
            self.refresh()

    def handleMouseDrag(self, evt):
        # The EventObject is the object being dragged over.
        obj = evt.EventObject
        if evt.dragging:
            if not self.DragObject:
                self.DragObject = obj
            if self._dragImage:
                self._dragImage.Visible = obj.Parent is self.DragObject.Parent
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
            self.DragObject = None

    def treeSelect(self):
        dabo.ui.stop("Not implemented yet - sorry!")

    def createBaseMenu(self):
        """Creates a base menu with common menuitems."""
        menu_dict = self._createBaseMenuDict()
        self.makeMenuBar(menu_dict)
        dabo.ui.callAfter(self.saveState)

    def makeMenuBar(self, dct=None):
        mb = self.topLevelMenuBar
        if dct is None:
            mb.showTopLevel()
        else:
            mb.createMenuFromDict(dct)
        self.layout()

    def clearMenus(self):
        self.topLevelMenuBar.menus = []

    def getPropDictForObject(self, obj):
        return {}

    def saveMenu(self):
        if not self._menuFile:
            self._menuFile = dabo.ui.getSaveAs(wildcard="mnxml")
            if not self._menuFile:
                # User canceled
                return
            else:
                if not os.path.splitext(self._menuFile)[1] == ".mnxml":
                    self._menuFile += ".mnxml"
        propDict = self._getState()
        xml = xtd.dicttoxml(propDict)
        fname = self._menuFile
        # Try opening the file. If it is read-only, it will raise an
        # IOErrorrror that the calling method can catch.
        codecs.open(fname, "wb", encoding="utf-8").write(xml)
        self.saveState()

    def onPreview(self, evt):
        class PreviewWindow(dForm):
            def initProperties(self):
                self.Caption = "Menu Preview"
                self.ShowMenuBar = False

            def afterInit(self):
                mp = dPanel(self)
                self.Sizer.append1x(mp)
                sz = mp.Sizer = dSizer("v")
                sz.appendSpacer(30)
                self.lblResult = dLabel(
                    mp,
                    Caption="Menu Selection: \n\n ",
                    FontBold=True,
                    ForeColor="darkred",
                    AutoResize=True,
                    Alignment="Center",
                )
                self.lblResult.FontSize += 2
                sz.append(self.lblResult, "x", halign="center", border=10)
                btn = dButton(mp, Caption="Close Menu Preview", OnHit=self.onClose)
                sz.append(btn, halign="center", border=30)
                mp.fitToSizer()
                dabo.ui.callAfter(self.refresh)

            def onClose(self, evt):
                self.release()

            def notify(self, evt):
                itm = evt.EventObject
                pth = [itm.Caption]
                mp = itm.Parent
                while mp and not isinstance(mp, dabo.ui.dMenuBar.dMenuBar):
                    pth.append(mp.Caption)
                    mp = mp.Parent
                pth.reverse()
                cap = " - ".join(pth)
                fncText = "Function: %s" % itm._bindingText
                seltxt = "Menu Selection: %s\n\n%s" % (cap, fncText)
                self.lblResult.Caption = seltxt
                self.layout()

        propDict = self._getState()
        win = PreviewWindow(self, Centered=True)
        mb = dabo.ui.createMenuBar(propDict, win, win.notify)
        win.MenuBar = mb
        win.show()

    def _createBaseMenuDict(self):
        """This creates the dict that represents a base menu."""
        from dabo import icons

        iconPath = os.path.dirname(icons.__file__) + r"/themes/tango/16x16"
        # iconPath = "themes/tango/16x16"
        sep = {"attributes": {}, "children": [], "name": "SeparatorPanel"}

        m_new = {
            "attributes": {
                "Caption": _("&New"),
                "Action": "form.onNew",
                "HelpText": "",
                "HotKey": "Ctrl+N",
                "ItemID": "file_new",
                "Icon": "new",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_open = {
            "attributes": {
                "Caption": _("&Open"),
                "Action": "form.onOpen",
                "HelpText": "",
                "HotKey": "Ctrl+O",
                "ItemID": "file_open",
                "Icon": "open",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_close = {
            "attributes": {
                "Caption": _("&Close"),
                "Action": "form.onClose",
                "HelpText": "",
                "HotKey": "Ctrl+W",
                "ItemID": "file_close",
                "Icon": "close",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_save = {
            "attributes": {
                "Caption": _("&Save"),
                "Action": "form.onSave",
                "HelpText": "",
                "HotKey": "Ctrl+S",
                "ItemID": "file_save",
                "Icon": "save",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_saveas = {
            "attributes": {
                "Caption": _("Save &As"),
                "Action": "form.onSaveAs",
                "HelpText": "",
                "HotKey": "",
                "ItemID": "file_saveas",
                "Icon": "saveas",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_cmd = {
            "attributes": {
                "Caption": _("Command Win&dow"),
                "Action": "app.onCmdWin",
                "HelpText": "",
                "HotKey": "Ctrl+D",
                "ItemID": "file_commandwin",
                "Icon": "%s/apps/utilities-terminal.png" % iconPath,
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_quit = {
            "attributes": {
                "Caption": _("&Quit"),
                "Action": "app.onFileExit",
                "HelpText": "",
                "HotKey": "Ctrl+Q",
                "ItemID": "file_quit",
                "Icon": "quit",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        file_menu = {
            "attributes": {"Caption": "File", "HelpText": "", "MRU": True},
            "children": [
                m_new,
                m_open,
                m_close,
                m_save,
                m_saveas,
                sep,
                m_cmd,
                sep,
                m_quit,
            ],
            "name": "MenuPanel",
        }

        m_undo = {
            "attributes": {
                "Caption": _("&Undo"),
                "Action": "app.onEditUndo",
                "HelpText": "",
                "HotKey": "Ctrl+Z",
                "ItemID": "edit_",
                "Icon": "undo",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_redo = {
            "attributes": {
                "Caption": _("&Redo"),
                "Action": "app.onEditRedo",
                "HelpText": "",
                "HotKey": "Ctrl+Shift+Z",
                "ItemID": "edit_undo",
                "Icon": "redo",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_copy = {
            "attributes": {
                "Caption": _("&Copy"),
                "Action": "app.onEditCopy",
                "HelpText": "",
                "HotKey": "Ctrl+C",
                "ItemID": "edit_copy",
                "Icon": "copy",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_cut = {
            "attributes": {
                "Caption": _("Cu&t"),
                "Action": "app.onEditCut",
                "HelpText": "",
                "HotKey": "Ctrl+X",
                "ItemID": "edit_cut",
                "Icon": "cut",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_paste = {
            "attributes": {
                "Caption": _("&Paste"),
                "Action": "app.onEditPaste",
                "HelpText": "",
                "HotKey": "Ctrl+V",
                "ItemID": "edit_paste",
                "Icon": "paste",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_selectall = {
            "attributes": {
                "Caption": _("Select &All"),
                "Action": "app.onEditSelectAll",
                "HelpText": "",
                "HotKey": "Ctrl+A",
                "ItemID": "edit_selectall",
                "Icon": None,
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_find = {
            "attributes": {
                "Caption": _("&Find / Replace"),
                "Action": "app.onEditFind",
                "HelpText": "",
                "HotKey": "Ctrl+F",
                "ItemID": "edit_find",
                "Icon": "find",
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_findagain = {
            "attributes": {
                "Caption": _("Find A&gain"),
                "Action": "app.onEditFindAgain",
                "HelpText": "",
                "HotKey": "Ctrl+G",
                "ItemID": "edit_findagain",
                "Icon": None,
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        edit_menu = {
            "attributes": {"Caption": "Edit", "HelpText": "", "MRU": False},
            "children": [
                m_undo,
                m_redo,
                sep,
                m_cut,
                m_copy,
                m_paste,
                sep,
                m_selectall,
                sep,
                m_find,
                m_findagain,
            ],
            "name": "MenuPanel",
        }

        m_zoomin = {
            "attributes": {
                "Caption": _("&Increase Font Size"),
                "Action": "app.fontZoomIn",
                "HelpText": "",
                "HotKey": "Ctrl++",
                "ItemID": "view_zoomin",
                "Icon": None,
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_zoomout = {
            "attributes": {
                "Caption": _("&Decrease Font Size"),
                "Action": "app.fontZoomOut",
                "HelpText": "",
                "HotKey": "Ctrl+-",
                "ItemID": "view_zoomout",
                "Icon": None,
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        m_zoomnormal = {
            "attributes": {
                "Caption": _("&Normal Font Size"),
                "Action": "app.fontZoomNormal",
                "HelpText": "",
                "HotKey": "Ctrl+/",
                "ItemID": "view_zoomnormal",
                "Icon": None,
            },
            "children": [],
            "name": "MenuItemPanel",
        }
        view_menu = {
            "attributes": {"Caption": "View", "HelpText": "", "MRU": False},
            "children": [m_zoomin, m_zoomout, m_zoomnormal],
            "name": "MenuPanel",
        }

        help_menu = {
            "attributes": {"Caption": "Help", "HelpText": "", "MRU": False},
            "children": [],
            "name": "MenuPanel",
        }

        return {
            "attributes": {},
            "name": "MenuBarPanel",
            "children": [file_menu, edit_menu, view_menu, help_menu],
        }

    def onAppendMenu(self, evt):
        """Handler for the menu item selection."""
        cap = dabo.ui.getString(_("Caption?"))
        if cap:
            return self.topLevelMenuBar.appendMenu(cap)

    def onAppendMenuItem(self, evt):
        """Handler for the menu item selection."""
        menu = None
        sel = self.Selection
        while sel:
            if isinstance(sel, MenuPanel.MenuPanel):
                menu = sel
                break
            sel = sel.MenuParent
        if not menu:
            dabo.ui.stop(_("Please select a menu first."))
            return
        cap = dabo.ui.getString(_("Caption?"))
        if cap:
            return menu.appendMenuItem(cap)

    def onAppendSeparator(self, evt):
        """Handler for the menu item selection."""
        menu = None
        sel = self.Selection
        while sel:
            if isinstance(sel, MenuPanel.MenuPanel):
                menu = sel
                break
            sel = sel.MenuParent
        if not menu:
            dabo.ui.stop(_("Please select a menu first."))
            return
        return menu.appendSeparator()

    def onMoveItemUp(self, evt):
        self.Controller.Selection.onMoveUp(evt)

    def onMoveItemDown(self, evt):
        self.Controller.Selection.onMoveDown(evt)

    def onDeleteSelection(self, evt):
        sel = self.Controller.Selection
        itemType = {
            MenuPanel.MenuPanel: "menu",
            MenuPanel.MenuItemPanel: "menu item",
            MenuPanel.SeparatorPanel: "separator",
        }.get(sel.__class__)
        if itemType is None:
            # Not a valid selection to delete
            dabo.log.info(_("The current selection cannot be deleted"))
            return
        cap = sel.Caption
        if itemType == "separator":
            msg = "Are you sure you want to delete this separator?"
        else:
            msg = "Are you sure you want to delete the %(itemType)s '%(cap)s'?" % locals()
        if dabo.ui.areYouSure(msg, "Delete", defaultNo=True, cancelButton=False):
            sel.onDelete(evt)

    def copyAsJSON(self, evt):
        """
        Places a JSON-ified copy of the dict representing the current
        state of the menu design onto the clipboard.
        """
        dct = self._getState()
        jsonDct = dabo.lib.jsonEncode(dct)
        self.Application.copyToClipboard(jsonDct)

    def getObjectHierarchy(self, parent=None, level=0):
        """
        Returns a list of 2-tuples representing the structure of
        the objects on this form. The first element is the nesting level,
        and the second is the object. The objects are in the order
        created, irrespective of sizer position.
        """
        if parent is None:
            parent = self.topLevelMenuBar
        ret = [(level, parent)]
        for kid in parent.childItems:
            ret += self.getObjectHierarchy(kid, level + 1)
        return ret

    def updateLayout(self):
        try:
            self.PropForm.updateLayout()
        except AttributeError:
            # Prop form not yet created
            pass

    def saveState(self):
        self._savedState = self._getState()

    def _getState(self):
        return self.topLevelMenuBar.getDesignerDict()

    def beforeClose(self, evt):
        return not self._isDirty()

    def _isDirty(self):
        ret = False
        curr = self._getState()
        if curr != self._savedState:
            cf = self._menuFile
            if cf:
                fname = os.path.split(cf)[1]
            else:
                fname = _("Untitled")
            saveIt = dabo.ui.areYouSure(
                _("Do you want to save the changes to '%s'?") % fname,
                _("Unsaved Changes"),
            )
            if saveIt is None:
                # They canceled
                ret = True
            elif saveIt is True:
                # They want to save
                ret = self.saveMenu()
            # Otherwise, they said 'No'
        return ret

    def onNew(self, evt):
        if not self._isDirty():
            self.initMenuBar(addBaseMenu=True)

    def onOpen(self, evt):
        if self._isDirty():
            return
        pth = dabo.ui.getFile("mnxml")
        if not pth:
            # They canceled
            return
        self.openFile(pth)

    def onClose(self, evt):
        self.raiseEvent(events.Close, evt._uiEvent)

    def onSave(self, evt):
        self.saveMenu()

    def onSaveAs(self, evt):
        dabo.ui.stop("SaveAs Not Implemented Yet")

    def onKeyChar(self, evt):
        """Trap the arrow keys and use them for navigation, if possible."""
        kc = evt.keyCode
        dk = dabo.ui.dKeys
        if (kc not in list(dk.allArrowKeys.values())) or any(
            (evt.shiftDown, evt.altDown, evt.controlDown, evt.metaDown)
        ):
            # Only handle unmodified arrow keys.
            return
        # Necessary to prevent duplicate key events.
        evt.stop()
        curr = self.Controller.Selection
        sz = curr.ControllingSizer
        pos = curr.getPositionInSizer()
        plusKeys = {
            "Horizontal": (dk.key_Right, dk.key_Numpad_right),
            "Vertical": (dk.key_Down, dk.key_Numpad_down),
        }[sz.Orientation]
        minusKeys = {
            "Horizontal": (dk.key_Left, dk.key_Numpad_left),
            "Vertical": (dk.key_Up, dk.key_Numpad_up),
        }[sz.Orientation]
        if kc in plusKeys:
            change = 1
        elif kc in minusKeys:
            change = -1
        else:
            # Not an appropriate arrow key for the orientation
            return
        try:
            self.Controller.select(sz.ChildObjects[pos + change])
        except IndexError:
            # Will happen when the last item is selected; wrap to first.
            self.Controller.select(sz.ChildObjects[0])

    def openFile(self, pth):
        if not os.path.exists(pth):
            dabo.ui.stop("The file '%s' does not exist" % pth)
            return
        self._menuFile = pth
        xml = open(pth).read()
        try:
            dct = xtd.xmltodict(xml)
        except:
            raise IOError(_("This does not appear to be a valid menu file."))
        self.makeMenuBar(dct)
        self.layout()
        self.saveState()

    def updatePropVal(self, prop, val, typ):
        obj = self.Selection
        if obj is None:
            return
        if typ is bool:
            val = bool(val)
        if isinstance(val, str):
            strVal = val
        else:
            strVal = str(val)
        if typ in (str, str) or ((typ is list) and isinstance(val, str)):
            # Escape any single quotes, and then enclose
            # the value in single quotes
            strVal = "u'" + self.escapeQt(strVal) + "'"
        try:
            exec("obj.%s = %s" % (prop, strVal))
        except Exception as e:
            raise PropertyUpdateException(ustr(e))
        self.PropForm.updatePropGrid()
        # This is necessary to force a redraw when some props change.
        self.select(obj)
        try:
            obj.setWidth()
        except AttributeError:
            pass
        self.layout()

    def onShowPanel(self, menu):
        """Called when code makes a menu panel visible."""
        self.topLevelMenuBar.hideAllBut(menu)

    def select(self, obj):
        if obj is self._selection:
            return
        if self._selection is not None:
            self._selection.Selected = False
        self._selection = obj
        self.PropForm.select(obj)
        obj.Selected = True
        self.ensureVisible(obj)
        dabo.ui.callAfterInterval(100, self._selectAfter)

    def _selectAfter(self):
        self.update()
        self.refresh()

    def startPropEdit(self):
        self._inPropertyEditing = True

    def endPropEdit(self):
        self._inPropertyEditing = False

    def ensureVisible(self, obj):
        """When selecting a menu item, make sure that its menu is open."""
        if isinstance(obj, (list, tuple)):
            obj = obj[-1]

    def escapeQt(self, s):
        sl = "\\"
        qt = "'"
        return s.replace(sl, sl + sl).replace(qt, sl + qt)

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
            # Save the original position of the mouse down
            (formX, formY) = self._dragOrigPos = self.getMousePosition()
            (objX, objY) = self._dragObjOffset = val.getMousePosition()
            # Create an image of the control
            self._dragImage = self.drawBitmap(
                val.getCaptureBitmap(), x=formX - objX, y=formY - objY
            )
        self._dragObject = val

    def _getPropForm(self):
        noProp = self._propForm is None
        if not noProp:
            # Make sure it's still a live object
            try:
                junk = self._propForm.Visible
            except Exception:
                noProp = True
        if noProp:
            pf = self._propForm = MenuPropForm(
                self, Visible=False, MenuBarFile=self.MenuBarFile, Controller=self
            )
            pf.restoreSizeAndPosition()
            self.updateLayout()
            pf.Visible = True
        return self._propForm

    def _getPropSheet(self):
        if self._propSheet is None:
            self._propSheet = self.PropForm.PropSheet
        return self._propSheet

    def _getSelection(self):
        return self._selection

    def _setSelection(self, val):
        self.select(val)

    DragObject = property(
        _getDragObject,
        _setDragObject,
        None,
        _("Reference to the object being dragged on the form  (MenuPanel/MenuItemPanel)"),
    )

    PropForm = property(
        _getPropForm,
        None,
        None,
        _(
            """Reference to the form that contains the PropSheet
            object (MenuPropForm)"""
        ),
    )

    PropSheet = property(
        _getPropSheet, None, None, _("Reference to the Property Sheet (PropSheet)")
    )

    Selection = property(
        _getSelection, _setSelection, None, _("Currently selected item  (CaptionPanel)")
    )
