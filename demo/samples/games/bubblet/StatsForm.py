# -*- coding: utf-8 -*-
import dabo
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.ui import dDialog


class StatsForm(dDialog):
    def beforeInit(self):
        self._games = 0
        self._highGame = 0
        self._points = 0

    def addControls(self):
        self.Caption = "Bubblet Statistics"
        self.Centered = True
        self.Sizer.DefaultBorder = 20
        self.Sizer.DefaultBorderAll = True
        sz = dabo.ui.dGridSizer(MaxCols=2, VGap=8, HGap=4)
        self.Sizer.append1x(sz)

        lb = dabo.ui.dLabel(self, Caption="Number of Games:", FontSize=16, ForeColor=(0, 0, 128))
        sz.append(lb, halign="right")
        lb = dabo.ui.dLabel(self, Caption=ustr(self.Games), FontSize=16)
        sz.append(lb, halign="left")

        lb = dabo.ui.dLabel(self, Caption="Average:", FontSize=16, ForeColor=(0, 0, 128))
        sz.append(lb, halign="right")
        if self.Games > 0:
            avg = ustr(round((float(self.Points) / self.Games), 4))
        else:
            avg = 0
        lb = dabo.ui.dLabel(self, Caption=ustr(avg), FontSize=16)
        sz.append(lb, halign="left")

        lb = dabo.ui.dLabel(self, Caption="High Game:", FontSize=16, ForeColor=(0, 0, 128))
        sz.append(lb, halign="right")
        lb = dabo.ui.dLabel(self, Caption=ustr(self.HighGame), FontSize=16)
        sz.append(lb, halign="left")

        # OK, that does it for the display fields. Now add an OK button
        btn = dabo.ui.dButton(self, Caption="OK", RegID="btnOK", DefaultButton=True)
        # Add a spacer
        self.Sizer.appendSpacer(10)
        # Add the button
        self.Sizer.append(btn, halign="right")

        self.layout()

    def onHit_btnOK(self, evt):
        self.release()

    def _getGames(self):
        return self._games

    def _setGames(self, val):
        self._games = val

    def _getHighGame(self):
        return self._highGame

    def _setHighGame(self, val):
        self._highGame = val

    def _getPoints(self):
        return self._points

    def _setPoints(self, val):
        self._points = val

    Games = property(_getGames, _setGames, None, _("Number of games played  (int)"))

    HighGame = property(_getHighGame, _setHighGame, None, _("High score  (int)"))

    Points = property(_getPoints, _setPoints, None, _("Total points scored  (int)"))
