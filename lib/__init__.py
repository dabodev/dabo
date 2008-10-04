# -*- coding: utf-8 -*-
""" External libraries that can be loaded into Daboized applications.
"""

# Don't put any import statements here. Code will explicitly import 
# what it needs. For example:
#	from dabo.lib.ListSorter import ListSorter
#	import dabo.lib.ofFunctions as oFox

import uuid

try:
	import dejavuJSON
except:
	jsonConverter = None
	def jsonEncode(val): raise ImportError, "The simplejson module is not installed"
	def jsonDecode(val): raise ImportError, "The simplejson module is not installed"
else:
	jsonConverter = dejavuJSON.Converter()
	def jsonEncode(val):
		return jsonConverter.dumps(val)
	
	def jsonDecode(val):
		return jsonConverter.loads(val)


def getRandomUUID():
	return str(uuid.uuid4())


def getMachineUUID():
	return str(uuid.uuid1())
