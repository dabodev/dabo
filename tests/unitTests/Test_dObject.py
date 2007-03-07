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

class TestNameProperty(BaseTestdObject):
	"""
	Test List:
		- Set dObject.Name to n.  dObject.Name should be equal to n. (round trip test)
		- dObject.Name should return '?' if no name is assigned
		- dObject.Name should fail when given a non-string input
	"""
	
	def testRoundTrip(self):
		"""Set dObject.Name to n.  dObject.Name should be equal to n. (round trip test)"""
		self.dObject.Name = "Test Name"
		self.assertEqual("Test Name", self.dObject.Name)
	
	def testNoNameSet(self):
		"""dObject.Name should return '?' if no name is assigned"""
		self.assertEqual('?', self.dObject.Name)
	
	def testFailOnNonStringInput(self):
		"""dObject.Name should fail when given a non-string input"""
		def setName(val):
			self.dObject.Name = val
		self.assertRaises(TypeError, setName, 42)

class TestParentProperty(BaseTestdObject):
	"""
	Test List:
		- Set dObject.Parent to n. dObject.Parent should be equal to n. (round trip test)
		- dObject.Parent should return None if there is no parent
	"""
	
	def testRoundTrip(self):
		"""Set dObject.Parent to n. dObject.Parent should be equal to n. (round trip test)"""
		test = dObject()
		test.Parent = self.dObject
		self.assertEqual(test.Parent, self.dObject)
	
	def testNoParentSet(self):
		"""dObject.Parent should return None if there is no parent"""
		self.assertEqual(self.dObject.Parent, None)

class TestPreferenceManagerProperty(BaseTestdObject):
	"""
	Test List:
		- Set dObject.PreferenceManager to n. dObject.PreferenceManagier should be equal to n. (round trip test)
		- dObject.PreferenceManager should fail when set to an object not of type dPref
		- initial conditon test???
	"""
	
	def testRoundTrip(self):
		"""Set dObject.PreferenceManager to n. dObject.PreferenceManagier should be equal to n. (round trip test)"""
		from dabo.dPref import dPref
		testDPref = dPref()
		self.dObject.PreferenceManager = testDPref
		self.assertEqual(testDPref, self.dObject.PreferenceManager)
	
	def testSetFailOnNondPrefValue(self):
		"""dObject.PreferenceManager should fail when set to an object not of type dPref"""
		def setPreferenceManager(val):
			self.dObject.PreferenceManager = val
		self.assertRaises(TypeError, setPreferenceManager, 42)
	
	#TODO: NEED A TEST HERE FOR INITIAL CONDITION


#used for running this module bare without the test suite
if __name__ == "__main__":
	unittest.main()