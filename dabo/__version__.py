# The following 2 lines are the only thing you should change in this file.
# Everything else is boilerplate copied also to other dabo repositories.
package_name = "dabo"
_version = "0.7s"


import os
import lib

_revision = None
# First, try to get the revisionfrom svninfo, which lets the developer go back 
# and forth through revisions and the version information will still reflect
# reality.
package_path = os.path.split(os.path.split(lib.__file__)[0])[0]
if os.path.exists(os.path.join(package_path, ".svn")):
	try:
		_revision = os.popen("svnversion %s" % package_path).read().strip()
		if not _revision[0].isdigit():
			_revision = None
	except:
		pass

if _revision is None:
	# Okay, svninfo not available, which probably means svn isn't present, which
	# means the version information in lib._daborevs will likely be correct. That
	# revision information reflects the current revision at the time the 
	# distribution was rolled up.
	from lib._daborevs import _revs
	_revision = _revs.get(package_name, "")

version = {"version": _version,
		"revision": _revision}

if __name__ == "__main__":
	print """
Package Name: %s
     Version: %s
    Revision: %s
""" % (package_name, version["version"], version["revision"])
