import datetime
try:
	import decimal
except ImportError:
	decimal = None
from dabo.dLocalize import _
from dBackend import dBackend

class MySQL(dBackend):
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

		self._connection = dbapi.connect(host=connectInfo.Host, 
				user = connectInfo.User,
				passwd = connectInfo.revealPW(),
				db=connectInfo.Database,
				port=port, **kwargs)
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
		tempCursor.execute("select count(*) as ncount from %s" % tableName)
		return tempCursor.fetchall()[0][0]


	def getFields(self, tableName):
		if not tableName:
			return tuple()
		tempCursor = self._connection.cursor()
		tempCursor.execute("describe %s" % tableName)
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
			if ft.split()[0] == "tinyint(1)":
				ft = "B"
			elif "int" in ft or ft == "long":
				ft = "I"
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
			elif "decimal" in ft or "float" in ft:
				ft = "N"
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
		
		daboMapping = {"BLOB": "M",
				"CHAR": "C",
				"DATE": "D",
				"DATETIME": "T",
				"DECIMAL": "N",
				"DOUBLE": "I",
				"ENUM": "C",
				"FLOAT": "N",
				"GEOMETRY": "?",
				"INT24": "I",
				"INTERVAL": "?",
				"LONG": "I",
				"LONGLONG": "I",
				"LONG_BLOB": "M",
				"MEDIUM_BLOB": "M",
				"NEWDATE": "?",
				"NULL": "?",
				"SET": "?",
				"SHORT": "I",
				"STRING": "C",
				"TIME": "?",
				"TIMESTAMP": "?",
				"TINY": "I",
				"TINY_BLOB": "M",
				"VAR_STRING": "C",
				"YEAR": "?"}
		return daboMapping[typeMapping[backendFieldType]]


	def getWordMatchFormat(self):
		""" MySQL's fulltext search expression"""
		return """ match (%(field)s) against ("%(value)s") """


	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		if not cursor.AutoCommit:
			if hasattr(cursor.connection, "begin"):
				cursor.connection.begin()
			else:
				cursor.execute("BEGIN")
				

		
