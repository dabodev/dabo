##  reportWriter.py
##  begun 2/14/2005 by pkm
##  This is just a first pass, with ugly procedural code. When you run it by
##  "python reportWriter.py", it'll read the samplespec.py file and create a
##  test.pdf file.

import sys
from reportlab.pdfgen.canvas import Canvasimport reportlab.lib.pagesizes as pagesizes

#form = sys.argv[1]
import samplespec as form

#data = sys.argv[2]
data = [{"cArtist": "The Clash", "iid": 1},
        {"cArtist": "Queen", "iid": 2},
        {"cArtist": "Ben Harper and the Innocent Criminals", "iid":3}]

# Draw a dotted rectangle around each band:
showBands = True

unit = form.Page["unit"]
if unit == "inch":
	u = 72

if form.Page["size"] == "letter":
	pageSize = pagesizes.letter
elif form.Page["size"] == "a4":
	pageSize = pagesizes.a4

c = Canvas("test.pdf", pagesize=pageSize)
pageWidth, pageHeight = pageSize

print "pageWidth, pageHeight:", pageWidth, pageHeight

pageHeaderOrigin = (u*form.Page["margin"]["left"],
                   pageHeight - (u*form.Page["margin"]["top"])
                              - (u*form.PageHeader["height"]))
pageHeaderDestination = (pageWidth - (u*form.Page["margin"]["right"]),
                   pageHeight - (u*form.Page["margin"]["top"]))

print "pageHeaderOrigin, pageHeaderDestination:", pageHeaderOrigin, pageHeaderDestination

pageFooterOrigin = (u*form.Page["margin"]["left"], 
                    u*form.Page["margin"]["bottom"])
pageFooterDestination = (pageWidth - (u*form.Page["margin"]["right"]),
                    u*(form.PageFooter["height"] + form.Page["margin"]["bottom"]))

print "pageFooterOrigin, pageFooterDestination:", pageFooterOrigin, pageFooterDestination

ml = u*form.Page["margin"]["left"]
mt = u*form.Page["margin"]["top"]
mr = u*form.Page["margin"]["right"]
mb = u*form.Page["margin"]["bottom"]


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

	try: width = (u*object["width"])
	except (KeyError, TypeError): width = None

	try: height = (u*object["height"])
	except (KeyError, TypeError): height = None

	try: rotation = object["rotation"]
	except KeyError:	rotation = 0

	c.rotate(rotation)

	if object["type"] == "rectangle":
		try: lineWidth = object["lineWidth"]
		except KeyError: lineWidth = 1
		c.setLineWidth(lineWidth)
		c.rect(x,y,width,height)

	elif object["type"] == "string":
		try: borderWidth = object["borderWidth"]
		except KeyError: borderWidth=0

		if borderWidth <= 0:
			stroke = 0
		else:
			stroke = 1

		c.setLineWidth(borderWidth)

		if width is not None and height is not None:
			# clip the text to the specified width and height
			p = c.beginPath()
			if object["alignment"] == "center":
				posx = x - (width/2)
			elif object["alignment"] == "right":
				posx = x + width
			else:
				posx = x

			p.rect(posx,y,width,height)
			c.clipPath(p, stroke=stroke)

		funcs = {"center": c.drawCentredString,
		         "right": c.drawRightString,
		         "left": c.drawString}
		func = funcs[object["alignment"]]
		fontFace = object["fontFace"]
		fontSize = object["fontSize"]
		c.setFont(fontFace, fontSize)
		func(x,y,eval(object["expression"]))

	elif object["type"] == "image":
		try: mask = object["mask"]
		except: mask = None
		c.drawImage(eval(object["expression"]), x, y, width, height, mask)
	c.restoreState()


# Print the static bands (Page Header/Footer, Watermark):
for band in ("PageBackground", "PageHeader", "PageFooter"):
	bandDict = eval("form.%s" % band)
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
		height = bandDict["height"] * u

	if showBands:
		printBandOutline(band, x, y, width, height)

	for object in bandDict["objects"]:
		if bandDict == form.PageFooter:
			origin = pageFooterOrigin
		elif bandDict == form.PageHeader:
			origin = pageHeaderOrigin
		elif bandDict == form.PageBackground:
			origin = (0,1)

		x = u*object["x"] + origin[0]
		y = origin[1] + (u*object["y"])

		draw(object, x, y)

# Print the dynamic bands (Detail, GroupHeader, GroupFooter):
y = pageHeaderOrigin[1]
groups = form.Groups

recno = 0
for record in data:
	for band in ("Detail",):
		bandDict = eval("form.%s" % band)
		x = ml
		y = y - (u*bandDict["height"])
		width = pageWidth - ml - mr
		height = bandDict["height"] * u

		if showBands:
			printBandOutline("%s (record %s)" % (band, recno), x, y, width, height)

		for object in bandDict["objects"]:
			x = ml + (u*object["x"])
			y1 = y + (u*object["y"])
			draw(object, x, y1)
				
		recno += 1

c.save()

