# -*- coding: utf-8 -*-
"""
xmltodict(): convert xml into tree of Python dicts.

This was copied and modified from John Bair's recipe at aspn.activestate.com:
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/149368
"""
from six import text_type as sixUnicode
import os
import string
import locale
import codecs
from xml.parsers import expat

# If we're in Dabo, get the default encoding.
import dabo
import dabo.lib.DesignerUtils as desUtil
from dabo.dLocalize import _
from dabo.lib.utils import resolvePath
from dabo.lib.utils import ustr

app = dabo.dAppRef
default_encoding = dabo.getEncoding()
# Normalize the names, as xml.sax running on Gtk will complain for some variations
deLow = default_encoding.lower()
if deLow in ("utf8", "utf-8"):
	default_encoding = "utf-8"
if deLow in ("utf16", "utf-16"):
	default_encoding = "utf-16"

# Python seems to need to compile code with \n linesep:
code_linesep = "\n"
eol = os.linesep



class Xml2Obj(object):
	"""XML to Object"""
	def __init__(self, encoding=None):
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
		if encoding is None:
			self._encoding = dabo.getEncoding()
		else:
			self._encoding = encoding


	def StartElement(self, name, attributes):
		"""SAX start element even handler"""
		if name == "code":
			# This is code for the parent element
			self._inCode = True
			parent = self.nodeStack[-1]
			if "code" not in parent:
				parent["code"] = {}
				self._codeDict = parent["code"]

		elif name == "properties":
			# These are the custom property definitions
			self._inProp = True
			self._propName = ""
			self._propData = ""
			parent = self.nodeStack[-1]
			if "properties" not in parent:
				parent["properties"] = {}
				self._propDict = parent["properties"]

		else:
			if self._inCode:
				self._mthdName = name	#.encode()
			elif self._inProp:
				if self._propName:
					# In the middle of a prop definition
					self._currPropAtt = name	#.encode()
				else:
					self._propName = name	#.encode()
					self._currPropDict = {}
					self._currPropAtt = ""
			else:
				element = {"name": name}	#.encode()}
				if attributes:
					for att in self.attsToSkip:
						try:
							del attributes[att]
						except KeyError:
							pass
					# Unescape any escaped values
					for kk, vv in list(attributes.items()):
						attributes[kk] = unescape(vv)
					element["attributes"] = attributes

				# Push element onto the stack and make it a child of parent
				if len(self.nodeStack) > 0:
					parent = self.nodeStack[-1]
					if "children" not in parent:
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
				mth = self._mthdCode.strip()
				if not mth.endswith("\n"):
					mth += "\n"
				self._codeDict[self._mthdName] = mth
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
		if self._inCode or data.strip():
			data = data.replace("&lt;", "<").replace("&gt;", ">")
			data = data	#.encode()
			if self._inCode:
				if self._mthdCode:
					self._mthdCode += data
				else:
					self._mthdCode = data
			elif self._inProp:
				self._propData += data
			else:
				element = self.nodeStack[-1]
				if "cdata" not in element:
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
		return self.Parse(open(filename, "r").read())


def xmltodict(xml, attsToSkip=[], addCodeFile=False, encoding=None):
	"""Given an xml string or file, return a Python dictionary."""
	parser = Xml2Obj(encoding=encoding)
	parser.attsToSkip = attsToSkip
	if eol in xml and "<?xml" in xml:
		isPath = False
	else:
		isPath = os.path.exists(xml)
	errmsg = ""
	if eol not in xml and isPath:
		# argument was a file
		xmlContent = codecs.open(xml, "r", encoding).read()
		if isinstance(xmlContent, sixUnicode):
			xmlContent = xmlContent.encode(encoding)
		try:
			ret = parser.Parse(xmlContent)
		except expat.ExpatError as e:
			errmsg = _("The XML in '%(xml)s' is not well-formed and cannot be parsed: %(e)s") % locals()
	else:
		# argument must have been raw xml:
		try:
			ret = parser.Parse(xml)
		except expat.ExpatError as e:
			errmsg = _("An invalid XML string was encountered: %s") % e
	if errmsg:
		raise dabo.dException.XmlException(errmsg)
	if addCodeFile and isPath:
		# Get the associated code file, if any
		codePth = "%s-code.py" % os.path.splitext(xml)[0]
		if os.path.exists(codePth):
			try:
				codeContent = codecs.open(codePth, "r", encoding).read()
				codeDict = desUtil.parseCodeFile(codeContent)
				ret["importStatements"] = codeDict.pop("importStatements", "")
				desUtil.addCodeToClassDict(ret, codeDict)
			except Exception as e:
				print("Failed to parse code file:", e)
	return ret


