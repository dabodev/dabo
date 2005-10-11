""" xmltodict(): convert xml into tree of Python dicts.

This was copied and modified from John Bair's recipe at aspn.activestate.com:
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/149368
"""
import os
import string
from xml.parsers import expat


class Xml2Obj:
	"""XML to Object"""
	def __init__(self):
		self.root = None
		self.nodeStack = []
		self.attsToSkip = []
        
	def StartElement(self,name,attributes):
		"""SAX start element even handler"""
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
        
	def EndElement(self,name):
		"""SAX end element event handler"""
		self.nodeStack = self.nodeStack[:-1]

	def CharacterData(self,data):
		"""SAX character data event handler"""
		if string.strip(data):
			data = data.replace("&lt;", "<")
			data = data.encode()
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
	if "\n" not in xml and os.path.exists(xml):
		# argument was a file
		return parser.ParseFromFile(xml)
	else:
		# argument must have been raw xml:
		return parser.Parse(xml)


def dicttoxml(d, level=0, header=None):
	"""Given a Python dictionary, return an xml string.

	The dictionary must be in the format returned by dicttoxml(), with keys
	on "attributes", "cdata", "name", and "children".
	"""
	att = ""
	s = ""

	if d.has_key("attributes"):
		for a, v in d["attributes"].items():
			att += " %s=\"%s\"" % (a, v)

	s += "%s<%s%s" % ("\t" * level, d["name"], att)

	if not d.has_key("cdata") and not d.has_key("children"):
		s += " />\n"
	else:
		s += ">"
		if d.has_key("cdata"):
			s += "%s" % d["cdata"].replace("<", "&lt;")

		if d.has_key("children") and len(d["children"]) > 0:
			s += "\n"
			for child in d["children"]:
				s += dicttoxml(child, level+1)
			s += "%s" % "\t" * level
		
		s += "</%s>\n" % d["name"]

		if level == 1:
			s += "\n"
	
	if level == 0:
		if header is None:
			header = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n"""
		else:
			s = header + s

	return s
