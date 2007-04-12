# -*- coding: utf-8 -*-
import datetime
from dabo.dLocalize import _
from dBackend import dBackend

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


	def getConnection(self, connectInfo):
		"""The pymssql module requires the connection be created for the FreeTDS libraries first.  Therefore, the 
		DSN is really the name of the connection for FreeTDS
		  __init__(self, dsn, user, passwd, database = None, strip = 0)"""
		import pymssql 
		
		port = str(connectInfo.Port)
		if not port or port == "None":
			port = 1433
		host = "%s:%s" % (connectInfo.Host, port)
		user = connectInfo.User
		password = connectInfo.revealPW()
		database = connectInfo.Database
		
		# hack to make this work.  I am sure there is a better way.
		self.database = database
				
		self._connection = pymssql.connect(host=host, user=user,password=password, database=database)
		return self._connection


	def getDictCursorClass(self):
		"""Currently this is not working completely"""
		import pymssql
		class conCursor(pymssql.pymssqlCursor):
			def _getconn(self):
				return self.__source
			# pymssql doesn't supply this optional dbapi attribute, so create it here.
			connection = property(_getconn, None, None)
		return conCursor
		#return cursors.Connection.cursor
		

	def escQuote(self, val):
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl+sl).replace(qt, sl+qt) + qt
	
	
	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
	
	
	def getTables(self, includeSystemTables=False):
		tempCursor = self._connection.cursor()
		# jfcs 11/01/06 assumed public schema
		# cfk: this worries me: how does it know what db is being used?
		# tempCursor.execute("select name from sysobjects where xtype = 'U' order by name")
		
		dbName = self.database
		tempCursor.execute("select table_name"
			" from INFORMATION_SCHEMA.TABLES"
			" where table_catalog = %(db)s"
			" and table_type = 'BASE TABLE'"
			" order by table_name",
			 {'db':dbName} )
		rs = tempCursor.fetchall()
		tables = [x[0] for x in rs]
		tables = tuple(tables)
		return tables

	
	def getTableRecordCount(self, tableName):
		tempCursor = self._connection.cursor()
		tempCursor.execute("select count(*) as ncount from '%(tablename)'" % tableName)
		return tempCursor.fetchall()[0][0]

	def _fieldTypeNativeToDabo(self, nativeType):
		""" converts the results of 
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
			"BIGINT": "I",
			"BLOB": "M",
			"CHAR": "C",
			"DATE": "D",
			"DATETIME": "T",
			"DECIMAL": "N",
			"DOUBLE": "G",
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

	def getFields(self, tableName):
		""" Returns the list of fields of the passed table
			field: ( fieldname, dabo data type, key )
			"""
		tempCursor = self._connection.cursor()
		# fairly standard way of getting column settings
		# this may be standard enough to put in the super class

		dbName = self.database
		
		tempCursor.execute(
			"select COLUMN_NAME, DATA_TYPE" 
			" from INFORMATION_SCHEMA.COLUMNS"
			" where table_catalog = %(db)s"
			" and table_name = %(table)s"
			" order by ORDINAL_POSITION",
			 {'table':tableName, 'db':dbName} )
		fieldDefs = tempCursor.fetchall()

		tempCursor.execute(
			"select COLUMN_NAME "
			" from information_schema.Constraint_Column_Usage CCU"
			" join information_schema.TABLE_CONSTRAINTS TC"
			" on CCU.CONSTRAINT_NAME = TC.CONSTRAINT_NAME"
			" where"
			" CONSTRAINT_TYPE = 'PRIMARY KEY'"
			" and TC.CONSTRAINT_CATALOG = %(db)s" 
			" and TC.Table_Name = %(table)s",
			 {'table':tableName, 'db':dbName} )
		pkFields = tempCursor.fetchall()

		fields = []
		for r in fieldDefs:
			name = r[0]
			ft = self._fieldTypeNativeToDabo(r[1])
			pk = (name,) in pkFields
			fields.append((name, ft, pk))
		return tuple(fields)

		
	def noResultsOnSave(self):
		""" Most backends will return a non-zero number if there are updates.
		Some do not, so this will have to be customized in those cases.
		"""
		return 


	def noResultsOnDelete(self):
		""" Most backends will return a non-zero number if there are deletions.
		Some do not, so this will have to be customized in those cases.
		"""
		#raise dException.dException, _("No records deleted")
		return 

	
	def flush(self, cursor):
		self.commitTransaction(cursor)
		
		
	def getLimitWord(self):
		return "TOP"
	
	
	def formSQL(self, fieldClause, fromClause, joinClause,
				whereClause, groupByClause, orderByClause, limitClause):
		""" MS SQL wants the limit clause before the field clause.	"""
		clauses =  (limitClause, fieldClause, fromClause, joinClause, 
				whereClause, groupByClause, orderByClause)
		sql = "SELECT " + "\n".join( [clause for clause in clauses if clause] )
		return sql
