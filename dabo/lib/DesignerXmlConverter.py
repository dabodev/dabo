"""This is a class designed to take the XML in a Class Designer .cdxml file
and return the class object represented by that XML. Right now it's wxPython-
specific, since we only support wxPython, but I suppose that it could be updated
later on to support other UI toolkits.
"""
from datetime import datetime
import os
import re
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.dObject import dObject
from dabo.lib.xmltodict import xmltodict as xtd
# Doesn't matter what platform we're on; Python needs 
# newlines in its compiled code.
LINESEP = "\n"


class DesignerXmlConverter(dObject):
	def afterInit(self):
		# Added to ensure unique object names
		self._generatedNames = []
		# Holds the text for the generated code file
		self._codeFileName = self.Application.getTempFile("py")
		self._codeImportAs = "_daboCode"
		# Holds any import statements to apply to the class code.
		self._import = ""
		# RE pattern to extract the method signature.
		self._codeDefExtract = re.compile("(\s*)def ([^\(]+)\(([^\)]*)\):")
		# Counter for the suffix that is appended to each method. This is simpler
		# than tracking each method name and only adding if there is a conflict.
		self._methodNum = 0
		# This is the text that will go into the temp .py file for executed code
		self._codeFileText = """import dabo
dabo.ui.loadUI("wx")

"""
		
	
	def classFromXml(self, src):
		"""Given a cdxml file, returns a class object that that file 
		represents. You can pass the cdxml as either a file path, 
		a file object, or xml text.
		"""
		if isinstance(src, file):
			xml = src.read()
		else:
			if os.path.exists(src):
				xml = open(src).read()
			else:
				xml = src
		dct = xtd(xml)
		# Parse the XML and create the class definition text
		self.createClassText(dct)
		# Write the code file
		txt = self._import + LINESEP + self._codeFileText
		open(self._codeFileName, "w").write(txt)
		# Add the imports to the main file, too.
		self.classText = self.classText % (self._import + LINESEP,)
		
		## For debugging. This creates a copy of the generated code
		## so that you can help determine any problems.
		open("CLASSTEXT.py", "w").write(self.classText)

		compClass = compile(self.classText, "", "exec")
		nmSpace = {}
		exec compClass in nmSpace
		return nmSpace[self.mainClassName]

	
	def createClassText(self, dct, addImports=True, specList=[]):
		# 'self.classText' will contain the generated code
		self.classText = ""
		cdPath, cdFile = os.path.split(self._codeFileName)
		cdPath = cdPath.replace("\\", r"\\")
		cdFileNoExt = os.path.splitext(cdFile)[0]
		if addImports:
			self.classText += """import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
import sys
# debugging!
if "%s" not in sys.path:
	sys.path.append("%s")
import %s as %s
%s

""" % (cdPath, cdPath, cdFileNoExt, self._codeImportAs, "%s")

		# Standard class template
		self.classTemplate = """class %s(dabo.ui.%s):
	def __init__(self, parent=%s, attProperties=%s):
		dabo.ui.%s.__init__(self, parent=parent, attProperties=attProperties)
		self.Sizer = None
%s		

"""
		# Holds any required class definitions for contained objects
		self.innerClassText = ""
		self.innerClassNames = []
		self.parentStack = []
		self.sizerDict = {}
		self.indent = 1
		self.currParent = None
	
		nm = dct.get("name")
		atts = dct.get("attributes", {})
		code = dct.get("code", {})
		propDefs = dct.get("properties", {})
		kids = dct.get("children", [])
		clsID = atts.get("classID", None)
		rmv = []
		specKids = []
		for itm in specList:
			if itm:
				target = [subitem for subitem in itm
						if subitem.get("attributes", {}).get("classID", "") == clsID]
				if target:
					atts.update(target[0].get("attributes", {}))
					specKids.append(target[0].get("children", []))
					code.update(target[0].get("code", {}))
			else:
				rmv.append(itm)
		for rm in rmv:
			specList.remove(rm)
		cleanAtts = self.cleanAttributes(atts)
		
		# Create the main class definition
		self.mainClassName = clsName = self.uniqname(nm)
		# Leave the third %s in place. That will be replaced by any
		# inner class definitions we create
		propInit = ""
		for prop, propDef in propDefs.items():
			val = propDef["defaultValue"]
			if propDef["defaultType"] == "string":
				val = "\"" + val + "\""
			propInit += "self._%s%s = %s" % (prop[0].lower(), prop[1:], val) + LINESEP
		self.classText += 	self.classTemplate  % (clsName, nm, 
				self.currParent, cleanAtts, nm, self.indentCode(propInit, 2))
		self.classText += \
