#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Dabo Minesweeper

How To Play

Use your mouse button to clear a square. If the square was a mine,
you lose. Otherwise, a number will appear telling you how many
adjacent squares have mines. Use your right mouse button (Linux and
Windows) or Control+Click (Mac) to mark a square. Successive clicks
will change the mark from a '@' (flagged as a mine), to a '?' (a
helpful marker for your own use in solving the puzzle) and then
back to a blank square (ready to clear).

You win when all squares are either flagged as mines or cleared.
"""

import datetime
import random

import dabo
import dabo.db
import dabo.biz
import dabo.ui
import dabo.lib.StopWatch as StopWatch
from dabo.dApp import dApp
from dabo.dLocalize import _
from dabo.lib.utils import ustr
import dabo.dEvents as dEvents

# import dabo.lib.datanav as datanav
from dabo.lib import specParser

from dabo.ui import dPanel
from dabo.ui import dForm


# Dabo MineSweeper
# This is a demo of Dabo's UI - no bizobj or database layer.
#
# Begun 10/22/2004 while I was waiting for a program to compile.
# I wanted to see how useful dEditor was, so I developed minesweeper
# completely with dEditor. It isn't finished, but is playable. The
# code needs to be cleaned/refactored in places. But it does use the
# Dabo UI exclusively.
#
# My idea is to make a network-playable "battle minesweeper" where 2 or
# more users can play the same puzzle and see who can finish first. Each
# user's form would show how many mines their opponent has cleared.
#
# Another idea is to make a network "team minesweeper" where 2 or more
# players can collaborate on clearing the same minefield. Each user's
# minefield would get updated as other players flag mines and clear
# squares.
#
# Perhaps the high-scores can be recorded using a database/bizobj just
# to stay relevant with the Dabo project. <g>
#
# Anyway, this is also a good test for Dabo's performance, as each square
# is a dButton: make a 20x20 grid and all of a sudden you are
# instantiating 400 dButtons, each responding to mouse clicks.
#
# (if someone really wants to speed it up, I'd suggest using a DC to draw
# directly on the panel, and divining the current square based on the
# position of the mouse click).
#
# pkm

# Good games: 20x15, 36

_defaultBoardSize = (12, 8)
_defaultMineCount = 15
_mineMarkChar = "@"
_questionMarkChar = "?"
_squareBorder = 1
_timerInterval = 500

_mineMarkerColor = "orange"
_questionColor = "yellow"
_hintColor = "black"


class StateChanged(dabo.dEvents.Event):
    pass


class Square(dPanel):
    def initProperties(self):
        self.BackColor = "slategrey"

    def afterInit(self):
        self.image = self.drawText("", fontSize=14, x=3)
        self.image.DynamicText = self.getSquareText
        self.image.DynamicFontSize = self.Parent.getFontSize
        self.image.DynamicForeColor = self.getForeColor

    def getForeColor(self):
        return {
            "UnMarked": _hintColor,
            "MarkedMine": _mineMarkerColor,
            "QuestionMarked": _questionColor,
            "Cleared": _hintColor,
        }[self.State]

    def getSquareText(self):
        txt = self.image.Text
        if txt in (_questionMarkChar, _mineMarkChar) and (self.State == "UnMarked"):
            ret = ""
        else:
            ret = {
                "UnMarked": txt,
                "MarkedMine": _mineMarkChar,
                "QuestionMarked": _questionMarkChar,
                "Cleared": "",
            }[self.State]
        return ret

    def cycleState(self):
        orig = self.State
        if orig == "UnMarked":
            self.State = "MarkedMine"
        elif orig == "MarkedMine":
            self.State = "QuestionMarked"
        elif orig == "QuestionMarked":
            self.State = "UnMarked"
        else:
            # self.State = "Cleared"
            pass
        if orig != self.State:
            self.ClearBackground()
            self.update()
            self.refresh()

    def onResize(self, evt):
        self.autoClearDrawings = self.Application.Platform.lower() == "win"
        self.update()
        self.autoClearDrawings = False
        if self.image.Text:
            self.centerText()

    def reset(self):
        self.lockDisplay()
        self.image.Text = ""
        self.Visible = True
        self.Enabled = True
        self.FontBold = False
        self.FontItalic = False
        self._state = "UnMarked"
        self.autoClearDrawings = self.Application.Platform.lower() == "win"
        self._redraw()
        self.autoClearDrawings = False
        self.unlockDisplay()

    def centerText(self):
        wd = dabo.ui.fontMetricFromDrawObject(self.image)[0]
        if wd != 0:
            self.image.Xpos = max(1, int((self.Width - wd) / 2))
        ht = dabo.ui.fontMetricFromDrawObject(self.image)[1]
        if ht != 0:
            self.image.Ypos = max(1, int((self.Height - ht) / 2))

    def _getState(self):
        """Returns one of: 'UnMarked', 'MarkedMine', 'QuestionMarked', 'Cleared'"""
        try:
            state = self._state
        except AttributeError:
            state = self._state = "UnMarked"
        return state

    def _setState(self, val):
        """Sets State to one of:

            + "UnMarked"
            + "MarkedMine"
            + "QuestionMarked"
            + "Cleared"

        Side Effects:
            + Caption set to one of "", <mineMarkChar ("@")>, "?"
            + Raises StateChanged event
        """
        if val != self.State:
            self._state = val
            self.update()
            self.raiseEvent(StateChanged)

    def _getCaption(self):
        try:
            v = self.image.Text
        except AttributeError:
            v = self.image.Text = ""
        return v

    def _setCaption(self, val):
        self.image.Text = val
        self.centerText()
        self.refresh()

    Caption = property(_getCaption, _setCaption)

    State = property(_getState, _setState, None, "")


class Board(dPanel):
    def initProperties(self):
        self.squares = []
        self._resetting = False
        self.BackColor = "khaki"
        self.needResize = False
        self._squareFontSize = 12
        self._filledSize = (0, 0)

    def onResize(self, evt):
        self.needResize = True

    def onIdle(self, evt):
        if not self.needResize or not self.Sizer:
            return
        self.lockDisplay()
        self.needResize = False
        cols, rows = self.BoardSize
        wd, ht = self.Size
        hgap = self.Sizer.HGap
        vgap = self.Sizer.VGap
        wd = wd - ((cols - 1) * (hgap + (2 * _squareBorder)))
        ht = ht - ((rows - 1) * (vgap + (2 * _squareBorder)))
        maxSqWd = wd / float(cols)
        maxSqHt = ht / float(rows)
        dim = min(maxSqWd, maxSqHt)
        self._squareFontSize = self.calcFontSize(dim)
        self.setAll("Size", (dim, dim), "__class__ is Square")
        self.layout()
        self.unlockDisplay()

    def getFontSize(self):
        return self._squareFontSize

    def calcFontSize(self, sz):
        try:
            img = self.square_0_0.image
        except AttributeError:
            # Squares haven't been created yet
            return self._squareFontSize
        fs = img.FontSize
        tolerance = 7
        if sz == 0:
            # Object isn't finished sizing yet.
            return fs
        while True:
            fm = dabo.ui.fontMetric(
                txt="M",
                face=img.FontFace,
                size=fs,
                bold=img.FontBold,
                italic=img.FontItalic,
            )
            maxFont = max(fm)
            diff = sz - maxFont
            if maxFont > sz:
                # Too big
                fs -= 1
            elif diff < tolerance:
                break
            else:
                fs += tolerance
        return fs

    def newGame(self):
        sw = StopWatch.StopWatch()
        sw.start()
        self._firstHit = True
        self._makeBoardDict()
        if not self._filledSize == self.BoardSize:
            self.lockDisplay()
            self._fillBoard()
            self.layout()
            self.unlockDisplay()
        else:
            self._resetBoard()
        sw.stop()
        print("Board created in %f second(s)." % (sw.Value,))
        self._GameInProgress = True
        self._MinesRemaining = self.MineCount

    def _resetBoard(self):
        self._resetting = True
        for sq in self.squares:
            sq.reset()
            self._boardDict[sq.square]["obj"] = sq
        self._resetting = False

    def onSquareHit(self, evt):
        o = evt.EventObject
        if o.Caption not in ("@", "?"):
            # if the user has marked the square, don't detonate: it could have
            # been a mistake.
            self.showSquare(o.square)
            self.checkWin()

    def checkWin(self):
        """See if the player has won the game."""
        if self._GameInProgress:
            self.StopWatch.start()
        check = True
        if self.allCleared():
            for sq in list(self._boardDict.keys()):
                square = self._boardDict[sq]
                if square["mine"]:
                    if square["obj"].Caption == "@":
                        pass
                    else:
                        check = False
                        break
            if check:
                self._GameInProgress = False
                self.Form.StatusText = (
                    "You win!!! Picture fireworks bursting in air, in your honor!"
                )
                self.Form.recordScore()

    #                 info("You win!")

    def allCleared(self):
        """Return True if all non-mine squares have been cleared."""
        bd = self._boardDict
        for sq in list(bd.keys()):
            square = bd[sq]
            if not square["mine"]:
                if (
                    (square["adjacent"] == 0 and square["obj"].Visible == False)
                    or square["adjacent"] > 0
                    and square["obj"].Enabled == False
                ):
                    pass
                else:
                    return False
        return True

    def onContextMenu(self, evt):
        # stop the event from propagating, so that the click isn't processed (Mac):
        evt.stop()
        o = evt.EventObject
        if o != self and self._GameInProgress and o.Enabled:
            o.cycleState()

    def showSquare(self, square):
        i = self._boardDict[square]
        o = i["obj"]
        o.State = "UnMarked"
        if i["mine"]:
            if self._firstHit:
                # Don't blow them up on their first click.
                self._makeBoardDict()
                self._resetBoard()
                self.showSquare(square)
                return
            o.FontBold = True
            o.FontItalic = True
            self.showAllSquares()
            self._GameInProgress = False
            #            dabo.ui.stop("You lose!")
            self.Form.StatusText = "KaBoom!"
        else:
            a = i["adjacent"]
            if a == 0:
                # recursively clear all adjacent 0 squares
                self.clearZeros(o.square)
            else:
                o.Caption = ustr(a)
                o.Enabled = False
        o.unbindEvent(dabo.dEvents.Hit)
        self._firstHit = False

    def showAllSquares(self):
        bd = self._boardDict
        for sq in list(bd.keys()):
            o = bd[sq]["obj"]
            o.State = "UnMarked"
            if bd[sq]["mine"]:
                o.Caption = "M"
                o.FontItalic = True
                o.FontBold = True
                o.Enabled = False
            elif bd[sq]["adjacent"] == 0:
                o.Visible = False
            else:
                o.Caption = ustr(bd[sq]["adjacent"])
                o.Enabled = False

    def clearZeros(self, square):
        bd = self._boardDict
        if bd[square]["adjacent"] == 0:
            bd[square]["obj"].Visible = False
            for sq in self.getAdjacentSquares(square):
                if bd[sq]["adjacent"] == 0 and bd[sq]["mine"] == False and bd[sq]["obj"].Visible:
                    bd[sq]["obj"].Visible = False
                    self.clearZeros(sq)
                else:
                    if bd[sq]["obj"].Visible and bd[sq]["adjacent"] > 0:
                        bd[sq]["obj"].Caption = ustr(bd[sq]["adjacent"])
                        bd[sq]["obj"].State = "UnMarked"
                        bd[sq]["obj"].Enabled = False

    def _makeBoardDict(self):
        self._boardDict = {}
        width = self.BoardSize[0]
        height = self.BoardSize[1]
        for h in range(height):
            for w in range(width):
                self._boardDict[(w, h)] = {"mine": False, "flag": False, "adjacent": 0}
        self._fillMines()
        self._fillAdjacentCounts()

    def _fillMines(self):
        r = random.Random()
        r.seed()
        bc = self.MineCount
        squares = list(self._boardDict.keys())
        if bc > len(squares):
            bc = self.MineCount = len(squares)
        mines = random.sample(squares, bc)
        for mine in mines:
            self._boardDict[mine]["mine"] = True

    def _fillAdjacentCounts(self):
        for key in list(self._boardDict.keys()):
            adj = self.getAdjacentSquares(key)
            c = 0
            for s in adj:
                if self._boardDict[s]["mine"]:
                    c += 1
            self._boardDict[key]["adjacent"] = c

    def _fillBoard(self):
        cols = self.BoardSize[0]
        rows = self.BoardSize[1]
        sizer = dabo.ui.dGridSizer(HGap=0, VGap=0)

        sw = StopWatch.StopWatch()
        sw.start()

        # Release any existing squares
        [sq.release() for sq in self.squares]
        self.squares = []

        old_fastNameSet = dabo.fastNameSet
        dabo.fastNameSet = True
        for row in range(rows):
            for col in range(cols):
                o = self.addObject(Square, "square_%s_%s" % (col, row))
                o.square = (col, row)
                self._boardDict[(col, row)]["obj"] = o
                o.bindEvent(dabo.dEvents.MouseLeftClick, self.onSquareHit)
                o.bindEvent(dabo.dEvents.ContextMenu, self.onContextMenu)
                o.bindEvent(StateChanged, self.onStateChanged)
                sizer.append(o, row=row, col=col, border=_squareBorder)
                self.squares.append(o)
        dabo.fastNameSet = old_fastNameSet
        self._filledSize = self.BoardSize
        self.Sizer = sizer
        self.needResize = True

        sw.stop()
        print("\n\nTime creating squares:", sw.Value)

    def onStateChanged(self, evt):
        if self._resetting:
            return
        o = evt.EventObject
        if o.State == "MarkedMine":
            self._MinesRemaining -= 1
        elif o.State == "QuestionMarked":
            # this is the next state after MarkedMine
            self._MinesRemaining += 1
        self.checkWin()

    def getAdjacentSquares(self, square):
        row, col = square[1], square[0]
        adj = []
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                r = j + row
                c = i + col
                if (
                    r >= 0
                    and r < self.BoardSize[1]
                    and c >= 0
                    and c < self.BoardSize[0]
                    and (c, r) != square
                ):
                    adj.append((c, r))
        return tuple(adj)

    def onTimer(self, evt):
        self.Form.pausebutton.Caption = "%s sec." % int(round(self.StopWatch.Value))

    def _getBoardSize(self):
        try:
            bs = self._boardSize
        except AttributeError:
            bs = (0, 0)
        if 0 in bs:
            # Can't allow zero-dimension boards.
            pfm = self.Application.PreferenceManager
            if pfm.preset.id:
                bs = pfm.preset.width, pfm.preset.height
            else:
                bs = pfm.boardwidth, pfm.boardheight
            try:
                bs = int(bs[0]), int(bs[1])
            except (IndexError, ValueError):
                # Could be set to None or "None" somehow
                bs = _defaultBoardSize
            self.BoardSize = tuple(bs)
        return bs

    def _setBoardSize(self, size):
        assert type(size) in (list, tuple)
        assert len(size) == 2
        assert (type(size[0]), type(size[1])) == (int, int)
        if not (size[0] and size[1]):
            dabo.log.error(_("Cannot set dimensions to zero."))
            size = _defaultBoardSize
        self._boardSize = size
        self.Form.updateGameInfo()
        self.Application.PreferenceManager.boardwidth = size[0]
        self.Application.PreferenceManager.boardheight = size[1]

    def _getMineCount(self):
        try:
            bc = self._mineCount
        except AttributeError:
            bc = self.Application.PreferenceManager.minecount
            try:
                self.MineCount = int(bc)
            except ValueError:
                # could be None or "None" somehow
                self.MineCount = _defaultMineCount
        return bc

    def _setMineCount(self, count):
        assert type(count) == int
        # Guarantee at least one mine
        if count < 1:
            dabo.log.error(_("Mine count must be at least 1."))
            count = 1
        count = max(1, count)
        self._mineCount = count
        self.Form.updateGameInfo()
        self.Application.PreferenceManager.minecount = count

    def _getMinesRemaining(self):
        try:
            v = self._minesRemaining
        except AttributeError:
            v = self._minesRemaining = None
        return v

    def _setMinesRemaining(self, val):
        self._minesRemaining = val
        self.Form.tbMines.Value = val

    def _getGameInProgress(self):
        try:
            v = self._gameInProgress
        except AttributeError:
            v = self._gameInProgress = False
        return v

    def _setGameInProgress(self, val):
        if val:
            self.StopWatch.reset()
            # -             self.StopWatch.start()  ## no, do this on the first square clicked
            self.Timer.start()
        else:
            self.StopWatch.stop()
            self.Timer.stop()
            print("Game time: %f seconds." % self.StopWatch.Value)
        self._gameInProgress = val
        self.Form.pausebutton.Enabled = val

    def _getStopWatch(self):
        try:
            v = self._stopWatch
        except AttributeError:
            v = self._stopWatch = StopWatch.StopWatch()
        return v

    def _getTimer(self):
        try:
            v = self._timer
        except AttributeError:
            v = self._timer = dabo.ui.dTimer(self)
            v.Interval = _timerInterval
            v.bindEvent(dEvents.Hit, self.onTimer)
        return v

    BoardSize = property(
        _getBoardSize, _setBoardSize, None, _("Sets the dimension of the board. (w,h)")
    )

    MineCount = property(
        _getMineCount, _setMineCount, None, _("Sets the number of mines on the board.")
    )

    StopWatch = property(_getStopWatch)

    Timer = property(_getTimer)

    _MinesRemaining = property(_getMinesRemaining, _setMinesRemaining)

    _GameInProgress = property(_getGameInProgress, _setGameInProgress)


class MinesweeperForm(dForm):
    def afterInit(self):
        self.fillMenu()
        self.preset = {}
        self._initPrefs()
        dabo.ui.callAfter(self.newGame)

    def _initPrefs(self):
        """Make sure that the prefs exist. If not, initialize them to
        their default value.
        """
        pfm = self.Application.PreferenceManager
        if not isinstance(pfm.preset.mines, int):
            # First time through; initialize the default values.
            pfm.deleteAllPrefs()
            pfm.preset.mines = 0
            pfm.preset.width = 0
            pfm.preset.height = 0
            pfm.preset.name = ""
            pfm.preset.id = None
            pfm.boardwidth = _defaultBoardSize[0]
            pfm.boardheight = _defaultBoardSize[1]
            pfm.minecount = _defaultMineCount
            pfm.playername = None
        self.preset["Id"] = pfm.preset.id
        self.preset["Name"] = pfm.preset.name
        self.preset["Width"] = pfm.preset.width
        self.preset["Height"] = pfm.preset.height
        self.preset["Mines"] = pfm.preset.mines

    def initProperties(self):
        self.Caption = "Dabo MineSweeper"
        self.Sizer = dabo.ui.dSizer("vertical")
        self._autopause = False

    def onDeactivate(self, evt):
        """Pause the game automatically when form loses focus."""
        try:
            if (
                not self.pausebutton.Value
                and self.board._GameInProgress
                and self.board.StopWatch.Running
            ):
                self._autopause = True
                self.pausebutton.Value = True
                self.pausebutton.raiseEvent(dEvents.Hit)
        except Exception:
            # need to figure out what to do about this. Happens on win32 but
            # not Linux, presumably because the deactivate is received after the
            # form is already gone.
            pass

    def onActivate(self, evt):
        ## if game was automatically paused upon deactivate, unpause it now
        if self._autopause and self.board._GameInProgress:
            self.pausebutton.Value = False
            self.pausebutton.raiseEvent(dEvents.Hit)
        self._autopause = False

    def updateGameInfo(self):
        """The board setup has changed: reflect in the game info label in the toolbar."""
        b = self.board
        s = b.BoardSize
        m = b.MineCount
        self.lblGameInfo.Caption = "%sx%s,%s" % (s[0], s[1], m)

    def onEditPreferences(self, evt):
        if self.board._GameInProgress and (self.pausebutton.Value or self.board.StopWatch.Running):
            dabo.ui.stop("Please end your game before changing the preferences.")
            return
        dlg = PreferenceDialog(self)
        dlg.show()
        if dlg.accepted:
            pfm = self.Application.PreferenceManager
            pfm.preset.id = dlg.preset["Id"]
            pfm.preset.name = dlg.preset["Name"]
            pfm.preset.width = dlg.preset["Width"]
            pfm.preset.height = dlg.preset["Height"]
            pfm.preset.mines = dlg.preset["Mines"]
            self.board.BoardSize = (dlg.boardWidth, dlg.boardHeight)
            self.board.MineCount = dlg.boardMines
            self.preset = dlg.preset
            self.newGame()
        dlg.release()

    def onPause(self, evt):
        if self.pausebutton.Value == True:
            self.board.Timer.stop()
            self.board.StopWatch.stop()
            props = {"Caption": "Resume", "FontBold": True, "ForeColor": "red"}
        else:
            self.board.StopWatch.start()
            self.board.Timer.start()
            props = {"Caption": "Pause", "FontBold": False, "ForeColor": "black"}
        self.pausebutton.setProperties(props)
        self.board.Visible = not self.pausebutton.Value
        self.tbMines.Visible = not self.pausebutton.Value

    def onNewGame(self, evt):
        self.newGame()

    def onEndGame(self, evt):
        self.board.showAllSquares()
        self.board._GameInProgress = False

    def onViewHighScores(self, evt):
        # ToDo: put in a window. For now, echo to terminal.
        gameId = self.preset["Id"]
        if gameId < 0 or gameId is None:
            dabo.ui.stop("Please select a preset game in Preferences first.")
            return
        if dabo.ui.areYouSure("Viewing the high scores requires an internet connection. Continue?"):
            conn = dabo.db.dConnection(MinesweeperCI())
            biz = MinesweeperBO_scores(conn)
            biz.GameId = gameId
            biz.requery()
            if biz.RowCount > 0:
                ds = biz.getDataSet()
                print("\nTop %d Scores for %s:" % (biz.Limit, biz.Record.gamename))
                for idx, r in enumerate(ds):
                    r["row"] = idx + 1
                    print("\t%(row)d) %(playername)s: %(timestamp)s: %(time).3f sec." % r)
                print("\n")
            else:
                print("No high scores for this game yet.")

    def onRules(self, evt):
        win = dabo.ui.dDialog(
            self,
            NameBase="frmRulesDialog",
            Caption="Minesweeper Rules",
            SaveRestorePosition=True,
            Centered=True,
            Modal=False,
        )
        pnl = dabo.ui.dScrollPanel(win)
        win.Sizer.append1x(pnl)
        txt = dabo.ui.dLabel(pnl, Caption=__doc__)
        sz = dabo.ui.dSizer("v")
        sz.append1x(txt, border=10)
        pnl.Sizer = sz
        win.layout()
        pnl.fitToSizer()
        win.Visible = True

        # Not real sure why the dialog doesn't release itself upon Close, but
        # the following handles that until I figure it out:
        def onClose(evt):
            win.release()

        win.bindEvent(dEvents.Close, onClose)

    def newGame(self):
        try:
            self.board
        except AttributeError:
            self.addObject(Board, "board")
            self.Sizer.append(self.board, "expand", 1)
        bs = self.board.BoardSize
        mc = self.board.MineCount
        self.board.BoardSize = bs
        self.board.MineCount = mc
        self.board.newGame()
        self.layout()

    def recordScore(self):
        """Record the score, if it is possible/allowed.

        If this game was from a preset, we can optionally record the score to
        the public database. Present a dialog asking for Name and Comments,
        and if Ok pressed, record the score. Otherwise, don't even connect
        to the internet at all.
        """
        if self.preset["Id"] is None or self.preset["Id"] < 1:
            return

        class dlgScore(dabo.ui.dOkCancelDialog):
            def addControls(self):
                class Label(dabo.ui.dLabel):
                    def initProperties(self):
                        self.Alignment = "Right"
                        self.AutoResize = False
                        self.Width = 100

                vs = self.Sizer
                message = """Since you are playing a game defined in the public presets,
