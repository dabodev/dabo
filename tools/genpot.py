"""This script scans project directories and generates the .pot files needed for localization."""
import os
import popen2


def processLoc(proj, drct, xtra=None):
	if xtra is None:
		pth = drct
		xtra = ""
	else:
		pth = os.path.join(drct, xtra)
	flist = os.listdir(pth)
	for fname in flist:
		if fname.startswith("."):
			# Hidden file; skip
			continue
		fullname = os.path.join(pth, fname)
		newXtra = os.path.join(xtra, fname)
		if os.path.isdir(fullname):
			processLoc(proj, drct, newXtra)
		else:
			if fname.endswith(".py"):
				os.system("xgettext -d dabo -L Python %s" % fullname)


def main():
	### NOTE: This must be configured with your local paths
	projects = {"dabo": "/path/to/dabo/",
			"ide": "/path/to/ide/",
			"demo": "/path/to/demo/"}
	for project, drct in list(projects.items()):
		processLoc(project, drct)
	

if __name__ == "__main__":
	main()
