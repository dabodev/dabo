# -*- coding: utf-8 -*-
import datetime

import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from samples.games.bubblet.BubbletForm import BubbletForm

from dabo.ui import dButton
from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v")
        sz.appendSpacer(40)

        lbl = dLabel(
            self,
            Caption="Bubblet is a fun and somewhat addictive game.\n\nFor instructions, please see the Overview tab.",
        )
        sz.append(lbl, halign="center")
        sz.appendSpacer(30)
        btn = dButton(self, Caption="Run the Bubblet Game", OnHit=self.runGame)
        sz.append(btn, halign="center")

    def runGame(self, evt):
        frm = BubbletForm(self.Form, Size=(400, 300), Centered=True)
        frm.show()


category = "Games.Bubblet"

overview = """
<h3>About Bubblet</h3>
<p><b>Bubblet</b> is a fun and somewhat addictive game. There are columns
of bubbles of 4 different colors. If there are at least two adjacent
bubbles of the same color, clicking on one of them will select the
group. Clicking on any of the selected bubbles will pop them! When the
bubbles pop, any bubbles above them will drop down to fill the empty
spaces. The bubbles will also shift to the right to fill any open
spaces. </p>

<p> When a column of the board has been emptied, a new column with a
variable number of bubbles of random colors will replace it. It will
appear on the left of the board at first, and then immediately shift to
the right as necessary. I'm still working on the visual effects; I don't
have as much control of the appearance of the new column as I would
like. </p>


<h3>Scoring</h3>
<p>You get points for popping bubbles. The number of
points depends on the number of bubbles popped at once; bigger groups
score a lot more points! When you select a group of contiguous bubbles,
the bottom of the screen will show you the points you will receive if
you pop that group. If you're interested, the formula for bubble points
is: <b>n * (n-1)</b>, where 'n' is the total number of bubbles in the
selected group. </p>


<h3>Strategy</h3>
<p>Since larger groups of bubbles score more points
than smaller groups, you should try to get as many bubbles of the same
color together as you can. Keep in mind that while a group of 10 bubbles
would score 90 points, two groups of 5 bubbles each would only score 40
points. And 5 groups of 2 bubbles is only worth 10 points! So even
though you're popping the same number of bubbles, you'll do much better
by trying to pop as many at once. </p>

<p>The other thing to keep in mind is that to get really high scores,
you need a fresh supply of bubbles! The only way to do that is to
completely pop a column, so try to arrange the bubbles so that a column
is all the same color. If you have two bubbles next to each other
horizontally, and they are the only bubbles in their columns, you'll get
two fresh columns of bubbles when you pop them. </p>


<h3>End of Game</h3>
<p>When there are no longer any adjacent bubbles
of the same color, the game is over. Your score will be added to the
statistics, which keeps track of your high game, as well as the total
number of games you've played and your average score for those games.</p>
"""
