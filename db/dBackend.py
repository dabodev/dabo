""" dabo.db.backend.py : abstractions for the various db api's """
import dabo.common

class dBackend(dabo.common.dObject):
	""" Abstract object: inherit from this to define new dabo db interfaces.
	"""
	def __init__(self):
		self._baseClass = dBackend
		dBackend.doDefault(self)
		self.dbModuleName = None
		self._connection = None

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

	def getDictCursorClass(self):
		""" override in subclasses """
		return None
	
	def getCursor(self, cursorClass):
		""" override in subclasses if necessary """
		return cursorClass(self._connection)
	
	def formatDateTime(self, val):
		""" Properly format a datetime value to be included in an Update
		or Insert statement. Each backend can have different requirements
		for formatting dates, so this is where you encapsulate these rules
		in backend-specific subclasses. If nothing special needs to be done,
		the default is to return the original value.
		"""
		return val
	
	def getLastInsertID(self, cursor):
		""" Return the ID of the last inserted row, or None.
		
		When inserting a new record in a table that auto-generates a PK
		value, different databases have their own way of retrieving that value.
		This method should be coded in backend-specific subclasses to address
		that database's approach.
		"""
		
		# Here is some code to fall back on if the specific subclass doesn't 
		# override.
		try:
			# According to PEP-0249, it is common practice for a readonly 
			# lastrowid attribute to be added by module authors, which will
			# keep the last-insert id. This is by no means guaranteed, though.
			# I've confirmed that it does work for MySQLdb.
			return cursor.lastrowid
		except AttributeError:
			return None

	def getTables(self, includeSystemTables=False):
		""" Return a tuple of the tables in the current database.
		
		Different backends will do this differently, so override in subclasses.
		"""
		return tuple()
		
	def getTableRecordCount(self, tableName):
		""" Return the number of records in the backend table.
		"""
		return -1
	
	def getFields(self, tableName):
		""" Return field information from the backend table.
		
		See dCursorMixin.getFields() for a description of the return value.			
		"""
		# It is too bad, but dbapi2.0's cursor().description doesn't cut it.
		# It will give the field names, but the type info and pk info isn't
		# adequate generically yet.
		return ()
		
	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		pass
		
	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		pass
		
	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		pass
		
