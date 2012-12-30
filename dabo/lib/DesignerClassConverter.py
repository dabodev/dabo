# -*- coding: utf-8 -*-
"""This is a class designed to take the JSON or XML in a Class Designer file
and return the class object represented by that file. Right now it's wxPython-
specific, since we only support wxPython, but I suppose that it could be updated
later on to support other UI toolkits.
"""
from datetime import datetime
import time
import os
import re
import random
import codecs
import tempfile
import dabo
dabo.ui.loadUI("wx")
from dabo.dLocalize import _
from dabo.dObject import dObject
from dabo.lib import utils
import dabo.ui.dialogs as dlgs
import dabo.lib.xmltodict as xtd
import dabo.lib.DesignerUtils as desUtil
from dabo.lib.utils import ustr
# Doesn't matter what platform we're on; Python needs
# newlines in its compiled code.
LINESEP = "\n"


class DesignerClassConverter(dObject):
	def __init__(self, *args, **kwargs):
		self._createDesignerControls = False
		super(DesignerClassConverter, self).__init__(*args, **kwargs)


	def afterInit(self):
		# Set the text definitions separately. Since they require special indentation to match the
		# generated code and not the code in this class, it is much cleaner to define them
		# separately.
		self._defineTextBlocks()
		# Expression for substituing default parameters
		self.prmDefPat = re.compile(r"([^=]+)=?.*")
		# Added to ensure unique object names
		self._generatedNames = [""]
		# Holds the class file we will create in order to aid introspection
		try:
			self._classFileName = self.Application.getTempFile("py")
		except AttributeError:
			# No app object
			fd, self._classFileName = tempfile.mkstemp(suffix="py")
			os.close(fd)
		self._codeImportAs = "_daboCode"
		# Holds any import statements to apply to the class code.
		self._import = ""
		# RE pattern to extract the method signature.
		self._codeDefExtract = re.compile("(\s*)def ([^\(]+)\(([^\)]*)\):")
		# Counter for the suffix that is appended to each method. This is simpler
		# than tracking each method name and only adding if there is a conflict.
		self._methodNum = 0
		# This is the text that will go into the temp .py file for executed code
		self._codeFileText = self._hdrText
		# Tracks the current sizer type
		self._sizerTypeStack = []
		# Location of the cdxml source file, if any
		self._srcFile = None
		# Encoding to be used
		self._encoding = dabo.getEncoding()


	def classFromText(self, src):
		"""Given a text file, returns a class object that that file
		represents. You can pass the text as either a file path,
		a file object, or raw XML/JSON text.
		"""
		dct = self.dictFromStoredText(src)
		# Traverse the dct, looking for superclass information
		super = self.flattenClassDict(dct)
		if super:
			# We need to modify the info to incorporate the superclass info
			self.addInheritedInfo(dct, super, updateCode=True)
		# Parse the returned dict and create the class definition text
		self.createClassText(dct)
		# Work-around for bug in which a trailing comment line throws an error
		self.classText += "\n"
		if isinstance(self.classText, unicode):
			self.classText = self.classText.encode(self._encoding)
		open(self._classFileName, "w").write(self.classText)

		## For debugging. This creates a copy of the generated code
		## so that you can help determine any problems.
		## egl: removed 2007-02-10. If you want to see the output,
		##   just uncomment the next 2 lines.
