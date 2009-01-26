# -*- coding: utf-8 -*-

def importClass(clsName):
	components = clsName.split('.')
	modComponents = []
	for comp in components:
		if comp[0].isupper():
			break
		modComponents.append(comp)
	mod = __import__('.'.join(modComponents))
	for comp in components[1:]:
		mod = getattr(mod, comp)
	return mod


def loname(name):
	return name[0].lower() + name[1:]


class SerializableObjectChild(object):
	def getExpectedClasses(self):
		return [importClass(clsName) for clsName in self.expectedClsNames]


class AttributeChild(SerializableObjectChild):
	def __init__(self, clsName):
		self.expectedClsNames = [clsName]

	def attach(self, parentObj, name, attrName):
		cls = self.getExpectedClasses()[0]
		obj = cls()
		setattr(parentObj, name, obj)
		return obj

	def getExpectedNames(self, attrName):
		return [attrName]


class ObjectListChild(SerializableObjectChild):
	def __init__(self, clsNames):
		self.expectedClsNames = clsNames

	def attach(self, parentObj, name, attrName):
		for cls in self.getExpectedClasses():
			if loname(cls.__name__) == name:
				obj = cls()
				parentList = getattr(parentObj, attrName, [])
				parentList.append(obj)
				setattr(parentObj, attrName, parentList)
				return obj

	def getExpectedNames(self, attrName):
		return [loname(cls.__name__) for cls in self.getExpectedClasses()]

