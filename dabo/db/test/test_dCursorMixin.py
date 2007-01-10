import unittest
import dabo
from dabo.lib import getRandomUUID


# Testing anything other than sqlite requires network access. So set these
# flags so that only the db's you want to test against are True.
test_sqlite = True
test_mysql = True

if test_sqlite:
	sqlite_unittest = unittest.TestCase
else:
	sqlite_unittest = object

if test_mysql:
	mysql_unittest = unittest.TestCase
else:
	mysql_unittest = object


class Test_dCursorMixin(object):
	def setUp(self):
		cur = self.cur
		self.temp_table_name = "unittest%s" % getRandomUUID().replace("-", "")[-20:]
		self.createSchema()
		cur.UserSQL = "select * from %s" % self.temp_table_name
		cur.KeyField = "pk"
		cur.Table = self.temp_table_name
		cur.requery()

	def createSchema(self):
		"""Create the test schema. Override in subclasses."""
		pass

	def testRowCount(self):
		self.assertEqual(self.cur.RowCount, 3)

	def testRecordGetValue(self):
		self.assertEqual(self.cur.Record.cField, "Paul Keith McNett")

	def test_DataStructure(self):
		ds = self.cur.DataStructure
		self.assertTrue(ds[0] == ("pk", "I", True, self.temp_table_name, "pk", None)
				or ds[0] == ("pk", "G", True, self.temp_table_name, "pk", None))
		self.assertEqual(ds[1], ("cField", "C", False, self.temp_table_name, "cField", None))
		self.assertTrue(ds[2] == ("iField", "I", False, self.temp_table_name, "iField", None)
				or ds[2] == ("iField", "G", False, self.temp_table_name, "iField", None))
		self.assertEqual(ds[3], ("nField", "N", False, self.temp_table_name, "nField", None))


class Test_dCursorMixin_sqlite(Test_dCursorMixin, sqlite_unittest):
	def setUp(self):
		con = dabo.db.dConnection(DbType="SQLite", Database=":memory:")
		self.cur = con.getDaboCursor()
		super(Test_dCursorMixin_sqlite, self).setUp()

	def createSchema(self):
		cur = self.cur
		tableName = self.temp_table_name
		cur.executescript("""
create table %s (pk INTEGER PRIMARY KEY AUTOINCREMENT, cField CHAR, iField INT, nField DECIMAL (8,2));
insert into %s (cField, iField, nField) values ("Paul Keith McNett", 23, 23.23);
insert into %s (cField, iField, nField) values ("Edward Leafe", 42, 42.42);
insert into %s (cField, iField, nField) values ("Carl Karsten", 10223, 23032.76);
""" % (tableName, tableName, tableName, tableName, ))


class Test_dCursorMixin_mysql(Test_dCursorMixin, mysql_unittest):
	def setUp(self):
		con = dabo.db.dConnection(DbType="MySQL", User="dabo_unittest", 
				password="T30T35DB4K30Z45I67N60", Database="dabo_unittest",
				Host="paulmcnett.com")
		self.cur = con.getDaboCursor()
		super(Test_dCursorMixin_mysql, self).setUp()

	def tearDown(self):
		self.cur.execute("drop table %s" % self.temp_table_name)
		super(Test_dCursorMixin_mysql, self).tearDown()

	def createSchema(self):
		cur = self.cur
		cur.execute("""
create table %s (pk INTEGER PRIMARY KEY AUTO_INCREMENT, cField CHAR (32), iField INT, nField DECIMAL (8,2))
""" % self.temp_table_name)
		cur.execute("""		
insert into %s (cField, iField, nField) values ("Paul Keith McNett", 23, 23.23)
""" % self.temp_table_name)
		cur.execute("""		
insert into %s (cField, iField, nField) values ("Edward Leafe", 42, 42.42)
""" % self.temp_table_name)
		cur.execute("""		
insert into %s (cField, iField, nField) values ("Carl Karsten", 10223, 23032.76)
""" % self.temp_table_name)


if __name__ == "__main__":
	unittest.main()
