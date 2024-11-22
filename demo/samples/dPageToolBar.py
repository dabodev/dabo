# -*- coding: utf-8 -*-
import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer

from dabo.ui import dDropdownList

dPageToolBar = dabo.ui.dPageToolBar


class TestPanel(dPanel):
    def afterInit(self):
        self.currentTabPosition = "Top"
        sz = self.Sizer = dSizer("v")
        pgf = self.createPageToolBar()
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

    def createPageToolBar(self):
        try:
            self.pgf.release()
        except AttributeError:
            pass
        self.pgf = dPageToolBar(
            self, TabPosition=self.currentTabPosition, OnPageChanged=self.onPageChanged
        )
        # Add each image to the control, along with a string to use as a key value.
        self.pgf.addImage("themes/tango/32x32/actions/go-home.png", "First")
        self.pgf.addImage("themes/tango/32x32/actions/edit-clear.png", "Second")
        self.pgf.addImage("themes/tango/32x32/actions/software-update-available.png", "Third")
        self.pgf.addImage("themes/tango/32x32/actions/dialog-information.png", "Fourth")
        # Now add the pages, specifying which image key is displayed for each page.
        self.pgf.appendPage(caption="First", imgKey="First", BackColor="blue")
        self.pgf.appendPage(caption="Second", imgKey="Second", BackColor="salmon")
        self.pgf.appendPage(caption="Third", imgKey="Third", BackColor="darkred")
        self.pgf.appendPage(caption="Fourth", imgKey="Fourth", BackColor="green")
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

The current dPageToolBar control will be destroyed,
and a new control with the position you selected
will then be created."""
                dabo.ui.info(msg, "TabPosition Limitation")
            self.currentTabPosition = newpos
            self.createPageToolBar()


category = "Controls.dPageToolBar"

overview = """
<p><b>Paged Controls</b> allow you to organize the visual presentation of
your data and UI controls onto separate 'pages' that are selected by various
means. Only one page is visible at any given time.</p>

<p><b>dPageToolBar</b> is a variation on the common tabbed page control.
Instead of tabs, a toolbar is used to select the currently displayed page. The user
can select the page they want by clicking on one of the buttons in the toolbar
that is displayed along one edge of the control. To configure the images used
on the buttons, call the control's <b>addImage()</b> method, passing in the
path to the desired image (32x32 pixels), and a string that will be used as the
<b>key</b> for that image. When you add pages to the control, you also
specify the key for the image that you want to represent that page. The page's
Caption is not displayed directly; instead, it appears as a tooltip when you hover
the mouse over the toolbar icon.</p>
"""
