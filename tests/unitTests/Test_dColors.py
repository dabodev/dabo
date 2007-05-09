"""
Unit Tests for dColors.py

Copyright (c) 2004 - 2007 Paul McNett, Ed Leafe, et. al.

Author: Nathan Lowrie

This file also provides the suite function.  The suite function will compile all of the test cases
defined in this file and load them into a test suite.  The function then returns the test suite.

If this file is run standalone, it will automatically run all of the test cases found in the file.
"""

import unittest
from dabo import dColors
import random


class TestHexToDec(unittest.TestCase):
	"""
	Rules for class functionality:
		- Digits 0-9 and Letters A-F are valid hex characters
		- Hex values can only be positive integers or zero
		- Leading Zeros do not affect hex values
		- Both upper and lower case letters are allowed in Hex Values
	
	Class Requirements for proper behavior go here:
		- hexToDec should convert all valid hex strings to decimal
		- hexToDec should fail when recieving a non-hex character
		- hexToDec should fail when recieving a non-sting input
		- hexToDec should accept both upper and lowercase characters
		- hexToDec should return the same result for string and string.upper()
		- hexToDec should return the same result for number and '0'*n + number
	"""
	
	knownValues = (("0",0), ("1",1), ("2",2), ("3",3), ("4",4), ("5",5), ("6",6), ("7",7), ("8",8), ("9",9),
				  ("A",10), ("B",11), ("C",12), ("D",13), ("E",14), ("F",15), ("10",16), ("1A",26), ("1F",31),
				  ("20",32), ("A0",160), ("FF",255), ("100",256), ("FFFFFFFF",4294967295))
	
	def testKnownValues(self):
		"""hexToDec should give known result with known input"""
		for hex, integer in self.knownValues:
			result = dColors.hexToDec(hex)
			self.assertEqual(integer, result)
	
	def testBadHexInput(self):
		"""hexToDec should fail when a non-hex character is entered"""
		self.assertRaises(dColors.InvalidCharError, dColors.hexToDec, "#$%uidkxb")
	
	def testNoneStringInput(self):
		"""hexToDec should fail when a non-string variable is entered"""
		self.assertRaises(dColors.TypeError, dColors.hexToDec, 92)
	
	def testCaseInsensitive(self):
		"""hexToDec should accept and give same result for both upper and lowercase input"""
		lower = dColors.hexToDec("abcdef123")
		upper = dColors.hexToDec("ABCDEF123")
		self.assertEqual(lower, upper)
	
	def testLeadingZeros(self):
		"""testing hexToDec(number) = hexToDec('00'+number)"""
		number = "FF"
		result = dColors.hexToDec(number)
		zeroResult = dColors.hexToDec("000" + number)
		self.assertEqual(result, zeroResult)

