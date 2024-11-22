# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dDropdownList
from dabo.ui import dDockTabs
from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer


class TestPanel(dPanel):
    def afterInit(self):
        self.currentTabPosition = "Top"
        sz = self.Sizer = dSizer("v")
        pgf = self.createDockTabs()
        sz.appendSpacer(10)
        hsz = dSizer("h")
        lbl = dLabel(self, Caption="Tab Position:")
        dd = self.ddPos = dDropdownList(
            self, Choices=["Top", "Bottom"], DataSource=pgf, DataField="TabPosition"
        )
        hsz.append(lbl)
        hsz.appendSpacer(3)
        hsz.append(dd)
        sz.append(hsz, halign="center")
        sz.appendSpacer(20)

    def createDockTabs(self):
        try:
            self.pgf.release()
        except AttributeError:
            pass
        self.pgf = dDockTabs(
            self, TabPosition=self.currentTabPosition, OnPageChanged=self.onPageChanged
        )
        # Now add the pages, specifying which image key is displayed for each page.
        pg = self.pgf.appendPage(caption="First")
        pg.BackColor = "blue"
        pg = self.pgf.appendPage(caption="Second")
        pg.BackColor = "salmon"
        pg = self.pgf.appendPage(caption="Third")
        pg.BackColor = "darkred"
        pg = self.pgf.appendPage(caption="Fourth")
        pg.BackColor = "green"
        self.Sizer.insert(0, self.pgf, "x", 1)
        self.layout()
        return self.pgf

    def onPageChanged(self, evt):
        self.Form.logit("Page number changed from %s to %s" % (evt.oldPageNum, evt.newPageNum))


category = "Controls.dDockTabs"

overview = """
<p><b>Paged Controls</b> allow you to organize the visual presentation of
your data and UI controls onto separate 'pages' that are selected by various
means. Only one page is visible at any given time.</p>

<p><b>dDockTabs</b> is a variation on the common tabbed page control.
The tabs are fully draggable, allowing you to not only re-arrange their order, but
also detach them and dock their page to any edge of the control. You can place the
tabs at the top or bottom of the pages, and change that interactively. dDockTabs
does not support tabs on the left or right sides, though.
</p>
"""