"""		parentStack = []
		sizerDict = {}
		currParent = self
		currSizer = None
		sizerDict[currParent] = []
"""	
		# Add the child code.
		self.createChildCode(kids, specKids)
		
		# Add any main class code
		for mthd, cd in code.items():
			if mthd == "importStatements":
				self._import += cd + LINESEP
				continue
			codeProx = self.createProxyCode(cd)
			self.classText += LINESEP + self.indentCode(codeProx, 1)
		# Add any property definitions
		for prop, propDef in propDefs.items():
			self.classText += LINESEP + \
"""	%s = property(%s, %s, %s, 
			\"\"\"%s\"\"\")
""" % (prop, propDef["getter"], propDef["setter"], propDef["deller"], 
		propDef["comment"])
		
		# Add any contained class definitions.
		if self.innerClassText:
			innerTxt = (3 * LINESEP) + \
"""	def getCustControlClass(self, clsName):
		# Define the classes, and return the matching class
%s
		return eval(clsName)"""
			# Add in the class definition text
			innerTxt = innerTxt % self.indentCode(self.innerClassText, 2)
			self.classText += innerTxt
		
		# We're done!
		return
	
	
	def createChildCode(self, childList, specChildList=[]):
		"""Takes a list of child object dicts, and adds their code to the 
		generated class text.
		"""
		if not isinstance(childList, (list, tuple)):
			childList = [childList]
		if not isinstance(specChildList, (list, tuple)):
			specChildList = [[specChildList]]
		elif (len(specChildList) == 0) or not isinstance(specChildList[0], (list, tuple)):
			specChildList = [specChildList]
		for child in childList:
			nm = child.get("name")
			atts = child.get("attributes", {})
			clsID = atts.get("classID", "")
			specChild = {}
			specKids = []
			specCode = {}
			for spc in specChildList:
				specChildMatch = [specChild for specChild in spc
						if specChild.get("attributes", {}).get("classID", None) == clsID]
				if specChildMatch:
					specChild = specChildMatch[0]
					atts.update(specChild.get("attributes", {}))
					specKids.append(specChild.get("children", []))
					specCode.update(specChild.get("code", {}))
			cleanAtts = self.cleanAttributes(atts)
			szInfo = self._extractKey(atts, "sizerInfo", {})
			rcPos = self._extractKey(atts, "rowColPos")
			rowColString = ""
			if rcPos:
				rowColString = ", row=%s, col=%s" % eval(rcPos)
			kids = child.get("children", [])
			code = child.get("code", {})
			custProps = child.get("properties", {})
			code.update(specCode)
			isCustom = False
			isInherited = False
			
			clsname = self._extractKey(atts, "designerClass", "")
			if os.path.exists(clsname) and atts.has_key("classID"):
				chldList = [[child]] + specChildList[:]
				nm = self.createInheritedClass(clsname, chldList)
				code = {}
				kids = []
				isCustom = True
				isInherited = True
			else:
				if code or custProps:
					nm = self.createInnerClass(nm, atts, code, custProps)
					isCustom = True

			isSizer = (clsname in ("LayoutSizer", "LayoutGridSizer",
					"LayoutBorderSizer")) or (nm in ("dSizer", "dBorderSizer", "dGridSizer"))
			if isSizer:
				isGridSizer = clsname == "LayoutGridSizer"
				isBorderSizer = clsname == "LayoutBorderSizer"
				ornt = ""
				if not isGridSizer:
					ornt = "Orientation='%s'" % self._extractKey(atts, "Orientation", "H")
				prnt = ""
				if isBorderSizer:
					prnt = "currParent, "
					ornt = "%s, Caption=\"%s\"" % (ornt, self._extractKey(atts, "Caption", ""))
				self.classText += LINESEP + \
"""		obj = dabo.ui.%s(%s%s)
		if currSizer:
			currSizer.append(obj%s)
			currSizer.setItemProps(obj, %s)
""" % (nm, prnt, ornt, rowColString, szInfo)
			
			elif clsname == "LayoutSpacerPanel":
				# Insert a spacer
				spc = atts.get("Spacing", "10")
				self.classText += LINESEP + \
