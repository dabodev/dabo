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
			return
		# Store a reference to the bizobj that created this
		self.parent = parent
		self._dbType = dbType
		self._openConnection()
	
	
# 	def __del__(self):
# 		self._conn.close()
	
	def getConnection(self):
		return self._conn
		
	
	def _openConnection(self):
		""" Open a connection to the database, and store it for future use. """
		# For testing only! Should be made more generic for all db types
		from connstring import getConnVals
		import MySQLdb
		connstring = """self._conn = MySQLdb.connect(host="%s", user="%s", passwd="%s", db="%s")""" % getConnVals() 
		
		try:
			exec(connstring)
		except:
			self._conn = None
	