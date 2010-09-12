# -*- coding: utf-8 -*-
import datetime
import decimal
import unittest
import dabo
from dabo.lib import getRandomUUID


class Test_dEditBox(unittest.TestCase):
	def setUp(self):
		app = self.app = dabo.dApp(MainFormClass=None)
		app.setup()
		frm = dabo.ui.dForm(Caption="test_dEditBox")
		self.edt = frm.addObject(dabo.ui.dEditBox)

	def tearDown(self):
		self.edt = None
		self.app = None

	def mockUserInput(self, str_val):
		edt = self.edt
		edt._gotFocus()
		edt.SetValue(str_val)
		edt._lostFocus()

	def testValue(self):
		edt = self.edt
		edt.Value = "This is a string"
		self.assertTrue(isinstance(edt.Value, basestring))
		self.assertEqual(edt.Value, "This is a string")
		self.mockUserInput("23")
		self.assertTrue(isinstance(edt.Value, basestring))
		self.assertEqual(edt.Value, "23")
		edt.Value = None
		self.assertEqual(edt.Value, None)
		self.mockUserInput("hi there")
		self.assertEqual(edt.Value, "hi there")


if __name__ == "__main__":
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_dEditBox)
	unittest.TextTestRunner(verbosity=2).run(suite)
