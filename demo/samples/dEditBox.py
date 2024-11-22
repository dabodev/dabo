# -*- coding: utf-8 -*-
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import dButton
from dabo.ui import dLabel
from dabo.ui import dPanel
from dabo.ui import dSizer

dEditBox = dabo.ui.dEditBox


class TestPanel(dPanel):
    def afterInit(self):
        sz = self.Sizer = dSizer("v")
        sz.appendSpacer(25)

        self.edt = dEditBox(self, Width=400, Height=200)
        self.edt.Value = self.getGetty()
        sz.append(self.edt, halign="center")
        sz.appendSpacer(10)

        btn = dButton(self, Caption="Selection Info")
        btn.bindEvent(dEvents.Hit, self.onSelectionInfo)
        sz.append(btn, halign="center")

    def onSelectionInfo(self, evt):
        self.Form.logit(_("Selected Text: %s") % self.edt.SelectedText)
        self.Form.logit(_("Selection Start position: %s") % self.edt.SelectionStart)
        self.Form.logit(_("Selection End position: %s") % self.edt.SelectionEnd)
        self.Form.logit(_("Character before InsertionPoint: %s") % self.edt.charsBeforeCursor())
        self.Form.logit(_("Character after InsertionPoint: %s") % self.edt.charsAfterCursor())

    def getGetty(self):
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


category = "Controls.dEditBox"

overview = """
<p>The <b>dEditBox</b> class allows text to be displayed and edited (if desired).
It is best suited for cases where there can be a large amount of text
that needs to be displayed in a small area on the screen. You should
use <b>dTextBox</b> instead if you only need to display a single line of text.</p>
"""
