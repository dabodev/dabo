# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.lib.utils import ustr


from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dLed

from dabo.ui import dGridSizer

dTextBox = dabo.ui.dTextBox


class TestPanel(dPanel):
    def afterInit(self):
        self.Sizer = dSizer("v")
        sz = dGridSizer(MaxCols=2, HGap=7, VGap=12)
        self.Sizer.append(sz, "x", border=30, valign="middle")

        # Plain textbox
        lbl = dLabel(self, Caption=_("Plain TextBox"))
        txt = dTextBox(self, Name=_("PlainTextBox"), Value=_("Test it out and see"))
        txt.SelectionStart = 0
        sz.append(lbl, halign="right")
        sz.append(txt, "x")

        txt.bindEvent(dEvents.GotFocus, self.onTextGotFocus)
        txt.bindEvent(dEvents.LostFocus, self.onTextLostFocus)
        txt.bindEvent(dEvents.Destroy, self.onTextDestroy)
        txt.bindEvent(dEvents.KeyChar, self.onTextKeyChar)
        txt.bindEvent(dEvents.Hit, self.onTextHit)

        # Password textbox
        lbl = dLabel(self, Caption=_("Password"))
        txt = dTextBox(self, Name=_("Password TextBox"), PasswordEntry=True)
        sz.append(lbl, halign="right")
        sz.append(txt, "x")

        txt.bindEvent(dEvents.GotFocus, self.onTextGotFocus)
        txt.bindEvent(dEvents.LostFocus, self.onTextLostFocus)
        txt.bindEvent(dEvents.Destroy, self.onTextDestroy)
        txt.bindEvent(dEvents.KeyChar, self.onTextKeyChar)
        txt.bindEvent(dEvents.Hit, self.onTextHit)

        # Let the textbox column grow
        sz.setColExpand(True, 1)
        self.layout()

    def onTextGotFocus(self, evt):
        self.Form.logit(_("%s GotFocus") % evt.EventObject.Name)

    def onTextLostFocus(self, evt):
        self.Form.logit(_("%s LostFocus") % evt.EventObject.Name)

    def onTextDestroy(self, evt):
        self.Form.logit(_("%s Destroy") % evt.EventObject.Name)

    def onTextKeyChar(self, evt):
        cd, ch = evt.keyCode, ustr(evt.keyChar)
        self.Form.logit(_("KeyChar event; code=%(cd)s, char=%(ch)s") % locals())

    def onTextHit(self, evt):
        self.Form.logit(_("Hit event; new value='%s'") % evt.EventObject.Value)


category = "Controls.dTextBox"

overview = """
<p>The <b>dTextBox</b> class allows text to be displayed and edited (if desired).
It may be single line or multi-line, support styles or not, be read-only
or not, and even supports text masking for such things as passwords.</p>

<p>It is best suited for small amounts of text; for larger text blocks, you
should consider <b>dEditBox</b>, which features automatic scrolling to fit a
large amount of text in a small screen area.</p>
"""
