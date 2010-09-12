# -*- coding: utf-8 -*-
import unittest
import tempfile
import os
import shutil
import sys
import dabo
from dabo.lib import utils


def fmtPath(testpath):
    """Format a file path in os.specific format"""
    return testpath.replace("/",os.sep)

def createTempFile(filename):
    f = open(filename,"w")
    f.close()


class Test_Utils(unittest.TestCase):
	def setUp(self):
		"""Prepare test environment (basic setup shared by all tests)"""
		# Determine where the temp directory is and run the tests there
		self.tempTestDir = tempfile.gettempdir() + os.sep + "relpath_tests_dir"
		try:
			shutil.rmtree(self.tempTestDir)
		except OSError:
			pass
		os.mkdir(self.tempTestDir)
		os.chdir(self.tempTestDir)
		# Create directory structure
		os.makedirs("a/b/c/")
		os.makedirs("a1/b1/c1/d1")
		# Create a couple of files to point to
		createTempFile("file1")
		createTempFile("a/b/file2")
		createTempFile("a1/b1/c1/d1/file3")


	def tearDown(self):
		"""Bin the temp test dir and everything in it"""
		os.chdir(self.tempTestDir)
		os.chdir(os.pardir)
		shutil.rmtree("relpath_tests_dir")


	def test_StringFuncs(self):
		teststring = "This is a very long string with Unicode chars: Žš”¯ and 1234567890"
		revstring = "0987654321 dna ¯”šŽ :srahc edocinU htiw gnirts gnol yrev a si sihT"
		self.assertEqual(utils.reverseText(teststring), revstring)
		cap = "&File"
		self.assertEqual(utils.cleanMenuCaption(cap), "File")
		self.assertEqual(utils.cleanMenuCaption(cap, "e"), "&Fil")


	def test_DictFuncs(self):
		testdict = {u"First": 1, u"Second": 2, "Th”rd": 3}
		ds = utils.dictStringify(testdict)
		for kk in ds.keys():
			self.assertEqual(type(kk), str)


	def test_Pathing(self):
		prfx = utils.getPathAttributePrefix()
		pth = "a/b/file2"
		self.assertEqual(utils.resolvePath(pth), "a/b/file2")
		pth2 = "../../file2"
		self.assertEqual(utils.resolvePath(pth2, "a1/b1"), "../../file2")
		self.assertEqual(utils.relativePath(pth), "a/b/file2")
		self.assertEqual(utils.relativePath(pth2), "../../file2")
		self.assertEqual(utils.relativePath(pth,pth2), "../tmp/relpath_tests_dir/a/b/file2")
		self.assertEqual(utils.relativePathList(pth,pth2), ["..", "tmp", "relpath_tests_dir", "a", "b", "file2"])
		atts = {"Foo": "Bar", "ThePath": "%s../some/file.txt" % prfx}
		utils.resolveAttributePathing(atts, os.getcwd())
		self.assertEqual(atts, {"Foo": "Bar", "ThePath": "../some/file.txt"})
		atts = {"Foo": "Bar", "ThePath": "%sa/b/file2" % prfx}
		utils.resolveAttributePathing(atts, os.getcwd())
		self.assertEqual(atts, {"Foo": "Bar", "ThePath": "a/b/file2"})
		atts = {"Foo": "Bar", "ThePath": "%s../a/b/file2" % prfx}
		utils.resolveAttributePathing(atts, "a1/")
		self.assertEqual(atts, {"Foo": "Bar", "ThePath": "../a/b/file2"})

if __name__ == "__main__":
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_Utils)
	unittest.TextTestRunner(verbosity=2).run(suite)
