from dBackend import dBackend
import datetime

class Sqlite(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "sqlite"

		
	def getConnection(self, connectInfo):
		return None
 		import sqlite as dbapi
 		
		# sqlite databases are local, either completely in memory
		# or a local file. Whatever gets passed as the db parameter
		# will be used as the database, whether it already exists
		# or not. Pass ":memory" for an in-memory database with no
		# disk presence at all.
 		return dbapi.connect(db=connectInfo.DbName)

		
	def getDictCursorClass(self):
		return None
#		## TO DO 
# 		import dbapi.cursors as cursors
# 		return cursors.DictCursor


	def getCursor(self, cursorClass):
		return self._connection.cursor()

		
	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
		
		
	def getLastInsertID(self, cursor):
		cursor.execute("select last_insert_rowid() as lastid")
		return cursor.fetchall()[0][0]

		
	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
 		cursor.execute("BEGIN")

	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
 		cursor.execute("COMMIT")

	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
 		cursor.execute("ROLLBACK")
