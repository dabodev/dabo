import dBackend

class dConnectInfo(object):
	""" Holder for the properties for connecting to the backend.

	Each backend may have different names for properties, but this object
	tries to abstract that.

		ci = ConnectInfo('MySQL')
		ci.host = 'domain.com'
		ci.user = 'dabo'
		ci.password = 'dabo'
	"""
	def __init__(self, backendName=None, host=None, user=None, 
					password=None, dbName=None, port=None):

		self.setBackendName(backendName)
		self.setHost(host)
		self.setUser(user)
		self.setPassword(password)
		self.setDbName(dbName)
		self.setPort(port)

	def getConnection(self):
		return self._backendObject.getConnection(self)

	def getDictCursor(self):
		try:
			return self._backendObject.getDictCursor()
		except TypeError:
			return None

	def getBackendName(self): 
		return self._backendName

	def setBackendName(self, backendName):
		""" Set the backend type for the connection.

		Only sets the backend name if valid.
		"""
		try:
			backendObject = eval("dBackend.%s()" % backendName)
			self._backendName = backendName
			self._backendObject = backendObject
		except:
			self._backendName = None
			self._backendObject = None

	def getBackendObject(self):
		return self._backendObject

	def getHost(self): 
		return self._host

	def setHost(self, host): 
		self._host = host

	def getUser(self): 
		return self._user

	def setUser(self, user): 
		self._user = user

	def getPassword(self): 
		return self._password

	def setPassword(self, password): 
		self._password = password

	def getDbName(self): 
		return self._dbName

	def setDbName(self, dbName): 
		self._dbName = dbName

	def getPort(self): 
		return self._port

	def setPort(self, port): 
		self._port = port

	BackendName = property(getBackendName, setBackendName)
	Host = property(getHost, setHost)
	User = property(getUser, setUser)
	Password = property(getPassword, setPassword)
	DbName = property(getDbName, setDbName)
	BackendObject = property(getBackendObject)
	Port = property(getPort, setPort)

if __name__ == '__main__':
	test = dConnectInfo()
	print test.backendName
	test.backendName = "MySQL"
	print test.backendName
	test.backendName = "mssql"
	print test.backendName

