# -*- coding: utf-8 -*-
import datetime

from decimal import Decimal
import os
import sys
import tempfile


class TempFileHolder(object):
	"""Utility class to get temporary file names and to make sure they are 
	deleted when the Python session ends.
	"""
	def __init__(self):
		self._tempFiles = []

	def __del__(self):
		# Try to erase all temp files created during life.
		for f in self._tempFiles:
			try:
				os.remove(f)
			except OSError:
				pass

	def append(self, f):
		self._tempFiles.append(f)

	def getTempFile(self, ext="pdf"):
		if ext[0] != ".":
			ext = ".%s" % ext 
		fd, fname = tempfile.mkstemp(suffix=ext)
		os.close(fd)
		self.append(fname)
		return fname

tempFileHolder = TempFileHolder()
getTempFile = tempFileHolder.getTempFile


def previewPDF(path, modal=False):
	"""Preview the passed PDF file in the default PDF viewer."""
	try:
		os.startfile(path)
	except AttributeError:
		# startfile only available on Windows
		if sys.platform == "darwin":
			os.system("open %s" % path)
		else:
			# On Linux, try to find an installed viewer and just use the first one
			# found. I just don't know how to reliably get the default viewer from 
			# the many distros.
			viewers = ("gpdf", "kpdf", "evince", "acroread", "xpdf", "firefox", 
					"mozilla-firefox")

			viewer = None
			for v in viewers:
				r = os.system("which %s 1> /dev/null 2> /dev/null" % v)
				if r == 0:
					viewer = v
					break

			if viewer:
				if modal:
					sysfunc = os.system
				else:
					sysfunc = os.popen2
				sysfunc("%s '%s'" % (viewer, path))



def printPDF(path):
	"""Print the passed PDF file to the default printer."""
	try:
		os.startfile(path, "print")
	except AttributeError:
		# startfile() only available on Windows
		os.system("lpr %s" % path)



def getTestCursorXmlFromDataSet(dataset):
	"""Returns the xml for insertion into a .rfxml file from a dataset."""
	from dabo.lib.xmltodict import escape

	assert len(dataset) > 0

	xml = """\t<TestCursor>\n"""

	for r in dataset:
		xml += """\t\t<Record\n"""
		for k, v in sorted(r.items()):
			if isinstance(v, basestring):
				v = v.replace("'", "")
			v = repr(v)
			v = escape(v, escapeAmp=False)
			v = v.replace('"', "'")
			xml += """\t\t\t%s = "%s"\n""" % (k, v)
		xml += """\t\t/>\n"""
	
	xml += """\t</TestCursor>\n"""
	return xml


if __name__ == "__main__":
	ds = [{"name": "Paul McNett"},
	      {"name": "A & B Motors"},
	      {"name": '9" Nails'},
	      {"name": "<None>"}]
	print getTestCursorXmlFromDataSet(ds)
