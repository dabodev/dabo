# -*- coding: utf-8 -*-
import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer

from dabo.ui import dDropdownList

dPageSelect = dabo.ui.dPageSelect


class TestPanel(dPanel):
    def afterInit(self):
        self.currentTabPosition = "Top"
        sz = self.Sizer = dSizer("v")
        pgf = self.createPageSelect()
        sz.appendSpacer(10)
        hsz = dSizer("h")
        lbl = dLabel(self, Caption="Tab Position:")
        dd = self.ddPos = dDropdownList(
            self,
            Choices=["Top", "Right", "Bottom", "Left"],
            Value=self.currentTabPosition,
            OnHit=self.onNewPosition,
        )
        hsz.append(lbl)
        hsz.appendSpacer(3)
        hsz.append(dd)
        sz.append(hsz, halign="center")
        sz.appendSpacer(20)

    def createPageSelect(self):
        try:
            self.pgf.release()
        except AttributeError:
            pass
        self.pgf = dPageSelect(
            self, TabPosition=self.currentTabPosition, OnPageChanged=self.onPageChanged
        )
        # Now add the pages, specifying which image key is displayed for each page.
        self.pgf.appendPage(caption="First", BackColor="blue")
        self.pgf.appendPage(caption="Second", BackColor="salmon")
        self.pgf.appendPage(caption="Third", BackColor="darkred")
        self.pgf.appendPage(caption="Fourth", BackColor="green")
        self.Sizer.insert(0, self.pgf, "x", 1)
        self.layout()
        return self.pgf

    def onPageChanged(self, evt):
        self.Form.logit("Page number changed from %s to %s" % (evt.oldPageNum, evt.newPageNum))

    def onNewPosition(self, evt):
        newpos = evt.EventObject.StringValue
        if newpos != self.currentTabPosition:
            # Notify the user the first time.
            try:
                self.Form.seenTabPositionWarning
            except AttributeError:
                self.Form.seenTabPositionWarning = True
                msg = """TabPosition must be defined when the control
is created, and cannot be changed afterwards.

The current dPageSelect control will be destroyed,
and a new control with the position you selected
will then be created."""
                dabo.ui.info(msg, "TabPosition Limitation")
            self.currentTabPosition = newpos
            self.createPageSelect()


category = "Controls.dPageSelect"

overview = """
<p><b>Paged Controls</b> allow you to organize the visual presentation of
your data and UI controls onto separate 'pages' that are selected by various
means. Only one page is visible at any given time.</p>

<p><b>dPageSelect</b> is a variation on the common tabbed page control.
Instead of tabs, a dropdown list control containing the captions for the control's
pages is used to select the page to display. The dropdown is displayed along one
edge of the control.</p>
"""
