#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo is like invoice.py, but shows how to use the progress dialog.
"""

from .. import ui
from ..application import dApp
from ..dReportWriter import dReportWriter
from ..lib import reportUtils


class ReportingForm(ui.dForm):
    def initProperties(self):
        self.Caption = "Invoice Report"
        self.BorderResizable = False

    def afterInit(self):
        ms = self.Sizer = ui.dSizer("v")
        ms.append(
            ui.dLabel(self, Caption="Invoice Report with Cancelable Progress Output"),
            "expand",
        )
        self.progress = ui.dReportProgress(self)
        ms.append(self.progress)
        ms.append(ui.dButton(self, Caption="Preview", OnHit=self.onPreview))
        self.Size = (400, 300)

    def onPreview(self, evt):
        self.preview()

    def preview(self):
        rw = dReportWriter()
        rw.ReportFormFile = "invoice.rfxml"
        rw.OutputFile = "invoice.pdf"
        rw.UseTestCursor = True
        rw.bindEvent(dabo.dEvents.ReportEnd, self.onReportEnd)
        rw.ProgressControl = self.progress
        self.progress.ProcessObject = rw
        rw.write()

    def onReportEnd(self, evt):
        """Will be called only if the user didn't cancel; you could also bind to
        ReportCancel to set a flag, but this seemed cleaner."""
        print("report end")
        reportUtils.previewPDF("invoice.pdf")


dApp(MainFormClass=ReportingForm).start()
