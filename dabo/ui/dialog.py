# -*- coding: utf-8 -*-
import warnings

import wx

from .. import constants
from .. import events
from .. import ui
from ..localization import _
from . import dButton
from . import dCheckBox
from . import dDropdownList
from . import dFormMixin
from . import dGridSizer
from . import dLabel
from . import dSizer
from . import dSpinner
from . import dTextBox
from . import makeDynamicProperty


class dDialog(dFormMixin, wx.Dialog):
    """
    Creates a dialog, which is a lightweight form.

    Dialogs are like forms, but typically are modal and are requesting a very
    specific piece of information from the user, and/or offering specific
    information to the user.
    """

    def __init__(self, parent=None, properties=None, *args, **kwargs):
        self._baseClass = dDialog
        self._modal = True
        self._centered = True
        self._fit = True
        self._borderless = self._extractKey((properties, kwargs), "Borderless", False)

        if self._borderless:
            defaultStyle = wx.STAY_ON_TOP
        else:
            defaultStyle = wx.DEFAULT_DIALOG_STYLE
        try:
            kwargs["style"] = kwargs["style"] | defaultStyle
        except KeyError:
            kwargs["style"] = defaultStyle

        preClass = wx.Dialog
        dFormMixin.__init__(self, preClass, parent, properties=properties, *args, **kwargs)

        # Hook method, so that we add the buttons last
        self._addControls()

        # Needed starting with wx 2.7, for the first control to have the focus:
        self.setFocus()

    def getBizobj(self, *args, **kwargs):
        ## self.Form resolves to the containing dialog, making calls to 'self.Form.getBizobj()'
        ## fail since the dialog knows nothing about bizobjs. Let's be helpful and pass the
        ## request up to the form:
        return self.Form.getBizobj(*args, **kwargs)

    def EndModal(self, *args, **kwargs):
        self.saveSizeAndPosition()
        # JFCS 6/11/20 self.hide() causes the self.IsModal() == False which is wrong.
        # isItModal = self.IsModal()
        # self.Hide()
        # if self.Modal:  #this uses the property of the Dabo dialog
        # if self.IsModal:  #this uses the wx.IsModal that checks the dialog.
        # I believe either is required because the call is to end a modal dialog
        # if it fails no harm.
        # EGL 2025-05-09: IsModal() was failing to release Wizard dialogs. Checking for both fixes
        # that problem.
        if self.Modal or self.IsModal():
            try:
                super().EndModal(*args, **kwargs)
            except wx._core.PyAssertionError:
                # The modal hack is causing problems in some edge cases.
                super().release()

    def _afterInit(self):
        self.MenuBarClass = None
        self.Sizer = dSizer("V")
        super()._afterInit()

    def ShowModal(self):
        self.restoreSizeAndPositionIfNeeded()
        # updates were potentially suppressed while the dialog
        # wasn't visible, so update now.
        self.update()
        return super().ShowModal()

    def showModal(self):
        """Show the dialog modally."""
        ## pkm: We had to override this, because the default in dPemMixin doesn't
        ##      actually result in a modal dialog.
        self.Modal = True
        self.show()

    def showModeless(self):
        """Show the dialog non-modally."""
        self.Modal = False
        self.show()

    def _afterShow(self):
        if self.AutoSize:
            self.Fit()
        if self.Centered:
            self.Centre()

    def show(self):
        # Call _afterShow() once immediately, and then once after the dialog is visible, which
        # will correct minor mistakes such as the height of wordwrapped labels not being
        # accounted for. If we only called it after the dialog was already shown, then we
        # risk the dialog being too jumpy.
        self._afterShow()
        ui.callAfter(self._afterShow)
        if self.Modal:
            ret = self.ShowModal()
            return {wx.ID_OK: constants.DLG_OK, wx.ID_CANCEL: constants.DLG_CANCEL}.get(ret, ret)
        return self.Show(True)

    def _addControls(self):
        """
        Any controls that need to be added to the dialog
        can be added in this method in framework classes, or
        in addControls() in instances.
        """
        self.beforeAddControls()
        self.addControls()
        self.afterAddControls()

    def beforeAddControls(self):
        """This is a hook, called at the appropriate time by the framework."""
        pass

    def afterAddControls(self):
        """This is a hook, called at the appropriate time by the framework."""
        pass

    def addControls(self):
        """
        Add your custom controls to the dialog.

        This is a hook, called at the appropriate time by the framework.
        """
        pass

    def release(self):
        """
        Need to augment this to make sure the dialog
        is removed from the app's forms collection.
        """
        if self.Application is not None:
            self.Application.uiForms.remove(self)
        super().release()

    def _controlGotFocus(self, ctrl):
        # Placeholder until we unify dForm and dDialog
        pass

    # Property definitions
    @property
    def AutoSize(self):
        """When True, the dialog resizes to fit the added controls.  (bool)"""
        return self._fit

    @AutoSize.setter
    def AutoSize(self, val):
        self._fit = val

    @property
    def Borderless(self):
        """
        Must be passed at construction time. When set to True, the dialog displays without a title
        bar or borders  (bool)
        """
        return self._borderless

    @Borderless.setter
    def Borderless(self, val):
        if self._constructed():
            raise ValueError(_("Cannot set the Borderless property once the dialog is created."))
        else:
            self._properties["Borderless"] = val

    @property
    def Caption(self):
        """The text that appears in the dialog's title bar  (str)"""
        return self.GetTitle()

    @Caption.setter
    def Caption(self, val):
        if self._constructed():
            self.SetTitle(val)
        else:
            self._properties["Caption"] = val

    @property
    def Centered(self):
        """Determines if the dialog is displayed centered on the screen.  (bool)"""
        return self._centered

    @Centered.setter
    def Centered(self, val):
        self._centered = val

    @property
    def Modal(self):
        """Determines if the dialog is shown modal (default) or modeless.  (bool)"""
        return self._modal

    @Modal.setter
    def Modal(self, val):
        self._modal = val

    @property
    def ShowStatusBar(self):
        """Dialogs cannot have status bars, so return False"""
        return False

    DynamicAutoSize = makeDynamicProperty(AutoSize)
    DynamicCaption = makeDynamicProperty(Caption)
    DynamicCentered = makeDynamicProperty(Centered)


