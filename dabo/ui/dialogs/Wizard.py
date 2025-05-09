# -*- coding: utf-8 -*-
from ... import constants as constants
from ... import events
from ... import ui
from ...application import dApp
from ...localization import _
from .. import dBitmapButton
from .. import dBorderSizer
from .. import dButton
from .. import dCalendar
from .. import dCheckBox
from .. import dCheckList
from .. import dColumn
from .. import dDateTextBox
from .. import dDialog
from .. import dDropdownList
from .. import dEditBox
from .. import dExtendedCalendar
from .. import dForm
from .. import dGrid
from .. import dGridSizer
from .. import dImage
from .. import dLabel
from .. import dLine
from .. import dListControl
from .. import dMaskedTextBox
from .. import dMessageBox
from .. import dOkCancelDialog
from .. import dPageFrame
from .. import dPageFrameNoTabs
from .. import dPanel
from .. import dRadioList
from .. import dScrollPanel
from .. import dSizer
from .. import dSpinner
from .. import dTextBox
from .WizardPage import WizardPage


class Wizard(dDialog):
    """
    This is the main form for creating wizards. To use it, define
    a series of wizard pages, based on WizardPage. Then add these
    classes to your subclass of Wizard. The order that you add them
    will be the order that they appear in the wizard.
    """

    def __init__(self, parent=None, properties=None, *args, **kwargs):
        pgs = self._extractKey(kwargs, "Pages")
        kwargs["BorderResizable"] = kwargs.get("BorderResizable", False)
        kwargs["ShowMaxButton"] = kwargs.get("ShowMaxButton", False)
        kwargs["ShowMinButton"] = kwargs.get("ShowMinButton", False)
        kwargs["ShowCloseButton"] = kwargs.get("ShowCloseButton", False)
        self._pages = []
        self._currentPage = -1
        self._blankPage = None
        self._defaultPicture = ""
        self.wizardIcon = None
        super().__init__(parent=parent, properties=properties, *args, **kwargs)

        # Add the main panel
        mp = self.mainPanel = dPanel(self)
        self.Sizer.append(mp, 1, "x")
        mp.Sizer = dSizer(self.Sizer.Orientation)

        # Experimental!
        # Automatically sets the page to match the form's BackColor. Set
        # this to False if you want the pages to have their own BackColor.
        self.setPageColor = False

        # Changing this attribute determines if we confirm when
        # the user clicks 'Cancel'
        self.verifyCancel = True
        # This is the message displayed to the user when a Cancel
        # confirmation is displayed.
        self.confirmCancelMsg = _("Are you sure you want to exit?")
        # We want to size the form explicitly
        self.SaveRestorePosition = False
        # We also want the wizard to respect explicit sizing
        self.AutoSize = False

        self.setup()
        if pgs:
            self.append(pgs)

    def setup(self):
        """This creates the controls used by the wizard."""
        mp = self.mainPanel
        if self.setPageColor:
            mp.BackColor = self.BackColor
        mpsz = mp.Sizer
        mpsz.DefaultSpacing = 10
        mpsz.DefaultBorder = 12
        mpsz.DefaultBorderLeft = mpsz.DefaultBorderRight = True
        # Add a top border
        mpsz.appendSpacer(mpsz.DefaultBorder)

        self.wizardIcon = dImage(mp, ScaleMode="Proportional")
        if not self.Picture:
            self.PictureHeight = self.PictureWidth = 96
            self.Picture = "daboIcon096"
        hsz = dSizer("h")
        hsz.DefaultSpacing = 20
        hsz.append(self.wizardIcon, 0)

        # This is the panel that will contain the various pages
        pp = self.pagePanel = dPanel(mp)
        if self.setPageColor:
            pp.BackColor = pp.Parent.BackColor
        ppsz = pp.Sizer = dSizer("v")

        hsz.append(pp, 1, "x")
        mpsz.append(hsz, 1, "x")

        # Separator line
        ln = dLine(mp)
        mpsz.append(ln, "x")

        # Buttons
        hsz = dSizer("h")
        hsz.DefaultSpacing = 5
        self.btnBack = dButton(mp, Caption=_("< Back"))
        self.btnNext = dButton(mp, Caption=_("Next >"))
        self.btnCancel = dButton(mp, Caption=_("Cancel"))
        hsz.append(self.btnBack)
        hsz.append(self.btnNext)
        hsz.append(self.btnCancel)
        self.btnBack.bindEvent(events.Hit, self.onBack)
        self.btnNext.bindEvent(events.Hit, self.onNext)
        self.btnCancel.bindEvent(events.Hit, self.onCancel)

        mpsz.append(hsz, 0, alignment=("right", "bottom"))

        # Add the top and bottom borders
        mpsz.prependSpacer(mpsz.DefaultBorder)
        mpsz.appendSpacer(mpsz.DefaultBorder)

    def onBack(self, evt):
        pg = self._pages[self.CurrentPage]
        self.CurrentPage += pg.prevPage()

    def onNext(self, evt):
        pg = self._pages[self.CurrentPage]
        if self.CurrentPage == (self.PageCount - 1):
            # This is actually 'Finish', so call the
            # finish() method, which will by default
            # close the wizard, or if the wizard is not
            # complete, keep it open to the last page.
            self._finish()
        else:
            self.CurrentPage += pg.nextPage()

    def onCancel(self, evt):
        # User clicked the Cancel button
        if self.verifyCancel:
            if not ui.areYouSure(self.confirmCancelMsg, _("Cancel Received"), cancelButton=False):
                return
        ui.callAfter(self.closeWizard, constants.DLG_CANCEL)

    def _finish(self):
        pg = self._pages[self.CurrentPage]
        ok = pg.onLeavePage("forward")
        if ok is not False:
            finOK = self.finish()
            if finOK is not False:
                ui.callAfter(self.closeWizard, constants.DLG_OK)

    def finish(self):
        """
        This is the place to do any of your cleanup actions. You
        can prevent the wizard from closing by returning False.
        """
        return True

    def start(self):
        self.CurrentPage = 0
        self.show()

    def closeWizard(self, action=None):
        # Warning! The close method shouldn't be called before EndModal
        # because it causes 'IA__gtk_window_set_modal' error on GTK platform.
        if self.Modal:
            self.EndModal(action)
        if self.Parent is None:
            # Since this is a dialog, we need to explicitly remove
            # it or the app will hang.
            self.close(True)

    def append(self, pg):
        if isinstance(pg, (list, tuple)):
            ret = []
            for p in pg:
                ret.append(self.append(p))
        else:
            ret = self.insert(len(self._pages), pg)
        return ret

    def insert(self, pos, pg):
        if isinstance(pg, (list, tuple)):
            pg.reverse()
            ret = []
            for p in pg:
                ret.append(self.insert(pos, p))
        else:
            # Give subclasses a chance to override
            page = self._insertWizardPageOverride(pos, pg)
            if page is None:
                if isinstance(pg, WizardPage):
                    # Already instantiated. First make sure it is a child of
                    # the page panel
                    if pg.Parent is not self.pagePanel:
                        pg.changeParent(self.pagePanel)
                    page = pg
                else:
                    if isinstance(pg, str):
                        xml = pg
                        from .lib.DesignerClassConverter import DesignerClassConverter

                        conv = DesignerClassConverter()
                        pg = conv.classFromText(xml)
                    page = pg(self.pagePanel)
                page.Size = self.pagePanel.Size
                self._pages.insert(pos, page)
                page.Visible = False
            ret = page
        return ret

    def _insertWizardPageOverride(self, pos, pg):
        pass

    def getPageByClass(self, pgClass):
        """Returns the first page that is an instance of the passed class"""
        try:
            ret = [pg for pg in self._pages if isinstance(pg, pgClass)][0]
        except IndexError:
            ret = None
        return ret

    def showPage(self):
        if self.PageCount == 0:
            return
        if self._blankPage:
            self.pagePanel.Sizer.remove(self._blankPage)
            self._blankPage.release()
        for idx in range(self.PageCount):
            page = self._pages[idx]
            self.pagePanel.Sizer.remove(page)
            if idx == self._currentPage:
                page.Visible = True
                # Need this to keep the pages resizing correctly.
                page.Size = self.pagePanel.Size
                # Helps the pages look better under Windows
                if self.setPageColor:
                    page.BackColor = self.BackColor
                self.pagePanel.Sizer.append(page, 1, "x")
                self.btnBack.Enabled = idx > 0
                cap = _("Next >")
                if idx == (self.PageCount - 1):
                    cap = _("Finish")
                self.btnNext.Caption = cap
                if page.Picture is not None:
                    self.wizardIcon.Picture = page.Picture
                else:
                    self.wizardIcon.Picture = self.Picture
            else:
                page.Visible = False
        self.layout()

    def showBlankPage(self):
        if self._blankPage is None:
            self._blankPage = WizardPage(self.pagePanel)
            self._blankPage.Title = _("This Space For Rent")
        self._blankPage.Visible = True
        self.pagePanel.Sizer.append(self._blankPage, 1, "x")
        self.btnBack.Enabled = self.btnNext.Enabled = False
        self.layout()

    def getRelativePage(self, orig, incr):
        """
        Accepts a page reference and an offset, and returns
        the page that is that many places away in the page order.
        If the offset refers to a non-existent page (e.g., on the second
        page and specifying an offset of -4), None will    be returned.
        """
        try:
            idx = self._pages.index(orig)
            ret = self._pages[idx + incr]
        except ValueError:
            ret = None
        return ret

    # Property definitions
    @property
    def CurrentPage(self):
        """Index of the current page in the wizard  (WizardPage)"""
        return self._currentPage

    @CurrentPage.setter
    def CurrentPage(self, val):
        if isinstance(val, WizardPage):
            val = self._pages.index(val)
        if self.PageCount == 0:
            self.showBlankPage()
            return
        val = min(val, self.PageCount - 1)
        if val == self._currentPage:
            # No change
            return
        self.raiseEvent(events.PageChanging, oldPageNum=self._currentPage, newPageNum=val)
        if self._currentPage < 0:
            direction = "forward"
        else:
            # First, see if the current page will allow us to leave
            direction = {True: "forward", False: "back"}[self._currentPage < val]
            ok = self._pages[self._currentPage].onLeavePage(direction)
            if ok is False:
                return
        # Now make sure that the current page is valid
        if val < 0:
            val = 0
        elif val > len(self._pages) - 1:
            # We're done
            self.release()
            return
        oldPg = self._currentPage
        newPg = val
        self._currentPage = val
        self._pages[self._currentPage].onEnterPage(direction)
        self.showPage()
        ui.callAfter(self.raiseEvent, events.PageChanged, oldPageNum=oldPg, newPageNum=newPg)

    @property
    def PageCount(self):
        """Number of pages in this wizard  (int)"""
        return len(self._pages)

    @property
    def Picture(self):
        """Sets the visible icon for the wizard.  (str/path)"""
        try:
            ret = self._defaultPicture
        except AttributeError:
            ret = ""
        return ret

    @Picture.setter
    def Picture(self, val):
        if self._constructed():
            try:
                self.wizardIcon.Picture = val
                self.wizardIcon.Size = (self.PictureWidth, self.PictureHeight)
                self._defaultPicture = val
            except AttributeError:
                # wizard icon hasn't been constructed yet.
                ui.setAfter(self, "Picture", val)
            self.layout()
        else:
            self._properties["Picture"] = val

    @property
    def PictureHeight(self):
        """Height of the wizard icon in pixels  (int)"""
        return self.wizardIcon.Height

    @PictureHeight.setter
    def PictureHeight(self, val):
        if self._constructed():
            try:
                self.wizardIcon.Height = val
            except AttributeError:
                # wizard icon hasn't been constructed yet.
                ui.setAfter(self, "PictureHeight", val)
            self.layout()
        else:
            self._properties["PictureHeight"] = val

    @property
    def PictureWidth(self):
        """Width of the wizard icon in pixels  (int)"""
        return self.wizardIcon.Width

    @PictureWidth.setter
    def PictureWidth(self, val):
        if self._constructed():
            try:
                self.wizardIcon.Width = val
            except AttributeError:
                # wizard icon hasn't been constructed yet.
                ui.setAfter(self, "PictureWidth", val)
            self.layout()
        else:
            self._properties["PictureWidth"] = val


