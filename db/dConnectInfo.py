import dabo.common
import random
from dabo.dLocalize import _

class dConnectInfo(dabo.common.dObject):
	""" Holder for the properties for connecting to the backend. Each 
	backend may have different names for properties, but this object
	tries to abstract that. The value stored in the Password must be 
	encrypted in the format set in the app. This class has  'encrypt' and
	'decrypt' functions for doing this, or you can set the PlainTextPassword
	property, and the class will encypt that value and set the Password
	property for you.
	
	You can create it in several ways, like most Dabo objects. First, you 
	can pass all the settings as parameters to the constructor:
	
		ci = dConnectInfo(DbType="MySQL", Host="domain.com",
			User="daboUser", PlainTextPassword="secret", Port=3306,
			Database="myData")
			
	Or you can create a dictionary of the various props, and pass that
	in the 'connInfo' parameter:
	
		connDict = {"DbType" : "MySQL", "Host" : "domain.com",
			"User" : "daboUser", "PlainTextPassword" : "secret", 
			"Port" : 3306, "Database" : "myData"}
		ci = dConnectInfo(connInfo=connDict)
		
	Or, finally, you can create the object and then set the props
	individually:

		ci = dConnectInfo()
		ci.DbType = "MySQL"
		ci.Host = "domain.com"
		ci.User = "daboUser"
		ci.PlainTextPassword = "secret"
		ci.Database = "myData"
	"""
	def __init__(self, connInfo=None, **kwargs):
		self._baseClass = dConnectInfo
		self._backendObject = None
		self._host = self._user = self._password = self._dbType = self._database = self._port = ""
		super(dConnectInfo, self).__init__(**kwargs)
		if connInfo:	
			self.setConnInfo(connInfo)

	
	def lowerKeys(self, dct):
		"""Takes a dict, and returns another dict identical except
		for the fact that all the keys that were string types are now 
		lower case.
		"""
		ret = {}
		for kk, vv in dct.items():
			if isinstance(kk, basestring):
				kk = kk.lower()
			ret[kk] = vv
		return ret
		
		
	def setConnInfo(self, connInfo, nm=""):
		if isinstance(connInfo, dict):
			# The info is already in dict format
			connDict = self.lowerKeys(connInfo)
		else:
			# They've passed the info in XML format. Either this is the actual
			# XML, or it is a path to the XML file. Either way, the parser
			# will handle it.
			cd = dabo.common.connParser.importConnections(connInfo)
			# There may be multiple connections in this file. If they passed a 
			# name, use that connection; otherwise, use the first.
			try:
				connDict = cd[nm]
			except:
				nm = cd.keys()[0]
				connDict = cd[nm]
		
		# They passed a dictionary containing the connection settings
		if connDict.has_key("dbtype"):
			self.DbType = connDict["dbtype"]
		if connDict.has_key("host"):
			self.Host = connDict["host"]
		if connDict.has_key("user"):
			self.User = connDict["user"]
		if connDict.has_key("password"):
			self.Password = connDict["password"]
		if connDict.has_key("plaintextpassword"):
			self.PlainTextPassword = connDict["plaintextpassword"]
		if connDict.has_key("database"):
			self.Database = connDict["database"]
		if connDict.has_key("port"):
			try:
				self.Port = int(connDict["port"])
			except ValueError:
				# No valid port given
				self.Port = None
	
	
	def getConnection(self):
		return self._backendObject.getConnection(self)

	def getDictCursorClass(self):
		try:
			return self._backendObject.getDictCursorClass()
		except TypeError:
			return None
		

	def encrypt(self, val):
		if self.Application:
			return self.Application.encrypt(val)
		else:
			cryp = dabo.common.SimpleCrypt()
			return cryp.encrypt(val)

	def decrypt(self, val):
		if self.Application:
			return self.Application.decrypt(val)
		else:
			cryp = dabo.common.SimpleCrypt()
			return cryp.decrypt(val)
	
	
	def revealPW(self):
		return self.decrypt(self.Password)
	
	
	def getBackendObject(self):
		return self._backendObject

	def _getDbType(self): 
		try:
			return self._dbType
		except AttributeError:
			return None
	def _setDbType(self, dbType):
		""" Set the backend type for the connection if valid. """
		_oldObject = self._backendObject
		# As other backends are coded into the framework, we will need 
		# to expand the if/elif list.
		if dbType is not None:
			# Evaluate each type of backend
			nm = dbType.lower()
			if nm == "mysql":
				import dbMySQL
				self._backendObject = dbMySQL.MySQL()
			elif nm == "gadfly":
				import dbGadfly
				self._backendObject = dbGadfly.Gadfly()
			elif nm == "sqlite":
				import dbSQLite
				self._backendObject = dbSQLite.SQLite()
			elif nm == "firebird":
				import dbFirebird
				self._backendObject = dbFirebird.Firebird()
			elif nm == "postgresql":
				import dbPostgreSQL
				self._backendObject = dbPostgreSQL.Postgres()
			else:
				raise ValueError, "Invalid database type: %s." % nm
			if _oldObject != self._backendObject:
				self._dbType = dbType
		else:
			self._dbType = None
			self._backendObject = None

	def _getDatabase(self): 
		return self._database
	def _setDatabase(self, database): 
		self._database = database
			
	def _getHost(self):
		return self._host
	def _setHost(self, host): 
		self._host = host

	def _getUser(self): 
		return self._user
	def _setUser(self, user): 
		self._user = user

	def _getPassword(self): 
		return self._password
	def _setPassword(self, password): 
		self._password = password

	def _setPlainPassword(self, val): 
		self._password = self.encrypt(val)

	def _getPort(self): 
		return self._port
	def _setPort(self, port): 
		self._port = port


	DbType = property(_getDbType, _setDbType, None,
			_("Name of the backend database type.  (str)"))
	Database = property(_getDatabase, _setDatabase, None,
			_("The database name to login to. (str)"))
	Host = property(_getHost, _setHost, None, 
			_("The host name or ip address. (str)"))
	Password = property(_getPassword, _setPassword, None,
			_("The encrypted password of the user. (str)"))
	PlainTextPassword = property(None, _setPlainPassword, None,
			_("""Write-only property that encrypts the value and stores that
				in the Password property. (str)"""))
	Port = property(_getPort, _setPort, None, 
			_("The port to connect on (may not be applicable for all databases). (int)"))
	User = property(_getUser, _setUser, None,
			_("The user name. (str)"))


if __name__ == "__main__":
	test = dConnectInfo()
	print test.DbType
	test.DbType = "MySQL"
	print test.DbType
	test.DbType = "SQLite"
	print test.DbType

