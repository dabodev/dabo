import dabo.common

class dConnection(dabo.common.dObject):
	""" Hold a connection to a backend database. 
	"""
	def __init__(self, connectInfo, parent=None):
		self._baseClass = dConnection
		# Store a reference to the parent object (bizobj maybe; app 
		# object connection collection most likely)
		self.Parent = parent

		self._connectInfo = connectInfo
		self._connection = self._openConnection()
		
		
	def getConnection(self):
		return self._connection

	def getDictCursor(self):
		return self._connectInfo.getDictCursor()

	def _openConnection(self):
		""" Open a connection to the database and store it for future use. """
		return self._connectInfo.getConnection()
	
	def _getBackendObject(self):
		""" Return a reference to the connectInfo's backend-specific
		database object.
		"""
		return self._connectInfo.BackendObject
	
	BackendObject = property(_getBackendObject, None, None,
			"Reference to the backend-specific object")

if __name__ == "__main__":
	from dConnectInfo import dConnectInfo
	ci = dConnectInfo("MySQL")
	ci.host = "paulmcnett.com"
	ci.dbName = "house"
	ci.user = "dabo"
	ci.password = "dabo"

	conn = dConnection(ci).getConnection()
	cursor = conn.cursor()
	print cursor.execute("select * from addressbook order by iid limit 10") 
	for row in cursor.fetchall():
		print row[0], row[1]

