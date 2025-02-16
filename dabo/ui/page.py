#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .. import events
from .. import ui
from ..localization import _
from . import dScrollPanel
from . import makeDynamicProperty


class dPage(dScrollPanel):
    """Creates a page to appear as a tab in a pageframe."""

    def __init__(self, *args, **kwargs):
        self._caption = ""
        self._pendingUpdates = False
        self._deferredUpdates = False
        kwargs["AlwaysResetSizer"] = self._extractKey(kwargs, "AlwaysResetSizer", True)
        super().__init__(*args, **kwargs)
        self._baseClass = dPage

    def _afterInit(self):
        self.initSizer()
        self.itemsCreated = False
        super()._afterInit()

    def _initEvents(self):
        super()._initEvents()
        self.bindEvent(events.PageEnter, self.__onPageEnter)
        self.bindEvent(events.PageLeave, self.__onPageLeave)

    def initSizer(self):
        """Set up the default vertical box sizer for the page."""
        try:
            szCls = self.Parent.PageSizerClass
        except AttributeError:
            # Not part of a paged control
            return
        if szCls is not None:
            self.Sizer = szCls("vertical")

    def _createItems(self):
        self.lockDisplay()
        self.createItems()
        self.itemsCreated = True
        self.layout()
        ui.callAfter(self.unlockDisplay)

    def createItems(self):
        """
        Create the controls in the page.

        Called when the page is entered for the first time, allowing subclasses
        to delay-populate the page.
        """
        pass

    def update(self):
        if self.DeferredUpdates:
            try:
                if self.Parent.SelectedPage == self:
                    self._pendingUpdates = False
                else:
                    self._pendingUpdates = True
                    return
            except (ValueError, AttributeError):
                pass
        super().update()

    def __onPageEnter(self, evt):
        if not self.itemsCreated:
            self._createItems()
        if self._pendingUpdates:
            ui.callAfter(self.update)

    def __onPageLeave(self, evt):
        if hasattr(self, "Form"):
            form = self.Form
            if hasattr(form, "activeControlValid"):
                form.activeControlValid()

    def _saveLastActiveControl(self):
        self._lastFocusedControl = self.Form.ActiveControl

    def _restoreLastActiveControl(self):
        if getattr(self, "_lastFocusedControl", None):
            self.Form.ActiveControl = self._lastFocusedControl

    def _getPagePosition(self):
        """Returns the position of this page within its parent."""
        try:
            ret = self.Parent.Pages.index(self)
        except (ValueError, AttributeError):
            ret = -1
        return ret

    # Property definitions
    @property
    def Caption(self):
        """The text identifying this particular page.  (str)"""
        # Need to determine which page we are
        ret = ""
        pos = self._getPagePosition()
        if pos > -1:
            ret = self.Parent.GetPageText(pos)
        if not ret:
            ret = self._caption
        return ret

    @Caption.setter
    def Caption(self, val):
        self._caption = val
        if self._constructed():
            pos = self._getPagePosition()
            if pos > -1:
                self.Parent.SetPageText(pos, val)
        else:
            self._properties["Caption"] = val

    @property
    def DeferredUpdates(self):
        """Allow to defer controls updates until page become active.  (bool)"""
        return self._deferredUpdates

    @DeferredUpdates.setter
    def DeferredUpdates(self, val):
        self._deferredUpdates = val

    @property
    def Image(self):
        """
        Sets the image that is displayed on the page tab. This is determined by the key value
        passed, which must refer to an image already added to the parent pageframe.

        When used to retrieve an image, it returns the index of the page's image in the parent
        pageframe's image list.  (int)
        """
        return self.Parent.getPageImage(self)

    @Image.setter
    def Image(self, imgKey):
        if self._constructed():
            self.Parent.setPageImage(self, imgKey)
        else:
            self._properties["Image"] = imgKey

    DynamicCaption = makeDynamicProperty(Caption)
    DynamicImage = makeDynamicProperty(Image)


ui.dPage = dPage


class _dPage_test(dPage):
    def initProperties(self):
        self.BackColor = "Red"


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dPage_test)
