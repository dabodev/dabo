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
		- Setting dObject.BaseClass should fail for all inputs
		- Getting dObject.BaseClass should return None when not subclassed
	"""
	def testSetBaseClass(self):
		"""Setting dObject.BaseClass should fail for all inputs"""
		def setBaseClass(self):
			self.dObject.BaseClass = 42
		self.assertRaises(AttributeError, setBaseClass, 42)
	
	def testGetBaseClassNoSubclass(self):
		"""Getting dObject.BaseClass should return None when not subclassed"""
		self.assertEqual(None, self.dObject.BaseClass)

class TestBasePrefKeyProperty(BaseTestdObject):
	"""
	Test List:
		- (setting/getting) dObject.BasePrefKey should yield the original value
		- dObject.BasePrefKey should return '' if not set
		- setting dObject.BasePrefKey should fail if value is not a string
	"""
	def testRoundTripBasePrefKey(self):
		"""(setting/getting) dObject.BasePrefKey should yield the original value"""
		test = "original value"
		self.dObject.BasePrefKey = test
		self.assertEqual(test, self.dObject.BasePrefKey)
	
	def testBasePrefKeyNotSet(self):
		"""dObject.BasePrefKey should return '' if not set"""
		self.assertEqual('', self.dObject.BasePrefKey)
	
	def testBasePrefFailOnNonString(self):
		"""setting dObject.BasePrefKey should fail if value is not a string"""
		def setBasePrefKey(val):
			self.dObject.BasePrefKey = val
		self.assertRaises(TypeError, setBasePrefKey, 42)

class TestClassProperty(BaseTestdObject):
	"""
	Test List:
		- setting dObject.Class should fail for all inputs
		- dObject.Class should return the dObject class when instansiated
		- dObject.Class should return A when A subclasses dObject and is instansiated
	"""
	
	def testSetClassShouldFail(self):
		"""setting dObject.Class should fail for all inputs"""
		def setClass(val):
			self.dObject.Class = val
		self.assertRaises(AttributeError, setClass, 42)
	
	def testGetClassNoSubclass(self):
		"""dObject.Class should return the dObject class when instansiated"""
		self.assertEqual(dObject, self.dObject.Class)
	
	def testGetClassWithSubclass(self):
		"""dObject.Class should return A when A subclasses dObject and is instansiated"""
		class a(dObject):
			pass
		obj = a()
		self.assertEqual(a, obj.Class)


#used for running this module bare without the test suite
if __name__ == "__main__":
	unittest.main()