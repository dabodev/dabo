''' dabo.db.backend.py : abstractions for the various db api's '''

class Backend(object):
    ''' Abstract object: inherit from this to define new dabo db interfaces '''
    
    def __init__(self):
        object.__init__(self)
        self.dbModuleName = None
    
    def isValidModule(self):
        ''' Test the dbapi to see if it is supported on this
            computer. 
        '''
        try:
            exec("import %s as dbapi" % self.dbModuleName)
            return True
        except ImportError:
            return False
    
    def getConnection(self, connectInfo):
        ''' override in subclasses '''
        return None        

    def getDictCursor(self):
        ''' override in subclasses '''
        return None

class MySQL(Backend):
    def __init__(self):
        Backend.__init__(self)
        self.dbModuleName = "MySQLdb"
                
    def getConnection(self, connectInfo):
        import MySQLdb as dbapi
        
        return dbapi.connect(host=connectInfo.host, 
                             user=connectInfo.user,
                             passwd=connectInfo.password,
                             db=connectInfo.dbName)

    def getDictCursor(self):
        import MySQLdb.cursors as cursors
        return cursors.DictCursor
