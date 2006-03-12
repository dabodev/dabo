"""This is a class designed to take the XML in a Class Designer .cdxml file
and return the class object represented by that XML. Right now it's wxPython-
specific, since we only support wxPython, but I suppose that it could be updated
later on to support other UI toolkits.
"""
from datetime import datetime
import os
import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.dObject import dObject
from dabo.lib.xmltodict import xmltodict as xtd



class DesignerXmlConverter(dObject):
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

#		compClass = compile(self.classText, "junk.py", "exec")
		compClass = compile(self.classText, "", "exec")
		exec compClass
		ret = eval(self.mainClassName)
		return ret
	
	
	def createClassText(self, dct):
		# 'self.classText' will contain the generated code
		self.classText = """import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents

"""
		# Standard class template
		self.classTemplate = """class %s(dabo.ui.%s):
	def __init__(self, parent=%s, attProperties=%s):
		dabo.ui.%s.__init__(self, parent=parent, attProperties=attProperties)
		self.Sizer = None

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
		cleanAtts = self.cleanAttributes(atts)
		kids = dct.get("children", [])
		code = dct.get("code", {})
		# properties??
		
		# Create the main class definition
		self.mainClassName = clsName = self.uniqname(nm)
		# Leave the third %s in place. That will be replaced by any
		# inner class definitions we create
		self.classText += 	self.classTemplate  % (clsName, nm, 
				self.currParent, cleanAtts, nm)
		self.classText += \
"""		parentStack = []
		sizerDict = {}
		currParent = self
		currSizer = None
		sizerDict[currParent] = []
"""	
		# Add the child code.
		self.createChildCode(kids)
		
		# Add any main class code
		for cd in code.values():
			self.classText += os.linesep + self.indentCode(cd, 1)
		
		# Add any contained class definitions.
		if self.innerClassText:
			innerTxt = (3 * os.linesep) + \
"""	def getCustControlClass(self, clsName):
		# Define the classes, and return the matching class
%s

		return eval(clsName)"""
			# Add in the class definition text
			innerTxt = innerTxt % self.indentCode(self.innerClassText, 2)
			self.classText += innerTxt
		
		# We're done!
		
		## For debugging. This creates a copy of the generated code
		## so that you can help determine any problems.
		open("CLASSTEXT.py", "w").write(self.classText)
		return
	
	
	def createChildCode(self, childList):
		"""Takes a list of child object dicts, and adds their code to the 
		generated class text.
		"""
		if not isinstance(childList, (list, tuple)):
			childList = [childList]
		for child in childList:
			nm = child.get("name")
			atts = child.get("attributes", {})
			cleanAtts = self.cleanAttributes(atts)
			szInfo = self._extractKey(atts, "sizerInfo", {})
			rcPos = self._extractKey(atts, "rowColPos")
			rowColString = ""
			if rcPos:
				rowColString = ", row=%s, col=%s" % eval(rcPos)
			kids = child.get("children", [])
			code = child.get("code", {})
			isCustom = False
			# properties??
			if code:
				nm = self.createInnerClass(nm, atts, code)
				isCustom = True
			isSizer = atts.get("designerClass", "") in ("LayoutSizer", "LayoutGridSizer",
					"LayoutBorderSizer")

			if isSizer:
				isGridSizer = atts.get("designerClass", "") == "LayoutGridSizer"
				ornt = ""
				if not isGridSizer:
					ornt = "Orientation='%s'" % self._extractKey(atts, "Orientation", "V")

				self.classText += os.linesep + \
"""		obj = dabo.ui.%s(%s)
		if currSizer:
			currSizer.append(obj%s)
			currSizer.setItemProps(obj, %s)
""" % (nm, ornt, rowColString, szInfo)
			
			else:
				# This isn't a sizer; it's a control
				attPropString = ""
				moduleString = ""
				if isCustom:
					nm = "self.getCustControlClass('%s')" % nm
				else:
					moduleString = "dabo.ui."
					attPropString = ", attProperties=%s" % cleanAtts
				self.classText += os.linesep + \
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
					self.classText += os.linesep + \
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
						self.classText += os.linesep + \
"""		parentStack.append(currParent)
"""
						isGrid = atts.has_key("ColumnCount")
						if not isGrid:
							# We need to set up a unique name for the pageframe
							# so that all of the pages can reference their parent. Since
							# pages can contain lots of other stuff, the default 'obj'
							# reference will be trampled by the time the second page 
							# is created.
							pgfName = self.uniqname("pgf")
							self.classText += os.linesep + \
"""		# save a reference to the pageframe control
		%s = obj
