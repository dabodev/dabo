# -*- coding: utf-8 -*-
import datetime
import decimal
import unittest
import dabo
from dabo.lib import getRandomUUID


class Test_dTextBox(unittest.TestCase):
	def setUp(self):
		app = self.app = dabo.dApp(MainFormClass=None)
		app.setup()
		frm = dabo.ui.dForm(Caption="test_dTextBox")
		self.txt = frm.addObject(dabo.ui.dTextBox)

	def tearDown(self):
		self.txt = None
		self.app = None

	def mockUserInput(self, str_val, lose_focus=True):
		txt = self.txt
		txt._gotFocus()
		txt.SetValue(str_val)
		if lose_focus:
			txt._lostFocus()

	def testStringValue(self):
		txt = self.txt
		txt.Value = "This is a string"
		self.assertTrue(isinstance(txt.Value, basestring))
		self.assertEqual(txt.Value, "This is a string")
		self.mockUserInput("23")
		self.assertTrue(isinstance(txt.Value, basestring))
		self.assertEqual(txt.Value, "23")
		txt.Value = None
		self.assertEqual(txt.Value, None)
		self.mockUserInput("hi there")
		self.assertEqual(txt.Value, "hi there")

	def testFloatValue(self):
		txt = self.txt
		txt.Value = 1.23
		self.assertTrue(isinstance(txt.Value, float))
		self.assertEqual(txt.Value, 1.23)
		self.mockUserInput("23")
		self.assertTrue(isinstance(txt.Value, float))
		self.assertEqual(txt.Value, 23)
		txt.Value = None
		self.assertEqual(txt.Value, None)
		self.mockUserInput("hi there")
		self.assertEqual(txt.Value, None)
		self.mockUserInput("42")
		self.assertEqual(txt.Value, 42)
		self.assertTrue(isinstance(txt.Value, float))


	def testIntValue(self):
		txt = self.txt
		txt.Value = 23
		self.assertTrue(isinstance(txt.Value, int))
		self.assertEqual(txt.Value, 23)
		self.mockUserInput("323.75")
		self.assertTrue(isinstance(txt.Value, int))
		self.assertEqual(txt.Value, 23)
		txt.Value = None
		self.assertEqual(txt.Value, None)
		self.mockUserInput("hi there")
		self.assertEqual(txt.Value, None)
		self.mockUserInput("42")
		self.assertEqual(txt.Value, 42)
		self.assertTrue(isinstance(txt.Value, int))

	def testDateValue(self):
		txt = self.txt
		txt.Value = datetime.date.today()
		self.assertTrue(isinstance(txt.Value, datetime.date))
		self.assertEqual(txt.Value, datetime.date.today())
		self.mockUserInput("2006-05-03")
		self.assertTrue(isinstance(txt.Value, datetime.date))
		self.assertEqual(txt.Value, datetime.date(2006,5,3))
		txt.Value = None
		self.assertEqual(txt.Value, None)
		self.mockUserInput("hi there")
		self.assertEqual(txt.Value, None)
		self.mockUserInput("2006-05-03")
		self.assertEqual(txt.Value, datetime.date(2006,5,3))

	def testDateTimeValue(self):
		txt = self.txt
		txt.Value = val = datetime.datetime.now()
		self.assertTrue(isinstance(txt.Value, datetime.datetime))
		self.assertEqual(txt.Value, val)
		self.mockUserInput("bogus datetime")
		self.assertTrue(isinstance(txt.Value, datetime.datetime))
		self.assertEqual(txt.Value, val)
		txt.Value = None
		self.assertEqual(txt.Value, None)

	def testDecimalValue(self):
		txt = self.txt
		txt.Value = decimal.Decimal("1.23")
		self.assertTrue(isinstance(txt.Value, decimal.Decimal))
		self.assertEqual(txt.Value, decimal.Decimal("1.23"))
		self.mockUserInput("15badinput")
		self.assertTrue(isinstance(txt.Value, decimal.Decimal))
		self.assertEqual(txt.Value, decimal.Decimal("1.23"))
		txt.Value = None
		self.assertEqual(txt.Value, None)
		self.mockUserInput("hi there")
		self.assertEqual(txt.Value, None)
		self.mockUserInput("42.23")
		self.assertEqual(txt.Value, decimal.Decimal("42.23"))
		self.assertTrue(isinstance(txt.Value, decimal.Decimal))

	def testFlushValue(self):
		txt = self.txt
		txt.Form.df = None

		txt.DataSource = "form"
		txt.DataField = "df"
		txt.Value = "Paul"
		self.assertEqual(txt.Value, "Paul")
		self.assertEqual(txt.Value, txt.Form.df)

		self.mockUserInput("kk")
		self.assertEqual(txt.Value, "kk")

		self.mockUserInput("pp", lose_focus=False)
		self.assertEqual(txt.Value, "pp")
		self.assertEqual(txt.Form.df, "kk")
		txt.flushValue()
		self.assertEqual(txt.Form.df, "pp")
		self.assertEqual(txt.Value, "pp")


if __name__ == "__main__":
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_dTextBox)
	unittest.TextTestRunner(verbosity=2).run(suite)
