# -*- coding: utf-8 -*-
import wx

from .. import events
from .. import ui
from ..localization import _


class dButton(ui.dControlMixin, wx.Button):
    """
    Creates a button that can be pressed by the user to trigger an action.

    Example::

        class MyButton(ui.dButton):
            def initProperties(self):
                self.Caption = "Press Me"

            def onHit(self, evt):
                self.Caption = "Press Me one more time"

    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dButton
        preClass = wx.Button
        ui.dControlMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def _initEvents(self):
        super()._initEvents()
        self.Bind(wx.EVT_BUTTON, self._onWxHit)

    def _onCancelButton(self, evt, recurse=True):
        # This callback exists for when the user presses ESC and this button
        # is the cancel button. Raise events.Hit.
        if self.VisibleOnScreen:
            self.raiseEvent(events.Hit)
        else:
            # There may be another cancel button: give it a chance, too:
            if recurse:
                otherCancelButton = self.Form.FindWindowById(wx.ID_CANCEL)
                if otherCancelButton:
                    otherCancelButton._onCancelButton(evt, recurse=False)

    # Property definitions
    @property
    def CancelButton(self):
        """Specifies whether this command button gets clicked on -Escape-."""
        return self.GetId() == wx.ID_CANCEL

    @CancelButton.setter
    def CancelButton(self, val):
        if self._constructed():
            ## pkm: We can bind the key to self, Parent, or Form (or any object).
            ##      If bound to self, the <esc> keypress will only fire the Hit
            ##      when self has the focus. If bound to self.Parent, Hit will
            ##      fire when self.Parent or any of its children has the focus.
            ##      If bound to self.Form, Hit will fire whenever <esc> is pressed.
            ##      I'm making the decision to bind it to self.Form, even though
            ##      self.Parent is also a valid choice.
            ### egl: changed the binding on OS X to the form. Parent just doesn't work.
            ### pkm: followed suit with GTK (we should test Win too).
            ### pkm: removed GTK to bind to parent because it wasn't working on the form.
            target = self.Parent
            if self.Application.Platform in ("Mac"):
                target = self.Form
            if val:
                target.bindKey("esc", self._onCancelButton)
                self.SetId(wx.ID_CANCEL)
            else:
                target.unbindKey("esc")
                self.SetId(wx.ID_ANY)
        else:
            # In order to get the stock cancel button behavior from the OS, we need
            # to set the id here. So, getting the stock button behavior must happen
            # in the constructor, but theoretically we can get the escape behavior
            # anytime.
            if val:
                self._preInitProperties["id"] = wx.ID_CANCEL
            self._properties["CancelButton"] = val

    @property
    def DefaultButton(self):
        """Specifies whether this command button gets clicked on -Enter-."""
        try:
            v = self._defaultButton
        except AttributeError:
            v = self._defaultButton = False
        return v

    @DefaultButton.setter
    def DefaultButton(self, value):
        if self._constructed():
            if value:
                # Need to unset default from any other buttons:
                for child in self.Parent.Children:
                    if child is self:
                        continue
                    try:
                        db = child.DefaultButton
                    except AttributeError:
                        db = False
                    if db:
                        child.DefaultButton = False
                # Now set it for this button
                self.SetDefault()
            else:
                # No wx-way to unset default button. Probably a rare need, anyway.
                # One idea would be to create a hidden button, set default to it,
                # and then destroy it.
                pass
            self._defaultButton = value
        else:
            self._properties["DefaultButton"] = value

    DynamicCancelButton = ui.makeDynamicProperty(CancelButton)
    DynamicDefaultButton = ui.makeDynamicProperty(DefaultButton)


ui.dButton = dButton


class _dButton_test(dButton):
    def initProperties(self):
        self.Caption = "You better not push me"
        self.FontSize = 8
        self.Width = 223

    def onContextMenu(self, evt):
        print("context menu")

    def onMouseRightClick(self, evt):
        print("right click")

    def onHit(self, evt):
        self.ForeColor = "purple"
        self.FontBold = True
        self.FontItalic = True
        self.Caption = "Ok, you cross this line, and you die."
        self.Width = 333


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dButton_test)
