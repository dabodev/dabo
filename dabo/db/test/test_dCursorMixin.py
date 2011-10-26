# -*- coding: utf-8 -*-
import unittest
import dabo
from dabo.lib import getRandomUUID


# Testing anything other than sqlite requires network access. So set these
# flags so that only the db's you want to test against are True.
db_tests = {"sqlite": True,
		"mysql": False,
		"firebird": False,
		"postgresql": False,
		"mssql": False,
		"oracle": False}

# Convert the flags into class references. Setting to object will keep the tests
# for that backend from running.
#for k, v in db_tests.iteritems():
#	if v:
#		db_tests[k] = unittest.TestCase
#	else:
#		db_tests[k] = object



class Test_dCursorMixin(object):
	def setUp(self, _doRequery=True):
		cur = self.cur
		self.createSchema()
		cur.UserSQL = "select * from %s" % self.temp_table_name
		cur.KeyField = "pk"
		cur.Table = self.temp_table_name
		if _doRequery:
			cur.requery()

	def tearDown(self):
		self.cur = None

	def createSchema(self):
		"""Create the test schema. Override in subclasses."""
		cur = self.cur

	def getAdditionalWhere(self):
		return ""

	## - Begin property unit tests -
	def test_AutoSQL(self):
		cur = self.cur
		self.assertEqual(cur.AutoSQL, "select *\n  from %s\n limit 1000" % self.temp_table_name)

	def test_AutoPopulatePK(self):
		cur = self.cur
		self.assertEqual(cur.AutoPopulatePK, True)
		cur.AutoPopulatePK = False
		self.assertEqual(cur.AutoPopulatePK, False)

	def test_AuxCursor(self):
		cur = self.cur
		self.assertTrue(isinstance(cur.AuxCursor, dabo.db.dCursorMixin))

	def test_BackendObject(self):
		cur = self.cur
		self.assertTrue(isinstance(cur.BackendObject, dabo.db.dBackend.dBackend))

	def test_CurrentSQL(self):
		cur = self.cur
		self.assertEqual(cur.CurrentSQL, cur.UserSQL)

	def test_DataStructure(self):
		ds = self.cur.DataStructure
		self.assertTrue(ds[0] == ("pk", "I", True, self.temp_table_name, "pk", None)
				or ds[0] == ("pk", "G", True, self.temp_table_name, "pk", None))
		self.assertEqual(ds[1], ("cfield", "C", False, self.temp_table_name, "cfield", None))
		self.assertTrue(ds[2] == ("ifield", "I", False, self.temp_table_name, "ifield", None)
				or ds[2] == ("ifield", "G", False, self.temp_table_name, "ifield", None))
		self.assertEqual(ds[3], ("nfield", "N", False, self.temp_table_name, "nfield", None))

	def test_Encoding(self):
		cur = self.cur
		self.assertEqual(cur.Encoding, "utf-8")
		cur.Encoding = "latin-1"
		self.assertEqual(cur.Encoding, "latin-1")

	def test_FieldDescription(self):
		# The field description will vary depending on the backend, but according to
		# the dbapi2 it should always be a tuple of 7-tuples, with the field name
		# as the first element.
		cur = self.cur
		self.assertEqual(cur.FieldDescription[0][0], "pk")
		self.assertEqual(cur.FieldDescription[1][0], "cfield")
		self.assertEqual(cur.FieldDescription[2][0], "ifield")
		self.assertEqual(cur.FieldDescription[3][0], "nfield")

	def test_IsAdding(self):
		cur = self.cur
		self.assertEqual(cur.IsAdding, False)
		cur.new()
		cur.genTempAutoPK()
		cur.setNewFlag()
		self.assertEqual(cur.IsAdding, True)
		cur.first()
		self.assertEqual(cur.IsAdding, False)

	def test_LastSQL(self):
		cur = self.cur
		current_sql = cur.UserSQL
		cur.UserSQL = "select blah from temp"
		self.assertEqual(cur.UserSQL, "select blah from temp")
		self.assertEqual(cur.LastSQL, current_sql)

	def test_KeyField(self):
		cur = self.cur
		self.assertEqual(cur.KeyField, "pk")

	def test_Record(self):
		cur = self.cur
		self.assertEqual(cur.Record.cfield.rstrip(), "Paul Keith McNett")
		cur.Record.cfield = "Denise McNett"
		self.assertEqual(cur.Record.cfield, "Denise McNett")
		self.assertEqual(cur._mementos[cur.Record.pk]["cfield"].rstrip(), "Paul Keith McNett")
		cur.Record.cfield = "Alison Anton"
		self.assertEqual(cur.Record.cfield, "Alison Anton")
		self.assertEqual(cur._mementos[cur.Record.pk]["cfield"].rstrip(), "Paul Keith McNett")
		cur.setFieldVal("ifield", 80)
		self.assertEqual(cur.Record.ifield, 80)
		self.assertTrue(isinstance(cur.Record.ifield, (int, long)))
		self.assertEqual(cur._mementos[self.cur.Record.pk]["ifield"], 23)

		# Querying or setting a field that doesn't exist should raise
		# dException.FieldNotFoundException:
		def testGetRecord():
			return cur.Record.nonExistingFieldName
		def testSetRecord():
			cur.Record.nonExistingFieldName = "ppp"
		self.assertRaises(dabo.dException.FieldNotFoundException, testGetRecord)
		self.assertRaises(dabo.dException.FieldNotFoundException, testSetRecord)


	def test_RowCount(self):
		cur = self.cur
		self.assertEqual(cur.RowCount, 3)
		cur.delete()
		self.assertEqual(cur.RowCount, 2)
		cur.new()
		self.assertEqual(cur.RowCount, 3)


	def test_RowNumber(self):
		cur = self.cur
		self.assertEqual(cur.RowNumber, 0)
		cur.next()
		self.assertEqual(cur.RowNumber, 1)
		cur.moveToRowNum(2)
		self.assertEqual(cur.RowNumber, 2)
		cur.moveToPK(1)
		self.assertEqual(cur.RowNumber, 0)

	def test_Table(self):
		cur = self.cur
		self.assertEqual(cur.Table, self.temp_table_name)

	def test_UserSQL(self):
		cur = self.cur
		testSQL = "select * from %s where nfield = 23.23" % self.temp_table_name
		addWhere = self.getAdditionalWhere()
		if addWhere:
			testSQL += " AND %s" % addWhere
		cur.UserSQL = testSQL
		cur.requery()
		self.assertEqual(cur.LastSQL, cur.UserSQL)
		self.assertEqual(cur.UserSQL, testSQL)
		self.assertEqual(cur.RowCount, 1)
		self.assertEqual(cur.RowNumber, 0)
		self.assertEqual(cur.Record.cfield.rstrip(), "Paul Keith McNett")

	## - End property unit tests -

	## - Begin method unit tests -

	def test_oldVal(self):
		cur = self.cur
		self.assertEqual(cur.oldVal("cfield"), cur.Record.cfield)
		self.assertEqual(cur.oldVal("cfield", 1), cur.getFieldVal("cfield", 1))
		oldVal = cur.Record.cfield
		newVal = "pkm23"
		cur.Record.cfield = newVal
		self.assertEqual(cur.oldVal("cfield"), oldVal)
		self.assertEqual(cur.Record.cfield, newVal)
		self.assertRaises(dabo.dException.FieldNotFoundException, cur.oldVal, "bogusField")

	## - End method unit tests -

	def testMementos(self):
		cur = self.cur
		# With a new requery, mementos and new records should be empty.
		self.assertEqual(cur._mementos, {})
		self.assertEqual(cur._newRecords, {})

		priorVal = cur.Record.cfield
		# Make a change that is the same as the prior value:
		cur.Record.cfield = priorVal
		self.assertEqual(priorVal, cur.Record.cfield)
		self.assertEqual(cur._mementos, {})
		self.assertEqual(cur._newRecords, {})

		# Make a change that is different:
		cur.Record.cfield = "New test value"
		self.assertEqual(cur._mementos, {cur.Record.pk: {"cfield": priorVal}})
		self.assertEqual(cur.isChanged(), True)
		self.assertEqual(cur.isChanged(allRows=False), True)

		# Change it back:
		cur.Record.cfield = priorVal
		self.assertEqual(cur._mementos, {})
		self.assertEqual(cur.isChanged(), False)
		self.assertEqual(cur.isChanged(allRows=False), False)

		# Make a change that is different and cancel:
		cur.Record.cfield = "New test value"
		cur.cancel()
		self.assertEqual(cur._mementos, {})
		self.assertEqual(cur.isChanged(), False)
		self.assertEqual(cur.isChanged(allRows=False), False)

		# Add a record:
		cur.new()

		# The following 2 calls are normally done in dBizobj.new():
		cur.genTempAutoPK()
		cur.setNewFlag()

		self.assertEqual(cur.RowCount, 4)
		self.assertEqual(cur.RowNumber, 3)
		self.assertEqual(cur._newRecords, {-1: None})
		self.assertEqual(cur.isChanged(), False)  ## (because no field changed in new record)
		self.assertEqual(cur.isChanged(allRows=False), False)
		self.assertEqual(cur.Record.pk, -1)
		self.assertEqual(cur.Record.cfield, "")
		self.assertEqual(cur.Record.ifield, 0)
		self.assertEqual(cur.Record.nfield, 0)
		cur.save()
		self.assertEqual(cur.RowCount, 4)
		cur.requery()
		self.assertEqual(cur.RowCount, 3)
		self.assertEqual(cur.RowNumber, 2)
		self.assertEqual(cur._newRecords, {})
		self.assertEqual(cur.isChanged(), False)
		self.assertEqual(cur.isChanged(allRows=False), False)


	def testNullRecord(self):
		cur = self.cur
		self.createNullRecord()
		cur.requery()
		self.assertEqual(cur.RowCount, 4)
		cur.last()
		self.assertEqual(cur.RowNumber, 3)
		self.assertTrue("cur.Record.cfield is None")
		self.assertTrue("cur.Record.ifield is None")
		self.assertTrue("cur.Record.nfield is None")

	def test_new(self):
		cur = self.cur
		cur.new()
		self.assertEqual(cur.Record.cfield, "")
		self.assertEqual(cur.Record.ifield, 0)
		self.assertEqual(cur.Record.nfield, 0)


