from dConnection import dConnection
from dabo.biz.dBizobj import dBizobj
import dabo.dConstants as k


class bizZip(dBizobj):
	dataSource = "zipcodes"
	keyField = "iid"
	sql = "select * from zipcodes where ccity like '%s%%' "
	defaultValues = {"ccity":"PenfieldCopy", "cStateProv":"NY", "czip":"14526"}
	noDataOnLoad = True


class bizCust(dBizobj):
	dataSource = "customer"
	keyField = "iid"
	sql = "select iid, city, company from customer where company like %s "
	noDataOnLoad = True
	deleteChildLogic = k.REFINTEG_CASCADE
	autoPopulatePK = True

class bizOrders(dBizobj):
	dataSource = "orders"
	keyField = "order_id"
	sql = """select order_id, cust_id, order_date, order_amt, order_dsc 
	from orders where cust_id = %s """
	noDataOnLoad = True
	linkField = "cust_id"
	fillLinkFromParent = True
	autoPopulatePK = False
	
	def getParams(self):
		return (self.getParentPK(), )



def openConn():
	cn = dConnection("foo")
	return cn



def getBiz():
	cn = openConn().getConnection()
	biz = bizZip(cn)
	return biz
	

def main():
	cn = openConn().getConnection()
	cbiz = bizCust(cn, True)
	obiz = bizOrders(cn, True)
	cbiz.addChild(obiz)
	
	cbiz.setParams('B%')
	cbiz.requery()
	
#  	cbiz.new()
#  	vals = {'cust_id': 'FORBU', 'city': 'Hackensack', 'fax': '', 'dabo-newrec': 1, 'title': 'Wow', \
#  		'country': 'USA', 'company': 'Fearless Forbush Industries', \
#  		'maxordamt': 321.88, 'phone': '', 'contact': '', 'cust_id': 'FORBU', \
#  		'address': '212 Wilson St.', 'postalcode': '07601', 'region': ''}
#  	for kk,vv in vals.items():
#  		cbiz.setFieldVal(kk,vv)
	
	return cbiz
			
	
	# breaking point 
	x=1


if __name__ == "__main__":
	main()
	
