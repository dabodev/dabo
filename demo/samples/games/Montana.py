#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
import random
import os

import dabo
import dabo.ui
from dabo.dApp import dApp
from dabo.dLocalize import _

if __name__ == "__main__":
    import demo
    import cardlib
else:
    from . import cardlib


from dabo.ui import dTimer
from dabo.ui import dPanel
from dabo.ui import dForm


class MontanaDeck(cardlib.PokerDeck):
    #     def passHoverEvent(self, evt):
    #         self.board.onHover(evt)
    #
    #     def passEndHoverEvent(self, evt):
    #         self.board.endHover(evt)

    def appendCard(self, suit, rank):
        newCard = super(MontanaDeck, self).appendCard(suit, rank)
        #         newCard._hover = True
        #         newCard.onHover = self.passHoverEvent
        #         newCard.endHover = self.passEndHoverEvent
        newCard.bindEvent(dabo.dEvents.MouseLeftDown, self.board.onCardMDown)
        newCard.bindEvent(dabo.dEvents.MouseLeftUp, self.board.onCardMUp)
        newCard.bindEvent(dabo.dEvents.MouseLeftDoubleClick, self.board.onCardMDClick)
        newCard.bindEvent(dabo.dEvents.MouseRightClick, self.board.onCardMDClick)

    def createDeck(self):
        super(MontanaDeck, self).createDeck()
        self.faceUpAll()
        self.aces = []
        for card in self:
            if card.Rank == 1:
                self.aces.append(card)


class CardTimer(dTimer):
    def start(self, *args, **kwargs):
        self.target._cardTimerFirstHit = False
        super(CardTimer, self).start(*args, **kwargs)

    def onHit(self, evt):
        flashCards = self.target.flashCards
        if not flashCards:
            self.stop()
        else:
            for card in flashCards:
                card.Visible = not card.Visible
                card.refresh()
            self.start(100)
        self.target._cardTimerFirstHit = True


