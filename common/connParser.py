import xml.sax
from StringIO import StringIO
import os.path

class connHandler(xml.sax.ContentHandler):
	def __init__(self):
		self.connDict = {}
		self.blankConn = {"dbtype" : "",
				"host" : "",
				"database" : "",
				"user" : "",
				"password" : "",
				"port" : ""		}
		self.currDict = self.blankConn.copy()
		self.element = None
				
	
	def startElement(self, name, attrs):
		self.element = name
		if name == "connection":
			for att in attrs.keys():
				if att == "dbtype":
					self.currDict["dbtype"] = attrs.getValue("dbtype")


	def characters(self, content):
		if self.element:
			if self.currDict.has_key(self.element):
				self.currDict[self.element] += content
			
	
	def endElement(self, name):
		if name == "connection":
			if self.currDict:
				# Save it to the conn dict
				nm = "%s@%s" % (self.currDict["user"], self.currDict["host"])
				self.connDict[nm] = self.currDict.copy()
				self.currDict = self.blankConn.copy()
		self.element = None
		
	
	def getConnectionDict(self):
		return self.connDict
	

def importConnections(file=None):
	if file is None:
		return None
	file = fileRef(file)
	ch = connHandler()
	xml.sax.parse(file, ch)
	ret = ch.getConnectionDict()
	return ret


def fileRef(ref=""):
	"""  Handles the passing of file names, file objects, or raw
	XML to the parser. Returns a file-like object, or None.
	"""
	ret = None
	if type(ref) == str:
		if os.path.exists(ref):
			ret = file(ref)
		else:
			ret = StringIO(ref)
	return ret
	