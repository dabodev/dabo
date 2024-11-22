# -*- coding: utf-8 -*-
import dabo
import dabo.biz as biz
from dabo.dLocalize import _
from dabo.lib.utils import ustr
import random
import time
import os


class BubbleBizobj(biz.dBizobj):
    def beforeInit(self):
        # self.DataSource = "Bubble"
        self.bubbles = []
        self.selCount = 0
        self.__score = 0
        self.__message = ""
        self.__callbackFunc = None
        self.__gameOver = False
        self.__isNewHighGame = False

    def initProperties(self):
        self.BasePrefKey = dabo.dAppRef.BasePrefKey

    def newGame(self):
        for rr in self.bubbles:
            for cc in rr:
                cc.setRandomColor(True)
                cc.Selected = cc.Popped = False
        self.Score = 0
        self.GameOver = False
        self.IsNewHighGame = False
        self._allBubbles = []
        for bubrow in self.bubbles:
            self._allBubbles.extend(bubrow)

    def bubbleClick(self, bubble):
        ret = 0
        if bubble.Selected:
            ret = self.popBubbles()
            self.unselectBubbles()
            self.Message = _("You scored %s points!" % ret)
        else:
            self.unselectBubbles()
            self.selectBubbles(bubble)
            self.Message = _("Bubble Points: ") + ustr(self.BubbleScore)
        return ret

    def popBubbles(self):
        ret = self.BubbleScore
        self.Score += self.BubbleScore
        for rr in self.bubbles:
            for cc in rr:
                if cc.Selected:
                    cc.Popped = True
                    cc.Selected = False
        self.selCount = 0
        self.shiftBubbles()
        self.fillEmptyCols()
        return ret

    def fillEmptyCols(self):
        isEmpty = True
        rows = len(self.bubbles)
        cols = len(self.bubbles[0])

        # Check if the lowest bubble is empty.
        toFill = 0
        for cc in range(cols):
            if self.bubbles[rows - 1][cc].Popped:
                toFill += 1

        if toFill:
            # Set the callback, so that the calling object knows that further
            # work is left
            self.__callbackFunc = self.callbackShift
            self._shiftTime = time.time()

            # Fill the columns
            for cc in range(toFill):
                num = random.randrange(rows - 1) + 2
                for ii in range(rows - num, rows):
                    bub = self.bubbles[ii][cc]
                    bub.Selected = False
                    bub.setRandomColor(True)
        else:
            # See if there are any moves remaining.
            self.checkGameOver()

    def shiftBubbles(self):
        """This can vary, depending on the type of Bubblet game. For now,
        stick with the standard "megashift", where both rows and columns
        are collapsed.
        """
        # First, clear the callback
        self.__callbackFunc = None
        rows = len(self.bubbles)
        cols = len(self.bubbles[0])
        shifted = []
        for cc in range(cols):
            for rr in range(1, rows):
                if self.bubbles[rr][cc].Popped:
                    for rAbove in range(rr, 0, -1):
                        self.bubbles[rAbove][cc].Color = self.bubbles[rAbove - 1][cc].Color
                        self.bubbles[rAbove][cc].Popped = self.bubbles[rAbove - 1][cc].Popped
                    self.bubbles[0][cc].Popped = True
        # Now shift columns to the right
        for rr in range(rows):
            for cc in range(cols - 1, 0, -1):
                currBub = self.bubbles[rr][cc]
                if currBub.Popped:
                    # See if there are any bubbles to the left that are not empty
                    for cLeft in range(cc, -1, -1):
                        leftBub = self.bubbles[rr][cLeft]
                        if not leftBub.Popped:
                            currBub.Color = leftBub.Color
                            currBub.Popped = False
                            leftBub.Popped = True
                            break

    def callbackShift(self, recallFunc=None):
        self.shiftBubbles()
        self.checkGameOver()
        if recallFunc:
            recallFunc()

    def checkGameOver(self):
        """Determine if there are any more moves possible. IOW, find at least
        one bubble with a matching neighbor.
        """
        self.GameOver = True
        for bub in self._allBubbles:
            if self.hasMatchingNeighbor(bub):
                self.GameOver = False
                break

        if self.GameOver:
            self.NumberOfGames += 1
            self.TotalPoints += self.Score
            if self.Score > self.HighGame:
                self.HighGame = self.Score
                self.IsNewHighGame = True
            # Set the message
            self.Message = _("Game Over!")
        return self.GameOver

    def hasMatchingNeighbor(self, bubble):
        """Need to try for matches above, below, left and right."""
        if bubble.Popped:
            return False
        return bool(self.getMatchingNeighbors(bubble))

    def getMatchingNeighbors(self, bubble):
        color = bubble.Color
        rr, cc = bubble.row, bubble.col
        return [
            neighbor
            for neighbor in self._allBubbles
            if neighbor.Color == color
            and neighbor.Popped is False
            and (
                ((abs(neighbor.row - rr) == 1) and (neighbor.col == cc))
                or ((abs(neighbor.col - cc) == 1) and (neighbor.row == rr))
            )
        ]

    def selectBubbles(self, bubble):
        if bubble.Selected:
            return
        if bubble.Popped:
            # They clicked on an empty space
            return
        mn = self.getMatchingNeighbors(bubble)
        bubble.Selected = bool(mn)
        self.selCount += {True: 1, False: 0}[bool(mn)]
        for match in mn:
            if not match.Selected:
                self.selectBubbles(match)

    def unselectBubbles(self):
        selBubs = (bub for bub in self._allBubbles if bub.Selected)
        for sel in selBubs:
            sel.Selected = False
        self.selCount = 0
        self.Message = _("Bubble Points: 0")

    def resetStats(self):
        self.NumberOfGames = 0
        self.TotalPoints = 0
        self.HighGame = 0

    def getCallback(self):
        return self.__callbackFunc

    # Begin property definitions
    def _getBubbleScore(self):
        return self.selCount * (self.selCount - 1)

    def _getGameOver(self):
        return self.__gameOver

    def _setGameOver(self, val):
        self.__gameOver = val

    def _getHighGame(self):
        ret = self.PreferenceManager.highgame
        if not isinstance(ret, int):
            ret = 0
        return ret

    def _setHighGame(self, val):
        self.PreferenceManager.highgame = val

    def _getIsNewHighGame(self):
        return self.__isNewHighGame

    def _setIsNewHighGame(self, val):
        self.__isNewHighGame = val

    def _getMessage(self):
        return self.__message

    def _setMessage(self, msg):
        self.__message = msg

    def _getGames(self):
        ret = self.PreferenceManager.numbergames
        if not isinstance(ret, int):
            ret = 0
        return ret

    def _setGames(self, val):
        self.PreferenceManager.numbergames = val

    def _getScore(self):
        return self.__score

    def _setScore(self, val):
        self.__score = val

    def _getTotalPoints(self):
        ret = self.PreferenceManager.totalpoints
        if not isinstance(ret, int):
            ret = 0
        return ret

    def _setTotalPoints(self, val):
        self.PreferenceManager.totalpoints = val

    BubbleScore = property(_getBubbleScore, None, None, _("Current score of bubbles"))

    GameOver = property(_getGameOver, _setGameOver, None, _("Status of the game"))

    HighGame = property(_getHighGame, _setHighGame, None, _("High score"))

    IsNewHighGame = property(
        _getIsNewHighGame,
        _setIsNewHighGame,
        None,
        _("Is the current game the new high game?"),
    )

    Message = property(_getMessage, _setMessage, None, _("Status Message"))

    NumberOfGames = property(_getGames, _setGames, None, _("Number of games played"))

    Score = property(_getScore, _setScore, None, _("Current score of the game"))

    TotalPoints = property(
        _getTotalPoints, _setTotalPoints, None, _("Total number of points recorded")
    )
