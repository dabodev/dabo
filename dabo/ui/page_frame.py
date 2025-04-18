# -*- coding: utf-8 -*-
import random
import sys

import wx

from .. import color_tools
from .. import events
from .. import lib
from .. import settings
from .. import ui
from ..lib.utils import ustr
from ..localization import _
from . import dCheckBox
from . import dDropdownList
from . import dLabel
from . import dPage
from . import dPageFrameMixin
from . import dSizer

dabo_module = settings.get_dabo_package()

_USE_AGW = True
try:
    import wx.lib.agw.aui as aui
except ImportError:
    # wx versions prior to 2.8.9.2
    import wx.aui as aui

    _USE_AGW = False

# The Editra flatnotebook module takes care of the Nav Buttons and Dropdown Tab List
# overlap problem, so we try to import that module first.  If that doesn't
# Why wxPython doesn't fold this flatnotebook module into the main one is beyond me...
try:
    import wx.tools.Editra.src.extern.flatnotebook as fnb

    _USE_EDITRA = True
except ImportError:
    import wx.lib.agw.flatnotebook as fnb

    _USE_EDITRA = False


def readonly(value):
    """Create a read-only property."""
    return property(lambda self: value)


class dPageFrame(dPageFrameMixin, wx.Notebook):
    """
    Creates a pageframe, which can contain an unlimited number of pages,
    each of which should be a subclass/instance of the dPage class.
    """

    _evtPageChanged = readonly(wx.EVT_NOTEBOOK_PAGE_CHANGED)
    _evtPageChanging = readonly(wx.EVT_NOTEBOOK_PAGE_CHANGING)
    _tabposTop = readonly(wx.NB_TOP)
    _tabposBottom = readonly(wx.NB_BOTTOM)
    _tabposRight = readonly(wx.NB_RIGHT)
    _tabposLeft = readonly(wx.NB_LEFT)

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dPageFrame
        preClass = wx.Notebook

        dPageFrameMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def _afterInit(self):
        if sys.platform[:3] == "win":
            ## This keeps Pages from being ugly on Windows:
            self.SetBackgroundColour(self.GetBackgroundColour())
        super()._afterInit()


class dPageToolBar(dPageFrameMixin, wx.Toolbook):
    _evtPageChanged = readonly(wx.EVT_TOOLBOOK_PAGE_CHANGED)
    _evtPageChanging = readonly(wx.EVT_TOOLBOOK_PAGE_CHANGING)
    _tabposTop = readonly(wx.BK_TOP)
    _tabposBottom = readonly(wx.BK_BOTTOM)
    _tabposRight = readonly(wx.BK_RIGHT)
    _tabposLeft = readonly(wx.BK_LEFT)

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dPageToolBar
        preClass = wx.Toolbook

        dPageFrameMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def _afterInit(self):
        if sys.platform[:3] == "win":
            ## This keeps Pages from being ugly on Windows:
            self.SetBackgroundColour(self.GetBackgroundColour())

        il = wx.ImageList(
            32, 32, initialCount=0
        )  # Need to set image list first or else we get and error...
        self.AssignImageList(il)
        super()._afterInit()

    def removePage(self, pgOrPos, delPage=True):
        """
        Removes the specified page. You can specify a page by either
        passing the page itself, or a position. If delPage is True (default),
        the page is released, and None is returned. If delPage is
        False, the page is returned. There is a bug in the wx.Toolbook class
        that breaks the link between the toolbar buttons and their pages
        when a page is removed, so this attempts to work around this.
        """
        pos = pgOrPos
        if isinstance(pgOrPos, int):
            pg = self.Pages[pgOrPos]
        else:
            pg = pgOrPos
            pos = self.Pages.index(pg)
        # Get all the pages after the one to be deleted
        laterPages = self.Pages[pos + 1 :]
        for lpg in laterPages:
            self.RemovePage(pos + 1)
        if delPage:
            self.DeletePage(pos)
            ret = None
        else:
            self.RemovePage(pos)
            ret = pg
        for lpg in laterPages:
            self.appendPage(lpg, caption=lpg.Caption, imgKey=lpg.imgKey)
        return ret


