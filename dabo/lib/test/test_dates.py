import unittest
import datetime
import dabo
from dabo.lib import dates

year = datetime.date.today().year
year_str4 = str(year)
year_str2 = year_str4[-2:]

class Test_Dates(unittest.TestCase):

	def test_getDateFromString(self):
		formats = ["ISO8601", "YYYYMMDD", "YYMMDD", "MMDD"]
		tests = ["0503", "20060503", "2006-05-03", "060503"]
		expected_date = datetime.date(year, 05, 03)

		tests = ((["ISO8601"], "%s-05-03" % year_str4, expected_date),
		         (["YYYYMMDD"], "%s0503" % year_str4, expected_date),
		         (["YYMMDD"], "%s0503" % year_str2, expected_date),
		         (["MMDD"], "0503", expected_date),
		         (["ISO8601"], "%s05-03" % year_str4, None),)
		for test in tests:
			self.assertEqual(dates.getDateFromString(test[1], test[0]), test[2])


if __name__ == "__main__":
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_Dates)
	unittest.TextTestRunner(verbosity=2).run(suite)