class Test_dCursorMixin_sqlite(Test_dCursorMixin, unittest.TestCase):
	def setUp(self):
		con = dabo.db.dConnection(DbType="SQLite", Database=":memory:")
		self.cur = con.getDaboCursor()
		self.temp_table_name = "unittest%s" % getRandomUUID().replace("-", "")[-17:]
		super(Test_dCursorMixin_sqlite, self).setUp()

	def createSchema(self):
		cur = self.cur
		tableName = self.temp_table_name
		cur.executescript("""
create table %s (pk INTEGER PRIMARY KEY AUTOINCREMENT, cfield CHAR, ifield INT, nfield DECIMAL (8,2));
insert into %s (cfield, ifield, nfield) values ("Paul Keith McNett", 23, 23.23);
insert into %s (cfield, ifield, nfield) values ("Edward Leafe", 42, 42.42);
insert into %s (cfield, ifield, nfield) values ("Carl Karsten", 10223, 23032.76);
""" % (tableName, tableName, tableName, tableName, ))

	def createNullRecord(self):
		self.cur.AuxCursor.execute("""
insert into %s (cfield, ifield, nfield) values (NULL, NULL, NULL)
""" % self.temp_table_name)


class Test_dCursorMixin_mysql(Test_dCursorMixin, unittest.TestCase):
	def setUp(self):
		con = dabo.db.dConnection(DbType="MySQL", User="dabo_unittest",
				password="T30T35DB4K30Z45I67N60", Database="dabo_unittest",
				Host="paulmcnett.com")
		self.cur = con.getDaboCursor()
		self.temp_table_name = "unittest%s" % getRandomUUID().replace("-", "")[-17:]
		super(Test_dCursorMixin_mysql, self).setUp()

	def tearDown(self):
		self.cur.execute("drop table %s" % self.temp_table_name)
		super(Test_dCursorMixin_mysql, self).tearDown()

	def createSchema(self):
		cur = self.cur
		cur.execute("""
create table %s (pk INTEGER PRIMARY KEY AUTO_INCREMENT, cfield CHAR (32), ifield INT, nfield DECIMAL (8,2))
""" % self.temp_table_name)
		cur.execute("""
insert into %s (cfield, ifield, nfield) values ("Paul Keith McNett", 23, 23.23)
""" % self.temp_table_name)
		cur.execute("""
insert into %s (cfield, ifield, nfield) values ("Edward Leafe", 42, 42.42)
""" % self.temp_table_name)
		cur.execute("""
insert into %s (cfield, ifield, nfield) values ("Carl Karsten", 10223, 23032.76)
""" % self.temp_table_name)

	def createNullRecord(self):
		self.cur.AuxCursor.execute("""
insert into %s (cfield, ifield, nfield) values (NULL, NULL, NULL)
""" % self.temp_table_name)


