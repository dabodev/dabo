from dabo.dLocalize import _
import dBackend

class Gadfly(dBackend):
	""" Single-use version of Gadfly: specify a directory and 
		database. The directory should probably be on the local
		computer.
	"""
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "gadfly"

	def getConnection(self, connectInfo):
		import gadfly as dbapi
		return dbapi.gadfly(connectInfo.dbName, connectInfo.host)

	def getCursor(self, cursorClass):
		""" Not tested! Replace with actual Gadfly code """
		return self._connection.cursor()


class GadflyClient(dBackend):
	""" Network client version of Gadfly: connect to a Gadfly server.
		This is suitable for multiple users.
	"""
	def __init__(self):
		dBackend.__init__(self)
		self.dbModuleName = "gfclient"

	def getConnection(self, connectInfo):
		import gadfly.client as dbapi

		port = connectInfo.port
		if not port:
			port = "2222"

		return dbapi.gfclient(connectInfo.user, 
							port, 
							connectInfo.revealPW(),
							connectInfo.host)

							
