import dabo.common
from dConnectInfo import dConnectInfo
from dCursorMixin import dCursorMixin

class dConnection(dabo.common.dObject):
	""" Hold a connection to a backend database. 
	"""
	def __init__(self, connectInfo, parent=None):
		self._baseClass = dConnection
		# Store a reference to the parent object (bizobj maybe; app 
		# object connection collection most likely)
		self.Parent = parent

		if isinstance(connectInfo, dConnectInfo):
			self._connectInfo = connectInfo
		else:
			# If they passed a cnxml file, or a dict containing 
			# valid connection info, this will work fine. Otherwise,
			# an error will be raised in the dConnectInfo class.
			self._connectInfo = dConnectInfo(connInfo=connectInfo)
		self._connection = self._openConnection()
		
		
	def getConnection(self):
		return self._connection

	def getDictCursorClass(self):
		return self._connectInfo.getDictCursorClass()
		
	def getCursor(self, cursorClass):
		return self.getBackendObject().getCursor(cursorClass)
	
	def getDaboCursor(self, cursorClass=None):
		""" Accepts a backend-specific cursor class, mixes in the Dabo
		dCursorMixin class, and returns the result.
		"""
		if cursorClass is None:
			cursorClass = self.getDictCursorClass()
		class DaboCursor(dCursorMixin, cursorClass):
			superMixin = dCursorMixin
			superCursor = cursorClass
			def __init__(self, *args, **kwargs):
				if hasattr(dCursorMixin, "__init__"):
					apply(dCursorMixin.__init__,(self,) + args, kwargs)
				if hasattr(cursorClass, "__init__"):
					apply(cursorClass.__init__,(self,) + args, kwargs)
		
		bo = self.getBackendObject()
		crs = bo.getCursor(DaboCursor)
		crs.setBackendObject(bo)
		return crs


	def _openConnection(self):
		""" Open a connection to the database and store it for future use. """
		return self._connectInfo.getConnection()
	
	def getBackendObject(self):
		""" Return a reference to the connectInfo's backend-specific
		database object.
		"""
		return self._connectInfo.getBackendObject()


if __name__ == "__main__":
	from dConnectInfo import dConnectInfo
	ci = dConnectInfo("MySQL")
	ci.Host = "paulmcnett.com"
	ci.DbName = "house"
	ci.User = "dabo"
	ci.Password = ci.encrypt("dabo")

	conn = dConnection(ci).getConnection()
	cursor = conn.cursor()
	print cursor.execute("select * from addressbook order by iid limit 10") 
	for row in cursor.fetchall():
		print row[0], row[1]

