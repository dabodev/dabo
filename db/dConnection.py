
class dConnection(object):
    ''' Hold a connection to a backend database. '''
    
    def __init__(self, connectInfo, parent=None):
        # Store a reference to the parent object (bizobj maybe; app 
        # object connection collection most likely)
        self.parent = parent
        
        self._connectInfo = connectInfo
        self._connection = self._openConnection()

    def getConnection(self):
        return self._connection

    def _openConnection(self):
        ''' Open a connection to the database and store it for future use. '''
        return self._connectInfo.getConnection()

if __name__ == "__main__":
    from connectInfo import ConnectInfo
    ci = ConnectInfo('MySQL')
    ci.host = 'paulmcnett.com'
    ci.dbName = "house"
    ci.user = 'dabo'
    ci.password = 'dabo'

    conn = dConnection(ci).getConnection()
    cursor = conn.cursor()
    print cursor.execute("select * from addressbook order by iid limit 10") 
    for row in cursor.fetchall():
      print row[0], row[1]
   
