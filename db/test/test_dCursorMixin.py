import unittest
import dabo



class Test_dCursorMixin(object):
	def setUp(self):
		cur = self.cur
		cur.UserSQL = "select * from test"
		cur.KeyField = "pk"
		cur.Table = "test"
		cur.requery()

	def createSchema(self):
		"""Create the test schema. Override in subclasses."""
		pass

	def testRowCount(self):
		self.assertEqual(self.cur.RowCount, 3)

	def testRecordGetValue(self):
		self.assertEqual(self.cur.Record.cField, "Paul Keith McNett")

	def testDataStructure(self):
		ds = self.cur.DataStructure
		self.assertEqual(ds[0], ("pk", "I", True, "test", "pk", None))
		self.assertEqual(ds[1], ("cField", "C", False, "test", "cField", None))


class Test_dCursorMixin_sqlite(Test_dCursorMixin, unittest.TestCase):
	def setUp(self):
		con = dabo.db.dConnection(DbType="SQLite", Database=":memory:")
		self.cur = con.getDaboCursor()
		self.createSchema()
		super(Test_dCursorMixin_sqlite, self).setUp()

	def createSchema(self):
		"""Creates the test database schema for the tests."""
		cur = self.cur
		cur.executescript("""
create table test (pk INTEGER PRIMARY KEY AUTOINCREMENT, cField CHAR, iField INT, nField DECIMAL (8,2));
insert into test (cField, iField, nField) values ("Paul Keith McNett", 23, 23.23);
insert into test (cField, iField, nField) values ("Edward Leafe", 42, 42.42);
insert into test (cField, iField, nField) values ("Carl Karsten", 10223, 23032.76);""")

	def tearDown(self):
		self.cur = None

if __name__ == "__main__":
	unittest.main()
