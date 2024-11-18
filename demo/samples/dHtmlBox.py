# -*- coding: utf-8 -*-
import datetime

import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dButton
from dabo.ui import dEditBox

dHtmlBox = dabo.ui.dHtmlBox


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v")
        sz.appendSpacer(25)

        self.htmlbox = dHtmlBox(self, Source=self.getPageData())
        sz.append(self.htmlbox, 2, "x", border=10)
        sz.appendSpacer(10)

        lbl = dLabel(
            self,
            FontBold=True,
            FontItalic=True,
            ForeColor="blue",
            WordWrap=True,
            Caption="The HTML text below is the Source for the dHtmlBox.\nEdit it to changed the displayed HTML.",
            Alignment="Center",
        )
        lbl.FontSize -= 5
        sz.append(lbl, halign="center")
        sz.appendSpacer(2)

        eb = dEditBox(self, DataSource=self.htmlbox, DataField="Source")
        eb.bindEvent(dEvents.KeyChar, self.textChangeHandler)
        sz.append1x(eb)
        sz.appendSpacer(2)
        btn = dButton(self, Caption="Reset", OnHit=self.resetHTML)
        sz.append(btn, halign="right", border=10, borderSides=["right", "bottom"])
        self.layout()

    def textChangeHandler(self, evt):
        dabo.ui.callAfter(evt.EventObject.flushValue)

    def resetHTML(self, evt):
        self.htmlbox.Source = self.getPageData()
        self.update()

    def getPageData(self):
        return (
            """<html>
        <body bgcolor="pink">
        <center>
            <table bgcolor="#8470FF" width="100%%" cellspacing="0" cellpadding="0"
                    border="1">
                <tr>
                    <td align="center"><h1>dHtmlBox</h1></td>
                </tr>
            </table>
        </center>
        <p><b><font size="+2" color="#FFFFFF">dHtmlBox</font></b> is a Dabo UI widget that is designed to display html text.
        Be careful, though, because the widget doesn't support advanced functions like
        Javascript parsing.</p>
        <p>It's better to think of it as a way to display <b>rich text</b> using
        <font size="+1" color="#993300">HTML markup</font>, rather
        than a web browser replacement, although you <i>can</i> create links that will open
        in a web browser, like this: <a href="http://wiki.dabodev.com">Dabo Wiki</a>.</p>

        <p>&nbsp;</p>
        <div align="center"><img src="daboIcon.ico"></div>

        <p align="center"><b><a href="http://dabodev.com">Dabo</a></b> is brought to you by <b>Ed Leafe</b>, <b>Paul McNett</b>,
        and others in the open source community. Copyright &copy; 2004-%s
        </p>
        </body>
        </html>
        """
            % datetime.date.today().year
        )


category = "Controls.dHtmlBox"

overview = """
<b>dHtmlBox</b> creates a scrolled panel that can load and display html pages

The Html Window can load any html text, file, or url that is fed to it. It is somewhat limited in the complexity of HTML that it can render; it doesn't understand CSS or JavaScript. It's best to think of this not as a web browser, but as a way to display rich text that happens to be formatted with HTML markup.
"""
