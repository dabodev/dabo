""" dabo.icons """

def getIcon(iconName):
	return open("%s/%s.png" % (__path__[-1:][0], iconName), 'rb').read()

def getIconFileName(iconName):
	return "%s/%s.png" % (__path__[-1:][0], iconName)
