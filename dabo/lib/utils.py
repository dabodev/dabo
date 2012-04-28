# -*- coding: utf-8 -*-

# This serves as a catch-all script for common utilities that may be used
# in lots of places throughout Dabo. Typically, to use a function 'foo()' in
# this file, add the following import statement to your script:
#
#	import dabo.lib.utils as utils
#
# Then, in your code, simply call:
#
#	utils.foo()

import os
osp = os.path
import sys
import dabo
from dabo.dLocalize import _
from locale import getpreferredencoding
try:
	from win32com.shell import shell, shellcon
except ImportError:
	shell, shellcon = None, None


# can't compare NoneType to some types: sort None lower than anything else:
def noneSortKey(vv):
	vv = vv[0]
	if vv is None:
		return (0, None)
	else:
		return (1, vv)


def caseInsensitiveSortKey(vv):
	return (vv[0] or "").lower()


def reverseText(tx):
	"""
	Takes a string and returns it reversed. Example:

	utils.reverseText("Wow, this is so cool!")
		=> returns "!looc os si siht ,woW"
	"""
	return tx[::-1]


def getUserHomeDirectory():
	"""
	Return the user's home directory in a platform-portable way.

	If the home directory cannot be determined, return None.
	"""
	hd = None

	# If we are on Windows and win32com is available, get the user home
	# directory using the Windows API:
	if shell and shellcon:
		return shell.SHGetFolderPath(0, shellcon.CSIDL_PROFILE, 0, 0)

	# os.path.expanduser should work on all posix systems (*nix, Mac, and some
	# Windows NT setups):
	hd = osp.expanduser("~")

	# If for some reason the posix function above didn't work, most Linux setups
	# define the environmental variable $HOME, and perhaps this is done sometimes
	# on Mac and Win as well:
	if hd is None:
		hd = os.environ.get("HOME")

	# If we still haven't found a value, Windows tends to define a $USERPROFILE
	# directory, which usually expands to something like
	#	 c:\Documents and Settings\maryjane
	if hd is None:
		hd = os.environ.get("USERPROFILE")

	return hd


def getUserAppDataDirectory(appName="Dabo"):
	"""
	Return the directory where Dabo can save user preference and setting information.

	On \*nix, this will be something like /home/pmcnett/.dabo
	On Windows, it will be more like c:\Documents and Settings\pmcnett\Application Data\Dabo

	This function relies on platform conventions to determine this information. If it
	cannot be determined (because platform conventions were circumvented), the return
	value will be None.

	if appName is passed, the directory will be named accordingly.

	This function will try to create the directory if it doesn't already exist, but if the
	creation of the directory fails, the return value will revert to None.
	"""
	dd = None

	if sys.platform not in ("win32",):
		# On Unix, change appname to lower, don't allow spaces, and prepend a ".":
		appName = ".%s" % appName.lower().replace(" ", "_")

	# First, on Windows, try the Windows API function:
	if shell and shellcon:
		dd = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)

	if dd is None and sys.platform == "win32":
		# We are on Windows, but win32com wasn't installed. Look for the APPDATA
		# environmental variable:
		dd = os.environ.get("APPDATA")

	if dd is None:
		# We are either not on Windows, or we couldn't locate the directory for
		# whatever reason. Try going off the home directory:
		dd = getUserHomeDirectory()

	if dd is not None:
		dd = osp.join(dd, appName)
		if not osp.exists(dd):
			# try to create the dabo directory:
			try:
				os.makedirs(dd)
			except OSError:
				sys.stderr.write("Couldn't create the user setting directory (%s)." % dd)
				dd = None
	return dd


def getSharedAppDataDirectory(appName="Dabo"):
	"""
	Return the directory where Dabo can store shared mutable data.

	On \*nix, this will be something like /var/lib/dabo
	On Windows, it will be more like c:\Documents and Settings\All Users\Application Data\Dabo

	This function relies on platform conventions to determine this information. If it
	cannot be determined (because platform conventions were circumvented), the return
	value will be None.

	if appName is passed, the directory will be named accordingly.

	This function will try to create the directory if it doesn't already exist, but if the
	creation of the directory fails, the return value will revert to None.
	"""
	dd = None

	if sys.platform not in ("win32",):
		# On Unix, change appname to lower, don't allow spaces.
		appName = "%s" % appName.lower().replace(" ", "_")

	if sys.platform in ("win32",):
		# On Windows platform, get information using shell32 library function.
		if shell and shellcon:
			dd = shell.SHGetFolderPath(0, shellcon.CSIDL_COMMON_APPDATA, 0, 0)
		if dd is None:
			dd = os.environ.get("ALLUSERSPROFILE")
	elif sys.platform in ("darwin", "mac"):
		# We are on OS X.
		# Maybe "/Library/Application Support" is more adequate here.
		dd = osp.join(os.sep, "Users", "Shared")
	else:
		# It's probably *nix machine.
		dd = osp.join(os.sep, "var", "lib")

	if dd is not None:
		dd = osp.join(dd, appName)
		if not osp.exists(dd):
			# Try to create the dabo directory.
			try:
				os.makedirs(dd)
			except OSError:
				sys.stderr.write("Couldn't create the user setting directory (%s)." % dd)
				dd = None
	return dd


