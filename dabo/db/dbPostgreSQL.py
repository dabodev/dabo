# -*- coding: utf-8 -*-
import datetime
import dabo
from dabo.dLocalize import _
from dBackend import dBackend

class Postgres(dBackend):
	"""Class providing PostgreSQL connectivity. Uses psycopg."""
	def __init__(self):
		""" JFCS 08/23/07 Currently supporting only psycopg2"""
		dBackend.__init__(self)
		self.dbModuleName = "psycopg"
		self.conn_user = ""


	def getConnection(self, connectInfo, **kwargs):
		import psycopg2 as dbapi
		self.conn_user = connectInfo.User
		#- jfcs 11/01/04 port needs to be a string
		port = str(connectInfo.Port)
		if not port or port == "None":
			port = "5432"

		DSN = "host=%s port=%s dbname=%s user=%s password=%s" % (connectInfo.Host,
				port, connectInfo.Database, connectInfo.User, connectInfo.revealPW())
		# Instead of blindly appending kwargs here, it would be preferable to only accept
		# those that can be used safely.
# 		for kw, val in kwargs:
# 			DSN += " %s=%s" % (kw, val)
		self._connection = dbapi.connect(DSN)
		return self._connection


	def beginTransaction(self, cursor):
		dabo.dbActivityLog.write("SQL: begin (implicit, nothing done)")
		return True


	def getDictCursorClass(self):
		# the new psycopg 2.0 supports DictCursor
		import psycopg2.extras as cursors
		return cursors.DictCursor


	def escQuote(self, val):
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		return "'%s'" % val.replace('\\', '\\\\').replace("'", "''")


	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		return "'%s'" % self._stringify(val)


	def getTables(self, cursor, includeSystemTables=False):
		query = ["SELECT schemaname||'.'||tablename AS tablename"
				" FROM pg_tables WHERE"]
		if not includeSystemTables:
			query.append("(schemaname NOT LIKE 'pg_%' AND "
					"schemaname NOT LIKE 'information%') AND")
		query.append("has_schema_privilege(schemaname, 'usage') AND "
				"has_table_privilege(schemaname||'.'||tablename, 'select')")
		cursor.execute(' '.join(query))
		return tuple(record["tablename"] for record in cursor.getDataSet())


	def getTableRecordCount(self, tableName, cursor):
		cursor.execute("select count(*) as ncount from %s" % tableName)
		return cursor.getDataSet()[0]["ncount"]


	def getFields(self, tableName, cursor, includeSystemFields=False):
		try:
			schemaName, tableName = tableName.split(".", 1)
		except ValueError:
			schemaName = None
		sql = ["SELECT a.attname, t.typname,"
				# Note that the generate_series() function does not exist
				# in Postgres < 8.0, but it can easily be added, and that
				# in Postgres > 8.1, we could use the ANY syntax instead.
				" EXISTS(SELECT * FROM generate_series(0, 31) idx(n)"
				" WHERE a.attnum = i.indkey[idx.n]) AS isprimary"
				" FROM pg_class c"
				" JOIN pg_namespace n ON n.oid = c.relnamespace"
				" JOIN pg_attribute a ON a.attrelid = c.oid"
				" JOIN pg_type t ON t.oid  = a.atttypid"
				" LEFT JOIN pg_index i ON i.indrelid = c.oid AND i.indisprimary",
				"WHERE c.relname = '%s'" % tableName]
		if schemaName:
			sql.append("AND n.nspname = '%s'" % schemaName)
		if not includeSystemFields:
			sql.append("AND a.attname NOT IN "
					" ('ctid', 'cmin', 'cmax', 'tableoid', 'xmax', 'xmin')")
		sql.append("AND has_schema_privilege(n.oid, 'usage')"
				" AND has_table_privilege(c.oid, 'select')"
				" AND pg_table_is_visible(c.oid)"
				" ORDER BY c.relname, a.attname")
		cursor.execute(' '.join(sql))
		fields = []
		for r in cursor.getDataSet():
			name = r["attname"].strip()
			fldType = r["typname"]
			pk = r["isprimary"]
			if "int" in fldType:
				fldType = "I"
			elif "char" in fldType :
				fldType = "C"
			elif "bool" in fldType :
				fldType = "B"
			elif "text" in fldType:
				fldType = "M"
			elif "numeric" in fldType:
				fldType = "N"
			elif "double" in fldType:
				fldType = "F"
			elif "real" in fldType:
				fldType = "F"
			elif "float" in fldType:
				fldType = "F"
			elif "datetime" in fldType:
				fldType = "T"
			elif "timestamp" in fldType:
				fldType = "T"
			elif "date" in fldType:
				fldType = "D"
			elif "bytea" in fldType:
				fldType = "L"
			elif "point" in fldType:
				fldType = "C"
			elif "box" in fldType:
				fldType = "C"
			elif "circle" in fldType:
				fldType = "C"
			elif "lseg" in fldType:
				fldType = "C"
			elif "polygon" in fldType:
				fldType = "C"
			elif "path" in fldType:
				fldType = "C"
			elif "oid" in fldType:
				fldType = "I"
			else:
				fldType = "?"
			fields.append((name, fldType, pk))
		return tuple(fields)


	def getUpdateTablePrefix(self, tbl, autoQuote=True):
		""" By default, the update SQL statement will be in the form of
					tablename.fieldname
		but Postgres does not accept this syntax. If not, change
		this method to return an empty string, or whatever should
		preceed the field name in an update statement.
		 Postgres needs to return an empty string."""
		return ""


	def noResultsOnSave(self):
		""" Most backends will return a non-zero number if there are updates.
		Some do not, so this will have to be customized in those cases.
		"""
		return


	def noResultsOnDelete(self):
		""" Most backends will return a non-zero number if there are deletions.
		Some do not, so this will have to be customized in those cases.
		"""
		# raise dException.dException(_("No records deleted"))
		return


	def flush(self, cursor):
		""" Postgres requires an explicit commit in order to have changes
		to the database written to disk.
		"""
		self.commitTransaction(cursor)
		dabo.dbActivityLog.write("SQL: Commit")


	def getLastInsertID(self, cursor):
		""" Return the ID of the last inserted row, or None.

		When inserting a new record in a table that auto-generates a PK (such
		as a serial data type) value, different databases have their own way of retrieving that value.
		With Postgres a sequence is created.  The SQL statement determines the sequence name
		('table_pkid_seq') and needs three parameters the schema name, table name, and the primary
		key field for the table.
		cursor.KeyField = primary field
		cursor.Table = returns 'schema.table' for the cursor

		Postgres uses 'currval(sequence_name)' to determine the last value of the session.
		If two different sessions are open (two users accessing the same table for example)
		currval() will return the correct value for each session.

		"""

		try:
			schemaName, tableName = tableName.split(".", 1)
		except ValueError:
			schemaName = None

		#JFCS 01/13/08 changed the select statement to allow primary fields that were not based
		#on a serial data type to work.
		# special thanks to Lorenzo Alberton for his help with parsing of the fields.
		# It has been confirmed that the statement works with 7.4 through 8.3.x
		sql = ["SELECT curval(substring((SELECT substring("
				"pg_get_expr(d.adbin, d.adrelid) for 128)) as curval"
				" FROM pg_attrdef d WHERE d.adrelid = a.attrelid"
				" AND d.adnum = a.attnum AND a.atthasdef)"
				" FROM 'nextval[^'']*''([^'']*)')"
				" FROM pg_attribute a"
				" LEFT JOIN pg_class c ON c.oid = a.attrelid"
				" LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid"
				" AND d.adnum = a.attnum AND a.atthasdef"
				" LEFT JOIN pg_namespace n ON c.relnamespace = n.oid",
				"WHERE a.attname = '%s'" % cursor.KeyField,
				"AND (c.relname = '%s')" % tableName]
		if schemaName:
			sql.append(" AND n.nspname = '%s'" % schemaName)
		else:
			sql.append(" AND pg_table_is_visible(c.oid)")
		sql.append("NOT a.attisdropped AND a.attnum > 0"
				" AND pg_get_expr(d.adbin, d.adrelid) LIKE 'nextval%'")

		tempCursor = self._connection.cursor()
		try:
			tempCursor.execute(' '.join(sql))
			rs = tempCursor.fetchone()
		finally:
			tempCursor.close()
		if not rs or rs[0] is None:
			raise AttributeError("Unable to determine the sequence used"
					" or the sequence returns a strange value.")
		else:
			return rs[0]