# 		debugName = "CLASSTEXT_%s.py" % time.strftime("%H%M%S", time.localtime())
#  		open(debugName, "w").write(self.classText)

		# jfcs added self._codeFileName to below
		# egl - created a tmp file for the main class code that we can use
		#   for compiling. This allows for full Python introspection.
		compClass = compile(self.classText, self._classFileName, "exec")
		nmSpace = {}
		exec compClass in nmSpace
		return nmSpace[self.mainClassName]


	def dictFromStoredText(self, src):
		"""Takes either a path to a text file, an open file containing the text,
		or the raw text itself. Determines the format of the stored text, and
		returns the corresponding dict.
		"""
		# Determine the type of the text. Try JSON first, then XML.
		try:
			dct = self.importXmlSrc(src)
		except ValueError:
			# Try JSON format
			dct = self.importJsonSource(src)
		self.addCodeFile(dct)
		return dct


	def addCodeFile(self, dct, pth=None, encoding=None):
		if pth is None:
			pth = self._srcFile
		if encoding is None:
			encoding = self._encoding
		# Get the associated code file, if any
		codePth = "%s-code.py" % os.path.splitext(pth)[0]
		if os.path.exists(codePth):
			try:
				codeContent = codecs.open(codePth, "r", encoding).read()
				codeDict = desUtil.parseCodeFile(codeContent)
				dct["importStatements"] = codeDict.pop("importStatements", "")
				desUtil.addCodeToClassDict(dct, codeDict)
			except StandardError, e:
				print "Failed to parse code file:", e


	def importJsonSource(self, src):
		"""This will read in a JSON source. The parameter can be a
		file path, an open file object, or the raw XML. It will look for
		a matching code file and, if found, import that code.
		"""
		parseCode = True
		try:
			# Try a file object
			jsonText = src.read()
			self._srcFile = src.name
		except AttributeError:
			if os.path.exists(src):
				self._srcFile = src = utils.resolvePathAndUpdate(src)
				jsonText = file(src).read()
			else:
				# It must be raw json
				jsonText = src
				self._srcFile = os.getcwd()
		return dabo.lib.jsonDecode(jsonText)


	def importXmlSrc(self, src):
		"""This will read in an XML source. The parameter can be a
		file path, an open file object, or the raw XML. It will look for
		a matching code file and, if found, import that code.
		"""
		parseCode = True
		if isinstance(src, file):
			xml = src.read()
			self._srcFile = src.name
		else:
			xml = src
			if not src.startswith("<"):
				xml = src = utils.resolvePathAndUpdate(src)
			if os.path.exists(src):
				self._srcFile = src
			else:
				parseCode = False
				self._srcFile = os.getcwd()
		return xtd.xmltodict(xml)


	@classmethod
	def addInheritedInfo(cls, src, super, updateCode=False):
		"""Called recursively on the class container structure, modifying
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
				cls.addInheritedInfo(kid, super, updateCode)


	def flattenClassDict(self, cd, retDict=None):
		"""Given a dict containing a series of nested objects such as would
		be created by restoring from a stored class file, returns a dict with all classIDs
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
		classFile = utils.resolvePath(atts.get("designerClass", ""))
		superclass = utils.resolvePath(atts.get("superclass", ""))
		superclassID = atts.get("superclassID", "")
		if superclassID and os.path.exists(superclass):
			# Get the superclass info
			superCD = self.dictFromStoredText(superclass)
			flattenClassDict(superCD, retDict)
		if classID:
			if os.path.exists(classFile):
				# Get the class info
				classCD = self.dictFromStoredText(classFile)
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
					self.flattenClassDict(kid, retDict)
			else:
				# Not a file; most likely just a component in another class
				currDict = retDict.get(classID, {})
				retDict[classID] = {"attributes": atts, "code": code,
						"properties": props}
				retDict[classID].update(currDict)
		if kids:
			for kid in kids:
				self.flattenClassDict(kid, retDict)
		return retDict


	def createClassText(self, dct, addImports=True, specList=[]):
		# 'self.classText' will contain the generated code
		self.classText = ""
		self.classText += self._clsHdrText
		if self.CreateDesignerControls:
			self.classText += self._designerClassGenText

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
		self._import = dct.get("importStatements", "")
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

		# Create the main class definition. Split off any module pathing first.
		try:
			modpath, shortClsName = nm.rsplit(".", 1)
		except ValueError:
			# Default to the dabo.ui module
			modpath = "dabo.ui"
			shortClsName = nm
		self.mainClassName = clsName = self.uniqename(shortClsName)

		# Wizards are constructed differently than other top-level classes.
		tmpSpace = {}
		stmnt = "from %s import %s" % (modpath, shortClsName)
		try:
			exec stmnt in tmpSpace
		except (ImportError, ValueError):
			pass
		isWiz = issubclass(tmpSpace.get(shortClsName), dlgs.Wizard)

		# Leave the third %s in place. That will be replaced by any
		# inner class definitions we create
		propInit = ""
		for prop, propDef in propDefs.items():
			val = propDef["defaultValue"]
			if val == "" and propDef["defaultType"] != "string":
				continue
			if propDef["defaultType"] == "string":
				val = "\"" + val + "\""
			propInit += "self._%s%s = %s" % (prop[0].lower(), prop[1:], val) + LINESEP
		if self.CreateDesignerControls:
			superName = "getControlClass(%s.%s)" % (modpath, shortClsName)
		else:
			superName = "%s.%s" % (modpath, shortClsName)
		prnt = self.currParent
		indCode = self.indentCode(propInit, 2)

		isOkDlg = (nm == "dOkCancelDialog")
		if isOkDlg:
			template = self.okCancelDialogClassTemplate
			stackinit = self._okCancelStackInitText
		elif isWiz:
			template = self.wizardClassTemplate
			stackinit = self._stackInitText
		else:
			template = self.containerClassTemplate
			stackinit = self._stackInitText
		self.classText += template  % locals()
		self.classText += stackinit

		if isWiz:
			self.createWizardPages(kids, specKids)
		else:
			# Add the child code.
			self.createChildCode(kids, specKids, isOkDlg)

		# Add any main class code
		for mthd, cd in code.items():
			if mthd == "importStatements":
				self._import += cd + LINESEP
				continue
			self.classText = "%s%s%s" % (self.classText, LINESEP, self.indentCode(cd, 1))
		# Add any property definitions
		for prop, propDef in propDefs.items():
			pdg = propDef["getter"]
			pds = propDef["setter"]
			pdd = propDef["deller"]
			pdc = propDef["comment"]
			self.classText += LINESEP + self._propDefText % locals()

		# Add any contained class definitions.
		if self.innerClassText:
			innerTxt = (3 * LINESEP) + self._innerClsDefText

			if self.CreateDesignerControls:
				superEval = "getControlClass(eval(clsName))"
			else:
				superEval = "eval(clsName)"
			# Add in the class definition text
			indCode = self.indentCode(self.innerClassText, 2)
			innerTxt = innerTxt % locals()
			self.classText += innerTxt

		# Add any import statements
		if addImports:
			impt = self._import
		else:
			impt = ""
		ct = self.classText
		if isinstance(ct, unicode):
			self.classText = ct.encode(self._encoding)
		if isinstance(impt, unicode):
			impt = impt.encode(self._encoding)
		self.classText = self.classText.replace("|classImportStatements|", impt)

		# We're done!
		return


	def createWizardPages(self, pgList, specPgList=[]):
		"""Takes a list of wizard page dicts, and adds their code to the
		generated class text.
		"""
		for pg in pgList:
			pgNm = pg["name"]
			pgAtts = pg["attributes"]
			pgKids = pg.get("children", [])
			pgCode = pg.get("code", {})
			pgProps = pg.get("properties", {})
			szKids = pgKids[0]["children"]

			try:
				pgMod, pgShortName = pgNm.rsplit(".", 1)
			except ValueError:
				pgMod = ""
				pgShortName = pgNm

			if pgCode or pgProps:
				custPgNm = self.createInnerClass(pgNm, pgAtts, pgCode, pgProps)
				txt = self._custWizardPageTemplate % locals()
			else:
				txt = self._wizardPageTemplate % locals()
			self.classText += LINESEP + txt

			# The page should only have one child: its main sizer. It will
			# already have been created when the page was appended, so
			# we just need to add its children to it.
			self.createChildCode(szKids)



	def createChildCode(self, childList, specChildList=[], force1x=False):
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

			try:
				modpath, shortClsName = nm.rsplit(".", 1)
			except ValueError:
				# Default to the dabo.ui module
				modpath = "dabo.ui"
				shortClsName = nm

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
			if force1x:
				szInfo["Expand"] = True
				szInfo["Proportion"] = 1
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
			# Do we need to pop the containership/sizer stacks?
			needPop = True

			clsname = self._extractKey(atts, "designerClass", "")
			isSizer = (clsname in ("LayoutSizer", "LayoutGridSizer",
					"LayoutBorderSizer")) or (nm in ("dSizer", "dBorderSizer", "dGridSizer"))
			isTree = (nm == "dTreeView")
			# This will get set to True if we process a splitter control
			isSplitter = False
			splitterString = ""
			try:
				# Classes will have a single numeric classID (e.g.: 123456789).
				# Components inside those classes will have the outer ID hypenated
				# with their own ID (e.g.: 123456789-987654321).
				isInherited = (len(atts["classID"].split("-")) == 1)
			except KeyError:
				isInherited = False
			if isInherited:
				if not os.path.exists(clsname):
					clsname = dabo.lib.utils.locateRelativeTo(self._srcFile, clsname)
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
			if isSizer:
				isGridSizer = clsname == "LayoutGridSizer"
				if isGridSizer:
					propString = ""
					propsToSend = []
					for att, val in atts.items():
						if att in ("HGap", "MaxRows", "MaxCols", "VGap"):
							propsToSend.append("%s=%s" % (att, val))
						elif att == "MaxDimension":
							propsToSend.append("%s='%s'" % (att, val))
					if propsToSend:
						propString = ", ".join(propsToSend)
				isBorderSizer = clsname == "LayoutBorderSizer"
				ornt = ""
				prnt = ""
				if isGridSizer:
					szType = "G"
				else:
					if "Orientation" not in atts:
						# Default to Horizontal
						atts["Orientation"] = "H"
					szType = atts["Orientation"]
					for unneeded in ("SlotCount", "classID"):
						atts.pop(unneeded, None)
					propString = ", ".join(["%s='%s'" % (k,v) for k,v in atts.items()])
					if isBorderSizer:
						prnt = "currParent, "
				if self.CreateDesignerControls:
					superName = clsname
				else:
					superName = "dabo.ui.%s" % nm
				self.classText += LINESEP + self._szText % locals()
				self._sizerTypeStack.append(szType)

			elif clsname == "LayoutSpacerPanel":
				if self.CreateDesignerControls:
					spcObjDef = "currSizer.append(LayoutSpacerPanel(currParent, Spacing=%(spc)s))"
				else:
					spcObjDef = "currSizer.appendSpacer(%(spc)s)"
				# Insert a spacer
				spc = atts.get("Spacing", "10")
				spcObjDef = spcObjDef % locals()
				self.classText += LINESEP + self._spcText % locals()

			elif clsname == "LayoutPanel":
				if isinstance(szInfo, basestring):
					szInfo = eval(szInfo)
				defSizerInfo = {"Expand": True,  "Proportion": 1}
				defSizerInfo.update(szInfo)
				szInfo = defSizerInfo
				if self.CreateDesignerControls:
					superName = "getControlClass(%s.%s)" % (modpath, "dPanel")
				else:
					superName = "%s.%s" % (modpath, "dPanel")
				attPropString = ", attProperties=%s" % cleanAtts
				self.classText += LINESEP + self._createControlText % locals()

			else:
				# This isn't a sizer; it's a control
				attPropString = ""
				moduleString = ""
				try:
					typ = self._sizerTypeStack[-1]
				except IndexError:
					typ = "H"
				szDefaults = desUtil.getDefaultSizerProps(nm, typ)
				if isinstance(szInfo, basestring):
					szInfo = eval(szInfo)
				szDefaults.update(szInfo)
				szInfo = szDefaults

				isSplitter = ("SashPosition" in atts)
				isSlidePanel = ("PanelCount" in atts)
				if isSplitter:
					pos = self._extractKey(cleanAtts, "SashPosition")
					ornt = self._extractKey(cleanAtts, "Orientation")
					splt = self._extractKey(cleanAtts, "Split")
					cleanAtts["Split"] = "False"
					cleanAtts["ShowPanelSplitMenu"] = "False"
					splitterString = self._spltText % locals()
				elif isSlidePanel:
					# We don't want panels auto-created by the PanelCount prop
					pnlCnt = self._extractKey(cleanAtts, "PanelCount")
				if isCustom:
					superName = "self.getCustControlClass('%s')" % nm
				else:
					if self.CreateDesignerControls:
						superName = "getControlClass(%s.%s)" % (modpath, shortClsName)
					else:
						superName = "%s.%s" % (modpath, shortClsName)
					attPropString = ", attProperties=%s" % cleanAtts
				self.classText += LINESEP + self._createControlText % locals()

			# If this item has child objects, push the appropriate objects
			# on their stacks, and add the push statements to the code.
			# We'll pop them back off at the end.
			if kids:
				if isSizer:
					# We need to set the current sizer to this one, and push any
					# existing sizer onto the stack.
					self.classText += LINESEP + self._kidSzText

				elif isSplitter:
					# Create the two panels as custom classes, and add them to the
					# splitter as those classes
					splitName = self.uniqename("splt")
					self.classText += LINESEP + ("""		%s = obj""" % splitName)
					kid = kids[0]
					kidCleanAtts = self.cleanAttributes(kid.get("attributes", {}))
					nm = kid.get("name")
					code = kid.get("code", {})
					grandkids1 = kid.get("children")
					p1nm = self.createInnerClass(nm, kidCleanAtts, code, custProps)
					self.classText += (LINESEP +
							"""		%(splitName)s.createPanes(self.getCustControlClass('%(p1nm)s'), pane=1)""" % locals())
					kid = kids[1]
					kidCleanAtts = self.cleanAttributes(kid.get("attributes", {}))
					nm = kid.get("name")
					code = kid.get("code", {})
					grandkids2 = kid.get("children")
					p2nm = self.createInnerClass(nm, kidCleanAtts, code, custProps)
					self.classText += (LINESEP +
							"""		%(splitName)s.createPanes(self.getCustControlClass('%(p2nm)s'), pane=2)""" % locals())
					hasGK = grandkids1 or grandkids2
					if hasGK:
						self.classText += LINESEP + self._childPushText

					# Clear the 'kids' value
					kids = []
					# We'll do our own stack popping here.
					needPop = False
					# Now create the panel kids, if any.
					if grandkids1:
						self.classText += LINESEP + (self._gk1Text % locals())
						# Call the create method recursively. When execution
						# returns to this level, all the children for this object will
						# have been added.
						self.createChildCode(grandkids1, specKids)

					if grandkids2:
						self.classText += LINESEP + (self._gk2Text % locals())
						# Call the create method recursively. When execution
						# returns to this level, all the children for this object will
						# have been added.
						self.createChildCode(grandkids2, specKids)

					if hasGK:
						self.classText += LINESEP + self._gkPopText

				elif isTree:
					self.classText += LINESEP + self._treeNodeText
					self.classText += LINESEP + (self._treeRootText % kids[0])
					needPop = False
					kids = []

				else:
					# We need to handle Grids and PageFrames separately,
					# since these 'children' are not random objects, but specific
					# classes.
					if (("ColumnCount" in atts) or ("PageCount" in atts) or ("PanelCount" in atts)):
						# Grid, pageframe or slide panel
						self.classText += LINESEP + self._complexCtlText
						isGrid = ("ColumnCount" in atts)
						isPageFrame = ("PageCount" in atts)
						if isPageFrame or isSlidePanel:
							# We need to set up a unique name for the control so
							# that all of the pages/panels can reference their
							# parent. Since these child containers can contain
							# lots of other stuff, the default 'obj' reference
							# will be trampled by the time the second child is
							# created.
							if isPageFrame:
								prntName = self.uniqename("pgf")
							elif isSlidePanel:
								prntName = self.uniqename("sldpn")
							self.classText += LINESEP + self._complexPrntRef % locals()
						for kid in kids:
							kidCleanAtts = self.cleanAttributes(kid.get("attributes", {}))
							if isGrid:
								self.classText += LINESEP + self._grdColText % locals()
							elif isPageFrame or isSlidePanel:
								# Paged control or Slide Panel control
								nm = kid.get("name")
								code = kid.get("code", {})
								subKids = kid.get("children")
								attPropString = ""
								moduleString = ""
								if code:
									nm = self.createInnerClass(nm, kidCleanAtts, code, {})
									nm = "self.getCustControlClass('%s')" % nm
								else:
									moduleString = "dabo.ui."
									attPropString = ", attProperties=%s" % kidCleanAtts
									kidCleanAtts = {}
								if isPageFrame:
									baseText = self._pgfPageText
								elif isSlidePanel:
									baseText = self._slidePanelText
								self.classText += LINESEP + baseText % locals()

								if subKids:
									self.createChildCode(subKids)
									self.classText += LINESEP + self._complexKidsText

						# We've already processed the child objects for these
						# grid/page controls, so clear the kids list.
						kids = []

					else:
						# We're adding things to a control. We have to clear
						# the current sizer, since the most likely child will
						# be the sizer that governs the contained controls.
						# Tell the class that we are dealing with a new parent object
						self.classText += LINESEP + self._childPushText
				if kids:
					# Call the create method recursively. When execution
					# returns to this level, all the children for this object will
					# have been added.
					self.createChildCode(kids, specKids)

				# Pop as needed off of the stacks.
				if needPop:
					if isSizer:
						self.classText += LINESEP + self._szPopText
						self._sizerTypeStack.pop()
					else:
						self.classText += LINESEP + self._ctlPopText
		return


	def createInnerClass(self, nm, atts, code, custProps):
		"""Define a class that will be used to create an instance of
		an object that contains its own method code and/or Properties.
		"""
		try:
			modpath, shortClsName = nm.rsplit(".", 1)
		except ValueError:
			# Default to the dabo.ui module
			modpath = "dabo.ui"
			shortClsName = nm
		clsName = self.uniqename(shortClsName)
		cleanAtts = self.cleanAttributes(atts)
		propInit = ""
		for prop, propDef in custProps.items():
			val = propDef["defaultValue"]
			if val == "" and propDef["defaultType"] != "string":
				continue
			if propDef["defaultType"] == "string":
				val = "\"" + val + "\""
			propInit += "self._%s%s = %s" % (prop[0].lower(), prop[1:], val) + LINESEP
		prnt = self.currParent
		indCode = self.indentCode(propInit, 2)
		self.innerClassText += self.classTemplate % locals()

		self.innerClassNames.append(clsName)
		# Since the code will be part of this class, which is at the outer level
		# of indentation, it needs to be indented one level.
		for mthd, cd in code.items():
			if mthd == "importStatements":
				self._import += cd + LINESEP
				continue
			self.innerClassText += self.indentCode(cd, 1)
			if not self.innerClassText.endswith(LINESEP):
				self.innerClassText += LINESEP
		# Add any property definitions
		for prop, propDef in custProps.items():
			pdg = propDef["getter"]
			pds = propDef["setter"]
			pdd = propDef["deller"]
			pdc = propDef["comment"]
			self.innerClassText += LINESEP + self._innerPropText % locals()
		self.innerClassText += (2 * LINESEP)
		return clsName


	def createInheritedClass(self, pth, specList):
		"""When a custom class is contained in a cdxml file, we need
		to add that class separately, and inherit from that. We will
		be passed a path to the cdxml file, along with a list of
		dictionaries that contains a dict for each level of specialization
		for this class.
		"""
		conv = DesignerClassConverter()
		xmlDict = conv.importXmlSrc(pth)
		conv.createClassText(xmlDict, addImports=False, specList=specList)
		self.innerClassText += conv.classText + (2 * LINESEP)
		self.innerClassNames.append(conv.mainClassName)
		return conv.mainClassName



	@staticmethod
	def indentCode(cd, level):
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


	def uniqename(self, nm):
		ret = ""
		while not ret or ret in self._generatedNames:
			# The empty string is always in the list, so it will run at least once.
			ret = "%s_%s" % (nm, random.randint(0,99999))
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
		dabo.lib.utils.resolveAttributePathing(ret, self._srcFile)
		return ret


	def _getCreateDesignerControls(self):
		return self._createDesignerControls

	def _setCreateDesignerControls(self, val):
		self._createDesignerControls = val


	CreateDesignerControls = property(_getCreateDesignerControls, _setCreateDesignerControls, None,
			_("When True, classes are mixed-in with the DesignerControlMixin  (bool)"))


	### Text block definitions follow. They're going after the prop defs ###
	### so as not to clutter the rest of the code visually.  ###
	def _defineTextBlocks(self):
		# Standard class template
		self.containerClassTemplate = """class %(clsName)s(%(superName)s):
	def __init__(self, parent=%(prnt)s, attProperties=%(cleanAtts)s, *args, **kwargs):
		super(%(clsName)s, self).__init__(parent=parent, attProperties=attProperties, *args, **kwargs)
		self.Sizer = None
%(indCode)s

"""
		# Standard template for wizards
		self.wizardClassTemplate = """class %(clsName)s(%(superName)s):
	def __init__(self, parent=%(prnt)s, attProperties=%(cleanAtts)s, *args, **kwargs):
		super(%(clsName)s, self).__init__(parent=parent, attProperties=attProperties, *args, **kwargs)
%(indCode)s

"""
		self.classTemplate = """class %(clsName)s(%(modpath)s.%(shortClsName)s):
	def __init__(self, parent=%(prnt)s, attProperties=%(cleanAtts)s, *args, **kwargs):
		%(modpath)s.%(shortClsName)s.__init__(self, parent=parent, attProperties=attProperties, *args, **kwargs)
%(indCode)s

"""
		# OK/Cancel dialog class template
		self.okCancelDialogClassTemplate = """class %(clsName)s(%(superName)s):
	def __init__(self, parent=%(prnt)s, attProperties=%(cleanAtts)s, *args, **kwargs):
		super(%(clsName)s, self).__init__(parent=parent, attProperties=attProperties, *args, **kwargs)
%(indCode)s
"""
		self._hdrText = """import dabo
dabo.ui.loadUI("wx")

"""
		self._clsHdrText = """import dabo
dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.lib.utils import ustr
import sys
|classImportStatements|

"""
		self._stackInitText = """		parentStack = []
		sizerDict = {}
		currParent = self
		currSizer = None
		sizerDict[currParent] = []
"""
		self._okCancelStackInitText = """	def addControls(self):
		parentStack = []
		sizerDict = {}
		currParent = self
		currSizer = self.Sizer
		sizerDict[currParent] = []
"""
		self._propDefText = """	%(prop)s = property(%(pdg)s, %(pds)s, %(pdd)s,
			\"\"\"%(pdc)s\"\"\")
"""
		self._innerClsDefText = """	def getCustControlClass(self, clsName):
		# Define the classes, and return the matching class
%(indCode)s
		return %(superEval)s"""

		self._szText = """		obj = %(superName)s(%(prnt)s%(propString)s)
		if currSizer:
			currSizer.append(obj%(rowColString)s)
			currSizer.setItemProps(obj, %(szInfo)s)
"""
		self._spcText = """		if currSizer:
			itm = %(spcObjDef)s
			currSizer.setItemProps(itm, %(szInfo)s)
"""
		self._spltText = """
		dabo.ui.setAfter(obj, "Orientation", "%(ornt)s")
		dabo.ui.setAfter(obj, "Split", %(splt)s)
		dabo.ui.setAfter(obj, "SashPosition", %(pos)s)
"""
		self._createControlText = """		obj = %(superName)s(currParent%(attPropString)s)%(splitterString)s
		if currSizer:
			currSizer.append(obj%(rowColString)s)
			currSizer.setItemProps(obj, %(szInfo)s)
"""
		self._kidSzText = """		if currSizer:
			sizerDict[currParent].append(currSizer)
		currSizer = obj
		if not currParent.Sizer:
			currParent.Sizer = obj
"""
		self._gk1Text = """		currParent = %(splitName)s.Panel1
		currSizer = None
		if not (currParent in sizerDict):
			sizerDict[currParent] = []
"""
		self._gk2Text = """		currParent = %(splitName)s.Panel2
		currSizer = None
		if not (currParent in sizerDict):
			sizerDict[currParent] = []
"""
		self._gkPopText = """		currParent = parentStack.pop()
		if not (currParent in sizerDict):
			sizerDict[currParent] = []
			currSizer = None
		else:
			try:
				currSizer = sizerDict[currParent].pop()
			except (KeyError, IndexError):
				pass
"""
		self._complexCtlText = """		parentStack.append(currParent)
		sizerDict[currParent].append(currSizer)
		currParent = obj
		sizerDict[currParent] = []
"""
		self._complexPrntRef = """		# save a reference to the parent control
		%(prntName)s = obj
"""
		self._grdColText = """		col = dabo.ui.dColumn(obj, attProperties=%(kidCleanAtts)s)
		obj.addColumn(col)
"""
		self._pgfPageText = """		pg = %(moduleString)s%(nm)s(%(prntName)s%(attPropString)s)
		%(prntName)s.appendPage(pg)
		currSizer = pg.Sizer = None
		parentStack.append(currParent)
		sizerDict[currParent].append(currSizer)
		currParent = pg
		sizerDict[currParent] = []
"""
		self._complexKidsText = """		currParent = parentStack.pop()
		if sizerDict[currParent]:
			try:
				currSizer = sizerDict[currParent].pop()
			except (KeyError, IndexError):
				pass
		else:
			currSizer = None
"""
		self._slidePanelText = """		pnl = %(moduleString)s%(nm)s(%(prntName)s%(attPropString)s)
		currSizer = pnl.Sizer = None
		parentStack.append(currParent)
		sizerDict[currParent].append(currSizer)
		currParent = pnl
		sizerDict[currParent] = []
"""
		self._treeNodeText = """		def _addDesTreeNode(_nodeParent, _nodeAtts, _kidNodes):
			_nodeCaption = self._extractKey(_nodeAtts, "Caption", "")
			if _nodeParent is None:
				obj.clear()
				_currNode = obj.setRootNode(_nodeCaption)
			else:
				_currNode = _nodeParent.appendChild(_nodeCaption)
			# Remove the name and designerClass atts
			self._extractKey(_nodeAtts, "name")
			self._extractKey(_nodeAtts, "designerClass")
			for _nodeProp, _nodeVal in _nodeAtts.items():
				try:
					exec "_currNode.%s = %s" % (_nodeProp, _nodeVal) in locals()
				except (SyntaxError, NameError):
					exec "_currNode.%s = \'%s\'" % (_nodeProp, _nodeVal) in locals()
			for _kidNode in _kidNodes:
				_kidAtts = _kidNode.get("attributes", {})
				_kidKids = _kidNode.get("children", {})
				_addDesTreeNode(_currNode, _kidAtts, _kidKids)
"""
		self._treeRootText = """		# Set the root
		_rootNode = %s
		_rootNodeAtts = _rootNode.get("attributes", {})
		_rootNodeKids = _rootNode.get("children", {})
		_addDesTreeNode(None, _rootNodeAtts, _rootNodeKids)
"""
		self._childPushText = """		parentStack.append(currParent)
		sizerDict[currParent].append(currSizer)
		currParent = obj
		currSizer = None
		if not (currParent in sizerDict):
			sizerDict[currParent] = []
"""
		self._szPopText = """		if sizerDict[currParent]:
			try:
				currSizer = sizerDict[currParent].pop()
			except (KeyError, IndexError):
				pass
		else:
			currSizer = None
"""
		self._ctlPopText = """		currParent = parentStack.pop()
		if not (currParent in sizerDict):
			sizerDict[currParent] = []
			currSizer = None
		else:
			try:
				currSizer = sizerDict[currParent].pop()
			except (KeyError, IndexError):
				pass
"""
		self._innerPropText = """	%(prop)s = property(%(pdg)s, %(pds)s, %(pdd)s,
			\"\"\"%(pdc)s\"\"\")
"""
		self._designerClassGenText = """from ClassDesignerControlMixin import ClassDesignerControlMixin as cmix
from ClassDesignerComponents import LayoutPanel
from ClassDesignerComponents import LayoutBasePanel
from ClassDesignerComponents import LayoutSpacerPanel
from ClassDesignerComponents import LayoutSizer
from ClassDesignerComponents import LayoutBorderSizer
from ClassDesignerComponents import LayoutGridSizer
from ClassDesignerComponents import LayoutSaverMixin
from ClassDesignerComponents import NoSizerBasePanel

def getControlClass(base):
	# Create a pref key that is the Designer key plus the name of the control
	prefkey = ustr(base).split(".")[-1].split("'")[0]
	class controlMix(cmix, base):
		superControl = base
		superMixin = cmix
		def __init__(self, *args, **kwargs):
			if hasattr(base, "__init__"):
				apply(base.__init__,(self,) + args, kwargs)
			parent = self._extractKey(kwargs, "parent")
			cmix.__init__(self, parent, **kwargs)
			self.NameBase = ustr(self._baseClass).split(".")[-1].split("'")[0]
			self.BasePrefKey = prefkey
	return controlMix

"""
		self._wizardPageTemplate = """		pg = self.append(%(pgMod)s.%(pgShortName)s)
		pg.setPropertiesFromAtts(%(pgAtts)s)
		currParent = pg
		sizerDict[currParent] = []
		currSizer = pg.Sizer
"""
		self._custWizardPageTemplate = """		pgCls = self.getCustControlClass('%(custPgNm)s')
		pg = self.append(pgCls)
		pg.setPropertiesFromAtts(%(pgAtts)s)
		currParent = pg
		sizerDict[currParent] = []
		currSizer = pg.Sizer
"""
