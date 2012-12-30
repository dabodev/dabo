# -*- coding: utf-8 -*-
import dabo
from dabo.dLocalize import _
from dabo.lib.reportWriter import ReportWriter
from dabo.dObject import dObject
import dabo.dEvents as dEvents

# dReportWriter is simply a raw ReportWriter/dObject mixin:
class dReportWriter(dObject, ReportWriter):
	"""The Dabo Report Writer Engine, which mixes a data cursor and a report
	format file (.rfxml) to output a PDF.

	For each row in the Cursor, a detail band is printed. For each page in the
	report, the pageBackground, pageHeader, pageFooter, and pageForeground
	bands are printed. For each defined grouping, the groupHeader and groupFooter
	bands are printed.

	Report variables can be defined as accumulators, or for any purpose you
	need. All properties of the report form are evaluated at runtime, so that
	you can achieve full flexibility and ultimate control.

	There is also a pure-python interface available.
	"""

	def _onReportCancel(self):
		super(dReportWriter, self)._onReportCancel()
		self.raiseEvent(dEvents.ReportCancel)
		self._hideProgress()

	def _onReportBegin(self):
		super(dReportWriter, self)._onReportBegin()
		self.raiseEvent(dEvents.ReportBegin)
		self._showProgress()

	def _onReportEnd(self):
		super(dReportWriter, self)._onReportEnd()
		self.raiseEvent(dEvents.ReportEnd)
		self._updateProgress(force=True)
		#self._hideProgress()  ## Let the form controlling the progress gauge do this (less blinky)

	def _onReportIteration(self):
		super(dReportWriter, self)._onReportIteration()
		self.raiseEvent(dEvents.ReportIteration)
		self._updateProgress()

	def _showProgress(self):
		win = self.ProgressControl
		if win:
			win.Caption = "Processing %s..." % self.ReportForm.getProp("Title")
			win.updateProgress(0, len(self.Cursor))
			win.show()
			win.Form.fitToSizer()

	def _updateProgress(self, force=False):
		if force or self.RecordNumber % 10 == 0:
			win = self.ProgressControl
			if win:
				win.updateProgress(self.RecordNumber, len(self.Cursor))
				dabo.ui.yieldUI(_safe=True)

	def _hideProgress(self):
		win = self.ProgressControl
		if win:
			win.hide()
			win.Form.fitToSizer()
			dabo.ui.yieldUI(_safe=True)

	def _getEncoding(self):
		try:
			v = self._encoding
		except AttributeError:
			v = dabo.getEncoding()
			self._encoding = v
		return v

	def _setEncoding(self, val):
		self._encoding = val


	def _getHomeDirectory(self):
		try:
			v = self._homeDirectory
		except AttributeError:
			v = self._homeDirectory = self.Application.HomeDirectory
		return v

	def _setHomeDirectory(self, val):
		self._homeDirectory = val


	def _getProgressControl(self):
		try:
			v = self._progressControl
		except AttributeError:
			v = self._progressControl = None
		return v

	def _setProgressControl(self, val):
		self._progressControl = val


	Encoding = property(_getEncoding, _setEncoding, None,
		_("Specifies the encoding for unicode strings.  (str)"))

	HomeDirectory = property(_getHomeDirectory, _setHomeDirectory, None,
		_("""Specifies the home directory for the report.

		Resources on disk (image files, etc.) will be looked for relative to the
		HomeDirectory if specified with relative pathing. The HomeDirectory should
		be the directory that contains the report form file. If you set
		self.ReportFormFile, HomeDirectory will be set for you automatically.
		Otherwise, it will get set to self.Application.HomeDirectory."""))

	ProgressControl = property(_getProgressControl, _setProgressControl, None,
		_("""Specifies the control to receive progress updates.

		The specified control will be updated with every record processed. It must have
		a updateProgress(current_row, num_rows) method.

		For the default control, use dabo.ui.dReportProgress.
		"""))

if __name__ == "__main__":
	## run a test:
	rw = dReportWriter(Name="dReportWriter1", OutputFile="./dRW-test.pdf")
	print rw.Name, rw.Application

	xml = """

<report>
	<title>Test Report from dReportWriter</title>

	<testcursor iid="int" cArtist="str">
		<record iid="1" cArtist='"The Clash"' />
		<record iid="2" cArtist='"Queen"' />
		<record iid="3" cArtist='"Metallica"' />
		<record iid="3" cArtist='"The Boomtown Rats"' />
	</testcursor>

	<page>
		<size>"letter"</size>
		<orientation>"portrait"</orientation>
		<marginLeft>".5 in"</marginLeft>
		<marginRight>".5 in"</marginRight>
		<marginTop>".5 in"</marginTop>
		<marginBottom>".5 in"</marginBottom>
	</page>

	<pageHeader>
		<height>"0.5 in"</height>
		<objects>
			<string>
				<expr>self.ReportForm["title"]</expr>
				<align>"center"</align>
				<x>"3.75 in"</x>
				<y>".3 in"</y>
				<hAnchor>"center"</hAnchor>
				<width>"6 in"</width>
				<height>".25 in"</height>
				<borderWidth>"0 pt"</borderWidth>
				<fontName>"Helvetica"</fontName>
				<fontSize>14</fontSize>
			</string>
		</objects>
	</pageHeader>

	<pageFooter>
		<height>"0.75 in"</height>
		<objects>
			<string>
				<expr>"(also see the test in dabo/lib/reporting)"</expr>
				<align>"right"</align>
				<hAnchor>"right"</hAnchor>
				<x>self.Bands["pageFooter"]["width"]-1</x>
				<y>"0 in"</y>
				<width>"6 in"</width>
			</string>
		</objects>
	</pageFooter>

	<detail>
		<height>".25 in"</height>
		<objects>
			<string>
				<expr>self.Record['cArtist']</expr>
				<width>"6 in"</width>
				<x>"1.25 in"</x>
			</string>
		</objects>
	</detail>

	<pageBackground></pageBackground>

</report>
"""
	rw.ReportFormXML = xml
	rw.UseTestCursor = True
	rw.write()
