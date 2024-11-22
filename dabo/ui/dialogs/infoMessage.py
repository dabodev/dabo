# -*- coding: utf-8 -*-
from ... import ui
from ...dLocalize import _
from .. import dBitmapButton
from .. import dButton
from .. import dCheckBox
from .. import dColumn
from .. import dDialog
from .. import dGrid
from .. import dLabel
from .. import dMenu
from .. import dPanel
from .. import dSizer
from .. import dStandardButtonDialog


class LblMessage(dLabel):
    def initProperties(self):
        self.WordWrap = True
        self.FontSize = 12
        self.Width = 500


class DlgInfoMessage(dStandardButtonDialog):
    def initProperties(self):
        self.AutoSize = True
        self.ShowCaption = False
        self.ShowCloseButton = False

    def addControls(self):
        vs = self.Sizer = dSizer("v", DefaultBorder=10)
        vs.append1x(LblMessage(self, RegID="lblMessage", Caption=self.Message))
        vs.append(
            dCheckBox(
                self,
                Caption=_("Show this message in the future?"),
                Value=self.DefaultShowInFuture,
                RegID="chkShowInFuture",
                FontSize=9,
            )
        )

    def _getDefaultShowInFuture(self):
        return getattr(self, "_defaultShowInFuture", True)

    def _setDefaultShowInFuture(self, val):
        self._defaultShowInFuture = bool(val)

    def _getMessage(self):
        return getattr(self, "_message", "")

    def _setMessage(self, val):
        self._message = val

    DefaultShowInFuture = property(
        _getDefaultShowInFuture,
        _setDefaultShowInFuture,
        None,
        _("Specifies whether the 'show in future' checkbox is checked by default."),
    )

    Message = property(_getMessage, _setMessage, None, _("Specifies the message to display."))


if __name__ == "__main__":
    from dabo.dApp import dApp

    app = dApp(MainFormClass=None)
    app.setup()
    dlg = DlgInfoMessage(
        None,
        Message="This is a test of the emergency broadcast system. If this were an actual "
        "emergency, you would have been given specific instructions. This is only a test.",
    )
    dlg.show()
