# -*- coding: utf-8 -*-
import datetime

import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from samples.games import MontanaForm


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dButton


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v")
        sz.appendSpacer(40)

        lbl = dLabel(
            self,
            Caption="Montana is a solitaire game that is easy to learn,\nbut difficult to master.\n\nFor instructions, please see the Overview tab.",
        )
        sz.append(lbl, halign="center")
        sz.appendSpacer(30)
        btn = dButton(self, Caption="Play Montana", OnHit=self.runGame)
        sz.append(btn, halign="center")

    def runGame(self, evt):
        frm = MontanaForm(self.Form, Size=(980, 514), Centered=True)
        frm.show()


category = "Games.Montana"

overview = """
<h3>About Montana</h3>
<p> <b>Montana</b> is a solitaire card game that is easy to learn, but
difficult to master. </p>

<h3>Object of the Game</h3>
<p> Arrange all of the cards into 4 rows in increasing order from 2 to
King, with one suit per row. </p>

<h3>Starting a Game</h3>
<p> The cards are dealt out into 4 rows of 13 cards each. The aces are
then removed, leaving 4 gaps. </p>

<h3>Playing the Game</h3>
<p> Move cards into the gaps, which will create new gaps in their old
location. The only card that can be moved into any gap is determined by
the card to the immediate left of the gap. The moved card must be the
same suit, and one rank higher. Example: if there is a gap, and the card
to left of it is 4C, only 5C can be moved to the gap. </p>

<p> If the gap is located in the leftmost column, any 2 card can be
moved there. If the card to the left of the gap is a King, no card can
be moved there. </p>

<p> When all 4 gaps are located to the right of Kings, no further moves
are possible, and the hand ends. If there are any re-deals remaining,
the cards are re-dealt, and another hand is played. When all re-deals
are used, the game ends. The number of re-deals can be set in the game
preferences (default=2 re-deals). </p>

<h3>Scoring</h3>
<p> When a card is placed "in order", it scores a point. "In order" is
defined as any cards arranged with a 2 of that suit in the leftmost
column of a row, followed by other cards of that suit in sequence. Since
Aces are not played, you can score a maximum of 48 points per level.
Completing a level starts you over again, adding an additional re-deal
to your remaining re-deal status. </p>

<h3>Re-deals</h3>
<p> All ordered cards (i.e., those that in sequence and have scored a
point) remain where they are. All unordered cards (i.e., those not in
sequence) are picked up, shuffled with the Aces, and dealt into the open
spaces. The Aces are then removed, and play resumes. </p>
"""
