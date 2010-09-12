"""JSON conversion support for Dejavu Units.

The source for this was obtained from: http://www.aminus.net/dejavu

It was published there with the statement that it was being placed in
the public domain. I have only modified it minimally for its inclusion
into Dabo.
"""

import datetime
import decimal
import time
import sys

try:
	from simplejson import JSONEncoder, JSONDecoder
except ImportError:
	print """

The required 'simplejson' module is not present.

Please install that module before using the web features of Dabo.

"""
	sys.exit()

__all__ = ["Encoder", "Decoder", "Converter"]

class Null(object):
	class meta(type):
		def __new__(cls, *args, **kwargs):
			if '_inst' not in vars(cls):
				cls._inst = type.__new__(cls, *args, **kwargs)
			return cls._inst
	__metaclass__ = meta
	def __init__(self, *args, **kwargs): pass
	def __call__(self, *args, **kwargs): return self
	def __repr__(self): return "Null()"
	def __nonzero__(self): return False
	def __getattr__(self, name): return self
	def __setattr__(self, name, value): return self
	def __delattr__(self, name): return self

class Encoder(JSONEncoder):
	"""Extends the base simplejson JSONEncoder for Dejavu."""

	DATE_FMT = "%Y-%m-%d"
	TIME_FMT = "%H:%M:%S"
	DATETIME_FMT = "%s %s" % (DATE_FMT, TIME_FMT)

	def default(self, o):
		_special_types = (datetime.date, datetime.time, datetime.datetime,
						  decimal.Decimal)
		# We MUST check for a datetime.datetime instance before datetime.date.
		# datetime.datetime is a subclass of datetime.date, and therefore
		# instances of it are also instances of datetime.date.
		if isinstance(o, datetime.datetime) or o is datetime.datetime:
			if o is datetime.datetime:
				o = Null()
			return {'__datetime__': True,
					'value': o.strftime(self.DATETIME_FMT)}

		if isinstance(o, datetime.date) or o is datetime.date:
			if o is datetime.date:
				o = Null()
			return {'__date__': True,
					'value': o.strftime(self.DATE_FMT)}

		if isinstance(o, datetime.time) or o is datetime.time:
			if o is datetime.time:
				o = Null()
			return {'__time__': True,
					'value': o.strftime(self.TIME_FMT)}

		if isinstance(o, decimal.Decimal) or o is decimal.Decimal:
			if o is decimal.Decimal:
				value = None
			else:
				value = unicode(o)
			return {'__decimal__': True,
					'value': value}

		if isinstance(o, Null):
			return None

		else:
			return JSONEncoder.default(self, o)

class Decoder(JSONDecoder):
	"""Extends the base simplejson JSONDecoder for Dejavu."""

	DATE_FMT = "%Y-%m-%d"
	TIME_FMT = "%H:%M:%S"
	DATETIME_FMT = "%s %s" % (DATE_FMT, TIME_FMT)

	def __init__(self, arena=None, encoding=None, object_hook=None):
		JSONDecoder.__init__(self, encoding, object_hook)
		if not self.object_hook:
			self.object_hook = self.json_to_python
		self.arena = arena

	def json_to_python(self, d):
		if '__datetime__' in d:
			if d['value'] is None:
				return None
			strp = time.strptime(d['value'], self.DATETIME_FMT)[:7]
			return datetime.datetime(*strp)
		if '__date__' in d:
			if d['value'] is None:
				return None
			strp = time.strptime(d['value'], self.DATE_FMT)[:3]
			return datetime.date(*strp)
		if '__time__' in d:
			if d['value'] is None:
				return None
			strp = time.strptime(d['value'], self.TIME_FMT)[3:6]
			return datetime.time(*strp)
		if '__decimal__' in d:
			if d['value'] is None:
				return None
			return decimal.Decimal(d['value'])
		return d

class Converter(object):
	"""Provides two-way conversion of Units/JSON via loads and dumps methods.

	Also converts datetime.date, datetime.time, datetime.datetime and
	decimal.Decimal to/from JSON.

	This is accomplished by the Encoder and Decoder classes, which are
	subclasses of their counterparts in simplejson.	 If you wish to change
	the output of the converter at all, you should probably subclass the
	Encoder/Decoder and then make a cusom Converter subclass with your
	encoder/decoder as class attributes.
	"""

	encoder = Encoder
	decoder = Decoder

	def __init__(self, arena=None):
		self.arena = arena

	def loads(self, s, encoding=None, **kw):
		return self.decoder(encoding=encoding, arena=self.arena, **kw).decode(s)

	def dumps(self, obj, skipkeys=False, ensure_ascii=False,
			  check_circular=True, allow_nan=True, indent=None, **kw):
		return self.encoder(skipkeys, ensure_ascii, check_circular,
							allow_nan, indent, **kw).encode(obj)