class TestTupleHexConversion(unittest.TestCase):
	"""
	Rules for class functionality:
		- Tuple must contain only 3 elements
		- Tuple elemens must be inegers in the range of 0-255
		- Digits 0-9 and Letters A-F are valid hex characters
		- Hex values can only be positive integers or zero
		- Leading Zeros do not affect hex values
		- Both upper and lower case letters are allowed in Hex Values
	
	Class Requirements for proper behavior go here:
		- tupleToHex should convert all valid tuples to hex strings
		- tupleToHex should fail when len(tuple) is not 3
		- tupleToHex should fail when all elements in tuple are not integers
		- colorTupleFromHex should convert all hex strings into tuples with 3 integer elements
		- colorTupleFromHex should fail with a non-hex character
		- colorTupleFromHex should ignore leading zeros and convert the correct value
		- colorTupleFromHex should fail if the hex value is bigger than 16777215
		- tuple = tupleToHex(colorTupleFromHex(tuple)) for all valid input values
	"""
	
	knownValues = (("#000000",(0,0,0)), ("#000001",(0,0,1)), ("#000101",(0,1,1)), ("#010101",(1,1,1)),
				  ("#898989",(137,137,137)), ("#FFFFFF",(255,255,255)), ("#AAAAAA",(170,170,170)), 
				  ("#A9A9A9",(169,169,169)), ("#0A0A0A",(10,10,10)), ("#090909",(9,9,9)),
				  ("#1A2BF3",(26,43,243)), ("#3F029E",(63,02,158)), ("#707070",(112,112,112)),
				  ("#6F6F6F",(111,111,111)), ("#8A8A8A",(138,138,138)), ("#00FF80",(0,255,128)),
				  ("#1F575E",(31,87,94)), ("#89092B",(137,9,43)))
	
	#Test happy paths
	def testKnownValuesTupleToHex(self):
		"""tupleToHex should give known result with known input"""
		for hex, tuple in self.knownValues:
			result = dColors.tupleToHex(tuple)
			self.assertEqual(result, hex)
	
	def testKnownValuesHexToTuple(self):
		"""colorTupleFromHex should give known result with known input"""
		for hex, tuple in self.knownValues:
			result = dColors.colorTupleFromHex(hex)
			self.assertEqual(result, tuple)
	
	def testSanity(self):
		"""tuple = tupleToHex(colorTupleFromHex(tuple)) for range of valid input values"""
		#All inputs was way too many
		for run in range(1000):
			a, b, c = random.choice(range(256)), random.choice(range(256)), random.choice(range(256))
			self.assertEqual((a,b,c), dColors.colorTupleFromHex(dColors.tupleToHex((a,b,c))))
	
	#Test Errors
	def testTupleToHexNegativeInput(self):
		"""tupleToHex should fail with a negative integer input"""
		self.assertRaises(dColors.RgbValueError, dColors.tupleToHex, (-1,-1,-1))
	
	def testTupleToHexIntegerTooLargeInput(self):
		"""tupleToHex should fail with an input larger than 255"""
		self.assertRaises(dColors.RgbValueError, dColors.tupleToHex, (256, 256, 256))
	
	def testTupleToHexLessThanThreeElements(self):
		"""tupleToHex should fail with less than 3 elements in the tuple"""
		self.assertRaises(dColors.LengthError, dColors.tupleToHex, (1,1))
	
	def testTupleToHexMoreThanThreeElements(self):
		"""tupleToHex should fail with more than 3 elements in the tuple"""
		self.assertRaises(dColors.LengthError, dColors.tupleToHex, (1,1,1,1))
	
	def testTupleToHexNonIntegerInput(self):
		"""tupleToHex should fail if anyone of the elements is a non-integer"""
		self.assertRaises(dColors.IntegerTypeError, dColors.tupleToHex, ("string", 1, 1))
		self.assertRaises(dColors.IntegerTypeError, dColors.tupleToHex, (1, "string", 1))
		self.assertRaises(dColors.IntegerTypeError, dColors.tupleToHex, (1, 1, "string"))
	
	def testHexToTupleBadHexInput(self):
		"""colorTupleFromHex should fail when a non-hex character is entered"""
		self.assertRaises(dColors.InvalidCharError, dColors.colorTupleFromHex, "#$%uidkxb")
	
	def testHexToTupleCaseInsensitive(self):
		"""colorTupleFromHex should accept and give same result for both upper and lowercase input"""
		lower = dColors.colorTupleFromHex("abcdef123")
		upper = dColors.colorTupleFromHex("ABCDEF123")
		self.assertEqual(lower, upper)
	
	#misc. tests
	def testHexToTupleLeadingZeros(self):
		"""testing colorTupleFromHex(number) = colorTupleFromHex('00'+number)"""
		number = "0A0CFF"
		result = dColors.colorTupleFromHex(number)
		zeroResult = dColors.colorTupleFromHex("000" + number)
		self.assertEqual(result, zeroResult)

