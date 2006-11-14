""" External libraries that can be loaded into Daboized applications.
"""

# Don't put any import statements here. Code will explicitly import 
# what it needs. For example:
#	from dabo.lib.ListSorter import ListSorter
#	import dabo.lib.ofFunctions as oFox

from uuid import uuid4
def getRandomUUID():
	return str(uuid4())
