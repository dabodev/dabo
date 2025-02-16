#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import wx
import wx.richtext

from .. import application
from .. import color_tools
from .. import ui
from ..lib.utils import ustr
from ..localization import _
from . import dButton
from . import dDataControlMixin
from . import dDropdownList
from . import dForm
from . import dTimer
from . import dToggleButton
from . import makeDynamicProperty

dabo_module = settings.get_dabo_package()


class dRichTextBox(dDataControlMixin, wx.richtext.RichTextCtrl):
    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dRichTextBox
        # Used to test if selection has any of the styles applied to any part of it.
        self._styleObj = wx.richtext.TextAttrEx()
        self._styleObj.SetFlags(
            wx.TEXT_ATTR_BACKGROUND_COLOUR
            | wx.TEXT_ATTR_FONT_FACE
            | wx.TEXT_ATTR_FONT_ITALIC
            | wx.TEXT_ATTR_FONT_SIZE
            | wx.TEXT_ATTR_FONT_UNDERLINE
            | wx.TEXT_ATTR_FONT_WEIGHT
            | wx.TEXT_ATTR_TEXT_COLOUR
        )
        # Used for saving/loading rich text from files
        self._xmlHandler = wx.richtext.RichTextXMLHandler()
        self._htmlHandler = wx.richtext.RichTextHTMLHandler()
        self._handlers = (self._xmlHandler, self._htmlHandler)
        preClass = wx.richtext.PreRichTextCtrl
        dDataControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def load(self, fileOrObj=None):
        """
        Takes either a file-like object or a file path, and loads the content
        into the control.
        """
        if fileOrObj is None:
            fileOrObj = ui.getFile("xml", "html")
        if isinstance(fileOrObj, str):
            mthdName = "LoadFile"
        else:
            mthdName = "LoadStream"
        buff = self.GetBuffer()
        for handler in self._handlers:
            mthd = getattr(handler, mthdName)
            try:
                if mthd(buff, fileOrObj):
                    break
            except Exception as e:
                print(e, type(e))
        ui.callAfter(self.Form.refresh)

    def save(self, filename=None):
        if filename is None:
            filename = ui.getSaveAs("xml", "html")
        if filename:
            # Default to xml if not found
            handler = {".xml": self._xmlHandler, ".html": self._htmlHandler}.get(
                os.path.splitext(filename)[1]
            )
            if handler is None:
                handler = self._xmlHandler
                filename = "%s.xml" % filename
                dabo_module.info(_("Forcing to RichText XML format"))
            handler.SaveFile(self.GetBuffer(), filename)

    def setPlain(self):
        """Removes all styles from the selected text"""
        self.SelectionPlain = True

    ## property definitions
    @property
    def CurrentBackColor(self):
        """Background color at the current insertion point.  (RGB 3-tuple)"""
        ds = self.GetDefaultStyle()
        ret = ds.GetBackgroundColour()[:3]
        return ret

    @property
    def CurrentForeColor(self):
        """Foreground color at the current insertion point.  (RGB 3-tuple)"""
        ds = self.GetDefaultStyle()
        ret = ds.GetTextColour()[:3]
        return ret

    @property
    def CurrentFontBold(self):
        """Font bold status at the current insertion point.  (str)"""
        return "Bold" in self._getCurrentStyle()

    @property
    def CurrentFontFace(self):
        """Font face at the current insertion point.  (str)"""
        ds = self.GetDefaultStyle()
        # Default to the current font face for the control
        ret = self.FontFace
        if ds.HasFont():
            ret = ds.GetFont().GetFaceName()
        return ret

    @property
    def CurrentFontItalic(self):
        """Font italic status at the current insertion point.  (str)"""
        return "Italic" in self._getCurrentStyle()

    @property
    def CurrentFontSize(self):
        """Font size at the current insertion point.  (str)"""
        ds = self.GetDefaultStyle()
        # Default to the current font face for the control
        ret = self.FontSize
        if ds.HasFont():
            ret = ds.GetFont().GetPointSize()
        return ret

    @property
    def CurrentFontUnderline(self):
        """Font underline status at the current insertion point.  (str)"""
        return "Underline" in self._getCurrentStyle()

    @property
    def CurrentStyle(self):
        """
        Returns the style in effect at the current insertion point. In other words, it is the style
        that will be applied to text that is typed at that position. Returns a tuple containing one
        or more of 'Plain', 'Bold', 'Italic', 'Underline'.  (read-only) (tuple)
        """
        ds = self.GetDefaultStyle()
        out = []
        if ds.HasFont():
            fnt = ds.GetFont()
            if "bold" in fnt.GetWeightString().lower():
                out.append("Bold")
            if "italic" in fnt.GetStyleString().lower():
                out.append("Italic")
            if fnt.GetUnderlined():
                out.append("Underline")
        else:
            if ds.HasFontWeight():
                out.append("Bold")
            if ds.HasFontItalic():
                out.append("Italic")
            if ds.HasFontUnderlined():
                out.append("Underline")
        if not out:
            out = ["Plain"]
        return tuple(out)

    @property
    def InsertionPosition(self):
        """Current position of the insertion point in the control.  (int)"""
        return self.GetInsertionPoint()

    @InsertionPosition.setter
    def InsertionPosition(self, val):
        if self._constructed():
            self.SetInsertionPoint(val)
        else:
            self._properties["InsertionPosition"] = val

    @property
    def ReadOnly(self):
        """Specifies whether or not the text can be edited. (bool)"""
        return not self.IsEditable()

    @ReadOnly.setter
    def ReadOnly(self, val):
        if self._constructed():
            self.SetEditable(not bool(val))
        else:
            self._properties["ReadOnly"] = val

    @property
    def SelectionBackColor(self):
        """Color of the current selection's background.  (RGB 3-tuple)"""
        if not self.HasSelection():
            return None
        rng = self.GetSelectionRange()
        ta = wx.richtext.TextAttrEx()
        st = self.GetStyleForRange(rng, ta)
        return ta.BackgroundColour[:3]

    @SelectionBackColor.setter
    def SelectionBackColor(self, val):
        if self._constructed():
            try:
                wxc = wx.Colour(*val)
            except TypeError:
                ct = color_tools.colorTupleFromName(val)
                wxc = wx.Colour(*ct)
            rng = self.GetSelectionRange()
            ta = wx.richtext.TextAttrEx()
            ta.SetFlags(wx.richtext.TEXT_ATTR_BACKGROUND_COLOUR)
            ta.SetBackgroundColour(wxc)
            self.SetStyleEx(rng, ta)
        else:
            self._properties["SelectionBackColor"] = val

    @property
    def SelectionEnd(self):
        """
        Returns the end position of the current text selection, or None if no text
        is selected. (int)
        """
        ret = self._getSelectionRange()[1]
        if ret is None:
            ret = self._getInsertionPosition()
        return ret

    @SelectionEnd.setter
    def SelectionEnd(self, val):
        if self._constructed():
            self._setSelectionRange((self._getSelectionStart(), val))
        else:
            self._properties["SelectionEnd"] = val

    @property
    def SelectionFontBold(self):
        """
        Reflects the Bold status of the current selection. This will be True if every character in
        the selection is bold; if even one character is not bold, this will be False. If there is no
        selection, this will be None. Setting this affects all selected text; it has no effect if no
        text is selected  (bool)
        """
        if self.HasSelection():
            return self.IsSelectionBold()
        else:
            return None

    @SelectionFontBold.setter
    def SelectionFontBold(self, val):
        if self._constructed():
            if not self.HasSelection:
                return
            if val:
                while not self.IsSelectionBold():
                    self.ApplyBoldToSelection()
            else:
                self.ApplyBoldToSelection()
                while self.IsSelectionBold():
                    self.ApplyBoldToSelection()
        else:
            self._properties["SelectionFontBold"] = val

    @property
    def SelectionFontFace(self):
        """
        Reflects the FontFace status of the current selection. If multiple faces are used throughout
        the selection, the face at the beginning of the selection will be returned. If there is no
        selection, None will be returned. Setting this affects all selected text; it has no effect
        if no text is selected  (str)
        """
        if not self.HasSelection():
            return None
        rng = self.GetSelectionRange()
        ta = wx.richtext.TextAttrEx()
        st = self.GetStyleForRange(rng, ta)
        fnt = ta.Font
        return fnt.FaceName

    @SelectionFontFace.setter
    def SelectionFontFace(self, val):
        if self._constructed():
            rng = self.GetSelectionRange()
            ta = wx.richtext.TextAttrEx()
            ta.SetFontFaceName(val)
            ta.SetFlags(wx.richtext.TEXT_ATTR_FONT_FACE)
            self.SetStyleEx(rng, ta)
        else:
            self._properties["SelectionFontFace"] = val

    @property
    def SelectionFontItalic(self):
        """
        Reflects the Italic status of the current selection. This will be True if every character in
        the selection is italic; if even one character is not italic, this will be False. If there
        is no selection, this will be None. Setting this affects all selected text; it has no effect
        if no text is selected  (bool)
        """
        if self.HasSelection():
            return self.IsSelectionItalics()
        else:
            return None

    @SelectionFontItalic.setter
    def SelectionFontItalic(self, val):
        if self._constructed():
            if not self.HasSelection:
                return
            if val:
                while not self.IsSelectionItalics():
                    self.ApplyItalicToSelection()
            else:
                self.ApplyItalicToSelection()
                while self.IsSelectionItalics():
                    self.ApplyItalicToSelection()
        else:
            self._properties["SelectionFontItalic"] = val

    @property
    def SelectionFontSize(self):
        """
        Reflects the FontSize status of the current selection. If multiple sizes are used throughout
        the selection, the size at the beginning of the selection will be returned. If there is no
        selection, None will be returned. Setting this affects all selected text; it has no effect
        if no text is selected  (int)
        """
        if not self.HasSelection():
            return None
        rng = self.GetSelectionRange()
        ta = wx.richtext.TextAttrEx()
        st = self.GetStyleForRange(rng, ta)
        fnt = ta.Font
        return fnt.GetPointSize()

    @SelectionFontSize.setter
    def SelectionFontSize(self, val):
        if self._constructed():
            rng = self.GetSelectionRange()
            ta = wx.richtext.TextAttrEx()
            ta.SetFontSize(val)
            ta.SetFlags(wx.richtext.TEXT_ATTR_FONT_SIZE)
            self.SetStyleEx(rng, ta)
        else:
            self._properties["SelectionFontSize"] = val

    @property
    def SelectionFontUnderline(self):
        """
        Reflects the Underline status of the current selection. This will be True if every character
        in the selection is underlined; if even one character is not underlined, this will be False.
        If there is no selection, this will be None. Setting this affects all selected text; it has
        no effect if no text is selected  (bool)
        """
        if self.HasSelection():
            return self.IsSelectionUnderlined()
        else:
            return None

    @SelectionFontUnderline.setter
    def SelectionFontUnderline(self, val):
        if self._constructed():
            if not self.HasSelection:
                return
            if val:
                while not self.IsSelectionUnderlined():
                    self.ApplyUnderlineToSelection()
            else:
                self.ApplyUnderlineToSelection()
                while self.IsSelectionUnderlined():
                    self.ApplyUnderlineToSelection()
        else:
            self._properties["SelectionFontUnderline"] = val

    @property
    def SelectionForeColor(self):
        """Color of the current selection's text.  (RGB 3-tuple)"""
        if not self.HasSelection():
            return None
        rng = self.GetSelectionRange()
        ta = wx.richtext.TextAttrEx()
        st = self.GetStyleForRange(rng, ta)
        return ta.TextColour[:3]

    @SelectionForeColor.setter
    def SelectionForeColor(self, val):
        if self._constructed():
            try:
                wxc = wx.Colour(*val)
            except TypeError:
                ct = color_tools.colorTupleFromName(val)
                wxc = wx.Colour(*ct)
            rng = self.GetSelectionRange()
            ta = wx.richtext.TextAttrEx()
            ta.SetFlags(wx.richtext.TEXT_ATTR_TEXT_COLOUR)
            ta.SetTextColour(wxc)
            self.SetStyleEx(rng, ta)
        else:
            self._properties["SelectionForeColor"] = val

    @property
    def SelectionPlain(self):
        """
        Reflects the Plain status of the current selection. This will be True if every character in
        the selection is neither bold, italic or underlined. If there is no selection, this will be
        None. Setting this affects all selected text; it has no effect if no text is selected
        (bool)
        """
        sel = self.GetSelectionRange()
        return self.HasCharacterAttributes(sel, self._styleObj)

    @SelectionPlain.setter
    def SelectionPlain(self, val):
        if self._constructed():
            self.SelectionFontBold = self.SelectionFontItalic = self.SelectionFontUnderline = False
        else:
            self._properties["SelectionPlain"] = val

    @property
    def SelectionRange(self):
        """
        Returns/sets the position of the current selected text. No selection is represented by
        (None, None). You can also unselect all text by setting this property to None.
        (2-tuple of int or None)
        """
        selFrom, selTo = self.GetSelectionRange()
        if (selFrom < 0) and (selTo < 0):
            return (None, None)
        else:
            return (selFrom, selTo)

    @SelectionRange.setter
    def SelectionRange(self, val):
        if self._constructed():
            if (val is None) or (None in val):
                self.SelectNone()
            else:
                self.SetSelection(*val)
        else:
            self._properties["SelectionRange"] = val

    @property
    def SelectionStart(self):
        """
        Returns the beginning position of the current text selection, or None if no text is
        selected. (int)
        """
        ret = self._getSelectionRange()[0]
        if ret is None:
            ret = self._getInsertionPosition()
        return ret

    @SelectionStart.setter
    def SelectionStart(self, val):
        if self._constructed():
            self._setSelectionRange((val, self._getSelectionEnd()))
        else:
            self._properties["SelectionStart"] = val


