# -*- coding: utf-8 -*-
""" External libraries that can be loaded into Daboized applications.
"""

# Don't put any import statements here. Code will explicitly import 
# what it needs. For example:
#	from dabo.lib.ListSorter import ListSorter
#	import dabo.lib.ofFunctions as oFox

import uuid
import dabo


def getRandomUUID():
	return str(uuid.uuid4())


def getMachineUUID():
	return str(uuid.uuid1())


try:
	import simplejson
except:
	jsonConverter = None
	def jsonEncode(val): raise ImportError, "The simplejson module is not installed"
	def jsonDecode(val): raise ImportError, "The simplejson module is not installed"
else:
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
