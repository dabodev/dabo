''' bizZip.py : add to this to test the biz object. Currently, it makes a 
    connection to Ed's webtest db. Either 'python bizZip.py' or open an
    interactive Python session and 'import bizZip'. 
'''
from dabo.db.dConnection import dConnection
from dabo.biz import dBiz

class bizZip(dBiz):
    dataSource = "zipcodes"
    keyField = "iid"
    sql = "select * from zipcodes where ccity like 'penf%' "
    defaultValues = {"ccity":"Penfield", "cStateProv":"NY", "czip":"14526"}

def getConnInfo():
    from dabo.db.connectInfo import ConnectInfo
    ci = ConnectInfo('MySQL')
    ci.host = 'leafe.com'
    ci.dbName = "webtest"
    ci.user = 'test'
    ci.password = 'test3'
    return ci

def openConn():
    return dConnection(getConnInfo())
    
def getBiz():
    biz = bizZip(openConn())
    print biz
    return biz

if __name__ == "__main__":
    biz = getBiz()
    print biz.getFieldVal("czip"), biz.getFieldVal("ccounty")
    biz.next()
    print biz.getFieldVal("czip"), biz.getFieldVal("ccounty")
