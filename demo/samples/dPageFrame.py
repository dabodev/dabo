# -*- coding: utf-8 -*-
import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer

from dabo.ui import dDropdownList
from dabo.ui import dGridSizer
from dabo.ui import dBorderSizer

dPageFrame = dabo.ui.dPageFrame


class TestPanel(dPanel):
    def afterInit(self):
        self.currentTabPosition = "Top"
        sz = self.Sizer = dSizer("v")
        pgf = self.createPageFrame()
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

    def createPageFrame(self):
        try:
            self.pgf.release()
        except AttributeError:
            pass
        self.pgf = dPageFrame(
            self, TabPosition=self.currentTabPosition, OnPageChanged=self.onPageChanged
        )
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

The current dPageFrame control will be destroyed,
and a new control with the position you selected
will then be created."""
                dabo.ui.info(msg, "TabPosition Limitation")
            self.currentTabPosition = newpos
            self.createPageFrame()
            # Need to update the


#         gsz = dGridSizer(MaxCols=2)
#         for num, pos in enumerate(("Top", "Right", "Bottom", "Left")):
#             pgf = dPageFrame(self, TabPosition=pos,
#                 OnPageChanged=self.onPageChanged)
#             pgf.appendPage(caption="First", BackColor="blue")
#             pgf.appendPage(caption="Second", BackColor="salmon")
#             pgf.appendPage(caption="Third", BackColor="darkred")
#             pgf.appendPage(caption="Fourth", BackColor="green")
#             pgf.SelectedPageNumber = num
#             bsz = dBorderSizer(self, Caption=pos)
#             bsz.append1x(pgf)
#             gsz.append(bsz, "x", border=10)
#         gsz.setColExpand(True, "all")
#         gsz.setRowExpand(True, "all")
#         self.Sizer.append1x(gsz)
#
#     def onPageChanged(self, evt):
#         self.Form.logit("TabPosition: %s; page number changed from %s to %s" %
#                 (evt.EventObject.TabPosition, evt.oldPageNum, evt.newPageNum))


category = "Controls.dPageFrame"

overview = """
<p><b>Paged Controls</b> allow you to organize the visual presentation of
your data and UI controls onto separate 'pages' that are selected by various
means. Only one page is visible at any given time.</p>

<p>The following are all the paged control classes in Dabo:
<ul>
    <li>dPageFrame</li>
    <li>dPageToolBar</li>
    <li>dPageList</li>
    <li>dPageSelect</li>
    <li>dDockTabs</li>
</ul>
</p>

<p><b>dPageFrame</b> is the most basic of the paged controls. The user can
select the page they want by clicking on one of several tabs that are located along
one edge of the control. Each page can have a Caption that will be displayed on
the tab. The appearance of the tabs is controlled by the OS, not Dabo.</p>
"""
