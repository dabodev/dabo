import dbConnection

class DbType(object):
    ''' Abstract object: inherit from this to define new dabo db interfaces '''
    
    def __init__(self):
        object.__init__(self)
        exec("import %s as dbapi" % self.dbModuleName)
        self.dbapi = dbapi
    
    def isValidModule(self):
        ''' Test the dbapi to see if it is supported on this
            computer. Currently, the only checking is to see
            if the named module imports or not. 
        '''
        try:
            exec("import %s as dbapi" % self.dbModuleName)
            return True
        except ImportError:
            return False
    
    def getConnection(self, connectInfo):
        ''' override this in subclasses '''
        return None        

class MySQL(DbType):
    def __init__(self):
        self.dbModuleName = "MySQLdb"
        DbType.__init__(self)
                
    def getConnection(self, connectInfo):
        return dbConnection.DbConnection(self.dbapi.connect, 
                                        host=connectInfo.host, 
                                        user=connectInfo.user,
                                        passwd=connectInfo.password,
                                        db=connectInfo.db)
        