if __name__ == "__main__":

    class WizPageOne(WizardPage):
        def createBody(self):
            self.Caption = _("This is the first page")
            lbl = dLabel(
                self,
                Caption=_(
                    """Are you getting excited yet???

I know that I am!!"""
                ),
            )
            self.Sizer.append(lbl, alignment="center")

    class WizPageTwo(WizardPage):
        def createBody(self):
            self.Caption = _("This is the second page")
            lbl = dLabel(
                self,
                Caption=_(
                    """This will demonstrate condtional skipping of
pages. If the checkbox below is checked, clicking
'Next' will move to Page 4 instead of Page 3."""
                ),
            )
            self.chk = dCheckBox(self, Caption="Skip?")
            self.Sizer.append(lbl, alignment="center")
            self.Sizer.appendSpacer(10)
            self.Sizer.append(self.chk, alignment="center")

        def skipIt(self):
            return self.chk.Value

        def nextPage(self):
            ret = 1
            if self.skipIt():
                # They checked the 'skip' box.
                ret = 2
            return ret

    class WizPageThree(WizardPage):
        def createBody(self):
            self.Caption = _("This is the third page")
            lbl = dLabel(
                self,
                Caption=_(
                    """You should only see this if you did not check
the box on Page Two.
"""
                ),
            )
            self.Sizer.append(lbl, alignment="center")

    class WizPageFour(WizardPage):
        def createBody(self):
            self.Caption = _("This is the fourth page")
            self.Picture = "cards/small/s1.png"
            lbl = dLabel(
                self,
                Caption=_(
                    """Did the skipping work OK?
"""
                ),
            )
            self.Sizer.append(lbl, alignment="center")
            self.txt = dTextBox(self)
            lbl = dLabel(self, Caption=_("You cannot move forward if this textbox is empty"))
            self.Sizer.appendSpacer(16)
            self.Sizer.append(self.txt, alignment="center")
            self.Sizer.append(lbl, alignment="center")
            lbl = dLabel(self, Caption=_("Also note that this page has a different icon!"))
            self.Sizer.appendSpacer(5)
            self.Sizer.append(lbl, alignment="center")

        def prevPage(self):
            """
            If the checkbox on the second page is checked,
            we want to skip over page three again. This demonstrates
            calling to the parent form to get references to other
            pages.
            """
            ret = -1
            pg = self.Form.getRelativePage(self, -2)
            if pg.skipIt():
                ret = -2
            return ret

        def onLeavePage(self, dir):
            ret = True
            if dir == "forward":
                if not self.txt.Value:
                    ui.stop(_("Fill in the text box!!"))
                    ret = False
            return ret

    class WizPageFive(WizardPage):
        def createBody(self):
            self.Caption = _("This is the fifth (and last) page")
            lbl = dLabel(
                self,
                Caption=_(
                    """This is the last page. Note that the 'Next' button
now reads 'Finish'. Click that to exit, or click 'Back'
to play some more.
"""
                ),
            )
            self.Sizer.append(lbl, alignment="center")

    app = dApp()
    app.MainFormClass = None
    app.setup()
    # OK, we've defined all of our pages. Now let's define
    # the wizard itself.
    wiz = Wizard(
        Picture="daboIcon096",
        Height=450,
        Width=530,
        Pages=(WizPageOne, WizPageTwo, WizPageThree, WizPageFour, WizPageFive),
    )

    wiz.start()
    app.start()
