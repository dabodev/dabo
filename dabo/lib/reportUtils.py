import os
import sys


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
			except:
				pass

	def append(self, f):
		self._tempFiles.append(f)

	def getTempFile(self, ext="pdf"):
		f = "%s.%s" % (os.tempnam(), ext)
		self.append(f)
		return f

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
				r = os.system("which %s > /dev/null" % v)
				if r == 0:
					viewer = v
					break

			if viewer:
				if modal:
					sysfunc = os.system
				else:
					sysfunc = os.popen2
				sysfunc("%s %s" % (viewer, path))