def escQuote(val, noEscape=False, noQuote=False):
	"""
	Add surrounding quotes to the string, and escape
	any illegal XML characters.
	"""
	val = ustr(val)
	if noQuote:
		qt = ''
	else:
		qt = '"'
	slsh = "\\"
# 	val = val.replace(slsh, slsh+slsh)
	if not noEscape:
		val = escape(val)
	return "%s%s%s" % (qt, val, qt)


def escape(val, escapeAmp=True):
	"""Escape any characters that cannot be stored directly in XML."""
	# First escape internal ampersands. We need to double them up due to a
	# quirk in wxPython and the way it displays this character.
	if escapeAmp:
		val = val.replace("&", "&amp;&amp;")
	else:
		val = val.replace("&", "&amp;")
	# Escape any internal quotes
	val = val.replace('"', '&quot;').replace("'", "&apos;")
	# Escape any high-order characters
	chars = []
	for pos, char in enumerate(list(val)):
		if ord(char) > 127:
			chars.append("&#%s;" % ord(char))
		else:
				chars.append(char)
	val = "".join(chars)
	val = val.replace("<", "&#060;").replace(">", "&#062;")
	return val


def unescape(val):
	"""
	Reverse the escape() process to re-create the original values. The parser
	handles the XML conventions; we need to reverse the doubled-up ampersands.
	"""
	val = val.replace("&&", "&")
	return val


def dicttoxml(dct, level=0, header=None, linesep=None):
	"""
	Given a Python dictionary, return an xml string.

	The dictionary must be in the format returned by dicttoxml(), with keys
	on "attributes", "code", "cdata", "name", and "children".

	Send your own XML header, otherwise a default one will be used.

	The linesep argument is a dictionary, with keys on levels, allowing the
	developer to add extra whitespace depending on the level.
	"""
	att = ""
	ret = ""

	if "attributes" in dct:
		for key, val in list(dct["attributes"].items()):
			# Some keys are already handled.
			noEscape = key in ("sizerInfo",)
			val = escQuote(val, noEscape)
			att += " %s=%s" % (key, val)
	ret += "%s<%s%s" % ("\t" * level, dct["name"], att)

	if (("cdata" not in dct) and ("children" not in dct) and ("code" not in dct)
			and ("properties" not in dct)):
		ret += " />%s" % eol
	else:
		ret += ">"
		if "cdata" in dct:
			ret += "%s" % dct["cdata"].replace("<", "&lt;").replace(">", "&gt;")

		if "code" in dct:
			if len(list(dct["code"].keys())):
				ret += "%s%s<code>%s" % (eol, "\t" * (level+1), eol)
				methodTab = "\t" * (level+2)
				for mthd, cd in list(dct["code"].items()):
					# Convert \n's in the code to eol:
					cd = eol.join(cd.splitlines())
					# Make sure that the code ends with a linefeed
					if not cd.endswith(eol):
						cd += eol

					ret += "%s<%s><![CDATA[%s%s]]>%s%s</%s>%s" % (methodTab,
							mthd, eol, cd, eol,
							methodTab, mthd, eol)
				ret += "%s</code>%s"	% ("\t" * (level+1), eol)

		if "properties" in dct:
			if len(list(dct["properties"].keys())):
				ret += "%s%s<properties>%s" % (eol, "\t" * (level+1), eol)
				currTab = "\t" * (level+2)
				for prop, val in list(dct["properties"].items()):
					ret += "%s<%s>%s" % (currTab, prop, eol)
					for propItm, itmVal in list(val.items()):
						itmTab = "\t" * (level+3)
						ret += "%s<%s>%s</%s>%s" % (itmTab, propItm, itmVal,
								propItm, eol)
					ret += "%s</%s>%s" % (currTab, prop, eol)
				ret += "%s</properties>%s"	% ("\t" * (level+1), eol)

		if ("children" in dct) and dct["children"]:
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
			header = '<?xml version="1.0" encoding="%s" standalone="no"?>%s' \
					% (default_encoding, eol)
		ret = header + ret

	return ret


