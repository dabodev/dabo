# -*- coding: utf-8 -*-
"""These are routines that are used to work with Class Designer code that has
been separated from the design.
"""
import re
import copy



def getCodeObjectSeperator():
	return "## *!* ## Dabo Code ID: "


def parseCodeFile(txt):
	"""This method takes the content of a code file saved by the class
	designer and parses it into a dict containing the code-ID values as
	keys, and a dict containing the methods as the values.
	"""
	codeObjectSep = getCodeObjectSeperator()
	ret = {}
	# regexp for extracting method names
	pat = re.compile("^(def ([^\(]+)\([^\)]*\):)\s*\n", re.M)
	# Replace any DOS-style newlines
	txt = txt.replace("\r\n", "\n")
	# The zero-th piece is the comments at the top of the file.
	codeParts = txt.split(codeObjectSep)
	imptPart = codeParts[0]
	codeObjs = codeParts[1:]
	# See if there are import statements
	imptLines = [ln for ln in imptPart.splitlines()
			if ln.strip()
			and not ln.strip().startswith("#")]
	ret["importStatements"] = "\n".join(imptLines)

	for codeObj in codeObjs:
		cd = {}
		# The first line in the code-ID, the rest is the code for
		# that object
		codeID, mthds = codeObj.split("\n", 1)

		mthdList = pat.split(mthds)
		# Element 0 is either empty or an import statement; the methods appear is
		# groups of three elements each: the 'def' line, followed by the method
		# name, followed by the method body.
		impt = mthdList[0]
		if impt:
			ret["importStatements"] += impt
		mthdList = mthdList[1:]
		while mthdList:
			cd[mthdList[1]] = "\n".join((mthdList[0], mthdList[2].rstrip()))
			mthdList = mthdList[3:]
		ret[codeID] = cd
	return ret


def addCodeToClassDict(clsd, cd):
	"""Takes the code that was stored in a separate file and re-integrates
	it into the class dict. Since this is a recursive structure, with children
	nested inside other children, it will be called recursively. No return
	value, as it modifies the class dict directly.
	"""
	atts = clsd.get("attributes", {})
	codeID = atts.get("code-ID", "")
	if codeID:
		clsd["code"] = cd.get(codeID, {})
	for kid in clsd.get("children", []):
		addCodeToClassDict(kid, cd)


