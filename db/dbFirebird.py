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
		
		return kinterbasdb.connect(host=host, user=user, password=password, database=database)

	def getDictCursor(self):
		import kinterbasdb
		return kinterbasdb.Cursor

	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
		
	def getLastInsertID(self, cursor):
		return None
#		## TO DO 

	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		cursor.execute("SET TRANSACTION")

	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		cursor.execute("COMMIT")

	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		cursor.execute("ROLLBACK")