class dPageList(dPageFrameMixin, wx.Listbook):
    _evtPageChanged = readonly(wx.EVT_LISTBOOK_PAGE_CHANGED)
    _evtPageChanging = readonly(wx.EVT_LISTBOOK_PAGE_CHANGING)
    _tabposBottom = readonly(wx.LB_BOTTOM)
    _tabposTop = readonly(wx.LB_TOP)
    _tabposRight = readonly(wx.LB_RIGHT)
    _tabposLeft = readonly(wx.LB_LEFT)

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dPageList
        preClass = wx.Listbook
        # Dictionary for tracking images by key value
        self._imageList = {}
        dPageFrameMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

        self.Bind(wx.EVT_LIST_ITEM_MIDDLE_CLICK, self.__onWxMiddleClick)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.__onWxRightClick)

    def __onWxMiddleClick(self, evt):
        self.raiseEvent(events.MouseMiddleClick, evt)

    def __onWxRightClick(self, evt):
        self.raiseEvent(events.MouseRightClick, evt)

    def layout(self):
        """We need to force the control to adjust the list size."""
        self.GetChildren()[0].InvalidateBestSize()
        self.Layout()

    def SetPageText(self, pos, val):
        super().SetPageText(pos, val)
        # Force the list to re-align the spacing
        self.layout()

    @property
    def ListSpacing(self):
        """Controls the spacing of the items in the controlling list  (int)"""
        return self.GetChildren()[0].GetItemSpacing()[0]

    @ListSpacing.setter
    def ListSpacing(self, val):
        if self._constructed():
            try:
                self.GetChildren()[0].SetItemSpacing(val)
            except AttributeError:
                # Changed this to write to the info log to avoid error messages that
                #  unnecessarily exaggerate the problem.
                dabo_module.info(_("ListSpacing is not supported in wxPython %s") % wx.__version__)
        else:
            self._properties["ListSpacing"] = val


class dPageSelect(dPageFrameMixin, wx.Choicebook):
    _evtPageChanged = readonly(wx.EVT_CHOICEBOOK_PAGE_CHANGED)
    _evtPageChanging = readonly(wx.EVT_CHOICEBOOK_PAGE_CHANGING)
    _tabposTop = readonly(wx.CHB_TOP)
    _tabposBottom = readonly(wx.CHB_BOTTOM)
    _tabposRight = readonly(wx.CHB_RIGHT)
    _tabposLeft = readonly(wx.CHB_LEFT)

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dPageSelect
        preClass = wx.Choicebook
        dPageFrameMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )
        # Dictionary for tracking images by key value
        self._imageList = {}

    def SetPageText(self, pg, tx):
        """
        Need to override this because this is not implemented yet
        on the Mac, at least as of wxPython 2.5.5.1
        """
        # Get a reference to the Choice control
        dd = self.GetChildren()[0]
        # Save the current position
        pos = dd.GetSelection()
        # Get the current contents
        choices = [dd.GetString(n) for n in range(dd.GetCount())]
        choices[pg] = tx
        dd.Clear()
        dd.AppendItems(choices)
        dd.SetSelection(pos)


