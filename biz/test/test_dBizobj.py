# -*- coding: utf-8 -*-
import unittest
import dabo
from dabo.lib import getRandomUUID

## Only tests against sqlite, as we already test dCursorMixin against the
## various backends. 

class Test_dBizobj(unittest.TestCase):
	def setUp(self):
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

	def tearDown(self):
		self.biz = None

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


	def test_DefaultValues(self):
		biz = self.biz
		biz.DefaultValues["iField"] = 2342
		biz.new()
		self.assertEqual(biz.Record.iField, 2342)
		self.assertEqual(biz.isChanged(), False)		

	def testVirtualFields(self):
		biz = self.biz
		def getCombinedName():
			return "%s:%s" % (biz.Record.cField.replace(" ", ""), biz.Record.iField)
		biz.VirtualFields["combined_name"] = getCombinedName

		def testBogus():
			return biz.Record.bogus_field_name

		self.assertRaises(dabo.dException.FieldNotFoundException, testBogus)
		self.assertEqual(biz.Record.combined_name, "PaulKeithMcNett:23")
		biz.Record.combined_name = "shouldn't be able to set this"
		self.assertEqual(biz.Record.combined_name, "PaulKeithMcNett:23")

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
		self.assertEqual(cur._mementos[biz.Record.pk]["cField"], "Paul Keith McNett")
		biz.Record.cField = "Alison Anton"
		self.assertEqual(biz.Record.cField, "Alison Anton")
		self.assertEqual(cur._mementos[biz.Record.pk]["cField"], "Paul Keith McNett")
		biz.setFieldVal("iField", 80)
		self.assertEqual(biz.Record.iField, 80)
		self.assertTrue(isinstance(biz.Record.iField, (int, long)))
		self.assertEqual(cur._mementos[self.biz.Record.pk]["iField"], 23)

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

	## - Begin method unit tests -

	def test_cancel(self):
		biz = self.biz
		biz.Record.cField = "pkm"
		biz.cancel()
		self.assertEqual(biz.Record.cField, "Paul Keith McNett")
		biz.new()
		self.assertEqual(biz.RowCount, 4)
		self.assertEqual(biz.RowNumber, 3)
		biz.cancel()
		self.assertEqual(biz.RowCount, 3)
		self.assertEqual(biz.RowNumber, 2)

		
	def test_isChanged(self):
		biz = self.biz
		self.assertEqual(biz.isChanged(), False)
		biz.Record.cField = "The Magnificent Seven"
		self.assertEqual(biz.isChanged(), True)
		biz.cancel()
		self.assertEqual(biz.isChanged(), False)

		# isChanged()	should be False for new records that haven't had any field
		# value changes.	
		biz.new()
		self.assertEqual(biz.isChanged(), False)
		biz.Record.cField = "Hitsville U.K."
		self.assertEqual(biz.isChanged(), True)


	def test_oldVal(self):
		biz = self.biz
		self.assertEqual(biz.oldVal("cField"), biz.Record.cField)
		self.assertEqual(biz.oldVal("cField", 1), biz.getFieldVal("cField", 1))
		oldVal = biz.Record.cField 
		newVal = "pkm23"
		biz.Record.cField = newVal
		self.assertEqual(biz.oldVal("cField"), oldVal)
		self.assertEqual(biz.Record.cField, newVal)
		self.assertRaises(dabo.dException.FieldNotFoundException, biz.oldVal, "bogusField")

	## - End method unit tests -

	def testDeleteNewSave(self):
		biz = self.biz
		biz.delete()
		biz.new()
		biz.save()
		self.assertEqual(biz.RowCount, 3)
		self.assertEqual(biz.RowNumber, 2)

		biz.deleteAll()
		self.assertEqual(biz.RowCount, 0)

		self.assertRaises(dabo.dException.NoRecordsException, biz.save)
		self.assertRaises(dabo.dException.NoRecordsException, biz.delete)

		biz.new()
		self.assertEqual(biz.RowCount, 1)
		biz.delete()
		self.assertEqual(biz.RowCount, 0)
		self.assertRaises(dabo.dException.NoRecordsException, biz.save)

		biz.new()
		biz.save()
		self.assertEqual(biz.RowCount, 1)
		self.assertEqual(biz.RowNumber, 0)


	def testMementos(self):
		biz = self.biz
		cur = biz._CurrentCursor

		priorVal = biz.Record.cField

		# Make a change that is the same as the prior value:
		biz.Record.cField = priorVal
		self.assertEqual(priorVal, biz.Record.cField)

		# Make a change that is different:
		biz.Record.cField = "New test value"
		self.assertEqual(cur._mementos, {biz.Record.pk: {"cField": priorVal}})
		self.assertEqual(biz.isChanged(), True)

		# Change it back:
		biz.Record.cField = priorVal
		self.assertEqual(cur._mementos, {})
		self.assertEqual(biz.isChanged(), False)

		# Make a change that is different and cancel:
		biz.Record.cField = "New test value"
		biz.cancel()
		self.assertEqual(cur._mementos, {})
		self.assertEqual(biz.isChanged(), False)

		# Add a record:
		biz.new()
		
		self.assertEqual(biz.RowCount, 4)
		self.assertEqual(biz.RowNumber, 3)
		self.assertEqual(cur._newRecords, {-1: None})
		self.assertEqual(biz.isChanged(), False)  ## (because no field changed in new record)
		self.assertEqual(cur.Record.pk, -1)
		self.assertEqual(biz.Record.cField, "")
		self.assertEqual(biz.Record.iField, 0)
		self.assertEqual(biz.Record.nField, 0)
		biz.save()
		self.assertEqual(biz.RowCount, 4)  ## still have 4 rows, even though the last one wasn't saved
		biz.requery()
		# We only have 3 rows, because one of the prior 4 rows was new with no changed fields:
		self.assertEqual(biz.RowCount, 3)
		# ...and RowNumber went to 0, because the previous row number (3) doesn't exist anymore:
		self.assertEqual(biz.RowNumber, 0)
		self.assertEqual(cur._newRecords, {})
		self.assertEqual(biz.isChanged(), False)
		self.assertEqual(biz.Record.pk, 1)


	def testChildren(self):
		bizMain = self.biz
		bizChild = dabo.biz.dBizobj(self.con)
		bizChild.UserSQL = "select * from %s" % self.temp_child_table_name
		bizChild.KeyField = "pk"
		bizChild.DataSource = self.temp_child_table_name
		bizChild.LinkField = "parent_fk"
		bizChild.FillLinkFromParent = True
		
		bizMain.addChild(bizChild)
		bizMain.requery()

		# At this point bizMain should be at row 0, and bizChild should have
		# two records, and be on row 0, and isChanged() should be False, since
		# no fields have been updated.
		self.assertEqual(bizMain.Record.pk, 1)
		self.assertEqual(bizMain.RowNumber, 0)
		self.assertEqual(bizChild.RowCount, 2)
		self.assertEqual(bizChild.RowNumber, 0)
		self.assertEqual(bizChild.Record.pk, 1)
		self.assertEqual(bizChild.Record.parent_fk, 1)
		self.assertEqual(bizMain.isChanged(), False)
		self.assertEqual(bizChild.isChanged(), False)
		self.assertEqual(bizMain.isAnyChanged(), False)
		self.assertEqual(bizChild.isAnyChanged(), False)

		bizMain.next()
		
		# At this point bizMain should be at row 1, and bizChild should have
		# zero records.
		self.assertEqual(bizMain.Record.pk, 2)
		self.assertEqual(bizMain.RowNumber, 1)
		self.assertEqual(bizChild.RowCount, 0)
		self.assertEqual(bizChild.RowNumber, 0)
		
		# Trying to get the field value from the nonexistent record should raise
		# dException.NoRecordsException:
		def testGetField():
			return bizChild.Record.pk
		def testSetField():
			bizChild.Record.pk = 23
		self.assertRaises(dabo.dException.NoRecordsException, testGetField)
		self.assertRaises(dabo.dException.NoRecordsException, testSetField)

		bizMain.next()

		# At this point bizMain should be at row 2, and bizChild should have
		# one record, and be on row 0.
		self.assertEqual(bizMain.Record.pk, 3)
		self.assertEqual(bizMain.RowNumber, 2)
		self.assertEqual(bizChild.RowCount, 1)
		self.assertEqual(bizChild.RowNumber, 0)
		self.assertEqual(bizChild.Record.pk, 3)
		self.assertEqual(bizChild.Record.parent_fk, 3)
		
		# Try a delete, which takes effect immediately without need to save:
		bizChild.delete()
		self.assertEqual(bizMain.RowNumber, 2)
		self.assertEqual(bizChild.RowCount, 0)
		self.assertEqual(bizChild.isAnyChanged(), False)
		self.assertEqual(bizMain.isAnyChanged(), False)
		bizMain.prior()
		self.assertEqual(bizChild.RowCount, 0)
		bizMain.next()
		self.assertEqual(bizChild.RowCount, 0)

		# Add a new child record:
		self.assertEqual(bizChild.IsAdding, False)
		bizChild.new()
		self.assertEqual(bizChild.IsAdding, True)
		self.assertEqual(bizChild.RowCount, 1)
		self.assertEqual(bizChild.isAnyChanged(), False)
		self.assertEqual(bizChild.isChanged(), False)
		self.assertEqual(bizMain.isAnyChanged(), False)
		self.assertEqual(bizMain.isChanged(), False)
		bizChild.Record.cInvNum = "IN99991"
		self.assertEqual(bizMain.isChanged(), True)
		self.assertEqual(bizMain.isAnyChanged(), True)
		self.assertEqual(bizChild.isChanged(), True)
		self.assertEqual(bizChild.isAnyChanged(), True)

		bizMain.prior()
		self.assertEqual(bizChild.IsAdding, False)
		bizMain.next()
		self.assertEqual(bizChild.IsAdding, True)

		self.assertEqual(bizChild.RowCount, 1)
		self.assertEqual(bizChild.isAnyChanged(), True)
		self.assertEqual(bizChild.isChanged(), True)
		self.assertEqual(bizMain.isAnyChanged(), True)
		self.assertEqual(bizMain.isChanged(), True)
		self.assertEqual(bizChild.Record.cInvNum, "IN99991")

		bizMain.saveAll()

		self.assertEqual(bizMain.RowCount, 3)
		self.assertEqual(bizMain.RowNumber, 2)
		self.assertEqual(bizChild.RowCount, 1)
		self.assertEqual(bizChild.Record.cInvNum, "IN99991")
		self.assertEqual(bizChild.IsAdding, False)
		bizMain.requery()
		self.assertEqual(bizMain.RowCount, 3)
		self.assertEqual(bizMain.RowNumber, 2)
		self.assertEqual(bizChild.RowCount, 1)
		self.assertEqual(bizChild.Record.cInvNum, "IN99991")
		bizMain.prior()
		bizMain.next()
		self.assertEqual(bizChild.RowCount, 1)
		self.assertEqual(bizChild.Record.cInvNum, "IN99991")

		# Test the case where you add a new parent record but no new children:
		bizMain.new()
		bizMain.Record.cField = "Junco Pardner"
		self.assertEqual(bizMain.RowCount, 4)
		self.assertEqual(bizMain.RowNumber, 3)
		bizMain.saveAll()
		self.assertEqual(bizMain.RowCount, 4)
		self.assertEqual(bizMain.RowNumber, 3)
		bizMain.requery()		
		self.assertEqual(bizMain.RowCount, 4)
		self.assertEqual(bizMain.RowNumber, 3)


	def testChildren_cancel(self):
		bizMain = self.biz
		bizChild = dabo.biz.dBizobj(self.con)
		bizChild.UserSQL = "select * from %s" % self.temp_child_table_name
		bizChild.KeyField = "pk"
		bizChild.DataSource = self.temp_child_table_name
		bizChild.LinkField = "parent_fk"
		bizChild.FillLinkFromParent = True
		
		bizMain.addChild(bizChild)
		bizMain.requery()

		# Test the case where you add a new child record, then cancel the parent:
		self.assertEqual(bizChild.RowCount, 2)
		bizChild.new()
		self.assertEqual(bizChild.RowCount, 3)
		bizMain.cancel()
		self.assertEqual(bizChild.RowCount, 2)
			

	def testChildren_clearParent(self):
		"""Requerying bizMain to 0 records should remove bizChild's records, too."""
		bizMain = self.biz
		bizChild = dabo.biz.dBizobj(self.con)
		bizChild.UserSQL = "select * from %s" % self.temp_child_table_name
		bizChild.KeyField = "pk"
		bizChild.DataSource = self.temp_child_table_name
		bizChild.LinkField = "parent_fk"
		bizChild.FillLinkFromParent = True
		
		bizMain.addChild(bizChild)
		bizMain.requery()

		bizMain.UserSQL = "select * from %s where 1=0" % self.temp_table_name
		bizMain.requery()
		self.assertEqual(bizMain.RowCount, 0)
		self.assertEqual(bizChild.RowCount, 0)
	
	def testNullRecord(self):
		biz = self.biz
		self.createNullRecord()
		biz.requery()
		self.assertEqual(biz.RowCount, 4)
		biz.last()
		self.assertEqual(biz.RowNumber, 3)
		self.assertEqual(biz.Record.cField, None)
		self.assertEqual(biz.Record.iField, None)
		self.assertEqual(biz.Record.nField, None)


if __name__ == "__main__":
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_dBizobj)
	unittest.TextTestRunner(verbosity=2).run(suite)
