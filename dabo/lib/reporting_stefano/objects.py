# -*- coding: utf-8 -*-
"""
This module contains "drawable objects", i.e. objects that can be draw on the page,
like rectangles, lines and text. These objects are contained inside bands, that are
defined in report.py
"""

from reportlab.graphics import shapes
from util import *

from serialization import *


class GenericObject(Serializable):
	"""This object implements the functionalities that are common to every object.

	It cannot be used as is, but must be subclassed.  Subclasses must implement
	the _draw() method, in order to perform the actual drawing.
	"""
	name = UnevalStringAttr('???')
	x = LengthAttr(0)
	y = LengthAttr(0)
	width = LengthAttr(55)
	height = LengthAttr(18)
	rotation = LengthAttr(0)
	hAnchor = StringChoiceAttr(['left', 'center', 'right'], 'left')
	vAnchor = StringChoiceAttr(['top', 'center', 'bottom'], 'bottom')

	def draw(self, canvas, x, y):
		## We'll be tweaking with the canvas settings below, so we need to save
		## the state first so we can restore when done. Do not do any short-circuit
		## returns between c.saveState() and c.restoreState()!
		canvas.saveState()

		if self.hAnchor == "right":
			x = x - self.width
		elif self.hAnchor == "center":
			x = x - (self.width / 2)

		if self.vAnchor == "top":
			y = y - self.height
		elif self.vAnchor == "center":
			y = y - (self.height / 2)

		self._draw(canvas, x, y)

		## All done, restore the canvas state to how we found it (important because
		## rotating, scaling, etc. are cumulative, not absolute and we don't want
		## to start with a canvas in an unknown state.)
		canvas.restoreState()


class Rect(GenericObject):
	" Rectangle "
	strokeWidth = LengthAttr(1)         # the brush stroke width for shapes
	fillColor = ColorAttr(None)         # None: transparent or (r,g,b) tuple
	strokeColor = ColorAttr( (0,0,0) )  # (black)
	strokeDashArray = GenericAttr(None) # (use for dashed lines)

	def _draw(self, canvas, x, y):
		drawing = shapes.Drawing(self.width, self.height)
		drawing.rotate(self.rotation)

		rect = shapes.Rect(0, 0, self.width, self.height)
		rect.setProperties({'strokeWidth':self.strokeWidth,
				'fillColor':self.fillColor,
				'strokeColor':self.strokeColor,
				'strokeDashArray':self.strokeDashArray,
		})
		drawing.add(rect)
		drawing.drawOn(canvas, x, y)


class String(GenericObject):
	" A simple text, with no carriage returns. "
	borderWidth = LengthAttr(0)                                   # width of border around strings
	borderColor = ColorAttr( (0,0,0) )                            # color of border around strings
	align = StringChoiceAttr(['left', 'center', 'right'], 'left') # string alignment
	fontName = StringAttr('Helvetica')
	fontSize = LengthAttr(10)
	fontColor = ColorAttr( (0,0,0) )
	fillColor = ColorAttr(None)  # ???
	expr = StringAttr('')

	def _draw(self, canvas, x, y):
		## Set canvas props based on our props:
		canvas.translate(x, y)
		canvas.rotate(self.rotation)
		canvas.setLineWidth(self.borderWidth)
		canvas.setStrokeColor(self.borderColor)
		canvas.setFillColor(self.fontColor)
		canvas.setFont(self.fontName, self.fontSize)

		if self.borderWidth > 0:
			stroke = 1
		else:
			stroke = 0

		# clip the text to the specified width and height
		path = canvas.beginPath()

		## HACK! the -5, +5 thing is to keep the area below the font's baseline
		## from being clipped. I've got to learn the right way to handle this.
		path.rect(0, -5, self.width, self.height+5)
		canvas.clipPath(path, stroke=stroke)

		func, posx = {"center": (canvas.drawCentredString, (self.width / 2)),
				"right": (canvas.drawRightString, self.width),
				"left": (canvas.drawString, 0),}[self.align]

		# draw the string using the function that matches the alignment:
		func(posx, 0, self.expr)


