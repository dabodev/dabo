""" dabo.icons """
import sys, os

def getIcon(iconName):
	return open("%s/%s.png" % (__path__[-1:][0], iconName), 'rb').read()

def getIconFileName(iconName):
	ret = "%s/%s.png" % (__path__[-1:][0], iconName)
	
	if not os.path.exists(ret):
		for pth in sys.path:
			icn = "%s/%s.png" % (pth, iconName)
			if os.path.exists(icn):
				ret = icn
				break	
	return ret