def dictStringify(dct):
	"""
	The ability to pass a properties dict to an object relies on
	the practice of passing '\*\*properties' to a function. Seems that
	Python requires that the keys in any dict being expanded like
	this be strings, not unicode. This method returns a dict with all
	unicode keys changed to strings.
	"""
	ret = {}
	for kk, vv in dct.items():
		if isinstance(kk, unicode):
			try:
				ret[str(kk)] = vv
			except UnicodeEncodeError:
				kk = kk.encode(dabo.getEncoding())
				ret[kk] = vv
		else:
			ret[kk] = vv
	return ret


def getEncodings():
	encodings = (dabo.getEncoding(), getpreferredencoding(), "iso8859-1", "iso8859-15", "cp1252", "utf-8")
	for enc in encodings:
		yield enc


def ustr(value):
	"""
	Convert the passed value to a python unicode object.

	When converting to a string, do not use the str() function, which
	can create encoding errors with non-ASCII text.
	"""
	if isinstance(value, unicode):
		# Don't change the encoding of an object that is already unicode.
		return value
	if isinstance(value, Exception):
		return exceptionToUnicode(value)
	try:
		## Faster for all-ascii strings and converting from non-basestring types::
		return unicode(value)
	except UnicodeDecodeError:
		# Most likely there were bytes whose integer ordinal were > 127 and so the
		# default ASCII codec used by unicode() couldn't decode them.
		pass
	except UnicodeEncodeError:
		# Most likely there were bytes whose integer ordinal were > 127 and so the
		# default ASCII codec used by unicode() couldn't encode them.
		pass
	for ln in getEncodings():
		try:
			return unicode(value, ln)
		except UnicodeError:
			pass
	raise UnicodeError("Unable to convert '%r'." % value)


def exceptionToUnicode(e):
	# Handle DBQueryException first.
	if hasattr(e, "err_desc"):
		return ustr(e.err_desc)
	if hasattr(e, "args") and e.args:
		return "\n".join((ustr(a) for a in e.args))
	if hasattr(e, "message"):
		# message is deprecated in python 2.6
		return ustr(e.message)
	try:
		return ustr(e)
	except:
		return u"Unknown message."


def relativePathList(toLoc, fromLoc=None):
	"""
	Given two paths, returns a list that, when joined with
	os.path.sep, gives the relative path from 'fromLoc' to
	"toLoc'. If 'fromLoc' is not specified, the current directory
	is assumed.
	"""
	if fromLoc is None:
		try:
			fromLoc = dabo.dAppRef.HomeDirectory
		except AttributeError:
			# No app object
			fromLoc = os.getcwd()
	if toLoc.startswith(".."):
		if osp.isdir(fromLoc):
			toLoc = osp.join(fromLoc, toLoc)
		else:
			toLoc = osp.join(osp.split(fromLoc)[0], toLoc)
	toLoc = osp.abspath(osp.normpath(toLoc))
	if osp.isfile(toLoc):
		toDir, toFile = osp.split(toLoc)
	else:
		toDir = toLoc
		toFile = ""
	fromLoc = osp.abspath(fromLoc)
	if osp.isfile(fromLoc):
		fromLoc = osp.split(fromLoc)[0]
	fromList = fromLoc.split(osp.sep)
	toList = toDir.split(osp.sep)
	# There can be empty strings from the split
	while len(fromList) > 0 and not fromList[0]:
		fromList.pop(0)
	while len(toList) > 0 and not toList[0]:
		toList.pop(0)
	lev = 0
	while (len(fromList) > lev) and (len(toList) > lev) and \
			(fromList[lev] == toList[lev]):
		lev += 1

	# 'lev' now contains the first level where they differ
	fromDiff = fromList[lev:]
	toDiff = toList[lev:]
	ret = [".."] * len(fromDiff) + toDiff
	if toFile:
		ret += [toFile]
	return ret


def relativePath(toLoc, fromLoc=None):
	"""Given two paths, returns a relative path from fromLoc to toLoc."""
	return osp.sep.join(relativePathList(toLoc, fromLoc))


def getPathAttributePrefix():
	return "path://"