def getSizerDefaults():
	"""Return a dict that contains the defaults for the various controls based upon
	what sort of sizer they are contained within.
	"""
	import dabo.ui as dui  ## kept here on purpose
	szDefaults = {}
	defVals = {
			"G": {"BorderSides": ["All"], "Proportion": 0, "HAlign": "Center", "VAlign": "Middle", "Border": 0, "Expand": True, "RowExpand": False, "ColExpand": True},
			"H": {"BorderSides": ["All"], "Proportion": 1, "HAlign": "Left", "VAlign": "Middle", "Border": 0, "Expand": True},
			"V": {"BorderSides": ["All"], "Proportion": 1, "HAlign": "Center", "VAlign": "Top", "Border": 0, "Expand": True}
			}
	# Use the defaults for each class, except where specified
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dBox] = dct
	szDefaults["dBox"] = dct
	dct = copy.deepcopy(defVals)
	dct["H"].update({"HAlign" : "center"})
	dct["V"].update({"VAlign" : "middle"})
	szDefaults[dui.dBitmap] = dct
	szDefaults["dBitmap"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "HAlign" : "center", "VAlign" : "middle",
			"ColExpand": False})
	dct["H"].update({"Proportion" : 0, "Expand" : False, "HAlign": "center"})
	dct["V"].update({"Proportion" : 0, "Expand" : False, "VAlign": "middle"})
	szDefaults[dui.dBitmapButton] = dct
	szDefaults["dBitmapButton"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "ColExpand": False})
	dct["H"].update({"Proportion" : 0, "Expand" : False})
	dct["V"].update({"Proportion" : 0, "Expand" : False})
	szDefaults[dui.dButton] = dct
	szDefaults["dButton"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "ColExpand": False})
	dct["H"].update({"Proportion" : 0, "Expand" : False})
	dct["V"].update({"Proportion" : 0, "Expand" : False})
	szDefaults[dui.dCheckBox] = dct
	szDefaults["dCheckBox"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "ColExpand": False})
	dct["H"].update({"Proportion" : 1, "Expand" : False})
	dct["V"].update({"Proportion" : 0, "Expand" : True})
	szDefaults[dui.dComboBox] = dct
	szDefaults["dComboBox"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "ColExpand": False})
	dct["H"].update({"Proportion" : 1, "Expand" : False})
	dct["V"].update({"Proportion" : 0, "Expand" : True})
	szDefaults[dui.dDateTextBox] = dct
	szDefaults["dDateTextBox"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dDialog] = dct
	szDefaults["dDialog"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "ColExpand": False})
	dct["H"].update({"Proportion" : 1, "Expand" : False})
	dct["V"].update({"Proportion" : 0, "Expand" : True})
	szDefaults[dui.dDropdownList] = dct
	szDefaults["dDropdownList"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dEditBox] = dct
	szDefaults["dEditBox"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dEditor] = dct
	szDefaults["dEditor"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dSlidePanelControl] = dct
	szDefaults["dSlidePanelControl"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "ColExpand": False})
	dct["H"].update({"Proportion" : 1, "Expand" : False})
	dct["V"].update({"Proportion" : 0, "Expand" : True})
	szDefaults[dui.dGauge] = dct
	szDefaults["dGauge"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dGrid] = dct
	szDefaults["dGrid"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dGridSizer] = dct
	szDefaults["dGridSizer"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dHtmlBox] = dct
	szDefaults["dHtmlBox"] = dct
	dct = copy.deepcopy(defVals)
	dct["H"].update({"HAlign" : "center"})
	dct["V"].update({"VAlign" : "middle"})
	szDefaults[dui.dImage] = dct
	szDefaults["dImage"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "ColExpand": False})
	dct["H"].update({"Proportion" : 0, "Expand" : False})
	dct["V"].update({"Proportion" : 0, "Expand" : False})
	szDefaults[dui.dLabel] = dct
	szDefaults["dLabel"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "HAlign" : "center", "VAlign" : "middle"})
	dct["H"].update({"Proportion" : 1, "Expand" : False, "HAlign": "center"})
	dct["V"].update({"Proportion" : 0, "Expand" : True, "VAlign": "middle"})
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 1, "Expand" : True, "HAlign" : "center", "VAlign" : "middle"})
	dct["H"].update({"Proportion" : 1, "Expand" : True, "HAlign": "center"})
	dct["V"].update({"Proportion" : 1, "Expand" : True, "VAlign": "middle"})
	szDefaults[dui.dLed] = dct
	szDefaults["dLed"] = dct
	szDefaults[dui.dLine] = dct
	szDefaults["dLine"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dListBox] = dct
	szDefaults["dListBox"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dListControl] = dct
	szDefaults["dListControl"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dOkCancelDialog] = dct
	szDefaults["dOkCancelDialog"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "ColExpand": True, "RowExpand": False})
	dct["H"].update({"Proportion" : 0, "Expand" : False})
	dct["V"].update({"Proportion" : 0, "Expand" : False})
	szDefaults[dui.dRadioList] = dct
	szDefaults["dRadioList"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dPage] = dct
	szDefaults["dPage"] = dct
	dct["H"].update({"HAlign" : "center"})
	dct["V"].update({"VAlign" : "middle"})
	szDefaults[dui.dPanel] = dct
	szDefaults["dPanel"] = dct
	dct = copy.deepcopy(defVals)
	dct["H"].update({"HAlign" : "center"})
	dct["V"].update({"VAlign" : "middle"})
	szDefaults[dui.dScrollPanel] = dct
	szDefaults["dScrollPanel"] = dct
	dct = copy.deepcopy(defVals)
	dct["H"].update({"HAlign" : "center"})
	dct["V"].update({"VAlign" : "middle"})
	szDefaults[dui.dPageFrame] = dct
	szDefaults["dPageFrame"] = dct
	dct = copy.deepcopy(defVals)
	dct["H"].update({"HAlign" : "center"})
	dct["V"].update({"VAlign" : "middle"})
	szDefaults[dui.dPageList] = dct
	szDefaults["dPageList"] = dct
	dct = copy.deepcopy(defVals)
	dct["H"].update({"HAlign" : "center"})
	dct["V"].update({"VAlign" : "middle"})
	szDefaults[dui.dPageSelect] = dct
	szDefaults["dPageSelect"] = dct
	dct = copy.deepcopy(defVals)
	dct["H"].update({"HAlign" : "center"})
	dct["V"].update({"VAlign" : "middle"})
	szDefaults[dui.dPageFrameNoTabs] = dct
	szDefaults["dPageFrameNoTabs"] = dct
	dct = copy.deepcopy(defVals)
	szDefaults[dui.dSizer] = dct
	szDefaults["dSizer"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "HAlign" : "center", "VAlign" : "middle", "ColExpand": True, "RowExpand": False})
	dct["H"].update({"Proportion" : 1, "Expand" : False, "HAlign": "center"})
	dct["V"].update({"Proportion" : 0, "Expand" : True, "VAlign": "middle"})
	szDefaults[dui.dSlider] = dct
	szDefaults["dSlider"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : False, "RowExpand": False})
	dct["H"].update({"Proportion" : 1, "Expand" : False})
	dct["V"].update({"Proportion" : 0, "Expand" : True})
	szDefaults[dui.dSpinner] = dct
	szDefaults["dSpinner"] = dct
	dct = copy.deepcopy(defVals)
	dct["H"].update({"HAlign" : "center"})
	dct["V"].update({"VAlign" : "middle"})
	szDefaults[dui.dSplitter] = dct
	szDefaults["dSplitter"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 1, "Expand" : True, "ColExpand": True, "RowExpand": False})
	dct["H"].update({"Proportion" : 1, "Expand" : False})
	dct["V"].update({"Proportion" : 0, "Expand" : True})
	szDefaults[dui.dTextBox] = dct
	szDefaults["dTextBox"] = dct
	dct = copy.deepcopy(defVals)
	dct["H"].update({"HAlign" : "center", "Proportion": 0, "Expand": False})
	dct["V"].update({"VAlign" : "middle", "Proportion": 0, "Expand": False})
	szDefaults[dui.dToggleButton] = dct
	szDefaults["dToggleButton"] = dct
	dct = copy.deepcopy(defVals)
	dct["G"].update({"Proportion" : 0, "Expand" : True, "HAlign" : "center", "VAlign" : "middle", "ColExpand": True, "RowExpand": True})
	dct["H"].update({"Proportion" : 1, "Expand" : True, "HAlign": "center"})
	dct["V"].update({"Proportion" : 1, "Expand" : True, "VAlign": "middle"})
	szDefaults[dui.dTreeView] = dct
	szDefaults["dTreeView"] = dct
	return szDefaults

_sizerDefaults = {}
_extraSizerDefaults = {}


def addSizerDefaults(defaults):
	"""Takes a dict of defaults, with the class as the key and the various defaults as
	the values. Used by external apps to customize behaviors for their own classes.
	"""
	global _extraSizerDefaults
	_extraSizerDefaults.update(defaults)


def getDefaultSizerProps(cls, szType):
	global _sizerDefaults
	global _extraSizerDefaults
	if not _sizerDefaults:
		_sizerDefaults = getSizerDefaults()
	# Add custom defaults, if any
	if _extraSizerDefaults:
		_sizerDefaults.update(_extraSizerDefaults)
		_extraSizerDefaults = {}
	typ = szType[0].upper()
	defaults = _sizerDefaults.get(cls, {})
	ret = defaults.get(typ, {})
	if not ret and isinstance(cls, basestring):
		# Sometimes the Class Designer mangles names so that they are unique
		# E.g., 'dTextBox' becomes 'dTextBox_323432'
		splitname = cls.split("_")
		if len(splitname) == 2 and splitname[1].isdigit():
			defaults = _sizerDefaults.get(splitname[0], {})
			ret = defaults.get(typ, {})
	return copy.deepcopy(ret)
