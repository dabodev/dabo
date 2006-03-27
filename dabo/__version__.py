import os
import dabo

_version = "0.6s"

# If dabo is a subversion working copy, we'll try to get the current revision 
# using the svnversion command against that working copy. Otherwise, we'll get
# the revision as saved in _daborevs, which is an external svn repository 
# updated by a svn post-commit hook on the server. 
daboPath = dabo.__path__[0]
_revision = None
olddir = os.getcwd()

if os.path.exists(os.path.join(daboPath, ".svn")):
	try:
		os.chdir(daboPath)
		_revision = os.popen("svnversion .").read().strip()
	except:
		pass
	os.chdir(olddir)

if _revision is None:
	from dabo.lib._daborevs import _revs
	_revision = _revs["dabo"]

version = {"version": _version,
		"revision": _revision}

if __name__ == "__main__":
	print "Dabo Version: %s \n    Revision: %s" % (
		version["version"], version["revision"])