class dDockTabs(dPageFrameMixin, aui.AuiNotebook):
    _evtPageChanged = readonly(aui.EVT_AUINOTEBOOK_PAGE_CHANGED)
    _evtPageChanging = readonly(aui.EVT_AUINOTEBOOK_PAGE_CHANGING)
    _tabposBottom = readonly(aui.AUI_NB_BOTTOM)
    _tabposRight = readonly(aui.AUI_NB_RIGHT)
    _tabposLeft = readonly(aui.AUI_NB_LEFT)
    _tabposTop = readonly(aui.AUI_NB_TOP)

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dDockTabs
        preClass = aui.AuiNotebook

        newStyle = aui.AUI_NB_TOP | aui.AUI_NB_SCROLL_BUTTONS
        self._movableTabs = self._extractKey(
            (properties, attProperties, kwargs), "MovableTabs", True
        )
        if self._movableTabs:
            newStyle = newStyle | aui.AUI_NB_TAB_MOVE | aui.AUI_NB_TAB_SPLIT
        if not _USE_AGW:
            newStyle = newStyle | aui.AUI_NB_CLOSE_ON_ALL_TABS
        newStyle = newStyle | kwargs.pop("style", 0) | kwargs.pop("agwStyle", 0)
        if _USE_AGW:
            kwargs["agwStyle"] = newStyle
        else:
            kwargs["style"] = newStyle
        dPageFrameMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def insertPage(self, pos, pgCls=None, caption="", imgKey=None, ignoreOverride=False):
        """
        Insert the page into the pageframe at the specified position,
        and optionally sets the page caption and image. The image
        should have already been added to the pageframe if it is
        going to be set here.
        """
        # Allow subclasses to potentially override this behavior. This will
        # enable them to handle page creation in their own way. If overridden,
        # the method will return the new page.
        ret = None
        if not ignoreOverride:
            ret = self._insertPageOverride(pos, pgCls, caption, imgKey)
        if ret:
            return ret
        if pgCls is None:
            pgCls = self.PageClass
        if isinstance(pgCls, dPage):
            pg = pgCls
        else:
            # See if the 'pgCls' is either some XML or the path of an XML file
            if isinstance(pgCls, str):
                xml = pgCls
                from lib.DesignerClassConverter import DesignerClassConverter

                conv = DesignerClassConverter()
                pgCls = conv.classFromText(xml)
            pg = pgCls(self)
        if not caption:
            # Page could have its own default caption
            caption = pg._caption
        if imgKey:
            idx = self._imageList[imgKey]
            bmp = self.GetImageList().GetBitmap(idx)
            self.InsertPage(pos, pg, caption=caption, bitmap=bmp)
        else:
            self.InsertPage(pos, pg, caption=caption)
        self.layout()
        return self.Pages[pos]

    def _insertPageOverride(self, pos, pgCls, caption, imgKey):
        pass

    @property
    def MovableTabs(self):
        """
        When True (default), tabs can be re-arranged by dragging, and docked at different sides of
        the control. This can only be set when the control is created. Default = True.  (bool)
        """
        return self._movableTabs


