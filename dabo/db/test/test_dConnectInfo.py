# -*- coding: utf-8 -*-
import unittest

from .. import db


class Test_dConnectInfo(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init_noParms(self):
        def noParms():
            ci = db.dConnection()

        self.assertRaises(TypeError, noParms)

    def test_init_bogusParm(self):
        def bogusParm():
            ci = db.dConnection(bogus=1)

        self.assertRaises(bogusParm)

    def test_init_oneBogusParm(self):
        def anotherBogusParm():
            ci = db.dConnection(DbType="SQLite", Db=":memory:")

        self.assertRaises(anotherBogusParm)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(Test_dConnectInfo)
    unittest.TextTestRunner(verbosity=2).run(suite)