class Test_dCursorMixin_oracle(Test_dCursorMixin, unittest.TestCase):
	def setUp(self):
		con = dabo.db.dConnection(DbType="Oracle", User="fwadm",
				password="V7EE74E49H6BV27TA0J65G2AS21", Database="XE",
				Host="athlon28")
		self.cur = con.getDaboCursor()
		self.temp_table_name = "unittest%s" % getRandomUUID().replace("-", "")[-17:]
		super(Test_dCursorMixin_oracle, self).setUp()

	def tearDown(self):
		self.cur.execute("drop table %s" % self.temp_table_name)
		super(Test_dCursorMixin_mysql, self).tearDown()

	def createSchema(self):
		cur = self.cur
		cur.execute("""
create table %s (pk INTEGER PRIMARY KEY, cfield CHAR (32), ifield INT, nfield DECIMAL (8,2))
""" % self.temp_table_name)
		cur.execute("""
insert into %s (cfield, ifield, nfield) values ("Paul Keith McNett", 23, 23.23)
""" % self.temp_table_name)
		cur.execute("""
insert into %s (cfield, ifield, nfield) values ("Edward Leafe", 42, 42.42)
""" % self.temp_table_name)
		cur.execute("""
insert into %s (cfield, ifield, nfield) values ("Carl Karsten", 10223, 23032.76)
""" % self.temp_table_name)

	def createNullRecord(self):
		self.cur.AuxCursor.execute("""
insert into %s (cfield, ifield, nfield) values (NULL, NULL, NULL)
""" % self.temp_table_name)


