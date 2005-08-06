from dBackend import dBackend
import datetime

class MySQL(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "MySQLdb"
		# Are we using a version of MySQL that supports transactions?
		self.useTransactions = False

	def getConnection(self, connectInfo):
		import MySQLdb as dbapi

		port = connectInfo.Port
		if not port:
			port = 3306
				
		self._connection = dbapi.connect(host=connectInfo.Host, 
				user = connectInfo.User,
				passwd = connectInfo.revealPW(),
				db=connectInfo.DbName,
				port=port)

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
		tempCursor = self._connection.cursor()
		tempCursor.execute("describe %s" % tableName)
		rs = tempCursor.fetchall()
		fldDesc = tempCursor.description
		# The field name is the first element of the tuple. Find the
		# first entry with the field name 'Key'; that will be the 
		# position for the PK flag
		for i in range(len(fldDesc)):
			if fldDesc[i][0] == 'Key':
				pkPos = i
				break
		
		fields = []
		for r in rs:
			name = r[0]
			ft = r[1]
			if ft.split()[0] == "tinyint(1)":
				ft = "B"
			elif "int" in ft:
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
			elif "decimal" in ft:
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
		
	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		if self.useTransactions:
			cursor.execute("BEGIN")

	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		if self.useTransactions:
			cursor.execute("COMMIT")

	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		if self.useTransactions:
			cursor.execute("ROLLBACK")

	def getWordMatchFormat(self):
		""" MySQL's fulltext search expression
		"""
		return """ match (%(field)s) against ("%(value)s") """
