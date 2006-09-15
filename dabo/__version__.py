import os


# The _version line is the only thing you should change in this file.
# Everything else is boilerplate copied also to other dabo repositories.
package_name = "dabo"
_version = "0.7a"


# If the package is a subversion working copy, we'll try to get the current 
# revision using the svnversion command against that working copy. Otherwise, 
# we'll get the revision as saved in _daborevs, which is an external svn 
# repository updated by a svn post-commit hook on the server. 

cwd_split = os.path.split(os.getcwd())
package_path = ''.join(cwd_split[:-1])

_revision = None
olddir = os.getcwd()

if os.path.exists(os.path.join(package_path, ".svn")):
	try:
		os.chdir(package_path)
		_revision = os.popen("svnversion .").read().strip()
	except:
		pass
	os.chdir(olddir)

if _revision is None:
	from lib._daborevs import _revs
	_revision = _revs[package_name]

version = {"version": _version,
		"revision": _revision}

if __name__ == "__main__":
	print """
Package Name: %s
     Version: %s
    Revision: %s
""" % (package_name, version["version"], version["revision"])
