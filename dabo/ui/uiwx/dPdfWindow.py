# -*- coding: utf-8 -*-
# TODO: wait for Robin's feed back
import os
import wx
import dabo

if __name__ == "__main__":
	import dabo.ui
	dabo.ui.loadUI("wx")
	if __package__ is None:
		import dabo.ui.uiwx
		__package__ = "dabo.ui.uiwx"

from dabo.ui import makeDynamicProperty
import dControlMixin as cm
from dabo.dLocalize import _

# Need to define this exception class for x-platform
try:
	WindowsError
except:
	class WindowsError: pass

try:
	import wx.lib.pdfwin as pdfwin
	PDFWindow = pdfwin.PDFWindow
except Exception:
	## If there's any exception at all in importing pdfwin, use the dummy.
	class Dummy(object):
		_dummy = True
	PDFWindow = Dummy


class dPdfWindow(cm.dControlMixin, PDFWindow):
	"""
	Displays a PDF file on Windows using Adobe Acrobat Reader in a panel.

	See wx.lib.pdfwin.PDFWindow for the API.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		if hasattr(PDFWindow, "_dummy"):
			raise ImportError("wx.lib.pdfwin couldn't be imported, so dPdfWindow cannot instantiate.")

		self._baseClass = dPdfWindow
		preClass = pdfwin.PDFWindow
		cm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)



class _dPdfWindow_test(dPdfWindow):
	def afterInit(self):
		# Run the dReportWriter test, which will output a test
		# pdf in this directory, and load that into the dPdfWindow:
		os.system("python ../../dReportWriter.py")
		self.LoadFile(os.path.abspath("dRW-test.pdf"))


if __name__ == "__main__":
	from . import test
	test.Test().runTest(_dPdfWindow_test)

