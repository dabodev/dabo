# -*- coding: utf-8 -*-
import unittest
import dabo
from dabo.lib import getRandomUUID


class Test_dForm(unittest.TestCase):
	def setUp(self):
		# We set up a test connection to an in-memory sqlite database, and then we
		# make a dBizobj against the test table, and then we create a dForm with some
		# dTextBox's to test the interaction.
		self.con = dabo.db.dConnection(DbType="SQLite", Database=":memory:")
		biz = self.biz = dabo.biz.dBizobj(self.con)
		uniqueName = getRandomUUID().replace("-", "")[-20:]
		self.temp_table_name = "unittest%s" % uniqueName
		self.temp_child_table_name = "ut_child%s" % uniqueName
		self.createSchema()
		biz.UserSQL = "select * from %s" % self.temp_table_name
		biz.KeyField = "pk"
		biz.DataSource = self.temp_table_name
		biz.requery()

		## set up the ui elements:
		app = self.app = dabo.dApp(MainFormClass=None)
		app.setup()
		frm = self.frm = dabo.ui.dForm(Caption="test_dForm")
		frm.addObject(dabo.ui.dTextBox, DataSource=biz.DataSource, DataField="cField", RegID="cField")
		frm.addObject(dabo.ui.dTextBox, DataSource=biz.DataSource, DataField="nField", RegID="nField")
		frm.addObject(dabo.ui.dTextBox, DataSource=biz.DataSource, DataField="iField", RegID="iField")

		## connect the biz to the frm:
		frm.addBizobj(biz)

		## force the frm to get the first record:
		frm.first()
		frm.update(interval=0)  ## need to force the update here because it is delayed by default, which doesn't work for scripted tests.

	def tearDown(self):
		self.biz = None
		self.frm = None
		self.app = None

	def createSchema(self):
		biz = self.biz
		tableName = self.temp_table_name
		childTableName = self.temp_child_table_name
		biz._CurrentCursor.executescript("""
create table %(tableName)s (pk INTEGER PRIMARY KEY AUTOINCREMENT, cField CHAR, iField INT, nField DECIMAL (8,2));
insert into %(tableName)s (cField, iField, nField) values ("Paul Keith McNett", 23, 23.23);
insert into %(tableName)s (cField, iField, nField) values ("Edward Leafe", 42, 42.42);
insert into %(tableName)s (cField, iField, nField) values ("Carl Karsten", 10223, 23032.76);

create table %(childTableName)s (pk INTEGER PRIMARY KEY AUTOINCREMENT, parent_fk INT, cInvNum CHAR);
insert into %(childTableName)s (parent_fk, cInvNum) values (1, "IN00023");
insert into %(childTableName)s (parent_fk, cInvNum) values (1, "IN00455");
insert into %(childTableName)s (parent_fk, cInvNum) values (3, "IN00024");
""" % locals())

	def createNullRecord(self):
		self.biz._CurrentCursor.AuxCursor.execute("""
insert into %s (cField, iField, nField) values (NULL, NULL, NULL)
""" % self.temp_table_name)

	def testSomeSanityThings(self):
		frm = self.frm
		biz = frm.getBizobj()
		self.assertEqual(frm.cField.Value, "Paul Keith McNett")
		frm.next()
		frm.update(interval=0)  ## Need to force the update here which would otherwise happen 100 ms in the future.
		self.assertEqual(biz.RowNumber, 1)
		self.assertEqual(frm.cField.Value, "Edward Leafe")


	def testNullRecord(self):
		# This test currently fails (thanks John Fabiani for pointing it out). The
		# Dabo UI layer inappropriately converts None values into u"None" values.
		frm = self.frm
		biz = frm.getBizobj()
		self.createNullRecord()
		frm.requery()
		self.assertEqual(biz.RowCount, 4)
		frm.last()
		frm.update(interval=0)  ## Need to force the update here, otherwise it won't happen until 100 ms in the future.
		self.assertEqual(biz.RowNumber, 3)
		self.assertEqual(biz.Record.cField, None)
		self.assertEqual(biz.Record.iField, None)
		self.assertEqual(biz.Record.nField, None)

		self.assertEqual(frm.cField.Value, None)
		self.assertEqual(frm.iField.Value, None)
		self.assertEqual(frm.nField.Value, None)


if __name__ == "__main__":
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_dForm)
	unittest.TextTestRunner(verbosity=2).run(suite)
