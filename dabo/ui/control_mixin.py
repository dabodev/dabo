# -*- coding: utf-8 -*-
import time

import wx

from . import ui
from .dLocalize import _
from .ui import events


class dControlMixin(ui.dPemMixin):
    """Provide common functionality for all controls."""

    def __onGotFocus(self, evt):
        if self.Form:
            # Grab reference to current ActiveControl
            sfac = self.Form.ActiveControl
            # Set the form's ActiveControl reference
            if sfac != self:
                # make sure prior control's value has been flushed
                self.Form.activeControlValid()
                self.Form._activeControl = self
        if self.Parent:
            self.Parent._activeControl = self

    def _initEvents(self):
        super(dControlMixin, self)._initEvents()
        self.Bind(wx.EVT_NAVIGATION_KEY, self.__onWxNavKey)
        self.bindEvent(events.GotFocus, self.__onGotFocus)

    def _onWxHit(self, evt, *args, **kwargs):
        # This is called by a good number of the controls, when the default
        # event happens, such as a click in a command button, text being
        # entered in a text control, a timer reaching its interval, etc.
        # We catch the wx event, and raise the dabo Hit event for user code
        # to work with.

        # Hide a problem on Windows toolbars where a single command event will
        # be raised up to three separate times.
        #         print "CONTROL WXHIT", self, evt
        now = time.time()
        if not hasattr(self, "_lastHitTime") or (now - self._lastHitTime) > 0.001:
            self.raiseEvent(events.Hit, evt, *args, **kwargs)
            #            print "CONTROL RAISING HIT"
            self._lastHitTime = time.time()

    def __onWxNavKey(self, evt):
        # A navigation key event has caused this control to want to
        # get the focus. Only allow it if self.TabStop is True.
        evt.Skip()
        if not self.TabStop:
            ui.callAfter(self.Navigate, evt.GetDirection())

    def _getTabStop(self):
        return getattr(self, "_tabStop", True)

    def _setTabStop(self, val):
        assert isinstance(val, bool)
        self._tabStop = val

    TabStop = property(
        _getTabStop,
        _setTabStop,
        None,
        _("Specifies whether this control can receive focus from keyboard navigation."),
    )


ui.dControlMixin = dControlMixin
