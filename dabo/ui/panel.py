# -*- coding: utf-8 -*-
import wx

from .. import color_tools, events, ui
from ..localization import _
from . import dControlMixin, dDataControlMixin, makeDynamicProperty


class _BasePanelMixin(object):
    def __init__(
        self,
        superclass,
        preClass,
        parent,
        properties=None,
        attProperties=None,
        *args,
        **kwargs,
    ):
        self._minSizerWidth = 10
        self._minSizerHeight = 10
        self._alwaysResetSizer = False
        self._buffered = None
        self._square = False
        buff = self._extractKey(attProperties, "Buffered", None)
        if buff is not None:
            buff = buff == "True"
        else:
            buff = self._extractKey((properties, kwargs), "Buffered", False)
        kwargs["Buffered"] = buff
        style = self._extractKey((properties, kwargs), "style", 0)
        style = style | wx.TAB_TRAVERSAL | wx.CLIP_CHILDREN
        kwargs["style"] = style
        # For performance, store this at init
        self._platformIsWindows = self.Application.Platform == "Win"
        superclass.__init__(
            self,
            preClass=preClass,
            parent=parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

        self._inResizeHandler = False
        self.Bind(wx.EVT_SIZE, self._onWxResize)

    def _onWxResize(self, evt):
        if self._inResizeHandler:
            return
        if not self.Square:
            evt.Skip()
            return
        self._inResizeHandler = True
        minsize = min(evt.GetSize())
        self.SetSize((minsize, minsize))
        self._positionSquareInSizer(evt, minsize)
        # We need to NOT skip the event. Otherwise, resizing gets stuck
        # at the largest size
        # evt.Skip()
        self._inResizeHandler = False

    def _positionSquareInSizer(self, evt, sz):
        """
        When resizing to a square, we have to manually handle alignment if
        this panel is in a sizer and set to expand.
        """
        cs = self.ControllingSizer
        try:
            expand = cs.getItemProp(self, "expand")
        except AttributeError:
            # Not in a sizer
            return
        if not expand:
            return
        ewd, eht = evt.GetSize()
        halign = cs.getItemProp(self, "halign")[0]
        valign = cs.getItemProp(self, "valign")[0]
        orient = cs.Orientation[0]
        if (self.Left + sz) < ewd:
            if halign == "C":
                # Center the square
                self.Left += (ewd - sz) / 2
            elif halign == "R":
                self.Right = self.Left + ewd
        elif (self.Top + sz) < eht:
            if valign == "M":
                self.Top += (eht - sz) / 2
            elif valign == "B":
                self.Bottom = self.Top + eht

    def layout(self, resetMin=False):
        """Wrap the wx version of the call, if possible."""
        if not self:
            return
        if resetMin or self._alwaysResetSizer or self._square:
            # Set the panel's minimum size back to zero. This is sometimes
            # necessary when the items in the panel have reduced in size.
            self.SetMinSize((self.MinSizerWidth, self.MinSizerHeight))
        self.Layout()
        # Sizer's children are the same as self.Children
        if not self.Sizer:
            for child in self.Children:
                try:
                    child.layout()
                except AttributeError:
                    pass
        try:
            # Call the Dabo version, if present
            self.Sizer.layout()
        except AttributeError:
            pass
        if self._platformIsWindows:
            self.refresh()

    def _onPaintBuffer(self, evt):
        # We create it; as soon as 'dc' goes out of scope, the
        # DC is destroyed, which copies its contents to the display
        dc = wx.BufferedPaintDC(self, self._buffer)

    def _onResizeBuffer(self, evt):
        evt.Skip()
        self._buffer = wx.EmptyBitmap(max(1, self.Width), max(1, self.Height))
        self.__updateDrawing()

    def __updateDrawing(self):
        dc = wx.BufferedDC(wx.ClientDC(self), self._buffer)
        dc.Clear()  # make sure you clear the bitmap!
        self._redraw(dc)

    def _onResizeSquare(self, evt):
        smaller = min(self.Size)
        self.SetMinSize((self.MinSizerWidth, self.MinSizerHeight))
        self.Size = (smaller, smaller)

    def _redraw(self, dc=None):
        if self._buffered:
            # Override the base call to provide a buffered DC.
            try:
                self._buffer
            except AttributeError:
                # This is being called way too early; skip this call
                return
            if dc is None:
                dc = wx.BufferedDC(wx.ClientDC(self), self._buffer)
                dc.Clear()  # make sure you clear the bitmap!
        super()._redraw(dc)

    # property definitions follow:
    @property
    def ActiveControl(self):
        """Specifies which control in the panel has the keyboard focus."""
        return getattr(self, "_activeControl", None)

    @ActiveControl.setter
    def ActiveControl(self, obj):
        obj.setFocus()

    @property
    def AlwaysResetSizer(self):
        """
        When True, the sizer settings are always cleared before a layout() is called.
        This may be necessary when a panel needs to reduce its size. Default=False   (bool)
        """
        return self._alwaysResetSizer

    @AlwaysResetSizer.setter
    def AlwaysResetSizer(self, val):
        if self._constructed():
            self._alwaysResetSizer = val
        else:
            self._properties["AlwaysResetSizer"] = val

    @property
    def Buffered(self):
        """Does this panel use double-buffering to create smooth redrawing?  (bool)"""
        return self._buffered

    @Buffered.setter
    def Buffered(self, val):
        if self._buffered == val:
            return
        self._buffered = val
        if val:
            # Set up the double-buffering.
            self._buffer = wx.EmptyBitmap(max(1, self.Width), max(1, self.Height))
            #             self.Bind(wx.EVT_PAINT, self._onPaintBuffer)
            self.Bind(wx.EVT_SIZE, self._onResizeBuffer)
        else:
            #             self.Unbind(wx.EVT_PAINT)
            self.Unbind(wx.EVT_SIZE)

    @property
    def MinSizerHeight(self):
        """Minimum height for the panel. Default=10px  (int)"""
        return self._minSizerHeight

    @MinSizerHeight.setter
    def MinSizerHeight(self, val):
        if self._constructed():
            self._minSizerHeight = val
        else:
            self._properties["MinSizerHeight"] = val

    @property
    def MinSizerWidth(self):
        """Minimum width for the panel. Default=10px  (int)"""
        return self._minSizerWidth

    @MinSizerWidth.setter
    def MinSizerWidth(self, val):
        if self._constructed():
            self._minSizerWidth = val
        else:
            self._properties["MinSizerWidth"] = val

    @property
    def Square(self):
        """When True, the panel will keep all sides the same length. Default=False  (bool)"""
        return self._square

    @Square.setter
    def Square(self, val):
        self._square = val
        if self._constructed():
            self._square = val
            if val:
                self.bindEvent(events.Resize, self._onResizeSquare)
            else:
                self.unbindEvent(events.Resize, self._onResizeSquare)
        else:
            self._properties["Square"] = val


class _PanelMixin(dControlMixin, _BasePanelMixin):
    def __init__(self, preClass, parent, properties=None, attProperties=None, *args, **kwargs):
        _BasePanelMixin.__init__(
            self,
            dControlMixin,
            preClass=preClass,
            parent=parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )


class _DataPanelMixin(dDataControlMixin, _BasePanelMixin):
    def __init__(self, preClass, parent, properties=None, attProperties=None, *args, **kwargs):
        _BasePanelMixin.__init__(
            self,
            dDataControlMixin,
            preClass=preClass,
            parent=parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )


class dPanel(_PanelMixin, wx.Panel):
    """
    Creates a panel, a basic container for controls.

    Panels can contain subpanels to unlimited depth, making them quite
    flexible for many uses. Consider laying out your forms on panels
    instead, and then adding the panel to the form.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dPanel
        preClass = wx.Panel
        _PanelMixin.__init__(
            self,
            preClass=preClass,
            parent=parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )


class dDataPanel(_DataPanelMixin, wx.Panel):
    """
    Creates a panel, a basic container for controls. This panel, unlike the plain
    dPanel class, inherits from the Data Control mixin class, which makes it useful
    building composite controls that have a Value that can be bound like any simple
    control.

    .. note::
        You are responsible for implementing the Value property correctly in
        your subclasses.

    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dDataPanel
        preClass = wx.Panel
        _DataPanelMixin.__init__(
            self,
            preClass=preClass,
            parent=parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )


class dScrollPanel(_PanelMixin, wx.ScrolledWindow):
    """
    This is a basic container for controls that allows scrolling.

    Panels can contain subpanels to unlimited depth, making them quite
    flexible for many uses. Consider laying out your forms on panels
    instead, and then adding the panel to the form.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._horizontalScroll = self._verticalScroll = True
        self._baseClass = dScrollPanel
        preClass = wx.ScrolledWindow
        kwargs["AlwaysResetSizer"] = self._extractKey(
            (properties, kwargs, attProperties), "AlwaysResetSizer", True
        )
        _PanelMixin.__init__(
            self,
            preClass=preClass,
            parent=parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )
        self.SetScrollRate(10, 10)
        self.Bind(wx.EVT_SCROLLWIN, self.__onWxScrollWin)

    def __onWxScrollWin(self, evt):
        evtClass = ui.getScrollWinEventClass(evt)
        self.raiseEvent(evtClass, evt)
        evt.Skip()

    def scrollHorizontally(self, amt):
        """Change the horizontal scroll position by 'amt' units."""
        self._scroll(amt, 0)

    def scrollVertically(self, amt):
        """Change the vertical scroll position by 'amt' units."""
        # Y scrolling is a negative change
        self._scroll(0, -amt)

    def _scroll(self, xOff, yOff):
        x, y = self.GetViewStart()
        self.Scroll(x + xOff, y + yOff)
        ui.callAfterInterval(250, self.layout)

    def pageLeft(self):
        self.pageHorizontally(-1)

    def pageRight(self):
        self.pageHorizontally(1)

    def pageHorizontally(self, direction):
        """Scroll horizontally one 'page' width."""
        sz = self.GetScrollPageSize(wx.HORIZONTAL)
        if sz:
            x, y = self.GetViewStart()
            self.Scroll(x + (direction * sz), y)

    def pageUp(self):
        self.pageVertically(-1)

    def pageDown(self):
        self.pageVertically(1)

    def pageVertically(self, direction):
        """Scroll vertically one 'page' height."""
        sz = self.GetScrollPageSize(wx.VERTICAL)
        if sz:
            x, y = self.GetViewStart()
            self.Scroll(x, y + (direction * sz))

    @property
    def Children(self):
        """Child controls of this panel. Excludes the wx-specific scroll bars  (list of objects)"""
        ret = super().Children
        return [kid for kid in ret if isinstance(kid, ui.dPemMixin)]

    @Children.setter
    def Children(self, val):
        super()._setChildren(val)

    @property
    def HorizontalScroll(self):
        """Controls whether this object will scroll horizontally (default=True)  (bool)"""
        return self._horizontalScroll

    @HorizontalScroll.setter
    def HorizontalScroll(self, val, do=False):
        if do:
            self._horizontalScroll = val
            self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
            rt = self.GetScrollPixelsPerUnit()
            self.SetScrollRate({True: rt[0], False: 0}[val], rt[1])
        else:
            # on Mac at least, this is needed when setting from the constructor.
            ui.callAfter(self._setHorizontalScroll, val, do=True)

    @property
    def VerticalScroll(self):
        """Controls whether this object will scroll vertically (default=True)  (bool)"""
        return self._verticalScroll

    @VerticalScroll.setter
    def VerticalScroll(self, val, do=False):
        if do:
            self._verticalScroll = val
            self.EnableScrolling(self._horizontalScroll, self._verticalScroll)
            rt = self.GetScrollPixelsPerUnit()
            self.SetScrollRate(rt[0], {True: rt[1], False: 0}[val])
        else:
            ui.callAfter(self._setVerticalScroll, val, do=True)

    DynamicHorizontalScroll = makeDynamicProperty(HorizontalScroll)
    DynamicVerticalScroll = makeDynamicProperty(VerticalScroll)


ui.dPanel = dPanel
ui.dDataPanel = dDataPanel
ui.dScrollPanel = dScrollPanel


class _dPanel_test(dPanel):
    def initProperties(self):
        self.BackColor = "wheat"
        self.Hover = True

    def afterInit(self):
        self.addObject(dPanel, BackColor="green")

    def onHover(self, evt):
        self._normBack = self.BackColor
        self.BackColor = color_tools.randomColor()

    def endHover(self, evt):
        self.BackColor = self._normBack

    def onMouseLeftDown(self, evt):
        print("mousedown")

    def onPaint(self, evt):
        print("paint")

    def onKeyDown(self, evt):
        print(evt.EventData["keyCode"])


class _dScrollPanel_test(dScrollPanel):
    def initProperties(self):
        self.BackColor = "wheat"

    def afterInit(self):
        subpan = self.addObject(dPanel, BackColor="green")
        subpan.bindEvent(events.KeyDown, self.onKeyDown)
        self.SetScrollbars(10, 10, 100, 100)

    def onMouseLeftDown(self, evt):
        print("mousedown")
        self.SetFocusIgnoringChildren()

    def onPaint(self, evt):
        print("paint")

    def onKeyDown(self, evt):
        print(evt.EventData["keyCode"])

    def onScrollLineUp(self, evt):
        if evt.orientation == "Horizontal":
            print("Scroll Line Left")
        else:
            print("Scroll Line Up")

    def onScrollLineDown(self, evt):
        if evt.orientation == "Horizontal":
            print("Scroll Line Right")
        else:
            print("Scroll Line Down")

    def onScrollPageUp(self, evt):
        if evt.orientation == "Horizontal":
            print("Scroll Page Left")
        else:
            print("Scroll Page Up")

    def onScrollPageDown(self, evt):
        if evt.orientation == "Horizontal":
            print("Scroll Page Right")
        else:
            print("Scroll Page Down")


if __name__ == "__main__":
    from ..ui import dForm
    from . import test

    class SquarePanel(dPanel):
        def afterInit(self):
            self.Square = True
            self.BackColor = "green"

    class RegularPanel(dPanel):
        def afterInit(self):
            self.Square = False
            self.BackColor = "blue"

    class SquareForm(dForm):
        def afterInit(self):
            self.pnl = SquarePanel(self, Width=100)
            sz = self.Sizer
            sz.appendSpacer(20)
            sz.append(self.pnl, 1, "x", halign="right", valign="bottom", border=5)
            sz.appendSpacer(20)
            self.regPanel = RegularPanel(self, Width=100)
            sz.append1x(self.regPanel, halign="center", border=5)
            sz.appendSpacer(20)
            self.layout()

    #     app = dApp(MainFormClass = SquareForm)
    #     app.start()

    test.Test().runTest(_dPanel_test)
    test.Test().runTest(_dScrollPanel_test)
