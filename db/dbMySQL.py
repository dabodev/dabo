# -*- coding: utf-8 -*-
import datetime
try:
	import decimal
except ImportError:
	decimal = None
from dabo.dLocalize import _
from dBackend import dBackend
import dabo.dException as dException
from dNoEscQuoteStr import dNoEscQuoteStr as dNoEQ

class MySQL(dBackend):
	"""Class providing MySQL connectivity. Uses MySQLdb."""

	# MySQL uses the backtick to enclose names with spaces.
	nameEnclosureChar = "`"

	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "MySQLdb"


	def getConnection(self, connectInfo):
		import MySQLdb as dbapi

		port = connectInfo.Port
		if not port:
			port = 3306

		kwargs = {}
		if decimal is not None:
			# MySQLdb doesn't provide decimal converter by default, so we do it here
			from MySQLdb import converters
			from MySQLdb import constants

			DECIMAL = constants.FIELD_TYPE.DECIMAL
			conversions = converters.conversions.copy()
			conversions[DECIMAL] = decimal.Decimal

			def dec2str(dec, dic):
				return str(dec)

			conversions[decimal.Decimal] = dec2str
			kwargs["conv"] = conversions

		try:
			self._connection = dbapi.connect(host=connectInfo.Host, 
					user = connectInfo.User,
					passwd = connectInfo.revealPW(),
					db=connectInfo.Database,
					port=port, **kwargs)
		except Exception, e:			
			if "access denied" in str(e).lower():
				raise dException.DBNoAccessException(e)
			else:
				raise dException.DatabaseException(e)
		return self._connection


	def getDictCursorClass(self):
		import MySQLdb.cursors as cursors
		return cursors.DictCursor


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
	
	
	def _isExistingTable(self, tablename):
		tempCursor = self._connection.cursor()
		tbl = self.encloseNames(self.escQuote(tablename))
		tempCursor.execute("SHOW TABLES LIKE %s" % tbl)
		rs = tempCursor.fetchall()
		return bool(rs)
			
	
	def getTables(self, includeSystemTables=False):
		# MySQL doesn't have system tables, in the traditional sense, as 
		# they exist in the mysql database.
		tempCursor = self._connection.cursor()
		tempCursor.execute("show tables")
		rs = tempCursor.fetchall()
		tables = []
		for record in rs:
			tables.append(record[0])
		return tuple(tables)
		
		
	def getTableRecordCount(self, tableName):
		tempCursor = self._connection.cursor()
		tempCursor.execute("select count(*) as ncount from %s" % self.encloseNames(tableName))
		return tempCursor.fetchall()[0][0]


	def getFields(self, tableName):
		if not tableName:
			return tuple()
		tempCursor = self._connection.cursor()
		tempCursor.execute("describe %s" % self.encloseNames(tableName))
		rs = tempCursor.fetchall()
		fldDesc = tempCursor.description
		# The field name is the first element of the tuple. Find the
		# first entry with the field name 'Key'; that will be the 
		# position for the PK flag
		pkPos = 0
		for i in range(len(fldDesc)):
			if fldDesc[i][0] == "Key":
				pkPos = i
				break
		
		fields = []
		for r in rs:
			name = r[0]
			ft = r[1]
			if ft.split()[0] == "tinyint(1)" or "bit" in ft:
				ft = "B"
			elif "int" in ft:
				ft = "I"
			elif ft == "long":
				ft = "G"
			elif "varchar" in ft:
				# will be followed by length
				ln = int(ft.split("(")[1].split(")")[0])
				if ln > 255:
					ft = "M"
				else:
					ft = "C"
			elif "char" in ft :
				ft = "C"
			elif "text" in ft:
				ft = "M"
			elif "blob" in ft:
				ft = "L"
			elif "decimal" in ft:
				ft = "N"
			elif "float" in ft:
				ft = "F"
			elif "datetime" in ft:
				ft = "T"
			elif "date" in ft:
				ft = "D"
			elif "enum" in ft:
				ft = "C"
			else:
				ft = "?"
			pk = (r[pkPos] == "PRI")
			
			fields.append((name.strip(), ft, pk))
		return tuple(fields)


	def getDaboFieldType(self, backendFieldType):
		import MySQLdb.constants.FIELD_TYPE as ftypes
		typeMapping = {}
		for i in dir(ftypes):
			if i[0] != "_":
				v = getattr(ftypes, i)
				typeMapping[v] = i
		# typeMapping[16]='BIT'

		daboMapping = {"BIT": "I",
				"BLOB": "M",
				"CHAR": "C",
				"DATE": "D",
				"DATETIME": "T",
				"DECIMAL": "N",
				"DOUBLE": "G",
				"ENUM": "C",
				"FLOAT": "F",
				"GEOMETRY": "?",
				"INT24": "I",
				"INTERVAL": "?",
				"LONG": "G",
				"LONGLONG": "G",
				"LONG_BLOB": "M",
				"MEDIUM_BLOB": "M",
				"NEWDATE": "?",
				"NEWDECIMAL": "N",
				"NULL": "?",
				"SET": "?",
				"SHORT": "I",
				"STRING": "C",
				"TIME": "?",
				"TIMESTAMP": "T",
				"TINY": "I",
				"TINY_BLOB": "M",
				"VAR_STRING": "C",
				"YEAR": "?"}
		return daboMapping[typeMapping[backendFieldType]]


	def getWordMatchFormat(self):
		""" MySQL's fulltext search expression"""
		return """ match (`%(table)s`.`%(field)s`) against ("%(value)s") """


	def createTableAndIndexes(self, tabledef, cursor, createTable=True, 
			createIndexes=True):
		if not tabledef.Name:
			raise
		
		toExc = []
		
		#Create the table
		if createTable:			
			
			if not tabledef.IsTemp:
				sql = "CREATE TABLE "
			else:
				sql = "CREATE TEMPORARY TABLE "
				
			sql = sql + tabledef.Name + " ("
			
			for fld in tabledef.Fields:
				pks = []
				sql = sql + fld.Name + " "
				
				if fld.DataType == "Numeric":
					if fld.Size == 0:
						sql = sql + "BIT "
					elif fld.Size == 1:
						sql = sql + "TINYINT "
					elif fld.Size == 2:
						sql = sql + "SMALLINT "
					elif fld.Size in (3,4):
						sql = sql + "INT "
					elif fld.Size in (5,6,7,8):
						sql = sql + "BIGINT "
					else:
						raise #what should happen?
											
				elif fld.DataType == "Float":
					if fld.Size in (0,1,2,3,4):
						sql = sql + "FLOAT(" + str(fld.TotalDP) + "," + str(fld.RightDP) + ") "
					elif fld.Size in (5,6,7,8):
						sql = sql + "DOUBLE(" + str(fld.TotalDP) + "," + str(fld.RightDP) + ") "
					else:
						raise #what should happen?
				elif fld.DataType == "Decimal":
					sql = sql + "DECIMAL(" + str(fld.TotalDP) + "," + str(fld.RightDP) + ") "
				elif fld.DataType == "String":
					if fld.Size <= 255:
						sql = sql + "VARCHAR(" + str(fld.Size) + ") "
					elif fld.Size <= 65535:
						sql = sql + "TEXT "
					elif fld.Size <= 16777215:
						sql = sql + "MEDIUMTEXT "
					elif fld.Size <= 4294967295:
						sql = sql + "LONGTEXT "
					else:
						raise #what should happen?
				elif fld.DataType == "Date":
					sql = sql + "DATE "
				elif fld.DataType == "Time":
					sql = sql + "TIME "
				elif fld.DataType == "DateTime":
					sql = sql + "DATETIME "
				elif fld.DataType == "Stamp":
					sql = sql + "TIMESTAMP "
					fld.Default = dNoEQ("CURRENT_TIMESTAMP")
				elif fld.DataType == "Binary":
					if fld.Size <= 255:
						sql = sql + "TINYBLOB "
					elif fld.Size <= 65535:
						sql = sql + "BLOB "
					elif fld.Size <= 16777215:
						sql = sql + "MEDIUMBLOB "
					elif fld.Size <= 4294967295:
						sql = sql + "LONGBLOB "
					else:
						raise #what should happen?
				
				if fld.IsPK:
					sql = sql + "PRIMARY KEY "
					pks.append(fld.Name)
					if fld.IsAutoIncrement:
						sql = sql + "AUTO_INCREMENT "
				
				if not fld.AllowNulls:
					sql = sql + "NOT NULL "
				if not fld.IsPK:
					sql = "%sDEFAULT %s," % (sql, self.formatForQuery(fld.Default))
				else:
					sql = sql + ","
				
				if sql.count("PRIMARY KEY ") > 1:
					sql = sql.replace("PRIMARY KEY ","") + "PRIMARY KEY(" + ",".join(pks) + "),"
				
			if sql[-1:] == ",":
				sql = sql[:-1]
			sql = sql + ")"
			
			try:
				cursor.execute(sql)
			except dException.DBNoAccessException:
				toExc.append(sql)
	
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
				
				if toExc == []:
					try:
						cursor.execute(sql)
					except dException.DBNoAccessException:
						toExc.append(sql)
				else:
					toExc.append(sql)

		if toExc != []:
			return toExc
