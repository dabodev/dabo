"""Contains helper functions for dealing with dates and datetimes.

For example, getting a date from a string in various formats.
"""
import datetime
import re

_dregex = {}
_dtregex = {}
_tregex = {}


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
		exp = "^%(hour)s:%(minute)s:%(second)s%(ms)s$" % exp
	else:
		return None
	return re.compile(exp % elements)


def getDateFromString(strVal, formats=None):
	"""Given a string in a defined format, return a date object or None."""
	global _dregex

	ret = None
	if formats is None:
		formats = ["ISO8601"]
	
	# Try each format in order:
	for format in formats:
		try:
			regex = _dregex[format]
		except KeyError:
			regex = _getDateRegex(format)
			if regex is None:
				continue
			_dregex[format] = regex
		m = regex.match(strVal)
		if m is not None:
			groups = m.groupdict()
			if not groups.has_key("year"):
				curYear = datetime.date.today().year
				if groups.has_key("shortyear"):
					groups["year"] = int("%s%s" % (str(curYear)[:2], 
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


def getDateTimeFromString(strVal, formats=None):
	"""Given a string in a defined format, return a datetime object or None."""
	global _dtregex

	ret = None
	if formats is None:
		formats = ["ISO8601"]
	
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
				if not groups.has_key(skip_group) or len(groups[skip_group]) == 0:
					# group not in the expression: default to 0
					groups[skip_group] = 0
			if not groups.has_key("year"):
				curYear = datetime.date.today().year
				if groups.has_key("shortyear"):
					groups["year"] = int("%s%s" % (str(curYear)[:2], 
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


if __name__ == "__main__":
	print "testing converting strings to dates:"
	formats = ["ISO8601", "YYYYMMDD", "YYMMDD", "MMDD"]
	tests = ["0503", "20060503", "2006-05-03", "060503"]
	for test in tests:
		for format in formats:
			print "%s (%s) -> %s" % (test, format, repr(getDateFromString(test, [format])))
