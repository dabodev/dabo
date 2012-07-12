# -*- coding: utf-8 -*-
# The following 3 lines are the only thing you should change in this file.
# Everything else is boilerplate copied also to other dabo repositories.
package_name = "dabo"
_version = "0.9.4"
_approximateRevision = "~7206"

import os
import lib

_revision = None
# First, try to get the revision from svninfo, which lets the developer go back
# and forth through revisions and the version information will still reflect
# reality.
package_path = os.path.split(os.path.split(lib.__file__)[0])[0]
if os.path.exists(os.path.join(package_path, ".svn")):
	try:
		_revision = os.popen("svnversion %s" % package_path).read().strip()
		if not _revision[0].isdigit():
			_revision = None
	except IndexError:
		_revision = None

if _revision is None:
	_revision = _approximateRevision

version = {"version": _version,
		"revision": _revision,
		"file_revision": _approximateRevision.strip("~")}

if __name__ == "__main__":
	print """
Package Name: %s
     Version: %s
    Revision: %s
""" % (package_name, version["version"], version["revision"])