class dStandardButtonDialog(dDialog):
    """
    Creates a dialog with standard buttons and associated functionality. You can
    choose the buttons that display by passing True for any of the following
    properties:

        OK
        Cancel
        Yes
        No
        Help

    If you don't specify buttons, only the OK will be included; if you do specify buttons,
    you must specify them all; in other words, OK is only assumed if nothing is specified.
    Then add your custom controls in the addControls() hook method, and respond to
    the pressing of the standard buttons in the run*() handlers, where * is the name of the
    associated property (e.g., runOK(), runNo(), etc.). You can query the Accepted property
    to find out if the user pressed "OK" or "Yes"; if neither of these was pressed,
    Accepted will be False.
    """

    def __init__(self, parent=None, properties=None, *args, **kwargs):
        self._ok = self._extractKey((properties, kwargs), "OK")
        self._cancel = self._extractKey((properties, kwargs), "Cancel")
        self._yes = self._extractKey((properties, kwargs), "Yes")
        self._no = self._extractKey((properties, kwargs), "No")
        self._help = self._extractKey((properties, kwargs), "Help")
        # Check for both OK and Yes. This simply does not work, at least with wxPython.
        if self._ok and self._yes:
            raise ValueError(_("Dialogs cannot have both 'OK' and 'Yes' buttons."))
        self._cancelOnEscape = True
        super().__init__(parent=parent, properties=properties, *args, **kwargs)
        self._baseClass = dStandardButtonDialog
        self._accepted = False

    def _addControls(self):
        # By default, don't intercept the esc key.
        self.setEscapeButton(None)

        # Set some default Sizer properties (user can easily override):
        sz = self.Sizer
        sz.DefaultBorder = 20
        sz.DefaultBorderLeft = sz.DefaultBorderRight = True
        sz.append((0, sz.DefaultBorder))

        # Add the specified buttons. If none were specified, then just add OK
        ok = self._ok
        cancel = self._cancel
        yes = self._yes
        no = self._no
        help = self._help
        if ok is None and cancel is None and yes is None and no is None and help is None:
            ok = True

        flags = 0
        if ok:
            flags = flags | wx.OK
        if cancel:
            flags = flags | wx.CANCEL
        if yes:
            flags = flags | wx.YES
        if no:
            flags = flags | wx.NO
        if help:
            flags = flags | wx.HELP
        if flags == 0:
            # Nothing specified; default to just OK
            flags = wx.OK
        # Initialize the button references
        self.btnOK = self.btnCancel = self.btnYes = self.btnNo = self.btnHelp = None

        # We need a Dabo sizer to wrap the wx sizer.
        self.stdButtonSizer = dSizer()
        sbs = self.CreateButtonSizer(flags)
        self.stdButtonSizer.append1x(sbs)

        btns = [b.GetWindow() for b in sbs.GetChildren() if b.IsWindow()]
        for btn in btns:
            id_ = btn.GetId()
            if id_ == wx.ID_YES:
                self.btnYes = newbtn = dButton(btn.Parent)
                mthd = self._onYes
            elif id_ == wx.ID_NO:
                self.btnNo = newbtn = dButton(btn.Parent)
                mthd = self._onNo
            elif id_ == wx.ID_OK:
                self.btnOK = newbtn = dButton(btn.Parent)
                mthd = self._onOK
            elif id_ == wx.ID_CANCEL:
                self.btnCancel = newbtn = dButton(btn.Parent)
                mthd = self._onCancel
            elif id_ == wx.ID_HELP:
                self.btnHelp = btn
                newbtn = None
                mthd = self._onHelp
            if newbtn is None:
                # Only the Help button cannot be wrapped, as it is platform-specific in appearance.
                btn.Bind(wx.EVT_BUTTON, mthd)
            else:
                newbtn.Caption = btn.GetLabel()
                pos = ui.getPositionInSizer(btn)
                sz = btn.GetContainingSizer()
                sz.Replace(btn, newbtn)
                btn.Destroy()
                newbtn.bindEvent(events.Hit, mthd)
        if ok:
            self.OKButton.DefaultButton = True
        elif yes:
            self.YesButton.DefaultButton = True

        # Force the escape button to be set appropriately:
        self.CancelOnEscape = self.CancelOnEscape

        # Wx rearranges the order of the buttons per platform conventions, but
        # doesn't rearrange the tab order for us. So, we do it manually:
        buttons = []
        for child in sbs.GetChildren():
            win = child.GetWindow()
            if win is not None:
                buttons.append(win)
        for pos, btn in enumerate(buttons[1:]):
            btn.MoveAfterInTabOrder(buttons[pos - 1])

        # Let the user add their controls
        super()._addControls()

        # Just in case user changed Self.Sizer, update our reference:
        sz = self.Sizer
        if self.ButtonSizerPosition is None:
            # User code didn't add it, so we must.
            if sz.DefaultBorder:
                spacer = sz.DefaultBorder
            else:
                spacer = 10
            bs = dSizer("v")
            bs.append((0, spacer / 2))
            bs.append(self.ButtonSizer, "x")
            bs.append((0, spacer))
            sz.append(bs, "x")
        self.layout()

    def setEscapeButton(self, btn=None):
        """
        Set which button gets hit when Esc pressed.

        CancelOnEscape must be True for this to work.
        """
        if not self.CancelOnEscape or not btn:
            self.SetEscapeId(wx.ID_NONE)
        else:
            self.SetEscapeId(btn.GetId())

    ################################################
    #    Handlers for the standard buttons.
    ################################################
    # Note that onOK() and
    # onCancel() are the names of the old event handlers, and
    # code has been written to use these. So as not to break this
    # older code, we issue a deprecation warning and call the
    # old handler.
    def _onOK(self, evt):
        self.Accepted = True
        self.activeControlValid()
        try:
            self.onOK()
        except TypeError:
            warnings.warn(
                _("The onOK() handler is deprecated. Use the runOK() method instead"),
                Warning,
            )
            self.onOK(None)
        except AttributeError:
            # New code should not have onOK
            pass
        if self.runOK() is not False:
            if self.Modal or self.IsModal():
                self.EndModal(constants.DLG_OK)
            else:
                self.release()

    def _onCancel(self, evt):
        self.Accepted = False
        self.activeControlValid()
        try:
            self.onCancel()
        except TypeError:
            warnings.warn(
                _("The onCancel() handler is deprecated. Use the runCancel() method instead"),
                Warning,
            )
            self.onCancel(None)
        except AttributeError:
            # New code should not have onCancel
            pass

        if self.runCancel() is not False:
            self.EndModal(constants.DLG_CANCEL)
        else:
            evt.stop()

    def _onYes(self, evt):
        self.Accepted = True
        if self.runYes() is not False:
            self.EndModal(constants.DLG_YES)

    def _onNo(self, evt):
        self.Accepted = False
        if self.runNo() is not False:
            self.EndModal(constants.DLG_NO)
        else:
            evt.stop()

    def _onHelp(self, evt):
        self.runHelp()

    # The following are stub methods that can be overridden when needed.
    def runOK(self):
        pass

    def runCancel(self):
        pass

    def runYes(self):
        pass

    def runNo(self):
        pass

    def runHelp(self):
        pass

    ################################################

    def addControls(self):
        """
        Use this method to add controls to the dialog. The standard buttons will be added
        after this method runs, so that they appear at the bottom of the dialog.
        """
        pass

    def addControlSequence(self, seq):
        """
        This takes a sequence of 3-tuples or 3-lists, and adds controls
        to the dialog as a grid of labels and data controls. The first element of
        the list/tuple is the prompt, the second is the data type, and the third
        is the RegID used to retrieve the entered value.
        """
        gs = dGridSizer(HGap=5, VGap=8, MaxCols=2)
        for prmpt, typ, rid in seq:
            chc = None
            gs.append(dLabel(self, Caption=prmpt), halign="right")
            if typ in (int, int):
                cls = dSpinner
            elif typ is bool:
                cls = dCheckBox
            elif isinstance(typ, list):
                cls = dDropdownList
                chc = typ
            else:
                cls = dTextBox
            ctl = cls(self, RegID=rid)
            gs.append(ctl)
            if chc:
                ctl.Choices = chc
        gs.setColExpand(True, 1)
        self.Sizer.insert(self.LastPositionInSizer, gs, "x")
        self.layout()

    @property
    def Accepted(self):
        """Specifies whether the user accepted the dialog, or canceled.  (bool)"""
        return self._accepted

    @Accepted.setter
    def Accepted(self, val):
        self._accepted = val

    @property
    def ButtonSizer(self):
        return getattr(self, "stdButtonSizer", None)

    """Returns a reference to the sizer controlling the Ok/Cancel buttons.  (dSizer)"""

    @property
    def ButtonSizerPosition(self):
        """Returns the position of the Ok/Cancel buttons in the sizer.  (int)"""
        return self.ButtonSizer.getPositionInSizer()

    @property
    def CancelButton(self):
        """Reference to the Cancel button on the form, if present  (dButton or None)."""
        return self.btnCancel

    @property
    def CancelOnEscape(self):
        """
        When True (default), pressing the Escape key will perform the same action as clicking the
        Cancel button. If no Cancel button is present but there is a No button, the No behavior will
        be executed. If neither button is present, the default button's action will be executed
        (bool)
        """
        return self._cancelOnEscape

    @CancelOnEscape.setter
    def CancelOnEscape(self, val):
        if self._constructed():
            self._cancelOnEscape = val
            self.setEscapeButton(None)
            if val:
                for trial in (self.btnCancel, self.btnNo):
                    if trial is not None:
                        self.setEscapeButton(trial)
                        break
        else:
            self._properties["CancelOnEscape"] = val

    @property
    def HelpButton(self):
        """Reference to the Help button on the form, if present  (dButton or None)."""
        return self.btnHelp

    @property
    def NoButton(self):
        """Reference to the No button on the form, if present  (dButton or None)."""
        return self.btnNo

    @property
    def OKButton(self):
        """Reference to the OK button on the form, if present  (dButton or None)."""
        return self.btnOK

    @property
    def YesButton(self):
        """Reference to the Yes button on the form, if present  (dButton or None)."""
        return self.btnYes