class Board(dPanel):
    def afterInit(self):
        self.DeckDirectory = self.Form.getDeckDir()
        self.BackColor = "olivedrab"
        self._priorHandScore = 0
        self._score = 0
        self.isStuck = True
        # Controls card flashing
        self.cardTimer = CardTimer()
        self.cardTimer.target = self
        self._cardTimerFirstHit = False
        self.flashCards = []
        # Flag that indicates we need to resize the cards
        self.needResize = False
        self.gridSizer = None
        # Border around the cards
        self._border = 15
        # Create the deck
        self.deck = MontanaDeck(self)
        self.createSizer()

    def createSizer(self):
        if not self.Sizer:
            self.Sizer = dabo.ui.dSizer("v")
            self.Sizer.DefaultBorder = self._border
            self.Sizer.DefaultBorderAll = True
        if self.gridSizer:
            self.Sizer.remove(self.gridSizer)
            for card in self.deck:
                self.gridSizer.remove(card)
            self.gridSizer.release()
        self.gridSizer = dabo.ui.dGridSizer(MaxCols=13, HGap=2, VGap=2)
        self.Sizer.append1x(self.gridSizer)

    def newGame(self):
        self.Redeals = self.Form.PreferenceManager.redeals
        self._priorHandScore = 0
        self._score = 0

        # Contains the current layout of the cards.
        self.cardLayout = ()
        # This holds the history, enabling undo. Most recent positions
        # are at the end.
        self.historyStack = []
        # This holds the redo stack
        self.redoStack = []
        # Clear the 'scored' attribute for the cards
        for card in self.deck:
            card.scored = False
        random.shuffle(self.deck)
        self.createSizer()
        self.gridSizer.appendItems(self.deck)
        self.updateCardLayout()
        self.updateStatus()

    def redeal(self):
        """Gather all the non-scored cards, shuffle 'em,
        and place them back into the layout.
        """
        sz = self.gridSizer
        redo = []
        for card in self.deck:
            if not card.scored:
                sz.remove(card)
                redo.append(card)
        random.shuffle(redo)
        sz.appendItems(redo)
        self.Redeals -= 1
        self.historyStack = []
        self.redoStack = []
        #        self.cardLayout = ()
        self.updateCardLayout(False)
        self.updateStatus()

    def cardClick(self, card):
        """Called from a card when it is clicked."""
        if card is None:
            return
        rank, suit = card.Rank, card.Suit
        if rank == 1:
            # Ace; nothing to do
            return
        if rank == 2:
            # See if there are any aces in the first column.
            for row in range(4):
                firstColCard = self.gridSizer.getItemByRowCol(row, 0)
                if firstColCard is not None:
                    if firstColCard.Rank == 1:
                        self.switchCards(card, firstColCard)
                        self.updateStatus()
                        break
        else:
            # See if the card below it in sequence has an ace to its right
            prevCard = self.getCard(rank - 1, suit)
            rCard = self.gridSizer.getNeighbor(prevCard, "right")
            if rCard is not None:
                if rCard.Rank == 1:
                    # We can move it
                    self.switchCards(card, rCard)
                    self.updateStatus()

    #     def onHover(self, evt):
    #         if evt is None:
    #             return
    #         self.onCardMDown(evt)
    #     def endHover(self, evt):
    #         if evt is None:
    #             return
    #         self.onCardMUp(evt)

    def onCardMDown(self, evt):
        card = evt.EventObject
        rank, suit = card.Rank, card.Suit
        aceClicked = rank == 1
        if aceClicked:
            # Ace; flash the card that goes in this slot
            leftCard = self.gridSizer.getNeighbor(card, "left")
            if leftCard is None:
                # We're at the left column: flash all the 2's:
                targets = []
                for suit in "SCDH":
                    targets.append(self.getCard(2, suit))
                self.flashCards = targets
                self.cardTimer.start(1)
                return
            else:
                rank, suit = leftCard.Rank, leftCard.Suit
                if rank == 1:
                    # Another ace; do nothing
                    return

        if rank and suit:
            flashAll = aceClicked or not self.Form.getOnlyFlashAces()
            # Flash the card next in sequence
            target = self.getCard(rank + 1, suit)
            if target and flashAll:
                self.flashCards = [
                    target,
                ]
            if aceClicked:
                self.cardTimer.start(1)
            else:
                # Add the card before in sequence also
                target = self.getCard(rank - 1, suit)
                if (target.Rank > 1) and flashAll:
                    self.flashCards.append(target)
                # Need to delay the start of the blinking, so that the user has enough
                # time to finish the click to move the card
                self.cardTimer.start(500)

    def onCardMUp(self, evt):
        card = evt.EventObject
        if card is None:
            return
        # Stop any flashing:
        self.cardTimer.stop()
        for fc in self.flashCards:
            fc.Visible = True
            self.flashCards = []

        if not self._cardTimerFirstHit:
            # user wasn't holding down the mouse button, so process the click
            self.cardClick(card)

    def onCardMDClick(self, evt):
        card = evt.EventObject
        if not card.Rank == 1:
            return
        left_card = self.gridSizer.getNeighbor(card, "left")
        if not left_card:
            return
        left_rank, left_suit = left_card.Rank, left_card.Suit
        target = self.getCard(left_rank + 1, left_suit)
        self.cardClick(target)

    def updateStatus(self):
        """Several things need to be determined:
        - update the score and the scored property of the cards
        - xmark and count any dead aces
        - if all aces are dead, enable re-deal button
        """
        # Calculate the score
        self._score = 0
        for row in range(4):
            start = row * 13
            cards = self.cardLayout[start : start + 12]
            if cards[0].Rank == 2:
                # There is scoring in this row
                suit = cards[0].Suit
                seq = 1
                for card in cards:
                    if card.Suit == suit:
                        if card.Rank == seq + 1:
                            card.scored = True
                            self._score += 1
                            seq += 1
                        else:
                            break
                    else:
                        break

        # update the form
        self.Form.updateScore()
        deckdir = self.DeckDirectory
        # Mark the dead aces. These are all the aces to the right
        # of Kings.
        sz = self.gridSizer
        for ace in self.deck.aces:
            ace.AlternatePicture = "%s/blank" % deckdir
        dead = 0
        self.isStuck = False
        for suit in "SHDC":
            king = self.getCard(13, suit)
            rtCard = sz.getNeighbor(king, "right")
            while (rtCard is not None) and (rtCard.Rank == 1):
                rtCard.AlternatePicture = "%s/x" % deckdir
                dead += 1
                rtCard = sz.getNeighbor(rtCard, "right")
        if dead == 4:
            # No more moves possible!
            self.stuck()

        # Update the redeal button:
        self.Form.updateRedealCaption()

        if self.Application.Platform == "Win":
            # Windows needs to be refreshed, or card pix are wrong, but don't do this on
            # Mac or Linux because it isn't necessary and it adds a noticeable lag.
            self.refresh()

    def stuck(self, _forceWin=False, _forceLose=False):
        """Called when no more moves are possible. If there
        are re-deals left, enable the re-deal button. Otherwise,
        flash 'em the Game Over message.
        """
        self.isStuck = True
        # see if we've completed the deck
        outOfPlace = [cd for cd in self.deck if cd.Rank != 1 and not cd.scored]
        if not outOfPlace or _forceWin:
            self._priorHandScore += self._score
            msg = (
                "Congratulations! You completed the board!\n\n"
                + "You have earned an extra re-deal, and the game continues!"
            )
            dabo.ui.exclaim(msg)
            # We have to add 2 here, since the redeal count will be decreased
            # by one when we call redeal().
            self.Redeals += 2
            # Mark all the cards as not 'scored' so that they are all shuffled.
            self.setAll("scored", False)
            self.redeal()
            return
        if self.Redeals < 1 or _forceLose:
            msg = "Game over! Your final score was %s" % self.TotalScore
            dabo.ui.callAfter(dabo.ui.info, msg)
        else:
            self.Form.showRedeal()

    def switchCards(self, c1, c2):
        """Change the position of the two cards."""
        sz = self.gridSizer
        c1.lockDisplay()
        c2.lockDisplay()
        row1, col1 = sz.getGridPos(c1)
        row2, col2 = sz.getGridPos(c2)
        # Move the first out of the way
        tempRow, tempCol = sz.findFirstEmptyCell()
        sz.moveObject(c1, tempRow, tempCol, delay=True)
        # Now move the second to the first position
        sz.moveObject(c2, row1, col1, delay=True)
        # Now move the first to the second position
        sz.moveObject(c1, row2, col2)
        # Since this is a move forward, clear the redo stack
        self.redoStack = []
        # Update the card layout and history
        self.updateCardLayout()
        dabo.ui.callAfter(c1.unlockDisplay)
        dabo.ui.callAfter(c2.unlockDisplay)

    def updateCardLayout(self, addToHistory=True):
        if addToHistory:
            if self.cardLayout:
                # Push the old layout onto the history stack
                self.historyStack.append(self.cardLayout)
        # Set the new card layout
        layout = []
        sz = self.gridSizer
        for row in range(4):
            for col in range(13):
                layout.append(sz.getItemByRowCol(row, col))
        self.cardLayout = tuple(layout)

    def undo(self):
        self.undoRedo(self.historyStack, self.redoStack)

    def redo(self):
        self.undoRedo(self.redoStack, self.historyStack)

    def undoRedo(self, fromStack, toStack):
        if fromStack:
            turn = fromStack.pop()
            toStack.append(self.cardLayout)
            self.createSizer()
            self.gridSizer.appendItems(turn)
            self.layout()
            self.updateCardLayout(False)
            self.updateStatus()

    def getCard(self, rank, suit):
        """Returns a reference to the card that has the specified
        rank and suit.
        """
        # Updated to use RegIDs.
        id = "%s%s" % (suit, rank)
        ret = self.Form.getObjectByRegID(id)
        if ret is None:
            try:
                ret = [cd for cd in self.deck if (cd.Rank == rank) and (cd.Suit == suit)][0]
            except Exception:
                ret = None
        return ret

    def _getRedeals(self):
        if hasattr(self, "_redeals"):
            v = self._redeals
        else:
            v = self._redeals = self.Form.PreferenceManager.redeals
        return v

    def _setRedeals(self, val):
        self._redeals = val

    def _getScore(self):
        return self._score

    def _setScore(self, val):
        self._score = val

    def _getTotScore(self):
        return self._priorHandScore + self._score

    Redeals = property(_getRedeals, _setRedeals, None, _("Number of remaining redeals  (int)"))

    Score = property(_getScore, _setScore, None, _("Score of the game for the current hand  (int)"))

    TotalScore = property(
        _getTotScore,
        None,
        None,
        _("Total score of the game, including prior hands  (int)"),
    )


