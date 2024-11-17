# -*- coding: utf-8 -*-
import unittest
import dabo.db


class Test_dConnectInfo(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init_noParms(self):
        def noParms():
            ci = dabo.db.dConnection()

        self.assertRaises(TypeError, noParms)

    def test_init_bogusParm(self):
        def bogusParm():
            ci = dabo.db.dConnection(bogus=1)

        self.assertRaises(bogusParm)

    def test_init_oneBogusParm(self):
        def anotherBogusParm():
            ci = dabo.db.dConnection(DbType="SQLite", Db=":memory:")

        self.assertRaises(anotherBogusParm)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(Test_dConnectInfo)
    unittest.TextTestRunner(verbosity=2).run(suite)
