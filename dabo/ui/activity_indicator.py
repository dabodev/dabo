# -*- coding: utf-8 -*-
import wx

from .. import settings
from .. import ui
from ..localization import _
from . import dPemMixin
from . import makeDynamicProperty

dabo_module = settings.get_dabo_package()


class dActivityIndicator(dPemMixin, wx.ActivityIndicator):
    """
    Creates a widget that is used to indicate that the app is doing something instead of frozen.
    """

    def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
        self._baseClass = dActivityIndicator

        preClass = wx.ActivityIndicator
        dPemMixin.__init__(
            self,
            preClass,
            parent,
            properties=properties,
            attProperties=attProperties,
            *args,
            **kwargs,
        )

    def _afterInit(self):
        super()._afterInit()
        self.start()

    def start(self):
        self.Start()

    def stop(self):
        self.Stop()

    def toggle(self):
        if self.Running:
            self.stop()
        else:
            self.start()

    # Property definitions
    @property
    def Running(self):
        """
        This will be True when the control's display is running, and False when not. Setting it will
        either start or stop the indicator's activity.  (bool)
        """
        return self.IsRunning()

    @Running.setter
    def Running(self, val):
        if self._constructed():
            self.Start() if val else self.Stop()
        else:
            self._properties["Running"] = val


ui.dActivityIndicator = dActivityIndicator


class _dActivityIndicator_test(dActivityIndicator):
    def afterInit(self):
        pnl = self.Parent
        self.btn = ui.dButton(pnl, Caption="Stop", OnHit=self._toggle)
        pnl.Sizer.append(self.btn, border=20)
        self.Size = (50, 50)
        self.Position = (100, 150)

    def _toggle(self, evt):
        if self.Running:
            self.stop()
            self.btn.Caption = "Start"
        else:
            self.start()
            self.btn.Caption = "Stop"


if __name__ == "__main__":
    from . import test

    test.Test().runTest(_dActivityIndicator_test, obj_proportion=0, obj_expand=False)
