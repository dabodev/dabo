"""Test Case for the dTextbox class.

To import this file into the test suite run:

import Test_dTextBox
suiteList.append(unittest.TestLoader().loadTestsFromModule(Test_dTextBox))

If this file is run standalone, it will automatically run all of the test cases found in the file.
"""

import unittest
import dabo
from mock import Mock
dabo.ui.loadUI('wx')

#We want the dApp and mainForm to persist through the settings for speed sake
#NOTE:  It would be really good if we could extract all of this out so we don't have
#		to do it for every single widget test
App = dabo.dApp()
App.setup()

testForm = dabo.ui.dForm()

#Set up a movabe
class BaseTestdTextBox(unittest.TestCase):
	"""This class will set up a the fresh part of the picture which is the dTextBox
	object being instantiated.  All Test Cases should subclass this.
	"""
	
	def setUp(self):
		self.testTextBox = dabo.ui.dTextBox(testForm)
	
	def tearDown(self):
		del self.testTextBox
	
	def setProperty(self, propertyInfo):
		"""setProperty(self, (object.property, val))"""
		exec("%s = %s" % propertyInfo)


class TestTextLengthProperty(BaseTestdTextBox):
	"""
	Test List:
		- Set TextLength to n.  TextLength should be equal to n. (round trip test)
		- setting TextLength should fail with a value that can't be converted to an int
		- Set TextLength to n.  Value should remain the same if < n
		- Set TextLength to n.  Value should remain the same if = n
		- Set TextLength to n.  Value should now be dTextBox.Value[:n] if > n
		- setting TextLength to a negative number should fail.
		- setting TextLength to None should allow any length
		- setting TextLength to Zero should fail.
		- TextLength = n.  Set Value to string with length > n should set only string[:n].
	"""
	
	def testRoundTrip(self):
		"""Set TextLength to n.  TextLength should be equal to n. (round trip test)"""
		for x in range(1,15):
			self.testTextBox.TextLength = x
			self.assertEqual(self.testTextBox.TextLength, x)
			self.testTextBox.TextLength = str(x)
			self.assertEqual(self.testTextBox.TextLength, x)
	
	def testNonIntegerInput(self):
		"""setting TextLength should fail with a value that can't be converted to an int"""
		self.assertRaises(ValueError, self.setProperty, ("self.testTextBox.TextLength", '"not a number"'))
		self.assertRaises(TypeError, self.setProperty, ("self.testTextBox.TextLength", "(234, 543, 'ho hum')"))
	
	def testValueLessThanLength(self):
		"""Set TextLength to n.  Value should remain the same if < n"""
		self.testTextBox.Value = "Length is 12"
		self.testTextBox.TextLength = 13
		self.assertEqual(self.testTextBox.Value, "Length is 12")
	
	def testValueEqualToLength(self):
		"""Set TextLength to n.  Value should remain the same if = n"""
		self.testTextBox.Value = "Length is 12"
		self.testTextBox.TextLength = 12
		self.assertEqual(self.testTextBox.Value, "Length is 12")
	
	def testValueGreaterThanLength(self):
		"""Set TextLength to n.  Value should now be dTextBox.Value[:n] if > n"""
		self.testTextBox.Value = "Length is 12"
		self.testTextBox.TextLength = 11
		self.assertEqual(self.testTextBox.Value, "Length is 1")
	
	def testFailOnNegativeInput(self):
		"""setting TextLength to a negative number should fail."""
		self.assertRaises(ValueError, self.setProperty, ("self.testTextBox.TextLength", "-1"))
	
	def testNoneIsAnyLength(self):
		"""setting TextLength to None should allow any length"""
		self.testTextBox.TextLength = None
		self.testTextBox.Value = "aaaaa"*100
		self.assertEqual(self.testTextBox.Value, "aaaaa"*100)
	
	def testFailOnZeroInput(self):
		"""setting TextLength to Zero should fail."""
		self.assertRaises(ValueError, self.setProperty, ("self.testTextBox.TextLength", "-0"))
	
	def testNoInsertionUponLimitReached(self):
		"""extLength = n.  Set Value to string with length > n should set only string[:n]."""
		self.testTextBox.TextLength = 4
		self.testTextBox.Value = "Value"
		self.assertEqual(self.testTextBox.Value, "Valu")


if __name__ == "__main__":
	unittest.main()