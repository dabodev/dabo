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
		
	def getLastInsertID(self):
		return None
#		## TO DO 
# 		self.__saveProps()
# 		self.execute("select last_insert_id() as newid")
# 		ret = self._rows[0]["newid"]
# 		self.__restoreProps()
# 		return ret

	def beginTransaction(self):
		""" Begin a SQL transaction."""
		pass
#		## TO DO 
# 		self.__saveProps()
# 		self.execute("BEGIN TRANSACTION")
# 		self.__restoreProps()

	def commitTransaction(self):
		""" Commit a SQL transaction."""
		pass
#		## TO DO 
# 		self.__saveProps()
# 		self.execute("COMMIT TRANSACTION")
# 		self.__restoreProps()

	def rollbackTransaction(self):
		""" Roll back (revert) a SQL transaction."""
		pass
#		## TO DO 
# 		self.__saveProps()
# 		self.execute("ROLLBACK TRANSACTION")
# 		self.__restoreProps()
