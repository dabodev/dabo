# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import tempfile
import datetime
from decimal import Decimal

# If gsprint is available, use it for printing:
gsprint = True
try:
	p = subprocess.Popen(("gsprint",), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = p.communicate()
except OSError:
	gsprint = False


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
		# On Windows, use the default PDF viewer (probably Adobe Acrobat)
		os.startfile(path)
	except AttributeError:
		# On Mac, use the default PDF viewer (probably Preview.app)
		if sys.platform == "darwin":
			os.system("open %s" % path)
		else:
			# On Linux, try to find an installed viewer and just use the first one
			# found. I just don't know how to reliably get the default viewer from
			# the many distros.
			viewers = ("gpdf", "kpdf", "okular", "evince", "acroread", "xpdf", "firefox",
					"mozilla-firefox")

			viewer = None
			for v in viewers:
				r = os.system("which %s 1> /dev/null 2> /dev/null" % v)
				if r == 0:
					viewer = v
					break

			if viewer:
				if modal:
					subprocess.call((viewer, path))
				else:
					subprocess.Popen((viewer, path))


def printPDF(path, printerName=None, printerPort=None, copies=1):
	"""Print the passed PDF file to the default printer.

	If gsprint is installed and on the path:
		1) printerName specifies which printer to output to. 
		2) printerPort specifies which port to output to.
		3) multiple copies are handled more efficiently.

	NOTE: gsprint	is part of gsview, and gsview depends on ghostscript.
	These packages are GPL - to avoid legal issues make sure your end 
	user installs themseparately from your application.
	"""
	if gsprint:
		args = ["gsprint", path]
		if printerName:
			args.insert(-1, '-printer')
			args.insert(-1, "%s" % printerName)
		if copies > 1:
			args.insert(-1, '-copies')
			args.insert(-1, str(copies))
		p = subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		p.communicate()
	else:
		for i in range(copies):
			if sys.platform.startswith("win"):
				os.startfile(path, "print")
			else:
				subprocess.Popen(("lpr", path))


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
