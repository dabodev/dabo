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
		
	def getLastInsertID(self):
		self.__saveProps()
		self.execute("select last_insert_id() as newid")
		ret = self._rows[0]["newid"]
		self.__restoreProps()
		return ret

	def beginTransaction(self):
		""" Begin a SQL transaction."""
		if self.useTransactions:
			self.__saveProps()
			self.execute("BEGIN")
			self.__restoreProps()

	def commitTransaction(self):
		""" Commit a SQL transaction."""
		if self.useTransactions:
			self.__saveProps()
			self.execute("COMMIT")
			self.__restoreProps()

	def rollbackTransaction(self):
		""" Roll back (revert) a SQL transaction."""
		if self.useTransactions:
			self.__saveProps()
			self.execute("ROLLBACK")
			self.__restoreProps()