class TestColorTupleFromName(unittest.TestCase):
	"""
	Rules for class functionality:
		- color names are strings predefined in a dictionary
		- if a name is not in the dictionary, treat it as a hex string or color tuple string
	
	Class Requirements for proper behavior go here:
		- colorTupleFromName should return a valid color tuple for all valid color name inputs
		- colorTupleFromName should return a valid color tuple for all valid hex string inputs
		- colorTupleFromName should return a valid color tuple for all valid color tuple string inputs
		- colorTupleFromName should fail when recieving an input that is not a valid color name,
		  hex string input, or color tuple string
	"""
	
	#happy path tests
	def testKnownColorValues(self):
		"""colorTupleFromName should return a known value for a known color name input"""
		for name in dColors.colorDict.keys():
			result = dColors.colorTupleFromName(name)
			self.assertEqual(result, dColors.colorDict[name])
	
	#need to refactor these next 2.  Test smells for repeated code tests
	def testKnownHexStringValues(self):
		"""colorTupleFromName should return a known value for a known hex string input"""
		self.assertEqual(dColors.colorTupleFromName("#010101"), (1, 1, 1))
	
	def testKnownColorTupleStringValues(self):
		"""colorTupleFromName should return a known value for a known color tuple string input"""
		self.assertEqual(dColors.colorTupleFromName("(1, 1, 1)"), (1, 1, 1))
	
	#error tests
	def testColorNameError(self):
		"""colorTupleFromName should fail when given a string that is not a valid color name, hex string,
		or color tuple string"""
		self.assertRaises(KeyError, dColors.colorTupleFromName, "Some Invalid Color Name")

class TestColorTupleFromString(unittest.TestCase):
	"""
	Rules for class functionality:
		- tuple strings are in form of "(int, int, int)"
		- Color tuples must have three integers
		- Integers must be between 0-255
	
	Class Requirements for proper behavior go here:
		- colorTupleFromString should return a valid tuple for all valid results
		- colorTupleFromString should fail when recieving an improperly formatted string
		- colorTupleFromString should fail when there are not three elements in tuple representation of string
		- colorTupleFromString should fail when elements in the string are not integers
		- colorTupleFromString should fail when integer elements are not in range 0-255
	"""
	
	#happy path tests
	def testKnownValues(self):
		"""colorTupleFromString should return known results for known values"""
		for a in range(256):
			test = "(%i, %i, %i)" % (a, 255-a, a)
			result = dColors.colorTupleFromString(test)
			self.assertEqual((a, 255-a, a), result)
			
			test = "(%i, %i, %i)" % (a, a, a)
			result = dColors.colorTupleFromString(test)
			self.assertEqual((a, a, a), result)
	
	#Error Path Tests
	def testMissingCommas(self):
		"""colorTupleFromString should fail with a lack of commas between integer values"""
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1 1, 1)")
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1, 1 1)")
	
	def testMissingParentheses(self):
		"""colorTupleFromString should fail with a lack of parentheses surrounding the tuple"""
		self.assertRaises(KeyError, dColors.colorTupleFromString, "1, 1, 1)")
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1, 1, 1")
	
	def testTupleTooSmall(self):
		"""colorTupleFromString should fail when the number of integer elements in the string is below 3"""
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1, 1)")
	
	def testTupleTooLarge(self):
		"""colorTupleFromString should fail when the number of integer elements in the string is above 3"""
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1, 1, 1, 1)")
	
	def testTupleNonInteger(self):
		"""colorTupleFromString should fail when one or more of the numbers are non-integers"""
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1.5, 1, 1)")
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1, 1.5, 1)")
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1, 1, 1.5)")
	
	def testIntegerTooLarge(self):
		"""colorTupleFromTest should fail when one or more of the integers is above 255"""
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(256, 1, 1)")
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1, 256, 1)")
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1, 1, 256)")
	
	def testIntegerTooSmall(self):
		"""colorTupleFromTest should fail when one or more of the integers is below 0"""
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(-1, 1, 1)")
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1, -1, 1)")
		self.assertRaises(KeyError, dColors.colorTupleFromString, "(1, 1, -1)")



#used for running this module bare without the test suite
if __name__ == "__main__":
	unittest.main()