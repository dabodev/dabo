# -*- coding: utf-8 -*-
import wx
import wx.lib.agw.foldpanelbar as fpb

from .. import dColors, events, settings, ui
from ..dLocalize import _
from . import dCheckBox, dControlMixin, dForm, dGridSizer, dLabel, dSizer, makeDynamicProperty

dabo_module = settings.get_dabo_package()


class dSlidePanel(dControlMixin, fpb.FoldPanelItem):
    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dSlidePanel
        preClass = fpb.FoldPanelItem
        self._widthAlreadySet = self._heightAlreadySet = True
        self._border = 5

        # This needs to be set *after* the panel is added to its parent
        collapsed = self._extractKey(attProperties, "Collapsed", None)
        if collapsed is not None:
            collapsed = collapsed == "True"
        else:
            collapsed = self._extractKey((kwargs, properties), "Collapsed", None)
            if collapsed is None:
                # They might have passed it as 'Expanded'
                collapsed = not self._extractKey((kwargs, properties), "Expanded", True)

        cbstyle = self._extractKey((kwargs, properties), "cbstyle", None)
        if cbstyle is None:
            kwargs["cbstyle"] = fpb.CaptionBarStyle()

        if isinstance(parent, fpb.FoldPanelBar):
            # Items have to be added to the internal panel instead
            self._cont = parent
            parent = parent._foldPanel
        else:
            # Must have been created from the parent control
            self._cont = parent.GetParent()

        self._captionForeColor = "black"
        self._barStyles = (
            "Borderless",
            "BorderOnly",
            "FilledBorder",
            "VerticalFill",
            "HorizontalFill",
        )
        self._barStylesLow = (
            "borderless",
            "borderonly",
            "filledborder",
            "verticalfill",
            "horizontalfill",
        )
        self._barStyleConstants = {
            "nostyle": fpb.CAPTIONBAR_NOSTYLE,
            "verticalfill": fpb.CAPTIONBAR_GRADIENT_V,
            "horizontalfill": fpb.CAPTIONBAR_GRADIENT_H,
            "borderless": fpb.CAPTIONBAR_SINGLE,
            "borderonly": fpb.CAPTIONBAR_RECTANGLE,
            "filledborder": fpb.CAPTIONBAR_FILLED_RECTANGLE,
        }

        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

        self._cont.appendPanel(self)
        self._cont.RedisplayFoldPanelItems()
        if collapsed is not None:
            self.Collapsed = collapsed
        # Enable detection of clicks on the caption bar
        self._captionBar.Bind(wx.EVT_LEFT_UP, self.__onWxCaptionClick)
        #         print "CAP BAR BINDING"
        # Set up the sizer
        self._baseSizer = sz = dSizer("v")
        self.SetSizer(sz, True)
        sz.appendSpacer(self.CaptionHeight)

    def GetBestSize(self):
        ret = super(dSlidePanel, self).GetBestSize()
        sibCount = len(self.GetParent().GetChildren())
        prnt = self.GetParent()
        if prnt:
            psz = prnt.GetSize()
            pWd, pHt = psz.GetWidth(), psz.GetHeight()
            capHt = self.CaptionHeight * (sibCount - 1)
            if ret.GetWidth() > pWd:
                ret.SetWidth(pWd)
            if not self.IsExpanded():
                ret.SetHeight(self.CaptionHeight)
            else:
                if self.Parent.Singleton:
                    ret.SetHeight(pHt - capHt)
                else:
                    if ret.GetHeight() > pHt - capHt:
                        ret.SetHeight(pHt - capHt)
        return ret

    def ResizePanel(self):
        """
        The native FoldPanelBar doesn't handle removing items form panels;
        this removes the item from the panel's internal item tracking.
        """
        for itm in self._items:
            if not itm._wnd:
                self._items.remove(itm)
        super(dSlidePanel, self).ResizePanel()

    def Destroy(self):
        self.Parent._panels.remove(self)
        self.Parent.raiseEvent(events.SlidePanelChange)
        super(dSlidePanel, self).Destroy()

    def onChildBorn(self, evt):
        self._cont.lockDisplay()
        ch = evt.child
        self._cont.AddFoldPanelWindow(self, ch)
        self._cont.RefreshPanelsFrom(self)
        self._cont.unlockDisplay()
        ui.callAfterInterval(50, self._cont.sizePanelHeights)

    def appendSeparator(self, color=None):
        """This draws a separator line on the panel"""
        if color is None:
            color = "black"
        self.AddSeparator(self.getWxColour(color))

    def layout(self):
        """Wrap the wx version of the call, if possible."""
        self.Layout()
        try:
            # Call the Dabo version, if present
            self._baseSizer.layout()
        except AttributeError:
            pass
        if self.Application.Platform == "Win":
            self.refresh()

    def _clickedOnIcon(self, evt):
        cb = self._captionBar
        vertical = self.IsVertical()
        if cb._foldIcons:
            pt = evt.GetPosition()
            rect = cb.GetRect()
            drw = rect.GetWidth() - cb._iconWidth - cb._rightIndent
            if (vertical and (pt.x > drw)) or (
                not vertical and (pt.y < (cb._iconHeight + cb._rightIndent))
            ):
                # They clicked the expand/collapse icon
                return True
        return False

    def __onWxCaptionClick(self, evt):
        #         print "WX CAP CLICK"
        if self._clickedOnIcon(evt):
            # Already handled
            return
        self.raiseEvent(events.SlidePanelCaptionClick, evt)

    @property
    def BarColor1(self):
        """Main color for the caption bar  (dColor)"""
        try:
            ret = self._barColor1
        except AttributeError:
            ret = self._barColor1 = self._captionBar.GetCaptionStyle().GetFirstColour().Get()
        return ret

    @BarColor1.setter
    def BarColor1(self, val):
        color = self.getWxColour(val)
        self._barColor1 = val
        style = self._captionBar.GetCaptionStyle()
        style.SetFirstColour(color)
        self._captionBar.SetCaptionStyle(style)

    @property
    def BarColor2(self):
        """Secondary color for the caption bar. Only used in gradients  (dColor)"""
        try:
            ret = self._barColor2
        except AttributeError:
            ret = self._barColor2 = self._captionBar.GetCaptionStyle().GetSecondColour().Get()
        return ret

    @BarColor2.setter
    def BarColor2(self, val):
        color = self.getWxColour(val)
        self._barColor2 = val
        style = self._captionBar.GetCaptionStyle()
        style.SetSecondColour(color)
        self._captionBar.SetCaptionStyle(style)

    @property
    def BarStyle(self):
        """
        Determines how the bar containing the caption for this panel is drawn. (str)

        Can be one of the following:
            Borderless     (no border, just a plain fill color; default)
            BorderOnly     (simple border, no fill color)
            FilledBorder   (combination of the two above)
            VerticalFill   (vertical gradient fill, using the two caption colors)
            HorizontalFill (horizontal gradient fill, using the two caption colors)
        """
        wxbs = self._captionBar.GetCaptionStyle()._captionStyle
        lowerStyle = [k for k, v in list(self._barStyleConstants.items()) if v == wxbs][0]
        return self._barStyles[list(self._barStylesLow).index(lowerStyle)]

    @BarStyle.setter
    def BarStyle(self, val):
        if self._constructed():
            if val.lower().strip() not in self._barStylesLow:
                bs = ", ".join(self._barStyles)
                dabo_module.error(
                    _("Unknown BarStyle passed: %(val)s. BarStyle must be one of: %(bs)s")
                    % locals()
                )
            else:
                self._barStyle = val
                # Apply it
                style = self._captionBar.GetCaptionStyle()
                style.SetCaptionStyle(self._barStyleConstants[val.lower().strip()])
                self._captionBar.SetCaptionStyle(style)
        else:
            self._properties["BarStyle"] = val

    @property
    def Border(self):
        """Border between the contents and edges of the panel. Default=5  (int)"""
        return self._border

    @Border.setter
    def Border(self, val):
        if self._constructed():
            if val == self._border:
                return
            try:
                bs = self._baseSizer
            except AttributeError:
                # Passed in params; base sizer isn't yet present
                ui.callAfter(self._setBorder, val)
                return
            sz = self.Sizer
            self._border = val
            if sz is not None:
                sz.setItemProp(sz, "Border", val)
                self.layout()
        else:
            self._properties["Border"] = val

    @property
    def Caption(self):
        """Caption displayed on the panel bar  (str)"""
        return self._captionBar._caption

    @Caption.setter
    def Caption(self, val):
        if self._constructed():
            self._captionBar._caption = val
            self.refresh()
        else:
            self._properties["Caption"] = val

    @property
    def CaptionForeColor(self):
        """Text color of the caption bar  (str or tuple)"""
        return self._captionForeColor

    @CaptionForeColor.setter
    def CaptionForeColor(self, val):
        self._captionForeColor = val
        style = self._captionBar.GetCaptionStyle()
        style.SetCaptionColour(self.getWxColour(val))
        self._captionBar.SetCaptionStyle(style)

    @property
    def CaptionHeight(self):
        """Height of the caption bar. Read-only  (int)"""
        return self._captionBar.GetSize()[1]

    @property
    def Collapsed(self):
        """Is the panel main area hidden?  (bool)"""
        return not self.IsExpanded()

    @Collapsed.setter
    def Collapsed(self, val):
        if val:
            self._cont.collapse(self)
        else:
            self._cont.expand(self)

    @property
    def Expanded(self):
        """Is the panel main area visible?  (bool)"""
        return self.IsExpanded()

    @Expanded.setter
    def Expanded(self, val):
        if val:
            self._cont.expand(self)
        else:
            self._cont.collapse(self)

    @property
    def Parent(self):
        """Reference to the containing dSlidePanelControl."""
        return self._cont

    @property
    def PanelPosition(self):
        """Position of this panel within the parent container  (int)"""
        try:
            ret = self._cont.Children.index(self)
        except (ValueError, IndexError):
            ret = None
        return ret

    @PanelPosition.setter
    def PanelPosition(self, val):
        if self._constructed():
            if val == self.PanelPosition:
                return
            cnt = self._cont
            if self not in cnt._panels:
                # Not fully constructed yet
                return
            cnt._panels.remove(self)
            cnt._panels.insert(val, self)
            cnt.raiseEvent(events.SlidePanelChange)
        else:
            self._properties["PanelPosition"] = val

    @property
    def Sizer(self):
        """The sizer for the object."""
        sz = self._baseSizer
        try:
            ret = sz.Children[1].GetSizer()
        except (IndexError, AttributeError):
            ret = None
        return ret

    @Sizer.setter
    def Sizer(self, val):
        if self._constructed():
            sz = self._baseSizer
            try:
                userSizer = sz.Children[1].GetSizer()
            except (IndexError, AttributeError):
                userSizer = None
            if userSizer:
                sz.remove(userSizer)
            if val is not None:
                sz.append1x(val, border=self.Border)
            try:
                val.Parent = self
            except AttributeError:
                pass
        else:
            self._properties["Sizer"] = val

    DynamicBarColor1 = makeDynamicProperty(BarColor1)
    DynamicBarColor2 = makeDynamicProperty(BarColor2)
    DynamicBarStyle = makeDynamicProperty(BarStyle)
    DynamicCaption = makeDynamicProperty(Caption)
    DynamicCaptionForeColor = makeDynamicProperty(CaptionForeColor)
    DynamicCollapsed = makeDynamicProperty(Collapsed)
    DynamicExpanded = makeDynamicProperty(Expanded)