class dOkCancelDialog(dStandardButtonDialog):
    def __init__(self, parent=None, properties=None, *args, **kwargs):
        kwargs["Yes"] = kwargs["No"] = False
        kwargs["OK"] = kwargs["Cancel"] = True
        super().__init__(parent, properties, *args, **kwargs)
        self._baseClass = dOkCancelDialog


class dYesNoDialog(dStandardButtonDialog):
    def __init__(self, parent=None, properties=None, *args, **kwargs):
        kwargs["Yes"] = kwargs["No"] = True
        kwargs["OK"] = kwargs["Cancel"] = False
        super().__init__(parent, properties, *args, **kwargs)
        self._baseClass = dYesNoDialog


class FloatDialog(dDialog):
    def __init__(self, owner, *args, **kwargs):
        self._above = None
        self._owner = None
        kwargs["Borderless"] = True
        kwargs["FloatOnParent"] = True
        super().__init__(*args, **kwargs)

    def clear(self):
        """Releases any controls remaining from a previous usage."""
        self.Sizer.clear(True)

    def show(self):
        # position by owner
        if self.Owner is None:
            self.Centered = True
        else:
            self.Centered = None
            left, top = self.Owner.absoluteCoordinates()
            self.Left = left
            if self.Above:
                self.Bottom = top
            else:
                self.Top = top + self.Owner.Height
        # Make sure that we're within the display limits
        maxW, maxH = ui.getDisplaySize()
        self.Left = max(5, self.Left)
        self.Top = max(5, self.Top)
        self.Right = min(self.Right, maxW - 5)
        self.Bottom = min(self.Bottom, maxH - 5)
        ui.callAfterInterval(10, self._resetPosition, self.Position)
        super().show()

    def _resetPosition(self, pos):
        """
        On gtk at least, something in wxPython sets Position to centered
        otherwise.
        """
        self.Position = pos

    @property
    def Above(self):
        return self._above

    @Above.setter
    def Above(self, val):
        """Is this dialog positioned above its owner? Default=False  (bool)"""
        if self._constructed():
            self._above = val
        else:
            self._properties["Above"] = val

    @property
    def Owner(self):
        """Control which is currently managing this window.  (varies)"""
        return self._owner

    @Owner.setter
    def Owner(self, val):
        if self._constructed():
            self._owner = val
        else:
            self._properties["Owner"] = val


ui.dDialog = dDialog
ui.dStandardButtonDialog = dStandardButtonDialog
ui.dOkCancelDialog = dOkCancelDialog
ui.dYesNoDialog = dYesNoDialog


if __name__ == "__main__":
    from . import test

    test.Test().runTest(dDialog)
    test.Test().runTest(dStandardButtonDialog)
    test.Test().runTest(dOkCancelDialog)
    test.Test().runTest(dYesNoDialog)