you can record your score in the public database. If you'd like to do this, just
enter your name and optional comment. You'll need an internet connection for
this to work."""
                o = self.addObject(dabo.ui.dLabel, Caption=message)
                vs.append(o, border=10)

                brdr = 5
                hs = dabo.ui.dSizer("horizontal")
                lbl = Label(self, Name="lblName", Caption="Name:")
                txt = dabo.ui.dTextBox(self, RegID="txtName")
                hs.append(lbl, "fixed", alignment="right", border=brdr)
                hs.append1x(txt, border=brdr)
                vs.append1x(hs)

                hs = dabo.ui.dSizer("horizontal")
                lbl = Label(self, Name="lblComment", Caption="Comment:")
                txt = dabo.ui.dTextBox(self, RegID="txtComment")
                hs.append(lbl, "fixed", alignment="right", border=brdr)
                hs.append1x(txt, border=brdr)
                vs.append1x(hs)

                playername = self.Application.PreferenceManager.playername
                if isinstance(playername, str):
                    self.txtName.Value = playername
                else:
                    self.txtName.Value = ""
                    self.Application.PreferenceManager.playername = ""

        dlg = dlgScore(self, Caption="Record Score")
        dlg.fitToSizer()
        dlg.show()
        if dlg.Accepted:
            # get the bizobj, add the new record, and commit
            conn = dabo.db.dConnection(MinesweeperCI())
            biz = MinesweeperBO_scores(conn)
            biz.new()
            while True:
                try:
                    biz.Record.playername = dlg.txtName.Value
                    biz.Record.playercomments = dlg.txtComment.Value
                    biz.Record.gamedefid = self.preset["Id"]
                    biz.Record.time = self.board.StopWatch.Value
                    biz.save()
                    self.Application.PreferenceManager.playername = biz.Record.playername
                    break
                except dabo.dException.BusinessRuleViolation as e:
                    dabo.ui.exclaim(ustr(e))
                dlg.show()
                if not dlg.Accepted:
                    break
        dlg.release()

    def fillMenu(self):
        iconPath = "themes/tango/16x16"

        mb = self.MenuBar
        fileMenu = mb.getMenu("base_file")

        fileMenu.prependSeparator()
        fileMenu.prepend(
            _("&New Game"),
            HotKey="Ctrl+N",
            help=_("Start a new game"),
            OnHit=self.onNewGame,
            bmp="%s/actions/document-new.png" % iconPath,
        )

        viewMenu = mb.getMenu("base_view")

        viewMenu.append(
            _("&High scores"),
            help=_("View the high scores"),
            OnHit=self.onViewHighScores,
        )

        helpMenu = mb.getMenu("base_help")
        helpMenu.append(
            _("&How to Play"),
            HotKey="Ctrl+I",
            help=_("Rules of the game"),
            OnHit=self.onRules,
            bmp="%s/apps/help-browser.png" % iconPath,
        )

        tb = self.ToolBar = dabo.ui.dToolBar(
            self, ShowCaptions=True
        )  ## Mac has a resize problem otherwise

        if self.Application.Platform == "Mac":
            # Toolbar looks better with larger icons on Mac. In fact, I believe HIG
            # recommends 32x32 for Mac Toolbars.
            iconSize = (32, 32)
        else:
            iconSize = (22, 22)
        tb.SetToolBitmapSize(iconSize)  ## need to abstract in dabo.ui.dToolBar!
        iconPath = "themes/tango/%sx%s" % iconSize

        tb.appendButton(
            "New",
            pic="%s/actions/document-new.png" % iconPath,
            toggle=False,
            OnHit=self.onNewGame,
            tip="New Game",
            help="Start a new game",
        )

        tb.appendButton(
            "End",
            pic="%s/actions/process-stop.png" % iconPath,
            toggle=False,
            OnHit=self.onEndGame,
            tip="End Game",
            help="End the current game",
        )

        tb.appendButton(
            "Preferences",
            pic="%s/categories/preferences-system.png" % iconPath,
            toggle=False,
            OnHit=self.onEditPreferences,
            tip="Preferences",
            help="Edit preferences",
        )

        tb.appendSeparator()

        self.lblGameInfo = tb.appendControl(dabo.ui.dLabel(tb, Width=100, Height=24))
        tb.appendSeparator()

        self.pausebutton = tb.appendControl(
            dabo.ui.dToggleButton(
                tb,
                Caption="Pause",
                ToolTipText="Pause/Resume",
                StatusText="Pause/Resume the game",
                OnHit=self.onPause,
            )
        )

        tb.appendSeparator()
        self.lblMines = tb.appendControl(
            dabo.ui.dLabel(tb, Width=50, Height=20, FontSize=9, Caption="Mines:")
        )
        self.tbMines = tb.appendControl(dabo.ui.dTextBox(tb, Width=30, ReadOnly=True))


class PreferenceDialog(dabo.ui.dOkCancelDialog):
    def initProperties(self):
        self.AutoSize = False
        self.Caption = "Minesweeper Preferences"
        self.SaveRestorePosition = True

    def afterInit(self):
        b = self.Parent.board
        self.boardWidth = b.BoardSize[0]
        self.boardHeight = b.BoardSize[1]
        self.boardMines = b.MineCount
        self.accepted = False
        self.Modal = True
        self.Centered = True

    def onPickPreset(self, evt):
        """Called when the user pushes the butPickPreset button on the preset page."""

        class Browse(dabo.ui.dGrid):
            pass

        class PickPreset(dabo.ui.dOkCancelDialog):
            def initProperties(self):
                self.AutoSize = False
                self.Caption = "Pick Game Preset"
                self.SaveRestorePosition = True
                self.Modal = True
                self.Centered = True
                self.FormType = "PickList"
                self.accepted = False

            def pickRecord(self):
                self.accepted = True
                self.hide()

            def getBizobj(self, ds):
                ## This simulates dForm enough to get by.
                return self.biz

            def addControls(self):
                conn = dabo.db.dConnection(MinesweeperCI())
                biz = self.biz = MinesweeperBO_gamedefs(conn)
                biz.requery()

                g = self.grid = self.addObject(Browse)
                g.FieldSpecs = biz.getGameDefFieldSpecs()
                g.DataSource = biz.DataSource
                self.Sizer.append1x(g)

        f = PickPreset(self)
        if self.preset["Id"] is not None:
            # Have the grid select the current id as a convenience:
            f.biz.seek(self.preset["Id"], "id")
        #        f.grid.populate()
        f.grid.buildFromDataSet(f.grid.DataSource)
        f.show()
        if f.accepted:
            biz = f.biz
            self.preset["Id"] = biz.Record.id
            self.preset["Name"] = biz.Record.name
            self.preset["Width"] = biz.Record.width
            self.preset["Height"] = biz.Record.height
            self.preset["Mines"] = biz.Record.mines
            self.refreshPresets()

    def refreshPresets(self):
        p = self.PageFrame.Pages[0]
        for c in ("Name", "Width", "Height", "Mines"):
            o = p.__dict__["o%s" % c]
            o.Value = self.preset[c]

    def addControls(self):
        pgf = self.PageFrame = dabo.ui.dPageFrame(self)
        p1 = pgf.appendPage(caption="Choose From Presets")
        p2 = pgf.appendPage(caption="Set By Hand")

        class lbl(dabo.ui.dLabel):
            def initProperties(self):
                self.Alignment = "Right"
                self.AutoResize = False
                self.Width = 100

        # p1:
        b = 5
        vs = dabo.ui.dSizer("vertical")

        app = self.Application
        preset = self.preset = self.Parent.preset

        if preset["Id"] is None or preset["Id"] < 1:
            preset["Name"] = "< None >"
        hs = dabo.ui.dSizer("horizontal")
        cb = p1.addObject(
            dabo.ui.dButton,
            Name="butPickPreset",
            Caption="Preset:",
            ToolTipText="""Press this button to choose a preset from the public game definitions.

