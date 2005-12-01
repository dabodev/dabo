import sys
import os

def getIcon(iconName):
	return open("%s/%s.png" % (__path__[-1:][0], iconName), 'rb').read()

def getIconFileName(iconName):
	ret = os.path.join(__path__[-1:][0], "%s.png" % iconName)
	
	if not os.path.exists(ret):
		for pth in sys.path:
			icn = os.path.join(pth, "%s.png" % iconName)
			if os.path.exists(icn):
				ret = icn
				break	
	return ret