class Image(GenericObject):
	" An image "
	borderWidth = LengthAttr(0)
	borderColor = ColorAttr( (0,0,0) )
	imageMask = StringAttr(None)                        # Transparency mask for images (type?)
	mode = StringChoiceAttr(['clip', 'scale'], 'scale') # "clip" or "scale" for images.
	expr = StringAttr('')

	def _draw(self, canvas, x, y):
		canvas.translate(x, y)
		canvas.rotate(self.rotation)
		canvas.setLineWidth(self.borderWidth)
		canvas.setStrokeColor(self.borderColor)

		if self.borderWidth > 0:
			stroke = 1
		else:
			stroke = 0

		# clip around the outside of the image:
		path = canvas.beginPath()
		path.rect(-1, -1, self.width+2, self.height+2)
		canvas.clipPath(path, stroke=stroke)

		if self.mode == "clip":
			# Need to set w,h to None for the drawImage, which will draw it in its
			# "natural" state 1:1 pixel:point, which could flow out of the object's
			# width/height, resulting in clipping.
			self.width, self.height = None, None
		canvas.drawImage(self.expr, 0, 0, self.width, self.height, self.imageMask)

#
#  Frameset is commented out because I haven't implemented it yet.
#  The reason for this is lazyness :), but also uncertainty:
#  I don't know how reportlab's framesets should be used, whether to expose
#  them directly to the report rfxml template, like it was originally, or to
#  use them within the String object type, when the text being written to the page
#  contains carriage returns. This topic should be discussed more thoroughly.
#

## pkm: Yes, let's discuss. I implemented the frameset thing rather quickly, to
##      be able to get columns working. But that was columns within a flowable,
##      for our banded report writer we want to be able to define columns per
##      page. Different things.


#class Frameset(GenericObject):
#    def __init__(self, borderWidth='0',
#                       borderColor='(0, 0, 0)',
#                       frameId='None',
#                       padLeft='0',
#                       padRight='0',
#                       padTop='0',
#                       padBottom='0',
#                       columns='1',
#                       expr='""',
#                       **args):
#        super(Frameset, self).__init__(**args)
#        self.borderWidth = self.getPt(eval(borderWidth))
#        self.borderColor = eval(borderColor, self.env)
#        self.frameId = eval(frameId, self.env)
#        self.padLeft = self.getPt(eval(padLeft, self.env))
#        self.padRight = self.getPt(eval(padRight, self.env))
#        self.padTop = self.getPt(eval(padTop, self.env))
#        self.padBottom = self.getPt(eval(padBottom, self.env))
#        self.columns = eval(columns, self.env)
#        self.expr = eval(expr, self.env)
#
#    def _draw(self, canvas, x, y):
#        # A frame is directly related to reportlab's platypus Frame.
#        columnWidth = self.width/self.columns
#
#        ## Set canvas props based on our props:
#        canvas.translate(x, y)
#        canvas.rotate(self.rotation)
#        canvas.setLineWidth(self.borderWidth)
#        canvas.setStrokeColor(self.borderColor)
#
#        if self.borderWidth > 0:
#            boundary = 1
#        else:
#            boundary = 0
#
#        story = []
#
#        styles_ = styles.getSampleStyleSheet()
#
#        story = []
#        for paragraph in self.paragraphs:
#            try:
#                s = styles_[eval(object["style"])]
#            except:
#                s = styles_[self.default_style]
#            e = eval(object["expr"])
#            s = copy.deepcopy(s)
#
#            if object.has_key("fontSize"):
#                s.fontSize = eval(object["fontSize"])
#
#            if object.has_key("fontName"):
#                s.fontName = eval(object["fontName"])
#
#            if object.has_key("leading"):
#                s.leading = eval(object["leading"])
#
#            if object.has_key("spaceAfter"):
#                s.spaceAfter = eval(object["spaceAfter"])
#
#            if object.has_key("spaceBefore"):
#                s.spaceBefore = eval(object["spaceBefore"])
#
#            if object.has_key("leftIndent"):
#                s.leftIndent = eval(object["leftIndent"])
#
#            if object.has_key("firstLineIndent"):
#                s.firstLineIndent = eval(object["firstLineIndent"])
#
#            if t == "paragraph":
#                story.append(platypus.Paragraph(e, s))
#
#        for columnIndex in range(columns):
#            f = platypus.Frame(columnIndex*columnWidth, 0, columnWidth, height, leftPadding=padLeft,
#                               rightPadding=padRight, topPadding=padTop,
#                               bottomPadding=padBottom, id=frameId,
#                               showBoundary=boundary)
#
#            f.addFromList(story, canvas)