class dPageStyled(dPageFrameMixin, fnb.FlatNotebook):
    """
    Creates a pageframe, which can contain an unlimited number of pages,
    each of which should be a subclass/instance of the dPage class. Note that there
    is no visible border around the pages.
    """

    _evtPageChanged = readonly(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED)
    _evtPageChanging = readonly(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING)
    _tabposBottom = readonly(fnb.FNB_BOTTOM)

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dPageStyled
        preClass = fnb.FlatNotebook
        # For some reason this class always opens to the *last* page, unlike all other
        # paged controls. This will make it open to the first page, unless otherwise
        # explicitly set.
        selpg = int(
            self._extractKey(
                (properties, attProperties, kwargs), "SelectedPageNumber", defaultVal=0
            )
        )
        dPageFrameMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )
        ui.setAfter(self, "SelectedPageNumber", selpg)

    def _initEvents(self):
        super()._initEvents()
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.__onPageClosing)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSED, self.__onPageClosed)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CONTEXT_MENU, self.__onPageContextMenu)

    def _afterInit(self):
        if sys.platform[:3] == "win":
            ## This keeps Pages from being ugly on Windows:
            self.SetBackgroundColour(self.GetBackgroundColour())
        super()._afterInit()

    def __onPageClosing(self, evt):
        """The page has not yet been closed, so we can veto it if conditions call for it."""
        pageNum = evt.GetSelection()
        if self._beforePageClose(pageNum) is False:
            evt.Veto()
        else:
            evt.Skip()
        self.raiseEvent(events.PageClosing, pageNum=pageNum)

    def _beforePageClose(self, page):
        return self.beforePageClose(page)

    def insertPage(self, *args, **kwargs):
        page = super().insertPage(*args, **kwargs)
        # incline isn't autoset on new page add so set it
        self.SetAllPagesShapeAngle(self.TabSideIncline)
        return page

    def beforePageClose(self, page):
        """Return False from this method to prevent the page from closing."""
        pass

    def __onPageClosed(self, evt):
        self.raiseEvent(events.PageClosed)

    def __onPageContextMenu(self, evt):
        self.GetPage(self.GetSelection()).raiseEvent(events.PageContextMenu)

    # Property definitions
    @property
    def ActiveTabColor(self):
        """
        Specifies the color of the active tab (str or 3-tuple) (Default=None)
        Note: is not visible with the 'VC8' TabStyle
        """
        try:
            ret = self._activeTabColor
        except AttributeError:
            ret = self._activeTabColor = None
        return ret

    @ActiveTabColor.setter
    def ActiveTabColor(self, val):
        if self._constructed():
            self._activeTabColor = val
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            if isinstance(val, tuple):
                self.SetActiveTabColour(wx.Colour(*val))
                self.Refresh()
            else:
                raise ValueError(_("'%s' can not be translated into a color" % val))
        else:
            self._properties["ActiveTabColor"] = val

    @property
    def ActiveTabTextColor(self):
        """
        Specifies the color of the text of the active tab (str or 3-tuple) (Default=None)
        Note: is not visible with the 'VC8' TabStyle
        """
        try:
            ret = self._activeTabTextColor
        except AttributeError:
            ret = self._activeTabTextColor = None
        return ret

    @ActiveTabTextColor.setter
    def ActiveTabTextColor(self, val):
        if self._constructed():
            self._activeTabTextColor = val
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            if isinstance(val, tuple):
                self.SetActiveTabTextColour(wx.Colour(*val))
                self.Refresh()
            else:
                raise ValueError(_("'%s' can not be translated into a color" % val))
        else:
            self._properties["ActiveTabTextColor"] = val

    @property
    def InactiveTabTextColor(self):
        """
        Specifies the color of the text of non active tabs (str or 3-tuple) (Default=None)
        Note: is not visible with the 'VC8' TabStyle
        """
        try:
            ret = self._inactiveTabTextColor
        except AttributeError:
            ret = self._inactiveTabTextColor = None
        return ret

    @InactiveTabTextColor.setter
    def InactiveTabTextColor(self, val):
        if self._constructed():
            self._inactiveTabTextColor = val
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            if isinstance(val, tuple):
                self.SetNonActiveTabTextColour(wx.Colour(*val))
                self.Refresh()
            else:
                raise ValueError(_("'%s' can not be translated into a color" % val))
        else:
            self._properties["InactiveTabTextColor"] = val

    @property
    def ShowDropdownTabList(self):
        """
        Specifies whether the dropdown tab list button is visible in the menu (bool) (Default=False)
        Setting this property to True will set ShowNavButtons to False
        """
        try:
            ret = self._showDropdownTabList
        except AttributeError:
            ret = self._showDropdownTabList = False
        return ret

    @ShowDropdownTabList.setter
    def ShowDropdownTabList(self, val):
        val = bool(val)
        if val:
            self._addWindowStyleFlag(fnb.FNB_DROPDOWN_TABS_LIST)
            if not _USE_EDITRA:
                self._addWindowStyleFlag(fnb.FNB_NO_NAV_BUTTONS)
                self._showNavButtons = False
        else:
            self._delWindowStyleFlag(fnb.FNB_DROPDOWN_TABS_LIST)

        self._showDropdownTabList = val

    @property
    def ShowMenuCloseButton(self):
        """Specifies whether the close button is visible in the menu (bool) (Default=True)"""
        try:
            ret = self._showMenuCloseButton
        except AttributeError:
            ret = self._showMenuCloseButton = True
        return ret

    @ShowMenuCloseButton.setter
    def ShowMenuCloseButton(self, val):
        val = bool(val)
        if val:
            self._delWindowStyleFlag(fnb.FNB_NO_X_BUTTON)
        else:
            self._addWindowStyleFlag(fnb.FNB_NO_X_BUTTON)
        self._showMenuCloseButton = val

    @property
    def ShowMenuOnSingleTab(self):
        """
        Specifies whether the tab thumbs and nav buttons are shown when there is a single tab.
        (bool) (Default=True)"
        """
        try:
            ret = self._showMenuOnSingleTab
        except AttributeError:
            ret = self._showMenuOnSingleTab = True
        return ret

    @ShowMenuOnSingleTab.setter
    def ShowMenuOnSingleTab(self, val):
        val = bool(val)
        if val:
            self._delWindowStyleFlag(fnb.FNB_HIDE_ON_SINGLE_TAB)
        else:
            self._addWindowStyleFlag(fnb.FNB_HIDE_ON_SINGLE_TAB)
        self._showMenuOnSingleTab = val

    @property
    def ShowNavButtons(self):
        """
        Specifies whether the left and right nav buttons are visible in the menu (bool)
        (Default=True) Setting this property to True will set ShowDropdownTabList to False
        """
        try:
            ret = self._showNavButtons
        except AttributeError:
            ret = self._showNavButtons = True
        return ret

    @ShowNavButtons.setter
    def ShowNavButtons(self, val):
        val = bool(val)
        if val:
            self._delWindowStyleFlag(fnb.FNB_NO_NAV_BUTTONS)
            if not _USE_EDITRA:
                self._delWindowStyleFlag(fnb.FNB_DROPDOWN_TABS_LIST)
                self._showDropdownTabList = False
        else:
            self._addWindowStyleFlag(fnb.FNB_NO_NAV_BUTTONS)
        self._showNavButtons = val

    @property
    def ShowPageCloseButtons(self):
        """Specifies whether the close button is visible on the page tab (bool) (Default=False)"""
        try:
            ret = self._showPageCloseButtons
        except AttributeError:
            ret = self._showPageCloseButtons = False
        return ret

    @ShowPageCloseButtons.setter
    def ShowPageCloseButtons(self, val):
        val = bool(val)
        if val:
            self._addWindowStyleFlag(fnb.FNB_X_ON_TAB)
        else:
            self._delWindowStyleFlag(fnb.FNB_X_ON_TAB)
        self._showPageCloseButtons = val

    @property
    def TabAreaColor(self):
        """
        Specifies the background color of the tab area. This is exactly the same as the
        'MenuBackColor' property, but with a more intuitive name.  (str or 3-tuple) (Default=None)
        Note: is not visible with 'VC71' TabStyle.
        """
        try:
            ret = self._tabAreaColor
        except AttributeError:
            ret = self._tabAreaColor = None
        return ret

    @TabAreaColor.setter
    def TabAreaColor(self, val):
        if self._constructed():
            self._tabAreaColor = val
            if isinstance(val, str):
                val = color_tools.colorTupleFromName(val)
            if isinstance(val, tuple):
                self.SetTabAreaColour(wx.Colour(*val))
                self.Refresh()
            else:
                raise ValueError(_("'%s' can not be translated into a color" % val))
        else:
            self._properties["MenuBackColor"] = val

    @property
    def TabPosition(self):
        """
        Specifies where the page tabs are located. (string)
            Top (default)
            Bottom
        """
        if self._hasWindowStyleFlag(self._tabposBottom):
            return "Bottom"
        else:
            return "Top"

    @TabPosition.setter
    def TabPosition(self, val):
        lowval = ustr(val).lower()[0]
        self._delWindowStyleFlag(self._tabposBottom)

        if lowval == "t":
            pass
        elif lowval == "b":
            self._addWindowStyleFlag(self._tabposBottom)
        else:
            raise ValueError(_("The only possible values are 'Top' and 'Bottom'"))

    @property
    def TabSideIncline(self):
        """
        Specifies the incline of the sides of the tab in degrees (int) (Default=0)
        Acceptable values are 0  - 15.
        Note: this property will have no effect on TabStyles other than Default.
        """
        try:
            ret = self._tabSideIncline
        except AttributeError:
            ret = self._tabSideIncline = 0
        return ret

    @TabSideIncline.setter
    def TabSideIncline(self, val):
        val = int(val)
        if not (0 <= val <= 15):
            raise ValueError(_("Value must be 0 through 15"))
        self._tabSideIncline = val
        self.SetAllPagesShapeAngle(val)

    @property
    def TabStyle(self):
        """
        Specifies the style of the display tabs. (string)
            "Default" (default)
            "VC8"
            "VC71"
            "Fancy"
            "Firefox"
        """
        try:
            ret = self._tabStyle
        except AttributeError:
            ret = self._tabStyle = "Default"
        return ret

    @TabStyle.setter
    def TabStyle(self, val):
        self._delWindowStyleFlag(fnb.FNB_VC8)
        self._delWindowStyleFlag(fnb.FNB_VC71)
        self._delWindowStyleFlag(fnb.FNB_FANCY_TABS)
        self._delWindowStyleFlag(fnb.FNB_FF2)
        lowval = ustr(val).lower()
        flags = {
            "default": "",
            "vc8": fnb.FNB_VC8,
            "vc71": fnb.FNB_VC71,
            "fancy": fnb.FNB_FANCY_TABS,
            "firefox": fnb.FNB_FF2,
        }
        cleanStyles = {
            "default": "Default",
            "vc8": "VC8",
            "vc71": "VC71",
            "fancy": "Fancy",
            "firefox": "Firefox",
        }
        try:
            flagToSet = flags[lowval]
            self._tabStyle = cleanStyles[lowval]
        except KeyError:
            raise ValueError(
                _("The only possible values are 'Default' and 'VC8', 'VC71', 'Fancy', or 'Firefox'")
            )
        if flagToSet:
            self._addWindowStyleFlag(flagToSet)

    # This is exactly the same as the 'TabAreaColor' property, but is maintained for backwards
    # compatibility.
    MenuBackColor = TabAreaColor


