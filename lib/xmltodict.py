""" xmltodict(): convert xml into tree of Python dicts.

This was copied and modified from John Bair's recipe at aspn.activestate.com:
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/149368
"""
import os
import string
from xml.parsers import expat

code_linesep = "\n"

class Xml2Obj:
	"""XML to Object"""
	def __init__(self):
		self.root = None
		self.nodeStack = []
		self.attsToSkip = []
		self._inCode = False
		self._mthdName = ""
		self._mthdCode = ""
		self._codeDict = None
		

	def StartElement(self, name, attributes):
		"""SAX start element even handler"""
		if name == "code":
			# This is code for the parent element
			self._inCode = True
			parent = self.nodeStack[-1]
			if not parent.has_key("code"):
				parent["code"] = {}
				self._codeDict = parent["code"]

		else:
			if self._inCode:
				self._mthdName = name.encode()
			else:
				element = {"name": name.encode()}
				if len(attributes) > 0:
					for att in self.attsToSkip:
						if attributes.has_key(att):
							del attributes[att]
					element["attributes"] = attributes
		
				# Push element onto the stack and make it a child of parent
				if len(self.nodeStack) > 0:
					parent = self.nodeStack[-1]
					if not parent.has_key("children"):
						parent["children"] = []
					parent["children"].append(element)
				else:
					self.root = element
				self.nodeStack.append(element)


	def EndElement(self, name):
		"""SAX end element event handler"""
		if self._inCode:
			if name == "code":
				self._inCode = False
				self._codeDict = None
			else:
				# End of an individual method
				self._codeDict[self._mthdName] = self._mthdCode
				self._mthdName = ""
				self._mthdCode = ""
		else:
			self.nodeStack = self.nodeStack[:-1]


	def CharacterData(self, data):
		"""SAX character data event handler"""
		if data.strip():
			data = data.replace("&lt;", "<")
			data = data.encode()
			if self._inCode:
				if self._mthdCode:
					self._mthdCode += "%s%s" % (code_linesep, data)
				else:
					self._mthdCode = data
			else:
				element = self.nodeStack[-1]
				if not element.has_key("cdata"):
					element["cdata"] = ""
				element["cdata"] += data
			

	def Parse(self, xml):
		# Create a SAX parser
		Parser = expat.ParserCreate()
		# SAX event handlers
		Parser.StartElementHandler = self.StartElement
		Parser.EndElementHandler = self.EndElement
		Parser.CharacterDataHandler = self.CharacterData
		# Parse the XML File
		ParserStatus = Parser.Parse(xml, 1)
		return self.root


	def ParseFromFile(self, filename):
		return self.Parse(open(filename,"r").read())


def xmltodict(xml, attsToSkip=[]):
	"""Given an xml string or file, return a Python dictionary."""
	parser = Xml2Obj()
	parser.attsToSkip = attsToSkip
	if os.linesep not in xml and os.path.exists(xml):
		# argument was a file
		return parser.ParseFromFile(xml)
	else:
		# argument must have been raw xml:
		return parser.Parse(xml)


def dicttoxml(dct, level=0, header=None, linesep=None):
	"""Given a Python dictionary, return an xml string.

	The dictionary must be in the format returned by dicttoxml(), with keys
	on "attributes", "code", "cdata", "name", and "children".

	Send your own XML header, otherwise a default one will be used.

	The linesep argument is a dictionary, with keys on levels, allowing the
	developer to add extra whitespace depending on the level.
	"""
	def escQuote(val):
		"""Add surrounding quotes to the string, and escape
		any illegal XML characters.
		"""
		if not isinstance(val, basestring):
			val = str(val)
		for qt in ('"', "'", '"""', "'''"):
			if qt not in val:
				break
		val = val.replace("<", "&lt;").replace(">", "&gt;")
		return "%s%s%s" % (qt, val, qt)

	att = ""
	ret = ""

	if dct.has_key("attributes"):
		for key, val in dct["attributes"].items():
			val = escQuote(val)
			att += " %s=%s" % (key, val)

	ret += "%s<%s%s" % ("\t" * level, dct["name"], att)

	if (not dct.has_key("cdata") and not dct.has_key("children") 
			and not dct.has_key("code")):
		ret += " />%s" % os.linesep
	else:
		ret += ">"
		if dct.has_key("cdata"):
			ret += "%s" % dct["cdata"].replace("<", "&lt;")

		if dct.has_key("code"):
			if len(dct["code"].keys()):
				ret += "%s%s<code>%s"	% (os.linesep, "\t" * (level+1), os.linesep)
				methodTab = "\t" * (level+2)
				for mthd, cd in dct["code"].items():
					# Make sure that the code ends with a linefeed
					if not cd.endswith(os.linesep):
						cd += os.linesep
					ret += "%s<%s><![CDATA[%s%s]]>%s%s</%s>%s" % (methodTab,
							mthd, os.linesep, cd.replace("<", "&lt;"), os.linesep, 
							methodTab, mthd, os.linesep)
				ret += "%s</code>%s"	% ("\t" * (level+1), os.linesep)

		if dct.has_key("children") and len(dct["children"]) > 0:
			ret += os.linesep
			for child in dct["children"]:
				ret += dicttoxml(child, level+1, linesep=linesep)
		indnt = ""
		if ret.endswith(os.linesep):
			# Indent the closing tag
			indnt = ("\t" * level)
		ret += "%s</%s>%s" % (indnt, dct["name"], os.linesep)

		if linesep:
			ret += linesep.get(level, "")

	if level == 0:
		if header is None:
			header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>%s' \
					% os.linesep 
		ret = header + ret

	return ret
