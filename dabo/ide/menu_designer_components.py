#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from .. import ui
from ..dLocalize import _
from .. import events
from ..ui import makeDynamicProperty
from ..ui import makeProxyProperty

from ..ui import dBitmap
from ..ui import dForm
from ..ui import dPanel


class MenuSaverMixin(object):
    """Contains the basic code for generating the dict required
    to save the MenuDesigner's contents.
    """

    def getDesignerDict(self):
        ret = {}
        ret["name"] = self.__class__.__name__
        ret["attributes"] = ra = {}
        propsToExclude = ("HotKeyChar", "HotKeyControl", "HotKeyAlt", "HotKeyShift")
        for prop in self.DesignerProps:
            if prop in propsToExclude:
                continue
            if hasattr(self, prop):
                val = eval("self.%s" % prop)
            else:
                # Custom-defined property; that's saved elsewhere
                continue
            if isinstance(val, str) and os.path.exists(val):
                # It's a path; convert it to a relative path
                if isinstance(self, dForm):
                    ref = self.Form._menuBarFile
                else:
                    ref = "."
                ref = os.path.abspath(ref)
                val = dabo.lib.utils.getPathAttributePrefix() + dabo.lib.utils.relativePath(
                    val, ref
                )
            if isinstance(val, str):
                strval = val
            else:
                strval = str(val)
            # Special cases
            try:
                evalStrVal = eval(strval)
            except:
                evalStrVal = None
            ra[prop] = val
        ret["children"] = [
            kid.getDesignerDict() for kid in self.Children if hasattr(kid, "getDesignerDict")
        ]
        return ret


