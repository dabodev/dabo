''' bizZip.py : add to this to test the biz object. Currently, it makes a 
    connection to Ed's webtest db. Either 'python bizZip.py' or open an
    interactive Python session and 'import bizZip'. 
'''
from dabo.db.dConnection import dConnection
from dabo.biz import dBizobj

class bizZip(dBizobj):
    dataSource = "zipcodes"
    keyField = "iid"
    sql = "select * from zipcodes where ccity like 'penf%' "
    defaultValues = {"ccity":"Penfield", "cStateProv":"NY", "czip":"14526"}

def getConnInfo():
    from dabo.db.dConnectInfo import dConnectInfo
    ci = dConnectInfo('MySQL')
    ci.host = 'leafe.com'
    ci.dbName = "webtest"
    ci.user = 'test'
    ci.password = 'test3'
    return ci

def openConn():
    return dConnection(getConnInfo())
    
def getBiz():
    biz = bizZip(openConn())
    return biz

if __name__ == "__main__":
    biz = getBiz()
    print biz
    print "Rowcount: %s" % biz.getRowCount()
    print biz.getFieldVal("czip"), biz.getFieldVal("ccounty")
    print biz.next()
    print biz.getFieldVal("czip"), biz.getFieldVal("ccounty")
    print biz.next()
    print biz.getFieldVal("czip"), biz.getFieldVal("county")
    print biz.next()
    print biz.getFieldVal("czip"), biz.getFieldVal("county")
