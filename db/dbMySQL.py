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

		return dbapi.connect(host=connectInfo.Host, 
							user=connectInfo.User,
							passwd=connectInfo.Password,
							db=connectInfo.DbName,
							port=port)

	def getDictCursor(self):
		import MySQLdb.cursors as cursors
		return cursors.DictCursor

	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
		
	def getLastInsertID(self, cursor):
		cursor.execute("select last_insert_id() as newid")
		ret = cursor._records[0]["newid"]
		return ret

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
