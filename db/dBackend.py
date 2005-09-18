""" dabo.db.backend.py : abstractions for the various db api's """
import sys
from dabo.dLocalize import _
import dabo.dException as dException
import dabo.common

class dBackend(dabo.common.dObject):
	""" Abstract object: inherit from this to define new dabo db interfaces.
	"""
	def __init__(self):
		self._baseClass = dBackend
		#dBackend.doDefault(self)
		super(dBackend, self).__init__()
		self.dbModuleName = None
		self._connection = None
#		sysenc = sys.getdefaultencoding()
#		self._encoding = sysenc == 'ascii' and 'latin-1' or sysenc
		self._encoding = "utf-8"

	def isValidModule(self):
		""" Test the dbapi to see if it is supported on this computer. 
		"""
		try:
			dbapi = __import__(self.dbModuleName)
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
	
	def noResultsOnSave(self):
		""" Most backends will return a non-zero number if there are updates.
		Some do not, so this will have to be customized in those cases.
		"""
		raise dException.dException, _("No records updated")

	def noResultsOnDelete(self):
		""" Most backends will return a non-zero number if there are deletions.
		Some do not, so this will have to be customized in those cases.
		"""
		raise dException.dException, _("No records deleted")
		
	def flush(self, cursor):
		""" Only used in some backends """
		return

	def processFields(self, txt):
		""" Default is to return the string unchanged. Override
		in cases where the str needs processing.
		"""
		return txt


	def escQuote(self, val):
		""" Escape special characters in SQL strings.

		Escapes any single quotes that could cause SQL syntax errors, as well 
		as any other characters which have special meanings with the backend
		database's engine.
		"""
		# OVERRIDE IN SUBCLASSES!
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
		try:
			cursor.connection.begin()
		except:
			# Should we raise an error?
			pass
		
	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		try:
			cursor.connection.commit()
		except:
			# Should we raise an error?
			pass
		
	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		try:
			cursor.connection.rollback()
		except:
			# Should we raise an error?
			pass
		
	def addWithSep(self, base, new, sep=",\n\t"):
		""" Convenient method of adding to an expression that 
		may or may not have an existing value. If there is a value, 
		the separator is inserted between the two.
		"""
		if base:
			ret = sep.join( (base, new) )
		else:
			ret = new
		return ret
		
	def addField(self, clause, exp):
		""" Add a field to the field clause.
		"""
		return self.addWithSep(clause, exp)

	def addFrom(self, clause, exp):
		""" Add a table to the sql statement.
		"""
		return self.addWithSep(clause, exp)

	def addWhere(self, clause, exp, comp="and"):
		""" Add an expression to the where clause.
		"""
		return self.addWithSep(clause, exp, sep=" %s " % comp)

	def addGroupBy(self, clause, exp):
		""" Add an expression to the group-by clause.
		"""
		return self.addWithSep(clause, exp)

	def addOrderBy(self, clause, exp):
		""" Add an expression to the order-by clause.
		"""
		return self.addWithSep(clause, exp)
		
	def getLimitWord(self):
		""" Return the word to use in the db-specific limit clause.
		Override for backends that don't use the word 'limit'
		"""
		return "limit"
	
	def formSQL(self, fieldClause, fromClause, 
				whereClause, groupByClause, orderByClause, limitClause):
		""" Creates the appropriate SQL for the backend, given all 
		the required clauses. Some backends order these differently, so 
		they should override this method with their own ordering.
		"""
		clauses =  (fieldClause, fromClause, whereClause, groupByClause,
				orderByClause, limitClause)
		sql = "select " + "\n".join( [clause for clause in clauses if clause] )
		return sql

	def prepareWhere(self, clause):
		""" Normally, just return the original. Can be overridden as needed
		for specific backends.
		"""
		return clause
		
	def getWordMatchFormat(self):
		""" By default, will return the standard format for an 
		equality test. If search by words is available, the format
		must be implemented in each specific backend.
		
		The format must have the expressions %(field)s and %(value)s
		which will be replaced with the field and value strings, 
		respectively.
		"""
		return " %(field)s = %(value)s "

	def getUpdateTablePrefix(self, tbl):
		""" By default, the update SQL statement will be in the form of
					tablename.fieldname
		but some backends do no accept this syntax. If not, change
		this method to return an empty string, or whatever should 
		preceed the field name in an update statement.
		"""
		return tbl + "."
	
	
	def getWhereTablePrefix(self, tbl):
		""" By default, the comparisons in the WHERE clauses of
		SQL statements will be in the form of
					tablename.fieldname
		but some backends do no accept this syntax. If not, change
		this method to return an empty string, or whatever should 
		preceed the field name in a comparison in the WHERE clause
		of an SQL statement.
		"""
		return tbl + "."
	
	
	def massageDescription(self, cursor):
		"""Some dbapi programs do strange things to the description.
		In particular, kinterbasdb forces the field names to upper case 
		if the field statement in the SQL that was executed contains an 
		'as' expression. 
		
		This is called after every execute() by the cursor, since the 
		description field is updated each time. By default, we do 
		nothing to the description.
		"""
		return
	
	
	def  getDescription(self, cursor):
		"""Normally, cursors should always be able to report their
		description properly. However, some backends such as 
		SQLite will not report a description if there is no data in the
		record set. This method provides a way for those backends
		to deal with this. By default, though, just return the contents
		of the description attribute.
		"""
		if cursor.description is None:
			return ()
		else:
			return cursor.description

	
	def pregenPK(self, cursor):
		"""In the case where the database requires that PKs be generated 
		before an insert, this method provides a backend-specific 
		means of accomplishing this. By default, we return None.
		"""
		return None
	
	
	def setNonUpdateFields(self, cursor):
		"""Normally, this routine should work for all backends. But
		in the case of SQLite, the routine that grabs an empty cursor
		doesn't fill in the description, so that backend has to use
		an alternative approach.
		"""
		if not cursor.Table:
			# No table specified, so no update checking is possible
			return
		# This is the current description of the cursor.
		if not cursor.FieldDescription:
			# A query hasn't been run yet; so we need to get one
			holdWhere = cursor._whereClause
			cursor.addWhere("1 = 0")
			cursor.execute(cursor.getSQL())
			cursor._whereClause = holdWhere
		descFlds = cursor.FieldDescription
		# Get the raw version of the table
		sql = """select * from %s where 1=0 """ % cursor.Table
		auxCrs = cursor._getAuxCursor()
		auxCrs.execute( sql )
		# This is the clean version of the table.
		stdFlds = auxCrs.FieldDescription

		# Get all the fields that are not in the table.
		cursor.__nonUpdateFields = [d[0] for d in descFlds 
				if d[0] not in [s[0] for s in stdFlds] ]
		# Extract the remaining fields (no need to test any already excluded
		remFlds = [ d for d in descFlds if d[0] not in cursor.__nonUpdateFields ]
		
		# Now add any for which the members (except the display value, 
		# which is in position 2) do not match
		cursor.__nonUpdateFields += [ b[0] for b in remFlds 
				for s in [z for z in stdFlds if z[0] == b[0] ]
				if (b[1] != s[1]) or (b[3] != s[3]) or (b[4] != s[4]) 
				or (b[5] != s[5]) or (b[6] != s[6]) ]
		
		
	def getStructureDescription(self, cursor):
		"""This will work for most backends. However, SQLite doesn't
		properly return the structure when no records are returned.
		"""
		#Try using the no-records version of the SQL statement. 
		try:
			tmpsql = cursor.getStructureOnlySql()
		except AttributeError:
			# We need to parse the sql property to get what we need.
			import re
			pat = re.compile("(\s*select\s*.*\s*from\s*.*\s*)((?:where\s(.*))+)\s*", re.I | re.M | re.S)
			if pat.search(cursor.sql):
				# There is a WHERE clause. Add the NODATA clause
				tmpsql = pat.sub("\\1 where 1=0 ", cursor.sql)
			else:
				# no WHERE clause. See if it has GROUP BY or ORDER BY clauses
				pat = re.compile("(\s*select\s*.*\s*from\s*.*\s*)((?:group\s*by\s(.*))+)\s*", re.I | re.M | re.S)
				if pat.search(cursor.sql):
					tmpsql = pat.sub("\\1 where 1=0 ", cursor.sql)
				else:               
					pat = re.compile("(\s*select\s*.*\s*from\s*.*\s*)((?:order\s*by\s(.*))+)\s*", re.I | re.M | re.S)
					if pat.search(cursor.sql):
						tmpsql = pat.sub("\\1 where 1=0 ", cursor.sql)
					else:               
						# Nothing. So just tack it on the end.
						tmpsql = cursor.sql + " where 1=0 "
		auxCrs = cursor._getAuxCursor()
		auxCrs.execute(tmpsql)
		return auxCrs.FieldDescription
	
	
	###########################################	
	# The following methods by default simply return the text 
	# supplied to them. If a particular backend (Firebird comes
	# to mind) has specific formatting requirements, though, 
	# that subclass should override these.
	def setSQL(self, sql):
		return sql
	def setFieldClause(self, clause):
		return clause
	def setFromClause(self, clause):
		return clause
	def setWhereClause(self, clause):
		return clause
	def setChildFilterClause(self, clause):
		return clause
	def setGroupByClause(self, clause):
		return clause
	def setOrderByClause(self, clause):
		return clause
	###########################################	

	def _setEncoding(self, enc):
		""" Set backend encoding. Must be overridden in the subclass
		to notify database about proper charset conversion.
		"""
		self._encoding = enc
	def _getEncoding(self):
		""" Get backend encoding."""
		return self._encoding

	Encoding = property(_getEncoding, _setEncoding, None, "Backend encoding")
