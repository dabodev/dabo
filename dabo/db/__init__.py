# -*- coding: utf-8 -*-
"""
dabo.db is the lowest tier, db access.

This is where the communication to and from the backend database happens, and
cursors get generated to be manipulated by the bizobj's in dabo.biz.

dabo.biz.dBiz is the entity that will interact with this dabo.db stuff, but you
can also work with dabo.db directly if you want. Perhaps you just want to read
some rows from a backend database in a script. Here's an example of that::

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
from decimal import Decimal
from dConnection import dConnection
from dCursorMixin import dCursorMixin
from dConnectInfo import dConnectInfo
from dTable import dTable
from dDataSet import dDataSet
import dabo
from dabo.dException import FieldNotFoundException

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
		"L": buffer,              ## BLOB
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

def getDataType(pythonType):
	"""
	Given a python data type, returns the appropriate type for database values.
	This is generally the same as the original, except when the value is float and
	the Decimal type is available.
	"""
	ret = pythonType
	if pythonType is float and dabo.convertFloatToDecimal:
		ret = daboTypes["N"]
	return ret

def connect(*args, **kwargs):
	"""
	Convenience method: given connection info, return a dConnection instance.

	Passed connection info can either be in the form of a dConnectInfo object,
	or individual arguments to pass to dConnection's constructor.
	"""
	if args == (":memory:",) and not kwargs:
		# special case:
		kwargs["DbType"] = "SQLite"
		kwargs["Database"] = ":memory:"
		args = ()
	return dConnection(*args, **kwargs)


def _getRecord(self_):
	### Used by dCursorMixin *and* dBizobj.
	class CursorRecord(object):
		def __init__(self, _cursor):
			self._cursor = _cursor
			super(CursorRecord, self).__init__()

		def __getattr__(self, att):
			return self._cursor.getFieldVal(att)

		def __setattr__(self, att, val):
			if att in ("_cursor"):
				super(CursorRecord, self).__setattr__(att, val)
			else:
				self._cursor.setFieldVal(att, val)

		def __getitem__(self, key):
			try:
				val = self.__getattr__(key)
			except FieldNotFoundException:
				# __getitem__ added for a dict key-like interface, so convert
				# the FieldNotFoundException to KeyError.
				raise KeyError, key
			return val

		def __setitem__(self, key, val):
			try:
				return self.__setattr__(key, val)
			except FieldNotFoundException:
				# see comment in __getitem__
				raise KeyError, key

	## The rest of this block adds a property to the Record object
	## for each field, the sole purpose being to have the field
	## names appear in the command window intellisense dropdown.
	def getFieldProp(field_name):
		def fget(self_):
			return self_._cursor.getFieldVal(field_name)
		def fset(self_, val):
			self_._cursor.setFieldVal(field_name, val)
		return property(fget, fset)

	field_aliases = [ds[0] for ds in self_.DataStructure]
	field_aliases.extend(self_.VirtualFields.keys())
	for field_alias in field_aliases:
		setattr(CursorRecord, field_alias, getFieldProp(field_alias))
	return CursorRecord(self_)


