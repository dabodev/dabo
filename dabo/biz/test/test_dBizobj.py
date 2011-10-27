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
		self.temp_table_name = "parent"
		self.temp_child_table_name = "child"
		self.temp_child2_table_name = "grandchild"
		self.createSchema()
		biz.KeyField = "pk"
		biz.DataSource = self.temp_table_name
		biz.requery()

	def tearDown(self):
		self.biz = None

	def createSchema(self):
		biz = self.biz
		tableName = self.temp_table_name
		childTableName = self.temp_child_table_name
		child2TableName = self.temp_child2_table_name
		biz._CurrentCursor.executescript("""
create table %(tableName)s (pk INTEGER PRIMARY KEY AUTOINCREMENT, cField CHAR, iField INT, nField DECIMAL (8,2));
insert into %(tableName)s (cField, iField, nField) values ("Paul Keith McNett", 23, 23.23);
insert into %(tableName)s (cField, iField, nField) values ("Edward Leafe", 42, 42.42);
insert into %(tableName)s (cField, iField, nField) values ("Carl Karsten", 10223, 23032.76);

create table %(childTableName)s (pk INTEGER PRIMARY KEY AUTOINCREMENT, parent_fk INT, cInvNum CHAR);
insert into %(childTableName)s (parent_fk, cInvNum) values (1, "IN00023");
insert into %(childTableName)s (parent_fk, cInvNum) values (1, "IN00455");
insert into %(childTableName)s (parent_fk, cInvNum) values (3, "IN00024");

create table %(child2TableName)s (pk INTEGER PRIMARY KEY AUTOINCREMENT, parent_fk INT, cPart CHAR);
insert into %(child2TableName)s (parent_fk, cPart) values (1, "fldk-333");
insert into %(child2TableName)s (parent_fk, cPart) values (1, "9930");
insert into %(child2TableName)s (parent_fk, cPart) values (2, "hhfg-234");
insert into %(child2TableName)s (parent_fk, cPart) values (2, "pkd-8878");
""" % locals())

	def createNullRecord(self):
		self.biz._CurrentCursor.AuxCursor.execute("""
insert into %s (cField, iField, nField) values (NULL, NULL, NULL)
""" % self.temp_table_name)

	## - Begin property unit tests -
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
		self.assertEqual(biz.CurrentSQL, biz.AutoSQL)
		biz.UserSQL = "select * from %s limit 2" % self.temp_table_name
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
		self.assertEqual(biz.Encoding, dabo.getEncoding())
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
		self.assertEqual(biz.LastSQL, biz.AutoSQL)
		biz.UserSQL = "select * from %s limit 23" % (self.temp_table_name)
		biz.requery()
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

		self.assertRaises(dabo.dException.NoRecordsException, biz.delete)

		biz.new()
		self.assertEqual(biz.RowCount, 1)
		biz.delete()
		self.assertEqual(biz.RowCount, 0)

		biz.new()
		biz.save()
		self.assertEqual(biz.RowCount, 1)
		self.assertEqual(biz.RowNumber, 0)


	def testDeleteChildThenDeleteParent(self):
		"""See ticket #1312"""
		bizMain = self.biz
		bizChild = dabo.biz.dBizobj(self.con)
		bizChild.KeyField = "pk"
		bizChild.DataSource = self.temp_child_table_name
		bizChild.LinkField = "parent_fk"
		bizChild.FillLinkFromParent = True

		bizMain.addChild(bizChild)
		bizMain.requery()

		# bizMain is on row 0, id 1. bizChild is on row 0 with 2 rows.
		self.assertEqual(bizMain.Record.pk, 1)
		self.assertEqual(bizChild.RowCount, 2)
		self.assertEqual(bizChild.RowNumber, 0)
		self.assertEqual(bizChild.Record.parent_fk, 1)
		bizChild.delete()
		bizMain.delete()
		self.assertEqual(bizChild.RowCount, 0)
		self.assertEqual(bizMain.RowCount, 2)


	def testSaveNewUnchanged(self):
		"""See ticket #1101"""
		bizMain = self.biz
		bizChild = dabo.biz.dBizobj(self.con)
		bizChild.KeyField = "pk"
		bizChild.DataSource = self.temp_child_table_name
		bizChild.LinkField = "parent_fk"
		bizChild.FillLinkFromParent = True

		bizMain.addChild(bizChild)
		bizMain.requery()

		# test case 1: True in both parent/child, record should save to backend:
		bizMain.SaveNewUnchanged = True
		bizChild.SaveNewUnchanged = True
		bizChild.new()
		self.assertEqual(bizChild.RowCount, 3)
		self.assertEqual(bizMain.isAnyChanged(), True)
		bizMain.save()
		self.assertEqual(bizMain.isAnyChanged(), False)
		self.assertEqual(bizChild.RowCount, 3)
		test_sql = "select count(*) as count from %s where parent_fk = ?" % self.temp_child_table_name
		temp = bizMain.getTempCursor(test_sql, (bizMain.Record.pk,))
		self.assertEqual(bizChild.RowCount, temp.Record.count)

		# test case 2: False in parent but True in child: won't save child changes but will keep prompting
		bizMain.SaveNewUnchanged = False
		bizChild.new()
		self.assertEqual(bizChild.RowCount, 4)
		self.assertEqual(bizMain.SaveNewUnchanged, False)
		self.assertEqual(bizChild.SaveNewUnchanged, True)
		self.assertEqual(bizMain.isAnyChanged(), True)  ## the new child record isn't changed
		self.assertEqual(bizMain.getChangedRows(), [])
		self.assertEqual(bizChild.isAnyChanged(), True)  ## bizChild.SaveNewUnchanged == True
		self.assertEqual(bizChild.isAnyChanged(includeNewUnchanged=False), False)
		bizMain.save()
		self.assertEqual(bizChild.RowCount, 4)
		temp = bizMain.getTempCursor(test_sql, (bizMain.Record.pk,))
		self.assertEqual(temp.Record.count, 4)  ## bizChild.SaveNewUnchanged == True so should be saved.
		self.assertEqual(bizMain.getChangedRows(), [])

		

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
		self.assertEqual(bizChild.RowNumber, -1)

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


	def testChildren_moveParentRecordPointer(self):
		"""Moving the parent record pointer shouldn't erase child changes."""
		bizMain = self.biz
		bizChild = dabo.biz.dBizobj(self.con)
		bizChild.KeyField = "pk"
		bizChild.DataSource = self.temp_child_table_name
		bizChild.LinkField = "parent_fk"
		bizChild.FillLinkFromParent = True

		bizMain.addChild(bizChild)
		bizMain.requery()

		# preliminary sanity checks:
		self.assertEqual(bizChild.RowCount, 2)
		bizChild.RowNumber = 1
		bizMain.next()
		self.assertEqual(bizChild.RowCount, 0)
		bizMain.prior()
		self.assertEqual(bizChild.RowCount, 2)
		self.assertEqual(bizMain.RowNumber, 0)
		self.assertEqual(bizChild.RowNumber, 1)
		bizMain.RowNumber = 2
		self.assertEqual(bizChild.RowNumber, 0)

		# We are in row 2 of main, and row 0 of child

		# Change a field, and test isChanged() both before and after moving the
		# parent record pointer:
		bizChild.Record.cInvNum = "pkm0023"
		self.assertEqual(bizChild._CurrentCursor._mementos, {3: {'cInvNum': u'IN00024'}})
		self.assertEqual(bizChild.isChanged(), True)
		self.assertEqual(bizMain.isChanged(), True)

		# Prove no problem with simple change, and moving parent record pointer:
		bizMain.RowNumber = 2
		self.assertEqual(bizChild.Record.cInvNum, "pkm0023")
		self.assertEqual(bizChild._CurrentCursor._mementos, {3: {'cInvNum': u'IN00024'}})
		self.assertEqual(bizChild.isChanged(), True)
		self.assertEqual(bizMain.isChanged(), True)

		# Prove no problem with simple change, adding new record, and changing the
		# new record: the simple change is still there.
		bizChild.new()
		bizChild.Record.cInvNum = "pkm0024"
		self.assertEqual(bizChild.RowCount, 2)
		bizMain.RowNumber = 2
		self.assertEqual(bizChild.isAnyChanged(), True)
		self.assertEqual(bizChild.RowCount, 2)
		self.assertEqual(bizChild.isChanged(), True)
		bizChild.RowNumber = 0
		self.assertEqual(bizChild.isChanged(), True)
		self.assertEqual(bizChild._CurrentCursor._mementos, {3: {'cInvNum': u'IN00024'}, -1: {'cInvNum': u''}})

		# Now, here's the problem. If we add a new record to the child but don't
		# change any fields in that new record, then move the main record pointer,
		# all child changes in other records will be lost, not just the blank
		# new record which gets removed due to Dabo's design.
		bizChild.new()
		self.assertEqual(bizChild.RowCount, 3)
		self.assertEqual(bizChild.isAnyChanged(), True)
		self.assertEqual(bizChild._CurrentCursor._mementos, {3: {'cInvNum': u'IN00024'}, -1: {'cInvNum': u''}, -1: {'cInvNum': u''}})
		bizMain.RowNumber = 2
		# boom! a simple record change in the parent removed the change to the first
		# record, the new record with a change, as well as the expected last new record
		# that had no changes:
		self.assertEqual(bizChild.isAnyChanged(), True)


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


	def testMementoSaveNewPotentialProblem(self):
		"""This attempts to reproduce problems being reported on
		dabo-users (see thread http://leafe.com/archives/showFullThd/374683)
		"""
		biz = self.biz
		self.assertEqual(biz.isChanged(), False)
		self.assertEqual(biz.isAnyChanged(), False)
		biz.new()
		self.assertEqual(biz.isChanged(), False)
		self.assertEqual(biz.isAnyChanged(), False)
		biz.Record.cField = 'ppp'
		self.assertEqual(biz.isChanged(), True)
		self.assertEqual(biz.isAnyChanged(), True)
		biz.save()
		self.assertEqual(biz.isChanged(), False)
		self.assertEqual(biz.isAnyChanged(), False)


	def testChildRowNumberResetAfterGetChangedRows(self):
		"""My app is showing the child bo going from RowNumber 0 to
		RowNumber -1 after calling parent.getChangedRows().
		"""
		bizMain = self.biz
		bizChild = dabo.biz.dBizobj(self.con)
		bizChild.KeyField = "pk"
		bizChild.DataSource = self.temp_child_table_name
		bizChild.LinkField = "parent_fk"
		bizChild.FillLinkFromParent = True

		bizMain.addChild(bizChild)
		bizMain.requery()

		self.assertEqual(bizMain.RowNumber, 0)
		self.assertEqual(bizChild.RowNumber, 0)

		bizMain.getChangedRows()

		self.assertEqual(bizMain.RowNumber, 0)
		self.assertEqual(bizChild.RowNumber, 0)

	def testChangesToTwoChildRecords(self, mode="save"):
		"""After the dabo web server stuff and the @remote calls got added, only
		a single record from child bizobjs seem to get saved.
		"""
		bizMain = self.biz
		bizChild = dabo.biz.dBizobj(self.con)
		bizChild.KeyField = "pk"
		bizChild.DataSource = self.temp_child_table_name
		bizChild.LinkField = "parent_fk"
		bizChild.FillLinkFromParent = True

		bizChild2 = dabo.biz.dBizobj(self.con)
		bizChild2.KeyField = "pk"
		bizChild2.DataSource = self.temp_child2_table_name
		bizChild2.LinkField = "parent_fk"
		bizChild2.FillLinkFromParent = True

		bizMain.addChild(bizChild)
		bizChild.addChild(bizChild2)
		bizMain.requery()

		bizChild.RowNumber = 0
		bizChild.Record.cInvNum = "00293"
		bizChild2.RowNumber = 0
		bizChild2.Record.cPart = "flim"
		bizChild2.RowNumber = 1
		bizChild2.Record.cPart = "flam"
		bizChild.RowNumber = 1
		bizChild.Record.cInvNum = "03938"
		bizChild2.RowNumber = 0
		bizChild2.Record.cPart = "flim"
		bizChild2.RowNumber = 1
		bizChild2.Record.cPart = "flam"

		self.assertEqual(bizMain.isAnyChanged(), True)
		self.assertEqual(bizMain.getChangedRows(), [0])
		self.assertEqual(bizChild.getChangedRows(), [0,1])
		if mode == "save":
			bizMain.save()
		elif mode == "cancel":
			bizMain.cancelAll()
		self.assertEqual(bizChild2.getChangedRows(), [])
		self.assertEqual(bizChild.getChangedRows(), [])
		self.assertEqual(bizMain.getChangedRows(), [])
		self.assertEqual(bizMain.isAnyChanged(), False)

	def testChangesToTwoChildRecords_cancel(self):
		"""Do the same test as for save, but with cancelAll()."""
		self.testChangesToTwoChildRecords("cancel")

if __name__ == "__main__":
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_dBizobj)
	unittest.TextTestRunner(verbosity=2).run(suite)
