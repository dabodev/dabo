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


def getPt(val):
	"""Given a string or a number, convert the value into a numeric pt value.

	Strings can have the unit appended, like "3.5 in", "2 cm", "3 pica", "10 mm".

	> print getPt("1 in")
	72
	> print getPt("1")
	1
	> print getPt(1)
	1
	"""
	if type(val) in (int, long, float):
		# return as-is as the pt value.
		return val
	else:
		# try to run it through reportlab's units.toLength() function:
		return units.toLength(val)


#data = sys.argv[2]
data = [{"cArtist": "The Clash", "iid": 1},
        {"cArtist": "Queen", "iid": 2},
        {"cArtist": "Ben Harper and the Innocent Criminals", "iid":3}]

# The report dict contains information about the running report:
report = {}
report["bands"] = {}


# Draw a dotted rectangle around each band:
showBands = True

## Set the Page Size:
# get the string pageSize value from the spec file:
pageSize = eval(form.Page["size"])
# reportlab expects the pageSize to be upper case:
pageSize = pageSize.upper()
# convert to the reportlab pageSize value (tuple(width,height)):
pageSize = eval("pagesizes.%s" % pageSize)
# run it through the portrait/landscape filter:
try:
	orientation = eval(form.Page["orientation"])
except KeyError:
	orientation = "portrait"
func = eval("pagesizes.%s" % orientation)
pageSize = func(pageSize)
pageWidth, pageHeight = pageSize
print "Page Size:", pageSize
## end Page Size setting (refactor to a separate function)


# Create the report canvas:
c = canvas.Canvas("test.pdf", pagesize=pageSize)


# Set the page margins:
ml = getPt(eval(form.Page["marginLeft"]))
mt = getPt(eval(form.Page["marginTop"]))
mr = getPt(eval(form.Page["marginRight"]))
mb = getPt(eval(form.Page["marginBottom"]))


# Page header/footer origins are needed in various places:
pageHeaderOrigin = (ml, pageHeight - mt 
                    - getPt(eval(form.PageHeader["height"])))
pageFooterOrigin = (ml, mb)


def printBandOutline(band, x, y, width, height):
		## draw a dotted rectangle around the entire band, and type a small faded 
		## caption at the origin of the band.
		c.saveState()
		c.setLineWidth(0.1)
		c.setStrokeColorRGB(0.8, 0.5, 0.7)
		c.setDash(1, 2)
		c.rect(x, y, width, height)
		c.setFont("Helvetica", 8)
		c.setFillColor((0.6, 0.8, 0.7))
		c.drawString(x, y, band)
		c.restoreState()

def draw(object, x, y):
	c.saveState()

	try: 
		width = getPt(eval(object["width"]))
	except (KeyError, TypeError, ValueError): 
		width = 25

	try: 
		height = getPt(eval(object["height"]))
	except (KeyError, TypeError, ValueError): 
		height = 25

	try: 
		rotation = eval(object["rotation"])
	except KeyError:
		rotation = 0

	try:
		hAnchor = eval(object["hAnchor"])
	except:
		hAnchor = "left"

	try:
		vAnchor = eval(object["vAnchor"])
	except:
		vAnchor = "bottom"

	if hAnchor == "right":
		x = x - width
	elif hAnchor == "center":
		x = x - (width / 2)
	
	if vAnchor == "top":
		y = y - height
	elif vAnchor == "center":
		y = y - (height / 2)

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
			props["strokeWidth"] = getPt(eval(object["strokeWidth"]))
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
			borderWidth = getPt(eval(object["borderWidth"]))
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
	report["bands"][band] = {}
	bandDict = eval("form.%s" % band)

	# Find out geometry of the band and fill into report["bands"][band]
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
		height = getPt(eval(bandDict["height"]))

	report["bands"][band]["x"] = x
	report["bands"][band]["y"] = y
	report["bands"][band]["width"] = width
	report["bands"][band]["height"] = height

	if showBands:
		printBandOutline(band, x, y, width, height)

	for object in bandDict["objects"]:

		if bandDict == form.PageHeader:
			origin = pageHeaderOrigin
		elif bandDict == form.PageFooter:
			origin = pageFooterOrigin
		elif bandDict == form.PageBackground:
			origin = (0,1)

		x = getPt(eval(object["x"])) + origin[0]
		y = origin[1] + getPt(eval(object["y"]))

		draw(object, x, y)

# Print the dynamic bands (Detail, GroupHeader, GroupFooter):
y = pageHeaderOrigin[1]
groups = form.Groups

recno = 0
for record in data:
	for band in ("Detail",):
		bandDict = eval("form.%s" % band)
		x = ml
		y = y - getPt(eval(bandDict["height"]))
		width = pageWidth - ml - mr
		height = getPt(eval(bandDict["height"]))

		if showBands:
			printBandOutline("%s (record %s)" % (band, recno), x, y, width, height)
		for object in bandDict["objects"]:
			x = ml + getPt(eval(object["x"]))
			y1 = y + getPt(eval(object["y"]))
			draw(object, x, y1)
				
		recno += 1

c.save()

