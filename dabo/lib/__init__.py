# -*- coding: utf-8 -*-
"""External libraries that can be loaded into Daboized applications."""

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
	# cjson is fastest; use that if available.
	import cjson as json
	jsonEncode = json.encode
	jsonDecode = json.decode
except ImportError:
	try:
		import simplejson as json
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
				for enctype in (dabo.getEncoding(), "utf-8", "latin-1"):
					try:
						ret = jsonConverter.loads(val, enctype)
						break
					except UnicodeDecodeError:
						continue
			if ret is None:
				raise
			return ret
	except ImportError:
		# Python 2.6 comes with the json module built-in
		try:
			import json
			jsonEncode = json.dumps
			jsonDecode = json.loads
		except ImportError:
			jsonConverter = None
			def jsonEncode(val):
				raise ImportError("The cjson, simplejson, or json modules are not installed")
			def jsonDecode(val):
				raise ImportError("The cjson, simplejson, or json modules are not installed")