class dSlidePanelControl(dControlMixin, fpb.FoldPanelBar):
    """
    Creates a control consisting of several panels that can be
    hidden or revealed by clicking on their 'caption bar'.

    This allows you to collapse each panel down to its caption bar,
    which either remains in place or drops to the bottom.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dSlidePanelControl
        preClass = fpb.FoldPanelBar
        self._singleClick = False
        self._collapseToBottom = False
        self._singleton = False
        self._expandContent = True
        self._styleAttributeVal = None
        # Flag to indicate whether panels are being expanded
        # or collapsed due to internal rules for Singleton format.
        self.__inSingletonProcess = False
        # Flag to track the currently expanded panel in Singleton format.
        self.__openPanel = None
        # Ensures that the control has a minimum size.
        self._minSizerWidth = self._minSizerHeight = 100

        dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

        self._setInitialOpenPanel()
        self.bindEvent(events.SlidePanelChange, self.__onSlidePanelChange)

    def append(self, pnl=None, **kwargs):
        if pnl is None:
            # Make sure that the Caption property has been passed
            if not "Caption" in kwargs:
                raise ValueError(_("You must specify a Caption when adding a panel"))
            pnl = dSlidePanel(self, **kwargs)
        elif isinstance(pnl, str):
            # Just the caption; create the panel and use that
            pnl = dSlidePanel(self, Caption=pnl, **kwargs)
        return pnl

    def appendPanel(self, pnl):
        # Panel is being instantiated and added as part of its __init__().
        pos = 0
        if len(self._panels) > 0:
            pos = self._panels[-1].GetItemPos() + self._panels[-1].GetPanelLength()
        pnl.Reposition(pos)
        self._panels.append(pnl)
        self.raiseEvent(events.SlidePanelChange, self._createCapBarEvt(pnl))
        pnl.bindEvent(events.SlidePanelCaptionClick, self.__onSlidePanelCaptionClick, pnl)
        #         print "PANEL CAP CLICK BOUND"
        return pnl

    def __onSlidePanelCaptionClick(self, evt):
        #         print "DABO CAPCLK", self.SingleClick
        if self.SingleClick:
            obj = evt.EventObject
            obj.Expanded = not obj.Expanded

    def _createCapBarEvt(self, pnl):
        evt = fpb.CaptionBarEvent(fpb.wxEVT_CAPTIONBAR)
        cap = pnl._captionBar
        evt.SetId(cap.GetId())
        evt.SetEventObject(cap)
        evt.SetBar(cap)
        return evt

    def Collapse(self, pnl):
        if pnl.Collapsed:
            # nothing to do here
            return
        super(dSlidePanelControl, self).Collapse(pnl)
        self.raiseEvent(events.SlidePanelChange, self._createCapBarEvt(pnl))

    def Expand(self, pnl):
        if pnl.Expanded:
            # nothing to do here
            return
        super(dSlidePanelControl, self).Expand(pnl)
        self.raiseEvent(events.SlidePanelChange, self._createCapBarEvt(pnl))

    # Throw in Dabo-style wrapper names
    expand = Expand
    collapse = Collapse

    def collapseAll(self):
        for pnl in self._panels:
            pnl.Collapsed = True

    def expandAll(self):
        for pnl in self._panels:
            pnl.Expanded = True

    def refresh(self):
        super(dSlidePanelControl, self).refresh()
        if self.CollapseToBottom:
            rect = self.RepositionCollapsedToBottom()
            vertical = self.IsVertical()
            if vertical and rect.GetHeight() > 0 or not vertical and rect.GetWidth() > 0:
                self.RefreshRect(rect)

    def layout(self):
        """Wrap the wx version of the call, if possible."""
        if not self:
            # The object may have already been released.
            return
        self.SetMinSize((self.MinSizerWidth, self.MinSizerHeight))
        for kid in self.Children:
            kid.SetMinSize((self.MinSizerWidth, self.MinSizerHeight))
        self.Layout()

    def onResize(self, evt):
        self.sizePanelHeights()

    @classmethod
    def getBasePanelClass(cls):
        return dSlidePanel

    def _setInitialOpenPanel(self):
        """
        When self.Singleton is true, ensures that one panel is
        open.
        """
        if not self.Singleton:
            return
        # Make sure that one panel is open. If not, open the first.
        # If there is more than one panel open, close all but the
        # first open panel.
        if len(self._panels) == 0:
            return
        self.__inSingletonProcess = True
        found = False
        for pnl in self._panels:
            if pnl.Expanded:
                if found:
                    pnl.Expanded = False
                else:
                    self.__openPanel = pnl
                    found = True
        if not found:
            self._panels[0].Expanded = True
            self.__openPanel = self._panels[0]
        self.__inSingletonProcess = False

    def __onSlidePanelChange(self, evt):
        """
        This ensures that one and only one panel remains expanded
        when the control is in Singleton mode.
        """
        if not self.Singleton:
            self.sizePanelHeights(force=True)
            return
        if self.__inSingletonProcess:
            # The panel is changing due to this method, so ignore
            # it to avoid infinite loops.
            return
        self.__inSingletonProcess = True
        # This is in response to an external request to a panel
        # being expanded or collapsed.
        curr = self.__openPanel
        try:
            evtPanel = evt.panel
        except AttributeError:
            # Not fully built yet; ignore
            return
        isOpening = evt.expanded
        changing = curr is not evtPanel
        if isOpening:
            if curr is not None:
                if curr is not evtPanel:
                    # Close the current one
                    ui.callAfter(self.collapse, curr)
            self.__openPanel = evtPanel
        else:
            # The panel is closing. If it was the current panel,
            # keep it open.
            if curr is None:
                # This is the first panel being added; keep it open
                self.expand(evtPanel)
                self.__openPanel = evtPanel
            elif curr is evtPanel:
                self.expand(curr)
        if changing:
            self.layout()
            ui.callAfter(self.sizePanelHeights)
            self.refresh()
        self.__inSingletonProcess = False

    def sizePanelHeights(self, force=False):
        """
        Control the heights of the panels. Originally I thought we only needed
        this when running in Singleton mode, but now it seems better to run this
        in all modes.
        """
        # -         if not self.Singleton and not force:
        # -             return
        # Size the open panel to fill the space
        top = 0
        pnlList = self._panels[:]
        if not pnlList:
            # Not constructed fully
            return
        if self.CollapseToBottom:
            # Sort so that the first panel is the expanded one.
            pnlList.sort(key=lambda x: x.Collapsed)
        fp = pnlList[0]
        fp.Reposition(0)
        self.RefreshPanelsFrom(fp)
        for pnl in pnlList:
            if not pnl.Expanded:
                pnl.Height = pnl.CaptionHeight
            elif self.ExpandContent:
                # Make the panel that big, minus the height of the captions
                capHt = pnl.CaptionHeight * (len(self._panels) - 1)
                pnl.Height = self.Height - capHt
            pnl.Top = top
            pnl.layout()
            top += pnl.Height
        ui.callAfter(self.layout)

    def _setUnderlyingStyleAtt(self):
        try:
            # See if we use the original attribute name
            self._extraStyle
            self._styleAttributeVal = "_extraStyle"
        except AttributeError:
            # Newer versions use a different attribute name
            self._styleAttributeVal = "_agwStyle"

    def _getChildren(self):
        return self._panels

    def _getCollapseToBottom(self):
        return bool(self._StyleAttribute & fpb.FPB_COLLAPSE_TO_BOTTOM)

    def _setCollapseToBottom(self, val):
        self._collapseToBottom = val
        if val:
            newStyle = self._StyleAttribute | fpb.FPB_COLLAPSE_TO_BOTTOM
        else:
            newStyle = self._StyleAttribute & ~fpb.FPB_COLLAPSE_TO_BOTTOM
        self._StyleAttribute = newStyle
        if self._panels:
            fp = self._panels[0]
            fp.Reposition(0)
            self.RefreshPanelsFrom(fp)
            self.sizePanelHeights(force=True)
            self.layout()

    def _getExpandContent(self):
        return self._expandContent

    def _setExpandContent(self, val):
        if self._constructed():
            self._expandContent = val
        else:
            self._properties["ExpandContent"] = val

    def _getMinSizerHeight(self):
        return self._minSizerHeight

    def _setMinSizerHeight(self, val):
        if self._constructed():
            self._minSizerHeight = val
        else:
            self._properties["MinSizerHeight"] = val

    def _getMinSizerWidth(self):
        return self._minSizerWidth

    def _setMinSizerWidth(self, val):
        if self._constructed():
            self._minSizerWidth = val
        else:
            self._properties["MinSizerWidth"] = val

    def _getPanelClass(self):
        try:
            return self._panelClass
        except AttributeError:
            return dSlidePanel

    def _setPanelClass(self, val):
        if self._constructed():
            self._panelClass = val
        else:
            self._properties["PanelClass"] = val

    def _getPanelCount(self):
        return len(self.Children)

    def _setPanelCount(self, val):
        if self._constructed():
            val = int(val)
            if val < 0:
                raise ValueError(_("Cannot set PanelCount to less than zero."))
            panelCount = len(self.Children)
            panelClass = self.PanelClass

            if val > panelCount:
                for i in range(panelCount, val):
                    pnl = panelClass(self)
                    if not pnl.Caption:
                        pnl.Caption = _("Panel %s") % (i + 1,)
            elif val < panelCount:
                for i in range(panelCount, val, -1):
                    self.Panels[i - 1].release()
        else:
            self._properties["PanelCount"] = val

    def _getSingleClick(self):
        return self._singleClick

    def _setSingleClick(self, val):
        self._singleClick = val

    def _getSingleton(self):
        return self._singleton

    def _setSingleton(self, val):
        self._singleton = val
        # Make sure that only one panel is open
        self._setInitialOpenPanel()

    def _getStyleAttribute(self):
        try:
            return getattr(self, self._styleAttributeVal)
        except TypeError:
            self._setUnderlyingStyleAtt()
            return getattr(self, self._styleAttributeVal)

    def _setStyleAttribute(self, val):
        if self._constructed():
            try:
                setattr(self, self._styleAttributeVal, val)
            except TypeError:
                self._setUnderlyingStyleAtt()
                setattr(self, self._styleAttributeVal, val)
        else:
            self._properties["StyleAttribute"] = val

    Children = property(_getChildren, None, None, _("List of all panels in the control  (list))"))

    CollapseToBottom = property(
        _getCollapseToBottom,
        _setCollapseToBottom,
        None,
        _("When True, all collapsed panels are displayed at the bottom  (bool)"),
    )

    ExpandContent = property(
        _getExpandContent,
        _setExpandContent,
        None,
        _(
            """When True, the panels size themselves to the size of this object.
            Otherwise, panels only take up as much space as they need. (default=True) (bool)"""
        ),
    )

    MinSizerHeight = property(
        _getMinSizerHeight,
        _setMinSizerHeight,
        None,
        _("Minimum height for the control. Default=100px  (int)"),
    )

    MinSizerWidth = property(
        _getMinSizerWidth,
        _setMinSizerWidth,
        None,
        _("Minimum width for the control. Default=100px  (int)"),
    )

    PanelClass = property(
        _getPanelClass,
        _setPanelClass,
        None,
        _(
            """Specifies the class of control to use for panels by default. (dSlidePanel)
            This really only applies when using the PanelCount property to set the
            number of panels."""
        ),
    )

    PanelCount = property(
        _getPanelCount,
        _setPanelCount,
        None,
        _("Number of child panels.  (read-only) (int)"),
    )

    Panels = property(
        _getChildren,
        None,
        None,
        _("List of contained panels. Same as the 'Children' property.  (read-only) (list)"),
    )

    SingleClick = property(
        _getSingleClick,
        _setSingleClick,
        None,
        _(
            """When True, a single click on the caption bar toggles the
            expanded/collapsed state  (bool)"""
        ),
    )

    Singleton = property(
        _getSingleton,
        _setSingleton,
        None,
        _("When True, one and only one panel at a time will be expanded  (bool)"),
    )

    _StyleAttribute = property(
        _getStyleAttribute,
        _setStyleAttribute,
        None,
        _(
            """FOR INTERNAL USE ONLY! Internally the code for foldpanelbar changed
            the name of a 'private' attribute that the Dabo wrapper needs to address.
            This property handles the interaction with that private attribute.  (str)"""
        ),
    )

    DynamicCollapseToBottom = makeDynamicProperty(CollapseToBottom)
    DynamicSingleClick = makeDynamicProperty(SingleClick)
    DynamicSingleton = makeDynamicProperty(Singleton)


ui.dSlidePanel = dSlidePanel
ui.dSlidePanelControl = dSlidePanelControl


if __name__ == "__main__":
    from ..application import dApp

    class TestForm(dForm):
        def afterInit(self):
            dSlidePanelControl(self, RegID="slideControl", ExpandContent=False, SingleClick=True)
            self.Sizer.append1x(self.slideControl)
            self.p1 = dSlidePanel(self.slideControl, Caption="First", BackColor="orange")
            self.p2 = dSlidePanel(
                self.slideControl,
                Caption="Second",
                BarStyle="HorizontalFill",
                BarColor1="lightgreen",
                BarColor2="ForestGreen",
                BackColor="wheat",
            )
            self.p3 = dSlidePanel(
                self.slideControl,
                Caption="Third",
                BarStyle="BorderOnly",
                BackColor="powderblue",
                Border=33,
            )

            self.p1.Sizer = dSizer("v")
            btn = dButton(self.p1, Caption="Change Bar 1 Style")
            self.p1.Sizer.append(btn, border=25)
            btn.bindEvent(events.Hit, self.onBtn)

            self.p2.Sizer = dSizer("v")
            lbl = dLabel(self.p2, Caption="Tea For Two", FontItalic=True, FontSize=24)
            self.p2.Sizer.append(lbl)

            def collapse3(evt):
                mc = self.slideControl
                if mc.Singleton:
                    mc.expand(self.p2)
                else:
                    mc.collapse(self.p3)

            self.p3.Sizer = dGridSizer(HGap=5, VGap=2, MaxCols=2, DefaultBorder=3)
            lbl = dLabel(self.p3, Caption="Three Strikes")
            btn = dButton(self.p3, Caption="Collapse Me", OnHit=collapse3)
            self.p3.Sizer.appendItems((lbl, btn))
            # Demonstrate the grid
            self.p3.Sizer.append(dLabel(self.p3, Caption="Just"))
            self.p3.Sizer.append(dLabel(self.p3, Caption="taking"))
            self.p3.Sizer.append(dLabel(self.p3, Caption="up"))
            self.p3.Sizer.append(dLabel(self.p3, Caption="space"))
            self.p3.Sizer.append(dLabel(self.p3, Caption="in"))
            self.p3.Sizer.append(dLabel(self.p3, Caption="the"))
            self.p3.Sizer.append(dLabel(self.p3, Caption="Grid"))
            self.p3.Sizer.append(dLabel(self.p3, Caption="Sizer"))

            hsz = dSizer("h")
            btnCollapse = dButton(self, Caption="Collapse All")
            btnCollapse.bindEvent(events.Hit, self.onCollapseAll)
            btnExpand = dButton(self, Caption="Expand All")
            btnExpand.bindEvent(events.Hit, self.onExpandAll)
            hsz.append(btnCollapse)
            hsz.appendSpacer(10)
            hsz.append(btnExpand)
            hsz.appendSpacer(10)
            chkSingleton = dCheckBox(
                self,
                Caption="Singleton Style",
                DataSource="self.Form.slideControl",
                DataField="Singleton",
            )
            chkSingle = dCheckBox(
                self,
                Caption="Single Click to Toggle",
                DataSource="self.Form.slideControl",
                DataField="SingleClick",
            )
            chkBottom = dCheckBox(
                self,
                Caption="Collapsed Panels To Bottom",
                DataSource="self.Form.slideControl",
                DataField="CollapseToBottom",
            )
            chkExpand = dCheckBox(
                self,
                Caption="Expand Content to Full Size",
                DataSource="self.Form.slideControl",
                DataField="ExpandContent",
            )
            self.Sizer.appendSpacer(10)
            vsz = dSizer("v")
            vsz.append(chkSingleton)
            vsz.append(chkSingle)
            vsz.append(chkBottom)
            vsz.append(chkExpand)
            hsz.append(vsz)
            self.Sizer.append(hsz, 0, halign="center", border=10)
            self.layout()

        def onBtn(self, evt):
            import random

            p = self.p1
            style = random.choice(p._barStyles)
            p.BarStyle = style
            color1 = dColors.randomColorName()
            color2 = dColors.randomColorName()
            p.BarColor1 = color1
            p.BarColor2 = color2
            if style in ("VerticalFill", "HorizontalFill"):
                p.Caption = "Style: %s; Colors: %s, %s" % (style, color1, color2)
            elif style in ("BorderOnly",):
                p.Caption = "Style: %s" % style
            else:
                p.Caption = "Style: %s; Color: %s" % (style, color1)

        #             lbl = dLabel(p, Caption="Changed to %s" % p.BarStyle,
        #                     FontItalic=True, FontSize=12)
        #             p.Sizer.append(lbl)
        #             p.layout()

        def onCollapseAll(self, evt):
            self.slideControl.collapseAll()

        def onExpandAll(self, evt):
            self.slideControl.expandAll()

    app = dApp()
    app.MainFormClass = TestForm
    app.start()
