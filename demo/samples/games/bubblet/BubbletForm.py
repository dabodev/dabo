# -*- coding: utf-8 -*-
import time

import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dApp import dApp
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.ui import dForm

if __name__ == "__main__":
    from BubblePanel import BubblePanel
    from BubbleBizobj import BubbleBizobj
    from StatsForm import StatsForm
else:
    from .BubblePanel import BubblePanel
    from .BubbleBizobj import BubbleBizobj
    from .StatsForm import StatsForm


class BubbletForm(dForm):
    def afterInit(self):
        self.tmr = dabo.ui.dTimer()
        self.tmr.bindEvent(dEvents.Hit, self.onTimer)
        self._score = 0
        # Used to control unnecessary screen redraws
        self.noUpdate = False

        # Rows and columns
        self.rows = 7
        self.columns = 10
        bubbles = [[] for r in range(self.rows)]

        vsz = dabo.ui.dSizer("v")
        gsz = dabo.ui.dGridSizer(MaxCols=self.columns)

        for rr in range(self.rows):
            for cc in range(self.columns):
                pn = BubblePanel(self)
                pn.row = rr
                pn.col = cc
                # pn.ToolTipText = "Row %s, Col %s" % (rr,cc)
                bubbles[rr].append(pn)
                gsz.append(pn, "x")
        # Set the grid sizer to grow
        gsz.setColExpand(True, "all")
        gsz.setRowExpand(True, "all")
        vsz.append1x(gsz)

        # Add the score
        sp = self.scorePanel = dabo.ui.dPanel(self)
        sp.Sizer = hsz = dabo.ui.dSizer("h")
        label = dabo.ui.dLabel(sp, Caption=_("Score:"), FontSize=12)
        hsz.append1x(label, halign="right")
        self.scoreLabel = dabo.ui.dLabel(sp, FontSize=14, FontBold=True)
        hsz.append1x(self.scoreLabel)
        vsz.append(sp, 0, "x")

        # This should set the label, too
        self.Score = 0

        self.Sizer = vsz
        self.layout()

        biz = BubbleBizobj(None)
        biz.bubbles = bubbles
        biz.callbackFunc = self.update
        self.addBizobj(biz)

        self.Caption = "Bubblet"

        # Add the menu items
        mb = self.MenuBar
        fm = mb.fileMenu
        quitItem = mb.quitMenuItem
        quitPos = fm.getItemIndex(quitItem)
        if quitPos is None:
            quitPos = len(fm.Children)
        fm.insert(quitPos, _("&ScreenShot"), HotKey="Ctrl+S", OnHit=self.saveScreenShot)
        fm.insert(quitPos, _("&Reset Statistics"), HotKey="Ctrl+R", OnHit=self.onResetStats)
        fm.insert(quitPos, _("&Statistics"), HotKey="Ctrl+T", OnHit=self.onStats)
        fm.insertSeparator(0)
        fm.insert(0, _("&New Game"), HotKey="Ctrl+N", OnHit=self.onNewGame)

        self.unbindEvent(dEvents.Paint)
        biz.newGame()
        dabo.ui.callAfter(self.update)

    def saveScreenShot(self, evt):
        """Saves a screenshot of the current board."""
        dabo.ui.saveScreenShot(self)

    def refresh(self):
        dabo.ui.callAfterInterval(100, self._refresh)

    def _refresh(self):
        super(BubbletForm, self).refresh()

    def bubbleClick(self, bubble):
        biz = self.Bizobj
        if biz.GameOver:
            return
        self.noUpdate = True
        pts = biz.bubbleClick(bubble)
        if pts:
            self.Score += pts

        func = biz.getCallback()
        if func:
            dabo.ui.callAfter(func, self.updateBoard)
        self.StatusText = biz.Message
        self.noUpdate = False
        self.update()

        if biz.GameOver:
            dabo.ui.callAfterInterval(500, self.gameOverMsg)

    def updateBoard(self):
        self.tmr.start(100)

    def onTimer(self, evt):
        self.tmr.stop()
        self.update()
        if self.Bizobj.GameOver:
            dabo.ui.callAfterInterval(500, self.gameOverMsg)

    def gameOverMsg(self):
        msg = _("Game Over!")
        if self.Bizobj.IsNewHighGame:
            msg = _("New High Game!!")
        msg += _("\n\nYour score was %s") % self.Score
        dabo.ui.info(msg, _("Game Over"))

    def onNewGame(self, evt):
        biz = self.Bizobj
        if not biz.GameOver:
            if not dabo.ui.areYouSure(
                message=_("Are you sure you want to end this game?"),
                title=_("Game Not Over"),
                defaultNo=True,
                cancelButton=False,
            ):
                return
        biz.newGame()
        self.Score = 0
        self.update()

    def onStats(self, evt):
        biz = self.Bizobj
        num = biz.NumberOfGames
        pts = biz.TotalPoints
        high = biz.HighGame
        statsForm = StatsForm(self, Games=num, Points=pts, HighGame=high)
        statsForm.show()

    def onResetStats(self, evt):
        biz = self.Bizobj
        if biz.NumberOfGames > 0:
            if not dabo.ui.areYouSure(
                message=_("Are you sure you want to reset your statistics?"),
                title=_("Reset Statistics"),
                defaultNo=False,
                cancelButton=False,
            ):
                return
            else:
                biz.resetStats()

    def _getBizobj(self):
        return self.PrimaryBizobj

    def _getScore(self):
        return self._score

    def _setScore(self, score):
        if self._score != score:
            self._score = score
            self.scoreLabel.Caption = ustr(score)

    Bizobj = property(_getBizobj, None, None, _("Reference to the form's bizobj"))

    Score = property(_getScore, _setScore, None, _("Current score of the game.  (int)"))


if __name__ == "__main__":
    dApp(MainFormClass=BubbletForm).start()
