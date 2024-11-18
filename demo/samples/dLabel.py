# -*- coding: utf-8 -*-
import dabo
import dabo.ui
import dabo.dEvents as dEvents
from dabo.dLocalize import _


from dabo.ui import dPanel
from dabo.ui import dSizer
from dabo.ui import dTextBox
from dabo.ui import dButton
from dabo.ui import dCheckBox
from dabo.ui import dDialog
from dabo.ui import dLine
from dabo.ui import dSlider

dLabel = dabo.ui.dLabel


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v")
        sz.appendSpacer(20)

        # Plain Label
        lbl = dLabel(self, Caption=_("This label has the default font."))
        sz.append(lbl)

        lbl = dLabel(self, Caption=_("FontSize 5 points bigger"))
        lbl.FontSize += 5
        sz.append(lbl)

        lbl = dLabel(self, Caption=_("FontSize 10 points bigger"))
        lbl.FontSize += 10
        sz.append(lbl)

        lbl = dLabel(self, Caption=_("FontSize = 64"))
        lbl.FontSize = 64
        sz.append(lbl)

        lbl = dLabel(self, Caption=_("FontFace = Courier"))
        lbl.FontFace = _("Courier")
        sz.append(lbl)

        lbl = dLabel(self, Caption=_("FontBold = True"))
        lbl.FontBold = True
        sz.append(lbl)

        lbl = dLabel(self, Caption=_("FontItalic = True"))
        lbl.FontItalic = True
        sz.append(lbl)

        lbl = dLabel(self, Caption=_("FontBold and FontItalic = True"))
        lbl.FontBold = True
        lbl.FontItalic = True
        sz.append(lbl)

        lbl = dLabel(self, Caption=_("ForeColor = 'red'"))
        lbl.ForeColor = "red"
        sz.append(lbl)

        lbl = dLabel(self, Caption=_("BackColor = 'yellow'"))
        lbl.BackColor = "yellow"
        sz.append(lbl)

        lbl = self.dynamicLabel = dLabel(self, Caption="")
        lbl.DynamicFontSize = lambda: self.Width * 0.05
        lbl.DynamicCaption = self.getDynamicCaption
        sz.append(lbl)
        dabo.ui.callAfterInterval(200, self.update)

        sz.appendSpacer(20)
        sz.append(dLine(self, Width=500), halign="Center")
        sz.appendSpacer(20)

        btn = dButton(self, Caption=_("Show WordWrap demo"))
        btn.bindEvent(dEvents.Hit, self.onShowWWDemo)
        sz.append(btn, halign="center")

    def getDynamicCaption(self):
        return "DynamicFontSize: %s" % int(round(self.dynamicLabel.FontSize, 0))

    def onShowWWDemo(self, evt):
        class WordWrapDialog(dDialog):
            def addControls(self):
                sz = self.Sizer
                sz.appendSpacer(25)

                lbl = dLabel(
                    self,
                    FontBold=True,
                    ForeColor="darkred",
                    WordWrap=True,
                    Alignment="center",
                    Caption=_(
                        "The label below has WordWrap=True. "
                        + "Use the slider to resize the label to see it in action."
                    ),
                )
                lbl.FontSize += 1
                sz.append(lbl, "x", border=40, borderSides=("Left", "Right"))

                sld = self.slider = dSlider(self, Value=100, Continuous=False)
                sld.bindEvent(dEvents.Hit, self.onSlider)
                sld.bindEvent(dEvents.Resize, self.onSlider)
                sz.append(sld, "x", border=10)

                txt = getGettyAddr()
                lbl = self.gettyLabel = dLabel(self, Caption=txt, WordWrap=True)
                sz.append(lbl, 1, border=10)

                self.Caption = _("WordWrap Demo")
                self.Width = 640
                self.Height = 480
                self.layout()

            def onSlider(self, evt):
                wd = (self.slider.Value / 100.0) * self.slider.Width
                try:
                    self.gettyLabel.Width = wd
                except AttributeError:
                    # Dialog is just starting up
                    pass

        dlg = WordWrapDialog(self, BorderResizable=True, AutoSize=False, Centered=True)
        dlg.show()


def getGettyAddr():
    """Return Lincoln's Gettysburg Address."""
    return " ".join(
        [
            "Four score and seven years ago our fathers brought",
            "forth on this continent a new nation, conceived in liberty and",
            "dedicated to the proposition that all men are created equal.",
            "Now we are engaged in a great civil war, testing whether that",
            "nation or any nation so conceived and so dedicated can long",
            "endure. We are met on a great battlefield of that war. We have",
            "come to dedicate a portion of that field as a final resting-place",
            "for those who here gave their lives that that nation might live.",
            "It is altogether fitting and proper that we should do this. But in",
            "a larger sense, we cannot dedicate, we cannot consecrate, we",
            "cannot hallow this ground. The brave men, living and dead",
            "who struggled here have consecrated it far above our poor",
            "power to add or detract. The world will little note nor long",
            "remember what we say here, but it can never forget what they",
            "did here. It is for us the living rather to be dedicated here to",
            "the unfinished work which they who fought here have thus far",
            "so nobly advanced. It is rather for us to be here dedicated to",
            "the great task remaining before us --that from these honored",
            "dead we take increased devotion to that cause for which they",
            "gave the last full measure of devotion-- that we here highly",
            "resolve that these dead shall not have died in vain, that this",
            "nation under God shall have a new birth of freedom, and that",
            "government of the people, by the people, for the people shall",
            "not perish from the earth.",
        ]
    )


category = "Controls.dLabel"

overview = _("""
<p>The <b>dLabel</b> class is used to display text. It is not editable, and under
some platforms, cannot receive events. </p>

<p>It is typically used to denote what value an adjacent control represents,
or to provide information to the user.</p>
""")
