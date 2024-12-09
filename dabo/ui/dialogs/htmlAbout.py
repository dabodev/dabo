# -*- coding: utf-8 -*-
import os
import string
import sys

from ...dLocalize import _
from .. import (
    dBitmapButton,
    dButton,
    dColumn,
    dDialog,
    dGrid,
    dHtmlBox,
    dLabel,
    dMenu,
    dPanel,
    dSizer,
)


class HtmlAbout(dDialog):
    def initProperties(self):
        self.AutoSize = True
        self.Centered = True
        self.Caption = _("About")

    def initEvents(self):
        self.bindKey("space", self.onClear)
        self.bindKey("enter", self.onClear)

    def addControls(self):
        pnlBack = dPanel(self, BackColor="cornflowerblue")
        self.Sizer.append1x(pnlBack)
        pnlBack.Sizer = sz = dSizer("v")

        self.htmlBox = dHtmlBox(self)
        self.htmlBox.Size = (400, 300)
        sz.append(self.htmlBox, 1, halign="center", valign="center", border=30)

        # Copy info
        btnCopy = dButton(pnlBack, Caption=_("Copy Info"), OnHit=self.onCopyInfo)
        btnClose = dButton(pnlBack, Caption=_("OK"), OnHit=self.onClear)
        hsz = dSizer("H")
        hsz.append(btnCopy)
        hsz.appendSpacer(20)
        hsz.append(btnClose)
        sz.append(hsz, halign="right", border=30, borderSides=["right"])
        sz.append((0, 20))
        self.Layout()
        self.htmlBox.Source = self.writeHtmlPage()

    def writeHtmlPage(self):
        app = self.Application
        caption = "Dabo"
        if app:
            caption = "%s %s" % (
                app.getAppInfo("appName"),
                app.getAppInfo("appVersion"),
            )
        appinfo = ui.getSystemInfo("html")
        docstring = self.getAppSpecificString()
        return self.getPageData() % locals()

    def getAppSpecificString(self):
        app = self.Application
        if app:
            text = app.addToAbout()
            if text:
                return text
        return ""

    def onCopyInfo(self, evt):
        """Copy the system information to the Clipboard"""
        info = ui.getSystemInfo("string")
        appdoc = self.getAppSpecificString()
        self.Application.copyToClipboard("\n\n".join((info, appdoc)))

    def onClear(self, evt):
        self.release()

    def getPageData(self):
        """Basic Template structure of the About box."""
        return """
<html>
    <body bgcolor="#DDDDFF">
        <h1 align="center"><b>%(caption)s</b></h1>
        <p>%(appinfo)s</p>
        <hr />
        <p><font size="-1">%(docstring)s</font></p>
    </body>
</html>
"""


def main():
    from .application import dApp

    app = dApp()
    app.MainFormClass = None
    app.setup()
    app.MainForm = HtmlAbout(None)
    app.MainForm.show()
    app.start()


if __name__ == "__main__":
    main()