class MontanaForm(dForm):
    def afterInit(self):
        self.Centered = True
        self.Caption = "Montana"
        pfm = self.PreferenceManager
        if not isinstance(pfm.redeals, int):
            pfm.redeals = 2
        if not isinstance(pfm.flashOnlyAces, bool):
            pfm.flashOnlyAces = False
        if not isinstance(pfm.smallDeck, bool):
            pfm.smallDeck = False

        # Add the board, score display and re-deal button
        self.gameBoard = Board(self)
        self.Sizer.append1x(self.gameBoard)
        self.layout()
        self.fitToSizer(80, 30)
        self.fillMenu()
        dabo.ui.callAfter(self.startGame)

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
        )  ## Mac has a resize problem otherwise.

        if self.Application.Platform == "Mac":
            # Toolbar looks better with larger icons on Mac. In fact, I believe HIG
            # recommends 32x32 for Mac Toolbars.
            iconSize = (32, 32)
        else:
            iconSize = (22, 22)
        tb.SetToolBitmapSize(iconSize)  ## need to abstract in dToolBar!
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
            "Preferences",
            pic="%s/categories/preferences-system.png" % iconPath,
            toggle=False,
            OnHit=self.onEditPreferences,
            tip="Preferences",
            help="Edit preferences",
        )
        tb.appendSeparator()

        btn = self.btnRedeal = tb.appendControl(dabo.ui.dButton(tb, Enabled=False))
        btn.Height += 6
        self.updateRedealCaption()
        self.btnRedeal.bindEvent(dabo.dEvents.Hit, self.onRedeal)
        tb.appendSeparator()

        tb.appendControl(dabo.ui.dLabel(tb, Caption="Hand Score:", Width=50, Height=20))
        self.txtHandScore = tb.appendControl(
            dabo.ui.dTextBox(tb, Value=0, FontBold=True, Width=40, ReadOnly=True, Alignment="Right")
        )
        tb.appendSeparator()
        tb.appendControl(dabo.ui.dLabel(tb, Caption="Game Score:", Width=50, Height=20))
        self.txtGameScore = tb.appendControl(
            dabo.ui.dTextBox(tb, Value=0, FontBold=True, Width=40, ReadOnly=True, Alignment="Right")
        )

    def updateRedealCaption(self):
        btn = self.btnRedeal
        btn.Caption = "Redeals left: %s" % self.gameBoard.Redeals
        btn.Width = dabo.ui.fontMetric(btn.Caption, wind=btn)[0] + 24
        btn.Enabled = self.gameBoard.isStuck and self.gameBoard.Redeals > 0

    def getOnlyFlashAces(self):
        return self.PreferenceManager.flashOnlyAces

    def getDeckDir(self):
        pth = Path(__file__)
        # Looking for the 'demo' directory
        while pth.as_posix() and pth.name != "demo":
            pth = pth.parent
        card_type = "small" if self.PreferenceManager.smallDeck else "large"
        loc = pth / "media" / "cards" / card_type
        return loc.as_posix()

    def onEditUndo(self, evt):
        self.gameBoard.undo()

    def onEditRedo(self, evt):
        self.gameBoard.redo()

    def onEditPreferences(self, evt):
        """Create a dialog to edit preferences."""
        xml = self.getPrefControlXML()

        class MontanaPrefDialog(dabo.ui.dOkCancelDialog):
            def addControls(self):
                self.prf = self.Parent.PreferenceManager
                ctls = self.addObject(xml)
                self.Sizer.append1x(ctls, border=10)
                self.Sizer.appendSpacer(20)
                self.update()

        prf = self.PreferenceManager
        # Save the card size. If it changes, we need to create a new board
        small = prf.smallDeck
        prf.AutoPersist = False
        dlg = MontanaPrefDialog(self, Caption="Montana Prefs")
        dlg.show()
        if dlg.Accepted:
            prf.persist()
            if prf.smallDeck != small:
                msg = """You must quit and restart the game for the
                        card size changes to take effect""".replace("\t", "")
                dabo.ui.info(msg, title="Card Size Changed")
        else:
            prf.flushCache()
        prf.AutoPersist = True

    def onRules(self, evt):
        win = dabo.ui.dForm(self, Caption="Montana Rules", Centered=True)
        pnl = dabo.ui.dScrollPanel(win)
        win.Sizer.append1x(pnl)
        txt = dabo.ui.dLabel(pnl, Caption=helpText)
        sz = dabo.ui.dSizer("v")
        sz.append1x(txt, border=10)
        pnl.Sizer = sz
        btn = dabo.ui.dButton(win, Caption="OK")
        btn.bindEvent(dabo.dEvents.Hit, win.close)
        win.Sizer.append(btn, border=10, halign="right")
        win.layout()
        pnl.fitToSizer()
        win.Visible = True

    def onNewGame(self, evt):
        # Check for a game in progress.
        if self.gameBoard.historyStack and (not self.gameBoard.isStuck or self.gameBoard.Redeals):
            if not dabo.ui.areYouSure(
                message="Your game is not over. Are "
                + "you sure you want to end it and start a new game?"
            ):
                return
        self.startGame()

    def startGame(self):
        self.gameBoard.newGame()
        self.updateRedealCaption()

    def showRedeal(self):
        self.btnRedeal.Enabled = True

    def onRedeal(self, evt):
        self.gameBoard.redeal()
        self.btnRedeal.Enabled = False
        self.updateRedealCaption()

    def updateScore(self):
        self.txtHandScore.Value = self.gameBoard.Score
        self.txtGameScore.Value = self.gameBoard.TotalScore
        self.layout()

    def getPrefControlXML(self):
        return """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<dPanel classID="408701584" BorderColor="(0, 0, 0)" sizerInfo="{}" Name="dPanel" Buffered="False" code-ID="dPanel-top" ForeColor="(0, 0, 0)" designerClass="path://montanaPrefs.cdxml" BorderWidth="0" BackColor="(221, 221, 221)" BorderStyle="Default" ToolTipText="None" BorderLineStyle="Solid" savedClass="True">
    <dGridSizer classID="408701584-408700624" HGap="3" Rows="3" designerClass="LayoutGridSizer" VGap="3" MaxDimension="r" Columns="2">
        <dLabel classID="408701584-408656304" BorderColor="(0, 0, 0)" FontBold="False" Name="dLabel" sizerInfo="{'RowSpan': 1, 'RowExpand': False, 'ColSpan': 1, 'Proportion': 0, 'HAlign': 'Right', 'ColExpand': False, 'VAlign': 'Middle', 'Expand': False}" rowColPos="(0, 0)" Caption="Number of Redeals:" ForeColor="(0, 0, 0)" designerClass="controlMix" BorderWidth="0" BackColor="(221, 221, 221)" FontSize="13" BorderStyle="Default" ToolTipText="None" BorderLineStyle="Solid" FontItalic="False" FontUnderline="False"></dLabel>
        <dSpinner classID="408701584-408656560" BorderColor="(0, 0, 0)" FontBold="False" Name="dSpinner" sizerInfo="{'RowSpan': 1, 'RowExpand': False, 'ColSpan': 1, 'Proportion': 0, 'HAlign': 'Left', 'ColExpand': True, 'VAlign': 'Top', 'Expand': False}"  rowColPos="(0, 1)" FontUnderline="False" ForeColor="(0, 0, 0)" DataSource="self.Form.prf" designerClass="controlMix" BorderWidth="0" BackColor="(221, 221, 221)" FontSize="13" BorderStyle="Default" ToolTipText="None" BorderLineStyle="Solid" FontItalic="False" DataField="redeals"></dSpinner>
        <dLabel classID="408701584-408773008" BorderColor="(0, 0, 0)" FontBold="False" Name="dLabel1" sizerInfo="{'RowSpan': 1, 'RowExpand': False, 'ColSpan': 1, 'Proportion': 0, 'HAlign': 'Right', 'ColExpand': False, 'VAlign': 'Middle', 'Expand': False}" rowColPos="(1, 0)" Caption="Only flash empty spaces?" ForeColor="(0, 0, 0)" designerClass="controlMix" BorderWidth="0" BackColor="(221, 221, 221)" FontSize="13" BorderStyle="Default" ToolTipText="None" BorderLineStyle="Solid" FontItalic="False" FontUnderline="False"></dLabel>
        <dCheckBox classID="408701584-408811504" BorderColor="(0, 0, 0)" FontBold="False" DataField="flashOnlyAces" Name="dCheckBox" sizerInfo="{'RowSpan': 1, 'RowExpand': False, 'ColSpan': 1, 'Proportion': 0, 'HAlign': 'Left', 'ColExpand': True, 'VAlign': 'Top', 'Expand': True}" rowColPos="(1, 1)" Caption="" ForeColor="(0, 0, 0)" DataSource="self.Form.prf" designerClass="controlMix" BorderWidth="0" BackColor="(221, 221, 221)" FontSize="13" BorderStyle="Default" ToolTipText="None" BorderLineStyle="Solid" FontItalic="False" FontUnderline="False"></dCheckBox>
        <dCheckBox classID="408701584-430021296" BorderColor="(0, 0, 0)" FontBold="False" DataField="smallDeck" Name="dCheckBox1" sizerInfo="{'RowSpan': 1, 'RowExpand': False, 'ColSpan': 1, 'Proportion': 0, 'HAlign': 'Left', 'ColExpand': True, 'VAlign': 'Top', 'Expand': True}" rowColPos="(2, 1)" Caption="" ForeColor="(0, 0, 0)" DataSource="self.Form.prf" designerClass="controlMix" BorderWidth="0" BackColor="(221, 221, 221)" FontSize="13" BorderStyle="Default" ToolTipText="None" BorderLineStyle="Solid" FontItalic="False" FontUnderline="False"></dCheckBox>
        <dLabel classID="408701584-430460656" BorderColor="(0, 0, 0)" FontBold="False" Name="dLabel2" sizerInfo="{'RowSpan': 1, 'RowExpand': False, 'ColSpan': 1, 'Proportion': 0, 'HAlign': 'Right', 'ColExpand': False, 'VAlign': 'Middle', 'Expand': False}" rowColPos="(2, 0)" Caption="Use small cards" ForeColor="(0, 0, 0)" designerClass="controlMix" BorderWidth="0" BackColor="(221, 221, 221)" FontSize="13" BorderStyle="Default" ToolTipText="None" BorderLineStyle="Solid" FontItalic="False" FontUnderline="False"></dLabel>
    </dGridSizer>
</dPanel>"""


if __name__ == "__main__":
    app = dApp(MainFormClass=MontanaForm)
    app.BasePrefKey = "demo.games.montana"
    app.setAppInfo("appName", "Montana")
    app.start()
