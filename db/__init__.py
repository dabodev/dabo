""" dabo.db is the lowest tier, db access. 

This is where the communication to and from the backend database happens, and
cursors get generated to be manipulated by the bizobj's in dabo.biz.

dabo.biz.dBiz is the entity that will interact with this dabo.db stuff, but you
can also work with dabo.db directly if you want. Perhaps you just want to read 
some rows from a backend database in a script. Here's an example of that:

	from connectInfo import ConnectInfo
	from dConnection import dConnection

	ci = ConnectInfo('MySQL')
	ci.host = 'paulmcnett.com'
	ci.dbName = "house"
	ci.user = 'dabo'
	ci.password = 'dabo'

	conn = dConnection(ci).getConnection()
	cursor = conn.cursor()
	print cursor.execute("select * from addressbook order by iid limit 10")
	for row in cursor.fetchall():
		print row[0], row[1]

"""

# TODO: Currently, the logic for building a dictcursor mixin is inside
#       dabo.biz.dBiz. I think this logic should be here in dabo.db.
import datetime
try:
	from decimal import Decimal
except ImportError:
	Decimal = float
from dConnection import dConnection
from dCursorMixin import dCursorMixin
from dConnectInfo import dConnectInfo
from dTable import dTable
from dDataSet import dDataSet

daboTypes = {
		"C": unicode,             ## text
		"M": unicode,             ## memo (longtext) 
		"I": int,                 ## integer
		"G": long,                ## long integer
		"F": float,               ## float
		"B": bool,                ## boolean (logical)
		"D": datetime.date,       ## date
		"T": datetime.datetime,   ## datetime
		"N": Decimal,             ## decimal (numeric)
		"L": str,                 ## BLOB
		}

pythonTypes = dict([[v,k] for k,v in daboTypes.iteritems()])
pythonTypes[str] = "C"
pythonTypes[unicode] = "C"
del k, v, Decimal

def getPythonType(daboType):
	"""Given a char type code like "I" or "C", return the associated Python type."""
	return daboTypes.get(daboType, None)

def getDaboType(pythonType):
	"""Given a python data type, return the associated Dabo type code."""
	return pythonTypes.get(pythonType, "?")
