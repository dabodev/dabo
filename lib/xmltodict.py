""" xmltodict(): convert xml into tree of Python dicts.

This was copied and modified from John Bair's recipe at aspn.activestate.com:
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/149368
"""
import os
import string
from xml.parsers import expat

# Python seems to need to compile code with \n linesep:
code_linesep = "\n"
eol = os.linesep


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
		self._inProp = False
		self._propName = ""
		self._propData = ""
		self._propDict = None
		self._currPropAtt = ""
		self._currPropDict = None
		

	def StartElement(self, name, attributes):
		"""SAX start element even handler"""
		if name == "code":
			# This is code for the parent element
			self._inCode = True
			parent = self.nodeStack[-1]
			if not parent.has_key("code"):
				parent["code"] = {}
				self._codeDict = parent["code"]

		elif name == "properties":
			# These are the custom property definitions
			self._inProp = True
			self._propName = ""
			self._propData = ""
			parent = self.nodeStack[-1]
			if not parent.has_key("properties"):
				parent["properties"] = {}
				self._propDict = parent["properties"]

		else:
			if self._inCode:
				self._mthdName = name.encode()
			elif self._inProp:
				if self._propName:
					# In the middle of a prop definition
					self._currPropAtt = name.encode()
				else:
					self._propName = name.encode()
					self._currPropDict = {}
					self._currPropAtt = ""
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
		elif self._inProp:
			if name == "properties":
				self._inProp = False
				self._propDict = None
			elif name == self._propName:
				# End of an individual prop definition
				self._propDict[self._propName] = self._currPropDict
				self._propName = ""
			else:
				# end of a property attribute
				self._currPropDict[self._currPropAtt] = self._propData
				self._propData = self._currPropAtt = ""
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
			elif self._inProp:
				self._propData += data
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
	if eol not in xml and os.path.exists(xml):
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
	def escQuote(val, noEscape):
		"""Add surrounding quotes to the string, and escape
		any illegal XML characters.
		"""
		if not isinstance(val, basestring):
			val = str(val)
		qt = '"'
		slsh = "\\"
		val = val.replace("<", "&lt;").replace(">", "&gt;").replace(slsh, slsh+slsh)
		if not noEscape:
			# First escape internal ampersands:
			val = val.replace("&", "&amp;")
			# Escape any internal quotes
			val = val.replace('"', '&quot;').replace("'", "&apos;")
		return "%s%s%s" % (qt, val, qt)

	att = ""
	ret = ""

	if dct.has_key("attributes"):
		for key, val in dct["attributes"].items():
			# Some keys are already handled.
			noEscape = key in ("sizerInfo",)
			val = escQuote(val, noEscape)
			att += " %s=%s" % (key, val)

	ret += "%s<%s%s" % ("\t" * level, dct["name"], att)

	if (not dct.has_key("cdata") and not dct.has_key("children") 
			and not dct.has_key("code") and not dct.has_key("properties")):
		ret += " />%s" % eol
	else:
		ret += ">"
		if dct.has_key("cdata"):
			ret += "%s" % dct["cdata"].replace("<", "&lt;")

		if dct.has_key("code"):
			if len(dct["code"].keys()):
				ret += "%s%s<code>%s" % (eol, "\t" * (level+1), eol)
				methodTab = "\t" * (level+2)
				for mthd, cd in dct["code"].items():
					# Convert \n's in the code to eol:
					cd = eol.join(cd.splitlines())

					# Make sure that the code ends with a linefeed
					if not cd.endswith(eol):
						cd += eol

					ret += "%s<%s><![CDATA[%s%s]]>%s%s</%s>%s" % (methodTab,
							mthd, eol, cd, eol, 
							methodTab, mthd, eol)
				ret += "%s</code>%s"	% ("\t" * (level+1), eol)

		if dct.has_key("properties"):
			if len(dct["properties"].keys()):
				ret += "%s%s<properties>%s" % (eol, "\t" * (level+1), eol)
				currTab = "\t" * (level+2)
				for prop, val in dct["properties"].items():
					ret += "%s<%s>%s" % (currTab, prop, eol)
					for propItm, itmVal in val.items():
						itmTab = "\t" * (level+3)
						ret += "%s<%s>%s</%s>%s" % (itmTab, propItm, itmVal, 
								propItm, eol)
					ret += "%s</%s>%s" % (currTab, prop, eol)
				ret += "%s</properties>%s"	% ("\t" * (level+1), eol)
					
		if dct.has_key("children") and len(dct["children"]) > 0:
			ret += eol
			for child in dct["children"]:
				ret += dicttoxml(child, level+1, linesep=linesep)
		indnt = ""
		if ret.endswith(eol):
			# Indent the closing tag
			indnt = ("\t" * level)
		ret += "%s</%s>%s" % (indnt, dct["name"], eol)

		if linesep:
			ret += linesep.get(level, "")

	if level == 0:
		if header is None:
			header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>%s' \
					% eol 
		ret = header + ret

	return ret