class CaptionPanel(MenuSaverMixin, dPanel):
    # Name for the saved mnxml file
    _className = "CaptionPanel"
    # Displayed name
    _commonName = "Generic Item"
    _kids = []

    def __init__(self, parent, *args, **kwargs):
        self._caption = ""
        self._MRU = False
        self._selected = False
        self._inUpdate = False
        # The draw object representing the Caption
        self._capText = None
        # The draw object representing the HotKey
        self._hotKeyText = None
        # Minimum spacing between the caption and hot key
        self._captionHotKeySpacing = 20
        # Function to be called when a menu item is selected. This
        # is a string representation that will be eval'd at runtime
        self._action = ""
        # Flag to let the Menu Designer know that this is a MenuItem
        self.isMenuItem = False
        # The following underlie the HotKey property and its components
        self._hotKey = ""
        self._hotKeyAlt = False
        self._hotKeyChar = ""
        self._hotKeyControl = False
        self._hotKeyShift = False
        super(CaptionPanel, self).__init__(parent, *args, **kwargs)
        self.BorderWidth = 1
        self.BorderColor = (222, 222, 222)
        self.Height = 24
        self._unselectedBackColor = "white"
        self._selectedBackColor = (255, 255, 192)
        self._unselectedForeColor = "black"
        self._selectedForeColor = "blue"
        # This is the background draw object
        self._background = self.drawRectangle(
            0, 0, -1, -1, penWidth=0, fillColor=self._unselectedBackColor, visible=False
        )
        self._capText = self.drawText(self.Caption, 5, 5, visible=False)
        self._hotKeyText = self.drawText(self.AbbreviatedHotKey, 5, 5, visible=False)
        self.DynamicBackColor = self.getBack  # lambda: {True: self._selectedBackColor, False: self._unselectedBackColor}[self._selected]
        self._background.DynamicFillColor = self._capText.DynamicFillColor = (
            self._hotKeyText.DynamicFillColor
        ) = self.getBack  # lambda: {True: self._selectedBackColor, False: self._unselectedBackColor}[self._selected]
        self._capText.DynamicForeColor = lambda: {
            True: self._selectedForeColor,
            False: self._unselectedForeColor,
        }[self._selected]
        # This will allow the hot key text position to stay right-aligned.
        self._hotKeyText.DynamicXpos = self.positionHotKeyText
        self.refresh()
        self.Parent.update()
        self._dragging = False
        self._dragImg = None
        self._helpText = ""
        # We want the drawing surface cleared between drawings
        self.autoClearDrawings = True
        # We want Hover behavior
        self.Hover = True
        # Smooth the drawing
        self.Buffered = True

        self._kids = [self._background, self._hotKeyText, self._capText]

    def getBack(self):
        if self._selected:
            ret = self._selectedBackColor
        else:
            ret = self._unselectedBackColor
        return ret

    # These two methods will display the item's HelpText
    # in the form's Status Bar when the mouse is over them.
    def onHover(self, evt):
        self.Form.StatusText = self.HelpText

    def endHover(self, evt):
        self.Form.StatusText = ""

    #### Someday I hope to have the time to enable dragging menus
    #### around to re-arrange them!
    #     def onMouseLeftDown(self, evt):
    #         self._dragging = True
    #         self._dragImg = dDragImage(self)
    #
    #     def onMouseMove(self, evt):
    #         if not self._dragging:
    #             return
    #         if evt.mouseDown:
    #             self._dragImg.updatePosition()
    #         else:
    #             self._dragImg.clear()
    #             self._dragImg = None
    #             self._dragging = False
    #
    #     def onMouseLeftUp(self, evt):
    #         print "LEFT UP", self._caption,  self._dragging,
    #         self._dragging = False
    #         x, y = evt.mousePosition
    #         print x, y, self.posIsWithin(x, y)
    #         if self._dragImg:
    #             self._dragImg.clear()
    #         self._dragImg = None

    def setWidth(self):
        """Set the width to the width of the text, plus 5 pixels on each side."""
        curr = self.Width
        capwd = dabo.ui.fontMetricFromDrawObject(self._capText)[0]
        hkwd = dabo.ui.fontMetricFromDrawObject(self._hotKeyText)[0]
        addlwd = self.getAdditionalWidth()
        if self._hotKey:
            addlwd += self._captionHotKeySpacing
        calc = capwd + hkwd + addlwd
        if curr < calc:
            self.Width = calc

    def positionHotKeyText(self):
        "This is the function for the DynamicXPos property of the HotKey." ""
        hkt = self._hotKeyText
        wd = dabo.ui.fontMetricFromDrawObject(hkt)[0]
        margin = 10
        return (self.Width - wd) - margin

    def getAdditionalWidth(self):
        """Provide for a little 'breathing room' on the panel. Subclasses
        can override as needed if they contain additional items.
        """
        return 10

    def refresh(self):
        if self._capText is not None:
            dabo.ui.callAfterInterval(60, self._refresh)

    def _refresh(self):
        """By linking this to a 'callAfterInterval', when several events
        that require a refresh occur quickly, the 'slow stuff' only gets
        called once.
        """
        super(CaptionPanel, self).refresh()
        self.setWidth()
        self.Parent.update()
        self.Parent.layout()

    def onContextMenu(self, evt):
        self.Parent.processContextMenu(self, evt)

    def onMouseLeftClick(self, evt):
        self.Form.select(self)

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
        ctlTxt = {True: "c", False: ""}[self.HotKeyControl]
        shiftTxt = {True: "s", False: ""}[self.HotKeyShift]
        altTxt = {True: "a", False: ""}[self.HotKeyAlt]
        prefix = ctlTxt + altTxt + shiftTxt
        if prefix:
            prefix += "+"
        return prefix + self.HotKeyChar

    def _getAction(self):
        return self._action

    def _setAction(self, val):
        if self._constructed():
            self._action = val
        else:
            self._properties["Action"] = val

    def _getCaption(self):
        return self._caption

    def _setCaption(self, val):
        self._caption = val
        if self._capText is not None:
            self._capText.Text = val
            self.refresh()

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
            "Caption": {"type": str, "readonly": False},
            "HelpText": {"type": str, "readonly": False},
            "MRU": {"type": bool, "readonly": False},
        }
        if self.isMenuItem:
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
                }
            )
            del ret["MRU"]
        return ret

    def _getDisplayText(self):
        return "%s: '%s'" % (self._commonName, self.Caption)

    def _getHelpText(self):
        return self._helpText

    def _setHelpText(self, val):
        if self._constructed():
            self._helpText = val
        else:
            self._properties["HelpText"] = val

    def _getHotKey(self):
        return self._hotKey

    def _setHotKey(self, val):
        if self._constructed():
            self._hotKey = val
            self._updateHotKeyProps(val)
            self._hotKeyText.Text = self._getAbbreviatedHotKey()
            self.update()
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

    def _getMRU(self):
        return self._MRU

    def _setMRU(self, val):
        self._MRU = val

    def _getSelected(self):
        return self._selected

    def _setSelected(self, val):
        if self._constructed():
            self._selected = val
            #             self.clear()
            #             self.lockDisplay()
            #             backcolor = {True: self._selectedBackColor,
            #                     False: self._unselectedBackColor}[val]
            #             forecolor = {True: self._selectedForeColor,
            #                     False: self._unselectedForeColor}[val]
            #             self._capText.ForeColor = self._capText.PenColor = forecolor
            #             self._capText.FontBold = val
            #             self.BackColor = self._background.FillColor = backcolor
            self.Parent.refresh()
        #             self.unlockDisplay()
        else:
            self._properties["Selected"] = val

    # Tree display is the same as the displayed text
    def _getTreeDisplayCaption(self):
        return ("'%s'" % self.Caption, self._commonName)

    AbbreviatedHotKey = property(
        _getAbbreviatedHotKey,
        None,
        None,
        _("Short version of the HotKey string (read-only) (str)"),
    )

    Action = property(
        _getAction,
        _setAction,
        None,
        _("Action to be called when a menu item is selected.  (str)"),
    )

    Caption = property(_getCaption, _setCaption, None, _("Caption displayed on this panel  (str)"))

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

    DisplayText = property(
        _getDisplayText,
        None,
        None,
        _("Text used in the prop sheet to identify this object (read-only) (str)"),
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

    MRU = property(_getMRU, _setMRU, None, _("Should this menu be tracked for MRU lists  (bool)"))

    Selected = property(
        _getSelected,
        _setSelected,
        None,
        _("Is this the currently selected item?  (bool)"),
    )

    TreeDisplayCaption = property(
        _getTreeDisplayCaption,
        None,
        None,
        _("Identifying label displayed in the prop sheet tree (read-only) (str)"),
    )

    _proxyDict = {}
    Visible = makeProxyProperty(_proxyDict, "Visible", ("self", "_kids"))


class CaptionBitmapPanel(CaptionPanel):
    """Like the CaptionPanel, but can also display a bitmap image
    to the left of the caption.
    """

    # Name for the saved mnxml file
    _className = "CaptionBitmapPanel"

    def __init__(self, parent, *args, **kwargs):
        self._bitmap = None
        self._bmp = None
        self._picture = None
        super(CaptionBitmapPanel, self).__init__(parent, *args, **kwargs)

    def getAdditionalWidth(self):
        """Add in the width of the bitmap."""
        ret = super(CaptionBitmapPanel, self).getAdditionalWidth()
        if self._bmp is not None:
            ret += self._bmp.Width + 5
        return ret

    def _getBitmap(self):
        return self._bitmap

    def _setBitmap(self, val):
        self._bitmap = val
        if isinstance(val, str):
            bmp = dabo.ui.strToBmp(val)
        else:
            bmp = val
        # Create the bitmap object
        if self._bmp:
            # Remove it.
            self.removeDrawnObject(self._bmp)
            self._kids.remove(self._bmp)
            self._bmp = None
        self._bmp = self.drawBitmap(bmp, 5, 5, visible=self.Parent.Visible)
        self._kids.append(self._bmp)

        wd = self._bmp.Width
        # Move the text over to fit
        self._capText.Xpos = wd + 10
        self.refresh()

    def _getDesignerProps(self):
        ret = super(CaptionBitmapPanel, self)._getDesignerProps()
        ret.update(
            {
                "Picture": {
                    "type": "path",
                    "readonly": False,
                    "customEditor": "editStdPicture",
                }
            }
        )
        return ret

    def _getPicture(self):
        return self._picture

    def _setPicture(self, val):
        self._picture = val
        if isinstance(val, dBitmap):
            bmp = val
        else:
            bmp = dabo.ui.strToBmp(val)
        self._setBitmap(bmp)

    Bitmap = property(_getBitmap, _setBitmap, None, _("Bitmap to display on the panel  (bitmap)"))

    DesignerProps = property(
        _getDesignerProps,
        None,
        None,
        _("Properties exposed in the Menu Designer (read-only) (dict)"),
    )

    Picture = property(
        _getPicture,
        _setPicture,
        None,
        _("The file used as the source for the displayed image.  (str)"),
    )


class SeparatorPanel(CaptionBitmapPanel):
    """Represents a menu separator item."""

    # Name for the saved mnxml file
    _className = "SeparatorPanel"
    # Displayed name
    _commonName = "Separator"
    # Displayed separator line
    _line = None

    def afterInitAll(self):
        self.Height = 16
        midHt = self.Height / 2.0
        self._line = self.drawLine(4, midHt, self.Width - 4, midHt, penColor="gray", penWidth=1)
        self._line.DynamicPoints = self.setLineWidth
        self._line.DynamicPenWidth = self.setLineThick
        self._kids.append(self._line)

    def onResize(self, evt):
        if self._line:
            self.update()

    def setLineWidth(self):
        """We want the line to be the full width of the panel,
        with a few pixels 'breathing room' on each side.
        """
        midHt = self.Height / 2.0
        x1 = 4
        x2 = self.Width - 4
        y1 = y2 = midHt
        return ((x1, y1), (x2, y2))

    def setLineThick(self):
        """Make it look thicker when selected."""
        return {True: 2, False: 1}[self.Selected]

    def _getDesignerProps(self):
        return {}

    def _getDisplayText(self):
        return "Separator"

    DesignerProps = property(
        _getDesignerProps,
        None,
        None,
        _("Properties exposed in the Menu Designer (read-only) (dict)"),
    )

    DisplayText = property(
        _getDisplayText,
        None,
        None,
        _("Text used in the prop sheet to identify this object (read-only) (str)"),
    )