"""		if currSizer:
			itm = currSizer.appendSpacer(%s)
			currSizer.setItemProps(itm, %s)
""" % (spc, szInfo)
			else:
				# This isn't a sizer; it's a control
				attPropString = ""
				moduleString = ""
				if isCustom:
					nm = "self.getCustControlClass('%s')" % nm
				else:
					moduleString = "dabo.ui."
					attPropString = ", attProperties=%s" % cleanAtts
				self.classText += LINESEP + \
"""		obj = %s%s(currParent%s)
		if currSizer:
			currSizer.append(obj%s)
			currSizer.setItemProps(obj, %s)
""" % (moduleString, nm, attPropString, rowColString, szInfo)
			
			# If this item has child objects, push the appropriate objects
			# on their stacks, and add the push statements to the code.
			# We'll pop them back off at the end.
			if kids:
				if isSizer:
					# We need to set the current sizer to this one, and push any
					# existing sizer onto the stack.
					self.classText += LINESEP + \
"""		if currSizer:
			sizerDict[currParent].append(currSizer)
		currSizer = obj
		if not currParent.Sizer:
			currParent.Sizer = obj
"""
				else:
					# We need to handle Grids and PageFrames separately,
					# since these 'children' are not random objects, but specific
					# classes.
					if atts.has_key("ColumnCount") or atts.has_key("PageCount"):
						# Grid or pageframe
						self.classText += LINESEP + \
"""		parentStack.append(currParent)
		sizerDict[currParent].append(currSizer)
		currParent = obj
		sizerDict[currParent] = []
"""
						isGrid = atts.has_key("ColumnCount")
						if not isGrid:
							# We need to set up a unique name for the pageframe
							# so that all of the pages can reference their parent. Since
							# pages can contain lots of other stuff, the default 'obj'
							# reference will be trampled by the time the second page 
							# is created.
							pgfName = self.uniqname("pgf")
							self.classText += LINESEP + \
"""		# save a reference to the pageframe control
		%s = obj
""" % pgfName
						for kid in kids:
							kidCleanAtts = self.cleanAttributes(kid.get("attributes", {}))
							if isGrid:
								self.classText += LINESEP + \
"""		col = dabo.ui.dColumn(obj, attProperties=%s)
		obj.addColumn(col)
		col.setPropertiesFromAtts(%s)
""" % (kidCleanAtts, kidCleanAtts)
							else:
								# Paged control
								nm = kid.get("name")
								code = kid.get("code", {})
								pgKids = kid.get("children")
								attPropString = ""
								moduleString = ""
								# properties??
								if code:
									nm = self.createInnerClass(nm, atts, code, {})
									nm = "self.getCustControlClass('%s')" % nm
								else:
									moduleString = "dabo.ui."
									attPropString = ", attProperties=%s" % kidCleanAtts
				
								self.classText += LINESEP + \
"""		pg = %s%s(%s%s)
		%s.appendPage(pg)
		pg.setPropertiesFromAtts(%s)
		currSizer = pg.Sizer = None
		parentStack.append(currParent)
		sizerDict[currParent].append(currSizer)
		currParent = pg
		sizerDict[currParent] = []
""" % (moduleString, nm, pgfName, attPropString, pgfName, kidCleanAtts)

								if pgKids:
									self.createChildCode(pgKids)
									self.classText += LINESEP + \
"""		currParent = parentStack.pop()
		if sizerDict[currParent]:
			currSizer = sizerDict[currParent].pop()
		else:
			currSizer = None
"""

						# We've already processed the child objects for these
						# grid/page controls, so clear the kids list.
						kids = []

					else:
						# We're adding things to a control. We have to clear
						# the current sizer, since the most likely child will 
						# be the sizer that governs the contained controls.
						# Tell the class that we are dealing with a new parent object
						self.classText += LINESEP + \
"""		parentStack.append(currParent)
		sizerDict[currParent].append(currSizer)
		currParent = obj
		currSizer = None
		if not sizerDict.has_key(currParent):
			sizerDict[currParent] = []
"""
				if kids:
					# Call the create method recursively. When execution
					# returns to this level, all the children for this object will
					# have been added.
					self.createChildCode(kids, specKids)
					
				# Pop as needed off of the stacks.
				if isSizer:
					self.classText += LINESEP + \
"""		if sizerDict[currParent]:
			currSizer = sizerDict[currParent].pop()
		else:
			currSizer = None
"""
				
				else:
					self.classText += LINESEP + \