ui.dRichTextBox = dRichTextBox


class RichTextTestForm(dForm):
    def initProperties(self):
        self.ShowToolBar = True
        self.Caption = "Rich Text Control"

    def afterInitAll(self):
        self.textControl = dRichTextBox(self)
        self.textControl.Value = self.getDummyText()
        self.Sizer.append1x(self.textControl)
        self._currentDefaultStyle = None
        iconPath = "themes/tango/32x32/actions"
        self.tbbBold = self.appendToolBarButton(
            "Bold",
            pic="%s/format-text-bold" % iconPath,
            toggle=True,
            help="Toggle the Bold style of the selected text",
            tip="Bold",
            OnHit=self.toggleStyle,
        )
        self.tbbItalic = self.appendToolBarButton(
            "Italic",
            pic="%s/format-text-italic" % iconPath,
            toggle=True,
            help="Toggle the Italic style of the selected text",
            tip="Italic",
            OnHit=self.toggleStyle,
        )
        self.tbbUnderline = self.appendToolBarButton(
            "Underline",
            pic="%s/format-text-underline" % iconPath,
            toggle=True,
            help="Toggle the Underline style of the selected text",
            tip="Underline",
            OnHit=self.toggleStyle,
        )
        tb = self.ToolBar
        allfonts = ui.getAvailableFonts()
        # This is necessary because wx reports the font in some cases as 'applicationfont'.
        allfonts.append("applicationfont")
        allfonts.sort()
        self.tbFontFace = dDropdownList(
            tb,
            Caption="FontFace",
            ValueMode="String",
            OnHit=self.onSetFontFace,
            Choices=allfonts,
        )
        tb.appendControl(self.tbFontFace)
        self.tbFontSize = dDropdownList(
            tb, Caption="FontSize", ValueMode="String", OnHit=self.onSetFontSize
        )
        self.tbFontSize.Choices = [ustr(i) for i in range(6, 129)]
        tb.appendControl(self.tbFontSize)

        self.tbBackColor = dToggleButton(
            tb,
            Caption="BackColor",
            FontSize=8,
            Size=(54, 32),
            OnHit=self.onSetBackColor,
            BezelWidth=0,
            Value=True,
        )
        tb.appendControl(self.tbBackColor)
        self.tbForeColor = dToggleButton(
            tb,
            Caption="ForeColor",
            FontSize=8,
            Size=(54, 32),
            OnHit=self.onSetForeColor,
            BezelWidth=0,
            Value=True,
        )
        tb.appendControl(self.tbForeColor)
        self.openButton = dButton(tb, Caption="Open", OnHit=self.onOpen)
        tb.appendControl(self.openButton)
        self.saveButton = dButton(tb, Caption="Save", OnHit=self.onSave)
        tb.appendControl(self.saveButton)
        self.styleTimer = dTimer(self, Interval=500, Enabled=True, OnHit=self.checkForUpdate)

        # For development: uncomment the next line, and add the code you want to
        # run to the onTest() method.

    #         btn = tb.appendControl(dButton(tb, Caption="TEST", OnHit=self.onTest))

    def onTest(self, evt):
        pass

    def onOpen(self, evt):
        self.textControl.load()

    def onSave(self, evt):
        self.textControl.save()

    def onSetFontSize(self, evt):
        if self.textControl.SelectionRange == (None, None):
            # No selection; revert the dropdown value
            self.updateSelection()
            return
        self.textControl.SelectionFontSize = int(evt.EventObject.Value)

    def onSetFontFace(self, evt):
        if self.textControl.SelectionRange == (None, None):
            # No selection; revert the dropdown value
            self.updateSelection()
            return
        self.textControl.SelectionFontFace = evt.EventObject.Value

    def onSetBackColor(self, evt):
        self.tbBackColor.Value = True
        curr = self.textControl.SelectionBackColor
        if curr is None:
            # Nothing selected
            return
        newcolor = ui.getColor(curr)
        if newcolor:
            self.textControl.SelectionBackColor = newcolor

    def onSetForeColor(self, evt):
        self.tbForeColor.Value = True
        curr = self.textControl.SelectionForeColor
        if curr is None:
            # Nothing selected
            return
        newcolor = ui.getColor(curr)
        if newcolor:
            self.textControl.SelectionForeColor = newcolor

    def toggleStyle(self, evt):
        obj = evt.EventObject
        tx = self.textControl
        cap = obj.Caption
        if cap == "Bold":
            tx.SelectionFontBold = not tx.SelectionFontBold
        elif cap == "Italic":
            tx.SelectionFontItalic = not tx.SelectionFontItalic
        elif cap == "Underline":
            tx.SelectionFontUnderline = not tx.SelectionFontUnderline

    def getCurrentStyle(self):
        tx = self.textControl
        bc = tx.CurrentBackColor
        fc = tx.CurrentForeColor
        cff = tx.CurrentFontFace
        cfs = tx.CurrentFontSize
        cfb = tx.CurrentFontBold
        cfi = tx.CurrentFontItalic
        cfu = tx.CurrentFontUnderline
        return (cff, cfs, cfb, cfi, cfu, bc, fc)

    def checkForUpdate(self, evt):
        style = self.getCurrentStyle()
        if style != self._currentDefaultStyle:
            self._currentDefaultStyle = style
            self.updateSelection(style)

    def updateSelection(self, style=None):
        if style is None:
            style = self.getCurrentStyle()
        cff, cfs, cfb, cfi, cfu, bc, fc = style
        self.tbFontFace.Value = cff
        self.tbFontSize.Value = ustr(cfs)
        self.tbbBold.Value = cfb
        self.tbbItalic.Value = cfi
        self.tbbUnderline.Value = cfu
        self.tbBackColor.BackColor = bc
        self.tbForeColor.BackColor = fc

    def getDummyText(self):
        return """Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula
eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur
ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat
massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo,
rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium. Integer
tincidunt. Cras dapibus. Vivamus elementum semper nisi.

Aenean vulputate eleifend tellus. Aenean leo ligula, porttitor eu, consequat vitae, eleifend ac,
enim. Aliquam lorem ante, dapibus in, viverra quis, feugiat a, tellus. Phasellus viverra nulla ut
metus varius laoreet. Quisque rutrum. Aenean imperdiet. Etiam ultricies nisi vel augue. Curabitur
ullamcorper ultricies nisi. Nam eget ui. Etiam rhoncus. Maecenas tempus, tellus eget condimentum
rhoncus, sem quam semper libero, sit amet adipiscing sem neque sed ipsum. Nam quam nunc, blandit
vel, luctus pulvinar, hendrerit id, lorem. Maecenas nec odio et ante tincidunt tempus.

Donec vitae sapien ut libero venenatis faucibus. Nullam quis ante. Etiam sit amet orci eget eros
faucibus tincidunt. Duis leo. Sed fringilla mauris sit amet nibh. Donec sodales sagittis magna. Sed
consequat, leo eget bibendum sodales, augue velit cursus nunc.
"""


if __name__ == "__main__":
    from ..application import dApp

    app = dApp(MainFormClass=RichTextTestForm)
    app.start()
