# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import dBitmapButton

from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dBorderSizer

dBitmapButton = dabo.ui.dBitmapButton


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v", DefaultBorder=20, DefaultBorderLeft=True)
        sz.appendSpacer(25)

        lbl = dLabel(self, Alignment="Center", ForeColor="darkblue", Width=500, WordWrap=True)
        lbl.FontSize -= 3
        lbl.Caption = (
            "Below are three dBitmapButtons. They will normally "
            + "display the Ace of Spades, but when the mouse hovers over them, their "
            + "normal image will be the Ace of Hearts. If you click on them, the image "
            + "will change to the King of Spades for as long as you hold the mouse down."
        )
        bsz = dBorderSizer(self, "v")
        bsz.append(lbl, halign="center")
        plat = self.Application.Platform
        if plat == "Mac":
            cap = "These effects don't display on Mac OS X, unfortunately"
        elif plat == "GTK":
            cap = "Some of these effects don't display correctly on Gtk"
        else:
            cap = ""
        if cap:
            lbl = dLabel(self, FontItalic=True, Caption=cap)
            lbl.FontSize -= 4
            bsz.appendSpacer(5)
            bsz.append(lbl, halign="center")
        sz.append(bsz, halign="center")
        sz.appendSpacer(20)

        hsz = dSizer("h")
        btn = dBitmapButton(
            self,
            Picture="media/cards/small/s1.png",
            FocusPicture="media/cards/small/h1.png",
            DownPicture="media/cards/small/s13.png",
            Height=80,
            Width=80,
        )
        btn.bindEvent(dEvents.Hit, self.onButtonHit)
        hsz.append(btn)
        sz.appendSpacer(10)

        btn = dBitmapButton(
            self,
            Picture="media/cards/small/s1.png",
            FocusPicture="media/cards/small/h1.png",
            DownPicture="media/cards/small/s13.png",
            Height=80,
            Width=80,
        )
        btn.bindEvent(dEvents.Hit, self.onButtonHit)
        hsz.append(btn)

        btn = dBitmapButton(
            self,
            Picture="media/cards/small/s1.png",
            FocusPicture="media/cards/small/h1.png",
            DownPicture="media/cards/small/s13.png",
            Height=80,
            Width=80,
        )
        btn.bindEvent(dEvents.Hit, self.onButtonHit)
        hsz.append(btn)

        sz.append(hsz, halign="center")
        sz.layout()

    def onButtonHit(self, evt):
        obj = evt.EventObject
        self.Form.logit(_("Button Hit!"))


category = "Controls.dBitmapButton"

overview = """
<p>The <b>dBitmapButton</b> class is used much like the dButton class. The
difference, of course, is that instead of displaying text, it displays an image.</p>

<p>The <b>Picture</b> property determines the image that is displayed. If you want, you can
also specify a <b>DownPicture</b>, which is displayed when the button is depressed. You
can also specify a <b>FocusPicture</b>, which is displayed when the button has focus.</p>
"""
