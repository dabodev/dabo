import xml.sax

class FieldSpecHandler(xml.sax.ContentHandler):
	def __init__(self):
		self.appDict = {}
		self.currTableDict = {}
		self.currTable = ""
		self.currFieldDict = {}
		self.currRelaDict = {}
	
	def startElement(self, name, attrs):
		if name == "table":
			# New table starting
			self.currTable = attrs.getValue("name")
			self.currTableDict = {}
			self.currFieldDict = {}
			self.currRelaDict = {}

		elif name == "field":
			for att in attrs.keys():
				if att == "name":
					fldName = attrs.getValue("name")
				else:
					self.currFieldDict[att] = attrs.getValue(att)
			self.currTableDict[fldName] = self.currFieldDict.copy()

		elif name == "relation":
			target = attrs.getValue("target")
			relaName = "RELATION::" + target
			self.currRelaDict["target"] = target
			self.currRelaDict["parentField"] = attrs.getValue("parentField")
			self.currRelaDict["childField"] = attrs.getValue("childField")
			self.currTableDict[relaName] = self.currRelaDict.copy()
			
			
	
	def endElement(self, name):
		if name == "table":
			# Save it to the app dict
			self.appDict[self.currTable] = self.currTableDict.copy()
	
	def getFieldDict(self):
		return self.appDict
	

def importFieldSpecs(file=None, tbl=None):
	if file is None:
		return None
	fsh = FieldSpecHandler()
	xml.sax.parse(file, fsh)
	ret = fsh.getFieldDict()
	
	# Limit it to a specific table if requested
	if tbl is not None:
		ret = ret[tbl]
	
	return ret