Note that this will require an internet connection.
""",
        )
        t = p1.addObject(dabo.ui.dTextBox, "oName", Value=preset["Name"], ReadOnly=True)
        hs.append(cb, "fixed", alignment="right", border=b)
        hs.append(t, 1, border=b)
        vs.append(hs, "expand")

        cb.bindEvent(dEvents.Hit, self.onPickPreset)

        for name in ("Width", "Height", "Mines"):
            hs = dabo.ui.dSizer("horizontal")
            l = p1.addObject(lbl, Name="lbl%s" % name, Caption="%s:" % name)
            s = p1.addObject(
                dabo.ui.dSpinner,
                "o%s" % name,
                Value=preset[name],
                Enabled=False,
                Min=4,
                Max=50,
            )
            hs.append(l, "fixed", alignment="right", border=b)
            hs.append(s, border=b)
            vs.append(hs)

        p1.Sizer = vs

        # p2:
        b = 5
        vs = dabo.ui.dSizer("vertical")
        for name in ("Width", "Height", "Mines"):
            hs = dabo.ui.dSizer("horizontal")
            l = p2.addObject(lbl, Name="lbl%s" % name, Caption="%s:" % name)
            s = p2.addObject(
                dabo.ui.dSpinner,
                "o%s" % name,
                Value=eval("self.board%s" % name),
                Min=4,
                Max=50,
            )
            hs.append(l, "fixed", alignment="right", border=b)
            hs.append(s, border=b)
            vs.append(hs)

        p2.Sizer = vs

        self.Sizer.append1x(pgf)

        if (
            preset["Id"] is None
            or preset["Id"] < 1
            or (
                preset["Width"] != self.boardWidth
                or preset["Height"] != self.boardHeight
                or preset["Mines"] != self.boardMines
            )
        ):
            pgf.SelectedPageNumber = 1

    def runOK(self):
        self.accepted = True
        p = self.PageFrame.SelectedPage
        self.boardWidth = p.oWidth.Value
        self.boardHeight = p.oHeight.Value
        self.boardMines = p.oMines.Value
        pp = self.PageFrame.SelectedPageNumber
        if pp != 0:
            self.preset["Id"] = -1


##pkm: The following CI and BO's are for the future high-score and dynamic game
#      type editor. People will be able to define their favorite game settings,
#      and then save those settings to the public database so other players can
#      select that game from a list. It is these public games that will be able
#      to have high scores recorded.


class MinesweeperCI(dabo.db.dConnectInfo):
    def initProperties(self):
        self.DbType = "MySQL"
        self.Host = "paulmcnett.com"
        self.Database = "dabotest"
        self.User = "dabo"
        self.Port = 3306
        self.Password = "Y38Z11XA2Z5F"


class MinesweeperBO_gamedefs(dabo.biz.dBizobj):
    def initProperties(self):
        self.Caption = "Minesweeper Game Definitions"
        self.DataSource = "minesweeper_gamedefs"
        self.KeyField = "id"

    def afterInit(self):
        self.setBaseSQL()

    def setBaseSQL(self):
        self.addFrom("minesweeper_gamedefs")
        self.setLimitClause("500")
        self.addField("minesweeper_gamedefs.id as id")
        self.addField("minesweeper_gamedefs.name as name")
        self.addField("minesweeper_gamedefs.width as width")
        self.addField("minesweeper_gamedefs.height as height")
        self.addField("minesweeper_gamedefs.mines as mines")
        self.addField("minesweeper_gamedefs.comments as comments")
        self.addField("minesweeper_gamedefs.submittedby as submittedby")

    def getGameDefFieldSpecs(self):
        """For simplicity, I put this into the bizobj."""
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<daboAppSpecs>
    <table name="minesweeper_gamedefs">
        <fields>
            <field name="id"    type="int"    caption="id"
                searchInclude="0"    searchOrder="0"    wordSearch="0"
                listInclude="0"    listColWidth="-1"    listOrder="0"
                editInclude="0"    editReadOnly="0"    editOrder="0"  />

            <field name="name"    type="char"    caption="Name"
                searchInclude="1"    searchOrder="10"    wordSearch="0"
                listInclude="1"    listColWidth="-1"    listOrder="10"
                editInclude="1"    editReadOnly="0"    editOrder="10"  />

            <field name="width"    type="int"    caption="Width"
                searchInclude="1"    searchOrder="20"    wordSearch="0"
                listInclude="1"    listColWidth="-1"    listOrder="20"
                editInclude="1"    editReadOnly="0"    editOrder="20"  />

            <field name="height"    type="int"    caption="Height"
                searchInclude="1"    searchOrder="30"    wordSearch="0"
                listInclude="1"    listColWidth="-1"    listOrder="30"
                editInclude="1"    editReadOnly="0"    editOrder="30"  />

            <field name="mines"    type="int"    caption="Mines"
                searchInclude="1"    searchOrder="40"    wordSearch="0"
                listInclude="1"    listColWidth="-1"    listOrder="40"
                editInclude="1"    editReadOnly="0"    editOrder="40"  />

            <field name="comments"    type="memo"    caption="Comments"
                searchInclude="1"    searchOrder="50"    wordSearch="0"
                listInclude="0"    listColWidth="-1"    listOrder="50"
                editInclude="1"    editReadOnly="0"    editOrder="50"  />

            <field name="submittedby"    type="char"    caption="Submitted By"
                searchInclude="1"    searchOrder="60"    wordSearch="0"
                listInclude="1"    listColWidth="-1"    listOrder="60"
                editInclude="1"    editReadOnly="0"    editOrder="60"  />

        </fields>
    </table>

</daboAppSpecs>
"""
        return specParser.importFieldSpecs(xml, "minesweeper_gamedefs")


