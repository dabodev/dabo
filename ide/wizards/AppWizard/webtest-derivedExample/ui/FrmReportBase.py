# -*- coding: utf-8 -*-
import dabo.ui
import dabo.lib.reportUtils as reportUtils


class FrmReportBase(dabo.ui.dDialog):

	def initProperties(self):
		## Do this import here: in case prerequisites aren't installed, the app 
		## will still start.
		from dabo.dReportWriter import dReportWriter

		if self.ReportName:
			self.Caption = self.ReportName
		else:
			self.Caption = "Run Report"
		self.Modal = True
		self.ReportForm = None
		self.DataSet = []
		self.ReportWriter = dReportWriter(Encoding="latin-1")
		self.SizerBorder = 7


	def addControls(self):
		preview = self.addObject(dabo.ui.dButton, Caption="Run Report", 
		                         RegID="cmdRunReport")
		hs = dabo.ui.dSizer("h")
		hs.append(preview, alignment="right", border=self.SizerBorder)
		self.Sizer.append(hs, alignment="bottom", border=self.SizerBorder)


	def onHit_cmdRunReport(self, evt):
		self.runReport()


	def requery(self):
		"""Subclasses should override to fill self.DataSet"""
		pass


	def runReport(self, requery=True):
		"""Preview the report in the default pdf viewer."""
		if requery:
			self.requery()
		f = self.write()
		reportUtils.previewPDF(f)


	def write(self):
		"""Write the report to a temporary file, and return the file name."""
		rw = self.ReportWriter
		rw.ReportFormFile = self.ReportForm
		rw.Cursor = self.DataSet
		f = rw.OutputFile = reportUtils.getTempFile()
		rw.write()
		return f

