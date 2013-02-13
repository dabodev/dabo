# -*- coding: utf-8 -*-
import sys
import time
import re
import datetime
import threading
import decimal
import dabo
from dabo.dLocalize import _
import dabo.dException as dException
from dabo.dObject import dObject
from dabo.db import dTable
from dNoEscQuoteStr import dNoEscQuoteStr
from dabo.lib.utils import ustr
from dCursorMixin import dCursorMixin


class dBackend(dObject):
	"""Abstract class inherited by the specific Dabo database connectors."""
	# Pattern for determining if a function is present in a string
	functionPat = re.compile(r".*\([^\)]+\)")
	# When enclosing table or field names that contain spaces, what
	# character is used? Default to double quote.
	nameEnclosureChar = '"'
	# The character used in sql to represent parameters to be substituted
	paramPlaceholder = "%s"

	def __init__(self):
		self._baseClass = dBackend
		super(dBackend, self).__init__()
		self.dbModuleName = None
		self._connection = None
		# Reference to the cursor that is using this object
		self._cursor = None
		self.lastExecuteTime = time.time() # For keep alive interval


	def isValidModule(self):
		"""Test the dbapi to see if it is supported on this computer."""
		try:
			dbapi = __import__(self.dbModuleName)
			return True
		except ImportError:
			return False


	def getConnection(self, connectInfo, **kwargs):
		"""override in subclasses"""
		return None


	def getDictCursorClass(self):
		"""override in subclasses"""
		return None

	def getMainCursorClass(self):
		"""override in subclasses if they need something other than dCursorMixin"""
		return dCursorMixin


	def getCursor(self, cursorClass):
		"""override in subclasses if necessary"""
		return cursorClass(self._connection)


	def formatForQuery(self, val, fieldType=None):
		if isinstance(val, (datetime.date, datetime.datetime)):
			# Some databases have specific rules for formatting date values.
			return self.formatDateTime(val)
		elif isinstance(val, (int, long, float)):
			return ustr(val)
		elif isinstance(val, decimal.Decimal):
			return ustr(val)
		elif isinstance(val, dNoEscQuoteStr):
			return val
		elif fieldType == "L":
			return val
		elif val is None:
			return self.formatNone()
		else:
			return self.escQuote(val)


	def formatBLOB(self, val):
		"""
		Properly format a BLOB value to be included in an UPDATE
		or INSERT statement for a specific backend.
		"""
		return val


	def formatDateTime(self, val):
		"""
		Properly format a datetime value to be included in an UPDATE
		or INSERT statement. Each backend can have different requirements
		for formatting dates, so this is where you encapsulate these rules
		in backend-specific subclasses. If nothing special needs to be done,
		the default is to return the original value.
		"""
		return val


	def formatNone(self):
		"""
		Properly format a None value to be included in an update statement.

		Each backend should override as needed. The default is to return "NULL".
		"""
		return "NULL"


	def noResultsOnSave(self):
		"""
		Most backends will return a non-zero number if there are updates.
		Some do not, so this will have to be customized in those cases.
		"""
		raise dException.dException(_("No records updated"))


	def noResultsOnDelete(self):
		"""
		Most backends will return a non-zero number if there are deletions.
		Some do not, so this will have to be customized in those cases.
		"""
		raise dException.dException(_("No records deleted"))


	def flush(self, cursor):
		"""Only used in some backends"""
		return


	def processFields(self, txt):
		"""
		Default is to return the string unchanged. Override
		in cases where the str needs processing.
		"""
		return txt


	def escQuote(self, val):
		"""
		Escape special characters in SQL strings.

		Escapes any single quotes that could cause SQL syntax errors, as well
		as any other characters which have special meanings with the backend
		database's engine.
		"""
		# OVERRIDE IN SUBCLASSES!
		return val


	def getLastInsertID(self, cursor):
		"""
		Return the ID of the last inserted row, or None.

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


	def getTables(self, cursor, includeSystemTables=False):
		"""
		Return a tuple of the tables in the current database.

		Different backends will do this differently, so override in subclasses.
		"""
		return tuple()


	def getTableRecordCount(self, tableName, cursor):
		"""Return the number of records in the backend table."""
		return -1


	def getFields(self, tableName, cursor):
		"""
		Return field information from the backend table.

		See dCursorMixin.getFields() for a description of the return value.
		"""
		# It is too bad, but dbapi2.0's cursor().description doesn't cut it.
		# It will give the field names, but the type info and pk info isn't
		# adequate generically yet.
		return ()


	def getDaboFieldType(self, backendFieldType):
		"""
		Return the Dabo code (I, T, D, ...) for the passed backend Field Type.

		If it can't be determined, the field type will be '?'.
		"""
		return {int: "I", str: "C", float: "F"}.get(backendFieldType, "?")


	def getFieldInfoFromDescription(self, cursorDescription):
		"""Return field information from the cursor description."""
		# Default: return all the field names and "?", None for type and pkid.
		return tuple([(d[0], self.getDaboFieldType(d[1]), None) for d in cursorDescription])


	def beginTransaction(self, cursor):
		"""Begin a SQL transaction. Override in subclasses if needed."""
		self._connection.begin()
		dabo.dbActivityLog.info("SQL: begin")
		return True


	def commitTransaction(self, cursor):
		"""Commit a SQL transaction."""
		self._connection.commit()
		dabo.dbActivityLog.info("SQL: commit")
		return True


	def rollbackTransaction(self, cursor):
		"""Roll back (revert) a SQL transaction."""
		self._connection.rollback()
		dabo.dbActivityLog.info("SQL: rollback")
		return True


	@staticmethod
	def addWithSep(base, new, sep=",\n\t"):
		"""
		Convenient method of adding to an expression that
		may or may not have an existing value. If there is a value,
		the separator is inserted between the two.
		"""
		if base:
			if new not in base.split(sep):
				return sep.join((base, new))
		else:
			return new
		return base

	@staticmethod
	def removeWithSep(base, remove, sep=",\n\t"):
		"""
		Convenient method of removing an expression that
		may or may not have an existing value.
		"""
		splitbase = base.split(sep)
		try:
			idx = splitbase.index(remove)
		except ValueError:
			return base
		del(splitbase[idx])
		return sep.join(splitbase)

	def encloseNames(self, exp, autoQuote=True, keywords=None):
		"""
		When table/field names contain spaces, this will safely enclose them
		in quotes or whatever delimiter is appropriate for the backend, unless
		autoQuote is False, in which case it leaves things untouched. If there are
		keywords that are part of the expression that should not be enclosed
		within the field name, pass them as a tuple to the keywords parameter.
		"""
		if autoQuote:
			if keywords is None:
				parts = [exp]
				subs = lowkeys = tuple()
			else:
				# First separate any keywords: e.g., 'foo as bar'.
				pat = re.compile(r"(\b%s\b)" % r"\b|\b".join(keywords), re.I)
				parts = pat.split(exp)
				subs = tuple(pat.findall(exp))
				lowkeys = [k.lower() for k in keywords]
			delim = self.nameEnclosureChar
			def encPart(part):
				qtd = [delim + pt.strip() + delim for pt in part.split(".") if pt]
				return ".".join(qtd)
			exp = " %s ".join([encPart(pt) for pt in parts
					if pt.lower() not in lowkeys])
			return exp % subs
		return exp


	def addField(self, clause, exp, alias=None, autoQuote=True):
		"""Add a field to the field clause."""
		indent, exp = self._getFieldAddRemoveExp(exp, alias, autoQuote)
		return self.addWithSep(clause, exp, sep=",\n%s" % indent)

	def removeField(self, clause, exp, alias=None, autoQuote=True):
		"""Remove a previously added field from the field clause."""
		indent, exp = self._getFieldAddRemoveExp(exp, alias, autoQuote)
		return self.removeWithSep(clause, exp, sep=",\n%s" % indent)

	def _getFieldAddRemoveExp(self, exp, alias, autoQuote):
		indent = len("select ") * " "
		# If exp is a function, don't do anything special about spaces.
		if not self.functionPat.match(exp):
			exp = self.encloseNames(exp, autoQuote=autoQuote, keywords=("as",))
		if alias:
			alias = self.encloseNames(alias, autoQuote=autoQuote, keywords=("as",))
			exp = "%(exp)s as %(alias)s" % locals()
		# Give the backend-specific code a chance to update the format
		exp = self.processFields(exp)
		return indent, exp

	def addFrom(self, clause, exp, alias=None, autoQuote=True):
		"""Add a table to the sql statement."""
		exp = self.encloseNames(exp, autoQuote=autoQuote, keywords=("as",))
		if alias:
			exp = "%(exp)s as %(alias)s" % locals()
		indent = len("select ") * " "
		return self.addWithSep(clause, exp, sep=",\n%s" % indent)


	def addJoin(self, tbl, joinCondition, exp, joinType=None, autoQuote=True):
		"""Add a joined table to the sql statement."""
		tbl = self.encloseNames(tbl, autoQuote=autoQuote, keywords=("as",))
		joinType = self.formatJoinType(joinType)
		indent = len("select ") * " "
		clause = "%(joinType)s join %(tbl)s on %(joinCondition)s" % locals()
		return self.addWithSep(exp, clause, sep="\n%s" % indent)


	def addWhere(self, clause, exp, comp="and", autoQuote=True):
		"""Add an expression to the where clause."""
		indent = (len("select ") - len(comp)) * " "
		exp = self.processFields(exp)
		return self.addWithSep(clause, exp, sep="\n%s%s " % (indent, comp))


	def removeWhere(self, clause, exp, comp="and", autoQuote=True):
		"""Remove a previously-added expression from the where clause."""
		indent = (len("select ") - len(comp)) * " "
		exp = self.processFields(exp)
		return self.removeWithSep(clause, exp, sep="\n%s%s " % (indent, comp))


	def addGroupBy(self, clause, exp, autoQuote=True):
		"""Add an expression to the group-by clause."""
		exp = self.encloseNames(exp, autoQuote=autoQuote)
		indent = len("select ") * " "
		return self.addWithSep(clause, exp, sep=",\n%s" % indent)


	def addOrderBy(self, clause, exp, autoQuote=True):
		"""Add an expression to the order-by clause."""
		exp = self.encloseNames(exp, autoQuote=autoQuote, keywords=("asc", "desc"))
		indent = len("select ") * " "
		return self.addWithSep(clause, exp, sep=",\n%s" % indent)


	def getLimitWord(self):
		"""
		Return the word to use in the db-specific limit clause.
		Override for backends that don't use the word 'limit'
		"""
		return "limit"


	def formSQL(self, fieldClause, fromClause, joinClause,
				whereClause, groupByClause, orderByClause, limitClause):
		"""
		Creates the appropriate SQL for the backend, given all
		the required clauses. Some backends order these differently, so
		they should override this method with their own ordering.
		"""
		clauses =  (fieldClause, fromClause, joinClause, whereClause, groupByClause,
				orderByClause, limitClause)
		sql = "select " + "\n".join([clause for clause in clauses if clause])
		return sql


	def prepareWhere(self, clause, autoQuote=True):
		"""
		Normally, just return the original. Can be overridden as needed
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
		"""
		By default, will return the standard format for an
		equality test. If search by words is available, the format
		must be implemented in each specific backend.

		The format must have the expressions %(table)s, %(field)s,
		and %(value)s, which will be replaced with the table, field,
		and value strings, respectively.
		"""
		return " %(table)s.%(field)s = %(value)s "


	def getUpdateTablePrefix(self, tbl, autoQuote=True):
		"""
		By default, the update SQL statement will be in the form of

			tablename.fieldname

		but some backends do no accept this syntax. If not, change
		this method to return an empty string, or whatever should
		preceed the field name in an update statement.
		"""
		tbl = self.encloseNames(tbl, autoQuote=autoQuote)
		return tbl + "."


	def getWhereTablePrefix(self, tbl, autoQuote=True):
		"""
		By default, the comparisons in the WHERE clauses of
		SQL statements will be in the form of

			tablename.fieldname

		but some backends do no accept this syntax. If not, change
		this method to return an empty string, or whatever should
		preceed the field name in a comparison in the WHERE clause
		of an SQL statement.
		"""
		tbl = self.encloseNames(tbl, autoQuote=autoQuote)
		return tbl + "."


	def massageDescription(self, cursor):
		"""
		Some dbapi programs do strange things to the description.
		In particular, kinterbasdb forces the field names to upper case
		if the field statement in the SQL that was executed contains an
		'as' expression.

		This is called after every execute() by the cursor, since the
		description field is updated each time. By default, we simply
		copy it to the 'descriptionClean' attribute.
		"""
		cursor.descriptionClean = cursor.description


	def getDescription(self, cursor):
		"""
		Normally, cursors should always be able to report their
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
		"""
		In the case where the database requires that PKs be generated
		before an insert, this method provides a backend-specific
		means of accomplishing this. By default, we return None.
		"""
		return None


	def setNonUpdateFields(self, cursor, autoQuote=True):
		"""
		Normally, this routine should work for all backends. But
		in the case of SQLite, the routine that grabs an empty cursor
		doesn't fill in the description, so that backend has to use
		an alternative approach.
		"""
		if not cursor.Table:
			# No table specified, so no update checking is possible
			return None
		# This is the current description of the cursor.
		auxCrs = cursor._getAuxCursor()
		if not cursor.FieldDescription:
			# A query hasn't been run yet; so we need to get one
			holdWhere = auxCrs._whereClause
			auxCrs.addWhere("1 = 0")
			auxCrs.execute(auxCrs.getSQL())
			auxCrs._whereClause = holdWhere
		descFlds = auxCrs.FieldDescription
		# Get the raw version of the table
		sql = "select * from %s where 1=0 " % self.encloseNames(cursor.Table,
				autoQuote=autoQuote)
		auxCrs.execute(sql)
		# This is the clean version of the table.
		stdFlds = auxCrs.FieldDescription

		# Get all the fields that are not in the table.
		ret0 = [d[0] for d in descFlds
				if d[0] not in [s[0] for s in stdFlds] ]
		# Extract the remaining fields (no need to test any already excluded
		remFlds = [ d for d in descFlds if d[0] not in ret0]

		# Now add any for which the members (except the display value,
		# which is in position 2) do not match
		ret0 += [ b[0] for b in remFlds
				for s in [z for z in stdFlds if z[0] == b[0] ]
				if (b[1] != s[1]) or (b[3] != s[3]) or (b[4] != s[4])
				or (b[5] != s[5]) or (b[6] != s[6]) ]
		return ret0


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
			field_name = ustr(field_info[0])
			field_type = self.getDaboFieldType(field_info[1])
			field_names.append(field_name)
			field_structure[field_name] = (field_type, False,
					max(field_info[2], field_info[3]) or None, field_info[5] or None)

		standard_fields = cursor.getFields()
		for field_name, field_type, pk in standard_fields:
			if field_name in field_names or not field_names:
				# We only use the info for the standard field in one of two cases:
				#   1) There aren't any fields in the FieldDescription, which would be
				#      the case if we haven't set the SQL or requeried yet.
				#   2) The field exists in the FieldDescription, and FieldDescription
				#      didn't provide good type information.
				if field_structure[field_name][0] != field_type:
					# Only override what was in FieldStructure if getFields() gave better info.
					field_structure[field_name] = (field_type, pk,
							field_structure[field_name][2], field_structure[field_name][3])
				elif pk:
					# FieldStructure doesn't provide pk information:
					field_structure[field_name] = (field_structure[field_name][0], pk,
							field_structure[field_name][2], field_structure[field_name][3])

		ret = [(field, field_structure[field][0], field_structure[field][1],
				None, None,
				field_structure[field][2] if field_structure[field][0] == "C"
					else field_structure[field][3])
				for field in field_names]
		return tuple(ret)


	##########		Created by Echo 	##############
	def isExistingTable(self, table):
		"""Returns whether or not the table exists."""
		crs = self._cursor.AuxCursor
		if isinstance(table, dTable):
			return self._isExistingTable(table.name, crs)
		else:
			return self._isExistingTable(table, crs)


	def _isExistingTable(self, tablename, cursor):
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
	def setFieldClause(self, clause, autoQuote=True):
		return clause
	def setFromClause(self, clause, autoQuote=True):
		return clause
	def setJoinClause(self, clause, autoQuote=True):
		return clause
	def setWhereClause(self, clause, autoQuote=True):
		return clause
	def setChildFilterClause(self, clause, autoQuote=True):
		return clause
	def setGroupByClause(self, clause, autoQuote=True):
		return clause
	def setOrderByClause(self, clause, autoQuote=True):
		return clause
	###########################################

	def _applyKeepAlive(self):
		"""Start a thread to keep the connection alive."""

		class WorkerThread(threading.Thread):
			def __init__(self, backendObj):
				threading.Thread.__init__(self)
				self._toStop = False
				self.backendObj = backendObj

			def run(self):
				kal = self.backendObj.KeepAliveInterval
				app = self.backendObj.Application

				while self.backendObj._connection is None:
				    time.sleep(5)

				con = self.backendObj._connection
				cur = con.cursor()

				while True:
					time.sleep(5)

					if kal is None or not app or getattr(app, "_finished", False):
						self._toStop = True
					if self._toStop:
						return

					if time.time() - self.backendObj.lastExecuteTime > kal:
						cur.execute("select 1")
						self.backendObj.lastExecuteTime = time.time()

		existingThread = getattr(self, "_keepAliveThread", None)
		if existingThread:
			existingThread._toStop = True
		if self.KeepAliveInterval is not None:
			wt = self._keepAliveThread = WorkerThread(self)
			wt.start()

	def _getEncoding(self):
		"""Get backend encoding."""
		try:
			return self._encoding
		except AttributeError:
			self._encoding = dabo.getEncoding()
			return self._encoding

	def _setEncoding(self, enc):
		"""
		Set backend encoding. Must be overridden in the subclass
		to notify database about proper charset conversion.
		"""
		self._encoding = enc


	def _getKeepAliveInterval(self):
		try:
			ret = self._keepAliveInterval
		except AttributeError:
			ret = self._keepAliveInterval = None
		return ret

	def _setKeepAliveInterval(self, val):
		self._keepAliveInterval = val
		self._applyKeepAlive()


	Encoding = property(_getEncoding, _setEncoding, None,
			_("Backend encoding  (str)"))

	KeepAliveInterval = property(_getKeepAliveInterval, _setKeepAliveInterval, None,
			_("""Specifies how often a KeepAlive query should be sent to the server.

			Defaults to None, meaning we never send a KeepAlive query. The interval
			is expressed in seconds.
			"""))
