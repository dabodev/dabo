# The following 2 lines are the only thing you should change in this file.
# Everything else is boilerplate copied also to other dabo repositories.
package_name = "dabo"
_version = "0.7a"


import os
from lib._daborevs import _revs

# We'll get the revision as saved in _daborevs, which is an external svn 
# repository updated by a svn post-commit hook on the server. 

_revision = _revs.get(package_name, "")

version = {"version": _version,
		"revision": _revision}

if __name__ == "__main__":
	print """
Package Name: %s
     Version: %s
    Revision: %s
""" % (package_name, version["version"], version["revision"])
