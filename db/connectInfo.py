import backend

class ConnectInfo(object):
    ''' Holder for the properties for connecting to the backend 
    
        ci = ConnectInfo('MySQL')
        ci.host = 'domain.com'
        ci.user = 'dabo'
        ci.password = 'dabo'
        
    '''
    
    def __init__(self, backendName=None, host=None, user=None, 
                    password=None, dbName=None, port=None):
        
        self.setBackendName(backendName)
        self.setHost(host)
        self.setUser(user)
        self.setPassword(password)
        self.setDbName(dbName)
        self.setPort(port)

    def getConnection(self):
        try:
            return self._backendObject.getConnection(self)
        except TypeError:
            return None

    def getDictCursor(self):
        try:
            return self._backendObject.getDictCursor()
        except TypeError:
            return None
        
    def getBackendName(self): 
        return self._backendName
    
    def setBackendName(self, backendName):
        ''' Only set the backend name if valid,
            and also set self._backendObject to  
            the correct backend instance.
        '''
        try:
            backendObject = eval("backend.%s()" % backendName)
        except AttributeError:
            return
        if backendObject.isValidModule():
            self._backendName = backendName
            self._backendObject = backendObject
    
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
    
    backendName = property(getBackendName, setBackendName)
    host = property(getHost, setHost)
    user = property(getUser, setUser)
    password = property(getPassword, setPassword)
    dbName = property(getDbName, setDbName)
    backendObject = property(getBackendObject)
    port = property(getPort, setPort)
    
if __name__ == '__main__':
    test = ConnectInfo()
    print test.backendName
    test.backendName = "MySQL"
    print test.backendName
    test.backendName = "mssql"
    print test.backendName
    
