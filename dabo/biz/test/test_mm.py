# -*- coding: utf-8 -*-
import unittest
import dabo
import dabo.dException as dException
from dabo.lib import getRandomUUID

class Test_Many_To_Many(unittest.TestCase):
	def setUp(self):
		self.conn = dabo.db.dConnection(DbType="SQLite", Database=":memory:")
		pbiz = self.person_biz = dabo.biz.dBizobj(self.conn)
		self.crs = self.person_biz.getTempCursor()
		self.createSchema()
		pbiz.KeyField = "pkid"
		pbiz.DataSource = "person"
		pbiz.requery()
		comp = self.company_biz = dabo.biz.dBizobj(self.conn)
		comp.KeyField = "pkid"
		comp.DataSource = "company"
		comp.requery()
		fan_club = self.fan_club_biz = dabo.biz.dBizobj(self.conn)
		fan_club.KeyField = "pkid"
		fan_club.DataSource = "fan_club"
		fan_club.requery()
		self.restricted_biz = dabo.biz.dBizobj(self.conn)
		self.restricted_biz.KeyField = "pkid"
		self.restricted_biz.DataSource = "restricted"
		self.restricted_biz.requery()
		# Set the MM relations
		pbiz.addMMBizobj(self.company_biz, "employees", "person_id", "company_id")
		pbiz.addMMBizobj(self.fan_club_biz, "membership", "person_id", "fan_club_id")


	def tearDown(self):
		self.person_biz = self.company_biz = None


	def createSchema(self):
		self.crs.execute("create table person (pkid INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT, last_name TEXT);")
		self.crs.execute("create table company (pkid INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT);")
		self.crs.execute("create table employees (pkid INTEGER PRIMARY KEY AUTOINCREMENT, person_id INT, company_id INT);")
		self.crs.execute("insert into person (first_name, last_name) values ('Ed', 'Leafe')")
		self.crs.execute("insert into person (first_name, last_name) values ('Paul', 'McNett')")
		self.crs.execute("insert into company (company) values ('Acme Manufacturing')")

		self.crs.execute("create table fan_club (pkid INTEGER PRIMARY KEY AUTOINCREMENT, performer TEXT);")
		self.crs.execute("create table membership (pkid INTEGER PRIMARY KEY AUTOINCREMENT, person_id INT, fan_club_id INT);")
		self.crs.execute("insert into fan_club (performer) values ('Green Day')")
		self.crs.execute("insert into fan_club (performer) values ('The Clash')")
		self.crs.execute("insert into fan_club (performer) values ('Ramones')")
		self.crs.execute("insert into fan_club (performer) values ('Pat Boone')")

		# Table with NOT NULL restriction.
		self.crs.execute("create table restricted (pkid INTEGER PRIMARY KEY AUTOINCREMENT, regular TEXT, nonull TEXT NOT NULL);")
		self.crs.execute("create table rest_alloc (pkid INTEGER PRIMARY KEY AUTOINCREMENT, person_id INT, restricted_id INT);")
		self.crs.execute("insert into restricted (regular, nonull) values ('some_value', 'another_value')")


	def reccount(self, tbl, filt=None):
		"""Please note that SQL injection is consciously ignored here. These
		are in-memory tables!!
		"""
		if filt:
			self.crs.execute("select count(*) as cnt from %s where %s" % (tbl, filt))
		else:
			self.crs.execute("select count(*) as cnt from %s" % tbl)
		return self.crs.Record.cnt


	def test_bad_datasource(self):
		"""Ensure that the proper exception is raised when a DataSource is passed
		that does not correspond to an existing relation.
		"""
		pbiz = self.person_biz
		cbiz = self.company_biz
		pbiz.seek("Leafe", "last_name")
		self.assertRaises(dException.DataSourceNotFoundException,
				pbiz.mmAssociateValue, "dummy", "company", "Acme Manufacturing")
		

	def test_associate(self):
		"""Verify that bizobj.mmAssociateValue() works correctly."""
		pbiz = self.person_biz
		cbiz = self.company_biz
		self.assertEqual(self.reccount("company"), 1)

		pbiz.seek("Leafe", "last_name")
		pbiz.mmAssociateValue(cbiz, "company", "Acme Manufacturing")
		# Company count should not have changed
		self.assertEqual(self.reccount("company"), 1)
		pbiz.mmAssociateValue(cbiz, "company", "Amalgamated Industries")
		# Company count should have increased
		self.assertEqual(self.reccount("company"), 2)


	def test_associate_list(self):
		"""Verify that bizobj.mmAssociateValues() works correctly."""
		pbiz = self.person_biz
		fbiz = self.fan_club_biz
		orig_club_count = self.reccount("fan_club")
		orig_fan_count = self.reccount("membership")
		self.assertEqual(orig_fan_count, 0)

		pbiz.seek("Leafe", "last_name")
		pbiz.mmAssociateValues(fbiz, "performer", ["Ramones", "Green Day"])
		# Club count should not have changed
		self.assertEqual(self.reccount("fan_club"), orig_club_count)
		# Membership count should have increased
		self.assertEqual(self.reccount("membership"), orig_fan_count + 2)

		# Add a list with both existing and new clubs
		pbiz.mmAssociateValues(fbiz, "performer", ["Ramones", "Black Flag"])
		# Club count should have increased by 1
		self.assertEqual(self.reccount("fan_club"), orig_club_count + 1)
		# Membership count should have increased by 1
		self.assertEqual(self.reccount("membership"), orig_fan_count + 3)


	def test_dissociate(self):
		"""Verify that bizobj.mmDisssociateValue() works correctly."""
		pbiz = self.person_biz
		cbiz = self.company_biz
		pbiz.seek("Leafe", "last_name")
		leafe_pk = pbiz.getPK()
		pbiz.mmAssociateValue(cbiz, "company", "Acme Manufacturing")
		emp_count = self.reccount("employees", "person_id = %s" % leafe_pk)
		self.assertEqual(emp_count, 1)
		pbiz.mmAssociateValue(cbiz, "company", "Amalgamated Industries")
		emp_count = self.reccount("employees", "person_id = %s" % leafe_pk)
		self.assertEqual(emp_count, 2)
		pbiz.mmDisssociateValue(cbiz, "company", "Acme Manufacturing")
		emp_count = self.reccount("employees", "person_id = %s" % leafe_pk)
		self.assertEqual(emp_count, 1)


	def test_dissociate_list(self):
		"""Verify that bizobj.mmDisssociateValues() works correctly."""
		pbiz = self.person_biz
		cbiz = self.company_biz
		pbiz.seek("Leafe", "last_name")
		leafe_pk = pbiz.getPK()
		pbiz.mmAssociateValues(cbiz, "company", ["Acme Manufacturing", "Amalgamated Industries",
				"Dabo Incorporated"])
		emp_count = self.reccount("employees", "person_id = %s" % leafe_pk)
		self.assertEqual(emp_count, 3)
		pbiz.mmDisssociateValues(cbiz, "company", ["Acme Manufacturing", "Amalgamated Industries"])
		emp_count = self.reccount("employees", "person_id = %s" % leafe_pk)
		self.assertEqual(emp_count, 1)


	def test_dissociateAll(self):
		"""Verify that bizobj.mmDisssociateAll() works correctly."""
		pbiz = self.person_biz
		cbiz = self.company_biz
		pbiz.seek("Leafe", "last_name")
		leafe_pk = pbiz.getPK()
		# Add a bunch of related entries
		pbiz.mmAssociateValue(cbiz, "company", "AAAA")
		pbiz.mmAssociateValue(cbiz, "company", "BBBB")
		pbiz.mmAssociateValue(cbiz, "company", "CCCC")
		pbiz.mmAssociateValue(cbiz, "company", "DDDD")
		pbiz.mmAssociateValue(cbiz, "company", "EEEE")
		emp_count = self.reccount("employees", "person_id = %s" % leafe_pk)
		self.assertEqual(emp_count, 5)
		# Now disassociate all of them
		pbiz.mmDisssociateAll(cbiz)
		emp_count = self.reccount("employees", "person_id = %s" % leafe_pk)
		self.assertEqual(emp_count, 0)


	def test_full_associate(self):
		"""Verify that bizobj.mmSetFullAssociation() works correctly."""
		pbiz = self.person_biz
		cbiz = self.company_biz
		pbiz.seek("Leafe", "last_name")
		leafe_pk = pbiz.getPK()
		pbiz.mmAssociateValue(cbiz, "company", "AAAA")
		pbiz.mmAssociateValue(cbiz, "company", "BBBB")
		pbiz.mmAssociateValue(cbiz, "company", "CCCC")
		pbiz.mmAssociateValue(cbiz, "company", "DDDD")
		pbiz.mmAssociateValue(cbiz, "company", "EEEE")
		emp_count = self.reccount("employees", "person_id = %s" % leafe_pk)
		self.assertEqual(emp_count, 5)
		pbiz.mmSetFullAssociation(cbiz, "company", ["yy", "zz"])
		emp_count = self.reccount("employees", "person_id = %s" % leafe_pk)
		self.assertEqual(emp_count, 2)


	def test_add_to_both(self):
		"""Verify that bizobj.mmAddToBoth() works correctly."""
		pbiz = self.person_biz
		cbiz = self.company_biz
		person_count = self.reccount("person")
		self.assertEqual(person_count, 2)
		company_count = self.reccount("company")
		self.assertEqual(company_count, 1)
		emp_count = self.reccount("employees")
		self.assertEqual(emp_count, 0)

		# Add values that exist in both already
		pbiz.mmAddToBoth(cbiz, "last_name", "Leafe", "company", "Acme Manufacturing")
		# Person and company should be unchanged; there should be one more employee
		person_count = self.reccount("person")
		self.assertEqual(person_count, 2)
		company_count = self.reccount("company")
		self.assertEqual(company_count, 1)
		emp_count = self.reccount("employees")
		self.assertEqual(emp_count, 1)

		# Add a new company with an existing person
		pbiz.mmAddToBoth(cbiz, "last_name", "Leafe", "company", "Dabo Incorporated")
		# Person should be unchanged; there should be one more company and employee
		person_count = self.reccount("person")
		self.assertEqual(person_count, 2)
		company_count = self.reccount("company")
		self.assertEqual(company_count, 2)
		emp_count = self.reccount("employees")

		# Add a new person with an existing company
		pbiz.mmAddToBoth(cbiz, "last_name", "Schwartz", "company", "Dabo Incorporated")
		# Person should increase and employee should increase
		person_count = self.reccount("person")
		self.assertEqual(person_count, 3)
		company_count = self.reccount("company")
		self.assertEqual(company_count, 2)
		emp_count = self.reccount("employees")
		self.assertEqual(emp_count, 3)

		# Add the same relation again. Nothing should change.
		pbiz.mmAddToBoth(cbiz, "last_name", "Schwartz", "company", "Dabo Incorporated")
		person_count = self.reccount("person")
		self.assertEqual(person_count, 3)
		company_count = self.reccount("company")
		self.assertEqual(company_count, 2)
		emp_count = self.reccount("employees")
		self.assertEqual(emp_count, 3)

		# Add new values to both; all tables should increase.
		pbiz.mmAddToBoth(cbiz, "last_name", "Jones", "company", "SmithCo")
		person_count = self.reccount("person")
		self.assertEqual(person_count, 4)
		company_count = self.reccount("company")
		self.assertEqual(company_count, 3)
		emp_count = self.reccount("employees")
		self.assertEqual(emp_count, 4)


	def test_reverse_mm_relationship(self):
		"""Add the person bizobj to the company bizobj as a MM target."""
		pbiz = self.person_biz
		cbiz = self.company_biz
		cbiz.addMMBizobj(pbiz, "employees", "company_id", "person_id")
		emp_count = self.reccount("employees")
		self.assertEqual(emp_count, 0)
		cbiz.seek("Acme Manufacturing", "company")
		cbiz.mmAssociateValue(pbiz, "last_name", "McNett")
		# Employee count should have increased
		emp_count = self.reccount("employees")
		self.assertEqual(emp_count, 1)
		self.assertEqual(self.reccount("company"), 1)
		pbiz.mmAssociateValue(cbiz, "company", "Amalgamated Industries")
		# Company count should have increased
		self.assertEqual(self.reccount("company"), 2)


	def test_multiple_mm_relationships(self):
		"""Make sure that more than one MM relationship works as expected."""	
		pbiz = self.person_biz
		cbiz = self.company_biz
		fbiz = self.fan_club_biz
		emp_count = self.reccount("employees")
		orig_fan_count = self.reccount("membership")
		orig_club_count = self.reccount("fan_club")
		pbiz.seek("Leafe", "last_name")
		leafe_pk = pbiz.getPK()
		pbiz.mmAssociateValues(fbiz, "performer", ["Ramones", "Green Day", "The Clash"])
		new_fan_count = self.reccount("membership")
		self.assertEqual(new_fan_count, orig_fan_count + 3)
		self.assertEqual(orig_club_count, self.reccount("fan_club"))
		# Now add an employment
		self.assertEqual(self.reccount("employees"), 0)
		pbiz.mmAssociateValue(cbiz, "company", "Acme Manufacturing")
		# Employee count should now be 1
		self.assertEqual(self.reccount("employees"), 1)
		# Fan club count should not have changed
		self.assertEqual(new_fan_count, self.reccount("membership"))

		# Add two new clubs that didn't exist
		pbiz.mmAssociateValues(fbiz, "performer", ["Wire", "Burning Spear"])
		new_fan_count = self.reccount("membership")
		new_club_count = self.reccount("fan_club")
		self.assertEqual(new_fan_count, orig_fan_count + 5)
		self.assertEqual(new_club_count, orig_club_count + 2)
		# Employee count should not have changed
		self.assertEqual(self.reccount("employees"), 1)


	def test_get_associated_values(self):
		"""Ensure that the mmGetAssociatedValues() method works correctly."""
		pbiz = self.person_biz
		fbiz = self.fan_club_biz
		fbiz.addMMBizobj(pbiz, "membership", "fan_club_id", "person_id")
		fbiz.seek("Ramones", "performer")
		fbiz.mmAssociateValues(pbiz, "last_name", ["McNett", "Leafe"])
		recs = fbiz.mmGetAssociatedValues(pbiz, "first_name")
		self.assertEqual(len(recs), 2)
		for rec in recs:
			self.assertEqual(rec.keys(), ["first_name"])
			self.assert_(rec["first_name"] in ("Paul", "Ed"))

		# Check for no associated records
		fbiz.seek("Pat Boone", "performer")
		recs = fbiz.mmGetAssociatedValues(pbiz, "first_name")
		self.assertEqual(len(recs), 0)


	def test_add_remove_mm_relationship(self):
		"""Ensures that addMMBizobj() and removeMMBizobj() work correctly."""
		pbiz = self.person_biz
		rbiz = self.restricted_biz
		num_orig_assoc = len(pbiz._associations)
		pbiz.addMMBizobj(rbiz, "rest_alloc", "person_id", "restricted_id")
		self.assertEqual(len(pbiz._associations), num_orig_assoc + 1)
		pbiz.removeMMBizobj(rbiz)
		self.assertEqual(len(pbiz._associations), num_orig_assoc)


	def test_db_insert_fails(self):
		"""If adding a value is not successful, ensure that the proper error is raised."""
		pbiz = self.person_biz
		rbiz = self.restricted_biz
		pbiz.addMMBizobj(rbiz, "rest_alloc", "person_id", "restricted_id")
		self.assertRaises(dException.DBQueryException, pbiz.mmAssociateValue,
				rbiz, "regular", "test")
		pbiz.removeMMBizobj(rbiz)



if __name__ == "__main__":
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_Many_To_Many)
	unittest.TextTestRunner(verbosity=2).run(suite)
