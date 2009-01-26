# -*- coding: utf-8 -*-
from xml.parsers import expat
from serialization import *


def capname(name):
	return name[0].upper() + name[1:]

def loname(name):
	return name[0].lower() + name[1:]


class DeserializingParser(object):
	def __init__(self, rootCls):
		self.expectedNamesStack = [ (loname(rootCls.__name__),) ]
		self.rootCls = rootCls
		self.objStack = []
		self.currentAttrName = None
		self.cdata = ''

	def StartElement(self, name, attributes):
		expectedNames = self.expectedNamesStack[-1]
		assert name in expectedNames, 'Unexpected tag %r (expecting: %s)' \
				% (name, ', '.join(expectedNames))
		if len(self.objStack) == 0:
			# root element
			self.rootObj = self.rootCls()
			self.objStack.append(self.rootObj)
			self.expectedNamesStack.append(self.rootObj.getExpectedNames())
		else:
			parentObj = self.objStack[-1]
			attrName, attrType = parentObj.getChildObjType(name)
			if isinstance(attrType, SerializableAttribute):
				# tag represents an attribute of the object currently on top of the stack
				self.currentAttrName = attrName
				self.cdata = ''
			else:
				# tag represents a new child that should be pushed on the stack
				newObj = attrType.attach(parentObj, name, attrName)
				if len(attributes) > 0:
					newObj._xmlAttributes = dict(attributes)
				self.objStack.append(newObj)
				self.expectedNamesStack.append(newObj.getExpectedNames())

	def EndElement(self, name):
		if self.currentAttrName is not None:
			# write the attribute to the object
			self.objStack[-1].srcValues[self.currentAttrName] = self.cdata
			self.currentAttrName = None
		else:
			# pop the child object from the stack
			self.objStack.pop()
			self.expectedNamesStack.pop()

	def CharacterData(self, data):
		self.cdata = self.cdata + data

	def Parse(self, xml):
		# Create a SAX parser
		Parser = expat.ParserCreate()

		# SAX event handlers
		Parser.StartElementHandler = self.StartElement
		Parser.EndElementHandler = self.EndElement
		Parser.CharacterDataHandler = self.CharacterData

		# Parse the XML File
		ParserStatus = Parser.Parse(xml, 1)

		return self.rootObj

	def ParseFromFile(self, filename):
		return self.Parse(open(filename,'r').read())


def deserialize(xml, rootCls):
	import os
	parser = DeserializingParser(rootCls)
	if "\n" not in xml and os.path.exists(xml):
		# argument was a file
		return parser.ParseFromFile(xml)
	else:
		# argument must have been raw xml:
		return parser.Parse(xml)