class MinesweeperBO_scores(dabo.biz.dBizobj):
    def initProperties(self):
        self.Caption = "Minesweeper High Scores"
        self.DataSource = "minesweeper_scores"
        self.KeyField = "id"
        self.DefaultValues = {"timestamp": datetime.datetime.utcnow}

    def afterInit(self):
        self.NonUpdateFields = [
            "gamename",
            "gamewidth",
            "gameheight",
            "gamemines",
            "gamecomments",
        ]
        self.setFromClause("""minesweeper_scores scores
                inner join minesweeper_gamedefs gamedefs
                on gamedefs.id = scores.gamedefid""")
        self.addField("scores.id as id")
        self.addField("scores.gamedefid as gamedefid")
        self.addField("scores.timestamp as timestamp")
        self.addField("scores.playername as playername")
        self.addField("scores.playercomments as playercomments")
        self.addField("scores.time as time")
        self.addField("gamedefs.name as gamename")
        self.addField("gamedefs.width as gamewidth")
        self.addField("gamedefs.height as gameheight")
        self.addField("gamedefs.mines as gamemines")
        self.addField("gamedefs.comments as gamecomments")
        self.setOrderByClause("""gamedefs.name, scores.time, scores.timestamp""")
        self.GameId = None
        self.Limit = 20

    def validateRecord(self):
        err = ""
        if len(self.Record.playername.strip()) == 0:
            err += "Please enter your name"
        return err

    def _getGameId(self):
        return self._gameId

    def _setGameId(self, val):
        self._gameId = val
        if val is not None:
            self.setWhereClause("""gamedefs.id=%s""" % val)
        else:
            self.setWhereClause("")

    def _getLimit(self):
        return self._limit

    def _setLimit(self, val):
        self._limit = val
        self.setLimitClause("%s" % val)

    GameId = property(_getGameId, _setGameId)
    Limit = property(_getLimit, _setLimit)


if __name__ == "__main__":
    app = dApp(MainFormClass=MinesweeperForm)
    app.start()
