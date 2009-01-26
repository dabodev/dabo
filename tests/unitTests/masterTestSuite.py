"""Master test control for the test suite.  

This will import the DB, Biz, Lib, and UI Tiers for the test.  We will add 
the test files manually in the __init__.py files in each module.  The init 
files and every Test Case file must provide a function suite() which will 
return a unittest.TestSuite object that encompasses the all of the test 
cases and suite within that file or module.  See the sample init and 
testCase files for more information.
"""

import unittest
try:
	import coverage
except ImportError:
	coverage = None
import sys

if coverage:
	coverage.erase()
	coverage.start()

	coverage.exclude('if __name__ == "__main__":')

import dabo
dabo.ui.loadUI('wx')

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

if coverage:
	coverage.stop()
	#You can uncomment this to get test coverage on a particular module, but if you want to
	#see the entire report for dabo, run "python CoverageReport.py".  I would pipe it to a file though
	#coverage.report([dabo.dColors, dabo.dObject, dabo])
