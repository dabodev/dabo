from dBackend import dBackend
import datetime

class Sqlite(dBackend):
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "sqlite"

	def getConnection(self, connectInfo):
		return None
#		## TO DO 
# 		import sqlite as dbapi
# 
# 		return dbapi.connect(host=connectInfo.Host, 
# 							user=connectInfo.User,
# 							passwd=connectInfo.Password,
# 							db=connectInfo.DbName)

	def getDictCursor(self):
		return None
#		## TO DO 
# 		import dbapi.cursors as cursors
# 		return cursors.DictCursor

	def formatDateTime(self, val):
		""" We need to wrap the value in quotes. """
		sqt = "'"		# single quote
		return "%s%s%s" % (sqt, str(val), sqt)
		
	def getLastInsertID(self, cursor):
		return None
#		## TO DO 

	def beginTransaction(self, cursor):
		""" Begin a SQL transaction."""
		pass
#		## TO DO 
# 		cursor.execute("BEGIN TRANSACTION")

	def commitTransaction(self, cursor):
		""" Commit a SQL transaction."""
		pass
#		## TO DO 
# 		cursor.execute("COMMIT TRANSACTION")

	def rollbackTransaction(self, cursor):
		""" Roll back (revert) a SQL transaction."""
		pass
#		## TO DO 
# 		cursor.execute("ROLLBACK TRANSACTION")
