from dBackend import dBackend
import datetime

class Firebird(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "kinterbasdb"

	def getConnection(self, connectInfo):
		import kinterbasdb

		# Port doesn't seem to work, but I need to research... for now it's disabled.
# 		port = connectInfo.Port
# 		if not port:
# 			port = 3050

		# kinterbasdb will barf with unicode strings:
		host = str(connectInfo.Host)
		user = str(connectInfo.User)
		password = str(connectInfo.Password)
		database = str(connectInfo.DbName)
		
		self._connection = kinterbasdb.connect(host=host, user=user, password=password,
				database=database)
		
		return self._connection
		
	def getDictCursorClass(self):
		import kinterbasdb
		return kinterbasdb.Cursor

	def getCursor(self, cursorClass):
		return self._connection.cursor()

	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)

	def getTables(self, includeSystemTables=False):
		if includeSystemTables:
			whereClause = ''
		else:
			whereClause = "where rdb$relation_name not like 'RDB$%' "
			
		tempCursor = self._connection.cursor()
		tempCursor.execute("select rdb$relation_name from rdb$relations "
			"%s order by rdb$relation_name" % whereClause)
		rs = tempCursor.fetchall()
		tables = []
		for record in rs:
			tables.append(record[0].strip())
		return tuple(tables)
		
	def getTableRecordCount(self, tableName):
		tempCursor = self._connection.cursor()
		tempCursor.execute("select count(*) as ncount from %s where 1=1" % tableName)
		return tempCursor.fetchall()[0][0]

	def getFields(self, tableName):
		tempCursor = self._connection.cursor()
		tempCursor.execute("select rdb$field_name from rdb$relation_fields "
			"where rdb$relation_name = '%s'" % tableName)
		rs = tempCursor.fetchall()
		
		# This isn't fully implemented yet. You'll get the field names but not
		# the field types or whether the field is a pk or not.
		fields = []
		for r in rs:
			name = r[0]
			ft = "?"
			pk = False
			
			fields.append((name.strip(), ft, pk))
			
		return tuple(fields)
	
	def getLastInsertID(self, cursor):
		# This doesn't work - it'll return None. TODO: figure out what to do.
		return self.doDefault(cursor)

	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		cursor.execute("SET TRANSACTION")

	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		cursor.execute("COMMIT")

	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		cursor.execute("ROLLBACK")
