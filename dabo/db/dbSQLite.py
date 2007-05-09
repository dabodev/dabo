# -*- coding: utf-8 -*-
import os
import re
from dabo.dLocalize import _
from dBackend import dBackend
from dNoEscQuoteStr import dNoEscQuoteStr as dNoEQ
from dCursorMixin import dCursorMixin


class SQLite(dBackend):
	"""Class providing SQLite connectivity. Uses sqlite3 or pysqlite2 package."""
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "pysqlite2"
		try:
			from pysqlite2 import dbapi2 as dbapi
		except ImportError:
			import sqlite3 as dbapi
		self.dbapi = dbapi
		self._alreadyCorrectedFieldTypes = True
		

	def getConnection(self, connectInfo, **kwargs):
		## Mods to sqlite to return DictCursors by default, so that dCursor doesn't
		## need to do the conversion:
		dbapi = self.dbapi

		def dict_factory(cursor, row):
			_types = getattr(cursor, "_types", {})
			ret = {}
			fieldNames = (fld[0] for fld in cursor.description)
			for idx, field_name in enumerate(fieldNames):
				if _types:
					ret[field_name] = cursor._correctFieldType(row[idx], field_name, _fromRequery=True)
				else:
					ret[field_name] = row[idx]
			return ret

		class DictCursor(self.dbapi.Cursor):
			def __init__(self, *args, **kwargs):
				dbapi.Cursor.__init__(self, *args, **kwargs)
				self.row_factory = dict_factory

		class DictConnection(self.dbapi.Connection):
			def __init__(self, *args, **kwargs):
				dbapi.Connection.__init__(self, *args, **kwargs)

			def cursor(self):
				return DictCursor(self)

		self._dictCursorClass = DictCursor
		pth = os.path.expanduser(connectInfo.Database)
		self._connection = self.dbapi.connect(pth, factory=DictConnection)
		return self._connection
		

	def getDictCursorClass(self):
		return self._dictCursorClass
		

	def escQuote(self, val):			
		sl = "\\"
		qt = "\'"
		return qt + str(val).replace(sl, sl+sl).replace(qt, qt+qt) + qt
	
	
	def setAutoCommitStatus(self, cursor, val):
		"""SQLite doesn't use an 'autocommit()' method. Instead,
		set the isolation_level property of the connection.
		"""
		if val:
			self._connection.isolation_level = None
		else:
			self._connection.isolation_level = ""
		self._autoCommit = val
		
	
	def beginTransaction(self, cursor):
		""" Begin a SQL transaction. Since pysqlite does an implicit
		'begin' even when not using autocommit, simply do nothing.
		"""
		pass
	
	
	def flush(self, crs):
		self._connection.commit()


	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
		
	
	def _isExistingTable(self, tablename):
		tempCursor = self._connection.cursor()
		tempCursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=%s" % self.escQuote(tablename))
		rs = tempCursor.fetchall()
		return len(rs) > 0
	
	
	def getTables(self, includeSystemTables=False):
		tempCursor = self._connection.cursor()
		tempCursor.execute("select * from sqlite_master")
		rs = tempCursor.fetchall()
		if includeSystemTables:
			tables = [rec["name"] for rec in rs 
					if rec["type"] == "table"]
		else:
			tables = [rec["name"] for rec in rs
					if rec["type"] == "table"
					and not rec["name"].startswith("sqlite_")]
		return tuple(tables)
		
		
	def getTableRecordCount(self, tableName):
		tempCursor = self._connection.cursor()
		tempCursor.execute("select count(*) as ncount from %s" % tableName)
		return tempCursor.fetchall()[0]["ncount"]


	def getFields(self, tableName):
		tempCursor = self._connection.cursor()
		tempCursor.execute("pragma table_info('%s')" % tableName)
		rs = tempCursor.fetchall()
		fields = []
		for rec in rs:
			typ = rec["type"].lower()
			if typ[:3] == "int":	
				fldType = "I"
			elif typ[:3] == "dec" or typ[:4] == "real":
				fldType = "N"
			elif typ == "blob":
				fldType = "L"
			elif typ[:4] == "clob" or typ[:8] == "longtext":
				fldType = "M"
			else:
				# SQLite treats everything else as text
				fldType = "C"
			# Adi J. Sieker pointed out that the 'pk' column of the pragma command
			# returns a value indicating whether the field is the PK or not. This simplifies 
			# the routine over having to parse the CREATE TABLE code.
			fields.append( (rec["name"], fldType, bool(rec['pk'])) )
		return tuple(fields)


	def setNonUpdateFields(self, cursor):
		# Use an alternative, since grabbing an empty cursor, as is done in the 
		# default method, doesn't provide a  description. Assume that any field with 
		# the same name as the fields in the base table will be updatable.
		if not cursor.Table:
			# No table specified, so no update checking is possible
			return
		# This is the current description of the cursor.
		descFlds = cursor.FieldDescription
		# Get the field info for the table
		auxCrs = cursor._getAuxCursor()
		auxCrs.execute("pragma table_info('%s')" % cursor.Table)
		rs = auxCrs._records

		stdFlds = [ff["name"] for ff in rs]
		# Get all the fields that are not in the table.
		cursor.__nonUpdateFields = [d[0] for d in descFlds 
				if d[0] not in [s[0] for s in stdFlds] ]
		
		
	def getUpdateTablePrefix(self, table, autoQuote=True):
		"""Table name prefixes are not allowed."""
		return ""
		
		
	def getWhereTablePrefix(self, table, autoQuote=True):
		"""Table name prefixes are not allowed."""
		return ""


	def noResultsOnSave(self):
		""" SQLite does not return anything on a successful update"""
		pass
		
		
	def createTableAndIndexes(self, tabledef, cursor, createTable=True, 
			createIndexes=True):
		if not tabledef.Name:
			raise
			
		#Create the table
		if createTable:
			if not tabledef.IsTemp:
				sql = "CREATE TABLE "
			else:
				sql = "CREATE TEMP TABLE "
			sql = sql + tabledef.Name + " ("
			
			for fld in tabledef.Fields:
				dont_esc = False
				sql = sql + fld.Name + " "
				
				if fld.DataType == "Numeric":
					sql = sql + "INTEGER "					
				elif fld.DataType == "Float":
					sql = sql + "REAL "
				elif fld.DataType == "Decimal":
					sql = sql + "TEXT "
				elif fld.DataType == "String":
					sql = sql + "TEXT "
				elif fld.DataType == "Date":
					sql = sql + "TEXT "
				elif fld.DataType == "Time":
					sql = sql + "TEXT "
				elif fld.DataType == "DateTime":
					sql = sql + "TEXT "
				elif fld.DataType == "Stamp":
					sql = sql + "TEXT "
					fld.Default = dNoEQ("CURRENT_TIMESTAMP")
				elif fld.DataType == "Binary":
					sql = sql + "BLOB "
				
				if fld.IsPK:
					sql = sql + "PRIMARY KEY "
					if fld.IsAutoIncrement:
						sql = sql + "AUTOINCREMENT "
				
				if not fld.AllowNulls:
					sql = sql + "NOT NULL "
				sql = "%sDEFAULT %s," % (sql, self.formatForQuery(fld.Default))
			if sql[-1:] == ",":
				sql = sql[:-1]
			sql = sql + ")"
			
			cursor.execute(sql)
			
	
		if createIndexes:
			#Create the indexes
			for idx in tabledef.Indexes:
				if idx.Name.lower() != "primary":
					sql = "CREATE INDEX " + idx.Name + " ON " + tabledef.Name + "("
					for fld in idx.Fields:
						sql = sql + fld + ","
					if sql[-1:] == ",":
						sql = sql[:-1]
					sql = sql + ")"
				
				cursor.execute(sql)
