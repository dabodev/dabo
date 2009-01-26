# -*- coding: utf-8 -*-
import unittest
import dabo


class Test_dConnectInfo(unittest.TestCase):
	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_init_noParms(self):
		def noParms():
			co = dabo.db.dConnection()
		self.assertRaises(TypeError, noParms)

	def test_init_bogusParm(self):
		def bogusParm():
			co = dabo.db.dConnection(bogus=1)
		self.assertRaises(TypeError, bogusParm)

	def test_init_oneBogusParm(self):
		def anotherBogusParm():
			co = dabo.db.dConnection(DbType="SQLite", Db=":memory:")
		self.assertRaises(TypeError, anotherBogusParm)

if __name__ == "__main__":
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_dConnectInfo)
	unittest.TextTestRunner(verbosity=2).run(suite)
