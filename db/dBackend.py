""" dabo.db.backend.py : abstractions for the various db api's """
import sys
import re
import datetime
import dabo
from dabo.dLocalize import _
import dabo.dException as dException
from dabo.dObject import dObject
from dabo.db import dTable
from dabo.db import dNoEscQuoteStr
try:
	import decimal
except ImportError:
	decimal = None



class dBackend(dObject):
	""" Abstract object: inherit from this to define new dabo db interfaces."""

	# Pattern for determining if a function is present in a string
	functionPat = re.compile(r".*\([^\)]+\)")
	# When enclosing table or field names that contain spaces, what
	# character is used? Default to double quote.
	spaceEnclosureChar = '"'

	def __init__(self):
		self._baseClass = dBackend
		self._autoCommit = False
		# This forces the setting on the connection
		self.AutoCommit = False
		super(dBackend, self).__init__()
		self.dbModuleName = None
		self._connection = None
		if self.Application:
			self._encoding = self.Application.Encoding
		else:
			self._encoding = dabo.defaultEncoding


	def isValidModule(self):
		""" Test the dbapi to see if it is supported on this computer."""
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


	def formatForQuery(self, val):
		if isinstance(val, (datetime.date, datetime.datetime)):
			# Some databases have specific rules for formatting date values.
			return self.formatDateTime(val)
		elif isinstance(val, (int, long, float)):
			return str(val)
		elif decimal is not None and isinstance(val, decimal.Decimal):
			return str(val)
		elif isinstance(val, dNoEscQuoteStr):
			return val
		elif val is None:
			return self.formatNone()
		else:
			return self.escQuote(val)


	def formatDateTime(self, val):
		""" Properly format a datetime value to be included in an Update
		or Insert statement. Each backend can have different requirements
		for formatting dates, so this is where you encapsulate these rules
		in backend-specific subclasses. If nothing special needs to be done,
		the default is to return the original value.
		"""
		return val


	def formatNone(self):
		""" Properly format a None value to be included in an update statement.

		Each backend should override as needed. The default is to return "NULL".
		"""
		return "NULL"


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
		""" Return the number of records in the backend table."""
		return -1


	def getFields(self, tableName):
		""" Return field information from the backend table.

		See dCursorMixin.getFields() for a description of the return value.
		"""
		# It is too bad, but dbapi2.0's cursor().description doesn't cut it.
		# It will give the field names, but the type info and pk info isn't
		# adequate generically yet.
		return ()


	def getDaboFieldType(self, backendFieldType):
		""" Return the Dabo code (I, T, D, ...) for the passed backend Field Type.

		If it can't be determined, the field type will be '?'.
		"""
		return "?"


	def getFieldInfoFromDescription(self, cursorDescription):
		""" Return field information from the cursor description."""
		# Default: return all the field names and "?", None for type and pkid.
		return tuple([(d[0], self.getDaboFieldType(d[1]), None) for d in cursorDescription])


	def getAutoCommitStatus(self, cursor):
		return self._autoCommit


	def setAutoCommitStatus(self, cursor, val):
		if hasattr(self._connection, "autocommit"):
			self._connection.autocommit(val)
			self._autoCommit = val
		else:
			# Without an autocommit method, assume no autocommit.
			self._autoCommit = False
			if val:
				raise ValueError, "Can't set AutoCommit to True for this backend."


	def beginTransaction(self, cursor):
		""" Begin a SQL transaction. Override in subclasses if needed."""
		pass


	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		if not cursor.AutoCommit:
			self._connection.commit()


	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		self._connection.rollback()


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


	def encloseSpaces(self, exp):
		"""When table/field names contain spaces, this will safely enclose them
		in quotes or whatever delimiter is appropriate for the backend.
		"""
		ret = exp
		if " " in exp:
			delim = self.spaceEnclosureChar
			if not ret.startswith(delim):
				ret = "%(delim)s%(ret)s" % locals()
			if not ret.endswith(delim):
				ret = "%(ret)s%(delim)s" % locals()
		return ret
	
	
	def addField(self, clause, exp, alias=None):
		""" Add a field to the field clause."""
		if alias is None:
			# Backwards compatibility: see if the 'as' clause is present
			asPos = exp.lower().find(" as ")
			if asPos > -1:
				alias = exp[asPos+4:]
				exp = exp[:asPos]	
		# If exp is a function, don't do anything special about spaces.
		if not self.functionPat.match(exp):
			# See if it's in tbl.field format
			try:
				tbl, fld = exp.strip().split(".")
				exp = "%s.%s" % (self.encloseSpaces(tbl), self.encloseSpaces(fld))
			except ValueError:
				exp = self.encloseSpaces(exp)
		if alias:
			alias = self.encloseSpaces(alias)
			exp = "%(exp)s as %(alias)s" % locals()
		indent = len("select ") * " "
		# Give the backend-specific code a chance to update the format
		exp = self.processFields(exp)
		return self.addWithSep(clause, exp, sep=",\n%s" % indent)

	
	def addFrom(self, clause, exp):
		""" Add a table to the sql statement."""
		exp = self.encloseSpaces(exp)
		indent = len("select ") * " "
		return self.addWithSep(clause, exp, sep=",\n%s" % indent)
	
	
	def addJoin(self, tbl, joinCondition, exp, joinType=None):
		""" Add a joined table to the sql statement."""
		tbl = self.encloseSpaces(tbl)
		joinType = self.formatJoinType(joinType)
		indent = len("select ") * " "
		clause = "%(joinType)s join %(tbl)s on %(joinCondition)s" % locals()
		return self.addWithSep(clause, exp, sep="\n%s" % indent)


	def addWhere(self, clause, exp, comp="and"):
		""" Add an expression to the where clause."""
		indent = (len("select ") - len(comp)) * " "
		exp = self.processFields(exp)
		return self.addWithSep(clause, exp, sep="\n%s%s " % (indent, comp))


	def addGroupBy(self, clause, exp):
		""" Add an expression to the group-by clause."""
		exp = self.encloseSpaces(exp)
		indent = len("select ") * " "
		return self.addWithSep(clause, exp, sep=",\n%s" % indent)


	def addOrderBy(self, clause, exp):
		""" Add an expression to the order-by clause."""
		exp = self.encloseSpaces(exp)
		indent = len("select ") * " "
		return self.addWithSep(clause, exp, sep=",\n%s" % indent)


	def getLimitWord(self):
		""" Return the word to use in the db-specific limit clause.
		Override for backends that don't use the word 'limit'
		"""
		return "limit"


	def formSQL(self, fieldClause, fromClause, joinClause,
				whereClause, groupByClause, orderByClause, limitClause):
		""" Creates the appropriate SQL for the backend, given all
		the required clauses. Some backends order these differently, so
		they should override this method with their own ordering.
		"""
		clauses =  (fieldClause, fromClause, joinClause, whereClause, groupByClause,
				orderByClause, limitClause)
		sql = "select " + "\n".join( [clause for clause in clauses if clause] )
		return sql


	def prepareWhere(self, clause):
		""" Normally, just return the original. Can be overridden as needed
		for specific backends.
		"""
		return clause
	
	
	def formatJoinType(self, jt):
		"""Default formatting for jointype keywords. Override in subclasses if needed."""
		if jt is None:
			jt = "inner"
		else:
			# Default to trimmed lower-case
			jt = jt.lower().strip()
		return jt


	def getWordMatchFormat(self):
		""" By default, will return the standard format for an
		equality test. If search by words is available, the format
		must be implemented in each specific backend.

		The format must have the expressions %(table)s, %(field)s,
		and %(value)s, which will be replaced with the table, field,
		and value strings, respectively.
		"""
		return " %(table)s.%(field)s = %(value)s "


	def getUpdateTablePrefix(self, tbl):
		""" By default, the update SQL statement will be in the form of
					tablename.fieldname
		but some backends do no accept this syntax. If not, change
		this method to return an empty string, or whatever should
		preceed the field name in an update statement.
		"""
		tbl = self.encloseSpaces(tbl)
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
		tbl = self.encloseSpaces(tbl)
		return tbl + "."


	def massageDescription(self, cursor):
		"""Some dbapi programs do strange things to the description.
		In particular, kinterbasdb forces the field names to upper case
		if the field statement in the SQL that was executed contains an
		'as' expression.

		This is called after every execute() by the cursor, since the
		description field is updated each time. By default, we simply
		copy it to the 'descriptionClean' attribute.
		"""
		cursor.descriptionClean = cursor.description


	def getDescription(self, cursor):
		"""Normally, cursors should always be able to report their
		description properly. However, some backends such as
		SQLite will not report a description if there is no data in the
		record set. This method provides a way for those backends
		to deal with this. By default, though, just return the contents
		of the description attribute.
		"""
		if cursor.descriptionClean is None:
			return ()
		else:
			return cursor.descriptionClean


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
		sql = "select * from %s where 1=0 " % self.encloseSpaces(cursor.Table)
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
		"""Return the basic field structure."""
		field_structure = {}
		field_names = []

		field_description = cursor.FieldDescription
		if not field_description:
			# No query run yet: execute the structure-only sql:
			structure_only_sql = cursor.getStructureOnlySql()
			aux = cursor.AuxCursor
			aux.execute(structure_only_sql)
			field_description = aux.FieldDescription

		for field_info in field_description:
			field_name = field_info[0]
			field_type = self.getDaboFieldType(field_info[1])
			field_names.append(field_name)
			field_structure[field_name] = (field_type, False)

		standard_fields = cursor.getFields()
		for field_name, field_type, pk in standard_fields:
			if field_name in field_names or not field_names:
				# We only use the info for the standard field in one of two cases:
				#   1) There aren't any fields in the FieldDescription, which would be
				#      the case if we haven't set the SQL or requeried yet.
				#   2) The field exists in the FieldDescription, and FieldDescription
				#      didn't provide good type information.
				if field_structure[field_name][0] == "?":
					# Only override what was in FieldStructure if getFields() gave better info.
					field_structure[field_name] = (field_type, pk)
				if pk is True:
					# FieldStructure doesn't provide pk information:
					field_structure[field_name] = (field_structure[field_name][0], pk)

		ret = []
		for field in field_names:
			ret.append( (field, field_structure[field][0], field_structure[field][1]) )
		return tuple(ret)
		

	##########		Created by Echo 	##############
	def isExistingTable(self, table):
		"""Returns whether or not the table exists."""
		if isinstance(table, dTable):
			return self._isExistingTable(table.name)
		else:
			return self._isExistingTable(table)


	def _isExistingTable(self, tablename):
		# OVERRIDE IN SUBCLASSES!
		return False


	def createJustTable(self, tabledef, cursor):
		self.createTableAndIndex(tabledef, cursor, createIndexes=False)


	def createJustIndexes(self, tabledef, cursor):
		self.createTableAndIndexes(tabledef, cursor, createTable=False)


	def createTableAndIndexes(self, tabledef, cursor, createTable=True,
			createIndex=True):
		"""Creates a table and/or indexes based on the dTable passed to it."""
		# OVERRIDE IN SUBCLASSES!
		pass
	##########		END  - Created by Echo 	##############


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
	def setJoinClause(self, clause):
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


	Encoding = property(_getEncoding, _setEncoding, None,
			_("Backend encoding  (str)"))
