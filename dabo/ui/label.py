# -*- coding: utf-8 -*-
import wx

from .. import events
from .. import ui
from ..lib.utils import get_super_property_value
from ..lib.utils import set_super_property_value
from ..localization import _
from . import AlignmentMixin
from . import dCheckBox
from . import dControlMixin
from . import dPanel
from . import dSizer
from . import makeDynamicProperty


class dLabel(dControlMixin, AlignmentMixin, wx.StaticText):
    """Creates a static label, to make a caption for another control, for example."""

    _layout_on_set_caption = True

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dLabel
        self._wordWrap = False
        self._inResizeEvent = False
        self._resetAutoResize = True
        preClass = wx.StaticText
        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )
        self.bindEvent(events.Resize, self.__onResize)

    def __onResize(self, evt):
        """
        Event binding is set when WordWrap=True. Tell the label
        to wrap to its current width.
        """
        if self.WordWrap:
            if self._inResizeEvent:
                return
            self._inResizeEvent = True
            ui.callAfterInterval(101, self.__resizeExecute)

    def __resizeExecute(self):
        # We need to set the caption to the internally-saved caption, since
        # WordWrap can introduce additional linefeeds.
        try:
            self.Parent.lockDisplay()
        except RuntimeError:
            # Form is being destroyed; bail
            return
        self.SetLabel(self._caption)
        wd = {True: self.Width, False: -1}[self.WordWrap]
        self.Wrap(wd)
        ui.callAfterInterval(50, self.__endResize)

    def __endResize(self):
        """
        To prevent infinite loops while resizing, the _inResizeEvent
        flag must be reset outside of the execution method.
        """
        self.Parent.unlockDisplayAll()
        self._inResizeEvent = False

    # property definitions follow:
    @property
    def AutoResize(self):
        """
        Specifies whether the length of the caption determines the size of the label. This cannot be
        True if WordWrap is also set to True. Default=True.  (bool)
        """
        return not self._hasWindowStyleFlag(wx.ST_NO_AUTORESIZE)

    @AutoResize.setter
    def AutoResize(self, val):
        self._delWindowStyleFlag(wx.ST_NO_AUTORESIZE)
        if not val:
            self._addWindowStyleFlag(wx.ST_NO_AUTORESIZE)

    @property
    def FontBold(self):
        """Specifies if the font is bold-faced. (bool)"""
        return get_super_property_value(self, "FontBold")

    @FontBold.setter
    def FontBold(self, val):
        set_super_property_value(self, "FontBold", val)
        if self._constructed():
            # This will force an auto-resize
            self.SetLabel(self.GetLabel())

    @property
    def FontFace(self):
        """Specifies the font face. (str)"""
        return get_super_property_value(self, "FontFace")

    @FontFace.setter
    def FontFace(self, val):
        set_super_property_value(self, "FontFace", val)
        if self._constructed():
            # This will force an auto-resize
            self.SetLabel(self.GetLabel())

    @property
    def FontItalic(self):
        """Specifies whether font is italicized. (bool)"""
        return get_super_property_value(self, "FontItalic")

    @FontItalic.setter
    def FontItalic(self, val):
        set_super_property_value(self, "FontItalic", val)
        if self._constructed():
            # This will force an auto-resize
            self.SetLabel(self.GetLabel())

    @property
    def FontSize(self):
        """Specifies the point size of the font. (int)"""
        return get_super_property_value(self, "FontSize")

    @FontSize.setter
    def FontSize(self, val):
        set_super_property_value(self, "FontSize", val)
        if self._constructed():
            # This will force an auto-resize
            self.SetLabel(self.GetLabel())

    @property
    def WordWrap(self):
        """
        When True, the Caption is wrapped to the Width. Note that the control must have sufficient
        Height to display any wrapped text. Default=False  (bool)
        """
        return self._wordWrap

    @WordWrap.setter
    def WordWrap(self, val):
        if self._constructed():
            changed = self._wordWrap != val
            if not changed:
                return
            self._wordWrap = val
            if val:
                # Make sure AutoResize is False.
                if self.AutoResize:
                    self._resetAutoResize = True
                    self.AutoResize = False
                try:
                    ui.callAfter(self.Parent.layout)
                except AttributeError:
                    # Parent has no layout() method.
                    pass
            else:
                # reset the value
                self.AutoResize = self._resetAutoResize
            self.__resizeExecute()
        else:
            self._properties["WordWrap"] = val

    DynamicFontBold = makeDynamicProperty(FontBold)
    DynamicFontFace = makeDynamicProperty(FontFace)
    DynamicFontItalic = makeDynamicProperty(FontItalic)
    DynamicFontSize = makeDynamicProperty(FontSize)
    DynamicWordWrap = makeDynamicProperty(WordWrap)


ui.dLabel = dLabel


class _dLabel_test(dLabel):
    def initProperties(self):
        self.FontBold = True
        self.Alignment = "Center"
        self.ForeColor = "Red"
        self.Width = 300
        self.Caption = "My God, it's full of stars! " * 22
        self.WordWrap = False


if __name__ == "__main__":
    from ui.dForm import dForm

    from ..application import dApp

    class LabelTestForm(dForm):
        def afterInit(self):
            self.Caption = "dLabel Test"
            pnl = dPanel(self)
            self.Sizer.append1x(pnl)
            sz = pnl.Sizer = dSizer("v")
            sz.appendSpacer(25)
            self.sampleLabel = dLabel(
                pnl, Caption="This label has a very long Caption. " * 20, WordWrap=False
            )
            self.wrapControl = dCheckBox(
                pnl,
                Caption="WordWrap",
                DataSource=self.sampleLabel,
                DataField="WordWrap",
            )
            sz.append(self.wrapControl, halign="center", border=20)
            sz.append1x(self.sampleLabel, border=10)
            self.update()
            ui.callAfterInterval(200, self.layout)

    app = dApp(MainFormClass=LabelTestForm)
    app.start()