ui.dPageFrame = dPageFrame
ui.dPageToolBar = dPageToolBar
ui.dPageList = dPageList
ui.dPageSelect = dPageSelect
ui.dDockTabs = dDockTabs
ui.dPageStyled = dPageStyled


class TestMixin(object):
    def initProperties(self):
        self.Width = 600
        self.Height = 375
        self.TabPosition = random.choice(("Top", "Bottom", "Left", "Right"))

    def afterInit(self):
        self.appendPage(caption="Introduction")
        self.appendPage(caption="Chapter I")
        self.appendPage(caption="Chapter 2")
        self.appendPage(caption="Chapter 3")
        self.Pages[0].BackColor = "darkred"
        self.Pages[1].BackColor = "darkblue"
        self.Pages[2].BackColor = "green"
        self.Pages[3].BackColor = "yellow"

    def onPageChanged(self, evt):
        print("Page number changed from %s to %s" % (evt.oldPageNum, evt.newPageNum))


class _dPageToolBar_test(TestMixin, dPageToolBar):
    def afterInit(self):
        self.addImage("themes/tango/32x32/actions/go-previous.png", "Left")
        self.addImage("themes/tango/32x32/actions/go-next.png", "Right")
        self.addImage("themes/tango/32x32/actions/go-up.png", "Up")
        self.addImage("themes/tango/32x32/actions/go-down.png", "Down")
        self.appendPage(caption="Introduction", imgKey="Left")
        self.appendPage(caption="Chapter I", imgKey="Right")
        self.appendPage(caption="Chapter 2", imgKey="Up")
        self.appendPage(caption="Chapter 3", imgKey="Down")
        self.Pages[0].BackColor = "darkred"
        self.Pages[1].BackColor = "darkblue"
        self.Pages[2].BackColor = "green"
        self.Pages[3].BackColor = "yellow"


