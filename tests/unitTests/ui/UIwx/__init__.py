"""Provide an import for all of the files in the module.  Also provides a function called 
suite which will return a TestSuite of everything in the module.
"""

import unittest

#suiteList should contain all of the suite that are recieved from the modules and TestCases
suiteList = []

#import test module suites and add to list here


#import TestCase suites and add to list here
import Test_dTextBox
suiteList.append(unittest.TestLoader().loadTestsFromModule(Test_dTextBox))

#setup a suite and return it
def suite():
    return unittest.TestSuite(suiteList)