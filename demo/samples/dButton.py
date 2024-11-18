# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _

# from dabo.ui import dButtton
from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer

dButton = dabo.ui.dButton


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v", DefaultBorder=20, DefaultBorderLeft=True)
        sz.appendSpacer(25)

        btn = dButton(self, Caption="Normal")
        btn.bindEvent(dEvents.Hit, self.onButtonHit)
        sz.append(btn, halign="center")
        sz.appendSpacer(10)

        btn = dButton(self, Caption="Default", DefaultButton=True)
        btn.bindEvent(dEvents.Hit, self.onButtonHit)
        sz.append(btn, halign="center")
        sz.appendSpacer(10)

        btn = dButton(self, Caption="Cancel", CancelButton=True)
        btn.bindEvent(dEvents.Hit, self.onButtonHit)
        sz.append(btn, halign="center")
        sz.appendSpacer(10)

    def onButtonHit(self, evt):
        obj = evt.EventObject
        cap, dft, cncl = obj.Caption, obj.DefaultButton, obj.CancelButton
        self.Form.logit(_("Hit: %(cap)s; Default=%(dft)s; Cancel=%(cncl)s") % locals())


category = "Controls.dButton"

overview = """
<p>The <b>dButton</b> class is used anywhere you want to let your user click in
order to start some action. You can display a text prompt on the button
by setting its Caption property.</p>

<p>Two other properties affect behavior: <b>DefaultButton</b> and
<b>CancelButton</b>. When DefaultButton is True, the button will respond
when the user presses the 'Enter' key as if it had been clicked. When CancelButton
is True, it responds to pressing the 'Escape' key as if it were clicked.</p>
"""
