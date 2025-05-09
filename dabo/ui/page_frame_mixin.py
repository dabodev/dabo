# -*- coding: utf-8 -*-
import sys

import wx

from .. import events
from .. import lib
from .. import settings
from .. import ui
from ..lib.utils import ustr
from ..localization import _
from . import dControlMixin
from . import dPage
from . import makeDynamicProperty

dabo_module = settings.get_dabo_package()


MSG_SMART_FOCUS_ABUSE = _(
    "The '%s' control must inherit from dPage to use the UseSmartFocus feature."
)


class dPageFrameMixin(dControlMixin):
    """Creates a container for an unlimited number of pages."""

    def __init__(self, preClass, parent, properties=None, attProperties=None, *args, **kwargs):
        kwargs["style"] = self._extractKey((properties, kwargs), "style", 0) | wx.CLIP_CHILDREN
        super().__init__(
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def _beforeInit(self, pre):
        from ..ui import dSizer

        self._imageList = {}
        self._pageSizerClass = dSizer
        super()._beforeInit(pre)

    def _initEvents(self):
        super()._initEvents()
        self.Bind(self._evtPageChanged, self.__onPageChanged)
        self.Bind(self._evtPageChanging, self.__onPageChanging)
        self.bindEvent(events.Create, self.__onCreate)

    def __onPageChanging(self, evt):
        """The page has not yet been changed, so we can veto it if conditions call for it."""
        # Avoid event propagated from child frames.
        evt.StopPropagation()
        oldPageNum = evt.GetOldSelection()
        newPageNum = evt.GetSelection()
        if self._beforePageChange(oldPageNum, newPageNum) is False:
            evt.Veto()
        else:
            evt.Skip()
        if oldPageNum >= 0 and self.PageCount > oldPageNum and self.UseSmartFocus:
            try:
                self.Pages[oldPageNum]._saveLastActiveControl()
            except AttributeError:
                dabo_module.error(MSG_SMART_FOCUS_ABUSE % self.Name)
        self.raiseEvent(events.PageChanging, oldPageNum=oldPageNum, newPageNum=newPageNum)

    def _beforePageChange(self, old, new):
        return self.beforePageChange(old, new)

    def beforePageChange(self, fromPage, toPage):
        """Return False from this method to prevent the page from changing."""
        pass

    def __onCreate(self, evt):
        # Make sure the PageEnter fires for the current page on
        # pageframe instantiation, as this doesn't happen automatically.
        # Putting this code in afterInit() results in a segfault on Linux, btw.
        ui.callAfter(self.__pageChanged, 0, None)

    def __onPageChanged(self, evt):
        evt.Skip()
        evt.StopPropagation()

        newPageNum = evt.GetSelection()
        try:
            oldPageNum = self._lastPage
        except AttributeError:
            # _lastPage hasn't been defined yet.
            oldPageNum = None
        self.__pageChanged(newPageNum, oldPageNum)

    def __pageChanged(self, newPageNum, oldPageNum):
        ## Because of platform inconsistencies, it is safer to raise the dabo
        ## events in a callafter instead of directly.
        if not self:
            # JIC this object has been released
            return
        self._lastPage = newPageNum
        if oldPageNum is not None:
            if oldPageNum >= 0:
                try:
                    oldPage = self.Pages[oldPageNum]
                    ui.callAfter(oldPage.raiseEvent, events.PageLeave)
                except IndexError:
                    # Page has already been released
                    return

        if newPageNum >= 0 and self.PageCount > newPageNum:
            newPage = self.Pages[newPageNum]
            ui.callAfter(newPage.raiseEvent, events.PageEnter)
            ui.callAfter(
                self.raiseEvent,
                events.PageChanged,
                oldPageNum=oldPageNum,
                newPageNum=newPageNum,
            )
            if self.UseSmartFocus:
                try:
                    newPage._restoreLastActiveControl()
                except AttributeError:
                    dabo_module.warn(MSG_SMART_FOCUS_ABUSE % self.Name)

    # Image-handling function
    def addImage(self, img, key=None):
        """
        Adds the passed image to the control's ImageList, and maintains
        a reference to it that is retrievable via the key value.
        """
        if key is None:
            key = ustr(img)
        if isinstance(img, str):
            img = ui.strToBmp(img)
        il = self.GetImageList()
        if not il:
            il = wx.ImageList(img.GetWidth(), img.GetHeight(), initialCount=0)
            self.AssignImageList(il)
        idx = il.Add(img)
        self._imageList[key] = idx

    def setPageImage(self, pg, imgKey):
        """
        Sets the specified page's image to the image corresponding
        to the specified key. May also optionally pass the index of the
        image in the ImageList rather than the key.
        """
        pgIdx = self._getPageIndex(pg)
        if pgIdx is not None:
            if isinstance(imgKey, int):
                imgIdx = imgKey
            else:
                try:
                    imgIdx = self._imageList[imgKey]
                except KeyError:
                    # They may be trying to set the page's Image to an
                    # image that hasn't yet been added to the image list.
                    self.addImage(imgKey)
                    imgIdx = self._imageList[imgKey]
            self.SetPageImage(pgIdx, imgIdx)
            self.Pages[pgIdx].imgKey = imgKey

    def getPageImage(self, pg):
        """
        Returns the index of the specified page's image in the
        current image list, or -1 if no image is set for the page.
        """
        ret = -1
        pgIdx = self._getPageIndex(pg)
        if pgIdx is not None:
            ret = self.GetPageImage(pgIdx)
        return ret

    def appendPage(self, pgCls=None, caption="", imgKey=None, **kwargs):
        """
        Appends the page to the pageframe, and optionally sets
        the page caption and image. The image should have already
        been added to the pageframe if it is going to be set here.

        Any kwargs sent will be passed on to the constructor of the
        page class.
        """
        return self.insertPage(self.GetPageCount(), pgCls, caption, imgKey, **kwargs)

    def insertPage(self, pos, pgCls=None, caption="", imgKey=None, ignoreOverride=False, **kwargs):
        """
        Insert the page into the pageframe at the specified position,
        and optionally sets the page caption and image. The image
        should have already been added to the pageframe if it is
        going to be set here.

        Any kwargs sent will be passed on to the constructor of the
        page class.
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
            pg = pgCls(self, **kwargs)
        if not caption:
            # Page could have its own default caption
            caption = pg._caption
        if caption.count("&") == 1 and caption[-1] != "&":
            hotkey = "alt+%s" % (caption[caption.index("&") + 1],)
            self.Form.bindKey(hotkey, self._onHK)
            pg._rawCaption = caption
            if sys.platform.startswith("darwin"):
                # Other platforms underline the character after the &; Mac just
                # shows the &.
                caption = caption.replace("&", "")
        if imgKey:
            idx = self._imageList[imgKey]
            self.InsertPage(pos, pg, text=caption, select=False, imageId=idx)
        else:
            self.InsertPage(pos, pg, text=caption, select=False)
        self.Pages[pos].imgKey = imgKey
        self.layout()
        insertedPage = self.Pages[pos]
        insertedPage.Caption = caption
        return insertedPage

    def _insertPageOverride(self, pos, pgCls, caption, imgKey):
        pass

    def removePage(self, pgOrPos, delPage=True):
        """
        Removes the specified page. You can specify a page by either
        passing the page itself, or a position. If delPage is True (default),
        the page is released, and None is returned. If delPage is
        False, the page is returned.
        """
        pos = pgOrPos
        if isinstance(pgOrPos, int):
            pg = self.Pages[pgOrPos]
        else:
            pg = pgOrPos
            pos = self.Pages.index(pg)
        if delPage:
            self.DeletePage(pos)
            ret = None
        else:
            self.RemovePage(pos)
            ret = pg
        return ret

    def movePage(self, oldPgOrPos, newPos, selecting=True):
        """
        Moves the specified 'old' page to the new position and
        optionally selects it. If an invalid page number is passed,
        it returns False without changing anything.
        """
        self.Parent.lockDisplay()
        pos = oldPgOrPos
        if isinstance(oldPgOrPos, int):
            if oldPgOrPos > self.PageCount - 1:
                return False
            pg = self.Pages[oldPgOrPos]
        else:
            pg = oldPgOrPos
            pos = self.Pages.index(pg)
        # Make sure that the new position is valid
        newPos = max(0, newPos)
        newPos = min(self.PageCount - 1, newPos)
        if newPos == pos:
            # No change
            return
        cap = pg.Caption
        self.RemovePage(pos)
        self.insertPage(newPos, pg, caption=cap, imgKey=pg.imgKey)
        if selecting:
            self.SelectedPage = pg
        self.Parent.unlockDisplay()
        return True

    def cyclePages(self, num):
        """
        Moves through the pages by the specified amount, wrapping
        around the ends. Negative values move to previous pages; positive
        move through the next pages.
        """
        self.SelectedPageNumber = (self.SelectedPageNumber + num) % self.PageCount

    def layout(self):
        """Wrap the wx version of the call, if possible."""
        self.Layout()
        try:
            # Call the Dabo version, if present
            self.Sizer.layout()
        except AttributeError:
            pass
        for pg in self.Pages:
            try:
                pg.layout()
            except AttributeError:
                # could be that the page is a single control, not a container
                pass
        if self.Application.Platform == "Win":
            self.refresh()

    def _getPageIndex(self, pg):
        """
        Resolves page references to the page index, which is what
        is needed by most methods that act on pages.
        """
        ret = None
        if isinstance(pg, int):
            ret = pg
        else:
            # Most likely a page instance was passed. Find its index
            for i in range(self.PageCount):
                if self.GetPage(i) == pg:
                    ret = i
                    break
        return ret

    def _onHK(self, evt):
        char = chr(evt.EventData["keyCode"]).lower()
        for page in self.Pages:
            if "&%s" % char in getattr(page, "_rawCaption", "").lower():
                self.SelectedPage = page
                page.setFocus()
                return
        # raise ValueError("Caption for hotkey not found.") ## unsure if wise

    # Property definitions:
    @property
    def PageClass(self):
        """
        Specifies the class of control to use for pages by default. (classRef) This really only
        applies when using the PageCount property to set the number of pages. If you instead use
        AddPage() you still need to send an instance as usual. Class must descend from a dabo base
        class.
        """
        try:
            return self._pageClass
        except AttributeError:
            return dPage

    @PageClass.setter
    def PageClass(self, val):
        self._pageClass = val

    @property
    def PageCount(self):
        """
        Specifies the number of pages in the pageframe. (int)

        When using this to increase the number of pages, PageClass will be queried as the
        object to use as the page object.
        """
        return int(self.GetPageCount())

    @PageCount.setter
    def PageCount(self, val):
        if self._constructed():
            val = int(val)
            pageCount = self.GetPageCount()
            pageClass = self.PageClass
            if val < 0:
                raise ValueError(_("Cannot set PageCount to less than zero."))

            if val > pageCount:
                for i in range(pageCount, val):
                    pg = self.appendPage(pageClass)
                    if not pg.Caption:
                        pg.Caption = _("Page %s") % (i + 1,)
            elif val < pageCount:
                for i in range(pageCount, val, -1):
                    self.DeletePage(i - 1)
        else:
            self._properties["PageCount"] = val

    @property
    def Pages(self):
        """Returns a list of the contained pages.  (list)"""
        ## pkm: It is possible for pages to not be instances of dPage
        ##      (such as in the AppWizard), resulting in self.PageCount > len(self.Pages)
        ##      if using the commented code below.
        # return [pg for pg in self.Children    if isinstance(pg, ui.dPage) ]
        return [self.GetPage(pg) for pg in range(self.PageCount)]

    @property
    def PageSizerClass(self):
        """
        Default sizer class for pages added automatically to this control. Set this to None to
        prevent sizers from being automatically added to child pages. (dSizer or None)
        """
        return self._pageSizerClass

    @PageSizerClass.setter
    def PageSizerClass(self, val):
        if self._constructed():
            self._pageSizerClass = val
        else:
            self._properties["PageSizerClass"] = val

    @property
    def SelectedPage(self):
        """References the current frontmost page.  (dPage)"""
        try:
            sel = self.GetSelection()
            if sel < 0:
                ret = None
            else:
                ret = self.GetPage(sel)
        except AttributeError:
            ret = None
        return ret

    @SelectedPage.setter
    @ui.deadCheck
    def SelectedPage(self, pg):
        if self._constructed():
            idx = self._getPageIndex(pg)
            try:
                self.SetSelection(idx)
            except:
                self._properties["SelectedPage"] = pg

        else:
            self._properties["SelectedPage"] = pg

    @property
    def SelectedPageNumber(self):
        """Returns the index of the current frontmost page.  (int)"""
        return self.GetSelection()

    @SelectedPageNumber.setter
    @ui.deadCheck
    def SelectedPageNumber(self, val):
        if self._constructed():
            self.SetSelection(val)
        else:
            self._properties["SelectedPageNumber"] = val

    @property
    def TabPosition(self):
        """Specifies where the page tabs are located. (int)
        Top (default)
        Left
        Right
        Bottom
        """
        if self._hasWindowStyleFlag(self._tabposBottom):
            return "Bottom"
        elif self._hasWindowStyleFlag(self._tabposRight):
            return "Right"
        elif self._hasWindowStyleFlag(self._tabposLeft):
            return "Left"
        else:
            return "Top"

    @TabPosition.setter
    def TabPosition(self, val):
        val = ustr(val)

        self._delWindowStyleFlag(self._tabposTop)
        self._delWindowStyleFlag(self._tabposBottom)
        self._delWindowStyleFlag(self._tabposRight)
        self._delWindowStyleFlag(self._tabposLeft)

        if val == "Top":
            self._addWindowStyleFlag(self._tabposTop)
        elif val == "Left":
            self._addWindowStyleFlag(self._tabposLeft)
        elif val == "Right":
            self._addWindowStyleFlag(self._tabposRight)
        elif val == "Bottom":
            self._addWindowStyleFlag(self._tabposBottom)
        else:
            raise ValueError(_("The only possible values are 'Top', 'Left', 'Right', and 'Bottom'"))

    @property
    def UpdateInactivePages(self):
        """
        Determines if the inactive pages are updated too. (bool) Setting it to False can
        significantly improve update performance of multipage forms. Default=True
        """
        return getattr(self, "_updateInactivePages", True)

    @UpdateInactivePages.setter
    def UpdateInactivePages(self, val):
        self._updateInactivePages = val

    @property
    def UseSmartFocus(self):
        """
        Determines if focus has to be restored to the last active control on page when it become
        selected. (bool) Default=False.
        """
        return getattr(self, "_useSmartFocus", False)

    @UseSmartFocus.setter
    def UseSmartFocus(self, val):
        self._useSmartFocus = val

    DynamicPageClass = makeDynamicProperty(PageClass)
    DynamicPageCount = makeDynamicProperty(PageCount)
    DynamicSelectedPage = makeDynamicProperty(SelectedPage)
    DynamicSelectedPageNumber = makeDynamicProperty(SelectedPageNumber)
    DynamicTabPosition = makeDynamicProperty(TabPosition)
    DynamicUpdateInactivePages = makeDynamicProperty(UpdateInactivePages)


ui.dPageFrameMixin = dPageFrameMixin
