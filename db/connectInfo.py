import dbType

class DbConnectInfo(object):
    ''' Holder for the properties for connecting to the backend 
    
        ci = ConnectInfo('MySQL')
        ci.host = 'paulmcnett.com'
        ci.user = 'dabo'
        ci.password = 'dabo'
        
    '''
    
    def __init__(self, dbTypeName=None, host=None, user=None, 
                    password=None, dbName=None):
        self._dbTypeName = dbTypeName
        self._host = host
        self._user = user
        self._password = password
        self._dbName = None
        
        self._dbTypeObject = None

    def getConnection(self):
        try:
            return self._dbTypeObject.getConnection(self)
        except TypeError:
            return None
            
    def getDbTypeName(self): 
        return self._dbTypeName
    
    def setDbTypeName(self, dbTypeName):
        ''' Only set the db type name if valid,
            and also set self._dbTypeObject to  
            the correct type instance.
        '''
        import dbType
        try:
            dbTypeObject = eval("dbType.%s()" % dbTypeName)
        except AttributeError:
            return
        if dbTypeObject.isValidModule():
            self._dbTypeName = dbTypeName
            self._dbTypeObject = dbTypeObject
    
    def getDbTypeObject(self):
        return self._dbTypeObject
            
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
        
    dbTypeName = property(getDbTypeName, setDbTypeName)
    host = property(getHost, setHost)
    user = property(getUser, setUser)
    password = property(getPassword, setPassword)
    dbName = property(getDbName, setDbName)
    dbTypeObject = property(getDbTypeObject)
    
if __name__ == '__main__':
    test = ConnectInfo()
    print test.dbTypeName
    test.dbTypeName = "MySQL"
    print test.dbTypeName
    test.dbTypeName = "mssql"
    print test.dbTypeName
    
