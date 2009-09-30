#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo is like invoice.py, but shows how to use the progress dialog.
"""
import dabo
dabo.ui.loadUI("wx")
from dabo.dReportWriter import dReportWriter
from dabo.lib import reportUtils

class ReportingForm(dabo.ui.dForm):
	def initProperties(self):
		self.Caption = "Invoice Report"

	def afterInit(self):
		ms = self.Sizer = dabo.ui.dSizer("v")
		ms.append(dabo.ui.dLabel(self, Caption="Invoice Report with Cancelable Progress Output"), "expand")
		self.progress = dabo.ui.dReportProgress(self)
		ms.append(self.progress)
		ms.append(dabo.ui.dButton(self, Caption="Preview", OnHit=self.onPreview))
		self.fitToSizer()

	def onPreview(self, evt):
		self.SaveRestorePosition = False
		self.preview()

	def preview(self):
		rw = dReportWriter()
		rw.ReportFormFile = "invoice.rfxml"
		rw.OutputFile = "invoice.pdf"
		rw.UseTestCursor = True
		rw.bindEvent(dabo.dEvents.ReportEnd, self.onReportEnd)
		rw.ProgressControl = self.progress
		self.progress.ReportWriter = rw
		rw.write()

	def onReportEnd(self, evt):
		"""Will be called only if the user didn't cancel; you could also bind to
		ReportCancel to set a flag, but this seemed cleaner."""
		print "report end"
		reportUtils.previewPDF("invoice.pdf")


app = dabo.dApp(MainFormClass=ReportingForm)
app.start()

