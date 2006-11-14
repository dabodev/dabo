"""These are routines that are used to work with Class Designer code that has
been separated from the design. 
"""
import re

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
	codeObjs = txt.split(codeObjectSep)[1:]
	for codeObj in codeObjs:
		cd = {}
		impt = ""
		# The first line in the code-ID, the rest is the code for
		# that object
		codeID, mthds = codeObj.split("\n", 1)
		mthdList = pat.split(mthds)
		# Element 0 is either empty or an import statement; the methods appear is
		# groups of three elements each: the 'def' line, followed by the method
		# name, followed by the method body.
		impt = mthdList[0]
		if impt:
			cd["importStatements"] = impt
		mthdList = mthdList[1:]
		while mthdList:
			cd[mthdList[1]] = "\n".join((mthdList[0], mthdList[2]))
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