def flattenClassDict(cd, retDict=None):
	"""
	Given a dict containing a series of nested objects such as would
	be created by restoring from a cdxml file, returns a dict with all classIDs
	as keys, and a dict as the corresponding value. The dict value will have
	keys for the attributes and/or code, depending on what was in the original
	dict. The end result is to take a nested dict structure and return a flattened
	dict with all objects at the top level.
	"""
	if retDict is None:
		retDict = {}
	atts = cd.get("attributes", {})
	props = cd.get("properties", {})
	kids = cd.get("children", [])
	code = cd.get("code", {})
	classID = atts.get("classID", "")
	classFile = resolvePath(atts.get("designerClass", ""))
	superclass = resolvePath(atts.get("superclass", ""))
	superclassID = atts.get("superclassID", "")
	if superclassID and os.path.exists(superclass):
		# Get the superclass info
		superCD = xmltodict(superclass, addCodeFile=True)
		flattenClassDict(superCD, retDict)
	if classID:
		if os.path.exists(classFile):
			# Get the class info
			classCD = xmltodict(classFile, addCodeFile=True)
			classAtts = classCD.get("attributes", {})
			classProps = classCD.get("properties", {})
			classCode = classCD.get("code", {})
			classKids = classCD.get("children", [])
			currDict = retDict.get(classID, {})
			retDict[classID] = {"attributes": classAtts, "code": classCode,
					"properties": classProps}
			retDict[classID].update(currDict)
			# Now update the child objects in the dict
			for kid in classKids:
				flattenClassDict(kid, retDict)
		else:
			# Not a file; most likely just a component in another class
			currDict = retDict.get(classID, {})
			retDict[classID] = {"attributes": atts, "code": code,
					"properties": props}
			retDict[classID].update(currDict)
	if kids:
		for kid in kids:
			flattenClassDict(kid, retDict)
	return retDict


def addInheritedInfo(src, super, updateCode=False):
	"""
	Called recursively on the class container structure, modifying
	the attributes to incorporate superclass information. When the
	'updateCode' parameter is True, superclass code is added to the
	object's code
	"""
	atts = src.get("attributes", {})
	props = src.get("properties", {})
	kids = src.get("children", [])
	code = src.get("code", {})
	classID = atts.get("classID", "")
	if classID:
		superInfo = super.get(classID, {"attributes": {}, "code": {}, "properties": {}})
		src["attributes"] = superInfo["attributes"].copy()
		src["attributes"].update(atts)
		src["properties"] = superInfo.get("properties", {}).copy()
		src["properties"].update(props)
		if updateCode:
			src["code"] = superInfo["code"].copy()
			src["code"].update(code)
	if kids:
		for kid in kids:
			addInheritedInfo(kid, super, updateCode)



if __name__ == "__main__":
	test_dict = {"name": "test", "attributes":{"path": "c:\\temp\\name",
			"problemChars": "Welcome to <Jos\xc3\xa9's \ Stuff!>\xc2\xae".decode("latin-1")}}
	print("test_dict:", test_dict)
	xml = dicttoxml(test_dict)
	print("xml:", xml)
	test_dict2 = xmltodict(xml)
	print("test_dict2:", test_dict2)
	print("same?:", test_dict == test_dict2)
