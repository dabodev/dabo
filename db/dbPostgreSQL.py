from dBackend import dBackend
import datetime

class MySQL(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "PostgreSQLdb"
		self.useTransactions = True

	def getConnection(self, connectInfo):
		### TODO: what connector should we use?
		#import MySQLdb as dbapi

		port = connectInfo.Port
		if not port:
			### TODO: what port does PostgreSQL use?
			#port = 3306
				
		### TODO: Is this the correct syntax for creating the connection?
		self._connection = dbapi.connect(host=connectInfo.Host, 
				user = connectInfo.User,
				passwd = connectInfo.revealPW(),
				db=connectInfo.DbName,
				port=port)

		return self._connection

	def getDictCursorClass(self):
		### TODO: If PostgreSQL doesn't offer specific Dict cursors, 
		###   return a plain one, and Dabo will convert it.
		#import MySQLdb.cursors as cursors
		#return cursors.DictCursor

	def escQuote(self, val):
		### TODO: This method needs to escape any 'dangerous' characters,
		###   and properly enclose a string value in quotes.
		# escape backslashes and single quotes, and
		# wrap the result in single quotes
		sl = "\\"
		qt = "\'"
		return qt + val.replace(sl, sl+sl).replace(qt, sl+qt) + qt
	
	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		### TODO:  How does PostgreSQL handle date-time values?
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
		
	def getTables(self, includeSystemTables=False):
		# MySQL doesn't have system tables, in the traditional sense, as 
		# they exist in the mysql database.
		tempCursor = self._connection.cursor()
		### TODO: Verify that this is the correct syntax
		tempCursor.execute("show tables")
		rs = tempCursor.fetchall()
		tables = []
		for record in rs:
			tables.append(record[0])
		return tuple(tables)
		
	def getTableRecordCount(self, tableName):
		tempCursor = self._connection.cursor()
		### TODO: Verify syntax
		tempCursor.execute("select count(*) as ncount from %s" % tableName)
		return tempCursor.fetchall()[0][0]

	def getFields(self, tableName):
		tempCursor = self._connection.cursor()
		### TODO: Verify syntax
		tempCursor.execute("describe %s" % tableName)
		rs = tempCursor.fetchall()
		
		fields = []
		### TODO: Verify the field type names returned.
		for r in rs:
			name = r[0]
			fldType = r[1]
			if 'int' in fldType:
				fldType = 'I'
			elif 'char' in fldType :
				fldType = 'C'
			elif 'longtext' in fldType:
				fldType = 'M'
			elif 'decimal' in fldType:
				fldType = 'N'
			elif 'datetime' in fldType:
				fldType = 'T'
			elif 'date' in fldType:
				fldType = 'D'
			else:
				fldType = "?"
			pk = (r[3] == 'PRI')
			
			fields.append((name.strip(), fldType, pk))
			
		return tuple(fields)
		
	### TODO: Customize these for PostgreSQL syntax.

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
