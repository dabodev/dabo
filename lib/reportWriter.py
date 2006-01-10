import copy
import datetime

_USE_DECIMAL = True
try:
	import decimal
	Decimal = decimal.Decimal
except ImportError:
	_USE_DECIMAL = False

import locale
import sys
import os
######################################################
# Very first thing: check for required libraries:
_failedLibs = []
for lib in ("reportlab", "PIL"):
	try:
		__import__(lib)
	except ImportError:
		_failedLibs.append(lib)

if len(_failedLibs) > 0:
	msg = """
The Dabo Report Writer has dependencies on libraries you
don't appear to have installed. You still need:

	%s
	""" % "\n\t".join(_failedLibs)

	sys.exit(msg)
del(_failedLibs)
#######################################################

import reportlab.pdfgen.canvas as canvas
import reportlab.graphics.shapes as shapes
import reportlab.lib.pagesizes as pagesizes
import reportlab.lib.units as units
import reportlab.lib.styles as styles
import reportlab.platypus as platypus
#import reportlab.lib.colors as colors
from dabo.lib.xmltodict import xmltodict
from dabo.lib.xmltodict import dicttoxml


class ReportWriter(object):
	"""Reads a report form specification, iterates over a data cursor, and
	outputs a pdf file. Allows for lots of fine-tuned control over layout, and
	dynamic evaluation of object properties. Works with the concept of bands,
	letting the designer lay out the page header, footer, groups, and detail
	separately. 

	At runtime, you feed ReportWriter a data cursor (a list of dictionaries
	where each list index is a 'row' and each dictionary key is a 'field'.)
	The detail band will print once for every row.

	Define your properties in the report form specification file, which is
	either xml or pure Python, depending on your preferences. There are (will
	be) examples of both types of specification files here. In the future 
	there will be a Dabo Report Designer that will create the xml report form
	specification files for you.

	In the context of a running report, the property values of the specification
	can refer to 'self', which is the ReportWriter instance. Thus, you can use
	the self instance to get to whatever value you want for the property.

	For example, to get the value of a field to print in your detail band, just 
	put a string object into the detail band, positioned and sized how you want,
	and set the 'expr' property to refer to the field. If the field name is
	'cArtist', the expr for the string object would be 'self.Record["cArtist"]'.

	You'll need to craft denormalized data, as ReportWriter only wants to operate
	on a single table and there is no provision for relating one table to another.
	This is, IMO, the right way to go anyway, offering the most control and 
	flexibility yet still keeping it really simple. Just have the calling program
	get the data denormalized into one cursor, and then call ReportWriter 
	feeding it the Cursor, Report Form, and OutputFile.

	More documentation will come.
	"""

	## The following defaults will be used for properties that weren't defined in
	## the spec file (no need to explicitly define properties if you want the 
	## defaults). Subclass to change defaults to your needs.
	default_designerLock = False
	default_pageSize = "letter"            # you may want 'a4' outside of the US
	default_pageOrientation = "portrait"   # the other option is "landscape"
	default_marginLeft = 36
	default_marginRight = 36
	default_marginTop = 36
	default_marginBottom = 36
	default_width = 55
	default_height = 18
	default_x = 0
	default_y = 0
	default_rotation = 0                   # (0-359)
	default_hAnchor = "left"               # hor. anchor (what x is relative to)
	default_vAnchor = "bottom"             # vert. anchor (what y is relative to)
	default_strokeWidth = 1                # the brush stroke width for shapes
	default_fillColor = None               # None: transparent or (r,g,b) tuple
	default_strokeColor = (0, 0, 0)        # (black)
	default_strokeDashArray = None         # (use for dashed lines)
	default_borderWidth = 0                # width of border around strings
	default_borderColor = (0, 0, 0)        # color of border around strings
	default_align = "left"                 # string alignment
	default_fontName = "Helvetica"
	default_fontSize = 10
	default_fontColor = (0, 0, 0)      
	default_imageMask = None               # Transparency mask for images
	default_scaleMode = "scale"            # "clip" or "scale" for images.
	default_bandHeight = 0
	default_expr = "< New >"
	default_style = "Normal"
	default_frameId = None
	default_padLeft = 0
	default_padRight = 0
	default_padTop = 0
	default_padBottom = 0
	default_columnCount = 1

	_clearMemento = True


	def getProp(self, obj, prop, defaultName=None):
		"""Return the value of the property of the report form.

		If found in the report form, it will be eval()'d. Otherwise,
		the default will be returned.
		"""
		val = None

		if obj.has_key(prop):
			try:
				val = eval(obj[prop])
			except:
				# The eval() failed, use the default.
				pass
		else:
			# The object doesn't have the prop, use the default.
			pass

		if val is None:
			if hasattr(self, "default_%s" % prop):
				if defaultName is None:
					defaultName = prop
				val = getattr(self, "default_%s" % defaultName)
		return val


	def draw(self, obj, origin, getNeededHeight=False):
		"""Draw the given object on the Canvas.

		The object is a dictionary containing properties, and	origin is the (x,y)
		tuple where the object will be drawn. 
		"""
		neededHeight = 0

		## (Can't get x,y directly from object because it may have been modified 
		## by the calling program to adjust for	band position, and draw() 
		## doesn't know about bands.)

		c = self.Canvas
		x,y = origin

		## We'll be tweaking with the canvas settings below, so we need to save
		## the state first so we can restore when done. Do not do any short-circuit
		## returns between c.saveState() and c.restoreState()!
		c.saveState()

		## These properties can apply to all objects:
		width = self.getPt(self.getProp(obj, "width"))
	
		height = self.getProp(obj, "calculatedHeight")
		if height is not None:
			height = self.getPt(height)
		else:
			height = self.getPt(self.getProp(obj, "height"))
	
		rotation = self.getProp(obj, "rotation")
		hAnchor = self.getProp(obj, "hAnchor")
		vAnchor = self.getProp(obj, "vAnchor")	

		if hAnchor == "right":
			x = x - width
		elif hAnchor == "center":
			x = x - (width / 2)
		
		if vAnchor == "top":
			y = y - height
		elif vAnchor == "middle":
			y = y - (height / 2)
	
		
		## Do specific things based on object type:
		if obj["type"] == "rect":
			d = shapes.Drawing(width, height)
			d.rotate(rotation)
	
			props = {}
			## props available in reportlab that we use:
			##   x,y,width,height
			##   fillColor: None for transparent, or (r,g,b)
			##   strokeColor: None for transparent, or (r,g,b)
			##   strokeDashArray: None
			##   strokeWidth: 0.25
	
			## props available that we don't currently use:
			##   rx, ry
			##   strokeMiterLimit: 0
			##   strokeLineJoin: 0
			##   strokeLineCap: 0
			##
	
			for prop in ("strokeWidth", "fillColor", "strokeColor", 
					"strokeDashArray", ):
				props[prop] = self.getProp(obj, prop)
			props["strokeWidth"] = self.getPt(props["strokeWidth"])

			r = shapes.Rect(0, 0, width, height)
			r.setProperties(props)
			d.add(r)
			d.drawOn(c, x, y)
	
		if obj["type"] == "line":
			d = shapes.Drawing(width, height)
			d.rotate(rotation)
	
			props = {}
			## props available in reportlab that we use:
			##   x,y,width,height
			##   fillColor: None for transparent, or (r,g,b)
			##   strokeColor: None for transparent, or (r,g,b)
			##   strokeDashArray: None
			##   strokeWidth: 0.25
	
			## props available that we don't currently use:
			##   rx, ry
			##   strokeMiterLimit: 0
			##   strokeLineJoin: 0
			##   strokeLineCap: 0
			##
	
			for prop in ("strokeWidth", "strokeColor", "strokeDashArray", ):
				props[prop] = self.getProp(obj, prop)
			props["strokeWidth"] = self.getPt(props["strokeWidth"])

			r = shapes.Line(0, 0, width, height)
			r.setProperties(props)
			d.add(r)
			d.drawOn(c, x, y)
	
		elif obj["type"] == "string":
			## Set the props for strings:
			borderWidth = self.getPt(self.getProp(obj, "borderWidth"))
			borderColor = self.getProp(obj, "borderColor")
			align = self.getProp(obj, "align")
			fontName = self.getProp(obj, "fontName")
			fontSize = self.getProp(obj, "fontSize")
			fontColor = self.getProp(obj, "fontColor")

			## Set canvas props based on our props:
			c.translate(x, y)
			c.rotate(rotation)
			c.setLineWidth(borderWidth)
			c.setStrokeColor(borderColor)
			c.setFillColor(fontColor)
			c.setFont(fontName, fontSize)
	
			if borderWidth > 0:
				stroke = 1
			else:
				stroke = 0
	
			# clip the text to the specified width and height
			p = c.beginPath()
	
			## HACK! the -5, +5 thing is to keep the area below the font's baseline
			## from being clipped. I've got to learn the right way to handle this.
			p.rect(0, -5, width, height+5)
			c.clipPath(p, stroke=stroke)
	
			funcs = {"center": c.drawCentredString,
					"right": c.drawRightString,
					"left": c.drawString}
			func = funcs[align]

			if align == "center":
				posx = (width / 2)
			elif align == "right":
				posx = width
			else:
				posx = 0
	
			# draw the string using the function that matches the alignment:
			try:
				s = eval(obj["expr"])
			except Exception, e:
				# Something failed in the eval, print the exception string instead:
				s = e
			if isinstance(s, basestring):
				s = s.encode(self.Encoding)
			else:
				s = unicode(s)
			func(posx, 0, s)
	
		elif obj["type"] == "frameset":
			# A frame is directly related to reportlab's platypus Frame.
			borderWidth = self.getPt(self.getProp(obj, "borderWidth"))
			borderColor = self.getProp(obj, "borderColor")
			frameId = self.getProp(obj, "frameId")
			padLeft = self.getPt(self.getProp(obj, "padLeft"))
			padRight = self.getPt(self.getProp(obj, "padRight"))
			padTop = self.getPt(self.getProp(obj, "padTop"))
			padBottom = self.getPt(self.getProp(obj, "padBottom"))
			columnCount = self.getProp(obj, "columnCount")
	
			columnWidth = width/columnCount

			## Set canvas props based on our props:
			c.translate(x, y)
			c.rotate(rotation)
			c.setLineWidth(borderWidth)
			c.setStrokeColor(borderColor)
	
			if borderWidth > 0:
				boundary = 1
			else:
				boundary = 0

			story = []	
			
			styles_ = styles.getSampleStyleSheet()

			objects = obj["objects"]
			story = []
			for fobject in objects:
				objNeededHeight = 0

				t = fobject["type"]
				try:
					s = styles_[eval(fobject["style"])]
				except:
					s = styles_[self.default_style]
				e = eval(fobject["expr"]).encode(self.Encoding)
				s = copy.deepcopy(s)

				if fobject.has_key("fontSize"):
					s.fontSize = eval(fobject["fontSize"])

				if fobject.has_key("fontName"):
					s.fontName = eval(fobject["fontName"])
				
				if fobject.has_key("leading"):
					s.leading = eval(fobject["leading"])

				if fobject.has_key("spaceAfter"):
					s.spaceAfter = eval(fobject["spaceAfter"])

				if fobject.has_key("spaceBefore"):
					s.spaceBefore = eval(fobject["spaceBefore"])

				if fobject.has_key("leftIndent"):
					s.leftIndent = eval(fobject["leftIndent"])

				if fobject.has_key("firstLineIndent"):
					s.firstLineIndent = eval(fobject["firstLineIndent"])

				if t == "paragraph":
					paras = e.split("\n")
					for para in paras:
						if len(para) == 0: 
							# Blank line
							p = platypus.Spacer(0, s.leading)
						else:
							def escapePara(para):
								words = para.split(" ")
								for idx, word in enumerate(words):
									if "&" in word and ";" not in word:
										word = word.replace("&", "&amp;")
									if "<" in word and ">" not in word:
										word = word.replace("<", "&lt;")
									words[idx] = word
								return " ".join(words)
							para = escapePara(para)
							p = platypus.Paragraph(para, s)
						story.append(p)
						objNeededHeight += p.wrap(columnWidth-padLeft-padRight, None)[1]

				neededHeight = max(neededHeight, objNeededHeight) + padTop + padBottom

			for columnIndex in range(columnCount):
				f = platypus.Frame(columnIndex*columnWidth, 0, columnWidth, height, leftPadding=padLeft,
						rightPadding=padRight, topPadding=padTop,
						bottomPadding=padBottom, id=frameId, 
						showBoundary=boundary)
				if getNeededHeight:
					obj["calculatedHeight"] = "%s" % neededHeight
				else:
					f.addFromList(story, c)
	
		elif obj["type"] == "image":
			borderWidth = self.getPt(self.getProp(obj, "borderWidth"))
			borderColor = self.getProp(obj, "borderColor")
			mask = self.getProp(obj, "imageMask")
			mode = self.getProp(obj, "scaleMode")

			c.translate(x, y)
			c.rotate(rotation)
			c.setLineWidth(borderWidth)
			c.setStrokeColor(borderColor)
	
			if borderWidth > 0:
				stroke = 1
			else:
				stroke = 0
	
			# clip around the outside of the image:
			p = c.beginPath()
			p.rect(-1, -1, width+2, height+2)
			c.clipPath(p, stroke=stroke)
	
			if mode == "clip":
				# Need to set w,h to None for the drawImage, which will draw it in its
				# "natural" state 1:1 pixel:point, which could flow out of the object's
				# width/height, resulting in clipping.
				width, height = None, None

			imageFile = eval(obj["expr"])
			if not os.path.exists(imageFile):
				imageFile = os.path.join(self.HomeDirectory, imageFile)
			imageFile = str(imageFile)

			c.drawImage(imageFile, 0, 0, width, height, mask)

		## All done, restore the canvas state to how we found it (important because
		## rotating, scaling, etc. are cumulative, not absolute and we don't want
		## to start with a canvas in an unknown state.)
		c.restoreState()
		return neededHeight


	def getPt(self, val):
		"""Given a string or a number, convert the value into a numeric pt value.
	
		Strings can have the unit appended, like "3.5 in", "2 cm", "3 pica", "10 mm".
	
		> print self.getPt("1 in")
		72
		> print self.getPt("1")
		1
		> print self.getPt(1)
		1
		"""
		if isinstance(val, (int, long, float)):
			# return as-is as the pt value.
			return val
		else:
			# try to run it through reportlab's units.toLength() function:
			return units.toLength(val)
	
	
	def printBandOutline(self, band, x, y, width, height):
			## draw a dotted rectangle around the entire band, and type a small faded 
			## caption at the origin of the band.
			c = self.Canvas
			c.saveState()
			c.setLineWidth(0.1)
			c.setStrokeColorRGB(0.8, 0.5, 0.7)
			c.setDash(1, 2)
			c.rect(x, y, width, height)
			c.setFont("Helvetica", 8)
			c.setFillColor((0.6, 0.8, 0.7))
			c.drawString(x, y, band)
			c.restoreState()
		
		
	def write(self, save=True):
		"""Write the PDF file based on the ReportForm spec.
		
		If the save argument is True (the default), the PDF file will be
		saved and closed after the report form has been written. If False, 
		the PDF file will be left open so that additional pages can be added 
		with another call, perhaps after creating a different report form.
		"""
		_form = self.ReportForm
		if _form is None:
			raise ValueError, "ReportForm must be set first."

		_outputFile = self.OutputFile

		pageSize = self.getPageSize()		
		pageWidth, pageHeight = pageSize

		c = self.Canvas
		if not c:
			# Create the reportlab canvas:
			c = self._canvas = canvas.Canvas(_outputFile, pagesize=pageSize)
		
		# Get the number of columns:
		columnCount = self.getProp(_form, "columnCount")
		

		# Initialize the groups list:
		groups = _form.get("groups", ())
		self._groupValues = {}
		for group in groups:
			vv = {}
			vv["curVal"] = None
			self._groupValues[group["expr"]] = vv

		groupsDesc = [i for i in groups]
		groupsDesc.reverse()

		# Initialize the variables list:
		variables = _form.get("variables", ())
		self._variableValues = {}
		self.Variables = {}
		for variable in variables:
			vv = {}
			vv["value"] = None
			vv["curReset"] = None
			self.Variables[variable["name"]] = eval(variable["initialValue"])
			self._variableValues[variable["name"]] = vv

		self._recordNumber = 0
		self._currentColumn = 0

		## Let the page header have access to the first record:
		if len(self.Cursor) > 0:
			self.Record = self.Cursor[0]

		def processVariables():
			"""Apply the user's expressions to the current value of all the report vars.

			This is called once per record iteration, before the detail for the current
			band is printed..
			"""
			variables = self.ReportForm.get("variables", ())
			for variable in variables:
				vv = self._variableValues[variable["name"]]
				if variable.has_key("resetAt"):
					resetAt = eval(variable["resetAt"])
				else:
					resetAt = None
				curReset = vv.get("curReset")
				if resetAt != curReset:
					# resetAt tripped: value to initial value
					self.Variables[variable["name"]] = eval(variable["initialValue"])
				vv["curReset"] = resetAt

				# run the variable expression to get the current value:
				vv["value"] = eval(variable["expr"])

				# update the value of the public variable:
				self.Variables[variable["name"]] = vv["value"]			
					

		def printBand(band, y=None, group=None):
			"""Generic function for printing any band."""

			_form = self.ReportForm

			# Get the page margins into variables:
			ml = self.getPt(self.getProp(_form["page"], "marginLeft"))
			mt = self.getPt(self.getProp(_form["page"], "marginTop"))
			mr = self.getPt(self.getProp(_form["page"], "marginRight"))
			mb = self.getPt(self.getProp(_form["page"], "marginBottom"))
		
			# Page header/footer origins are needed in various places:
			pageHeaderOrigin = (ml, pageHeight - mt 
					- self.getPt(self.getProp(_form["pageHeader"], "height")))
			pageFooterOrigin = (ml, mb)
		
			workingPageWidth = pageWidth - ml - mr
			columnWidth = workingPageWidth / columnCount
