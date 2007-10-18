#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo uses a copy of my invoice report with bogus data to show how to
interact with the ReportWriter to create a PDF. Run this script to create
invoice.pdf. To modify the report form, use daboide/ReportDesigner to open
the invoice.rfxml file.
"""

from dabo.lib.reportWriter import ReportWriter
from dabo.lib import reportUtils

outFile = "invoice.pdf"

print "Instantiating the report writer..."
rw = ReportWriter()

# Set some required properties:
rw.ReportFormFile = "invoice.rfxml"
rw.OutputFile = "%s" % outFile
# (Normally, you'd also set the Cursor property, to provide the data,
#  but this sample just uses the test cursor inside the report form.)

# Set some optional properties:
rw.UseTestCursor = True
rw.ShowBandOutlines = True

print "Writing %s..." % outFile
rw.write()

print "Trying to preview it..."
reportUtils.previewPDF(outFile)
