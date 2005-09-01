import datetime
import dabo.db
import dabo.biz

class CiTest(dabo.db.dConnectInfo):
	def initProperties(self):
		self.DbType = "MySQL"
		self.Host = "paulmcnett.com"
		self.Database = "dabotest"
		self.User = "dabo"
		self.Port = 3306
		self.Password = "Y38Z11XA2Z5F"


class BizTest(dabo.biz.dBizobj):
	def initProperties(self):
		self.DataSource = "test"
		self.KeyField = "id"

	def afterInit(self):
		self.defaultValues = {"timestamp": datetime.datetime.utcnow}
		self.setBaseSQL()
		
	def setBaseSQL(self):
		self.addFrom("test")
		self.addField("test.id as id")
		self.addField("test.comment as comment")
		self.addField("test.timestamp as timestamp")

print "\nNew Record problem in dBizobj/dCursor\n"
conn = dabo.db.dConnection(CiTest())
biz = BizTest(conn)
comment = "trial one: requery the bizobj with a limit of 0 records, and add a record."
print comment
biz.setLimitClause("0")
biz.requery()
biz.new()
biz.comment = comment[:9]
biz.save()


comment = "trial two: requery the bizobj with a limit of 1 records, and add a record"
print comment
biz.setLimitClause("1")
biz.requery()
biz.new()
biz.comment = comment[:9]
biz.save()

# Retrieve our test records:
sql = """
select * 
  from test 
 order by id desc
 limit 2"""

biz.UserSQL = sql
biz.requery()

print "\nNow, we'll retrieve the two records we added. Note that only the second one has a value in comment.\n"
print "Id, Timetamp, Comment:"
for r in biz.getDataSet():
	print r["id"], r["timestamp"], r["comment"]

print "\n"
