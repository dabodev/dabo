# -*- coding: utf-8 -*-
"""Contains helper functions for dealing with dates and datetimes.

For example, getting a date from a string in various formats.
"""
import operator
import calendar
import datetime
import re
import time
import dabo
from dabo.lib.utils import ustr

_dregex = {}
_dtregex = {}
_tregex = {}

_usedDateFormats = ["%x"]


def _getDateRegex(format):
	elements = {}
	elements["year"] = "(?P<year>[0-9]{4,4})"              ## year 0000-9999
	elements["shortyear"] = "(?P<shortyear>[0-9]{2,2})"    ## year 00-99
	elements["month"] = "(?P<month>0[1-9]|1[012])"         ## month 01-12
	elements["day"] = "(?P<day>0[1-9]|[1-2][0-9]|3[0-1])"  ## day 01-31

	if format == "ISO8601":
		exp = "^%(year)s-%(month)s-%(day)s$"
	elif format == "YYYYMMDD":
		exp = "^%(year)s%(month)s%(day)s$"
	elif format == "YYMMDD":
		exp = "^%(shortyear)s%(month)s%(day)s$"
	elif format == "MMDD":
		exp = "^%(month)s%(day)s$"
	else:
		conv = {"%d": "%(day)s",
		        "%m": "%(month)s",
		        "%y": "%(shortyear)s",
		        "%Y": "%(year)s"}
		if "%d" in format and "%m" in format and ("%y" in format or "%Y" in format):
			for k in conv:
				format = format.replace(k, conv[k])
				format.replace(".", "\.")
				exp = "^%s$" % format
		else:
			return None

	return re.compile(exp % elements)


def _getDateTimeRegex(format):
	elements = {}
	elements["year"] = "(?P<year>[0-9]{4,4})"              ## year 0000-9999
	elements["shortyear"] = "(?P<shortyear>[0-9]{2,2})"    ## year 00-99
	elements["month"] = "(?P<month>0[1-9]|1[012])"         ## month 01-12
	elements["day"] = "(?P<day>0[1-9]|[1-2][0-9]|3[0-1])"  ## day 01-31
	elements["hour"] = "(?P<hour>[0-1][0-9]|2[0-3])"       ## hour 00-23
	elements["minute"] = "(?P<minute>[0-5][0-9])"          ## minute 00-59
	elements["second"] = "(?P<second>[0-5][0-9])"          ## second 00-59
	elements["ms"] = "\.{0,1}(?P<ms>[0-9]{0,6})"           ## optional ms
	elements["sep"] = "(?P<sep> |T)"                       ## separator between date and time

	if format == "ISO8601":
		exp = "^%(year)s-%(month)s-%(day)s%(sep)s%(hour)s:%(minute)s:%(second)s%(ms)s$"
	elif format == "YYYYMMDDHHMMSS":
		exp = "^%(year)s%(month)s%(day)s%(hour)s%(minute)s%(second)s%(ms)s$"
	elif format == "YYMMDDHHMMSS":
		exp = "^%(shortyear)s%(month)s%(day)s%(hour)s%(minute)s%(second)s%(ms)s$"
	elif format == "YYYYMMDD":
		exp = "^%(year)s%(month)s%(day)s$"
	elif format == "YYMMDD":
		exp = "^%(shortyear)s%(month)s%(day)s$"
	else:
		return None
	return re.compile(exp % elements)


def _getTimeRegex(format):
	elements = {}
	elements["hour"] = "(?P<hour>[0-1][0-9]|2[0-3])"       ## hour 00-23
	elements["minute"] = "(?P<minute>[0-5][0-9])"          ## minute 00-59
	elements["second"] = "(?P<second>[0-5][0-9])"          ## second 00-59
	elements["ms"] = "\.{0,1}(?P<ms>[0-9]{0,6})"           ## optional ms
	elements["sep"] = "(?P<sep> |T)"

	if format == "ISO8601":
		exp = "^%(hour)s:%(minute)s:%(second)s%(ms)s$"
	else:
		return None
	return re.compile(exp % elements)


def getStringFromDate(d):
	"""Given a datetime.date, convert to string in dabo.dateFormat style."""
	fmt = dabo.dateFormat
	if fmt is None:
		# Delegate formatting to the time module, which will take the
		# user's locale into account.
		fmt = "%x"
	## note: don't use d.strftime(), as it doesn't handle < 1900
	return time.strftime(fmt, d.timetuple())


def getDateFromString(strVal, formats=None):
	"""Given a string in a defined format, return a date object or None."""
	global _dregex
	global _usedDateFormats

	ret = None

	if formats is None:
		formats = ["ISO8601"]

	sdf = dabo.dateFormat
	if sdf is not None:
		if _usedDateFormats[0] == sdf:
			# current date format is already first in the list; do nothing
			pass
		else:
			if sdf in _usedDateFormats:
				del(_usedDateFormats[_usedDateFormats.index(sdf)])
			_usedDateFormats.insert(0, sdf)
	formats.extend(_usedDateFormats)

	# Try each format in order:
	for format in formats:
		try:
			regex = _dregex[format]
		except KeyError:
			regex = _getDateRegex(format)
			if regex is None:
				try:
					return datetime.date(*time.strptime(strVal, format)[:3])
				except ValueError:
					continue
			_dregex[format] = regex
		m = regex.match(strVal)
		if m is not None:
			groups = m.groupdict()
			if "year" not in groups:
				curYear = datetime.date.today().year
				if "shortyear" in groups:
					groups["year"] = int("%s%s" % (ustr(curYear)[:2],
							groups["shortyear"]))
				else:
					groups["year"] = curYear
			try:
				ret = datetime.date(int(groups["year"]),
					int(groups["month"]),
					int(groups["day"]))
			except ValueError:
				# Could be that the day was out of range for the particular month
				# (Sept. only has 30 days but the regex will allow 31, etc.)
				pass
		if ret is not None:
			break
	return ret