#			print workingPageWidth / 72, columnWidth / 72
#			print columnWidth, columnCount

			if y is None:
				y = pageHeaderOrigin[1]

			try:
				if group is not None:
					bandDict = group[band]
				else:
					bandDict = _form[band]
			except KeyError:
				# Band name doesn't exist.
				return y

			self.Bands[band] = {}

			# do the height calcs manually (not via getProp):
			try:		
				height = eval(bandDict["height"])
			except KeyError:
				height = self.default_bandHeight

			if height is not None:
				height = self.getPt(height)
			else:
				# figure out height based on the objects in the band.
				height = self.calculateBandHeight(bandDict)

			y = y - height
			width = pageWidth - ml - mr

			# Non-detail band special cases:
			if band == "pageHeader":
				x,y = pageHeaderOrigin
			elif band == "pageFooter":
				x,y = pageFooterOrigin
			elif band in ("pageBackground", "pageForeground"):
				x,y = 0,1
				width, height = pageWidth-1, pageHeight-1


			pf = _form.get("pageFooter")
			if pf is None:
				pfHeight = 0
			else:
				pfHeight = self.getPt(self.getProp(pf, "height"))

			if band in ("detail", "groupHeader", "groupFooter"):
				extraHeight = 0
				if band == "groupHeader":
					# Also account for the height of the first detail record: don't print the
					# group header on this page if we don't get at least one detail record
					# printed as well. Actually, this should be reworked so that any subsequent
					# group header records get accounted for as well...
					b = _form["detail"]
					extraHeight = b.get("height")
					if extraHeight is None:
						extraHeight = self.default_bandHeight
					else:
						extraHeight = eval(extraHeight)
					if extraHeight is None:
						extraHeight = self.calculateBandHeight(b)
					else:
						extraHeight = self.getPt(extraHeight)
				if y < pageFooterOrigin[1] + pfHeight + extraHeight:
					if self._currentColumn >= columnCount-1:
						endPage()
						beginPage()
						self._currentColumn = 0
					else:
						self._currentColumn += 1
					y = pageHeaderOrigin[1]
					if band == "detail":
						y = reprintGroupHeaders(y)
					y = y - height
				
			x = ml + (self._currentColumn * columnWidth)
				
			self.Bands[band]["x"] = x
			self.Bands[band]["y"] = y
			self.Bands[band]["width"] = width
			self.Bands[band]["height"] = height
		
			if self.ShowBandOutlines:
				self.printBandOutline("%s (record %s)" % (band, self.RecordNumber), 
						x, y, width, height)

			if bandDict.has_key("objects"):
				for obj in bandDict["objects"]:
					showExpr = obj.get("showExpr")
					if showExpr is not None:
						try:
							ev = eval(showExpr)
						except:
							## expression failed to eval: default to True (show it)
							ev = True
						if not ev:
							# user's showExpr evaluated to False: don't print!
							continue

					x1 = self.getPt(self.getProp(obj, "x"))
					y1 = self.getPt(self.getProp(obj, "y"))
					x1 = x + x1
					y1 = y + y1
					self.draw(obj, (x1, y1))
						
			return y		


		def beginPage():
			# Print the static bands that appear below detail in z-order:
			for band in ("pageBackground", "pageHeader", "pageFooter"):
				printBand(band)
			self._brandNewPage = True

		def endPage():
			printBand("pageForeground")
			self.Canvas.showPage()
		
		def reprintGroupHeaders(y):
			for group in groups:
				reprint = group.get("reprintHeaderOnNewPage")
				if reprint is not None:
					reprint = eval(reprint)
					if reprint is not None:
						y = printBand("groupHeader", y, group)
		
			return y

		beginPage()

		# Print the dynamic bands (Detail, GroupHeader, GroupFooter):
		y = None
		for idx, record in enumerate(self.Cursor):
			_lastRecord = self.Record
			self.Record = record

			# print group footers for previous group if necessary:
			if idx > 0:
				# First pass, iterate through the groups outer->inner, and if any group
				# expr has changed, reset the curval for the group and all child groups.
				resetCurVals = False
				for idx, group in enumerate(groups):
					vv = self._groupValues[group["expr"]]
					if resetCurVals or vv["curVal"] != eval(group["expr"]):
						resetCurVals = True
						vv["curVal"] = None

				# Second pass, iterate through the groups inner->outer, and print the 
				# group footers for groups that have changed.
				for idx, group in enumerate(groupsDesc):
					vv = self._groupValues[group["expr"]]
					if vv["curVal"] != eval(group["expr"]):
						# We need to temporarily move back to the last record so that the
						# group footer reflects what the user expects.
						self.Record = _lastRecord
						y = printBand("groupFooter", y, group)
						self.Record = record
						
			# Any report variables need their values evaluated again:
			processVariables()

			# print group headers for this group if necessary:
			for idx, group in enumerate(groups):
				vv = self._groupValues[group["expr"]]
				if vv["curVal"] != eval(group["expr"]):
					vv["curVal"] = eval(group["expr"])
					np = eval(group.get("startOnNewPage", "False")) \
							and self.RecordNumber > 0
					if np:
						endPage()
						beginPage()
						y = None
					y = printBand("groupHeader", y, group)


			# print the detail band:
			y = printBand("detail", y)

			self._recordNumber += 1


		# print the group footers for the last group:
		for idx, group in enumerate(groupsDesc):
			y = printBand("groupFooter", y, group)

		endPage()
		
		if save:
			if self.OutputFile is not None:
				c.save()
			self._canvas = None


	def calculateBandHeight(self, bandDict):
		maxHeight = 0
		if bandDict.has_key("objects"):
			for obj in bandDict["objects"]:
				y = self.getPt(self.getProp(obj, "y"))

				try:
					ht = eval(obj["height"])
				except KeyError:
					ht = self.default_height
				if ht is None:
					ht = self.calculateObjectHeight(obj)
				ht = self.getPt(ht)

				thisHeight = y + ht
				maxHeight = max(thisHeight, maxHeight)
		return maxHeight

		
	def calculateObjectHeight(self, obj):
		neededHeight = self.draw(obj, (0,0), getNeededHeight=True)
		return neededHeight


	def getPageSize(self):
		## Set the Page Size:
		# get the string pageSize value from the spec file:
		_form = self.ReportForm
		pageSize = self.getProp(_form["page"], "size", "pageSize")

		# reportlab expects the pageSize to be upper case:
		pageSize = pageSize.upper()
		# convert to the reportlab pageSize value (tuple(width,height)):
		pageSize = eval("pagesizes.%s" % pageSize)
		# run it through the portrait/landscape filter:
		orientation = self.getProp(_form["page"], "orientation", "pageOrientation")
		func = eval("pagesizes.%s" % orientation)
		return func(pageSize)


	def _getUniqueName(self):
		"""Returns a name that should be unique, but it doesn't check to make sure."""
		import time, md5, random
		t1 = time.time()
		t2 = t1 + random.random()
		base = md5.new(str(t1 +t2))
		name = "_" + base.hexdigest()
		return name
	

	def _getEmptyForm(self):
		"""Returns a report form with the minimal number of elements.

		Defaults will be filled in. Used by the report designer.
		"""
		title = ""

		page = {}
		page["size"] = '"%s"' % self.default_pageSize
		page["orientation"] = '"%s"' % self.default_pageOrientation
		page["marginLeft"] = '"%s"' % self.default_marginLeft
		page["marginRight"] = '"%s"' % self.default_marginRight
		page["marginTop"] = '"%s"' % self.default_marginTop
		page["marginBottom"] = '"%s"' % self.default_marginBottom

		pageHeader = {"height": '"%s"' % self.default_bandHeight}
		
		detail = {"height": '"%s"' % self.default_bandHeight}
		pageFooter = {"height": '"%s"' % self.default_bandHeight}
		pageBackground = {}
		pageForeground = {}

		return {"title": title, "page": page, "pageHeader": pageHeader,
				"detail": detail, "pageFooter": pageFooter, 
				"pageBackground": pageBackground, "pageForeground": pageForeground}


	def _isModified(self):
		"""Returns True if the report form definition has been modified.

		Used by the report designer.
		"""
		return not (self.ReportForm is None 
				or self.ReportForm == self._reportFormMemento)


	def _getXMLDictFromForm(self, form, d=None):
		"""Recursively generate the dict format required for the dicttoxml() function."""
		if d is None:
			d = {"name": "report", "children": []}

		positions = {"title": 0, "columnCount": 5, "page": 10, 
				"pageBackground": 20, 
				"pageForeground": 30, "groups": 40, "variables": 50,
				"pageHeader": 60, "groupHeader": 65, "detail": 70, 
				"groupFooter": 75, "pageFooter": 80,
				"objects": 99999, "testcursor": 999999}

		def elementSort(x,y):
			posX = positions.get(x, -1)
			posY = positions.get(y, -1)
			if posY > posX:
				return -1
			elif posY < posX:
				return 1
			return cmp(x,y)

		elements = form.keys()
		elements.sort(elementSort)

		for element in elements:
			if element == "type":
				continue
			child = {"name": element, "children": []}
			if isinstance(form[element], basestring):
				child["cdata"] = form[element]
			elif element == "testcursor":
				row = form["testcursor"][0]
				atts = {}
				fields = row.keys()
				fields.sort()
				for field in fields:
					if isinstance(row[field], basestring):
						t = "str"
					elif isinstance(row[field], float):
						t = "float"
					elif isinstance(row[field], (int, long)):
						t = "int"
					elif isinstance(row[field], bool):
						t = "bool"
					elif isinstance(row[field], datetime.date):
						t = "datetime.date"
					elif isinstance(row[field], datetime.datetime):
						t = "datetime.datetime"
					elif _USE_DECIMAL and isinstance(row[field], Decimal):
						t = "Decimal"
					atts[field] = t
				child["attributes"] = atts
					
				cursor = []
				for row in form["testcursor"]:
					fields = row.keys()
					fields.sort()
					attr = {}
					for field in fields:
						attr[field] = repr(row[field])
					cursor.append({"name": "record", "attributes": attr})
					child["children"] = cursor

			elif element in ("objects", "variables", "groups"):
				objects = []
				for index in range(len(form[element])):
					formobj = form[element][index]
					obj = {"name": formobj["type"], "children": []}
					props = formobj.keys()
					props.sort(elementSort)
					if formobj.has_key(element):
						# Recurse
						self._getXMLDictFromForm(formobj, obj)
					else:
						for prop in props:
							if prop != "type":
								if isinstance(formobj[prop], dict):
									# Recurse
									self._getXMLDictFromForm(formobj, obj)
									break
								else:
									if element != "groups":
										newchild = {"name": prop, "cdata": formobj[prop]}
										obj["children"].append(newchild)
					objects.append(obj)
				child["children"] = objects

			elif isinstance(form[element], dict):
				child = self._getXMLDictFromForm(form[element], child)

			d["children"].append(child)
		return d		


	def _getXMLFromForm(self, form):
		"""Returns a valid rfxml string from a report form dict."""
		# We need to first convert the report form dict into the dict format
		# as expected by the generic dicttoxml() function. This is a tree of
		# dicts with keys on 'cdata', 'children', 'name', and 'attributes'.
		d = self._getXMLDictFromForm(form)
		# Now that the dict is in the correct format, get the xml:
		return dicttoxml(d, header=self._getXmlHeader(), 
				linesep={1: os.linesep*1})


	def _getXmlHeader(self):
		"""Returns the XML header for the rfxml document."""
		return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>