def resolveAttributePathing(atts, pth=None, abspath=False):
	"""
	Dabo design files store their information in XML, which means
	when they are 'read' the values come back in a dictionary of
	attributes, which are then used to restore the designed object to its
	intended state. Path values will be stored in a relative path format,
	with the value preceeded by the string returned by
	getPathAttributePrefix(); i.e., 'path://'.

	This method finds all values that begin with the 'path://' label,
	strips off that label, converts the paths back to values that
	can be used by the object, and then updates the attribute dict with
	those new values.
	"""
	prfx = getPathAttributePrefix()
	pathsToConvert = ((kk, vv) for kk, vv in atts.items()
			if isinstance(vv, basestring) and vv.startswith(prfx))
	for convKey, convVal in pathsToConvert:
		# Strip the path designator
		convVal = convVal.replace(prfx, "")
		if abspath:
			if pth:
				retPath = osp.normpath(osp.join(pth, convVal))
			else:
				retPath = resolvePath(convVal, pth, True)
		else:
			# Convert to relative path
			retPath = relativePath(convVal, pth)
		# Update the atts
		atts[convKey] = retPath


def resolvePath(val, pth=None, abspath=False):
	"""
	Takes a single string value in the format Dabo uses to store pathing
	in XML, and returns the original path relative to the specified path (or the
	current directory, if no pth is specified). If 'abspath' is True, returns an
	absolute path instead of the default relative path.
	"""
	prfx = getPathAttributePrefix()
	# Strip the path designator
	val = val.replace(prfx, "")
	# Convert to relative path
	ret = relativePath(val, pth)
	if abspath:
		ret = osp.abspath(ret)
	return ret


def locateRelativeTo(containerPath, itemPath):
	"""
	Paths to items, such as custom contained classes, should be relative to
	the container they are in.
	"""
	# Start with the item's current location
	dirsToCheck = [""]
	if containerPath:
		# Add the location of the containing form or class
		containerDir = osp.dirname(containerPath)
		dirsToCheck.append(containerDir)
	try:
		# Look in the standard Dabo app directories. We may not be
		# running with an active app reference, so the try/except
		# will handle that.
		appPaths = dabo.dAppRef.getStandardDirectories()
		dirsToCheck.extend(appPaths)
	except AttributeError:
		pass
	# Add the current working directory
	dirsToCheck.append(os.getcwd())
	itemName = osp.basename(itemPath)
	# Default to the original value
	resolved = itemPath
	for testDir in dirsToCheck:
		testPath = osp.join(testDir, itemName)
		if osp.exists(testPath):
			# We found the file
			resolved = testPath
			break
	return resolved


def resolvePathAndUpdate(srcFile):
	app = dabo.dAppRef
	try:
		hd = app.HomeDirectory
	except AttributeError:
		# There is no app object
		hd = os.getcwd()
	opexists = os.path.exists
	# Make sure that the file exists
	if not opexists(srcFile):
		# Try common paths. First use the whole string; then use
		# each subdirectory in turn.
		fname = srcFile
		keepLooping = True
		while keepLooping:
			keepLooping = False
			for subd in ("ui", "forms", "menus", "resources", "db", "biz", "reports"):
				newpth = os.path.join(hd, subd, fname)
				if opexists(newpth):
					srcFile = newpth
					break
			if not opexists(srcFile):
				try:
					fname = fname.split(os.path.sep, 1)[1]
					keepLooping = True
				except IndexError:
					# No more directories to remove
					break
	if app is not None:
		if app.SourceURL:
			# The srcFile has an absolute path; the URLs work on relative.
			try:
				splt = srcFile.split(hd)[1].lstrip("/")
			except IndexError:
				splt = srcFile
			app.urlFetch(splt)
			try:
				nm, ext = os.path.splitext(splt)
			except ValueError:
				# No extension; skip it
				nm = ext = ""
			if ext == ".cdxml":
				# There might be an associated code file. If not, the error
				# will be caught in the app method, and no harm will be done.
				codefile = "%s-code.py" % nm
				app.urlFetch(codefile)
	# At this point the file should be present and updated. If not...
	if not os.path.exists(srcFile):
		raise IOError(_("The file '%s' cannot be found") % srcFile)
	return srcFile


def cleanMenuCaption(cap, bad=None):
	"""
	Menu captions can contain several special characters that make them
	unsuitable for things such as preference settings. This method provides
	a simple way of getting the 'clean' version of these captions. By default it
	strips ampersands, spaces and periods; you can change that by passing
	the characters you want stripped in the 'bad' parameter.
	"""
	if bad is None:
		bad = "&. "
	ret = cap
	for ch in bad:
		ret = ret.replace(ch, "")
	return ret