""" % pgfName
						for kid in kids:
							kidCleanAtts = self.cleanAttributes(kid.get("attributes", {}))
							if isGrid:
								self.classText += os.linesep + \
"""		col = dabo.ui.dColumn(obj, attProperties=%s)
		obj.addColumn(col)
		col.setPropertiesFromAtts(%s)
""" % (kidCleanAtts, kidCleanAtts)
							else:
								nm = kid.get("name")
								code = kid.get("code", {})
								pgKids = kid.get("children")
								attPropString = ""
								moduleString = ""
								# properties??
								if code:
									nm = self.createInnerClass(nm, atts, code)
									nm = "self.getCustControlClass('%s')" % nm
								else:
									moduleString = "dabo.ui."
									attPropString = ", attProperties=%s" % kidCleanAtts
				
								self.classText += os.linesep + \
"""		pg = %s%s(%s%s)
		%s.appendPage(pg)
		pg.setPropertiesFromAtts(%s)
		currSizer = pg.Sizer = None
		parentStack.append(currParent)
		currParent = pg
		sizerDict[currParent] = []
""" % (moduleString, nm, pgfName, attPropString, pgfName, kidCleanAtts)

								if pgKids:
									self.createChildCode(pgKids)								
						# We've already processed the child objects for these
						# grid/page controls, so clear the kids list.
						kids = []

					else:
						# We're adding things to a control. We have to clear
						# the current sizer, since the most likely child will 
						# be the sizer that governs the contained controls.
						# Tell the class that we are dealing with a new parent object
						self.classText += os.linesep + \
"""		parentStack.append(currParent)
		currParent = obj
		currSizer = None
		if not sizerDict.has_key("currParent"):
			sizerDict[currParent] = []
"""
				if kids:
					# Call the create method recursively. When execution
					# returns to this level, all the children for this object will
					# have been added.
					self.createChildCode(kids)
					
				# Pop as needed off of the stacks.
				if isSizer:
					self.classText += os.linesep + \
"""		if sizerDict[currParent]:
			currSizer = sizerDict[currParent].pop()
"""
				
				else:
					self.classText += os.linesep + \
"""		currParent = parentStack.pop()
		if not sizerDict.has_key("currParent"):
			sizerDict[currParent] = []
"""
		return				

	
	def createInnerClass(self, nm, atts, code):
		"""Define a class that will be used to create an instance of
		an object that contains its own method code.
		"""
		clsName = self.uniqname(nm)
		self.innerClassText += self.classTemplate  % (clsName, nm, 
				self.currParent, atts, nm)
		self.innerClassNames.append(clsName)
		# Since the code will be part of this class, which is at the outer level
		# of indentation, it needs to be indented one level.
		for cd in code.values():
# 			self.innerClassText += os.linesep + self.indentCode(cd, 1)
			self.innerClassText += self.indentCode(cd, 1)
		self.innerClassText += (2 * os.linesep)
		return clsName


	def indentCode(self, cd, level):
		"""Takes code and indents it to the desired level"""
		lns = cd.splitlines()
		indent = "\t" * level
		jn = os.linesep + indent
		ret = jn.join(lns)
		if ret:
			# Need to add the indent to the first line, too
			ret = indent + ret
		return ret
	
	
	def uniqname(self, nm):
		return "%s_%s" % (nm, str(datetime.utcnow().__hash__()).replace("-", "9"))
	

	def cleanAttributes(self, attDict):
		"""Return a dict that is the same as the source dict, dropping any 
		attributes that the Designer added that are not used
		in the runtime objects.
		"""
		ret = {}
		for key, val in attDict.items():
			if key not in ("SlotCount", "designerClass", "rowColPos", "sizerInfo",
					"PageCount", "ColumnCount", "classID", "savedClass"):
				if key == "Name":
					# Change it to 'NameBase' instead
					ret["NameBase"] = val
				else:
					ret[key] = val
		return ret
		