<!-- 
		This is a Dabo report form xml (rfxml) document, describing a
		report form. It was generated by the Dabo Report Writer, and can
		be edited by hand or by using the Dabo Report Designer.
-->

"""


	def _setMemento(self):
		"""Set the memento of the report form, which is the pristine version."""
		if self._clearMemento:
			import copy
			r = self._reportForm
			if r is None:
				m = None
			else:
				m = copy.deepcopy(r)
			self._reportFormMemento = m

	
	def _getFormFromXMLDict(self, xmldict, formdict=None, level=0):
		"""Recursively generate the form dict from the given xmldict."""

		if formdict is None:
			formdict = {}

		if xmldict.has_key("children"):
			# children with name of "objects", "variables" or "groups" are band 
			# object lists, while other children are sub-dictionaries.
			for child in xmldict["children"]:
				if child["name"] == "testcursor":
					# special case.
					records = []
					datatypes = child["attributes"]
					for childrecord in child["children"]:
						record = {}
						if childrecord["name"] == "record":
							for field, value in childrecord["attributes"].items():
								datatype = eval(datatypes[field])
#								record[field] = datatype(value)
								record[field] = eval(value)
							records.append(record)
					formdict[child["name"]] = records
				elif child.has_key("cdata"):
					formdict[child["name"]] = child["cdata"]
				elif child.has_key("attributes"):
					formdict[child["name"]] = child["attributes"]
				elif child.has_key("children"):
					if child["name"] in ("objects", "groups", "variables"):
						coll = child["name"]
						formdict[coll] = []
						for obchild in child["children"]:
							c = self._getFormFromXMLDict(obchild, {}, level+1)
							c["type"] = obchild["name"]
							formdict[coll].append(c)
					else:
						formdict[child["name"]] = self._getFormFromXMLDict(child, {}, level+1)

		return formdict


	def _getFormFromXML(self, xml):
		"""Returns the report form dict given xml in rfxml format."""

		# Get the xml into a generic tree of dicts:
		xmldict = xmltodict(xml)

		if xmldict["name"] == "report":
			form = self._getFormFromXMLDict(xmldict)
		else:
			print "This isn't a valid rfxml string."

		return form


	def _getBands(self):
		try:
			v = self._bands
		except AttributeError:
			v = self._bands = {}
		return v

	Bands = property(_getBands, None, None,
		"""Provides runtime access to bands of the currently running report.""")


	def _getCanvas(self):
		try:
			v = self._canvas
		except AttributeError:
			v = self._canvas = None
		return v

	Canvas = property(_getCanvas, None, None,
		"""Returns a reference to the reportlab canvas object.""")	


	def _getCursor(self):
		if self.UseTestCursor:
			try:
				v = self.ReportForm["testcursor"]
			except KeyError:
				v = []
		else:
			try:
				v = self._cursor
			except AttributeError:
				v = self._cursor = []
		return v

	def _setCursor(self, val):
		self._cursor = val
		self.UseTestCursor = False
		
	Cursor = property(_getCursor, _setCursor, None, 
		"""Specifies the data cursor that the report runs against.""")


	def _getEncoding(self):
		try:
			v = self._encoding
		except AttributeError:
			v = self._encoding = "utf-8"
			#v = self._encoding = sys.getdefaultencoding()
		return v

	def _setEncoding(self, val):
		self._encoding = val

	Encoding = property(_getEncoding, _setEncoding, None,
		"""Specifies the encoding for unicode strings.""")


	def _getHomeDirectory(self):
		try:
			v = self._homeDirectory
		except AttributeError:
			v = self._homeDirectory = self.Application.HomeDirectory
		return v

	def _setHomeDirectory(self, val):
		self._homeDirectory = val

	HomeDirectory = property(_getHomeDirectory, _setHomeDirectory, None,
		"""Specifies the home directory for the report.

		Resources on disk (image files, etc.) will be looked for relative to the
		HomeDirectory if specified with relative pathing. The HomeDirectory should
		be the directory that contains the report form file. If you set 
		self.ReportFormFile, HomeDirectory will be set for you automatically. 
		Otherwise, HomeDirectory will be set to self.Application.HomeDirectory.
		""")


	def _getOutputFile(self):
		try:
			v = self._outputFile
		except AttributeError:
			v = self._outputFile = None
		return v
		
	def _setOutputFile(self, val):
		if isinstance(val, file):
			self._outputFile = val
		else:
			s = os.path.split(val)
			if len(s[0]) == 0 or os.path.exists(s[0]):
				self._outputFile = val
			else:
				raise ValueError, "Path '%s' doesn't exist." % s[0]

	OutputFile = property(_getOutputFile, _setOutputFile, None,
		"""Specifies the output PDF file (name or file object).""")


	def _getRecord(self):
		try:
			v = self._record
		except AttributeError:
			v = self._record = {}
		return v

	def _setRecord(self, val):
		self._record = val

	Record = property(_getRecord, _setRecord, None,
		"""Specifies the dictionary that represents the current record.

		The report writer will automatically fill this in during the running 
		of the report. Allows expressions in the report form like:

			self.Record['cFirst']
		""")


	def _getRecordNumber(self):
		try:
			v = self._recordNumber
		except AttributeError:
			v = self._recordNumber = None
		return v

	RecordNumber = property(_getRecordNumber, None, None,
		"""Returns the current record number of Cursor.""")


	def _getReportForm(self):
		try:
			v = self._reportForm
		except AttributeError:
			v = self._reportForm = None
		return v
		
	def _setReportForm(self, val):
		self._reportForm = val
		self._setMemento()
		self._reportFormXML = None
		self._reportFormFile = None
		
	ReportForm = property(_getReportForm, _setReportForm, None,
		"""Specifies the python report form data dictionary.""")
	

	def _getReportFormFile(self):
		try:
			v = self._reportFormFile
		except AttributeError:
			v = self._reportFormFile = None
		return v
		
	def _setReportFormFile(self, val):
		if val is None:
			self._reportFormFile = None
			self._reportFormXML = None
			self._reportForm = None
			self._setMemento()
			return

		if os.path.exists(val):
			ext = os.path.splitext(val)[1] 
			if ext == ".py":
				# The file is a python module, import it and get the report dict:
				s = os.path.split(val)
				sys.path.append(s[0])
				exec("import %s as form" % s[1].split(".")[0])
				sys.path.pop()
				self._reportForm = form.report
				self._setMemento()
				self._reportFormXML = None
					
			elif ext == ".rfxml":
				# The file is a report form xml file. Open it and set ReportFormXML:
				self._reportFormXML = open(val, "r").read()
				self._reportForm = self._getFormFromXML(self._reportFormXML)
				self._setMemento()
			else:
				raise ValueError, "Invalid file type."
			self._reportFormFile = val
			self.HomeDirectory = os.path.join(os.path.split(val)[:-1])[0]
		else:
			raise ValueError, "Specified file does not exist."
		
	ReportFormFile = property(_getReportFormFile, _setReportFormFile, None,
		"""Specifies the path and filename of the report form spec file.""")
		

	def _getReportFormXML(self):
		try:
			v = self._reportFormXML
		except AttributeError:
			v = self._reportFormXML = None
		return v
		
	def _setReportFormXML(self, val):
		self._reportFormXML = val
		self._reportFormFile = None
		self._reportForm = self._getFormFromXML(self._reportFormXML)
		self._setMemento()
		
	ReportFormXML = property(_getReportFormXML, _setReportFormXML, None,
		"""Specifies the report format xml.""")


	def _getShowBandOutlines(self):
		try:
			v = self._showBandOutlines
		except AttributeError:
			v = False
		return v

	def _setShowBandOutlines(self, val):
		self._showBandOutlines = bool(val)


	ShowBandOutlines = property(_getShowBandOutlines, _setShowBandOutlines, None,
		"""Specifies whether the report bands are printed with outlines for
		debugging and informational purposes. In addition to the band, there is also
		a caption with the band name at the x,y origin point for the band.""")
		

	def _getUseTestCursor(self):
		try:
			v = self._useTestCursor
		except AttributeError:
			v = self._useTestCursor = False
		return v

	def _setUseTestCursor(self, val):
		self._useTestCursor = bool(val)
		if val:
			self._cursor = None

	UseTestCursor = property(_getUseTestCursor, _setUseTestCursor, None, 
		"""Specifies whether the TestCursor in the spec file is used.""")
			
			
if __name__ == "__main__":
	rw = ReportWriter()
	rw.ShowBandOutlines = True
	rw.UseTestCursor = True

	if len(sys.argv) > 1:
		for reportForm in sys.argv[1:]:
			if reportForm == "tempfile":
				import tempfile
				print "Creating tempfile.pdf from samplespec.rfxml"
				rw.ReportFormFile = "samplespec.rfxml"
				rw.OutputFile = tempfile.TemporaryFile()
				rw.write()
				f = open("tempfile.pdf", "wb")
				rw.OutputFile.seek(0)
				f.write(rw.OutputFile.read())
				f.close()
			else:
				output = "./%s.pdf" % os.path.splitext(reportForm)[0]
				print "Creating %s from report form %s..." % (output, reportForm)
				rw.ReportFormFile = reportForm
				rw.OutputFile = output
				rw.write()
	else:
		print "Usage: reportWriter <specFile> [<specFile>...]"
