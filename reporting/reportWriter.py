##  reportWriter.py
##  begun 2/14/2005 by pkm
##  This is just a first pass, with ugly procedural code. When you run it by
##  "python reportWriter.py", it'll read the samplespec.py file and create a
##  test.pdf file.

##  Almost all values from the spec file are evaluated at runtime, allowing
##  simple yet flexible redirection (a given prop can be gotten at runtime
##  from a user-defined function).

import sys
import reportlab.pdfgen.canvas as canvas
import reportlab.graphics.shapes as shapesimport reportlab.lib.pagesizes as pagesizes
import reportlab.lib.units as units
#import reportlab.lib.colors as colors

#form = sys.argv[1]
import samplespec as form


#data = sys.argv[2]
data = [{"cArtist": "The Clash", "iid": 1},
        {"cArtist": "Queen", "iid": 2},
        {"cArtist": "Ben Harper and the Innocent Criminals", "iid":3}]

# Draw a dotted rectangle around each band:
showBands = True


pageSize = eval(form.Page["size"])
if pageSize == "letter":
	pageSize = pagesizes.letter
elif pageSize == "a4":
	pageSize = pagesizes.a4


c = canvas.Canvas("test.pdf", pagesize=pageSize)
pageWidth, pageHeight = pageSize

print "pageWidth, pageHeight:", pageWidth, pageHeight


ml = units.toLength(eval(form.Page["margin"]["left"]))
mt = units.toLength(eval(form.Page["margin"]["top"]))
mr = units.toLength(eval(form.Page["margin"]["right"]))
mb = units.toLength(eval(form.Page["margin"]["bottom"]))

pageHeaderOrigin = (ml, pageHeight - mt 
                    - units.toLength(eval(form.PageHeader["height"])))
pageFooterOrigin = (ml, mb)

def printBandOutline(band, x, y, width, height):
		## draw a dotted rectangle around the entire band, and type a small faded 
		## caption at the origin of the band.
		c.saveState()
		c.setLineWidth(0.1)
		c.setStrokeColorRGB(0.2,0.5,0.3)
		c.setDash(1,2)
		c.rect(x,y,width,height)
		c.setFont("Helvetica", 8)
		c.drawString(x, y, band)
		c.restoreState()

def draw(object, x, y):
	c.saveState()

	try: 
		width = units.toLength(eval(object["width"]))
	except (KeyError, TypeError, ValueError): 
		width = 25

	try: 
		height = units.toLength(eval(object["height"]))
	except (KeyError, TypeError, ValueError): 
		height = 25

	try: 
		rotation = eval(object["rotation"])
	except KeyError:
		rotation = 0

	if object["type"] == "rect":
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

		try:
			props["strokeWidth"] = units.toLength(eval(object["strokeWidth"]))
		except KeyError: 
			props["strokeWidth"] = 1

		try:
			props["fillColor"] = eval(object["fillColor"])
		except KeyError:
			props["fillColor"] = None

		try:
			props["strokeColor"] = eval(object["strokeColor"])
		except KeyError:
			props["strokeColor"] = (0, 0, 0)

		try:
			props["strokeDashArray"] = eval(object["strokeDashArray"])
		except KeyError:
			props["strokeDashArray"] = None

		r = shapes.Rect(0, 0, width, height)
		r.setProperties(props)
		d.add(r)
		d.drawOn(c, x, y)

	elif object["type"] == "string":
		c.translate(x, y)
		c.rotate(rotation)
		try: 
			borderWidth = units.toLength(eval(object["borderWidth"]))
		except KeyError: 
			borderWidth = 0

		try: 
			borderColor = eval(object["borderColor"])
		except KeyError: 
			borderColor = (0, 0, 0)

		c.setLineWidth(borderWidth)
		c.setStrokeColor(borderColor)

		if borderWidth > 0:
			stroke = 1
		else:
			stroke = 0

		if width is not None and height is not None:
			# clip the text to the specified width and height
			p = c.beginPath()
			if eval(object["align"]) == "center":
				posx = (width / 2)
			elif eval(object["align"]) == "right":
				posx = width
			else:
				posx = 0

			p.rect(posx, 0, width, height)
			c.clipPath(p, stroke=stroke)

		funcs = {"center": c.drawCentredString,
		         "right": c.drawRightString,
		         "left": c.drawString}
		func = funcs[eval(object["align"])]

		try:
			fontName = eval(object["fontName"])
		except KeyError:
			fontName = "Helvetica"

		try:
			fontSize = eval(object["fontSize"])
		except KeyError:
			fontSize = 10

		try:
			fillColor = eval(object["fillColor"])
		except KeyError:
			fillColor = (0, 0, 0)

		c.setFillColor(fillColor)
		c.setFont(fontName, fontSize)

		func(0,0,eval(object["expr"]))

	elif object["type"] == "image":
		try: mask = eval(object["mask"])
		except: mask = None
		c.drawImage(eval(object["expr"]), x, y, width, height, mask)
	c.restoreState()


# Print the static bands (Page Header/Footer, Watermark):
for band in ("PageBackground", "PageHeader", "PageFooter"):
	bandDict = eval("form.%s" % band)

	if showBands:
		x = ml
		if band == "PageHeader":
			y = pageHeaderOrigin[1]
		elif band == "PageFooter":
			y = pageFooterOrigin[1]
		elif band == "PageBackground":
			x,y = 0,1
	
		if band == "PageBackground":
			width, height = pageWidth-1, pageHeight-1
		else:
			width = pageWidth - ml - mr
			height = units.toLength(eval(bandDict["height"]))

		printBandOutline(band, x, y, width, height)

	for object in bandDict["objects"]:

		if bandDict == form.PageHeader:
			origin = pageHeaderOrigin
		elif bandDict == form.PageFooter:
			origin = pageFooterOrigin
		elif bandDict == form.PageBackground:
			origin = (0,1)

		x = units.toLength(eval(object["x"])) + origin[0]
		y = origin[1] + units.toLength(eval(object["y"]))

		draw(object, x, y)

# Print the dynamic bands (Detail, GroupHeader, GroupFooter):
y = pageHeaderOrigin[1]
groups = form.Groups

recno = 0
for record in data:
	for band in ("Detail",):
		bandDict = eval("form.%s" % band)
		x = ml
		y = y - units.toLength(eval(bandDict["height"]))
		width = pageWidth - ml - mr
		height = units.toLength(eval(bandDict["height"]))

		if showBands:
			printBandOutline("%s (record %s)" % (band, recno), x, y, width, height)
		for object in bandDict["objects"]:
			x = ml + units.toLength(eval(object["x"]))
			y1 = y + units.toLength(eval(object["y"]))
			draw(object, x, y1)
				
		recno += 1

c.save()