def getStringFromDateTime(dt):
	"""Given a datetime.datetime, convert to string in dabo.dateTimeFormat style."""
	fmt = dabo.dateTimeFormat
	if fmt is None:
		# Delegate formatting to the time module, which will take the
		# user's locale into account.
		fmt = "%x %X"
	## note: don't use dt.strftime(), as it doesn't handle < 1900
	return time.strftime(fmt, dt.timetuple())


def getDateTimeFromString(strVal, formats=None):
	"""Given a string in a defined format, return a datetime object or None."""
	global _dtregex

	dtFormat = dabo.dateTimeFormat
	ret = None

	if formats is None:
		formats = ["ISO8601"]

	if dtFormat is not None:
		formats.append(dtFormat)

	for format in formats:
		regex = _dtregex.get(format, None)
		if regex is None:
			regex = _getDateTimeRegex(format)
			if regex is None:
				continue
			_dtregex[format] = regex
		m = regex.match(strVal)
		if m is not None:
			groups = m.groupdict()
			for skip_group in ["ms", "second", "minute", "hour"]:
				if (skip_group not in groups) or not groups[skip_group]:
					# group not in the expression: default to 0
					groups[skip_group] = 0
			if "year" not in groups:
				curYear = datetime.date.today().year
				if "shortyear" in groups:
					groups["year"] = int("%s%s" % (ustr(curYear)[:2],
							groups["shortyear"]))
				else:
					groups["year"] = curYear

			try:
				return datetime.datetime(int(groups["year"]),
					int(groups["month"]),
					int(groups["day"]),
					int(groups["hour"]),
					int(groups["minute"]),
					int(groups["second"]),
					int(groups["ms"]))
			except ValueError:
				raise
				# Could be that the day was out of range for the particular month
				# (Sept. only has 30 days but the regex will allow 31, etc.)
				pass
		if ret is not None:
			break
	if ret is None:
		if dtFormat is None:
			# Fall back to the current locale setting in user's os account:
			try:
				ret = datetime.datetime(*time.strptime(strVal, "%x %X")[:7])
			except ValueError:  ## ValueError from time.strptime()
				pass
	return ret


def getTimeFromString(strVal, formats=None):
	"""Given a string in a defined format, return a	time object."""
	global _tregex

	ret = None
	if formats is None:
		formats = ["ISO8601"]

	for format in formats:
		regex = _tregex.get(format, None)
		if regex is None:
			regex = _getTimeRegex(format)
			if regex is None:
				continue
			_tregex[format] = regex
		m = regex.match(strVal)
		if m is not None:
			groups = m.groupdict()
			if len(groups["ms"]) == 0:
				# no ms in the expression
				groups["ms"] = 0
			return datetime.time(int(groups["hour"]),
				int(groups["minute"]),
				int(groups["second"]),
				int(groups["ms"]))
		if ret is not None:
			break
	return ret


def goDate(date, days):
	"""Given a date or datetime, return the date or datetime that is <days> away."""
	op = operator.add
	if days < 0:
		op = operator.sub
	return op(date, datetime.timedelta(days=abs(days)))


def goMonth(date, months):
	"""Given a date or datetime, return the date or datetime that is <months> away.

	In case of the new month being shorter than the old day number, the last day of
	the new month will be used.
	"""
	# This solution is based on
	# http://stackoverflow.com/4130922/how-to-increment-datetime-month-in-python
	month = date.month -1 + months
	year = date.year + (month / 12)
	month = (month % 12) + 1
	day = min(date.day, calendar.monthrange(year, month)[1])
	return date.replace(year, month, day)


def webHeaderFormat(dtm):
	"""Takes a datetime value and returns a string in the format required by
	HTTP headers, such as an 'If-Modified-Since' header.
	"""
	hereNow, utcNow = datetime.datetime.now(), datetime.datetime.utcnow()
	offset = utcNow - hereNow
	adjusted = dtm + offset
	return adjusted.strftime("%a, %d %b %Y %H:%M:%S GMT")



if __name__ == "__main__":
	print "testing converting strings to dates:"
	formats = ["ISO8601", "YYYYMMDD", "YYMMDD", "MMDD"]
	tests = ["0503", "20060503", "2006-05-03", "060503"]
	for test in tests:
		for format in formats:
			print "%s (%s) -> %s" % (test, format, repr(getDateFromString(test, [format])))

	dt = datetime.datetime.now()
	print goDate(dt, -30)
	d = datetime.date.today()
	print goDate(d, -30)
