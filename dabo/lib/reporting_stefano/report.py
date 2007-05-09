# -*- coding: utf-8 -*-
from reportlab.pdfgen import canvas
from serialization import *
from util import *


class Report(Serializable):
	""" This object implements the report generation machinery """
	title = StringAttr('')
	page = AttributeChild('report.Page')
	testcursor = AttributeChild('report.TestCursor')

	def write(self, output, cursor):
		"Generate a pdf report by iterating through a given cursor"
		self.page.evaluate({})

		c = canvas.Canvas(output, pagesize=self.page.size)
		self.page.doLayout(self, c, cursor)
		c.save()

	def getTestCursor(self):
		for record in self.testcursor.records:
			yield record.getDict()


class TestCursor(Serializable):
	""" A sample cursor that is hardcoded inside the report object
	as a way for doing tests and debugging.
	"""
	records = ObjectListChild(['report.TestCursor.Record'])

	class Record(Serializable):
		def getDict(self):
			return self._xmlAttributes


class Page(Serializable):
	""" This object represents the actual pages of the report.

	The logic for iterating through the cursor and generating the pages
	accordingly is implemented here.
"""
## Actually, Page is probably not a good name.
## Better would be something like BandReportPageGenerator, as opposed to
## any other kind of report generation technique that could be implemented.

	marginTop = LengthAttr(36)
	marginBottom = LengthAttr(36)
	marginLeft = LengthAttr(36)
	marginRight = LengthAttr(36)
	orientation = PagesizesAttr('portrait')
	size = PagesizesAttr('letter')

	background = AttributeChild('report.Band')
	foreground = AttributeChild('report.Band')
	header = AttributeChild('report.Band')
	footer = AttributeChild('report.Band')
	detail = AttributeChild('report.Band')

	def __init__(self, **args):
		super(Page, self).__init__(**args)
		self.header = self.footer = self.background = self.foreground = self.detail = None

	def height(self):
		return self.size[1]
	height = property(height)

	def width(self):
		return self.size[0]
	width = property(width)

	def _drawHeader(self, canvas, env):
		if self.header:
			self.header.evaluateObjects(dictunion(env, {'header': self.header}))
			self.header.draw(canvas, 'header') #bandOutline * self.ShowBandOutlines)

	def _drawFooter(self, canvas, env):
		if self.footer:
			self.footer.evaluateObjects(dictunion(env, {'footer': self.footer}))
			self.footer.draw(canvas, 'footer') #bandOutline * self.ShowBandOutlines)

	def _drawBackground(self, canvas, env):
		if self.background:
			self.background.evaluateObjects(env)
			self.background.draw(canvas, 'background') #bandOutline * self.ShowBandOutlines)

	def _drawForeground(self, canvas, env):
		if self.foreground:
			self.foreground.evaluateObjects(env)
			self.foreground.draw(canvas, 'foreground') #bandOutline * self.ShowBandOutlines)

	def _placeStaticBands(self, env):
		if self.background:
			self.background.x = 0
			self.background.y = 0
			self.background.width = self.width
			self.background.height = self.height
		if self.foreground:
			self.foreground.x = 0
			self.foreground.y = 0
			self.foreground.width = self.width
			self.foreground.height = self.height
		if self.header:
			self.header.width = self.width - self.marginLeft - self.marginRight
			self.header.evaluateHeight(dictunion(env, {'header': self.header}))
			self.header.x = self.marginLeft
			self.header.y = self.height - self.marginTop - self.header.height
		if self.footer:
			self.footer.width = self.width - self.marginLeft - self.marginRight
			self.footer.evaluateHeight(dictunion(env, {'footer': self.footer}))
			self.footer.x = self.marginLeft
			self.footer.y = self.marginBottom

	def doLayout(self, report, canvas, cursor):
		""" This method iterates through the cursor and takes care of
		drawing a band for each record. For each page also, it draws
		the background, header, footer and foreground, when present.
		"""
		env = {'report':report,
				'page':self,
		}
		self._placeStaticBands(env)

		pageInitialized = False
		for recordNumber, record in enumerate(cursor):
			detailEnv = env.copy()
			detailEnv.update({'detail': self.detail,
					'record': record,
					'recordNumber': recordNumber,
			})
			self.detail.evaluateHeight(detailEnv)
			if pageInitialized and not self._detailBandFits():
				self._closePage(canvas, env)
				pageInitialized = False
			if not pageInitialized:
				pageInitialized = True
				self._beginPage(canvas, env)
			self._placeDetailBand()
			self.detail.evaluateObjects(detailEnv)
			bandOutline = "%s (record %s)" % ('detail', recordNumber)
			self.detail.draw(canvas, bandOutline) #bandOutline * self.ShowBandOutlines)
		self._drawForeground(canvas, env)

	def _beginPage(self, canvas, env):
		self.nextBandPos = self.height - self.marginTop
		if self.header is not None:
			self.nextBandPos -= self.header.height
		self._drawBackground(canvas, env)
		self._drawHeader(canvas, env)
		self._drawFooter(canvas, env)

	def _placeDetailBand(self):
		self.detail.x = self.marginLeft
		self.detail.y = self.nextBandPos - self.detail.height
		self.detail.width = self.width - self.marginLeft - self.marginRight
		self.nextBandPos -= self.detail.height

	def _detailBandFits(self):
		bottom = self.marginBottom
		if self.footer is not None:
			bottom += self.footer.height
		return self.nextBandPos-bottom >= self.detail.height

	def _closePage(self, canvas, env):
		self._drawForeground(canvas, env)
		canvas.showPage()


class Band(Serializable):
	""" This object represents a band, i.e. a collection of drawable objects
	like lines, boxes and text, that are evaluated every time the band
	is layed out on the page.
	"""
	height = LengthAttr(36)

	objects = ObjectListChild(['objects.String', 'objects.Rect', 'objects.Image'])

	def evaluateHeight(self, env):
		" Does whatever it takes to figure out the height of the band. "
		self.evaluate(env)

	def evaluateObjects(self, env):
		" Evaluate each drawable element to allow them to figure out their own properties. "
		for obj in self.objects:
			obj.evaluate(env)

	def draw(self, canvas, bandOutline=None):
		" Draw the band on the page, by drawing each element contained in it. "
		if bandOutline:
			self.printBandOutline(canvas, bandOutline)

		for obj in self.objects:
			obj.draw(canvas, self.x + obj.x, self.y + obj.y)

	def printBandOutline(self, canvas, text):
		""" Draw a dotted rectangle around the entire band, and type a small faded
		caption at the origin of the band.
		"""
		canvas.saveState()
		canvas.setLineWidth(0.1)
		canvas.setStrokeColorRGB(0.8, 0.5, 0.7)
		canvas.setDash(1, 2)
		canvas.rect(self.x, self.y, self.width, self.height)
		canvas.setFont("Helvetica", 8)
		canvas.setFillColor((0.6, 0.8, 0.7))
		canvas.drawString(self.x, self.y, text)
		canvas.restoreState()
