''' db.py 

    Main script of the dabo.db module
    
'''

import dbConnectInfo

class Db(object):
    def __init__(self):
        object.__init__(self)
        self._cachedConnection = None
        self.connectInfo = dbConnectInfo.DbConnectInfo()            
                
    def dbConnect(self):
        if self._cachedConnection == None:
            self._cachedConnection = self.connectInfo.getConnection()
        return self._cachedConnection

    def dbRecordSet(self, sql, *params):	
        return self.dbConnect()(sql, *params)

    def dbCommand(self, sql, *params):
        self.dbConnect().cursor().execute(sql, params)

    def dbInsert(self, sql, *params):
        # execute the passed command, and return the last_insert_id():
        # Need to make this generic - currently, only works with MySQL...
        self.dbConnect().cursor().execute(sql, params)
        return self.dbConnect()("select last_insert_id() as iid")[0].iid

