from dConstants import dConstants as k

class dConnection:
	"""
	Designed to be created by dabo to guarantee that a connection to the 
	database is made and available to create the necessary cursors.
	"""
	_conn = None
	
	###### TODO: change default to gadfly so that this works without
	######   having to install a database.
	def __init__(self, parent, dbType="MySQL"):
		# Reference to the database connection
		if not parent:
			# Should raise an error. For now, just bail
			return 0
		# Store a reference to the bizobj that created this
		self.parent = parent
		self._dbType = dbType
		if conn is None:
			self._conn = self._openConnection()
		else:
			self._conn = conn
		
		return (self.conn is not None)
	
	
	def __del__(self):
		self._conn.close()
	
	def getConnection(self):
		return self._conn
		
	
	def _openConnection(self):
		""" Open a connection to the database, and store it for future use. """
		# For testing only! Should be made more generic for all db types
		from connstring import getConnVals
		connstring = """MySQLdb.connect(host="%s", user="%s", passwd="%s", db="%s")""" % getConnVals() 
		
		try:
			conn = eval(connstring)
		except:
			conn = None
		return conn
