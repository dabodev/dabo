"""Master test control for the test suite.  Tests for all Tiers plus the lib section of Dabo are imported and run from here.

This will import the DB, Biz, Lib, and UI Tiers for the test.  We will add the test files manually in the __init__.py files
in each module.  The init files and every Test Case file must provide a function suite() which will return a unittest.TestSuite
object that encompasses the all of the test cases and suite within that file or module.  See the sample init and testCase files
for more information.
"""

import unittest
import coverage
import sys

coverage.erase()
coverage.start()

import dabo
import db
import biz
import lib
import ui

suiteList = [db.suite(), biz.suite(), lib.suite(), ui.suite()]

#import any tests for the main dabo folder
import Test_dColors
suiteList.append(unittest.TestLoader().loadTestsFromModule(Test_dColors))
import Test_dObject
suiteList.append(unittest.TestLoader().loadTestsFromModule(Test_dObject))


allTiersTestSuite = unittest.TestSuite(suiteList)
unittest.TextTestRunner(verbosity=2).run(allTiersTestSuite)

coverage.stop()
coverage.report([dabo.dColors, dabo.dObject])