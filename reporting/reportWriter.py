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
data = [{"artist": "The Clash", "iid": 1},
        {"artist": "Queen", "iid": 2},
        {"artist": "Ben Harper and the Innocent Criminals", "iid":3}]

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


def	printBandOutline(band, x, y, width, height):
		## draw a dotted rectangle around the entire band, and type a small faded 
		## caption at the origin of the band.
		c.saveState()
		c.setLineWidth(0.1)
		c.setStrokeColorRGB(0.2,0.5,0.3)
		c.setDash(1,2)
		c.rect(x,y,width,height)
		c.setFont("Helvetica", 8)
		c.drawString(ml, y, band)
		c.restoreState()


# Print the static bands (Page Header/Footer):
for band in ("PageHeader", "PageFooter"):
	bandDict = eval("form.%s" % band)
	x = ml
	if band == "PageHeader":
		y = pageHeaderOrigin[1]
	elif band == "PageFooter":
		y = pageFooterOrigin[1]
	width = pageWidth - ml - mr
	height = bandDict["height"] * u

	if showBands:
		printBandOutline(band, x, y, width, height)

	for object in bandDict["objects"]:
		c.setLineWidth(object["lineWidth"])
		geo = object["geometry"]
	
		x = u*geo["x"] + ml
		width = (u*geo["width"])

		if bandDict == form.PageFooter:
			origin = pageFooterOrigin[1]
		elif bandDict == form.PageHeader:
			origin = pageHeaderOrigin[1]

		print "band, origin:", band, origin

		y = origin + (u*geo["y"])
		height = (u*geo["height"])

		print "x,y,width,height:", x, y, width, height
		c.rect(x,y,width,height)		

# Print the dynamic bands (Detail, GroupHeader, GroupFooter):
y = pageHeaderOrigin[1]
for record in data:
#	for band in ("GroupHeader", "GroupFooter", "Detail"):
	for band in ("Detail",):
		bandDict = eval("form.%s" % band)
		x = ml
		y = y - (u*bandDict["height"])
		width = pageWidth - ml - mr
		height = bandDict["height"] * u

		if showBands:
			printBandOutline(band, x, y, width, height)
		
c.save()

