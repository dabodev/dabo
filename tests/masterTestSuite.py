"""Master test control for the test suite.  Tests for all Tiers plus the lib section of Dabo are imported and run from here.

This will import the DB, Biz, Lib, and UI Tiers for the test.  We will add the test files manually in the __init__.py files
in each module.  The init files and every Test Case file must provide a function suite() which will return a unittest.TestSuite
object that encompasses the all of the test cases and suite within that file or module.  See the sample init and testCase files
for more information.
"""

import unittest

import db
import biz
import lib
import ui

suiteList = [db.suite(), biz.suite(), lib.suite(), ui.suite()]

allTiersTestSuite = unittest.TestSuite(suiteList)
unittest.TextTestRunner(verbosity=2).run(allTiersTestSuite)