class _dPageFrame_test(TestMixin, dPageFrame):
    pass


class _dPageList_test(TestMixin, dPageList):
    pass


class _dPageSelect_test(TestMixin, dPageSelect):
    pass


class _dDockTabs_test(TestMixin, dDockTabs):
    pass


class _dPageStyled_test(TestMixin, dPageStyled):
    def initProperties(self):
        self.Width = 500
        self.Height = 250
        self.PageCount = 4
        self.TabStyle = random.choice(("Default", "VC8", "VC71", "Fancy", "Firefox"))
        self.TabPosition = random.choice(("Top", "Bottom"))
        self.ShowPageCloseButtons = random.choice((True, False))
        self.ShowDropdownTabList = random.choice((True, False))
        self.ShowMenuClose = random.choice((True, False))
        self.ShowMenuOnSingleTab = random.choice((True, False))
        self.ShowNavButtons = random.choice((True, False))
        self.MenuBackColor = "lightsteelblue"
        self.InactiveTabTextColor = "darkcyan"
        self.ActiveTabTextColor = "blue"

    def afterInit(self):
        # Make the pages visible by setting a BackColor
        self.Pages[0].BackColor = "darkred"
        self.Pages[1].BackColor = "darkblue"
        self.Pages[2].BackColor = "green"
        self.Pages[3].BackColor = "yellow"
        # Can't add controls to the Test form now, so use callAfter() to delay
        # the actual control creation.
        ui.callAfter(self._addControls)

    def _addControls(self):
        pnl = self.Form.Children[0]
        szr = pnl.Sizer
        szr.DefaultBorder = 2
        chk = dCheckBox(
            pnl,
            Caption="Show Page Close Buttons",
            DataSource=self,
            DataField="ShowPageCloseButtons",
        )
        szr.append(chk, halign="center")
        chk = dCheckBox(
            pnl, Caption="Show Nav Buttons", DataSource=self, DataField="ShowNavButtons"
        )
        szr.append(chk, halign="center")
        chk = dCheckBox(pnl, Caption="Show Menu Close", DataSource=self, DataField="ShowMenuClose")
        szr.append(chk, halign="center")
        lbl = dLabel(pnl, Caption="Tab Style:")
        dd = dDropdownList(
            pnl,
            Choices=["Default", "VC8", "VC71", "Fancy", "Firefox"],
            DataSource=self,
            DataField="TabStyle",
        )
        hsz = dSizer("h")
        hsz.append(lbl)
        hsz.append(dd)
        szr.append(hsz, halign="center")
        lbl = dLabel(pnl, Caption="Tab Position:")
        dd = dDropdownList(pnl, Choices=["Top", "Bottom"], DataSource=self, DataField="TabPosition")
        hsz = dSizer("h")
        hsz.append(lbl)
        hsz.append(dd)
        szr.append(hsz, halign="center")
        self.Form.layout()
        self.Form.fitToSizer()

    def onPageChanged(self, evt):
        print("Page number changed from %s to %s" % (evt.oldPageNum, evt.newPageNum))


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dPageFrame_test)
    test.Test().runTest(_dPageToolBar_test)
    test.Test().runTest(_dPageList_test)
    test.Test().runTest(_dPageSelect_test)
    test.Test().runTest(_dDockTabs_test)
    test.Test().runTest(_dPageStyled_test)
