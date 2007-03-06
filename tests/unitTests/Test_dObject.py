"""
Unit Tests for dColors.py

Copyright (c) 2004 - 2007 Paul McNett, Ed Leafe, et. al.

Author: Nathan Lowrie

This file also provides the suite function.  The suite function will compile all of the test cases
defined in this file and load them into a test suite.  The function then returns the test suite.

If this file is run standalone, it will automatically run all of the test cases found in the file.
"""

import unittest
from dabo.dObject import *

class BaseTestdObject(unittest.TestCase):
	"""Provides setup methods for the dObject TestCases"""
	def setUp(self):
		self.dObject = dObject()

class TestApplicationProperty(BaseTestdObject):
	"""
	Rules for functionality:
		- The property is read only
		- dObjects should not be able to change the dApp but need to reference it
	
	Test List:
		- Setting dObject.Application should fail
		- Getting dObject.Application should return a known application
	"""
	
	def testSetApplication(self):
		"""Setting dObject.Application should fail"""
		def setApplication(app):
			self.dObject.Application = app
		self.assertRaises(AttributeError, setApplication, 42)
	
	def testGetApplication(self):
		"""Getting dObject.Application should return a known application"""
		test = dabo.dApp()
		result = self.dObject.Application
		self.assertEqual(test, result)

class TestBaseClassProperty(BaseTestdObject):
	"""
	Test List:
		- Setting dObject.BaseClass should fail
		- Getting dObject.BaseClass should return None when not subclassed
	"""
	def testSetBaseClass(self):
		"""Setting dObject.BaseClass should fail"""
		def setBaseClass(self):
			self.dObject.BaseClass = 42
		self.assertRaises(AttributeError, setBaseClass, 42)
	
	def testGetBaseClassNoSubclass(self):
		"""Getting dObject.BaseClass should return None when not subclassed"""
		self.assertEqual(None, self.dObject.BaseClass)


#used for running this module bare without the test suite
if __name__ == "__main__":
	unittest.main()