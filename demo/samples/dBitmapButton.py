# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class TestPanel(dabo.ui.dPanel):
	def afterInit(self):
		sz = self.Sizer = dabo.ui.dSizer("v", DefaultBorder=20,
				DefaultBorderLeft=True)
		sz.appendSpacer(25)

		lbl = dabo.ui.dLabel(self, Alignment="Center", Width=400, WordWrap=True)
		lbl.Caption = "Below are three dBitmapButtons. They will normally " + \
				"display the Ace of Spades, but when the mouse hovers over them, their " + \
				"normal image will be the Ace of Hearts. If you click on them, the image " + \
				"will change to the King of Spades for as long as you hold the mouse down."
		sz.append(lbl, halign="center")
		if self.Application.Platform == "Mac":
			lbl = dabo.ui.dLabel(self, FontItalic=True,
					Caption="These effects don't display on Mac OS X, unfortunately")
			lbl.FontSize -= 2
			sz.appendSpacer(5)
			sz.append(lbl, halign="center")
		sz.appendSpacer(10)

		hsz = dabo.ui.dSizer("h")
		btn = dabo.ui.dBitmapButton(self, Picture="media/cards/small/s1.png",
				FocusPicture="media/cards/small/h1.png", DownPicture="media/cards/small/s13.png",
				Height=80, Width=80)
		btn.bindEvent(dEvents.Hit, self.onButtonHit)
		hsz.append(btn)
		sz.appendSpacer(10)

		btn = dabo.ui.dBitmapButton(self, Picture="media/cards/small/s1.png",
				FocusPicture="media/cards/small/h1.png", DownPicture="media/cards/small/s13.png",
				Height=80, Width=80)
		btn.bindEvent(dEvents.Hit, self.onButtonHit)
		hsz.append(btn)

		btn = dabo.ui.dBitmapButton(self, Picture="media/cards/small/s1.png",
				FocusPicture="media/cards/small/h1.png", DownPicture="media/cards/small/s13.png",
				Height=80, Width=80)
		btn.bindEvent(dEvents.Hit, self.onButtonHit)
		hsz.append(btn)

		sz.append(hsz, halign="center")


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
