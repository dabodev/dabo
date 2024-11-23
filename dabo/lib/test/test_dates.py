# -*- coding: utf-8 -*-
import unittest
import datetime
import dabo
from dabo.lib import dates
from dabo.lib.utils import ustr

year = datetime.date.today().year
year_str4 = ustr(year)
year_str2 = year_str4[-2:]


class Test_Dates(unittest.TestCase):
    def test_getDateFromString(self):
        formats = ["ISO8601", "YYYYMMDD", "YYMMDD", "MMDD"]
        tests = ["0503", "20060503", "2006-05-03", "060503"]
        expected_date = datetime.date(year, 0o5, 0o3)

        tests = (
            (["ISO8601"], "%s-05-03" % year_str4, expected_date),
            (["YYYYMMDD"], "%s0503" % year_str4, expected_date),
            (["YYMMDD"], "%s0503" % year_str2, expected_date),
            (["MMDD"], "0503", expected_date),
            (["ISO8601"], "%s05-03" % year_str4, None),
        )
        for test in tests:
            self.assertEqual(dates.getDateFromString(test[1], test[0]), test[2])

    def test_getDateTimeFromString(self):
        formats = ["ISO8601", "YYYYMMDDHHMMSS"]
        tests = ["0503", "20060503", "2006-05-03", "060503"]
        expected_date = datetime.datetime(year, 0o5, 0o3, 12, 15, 00)

        tests = (
            (["ISO8601"], "%s-05-03 12:15:00" % year_str4, expected_date),
            (["YYYYMMDDHHMMSS"], "%s0503121500" % year_str4, expected_date),
        )
        for test in tests:
            self.assertEqual(dates.getDateTimeFromString(test[1], test[0]), test[2])

    def test_getStringFromDate(self):
        test_str = "2006-05-03"
        test_date = dates.getDateFromString(test_str)
        dabo.dateFormat = "%Y-%m-%d"
        self.assertEqual(dates.getStringFromDate(test_date), test_str)

    def test_getStringFromDateTime(self):
        test_str = "2006-05-03 12:15:00"
        test_datetime = dates.getDateTimeFromString(test_str)
        dabo.dateTimeFormat = "%Y-%m-%d %H:%M:%S"
        self.assertEqual(dates.getStringFromDateTime(test_datetime), test_str)

    def test_goDate(self):
        self.assertEqual(
            dates.goDate(datetime.date(2006, 0o5, 0o3), 10),
            datetime.date(2006, 0o5, 13),
        )
        self.assertEqual(
            dates.goDate(datetime.datetime(2006, 0o5, 0o3, 12, 15, 23), 10),
            datetime.datetime(2006, 0o5, 13, 12, 15, 23),
        )
        self.assertEqual(
            dates.goDate(datetime.datetime(2006, 0o5, 0o3, 12, 15, 00), 10),
            datetime.datetime(2006, 0o5, 13, 12, 15, 00),
        )
        self.assertEqual(
            dates.goDate(datetime.date(2006, 0o5, 0o3), -2),
            datetime.date(2006, 0o5, 0o1),
        )
        self.assertEqual(
            dates.goDate(datetime.datetime(2006, 0o5, 0o3, 12, 15, 23), -2),
            datetime.datetime(2006, 0o5, 0o1, 12, 15, 23),
        )
        self.assertEqual(
            dates.goDate(datetime.datetime(2006, 0o5, 0o3, 12, 15, 00), -2),
            datetime.datetime(2006, 0o5, 0o1, 12, 15, 00),
        )

    def test_goMonth(self):
        self.assertEqual(dates.goMonth(datetime.date(2012, 8, 1), 10), datetime.date(2013, 6, 1))
        self.assertEqual(dates.goMonth(datetime.date(2012, 8, 1), 10), datetime.date(2013, 6, 1))
        self.assertEqual(dates.goMonth(datetime.date(2012, 3, 31), -1), datetime.date(2012, 2, 29))
        self.assertEqual(dates.goMonth(datetime.date(2012, 3, 31), -13), datetime.date(2011, 2, 28))


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(Test_Dates)
    unittest.TextTestRunner(verbosity=2).run(suite)