class Test_dCursorMixin_firebird(Test_dCursorMixin, unittest.TestCase):
	## NOTE: Firebird not set up completely yet. What is here is courtesy Uwe
	##		 Grauer. We need insert statements, and we need a firebird server.
	##		 I intend to set up a test server, but don't know when it will
	##		 actually occur.
	def setUp(self):
		con = dabo.db.dConnection(DbType="Firebird", User="dabotester",
				password="Y57W8EN6CB06KBCCDCX01D6B", Database="dabo_unittest",
				Host="dabodev.com")
		cur = self.cur = con.getDaboCursor()
		self.temp_table_name = "dabo_unittest_tbl"
		self.jobid = self.get_jobid()
		super(Test_dCursorMixin_firebird, self).setUp(_doRequery=False)
		cur.UserSQL = "select * from %s where jobid = %s" % (self.temp_table_name, self.jobid)
		cur.requery()

	def get_jobid(self):
		ret = None
		self.cur.execute("select gen_id(gen_jobid, 1) as nextval from rdb$database")
		ret = self.cur.getFieldVal("nextval")
		return ret

	def tearDown(self):
		self.cur.execute("commit")
		self.cur.execute("delete from %s where jobid = %f" % (self.temp_table_name, self.jobid))
		self.cur.execute("commit")
		super(Test_dCursorMixin_firebird, self).tearDown()

	def getAdditionalWhere(self):
		return "jobid = %f" % self.jobid

	def createSchema(self):
		cur = self.cur
		tableName = self.temp_table_name

		cur.execute("commit")
		cur.execute("""
insert into %s (jobid, cfield, ifield, nfield) values (%f, 'Paul Keith McNett', 23, 23.23)
""" % (tableName, self.jobid))
		cur.execute("""
insert into %s (jobid, cfield, ifield, nfield) values (%f, 'Edward Leafe', 42, 42.42)
""" % (tableName, self.jobid))
		cur.execute("""
insert into %s (jobid, cfield, ifield, nfield) values (%f, 'Carl Karsten', 10223, 23032.76)
""" % (tableName, self.jobid))
		cur.execute("commit")

	def createNullRecord(self):
		self.cur.AuxCursor.execute("""
insert into %s (jobid, cfield, ifield, nfield) values (%f, NULL, NULL, NULL)
""" % (self.temp_table_name, self.jobid))

	def test_AutoSQL(self):
		cur = self.cur
		self.assertEqual(cur.AutoSQL, "SELECT \n first 1000\n*\n  from %s\n\n\n"
				% self.temp_table_name)


if __name__ == "__main__":
	testClasses = []
	mapping = {"sqlite": Test_dCursorMixin_sqlite,
			"mysql": Test_dCursorMixin_mysql,
			"firebird": Test_dCursorMixin_firebird,
			"oracle": Test_dCursorMixin_oracle}
	for k, v in db_tests.items():
		if v:
			testClasses.append(mapping[k])
	for t in testClasses:
		suite = unittest.TestLoader().loadTestsFromTestCase(t)
		unittest.TextTestRunner(verbosity=2).run(suite)
