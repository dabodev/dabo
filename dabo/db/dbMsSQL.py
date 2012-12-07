# -*- coding: utf-8 -*-
import datetime
from dabo.dLocalize import _
from dBackend import dBackend
from dabo.lib.utils import ustr



class MSSQL(dBackend):
	"""Class providing Microsoft SQL Server connectivity. Uses pymssql."""
	def __init__(self):
		dBackend.__init__(self)
		#- jfcs 11/06/06 first try getting Microsoft SQL 2000 server working
		# MSSQL requires the installation of FreeTDS.  FreeTDS can be downloaded from
		# http://www.freetds.org/
		self.dbModuleName = "pymssql"
		self.useTransactions = True  # this does not appear to be required
		import pymssql
		self.dbapi = pymssql


	def getConnection(self, connectInfo, forceCreate=False, **kwargs):
		"""
		The pymssql module requires the connection be created for the FreeTDS libraries first.
		Therefore, the DSN is really the name of the connection for FreeTDS :
		  __init__(self, dsn, user, passwd, database = None, strip = 0)
		"""
		port = ustr(connectInfo.Port)
		if not port or port == "None":
			port = 1433
		host = "%s:%s" % (connectInfo.Host, port)
		user = connectInfo.User
		password = connectInfo.revealPW()
		database = connectInfo.Database

		# hack to make this work.  I am sure there is a better way.
		self.database = database
		# Hack to make new driver working with non us-ascii encoding.
		if "charset" not in kwargs and self.dbapi.__version__ >= "2.0.0":
			kwargs["charset"] = self.Encoding

		self._connection = self.dbapi.connect(host=host, user=user, password=password,
				database=database, **kwargs)
		return self._connection


	def getDictCursorClass(self):
		"""Since there are two versions of driver package we support both,
		deprecated and new one.
		"""
		if self.dbapi.__version__ >= "2.0.0":
			class ConCursor(self.dbapi.Cursor):
				def __init__(self, *args, **kwargs):
					# pymssql requires an additional param to be passed
					# to its __init__() method
					kwargs["as_dict"] = True
					super(ConCursor, self).__init__(*args, **kwargs)
				def fetchall(self):
					# In dictionary mode both column numbers and names are used
					# as keys. We need to filter them and leave name based keys only.
					rows = super(ConCursor, self).fetchall()
					for row in rows:
						for key in range(len(row) / 2):
							row.pop(key, None)
					return rows
		else:
			class ConCursor(self.dbapi.pymssqlCursor):
				def __init__(self, *args, **kwargs):
					# pymssql requires an additional param to be passed
					# to its __init__() method
					kwargs["as_dict"] = True
					super(ConCursor, self).__init__(*args, **kwargs)
				if not hasattr(self.dbapi.pymssqlCursor, "connection"):
					def _getconn(self):
						return self._source
					# pymssql doesn't supply this optional dbapi attribute, so create it here.
					connection = property(_getconn, None, None)

		return ConCursor


	def escQuote(self, val):
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl + sl).replace(qt, sl + qt) + qt


	def formatDateTime(self, val):
		"""We need to wrap the value in quotes."""
		sqt = "'"		# single quote
		val = ustr(val)
		return "%s%s%s" % (sqt, val, sqt)


	def getTables(self, cursor, includeSystemTables=False):
		# jfcs 11/01/06 assumed public schema
		# cfk: this worries me: how does it know what db is being used?
		# tempCursor.execute("select name from sysobjects where xtype = 'U' order by name")

		dbName = self.database

		sql = """
select table_schema + '.' + table_name AS table_name
  from INFORMATION_SCHEMA.TABLES
 where table_catalog = '%(db)s'
   and table_type IN ('BASE TABLE', 'VIEW')
 order by 1 """

		cursor.execute(sql % {'db':dbName})

		rs = cursor.getDataSet()
		tables = [x["table_name"] for x in rs]
		tables = tuple(tables)

		return tables


	def getTableRecordCount(self, tableName, cursor):
		cursor.execute("select count(*) as ncount from '%(tablename)'" % tableName)
		return cursor.getDataSet()[0]["ncount"]


	def _fieldTypeNativeToDabo(self, nativeType):
		"""
		converts the results of
		select DATA_TYPE from INFORMATION_SCHEMA.COLUMNS
		to a dabo datatype.
		"""

		# todo: break out the dict into a constant defined somewhere
		# todo: make a formal definition of the dabo datatypes.
		# (at least document them)

		try:
			ret = {
			"BINARY": "I",
			"BIT": "I",
			"BIGINT": "G",
			"BLOB": "M",
			"CHAR": "C",
			"DATE": "D",
			"DATETIME": "T",
			"DATETIME2": "T",
			"DECIMAL": "N",
			"DOUBLE": "G", ## G maps to Long (INT), but this could be wrong if it is supposed to be a double float.
			"ENUM": "C",
			"FLOAT": "F",
			"GEOMETRY": "?",
			"INT": "I",
			"IMAGE": "?",
			"INTERVAL": "?",
			"LONG": "G",
			"LONGBLOB": "M",
			"LONGTEXT": "M",
			"MEDIUMBLOB": "M",
			"MEDIUMINT": "I",
			"MEDIUMTEXT": "M",
			"MONEY": "F",
			"NEWDATE": "?",
			"NCHAR": "C",
			"NTEXT": "M",
			"NUMERIC": "N",
			"NVARCHAR": "C",
			"NULL": "?",
			"SET": "?",
			"SHORT": "I",
			"SMALLINT": "I",
			"STRING": "C",
			"TEXT": "M",
			"TIME": "?",
			"TIMESTAMP": "T",
			"TINY": "I",
			"TINYINT": "I",
			"TINYBLOB": "M",
			"TINYTEXT": "M",
			"UNIQUEIDENTIFIER": "?",
			"VARBINARY": "I",
			"VARCHAR": "C",
			"VAR_STRING": "C",
			"YEAR": "?"}[nativeType.upper()]
		except KeyError:
			print 'KeyError:', nativeType
			ret = '?'
		return ret


	def getFields(self, tableName, cursor):
		"""
		Returns the list of fields of the passed table
		field: ( fieldname, dabo data type, key )
		"""
		# fairly standard way of getting column settings
		# this may be standard enough to put in the super class
		dbName = self.database
		tableNamespace = tableName.split(".")
		if len(tableNamespace) > 1:
			tableSchema = tableNamespace[-2]
			tableName = tableNamespace[-1]
		else:
			tableSchema = "dbo"
		if not tableName:
			return ()
		sql = """
select COLUMN_NAME,
       DATA_TYPE
  from INFORMATION_SCHEMA.COLUMNS
 where table_catalog = %s and
 	table_schema = %s and
     table_name = %s
 order by ORDINAL_POSITION """

		cursor.execute(sql, (dbName, tableSchema, tableName))
		fieldDefs = cursor.getDataSet()

		sql = """
select kc.COLUMN_NAME from INFORMATION_SCHEMA.KEY_COLUMN_USAGE as kc
	inner join INFORMATION_SCHEMA.TABLE_CONSTRAINTS as tc
		on tc.CONSTRAINT_NAME = kc.CONSTRAINT_NAME
	where kc.TABLE_CATALOG = %s and
		kc.TABLE_SCHEMA = %s and
		kc.TABLE_NAME = %s and
		tc.CONSTRAINT_TYPE = 'PRIMARY KEY' """

		cursor.execute(sql, (dbName, tableSchema, tableName))
		pkFields = cursor.getDataSet()

		fields = []
		for r in fieldDefs:
			name = r["COLUMN_NAME"]
			ft = self._fieldTypeNativeToDabo(r["DATA_TYPE"])
			pk = (name,) in [(p["COLUMN_NAME"],) for p in pkFields]
			fields.append((name, ft, pk))

		return tuple(fields)


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
		#raise dException.dException(_("No records deleted"))
		return


	def flush(self, cursor):
		self.commitTransaction(cursor)


	def getLimitWord(self):
		return "TOP"


	def formSQL(self, fieldClause, fromClause, joinClause,
				whereClause, groupByClause, orderByClause, limitClause):
		"""MS SQL wants the limit clause before the field clause."""
		clauses = (limitClause, fieldClause, fromClause, joinClause,
				whereClause, groupByClause, orderByClause)
		sql = "SELECT " + "\n".join([clause for clause in clauses if clause])
		return sql


	def getLastInsertID(self, cursor):
		"""
		Pymssql does not populate the 'lastrowid' attribute of the cursor, so we
		need to get the newly-inserted PK ourselves.
		"""
		# Use the AuxCursor so as not to disturb the contents of the primary data cursor.
		try:
			idVal = cursor.lastrowid
		except AttributeError:
			crs = cursor.AuxCursor
			crs.execute("select @@IDENTITY as newid")
			idVal = crs.getFieldVal("newid")
		# Some interface versions return PK constraint values as Decimal type
		# what isn't well tolerated by Dabo.
		if "Decimal" in str(type(idVal)):
			idVal = int(idVal)
		return idVal


	def beginTransaction(self, cursor):
		pass
