import dabo.common
import random
from dabo.dLocalize import _

class dConnectInfo(dabo.common.dObject):
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
		self._baseClass = dConnectInfo
		#dConnectInfo.doDefault(self)
		super(dConnectInfo, self).__init__()
		self.BackendName = backendName
		self.Host = host
		self.User = user
		self.Password = password
		self.DbName = dbName
		self.Port = port
		
		
	def getConnection(self):
		return self.BackendObject.getConnection(self)

	def getDictCursorClass(self):
		try:
			return self.BackendObject.getDictCursorClass()
		except TypeError:
			return None
	
	
	def encrypt(self, val):
		tc = TinyCrypt(self.generateKey(val))
		return tc.encrypt(val)
		

	def generateKey(self, s):
		chars = []
		for i in range(len(s)):
			chars.append(chr(65 + random.randrange(26)))
		return "".join(chars)
	

	def decrypt(self, val):
		tc = TinyCrypt("".join([val[i] for i in range(0, len(val), 3)]))
		return tc.decrypt("".join([val[i+1:i+3] for i in range(0, len(val), 3)]))
	
	
	def revealPW(self):
		return self.decrypt(self.Password)
	

	def _getBackendName(self): 
		try:
			return self._backendName
		except AttributeError:
			return None

			
	def _setBackendName(self, backendName):
		""" Set the backend type for the connection if valid. 
		"""
		
		_oldObject = self.BackendObject
		
		# As other backends are coded into the framework, we will need 
		# to expand the if/elif list.
		if backendName is not None:
			# Evaluate each type of backend
			nm = backendName.lower()
			if nm == "mysql":
				import dbMySQL
				self._backendObject = dbMySQL.MySQL()
			elif nm == "gadfly":
				import dbGadfly
				self._backendObject = dbGadfly.Gadfly()
			elif nm == "sqlite":
				import dbSqlite
				self._backendObject = dbSqlite.Sqlite()
			elif nm == "firebird":
				import dbFirebird
				self._backendObject = dbFirebird.Firebird()
			elif nm == "postgres":
				import dbPostgreSQL
				self._backendObject = dbPostgreSQL.Postgres()
			else:
				raise ValueError, "Invalid backend name: %s." % nm
				
			if _oldObject != self.BackendObject:
				self._backendName = nm
				
		else:
			self._backendName = None
			self._backendObject = None

			
	def _getBackendObject(self):
		try:
			o = self._backendObject
		except AttributeError:
			o, self._backendObject = None, None
		return o

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

	def _getDbName(self): 
		return self._dbName

	def _setDbName(self, dbName): 
		self._dbName = dbName

	def _getPort(self): 
		return self._port

	def _setPort(self, port): 
		self._port = port

	BackendName = property(_getBackendName, _setBackendName)
	Host = property(_getHost, _setHost, None, 
			'The host name or ip address. (str)')
	User = property(_getUser, _setUser, None,
			'The user name. (str)')
	Password = property(_getPassword, _setPassword, None,
			'The password of the user. (str)')
	DbName = property(_getDbName, _setDbName, None,
			'The database name to login to. (str)')
	BackendObject = property(_getBackendObject, None, None,
			'The object reference to the database api. (obj)')
	Port = property(_getPort, _setPort, None, 
			'The port to connect on (may not be applicable for all databases). (int)')


class TinyCrypt:
	""" Simple class that handles basic encryption/decryption for 
	this script.
	
	Thanks to Raymond Hettinger for this code, originally found on
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/266586
	"""
	def __init__(self, aKey):
		self.__key = aKey
		self.rng = random.Random(aKey)
		self.rand = self.rng.randrange

	def encrypt(self, aString):
		crypted = [chr(ord(elem)^self.rand(256)) for elem in aString]
		hex = self.strToHex("".join(crypted))
		ret = "".join([self.__key[i/2]  + hex[i:i+2] for i in range(0, len(hex), 2)])
		return ret
		
	def decrypt(self, aString):
		aString = self.hexToStr(aString)
		decrypted = [chr(ord(elem)^self.rand(256)) for elem in aString]
		return "".join(decrypted)
		
	def strToHex(self, aString):
		hexlist = ["%02X" % ord(x) for x in aString]
		return ''.join(hexlist)
	
	def hexToStr(self, aString):
		# Break the string into 2-character chunks
		try:
			chunks = [chr(int(aString[i] + aString[i+1], 16)) 
					for i in range(0, len(aString), 2)]
		except:
			raise ValueError, _("Incorrectly-encrypted password")
		return "".join(chunks)
		
	
		
if __name__ == '__main__':
	test = dConnectInfo()
	print test.backendName
	test.backendName = "MySQL"
	print test.backendName
#	test.backendName = "mssql"
#	print test.backendName

