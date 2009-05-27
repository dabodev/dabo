# -*- coding: utf-8 -*-
""" External libraries that can be loaded into Daboized applications.
"""

# Don't put any import statements here. Code will explicitly import 
# what it needs. For example:
#	from dabo.lib.ListSorter import ListSorter
#	import dabo.lib.ofFunctions as oFox

import os
import sys
import uuid
import dabo


def getRandomUUID():
	return str(uuid.uuid4())


def getMachineUUID():
	return str(uuid.uuid1())


try:
	import simplejson
except ImportError:
	# Not installed in site-packages; use the included version
	pth = os.path.split(dabo.__file__)[0]
	sys.path.append("%s/lib" % pth)
	import simplejson

import dejavuJSON
jsonConverter = dejavuJSON.Converter()
def jsonEncode(val):
	return jsonConverter.dumps(val)

def jsonDecode(val):
	ret = None
	try:
		ret = jsonConverter.loads(val)
	except UnicodeDecodeError:
		# Try typical encodings, starting with the default.
		for enctype in (dabo.defaultEncoding, "utf-8", "latin-1"):
			try:
				ret = jsonConverter.loads(val, enctype)
				break
			except UnicodeDecodeError:
				continue
	if ret is None:
		raise
	return ret

