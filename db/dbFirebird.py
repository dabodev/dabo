from dBackend import dBackend
import datetime

class Firebird(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "Firebird"

	def getConnection(self, connectInfo):
		import kinterbasdb as dbapi

		port = connectInfo.Port
		if not port:
			port = 3050

		return dbapi.connect(host=connectInfo.Host, 
							user=connectInfo.User,
							passwd=connectInfo.Password,
							db=connectInfo.DbName,
							port=port)

	def getDictCursor(self):
		return None
#		## TO DO 
# 		import MySQLdb.cursors as cursors
# 		return cursors.DictCursor

	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
		
	def getLastInsertID(self, cursor):
		return None
#		## TO DO 
# 		cursor.execute("select last_insert_id() as newid")
# 		ret = cursor._rows[0]["newid"]
# 		return ret

	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		cursor.execute("SET TRANSACTION")

	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		cursor.execute("COMMIT")

	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		cursor.execute("ROLLBACK")
