#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import datetime
import dabo


class Manifest(object):
	"""This class encapsulates all of the methods needed to create and manage
	a manifest system for syncing directories.

	A manifest is simply a dictionary with the keys being the file paths, and the
	values being a timestamp. Two manifests, referred to as 'source' and 'target',
	can be compared to find the changes required to make 'target' match 'source'.
	"""
	# These are the file types that are included by default.
	includedTypes = ["py", "txt", "cnxml", "rfxml", "cdxml", "mnxml", "xml",
			"jpg" , "jpeg" , "gif" , "tif" , "tiff" , "png" , "ico" , "bmp" , "sh", "mo", "po"]
	# Format for stroring time values
	dtFormat = "%Y-%m-%d %H:%M:%S"


	@classmethod
	def getManifest(cls, pth, extraTypes=None, restrictTypes=None):
		"""Given a path, returns the manifest for the files on that path. Only the
		main file types are included; if you require additional types, pass them in
		the 'extraTypes' parameter as a list or tuple. If you don't want the standard
		included types, pass a list/tuple of the types you want in the 'restrictTypes'
		parameter, and only those types will be included.
		"""
		if restrictTypes is not None:
			okTypes = list(restrictTypes)
		else:
			if extraTypes is not None:
				okTypes = cls.includedTypes + list(extraTypes)
			else:
				okTypes = cls.includedTypes
		# Make sure the path exists
		pth = os.path.expanduser(pth)
		if not os.path.exists(pth):
			raise OSError("Path '%s' does not exist." % pth)

		# Returned paths are relative to the starting path.
		baseDirName = os.path.split(pth)[-1]
		ret = {}
		pathGen = os.walk(pth)
		for dirname, subdirs, fnames in pathGen:
			# Remove the base path and any leading separator
			reldir = dirname.split(pth)[-1].split(os.path.sep, 1)[-1]
			for fn in fnames:
				ext = os.path.splitext(fn)[1].split(".")[-1]
				if ext in okTypes:
					fullPath = os.path.join(dirname, fn)
					relativePath = os.path.join(reldir, fn)
# 					modtm = datetime.datetime.fromtimestamp(os.stat(fullPath)[8])
# 					ret[relativePath] = modtm.strftime(cls.dtFormat)
					ret[relativePath] = os.stat(fullPath)[8]
		return ret


	@classmethod
	def diff(cls, source, target):
		"""Returns a dict containing the changes that need to be made to make the target
		match the source. Files on the source that have been added or modified will be
		included as usual. Files that have been deleted on the source will also be included,
		but the timestamp will be empty to indicate that it no longer exists on the source.
		"""
		ret = {}
		# These are copies of the original keys in the target. As keys from the source are
		# processed, they will be popped from this list. Any leftover keys indicate deleted
		# files.
		targetKeys = target.keys()
		# Iterate through the source. If the key exists in the target, and the source is
		# newer than the target, add it to the return dict, and then pop the values from both
		# key lists.
		for srcKey, srcTimeString in source.items():
# 			srcTime = datetime.datetime.strptime(srcTimeString, cls.dtFormat)
			srcTime = int(srcTimeString)
			trgTimeString = target.get(srcKey)
			if trgTimeString is None:
				# New on the server
				ret[srcKey] =srcTimeString
			else:
# 				trgTime = datetime.datetime.strptime(trgTimeString, cls.dtFormat)
				trgTime = int(trgTimeString)
				if (srcTime - trgTime) > 0.5:
					# It's newer; include it
					ret[srcKey] =srcTimeString
				# Pop it from the target keys
				targetKeys.remove(srcKey)
		# Ok, we've processed all the source files. Are there any target files remaining?
		# If so, add them with no time value to indicate that they have been deleted from
		# the source.
		for tk in targetKeys:
			ret[tk] = ""
		return ret

