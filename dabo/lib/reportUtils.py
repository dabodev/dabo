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


def previewPDF(path):
	"""Preview the passed PDF file in the default PDF viewer."""
	try:
		os.startfile(path)
	except AttributeError:
		# startfile only available on Windows
		if sys.platform == "darwin":
			os.system("open %s" % path)
		else:
			# on Linux, punt with xpdf:
			os.popen2("xpdf %s" % path)


