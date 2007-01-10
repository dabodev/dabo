import unittest
import dabo
from dabo.lib import getRandomUUID


class Test_dBizobj(object):
	def setUp(self):
		biz = self.biz
		self.temp_table_name = "unittest%s" % getRandomUUID().replace("-", "")[-20:]
		self.createSchema()
		biz.UserSQL = "select * from %s" % self.temp_table_name
		biz.KeyField = "pk"
		biz.DataSource = self.temp_table_name
		biz.requery()

	def tearDown(self):
		self.biz = None

	def createSchema(self):
		"""Create the test schema. Override in subclasses."""
		pass


	## - Begin property unit tests -
	def test_AutoCommit(self):
		biz = self.biz
		self.assertEqual(biz.AutoCommit, False)
		biz.AutoCommit = True
		self.assertEqual(biz.AutoCommit, True)

	def test_AutoSQL(self):
		biz = self.biz
		self.assertEqual(biz.AutoSQL, "select *\n  from %s\n limit 1000" % self.temp_table_name)

	def test_AutoPopulatePK(self):
		biz = self.biz
		self.assertEqual(biz.AutoPopulatePK, True)
		biz.AutoPopulatePK = False
		self.assertEqual(biz.AutoPopulatePK, False)

	def test_CurrentSQL(self):
		biz = self.biz
		self.assertEqual(biz.CurrentSQL, biz.UserSQL)

	def test_DataSource(self):
		biz = self.biz
		self.assertEqual(biz.DataSource, self.temp_table_name)

	def test_DataStructure(self):
		ds = self.biz.DataStructure
		self.assertTrue(ds[0] == ("pk", "I", True, self.temp_table_name, "pk", None)
				or ds[0] == ("pk", "G", True, self.temp_table_name, "pk", None))
		self.assertEqual(ds[1], ("cField", "C", False, self.temp_table_name, "cField", None))
		self.assertTrue(ds[2] == ("iField", "I", False, self.temp_table_name, "iField", None)
				or ds[2] == ("iField", "G", False, self.temp_table_name, "iField", None))
		self.assertEqual(ds[3], ("nField", "N", False, self.temp_table_name, "nField", None))

	def test_Encoding(self):
		biz = self.biz
		self.assertEqual(biz.Encoding, "utf-8")
		biz.Encoding = "latin-1"
		self.assertEqual(biz.Encoding, "latin-1")

	def test_IsAdding(self):
		biz = self.biz
		self.assertEqual(biz.IsAdding, False)
		biz.new()
		self.assertEqual(biz.IsAdding, True)
		biz.first()
		self.assertEqual(biz.IsAdding, False)

	def test_LastSQL(self):
		biz = self.biz
		self.assertEqual(biz.LastSQL, biz.UserSQL)

	def test_KeyField(self):
		biz = self.biz
		self.assertEqual(biz.KeyField, "pk")

	def test_Record(self):
		biz = self.biz
		cur = biz._CurrentCursor
		self.assertEqual(biz.Record.cField, "Paul Keith McNett")
		biz.Record.cField = "Denise McNett"
		self.assertEqual(biz.Record.cField, "Denise McNett")
		biz.Record.cField = "Alison Anton"
		self.assertEqual(biz.Record.cField, "Alison Anton")
		biz.setFieldVal("iField", 80)
		self.assertEqual(biz.Record.iField, 80)
		self.assertTrue(isinstance(biz.Record.iField, (int, long)))

	def test_RowCount(self):
		biz = self.biz
		self.assertEqual(biz.RowCount, 3)
		biz.delete()
		self.assertEqual(biz.RowCount, 2)
		biz.new()
		self.assertEqual(biz.RowCount, 3)
		

	def test_RowNumber(self):
		biz = self.biz
		self.assertEqual(biz.RowNumber, 0)
		biz.next()
		self.assertEqual(biz.RowNumber, 1)
		biz.RowNumber = 2
		self.assertEqual(biz.RowNumber, 2)
		biz.first()
		self.assertEqual(biz.RowNumber, 0)

	def test_UserSQL(self):
		biz = self.biz
		testSQL = "select * from %s where nField = 23.23" % self.temp_table_name
		biz.UserSQL = testSQL
		biz.requery()
		self.assertEqual(biz.LastSQL, biz.UserSQL)
		self.assertEqual(biz.UserSQL, testSQL)
		self.assertEqual(biz.RowCount, 1)
		self.assertEqual(biz.RowNumber, 0)
		self.assertEqual(biz.Record.cField, "Paul Keith McNett")

	## - End property unit tests -


class Test_dBizobj_sqlite(Test_dBizobj, unittest.TestCase):
	def setUp(self):
		con = dabo.db.dConnection(DbType="SQLite", Database=":memory:")
		self.biz = dabo.biz.dBizobj(con)
		super(Test_dBizobj_sqlite, self).setUp()

	def createSchema(self):
		biz = self.biz
		tableName = self.temp_table_name
		biz._CurrentCursor.executescript("""
create table %s (pk INTEGER PRIMARY KEY AUTOINCREMENT, cField CHAR, iField INT, nField DECIMAL (8,2));
insert into %s (cField, iField, nField) values ("Paul Keith McNett", 23, 23.23);
insert into %s (cField, iField, nField) values ("Edward Leafe", 42, 42.42);
insert into %s (cField, iField, nField) values ("Carl Karsten", 10223, 23032.76);
""" % (tableName, tableName, tableName, tableName, ))


class Test_dBizobj_mysql(Test_dBizobj):
	def setUp(self):
		con = dabo.db.dConnection(DbType="MySQL", User="dabo_unittest", 
				password="T30T35DB4K30Z45I67N60", Database="dabo_unittest",
				Host="paulmcnett.com")
		self.biz = dabo.biz.dBizobj(con)
		super(Test_dBizobj_mysql, self).setUp()

	def tearDown(self):
		self.biz._CurrentCursor.execute("drop table %s" % self.temp_table_name)
		super(Test_dBizobj_mysql, self).tearDown()

	def createSchema(self):
		biz = self.biz
		cur = biz._CurrentCursor
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
