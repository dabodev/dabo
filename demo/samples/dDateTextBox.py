# -*- coding: utf-8 -*-
import datetime

import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer

dDateTextBox = dabo.ui.dDateTextBox


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v", DefaultBorder=20, DefaultBorderLeft=True)
        sz.appendSpacer(25)

        intro = (
            "dDateTextBox is a specialized text control designed to make it easy to "
            + "display and maniputate date values. It features several shortcut keystrokes "
            + "that enable you to quickly navigate to the desired date value.\n\nYou can see "
            + "the available keystrokes by hovering the mouse cursor over the control "
            + "to display the ToolTip."
        )
        lbl = dLabel(
            self,
            Caption=intro,
            ForeColor="darkblue",
            FontBold=True,
            WordWrap=True,
            Alignment="center",
        )
        sz.append(lbl, "x", halign="center")
        sz.appendSpacer(10)
        txt = dDateTextBox(self, Value=datetime.date.today(), FontSize=18, Height=36, Width=180)
        sz.append(txt, halign="center")
        dabo.ui.callAfter(self.layout)


category = "Controls.dDateTextBox"

overview = """
<p>The dDateTextBox class is a specialized subclass of dTextBox. It is
optimized for handling date values, and includes a popup calendar
for selecting date values.</p>

<p>It also features several keyboard shortcuts for quickly changing the
date. If you are familiar with the behavior of date fields in the personal
finance program '<b>Quicken</b>', you will recognize these keys. They are:</p>

<div align="center">
<table border="1">
    <tr bgcolor="#CCCCCC">
        <th>Key</th>
        <th>Action</th>
    </tr>
    <tr>
        <td align="center">T</td> <td><b>T</b>oday</td>
    </tr>
    <tr>
        <td align="center">+</td> <td>Up One Day</td>
    </tr>
    <tr>
        <td align="center">-</td> <td>Down One Day</td>
    </tr>
    <tr>
        <td align="center">[</td> <td>Up One Month</td>
    </tr>
    <tr>
        <td align="center">]</td> <td>Down One Month</td>
    </tr>
    <tr>
        <td align="center">M</td> <td>First Day of <b>M</b>onth</td>
    </tr>
    <tr>
        <td align="center">H</td> <td>Last Day of mont<b>H</b></td>
    </tr>
    <tr>
        <td align="center">Y</td> <td>First Day of <b>Y</b>ear</td>
    </tr>
    <tr>
        <td align="center">R</td> <td>Last Day of yea<b>R</b></td>
    </tr>
    <tr>
        <td align="center">C</td> <td>Display the Popup <b>C</b>alendar</td>
    </tr>
</table>
</div>
"""
