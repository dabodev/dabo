""" dabo.db.backend.py : abstractions for the various db api's """
import dabo.common

class dBackend(dabo.common.dObject):
	""" Abstract object: inherit from this to define new dabo db interfaces.
	"""
	def __init__(self):
		self._baseClass = dBackend
		dBackend.doDefault(self)
		self.dbModuleName = None

	def isValidModule(self):
		""" Test the dbapi to see if it is supported on this computer. 
		"""
		try:
			exec("import %s as dbapi" % self.dbModuleName)
			return True
		except ImportError:
			return False

	def getConnection(self, connectInfo):
		""" override in subclasses """
		return None        

	def getDictCursor(self):
		""" override in subclasses """
		return None
	
	def formatDateTime(self, val):
		""" Properly format a datetime value to be included in an Update
		or Insert statement. Each backend can have different requirements
		for formatting dates, so this is where you encapsulate these rules
		in backend-specific subclasses. If nothing special needs to be done,
		the default is to return the original value.
		"""
		return val
	
	def getLastInsertID(self, cursor):
		""" When inserting a new record in a table that auto-generates a PK
		value, different databases have their own way of retrieving that value.
		This method should be coded in backend-specific subclasses to address
		that database's approach.
		"""
		return None

	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		pass
		
	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		pass
		
	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		pass
		