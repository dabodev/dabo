# -*- coding: utf-8 -*-

import codecs
import datetime
import dabo
from dabo.dLocalize import _
from dBackend import dBackend
from dabo.lib.utils import ustr



class Postgres(dBackend):
	"""Class providing PostgreSQL connectivity. Uses psycopg."""


	_encodings = {
		# mapping from Python encoding names
		# to PostgreSQL character set names
		'big5': 'BIG5',
		'cp866': 'WIN866',
		'cp874': 'WIN874',
		'cp949': 'UHC',
		'cp1250': 'WIN1250',
		'cp1251': 'WIN1251',
		'cp1252': 'WIN1252',
		'cp1253': 'WIN1253',
		'cp1254': 'WIN1254',
		'cp1255': 'WIN1255',
		'cp1256': 'WIN1256',
		'cp1257': 'WIN1257',
		'cp1258': 'WIN1258',
		'euc_jis_2004': 'EUC_JIS_2004',
		'euc_jp': 'EUC_JP',
		'euc_kr': 'EUC_KR',
		'euc_tw': 'EUC_TW',
		'gb18030': 'GB18030',
		'gb2312': 'EUC_CN',
		'gbk': 'GBK',
		'iso8859-1': 'LATIN1',
		'iso8859-2': 'LATIN2',
		'iso8859-3': 'LATIN3',
		'iso8859-4': 'LATIN4',
		'iso8859-5': 'ISO_8859_5',
		'iso8859-6': 'ISO_8859_6',
		'iso8859-7': 'ISO_8859_7',
		'iso8859-8': 'ISO_8859_8',
		'iso8859-9': 'LATIN5',
		'iso8859-10': 'LATIN6',
		'iso8859-13': 'LATIN7',
		'iso8859-14': 'LATIN8',
		'iso8859-15': 'LATIN9',
		'iso8859-16': 'LATIN10',
		'johab': 'JOHAB',
		'koi8-r': 'KOI8',
		'shift_jis': 'SJIS',
		'shift_jis_2004': 'SHIFT_JIS_2004',
		'utf-8': 'UTF8'
	}


	def __init__(self):
		"""JFCS 08/23/07 Currently supporting only psycopg2"""
		dBackend.__init__(self)
		self.dbModuleName = "psycopg"
		self.conn_user = ""


	def getConnection(self, connectInfo, **kwargs):
		import psycopg2 as dbapi
		self.conn_user = connectInfo.User
		DSN = "host=%s port=%d dbname=%s user=%s password=%s" % (
			connectInfo.Host, connectInfo.Port or 5432, connectInfo.Database,
				self.conn_user, connectInfo.revealPW())
		self._connection = dbapi.connect(DSN)
		self.setClientEncoding()
		return self._connection


	def setClientEncoding(self, encoding=None):
		if not encoding:
			encoding = self.Encoding
		try:
			encoding = codecs.lookup(encoding).name
		except (AttributeError, LookupError):
			pass
		try:
			encoding = self._encodings[encoding]
		except KeyError:
			dabo.dbActivityLog.info("unknown encoding %r" % encoding)
		if self._connection.encoding != encoding:
			try:
				self._connection.set_client_encoding(encoding)
			except Exception:
				dabo.dbActivityLog.info("cannot set database client encoding")
		return encoding


	def beginTransaction(self, cursor):
		dabo.dbActivityLog.info("SQL: begin (implicit, nothing done)")
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
		"""We need to wrap the value in quotes."""
		return "'%s'" % ustr(val)


	def getTables(self, cursor, includeSystemTables=False):
		query = ["SELECT schemaname||'.'||tablename AS tablename"
				" FROM pg_tables WHERE"]
		if not includeSystemTables:
			query.append("(schemaname NOT LIKE 'pg_%' AND "
					"schemaname NOT LIKE 'information%') AND")
		query.append("""has_schema_privilege(schemaname, 'usage') AND """
                                 """has_table_privilege('"'||schemaname||'"."'||tablename||'"', 'select')""")
		record=[]
		cursor.execute(" ".join(query))
		for rec1 in cursor.getDataSet():
			record.append(rec1["tablename"])
		cursor.execute("SELECT schemaname||'.'||viewname as tablename FROM pg_views WHERE schemaname NOT IN('information_schema', 'pg_catalog')")

		for rec in cursor.getDataSet():
			record.append(rec["tablename"])

		return tuple(record)


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
		else:
			sql.append("AND pg_table_is_visible(c.oid)")
		if not includeSystemFields:
			sql.append("AND a.attname NOT IN "
					" ('ctid', 'cmin', 'cmax', 'tableoid', 'xmax', 'xmin')")
		sql.append("AND has_schema_privilege(n.oid, 'usage')"
				" AND has_table_privilege(c.oid, 'select')"
				" ORDER BY c.relname, a.attname")
		cursor.execute(' '.join(sql))
		fldTypeDict= {"int4":"I", "int8":"I", "int2":"I","varchar": "C",  "char": "C",'bpchar': 'C', "bool":"B", "text": "M", "numeric":"N", "double":"F", "real":"F","float4":"F", "float8":"F", "datetime":"T", "timestamp":"T", "date": "D","bytea": "L", "point":"C", "box":"C", "circle":"C", "lseg":"C", "polygon":"C", "path":"C","oid":"I"}
		fields = []
		for r in cursor.getDataSet():
			name = r["attname"].strip()
			fldType = r["typname"]
			pk = r["isprimary"]
			fieldType = fldTypeDict.get(fldType, '?')
			fields.append((name, fieldType, pk))
		#cursor.execute('rollback')
		self.rollbackTransaction(cursor)
		return tuple(fields)


	def getUpdateTablePrefix(self, tbl, autoQuote=True):
		"""
		By default, the update SQL statement will be in the form of

					tablename.fieldname

		but Postgres does not accept this syntax. If not, change
		this method to return an empty string, or whatever should
		preceed the field name in an update statement.
		Postgres needs to return an empty string.
		"""
		return ""


	def noResultsOnSave(self):
		"""
		Most backends will return a non-zero number if there are updates.
		Some do not, so this will have to be customized in those cases.
		"""
		return


	def noResultsOnDelete(self):
		"""
		Most backends will return a non-zero number if there are deletions.
		Some do not, so this will have to be customized in those cases.
		"""
		# raise dException.dException(_("No records deleted"))
		return


	def flush(self, cursor):
		"""
		Postgres requires an explicit commit in order to have changes
		to the database written to disk.
		"""
		self.commitTransaction(cursor)
		dabo.dbActivityLog.info("SQL: Commit")


	def getLastInsertID(self, cursor):
		"""
		Return the ID of the last inserted row, or None.

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
		tableName = cursor.Table
		try:
			schemaName, tableName = tableName.split(".", 1)
		except ValueError:
			schemaName = None

		#JFCS 01/13/08 changed the select statement to allow primary fields that were not based
		#on a serial data type to work.
		# special thanks to Lorenzo Alberton for his help with parsing of the fields.
		# It has been confirmed that the statement works with 7.4 through 8.3.x
		sql = ["SELECT currval(substring((SELECT substring("
				"pg_get_expr(d.adbin, d.adrelid) for 128)"
				" FROM pg_attrdef d WHERE d.adrelid = a.attrelid"
				" AND d.adnum = a.attnum AND a.atthasdef)"
				" FROM 'nextval[^'']*''([^'']*)')) as currval"
				" FROM pg_attribute a"
				" LEFT JOIN pg_class c ON c.oid = a.attrelid"
				" LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid"
				" AND d.adnum = a.attnum AND a.atthasdef"
				" LEFT JOIN pg_namespace n ON c.relnamespace = n.oid",
				"WHERE a.attname = '%s'" % cursor.KeyField,
				"AND (c.relname = '%s')" % tableName]
		if schemaName:
			sql.append("AND n.nspname = '%s'" % schemaName)
		else:
			sql.append("AND pg_table_is_visible(c.oid)")
		sql.append("AND NOT a.attisdropped AND a.attnum > 0"
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
