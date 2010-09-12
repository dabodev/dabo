# -*- coding: utf-8 -*-
import sys
import os
import glob

defaultExtension = "png"

def addExtension(iconName):
	"""If there isn't an extension, add the default extension."""
	splitext = os.path.splitext(iconName)
	if len(splitext[1]) == 0:
		iconName = "%s.%s" % (iconName, defaultExtension)
	return iconName


def getIcon(iconName):
	iconName = addExtension(iconName)
	return open("%s/%s" % (__path__[-1:][0], iconName), 'rb').read()


def getIconFileName(iconName):
	"""Returns the full path and file name of the passed icon name.

	If not found, returns None.
	"""
	iconName = addExtension(iconName)
	ret = os.path.join(__path__[-1:][0], "%s" % iconName)

	if not os.path.exists(ret):
		ret = None
		for pth in sys.path:
			icn = os.path.join(pth, "%s" % iconName)
			if os.path.exists(icn):
				ret = icn
				break
	return ret


def getAvailableIcons():
	"""Returns a list of all available icon names."""
	ret = []
	pth = __path__[0]
	defExt = ".%s" % defaultExtension
	exts = ["png", "jpg", "gif", "bmp"]
	for ext in exts:
		ics = glob.glob("%s/*.%s" % (pth, ext))
		ret += [os.path.split(ic)[-1].replace(defExt, "") for ic in ics]
	return ret
