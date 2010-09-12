# -*- coding: utf-8 -*-
# pkm TODO: serialization lib shouldn't have to rely on reporting lib's, or,
#           if serialization lib is specific to reporting, it should be moved
#           to dabo.lib.reporting.serialization. Stefano, thoughts?
from reportlab.lib import pagesizes
import dabo
from dabo.lib.utils import ustr


class SerializableAttribute(object):
	def __init__(self, default):
		self.default = default
		super(SerializableAttribute, self).__init__()

	def evaluate(self, value, env):
		""" Abstract method, must be overridden in subclasses. """
		return "--SerializableAttribute not overridden--"


class GenericAttr(SerializableAttribute):
	def evaluate(self, value, env):
		if value is None:
			return self.default
		return eval(value, env)


class StringAttr(SerializableAttribute):
	def evaluate(self, value, env):
		if value is None:
			return self.default
		value = eval(value, env)
		assert isinstance(value, basestring)
		return value


class UnevalStringAttr(SerializableAttribute):
	def evaluate(self, value, env):
		assert isinstance(value, basestring)
		return value


class LengthAttr(SerializableAttribute):
	def evaluate(self, value, env):
		if value is None:
			return self.default
		from dabo.lib.reporting import util
		return util.getPt(eval(value, env))


class StringChoiceAttr(SerializableAttribute):
	def __init__(self, choices, default):
		self.choices = choices
		self.default = default

	def evaluate(self, value, env):
		if value is None:
			return self.default
		v = eval(value, env)
		assert v in self.choices, "Invalid value %r for %s" % (v, self.__class__.__name__)
		return v


class ColorAttr(SerializableAttribute):
	def evaluate(self, value, env):
		if value is None:
			return self.default
		value = eval(value, env)
		assert isinstance(value, tuple)
		return value


class PagesizesAttr(SerializableAttribute):
	def evaluate(self, value, env):
		pageSize = getattr(pagesizes, ustr(value).upper(), None)
		if pageSize is None:
			pageSize = getattr(pagesizes, ustr(self.default).upper(), None)
		return pageSize

