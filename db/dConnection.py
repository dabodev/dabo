
class dConnection(object):
    ''' Hold a connection to a backend database. '''
    
    ###### TODO: change default to gadfly so that this works without
    ######   having to install a database.
    
    def __init__(self, parent=None, connectInfo):
        
        # Store a reference to the object (bizobj most likely)
        # that created this
        self.bizObj = bizObj
        self._connectInfo = connectInfo
        self._connection = self._openConnection()

    def getConnection(self):
        return self._connection

    def _openConnection(self):
        ''' Open a connection to the database and store it for future use. '''
        # For testing only! Should be made more generic for all db types
#        from connstring import getConnVals
#        import MySQLdb
#         connstring = """self._conn = MySQLdb.connect(host="%s", user="%s", passwd="%s", db="%s")""" % getConnVals() 
# 
#         try:
#             exec(connstring)
#         except:
#             self._conn = None

        return connection