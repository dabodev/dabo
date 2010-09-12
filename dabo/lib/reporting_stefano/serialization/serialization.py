# -*- coding: utf-8 -*-

from attributes import *
from children import *


class SerializableMeta(type):
	def __init__(cls, name, bases, dict):
		newDict = {}
		attributes = []
		for base in bases:
			if hasattr(base, '_xmlSerializationAttributes'):
				attributes.extend(base._xmlSerializationAttributes)
		for name, obj in dict.items():
			if (isinstance(obj, SerializableAttribute)
					or isinstance(obj, SerializableObjectChild)):
				attributes.append( (name, obj) )
				delattr(cls, name)
			else:
				newDict[name] = obj
		super(SerializableMeta, cls).__init__(name, bases, newDict)
		cls._xmlSerializationAttributes = attributes


class Serializable(object):
	__metaclass__ = SerializableMeta

	def __init__(self, **args):
		self.srcValues = {}
		attributeNames = [attrName for attrName,
				attrType in self._xmlSerializationAttributes]
		for key, value in args.iteritems():
			assert key in attributeNames, "Unknown attribute name %r for object %s" \
					% (key, self.__class__.__name__)
			self.srcValues[key] = value

	def getExpectedNames(cls):
		assert hasattr(cls, '_xmlSerializationAttributes'), "Class %r does not " \
				"define list of attributes needed for deserialization" % cls
		names = []
		for attrName, attrType in cls._xmlSerializationAttributes:
			if isinstance(attrType, SerializableAttribute):
				names.append(attrName)
			else:
				names.extend(attrType.getExpectedNames(attrName))
		return names
	getExpectedNames = classmethod(getExpectedNames)

	def getChildObjType(cls, childName):
		assert hasattr(cls, '_xmlSerializationAttributes'), "Class %r does not " \
				"define list of attributes needed for deserialization" % cls
		for attrName, attrType in cls._xmlSerializationAttributes:
			if isinstance(attrType, SerializableAttribute):
				if attrName == childName:
					return attrName, attrType
			else:
				if childName in attrType.getExpectedNames(attrName):
					return attrName, attrType
	getChildObjType = classmethod(getChildObjType)

	def evaluate(self, env, onlyAttr=None):
		for attrName, attrType in self._xmlSerializationAttributes:
			if onlyAttr is not None and attrName != onlyAttr:
				continue
			if not isinstance(attrType, SerializableAttribute):
				continue
			value = self.srcValues.get(attrName, None)
			try:
				value = attrType.evaluate(value, env)
			except Exception, e:
				import traceback
				traceback.print_exc()
				raise Exception("Error validating value %r for attribute %r (type %r) "
						"in object %s" % (value, attrName,
						attrType.__class__.__name__,
						self.__class__.__name__))
			setattr(self, attrName, value)