"""		currParent = parentStack.pop()
		if not sizerDict.has_key(currParent):
			sizerDict[currParent] = []
			currSizer = None
		else:
			currSizer = sizerDict[currParent].pop()
"""
		return				

	
	def createInnerClass(self, nm, atts, code, custProps):
		"""Define a class that will be used to create an instance of
		an object that contains its own method code and/or Properties.
		"""
		clsName = self.uniqname(nm)
		cleanAtts = self.cleanAttributes(atts)
		propInit = ""
		for prop, propDef in custProps.items():
			val = propDef["defaultValue"]
			if propDef["defaultType"] == "string":
				val = "\"" + val + "\""
			propInit += "self._%s%s = %s" % (prop[0].lower(), prop[1:], val) + LINESEP
		
		self.innerClassText += self.classTemplate  % (clsName, nm, 
				self.currParent, cleanAtts, nm, self.indentCode(propInit, 2))

		self.innerClassNames.append(clsName)
		# Since the code will be part of this class, which is at the outer level
		# of indentation, it needs to be indented one level.
		for mthd, cd in code.items():
			if mthd == "importStatements":
				self._import += cd + LINESEP
				continue
			codeProx = self.createProxyCode(cd)
			self.innerClassText += self.indentCode(codeProx, 1)
			if not self.innerClassText.endswith(LINESEP):
				self.innerClassText += LINESEP
# 			self.innerClassText += self.indentCode(cd, 1)
		# Add any property definitions
		for prop, propDef in custProps.items():
			self.innerClassText += LINESEP + \
"""	%s = property(%s, %s, %s, 
			\"\"\"%s\"\"\")
""" % (prop, propDef["getter"], propDef["setter"], propDef["deller"], 
		propDef["comment"])
		
		self.innerClassText += (2 * LINESEP)
		return clsName
	
	
	def createProxyCode(self, cd):
		"""Creates the substitute method call that will call the actual method in the temp file."""
		# Get the method name and params
		indnt, mthd, prmText = self._codeDefExtract.search(cd).groups()
		# Create the proxy method name
		proxMthd = "%s_%s" % (mthd, self._methodNum)
		self._methodNum += 1
		# Create the proxy call
		prox = "%sdef %s(%s):%s%s\treturn %s.%s(%s)" % (indnt, mthd, prmText, LINESEP, 
				indnt, self._codeImportAs, proxMthd, prmText)
		# Add the code to the output text
		cdOut = cd.replace(mthd, proxMthd, 1)
		self._codeFileText += cdOut + LINESEP + LINESEP
		return prox


	def createInheritedClass(self, pth, specList):
		"""When a custom class is contained in a cdxml file, we need
		to add that class separately, and inherit from that. We will 
		be passed a path to the cdxml file, along with a list of 
		dictionaries that contains a dict for each level of specialization
		for this class. 
		"""
		conv = DesignerXmlConverter()
		xml = open(pth).read()
		xmlDict = xtd(xml)
		conv.createClassText(xmlDict, addImports=False, specList=specList)
		self.innerClassText += conv.classText + (2 * LINESEP)
		self.innerClassNames.append(conv.mainClassName)
		return conv.mainClassName
		


	def indentCode(self, cd, level):
		"""Takes code and indents it to the desired level"""
		lns = cd.splitlines()
		indent = "\t" * level
		# Compiled code needs newlines, no matter what platform.
		jn = "\n" + indent
		ret = jn.join(lns)
		if ret:
			# Need to add the indent to the first line, too
			ret = indent + ret
		return ret
	
	
	def uniqname(self, nm):
		ret = ""
		while not ret or ret in self._generatedNames:
			ret = "%s_%s" % (nm, str(datetime.utcnow().__hash__()).replace("-", "9"))
		self._generatedNames.append(ret)
		return ret
	

	def cleanAttributes(self, attDict):
		"""Return a dict that is the same as the source dict, dropping any 
		attributes that the Designer added that are not used
		in the runtime objects.
		"""
		ret = {}
		for key, val in attDict.items():
			if key not in ("SlotCount", "designerClass", "rowColPos", 
					"sizerInfo", "PageCount", "ColumnCount", "propertyDefinitions",
					"classID", "savedClass"):
				if key == "Name":
					# Change it to 'NameBase' instead
					ret["NameBase"] = val
				else:
					ret[key] = val
		return ret
		
