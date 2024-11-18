# -*- coding: utf-8 -*-
import datetime

import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from samples.games import MinesweeperForm


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
            Caption="The classic game of Minesweeper, implemented in the Dabo UI.\n\nFor instructions, please see the Overview tab.",
        )
        sz.append(lbl, halign="center")
        sz.appendSpacer(30)
        btn = dButton(self, Caption="Play Minesweeper", OnHit=self.runGame)
        sz.append(btn, halign="center")

    def runGame(self, evt):
        frm = MinesweeperForm(self.Form, Size=(980, 514), Centered=True)
        frm.show()


category = "Games.Minesweeper"

overview = """
<h3>About Minesweeper</h3>
<p> <b>Minesweeper</b> is a classic computer game, implemented here in the Dabo UI. </p>

<h3>Object of the Game</h3>
<p> To identify all the mines without getting yourself blown up. </p>

<h3>Starting a Game</h3>
<p> Click the 'New' button in the toolbar at the top of the form. </p>

<h3>Playing the Game</h3>
<p> Click any square. If it is a mine, you are dead, and the game is over. If it is not a mine,
the number of mines on the squares immediately adjacent to that square will be displayed. Use
those numbers to judge the likelihood that mines will be located nearby. </p>

<p> Right-clicking on a square cycles it between three states: Marked (i.e., identified as a mine),
Uncertain (might be a mine; be careful about clicking!), or Normal. </p>

<h3>Winning the Game</h3>
<p> When you have correctly identified all the mines without getting yourself blown up. </p>
"""
