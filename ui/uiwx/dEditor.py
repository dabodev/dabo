#!/usr/bin/env python

import sys
import os
import re
import keyword
import code
import inspect
import wx
import wx.stc as stc
import wx.gizmos as gizmos
import dabo

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dControlMixin as cm
import dTimer

## testing load performance:
delay = False

## The following will eventually be properties:
autoCompListType = "user"  # 'user' or 'auto'
autoIndent = True
commentSequence = "#- "
bufferedDraw = True
edgeColumn = 79	 # if highlightCharsBeyondEdge
fontAntiAlias = True
#- fontMode = "proportional"	# 'mono' or 'proportional'
fontMode = "mono"  # 'mono' or 'proportional'
highlightCharsBeyondEdge = False
showCodeFoldingMargin = True
showEOL = False
showLineNumberMargin = True
showWhiteSpace = False
styleTimerInterval = 50  ## .5 second appears to be the best compromise
tabWidth = 4  # this doesn't seem to correspond to actual spaces
useStyleTimer = False  ## see styleTimerInterval: testing to try to improve performance.
useCallTips = True
useCodeCompletion = True
useLexer = True	 # Turn off to see the change in performance
useTabIndent = True
useTab = True

if wx.Platform == '__WXMSW__':
	monoFont = "Courier New"
	propFont = "Verdana"
	fontSize = 9
elif wx.Platform == '__WXMAC__':
	monoFont = "Monaco"
	propFont = "Verdana"
	fontSize = 12
else:
	monoFont = "Courier"
	propFont = "Helvetica"
	fontSize = 11

if fontMode == "mono":
	fontFace = monoFont
else:
	fontFace = propFont


class StyleTimer(dTimer.dTimer):
	def afterInit(self):
		StyleTimer.doDefault()
		self.bindEvent(dEvents.Hit, self.onHit)
		self.mode = "container"
		
	def onHit(self, evt):
		#self.Interval = 0
		self.stop()
		if self.mode == "python":
			self.Parent.SetLexer(stc.STC_LEX_PYTHON)
			self.mode = "container"
			self.Interval = styleTimerInterval
		else:
			self.Parent.SetLexer(stc.STC_LEX_CONTAINER)


class dEditor(stc.StyledTextCtrl, cm.dControlMixin):
	# The Editor is copied from the wxPython demo, StyledTextCtrl_2.py, 
	# and modified. Thanks to Robin Dunn and everyone that contributed to 
	# that demo to get us going!
	fold_symbols = 3

	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dEditor
		self._fileName = ""
		self._beforeInit(None)
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)

		stc.StyledTextCtrl.__init__(self, parent, -1, 
				style = wx.NO_BORDER)
		cm.dControlMixin.__init__(self, name, _explicitName=_explicitName)
		self._afterInit()
		
		self._newFileName = _("< New File >")
		self._curdir = os.getcwd()
		self._defaultsSet = False
		self._registerFunc = None
		self._unRegisterFunc = None
		# Used for parsing class and method names
		self._pat = re.compile("^[ \t]*((?:(?:class)|(?:def)) [^\(]+)\(", re.M)

		self.Bind(stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
		self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
		self.Bind(stc.EVT_STC_MODIFIED, self.OnModified)
		self.Bind(stc.EVT_STC_STYLENEEDED, self.OnStyleNeeded)
		
		if delay:
			self.bindEvent(dEvents.Idle, self.onIdle)
		else:
			self.setDefaults()
			self._defaultsSet = True

		self._syntaxColoring = True
		self.addObject(StyleTimer, "_styleTimer")
		self._styleTimer.stop()
		
		app = self.Application
		# Set the marker used for bookmarks
		self._bmkPos = 5
		self.MarkerDefine(self._bmkPos, 
				stc.STC_MARK_CIRCLE, "gray", "cyan")
		justFname = os.path.split(self._fileName)[1]
		svd = app.getUserSetting("bookmarks.%s", justFname, "{}")
		if svd:
			self._bookmarks = eval(svd)
		else:
			self._bookmarks = {}

#- 		zoom = app.getUserSetting("editor.zoom")
#- 		if zoom:
#- 			self.SetZoom(zoom)
		self._fontFace = app.getUserSetting("editor.fontface")
		self._fontSize = app.getUserSetting("editor.fontsize")
		if self._fontFace:
			dabo.ui.callAfter(self.changeFontFace, self._fontFace)
		else:
			self._fontFace = self.GetFont().GetFaceName()
		if self._fontSize:
			dabo.ui.callAfter(self.changeFontSize, self._fontSize)
		else:
			self._fontSize = self.GetFont().GetPointSize()

		if useStyleTimer:
			self._styleTimer.mode = "container"
			self._styleTimer.Interval = styleTimerInterval
			self._styleTimer.start()
		self._clearDocument()
		self.setTitle()
	
	
	def setFormCallbacks(self, funcTuple):
		self._registerFunc, self._unRegisterFunc = funcTuple


	def __del__(self):
		self._unRegisterFunc(self)
		super(dEditor, self).__del__()
	
	
	def setBookmark(self, nm, line=None):
		"""Creates a bookmark that can be referenced by the 
		identifying name that is passed. If a bookmark already
		exists for that name, the old one is deleted. The 
		bookmark is set on the current line unless a specific 
		line number is passed.
		"""
		if line is None:
			line = self.LineNumber
		if nm in self._bookmarks.keys():
			self.clearBookmark(nm)
		hnd = self.MarkerAdd(line, self._bmkPos)
		self._bookmarks[nm] = hnd
	
	
	def findBookmark(self, nm):
		"""Moves to the line for the specified bookmark. If no such
		bookmark exists, does nothing.
		"""
		try:
			foundLine = self.MarkerLineFromHandle(self._bookmarks[nm])
		except KeyError:
			# No such bookmark
			foundLine = -1
		if foundLine > -1:
			self.moveToEnd()
			# Add some breathing room above
			self.LineNumber = foundLine-3
			self.LineNumber = foundLine
	
	
	def clearBookmark(self, nm):
		"""Clears the specified bookmark. If no such bookmark 
		exists, does nothing.
		"""
		try:
			self.MarkerDeleteHandle(self._bookmarks[nm])
			del self._bookmarks[nm]
		except KeyError:
			pass


	def clearAllBookmarks(self):
		"""Removes all bookmarks."""
		self.MarkerDeleteAll(self._bmkPos)
		self._bookmarks.clear()
	
	
	def goNextBookMark(self, line=None):
		"""Moves to the next bookmark in the document. If the
		line to start searching from is not specified, searches from
		the current line. If there are no more bookmarks, nothing
		happens.
		"""
		### NOT WORKING! GOTTA FIGURE OUT THE MASK STUFF!  ###
		if line is None:
			line = self.LineNumber
		print "START LN", line
		nxtLine = self.MarkerNext(line, self._bmkPos)
		print "NEXT", nxtLine
		if nxtLine > -1:
			self.moveToEnd()
			self.LineNumber = nxtLine
		
		
	def goPrevBookMark(self, line=None):
		"""Moves to the previous bookmark in the document. If the
		line to start searching from is not specified, searches from
		the current line. If there are no more bookmarks, nothing
		happens.
		"""
		### NOT WORKING! GOTTA FIGURE OUT THE MASK STUFF!  ###
		if line is None:
			line = self.LineNumber
		print "START LN", line
		nxtLine = self.MarkerPrevious(line, self._bmkPos)
		print "PREV", nxtLine
		if nxtLine > -1:
			self.moveToEnd()
			self.LineNumber = nxtLine
		
	
	def getCurrentLineBookmark(self):
		"""Returns the name of the bookmark for the current
		line, or None if this line is not bookmarked.
		"""
		ret = None
		curr = self.LineNumber
		for nm, hnd in self._bookmarks.items():
			if self.MarkerLineFromHandle(hnd) == curr:
				ret = nm
				break
		return ret
		
		
	def getBookmarkList(self):
		"""Returns a list of all current bookmark names."""
		return self._bookmarks.keys()
		
		
	def getFunctionList(self, sorted=False):
		"""Returns a list of all 'class' and 'def' statements, along
		with their starting positions in the text.
		"""
		it = self._pat.finditer(self.GetText())
		ret = [(m.groups()[0], m.start()) for m in it]
		if sorted:
			cls = ""
			dct = {}
			mthdList = []
			clsList = []
			for itms in ret:
				itm = itms[0]
				if itm.startswith("class"):
					if mthdList:
						dct[cls] = mthdList
					cls = itm
					clsList.append(itm)
					mthdList = [itms]
				else:
					mthdList.append(itms)
			if mthdList:
				dct[cls] = mthdList
			# We need to sort by class, and then within class, by method
			ret = []
			classes = dct.keys()
			classes.sort()
			for cls in classes:
				mthds = dct[cls]
				mthds.sort()
				ret += mthds
		return ret		
		

	def getMarginWidth(self):
		"""Returns the width of the non-editing area along the left side."""
		ret = 0
		for ii in range(5):
			ret += self.GetMarginWidth(ii)
		return ret
		
		
	def OnSBScroll(self, evt):
		# redirect the scroll events from the dyn_sash's scrollbars to the STC
		self.GetEventHandler().ProcessEvent(evt)
		
	
	def OnSBFocus(self, evt):
		# when the scrollbar gets the focus move it back to the STC
		self.SetFocus()
	

	def OnStyleNeeded(self, evt):
		if not self._syntaxColoring:
			return
		self._styleTimer.mode = "python"
		self._styleTimer.Interval = styleTimerInterval
		self._styleTimer.start()
		
		
	def onIdle(self, evt):
		if not self._defaultsSet:
			self.setDefaults()
			self._defaultsSet = True
			

	def setDocumentDefaults(self):
		self.SetTabWidth(tabWidth)
		self.SetIndent(tabWidth)
		

	def setDefaults(self):
		self.UsePopUp(0)
		self.SetUseTabs(useTab)
		self.SetTabIndents(useTabIndent)

		## Autocomplete settings:
		self.AutoCompSetIgnoreCase(True)
		self.AutoCompSetAutoHide(False)	 ## don't hide when the typed string no longer matches
		#self.AutoCompStops(".(")  ## characters that will stop the autocomplete
		self.AutoCompSetFillUps(".(")

		if useLexer:
			self.SetLexer(stc.STC_LEX_PYTHON)
			self.SetKeyWords(0, " ".join(keyword.kwlist))
			
			## Note: "tab.timmy.whinge.level" is a setting that determines how to
			## indicate bad indentation.
			## It shows up as a blue underscore when the indentation is:
			##	   * 0 = ignore (default)
			##	   * 1 = inconsistent
			##	   * 2 = mixed spaces/tabs
			##	   * 3 = spaces are bad
			##	   * 4 = tabs are bad 
			self.SetProperty("tab.timmy.whinge.level", "1")
		self.SetMargins(0,0)

		self.SetViewWhiteSpace(showWhiteSpace)
		self.SetBufferedDraw(bufferedDraw)
		self.SetViewEOL(showEOL)
		self.SetUseAntiAliasing(fontAntiAlias)

		## Seems that eolmode is CRLF on Mac by default... explicitly set it!
		if wx.Platform == "__WXMSW__":
			self.SetEOLMode(stc.STC_EOL_CRLF)
		else:
			self.SetEOLMode(stc.STC_EOL_LF)

		if highlightCharsBeyondEdge:
			self.SetEdgeMode(stc.STC_EDGE_BACKGROUND)
			self.SetEdgeColumn(edgeColumn)

		if showLineNumberMargin:
			self.SetMarginType(1, stc.STC_MARGIN_NUMBER)
			self.SetMarginSensitive(1, True)
			self.SetMarginWidth(1, 36)

		if showCodeFoldingMargin:
			# Setup a margin to hold fold markers
			self.SetProperty("fold", "1")
			self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
			self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
			self.SetMarginSensitive(2, True)
			self.SetMarginWidth(2, 12)

			if self.fold_symbols == 0:
				# Arrow pointing right for contracted folders,
				# arrow pointing down for expanded
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,
					stc.STC_MARK_ARROWDOWN, "black", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDER,
					stc.STC_MARK_ARROW, "black", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,
					stc.STC_MARK_EMPTY, "black", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,
					stc.STC_MARK_EMPTY, "black", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,
					stc.STC_MARK_EMPTY, "white", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID,
					stc.STC_MARK_EMPTY, "white", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL,
					stc.STC_MARK_EMPTY, "white", "black");

			elif self.fold_symbols == 1:
				# Plus for contracted folders, minus for expanded
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,
					stc.STC_MARK_MINUS, "white", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDER,
					stc.STC_MARK_PLUS,	"white", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,
					stc.STC_MARK_EMPTY, "white", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,
					stc.STC_MARK_EMPTY, "white", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,
					stc.STC_MARK_EMPTY, "white", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID,
					stc.STC_MARK_EMPTY, "white", "black");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL,
					stc.STC_MARK_EMPTY, "white", "black");

			elif self.fold_symbols == 2:
				# Like a flattened tree control using circular headers and curved joins
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,
					stc.STC_MARK_CIRCLEMINUS, "white", "#404040");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDER,
					stc.STC_MARK_CIRCLEPLUS, "white", "#404040");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,
					stc.STC_MARK_VLINE, "white", "#404040");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,
					stc.STC_MARK_LCORNERCURVE, "white", "#404040");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,
					stc.STC_MARK_CIRCLEPLUSCONNECTED, "white", "#404040");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID,
					stc.STC_MARK_CIRCLEMINUSCONNECTED, "white", "#404040");
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL,
					stc.STC_MARK_TCORNERCURVE, "white", "#404040");

			elif self.fold_symbols == 3:
				# Like a flattened tree control using square headers
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,
					stc.STC_MARK_BOXMINUS, "white", "#808080")
				self.MarkerDefine(stc.STC_MARKNUM_FOLDER,
					stc.STC_MARK_BOXPLUS, "white", "#808080")
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,
					stc.STC_MARK_VLINE, "white", "#808080")
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,
					stc.STC_MARK_LCORNER, "white", "#808080")
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,
					stc.STC_MARK_BOXPLUSCONNECTED, "white", "#808080")
				self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID,
					stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
				self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL,
					stc.STC_MARK_TCORNER, "white", "#808080")

		# Make some styles,	 The lexer defines what each style is used for, we
		# just have to define what each style looks like.  This set is adapted from
		# Scintilla sample property files.
		self.setDefaultFont(fontFace, fontSize)
		# Python styles
		self.setPyFont(fontFace, fontSize)

		self.SetCaretForeground("BLUE")

		# Register some images for use in the AutoComplete box.
		self.RegisterImage(1, dabo.ui.strToBmp("daboIcon016"))
		self.RegisterImage(2, dabo.ui.strToBmp("property"))	#, setMask=False))
		self.RegisterImage(3, dabo.ui.strToBmp("event"))		#, setMask=False))
		self.RegisterImage(4, dabo.ui.strToBmp("method"))		#, setMask=False))
		self.RegisterImage(5, dabo.ui.strToBmp("class"))		#, setMask=False))

		self.CallTipSetBackground("yellow")
		

	def changeFontFace(self, fontFace):
		self._fontFace = fontFace
		self.setDefaultFont(self._fontFace, self._fontSize)
		self.setPyFont(self._fontFace, self._fontSize)
		self.Application.setUserSetting("editor.fontface", self._fontFace)
		
	
	def changeFontSize(self, fontSize):
		self._fontSize = fontSize
		self.setDefaultFont(self._fontFace, self._fontSize)
		self.setPyFont(self._fontFace, self._fontSize)
		self.Application.setUserSetting("editor.fontsize", self._fontSize)
		
		
	def setDefaultFont(self, fontFace, fontSize):
		# Global default styles for all languages
		self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%s,size:%d" % (fontFace, fontSize))
		self.StyleClearAll()  # Reset all to be like the default

		# Global default styles for all languages
		self.StyleSetSpec(stc.STC_STYLE_DEFAULT,
			"face:%s,size:%d" % (propFont, fontSize))
		self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,
			"back:#C0C0C0,face:%s,size:%d" % (propFont, 8))
		self.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR,
			"face:%s" % fontFace)
		self.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,
			"fore:#000000,back:#00FF00,bold")
		self.StyleSetSpec(stc.STC_STYLE_BRACEBAD,
			"fore:#000000,back:#FF0000,bold")


	def setPyFont(self, fontFace, fontSize):
		# Python-specific styles
		self.StyleSetSpec(stc.STC_P_DEFAULT,
			"fore:#000000,face:%s,size:%d" % (fontFace, fontSize))
		# Comments
		self.StyleSetSpec(stc.STC_P_COMMENTLINE,
			"fore:#007F00,face:%s,size:%d,italic" % (fontFace, fontSize))
		# Number
		self.StyleSetSpec(stc.STC_P_NUMBER,
			"fore:#007F7F,size:%d" % fontSize)
		# String
		self.StyleSetSpec(stc.STC_P_STRING,
			"fore:#7F007F,face:%s,size:%d" % (fontFace, fontSize))
		# Single quoted string
		self.StyleSetSpec(stc.STC_P_CHARACTER,
			"fore:#7F007F,face:%s,size:%d" % (fontFace, fontSize))
		# Keyword
		self.StyleSetSpec(stc.STC_P_WORD,
			"fore:#00007F,bold,size:%d" % fontSize)
		# Triple quotes
		self.StyleSetSpec(stc.STC_P_TRIPLE,
			"fore:#7F0000,size:%d,italic" % fontSize)
		# Triple double quotes
		self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE,
			"fore:#7F0000,size:%d,italic" % fontSize)
		# Class name definition
		self.StyleSetSpec(stc.STC_P_CLASSNAME,
			"fore:#0000FF,bold,underline,size:%d" % fontSize)
		# Function or method name definition
		self.StyleSetSpec(stc.STC_P_DEFNAME,
			"fore:#007F7F,bold,size:%d" % fontSize)
		# Operators
		self.StyleSetSpec(stc.STC_P_OPERATOR,
			"bold,size:%d" % fontSize)
		# Identifiers
		self.StyleSetSpec(stc.STC_P_IDENTIFIER,
			"fore:#000000,face:%s,size:%d" % (fontFace, fontSize))
		# Comment-blocks
		self.StyleSetSpec(stc.STC_P_COMMENTBLOCK,
			"fore:#7F7F7F,size:%d,italic" % fontSize)
		# End of line where string is not closed
		self.StyleSetSpec(stc.STC_P_STRINGEOL,
			"fore:#000000,face:%s,back:#E0C0E0,eol,size:%d" % (fontFace, fontSize))





		
	def onCommentLine(self, evt):
		sel = self.GetSelection()
		begLine = self.LineFromPosition(sel[0])
		endLine = self.LineFromPosition(sel[1]-1)

		self.BeginUndoAction()
		for line in range(begLine, endLine+1):
			pos = self.PositionFromLine(line)
			self.InsertText(pos, commentSequence)
		self.EndUndoAction()

		self.SetSelection(self.PositionFromLine(begLine), 
			self.PositionFromLine(endLine+1))
		

	def onUncommentLine(self, evt):
		sel = self.GetSelection()
		begLine = self.LineFromPosition(sel[0])
		endLine = self.LineFromPosition(sel[1]-1)

		self.BeginUndoAction()
		for line in range(begLine, endLine+1):
			pos = self.PositionFromLine(line)
			self.SetTargetStart(pos)
			self.SetTargetEnd(pos + len(commentSequence))
			if self.SearchInTarget(commentSequence) >= 0:
				self.ReplaceTarget("")
		self.EndUndoAction()

		self.SetSelection(self.PositionFromLine(begLine), 
			self.PositionFromLine(endLine+1))
	
	
	def onKeyDown(self, evt):
		keyCode = evt.EventData["keyCode"]
		if keyCode == wx.WXK_RETURN and autoIndent and not self.AutoCompActive():
			## Insert auto indentation as necessary. This code was adapted from
			## PythonCard - Thanks Kevin for suggesting I take a look at it.
			evt.Continue = False
			self.CmdKeyExecute(stc.STC_CMD_NEWLINE)
			line = self.LineNumber - 1
			txt = self.GetLine(line).rstrip()
			
			currIndent = self.GetIndent()
			if currIndent == 0:
				indentLevel = 0
			else:
				indentLevel = self.GetLineIndentation(line) / self.GetIndent()
			
			# First, indent to the current level of indent:
			if self.GetUseTabs():
				padchar = "\t"
			else:
				padchar = " "
			padding = padchar * indentLevel
			pos = self.GetCurrentPos()
			
			self.InsertText(pos, padding)
			pos = pos + len(padding)
			
			# Next, indent another level if last line ended with ":"
			if len(txt) > 0 and txt[-1] == ':':
				padding = padchar
				self.InsertText(pos, padding)
				pos = pos + len(padding)
			self.SetCurrentPos(pos)
			self.SetSelection(pos, pos)


	def onKeyChar(self, evt):
		keyChar = evt.EventData["keyChar"]
		self._insertChar = ""
		
		if keyChar == "(" and self.AutoCompActive():
			self._insertChar = "("
		elif keyChar == "(" and useCallTips and not self.AutoCompActive():
			self.callTip()
		elif keyChar == "." and useCodeCompletion:
			if self.AutoCompActive():
				# don't process the autocomplete, as it is 
				# already being processed. However, set the flag
				# so that onListSelection() knows to call 
				# autocomplete on the new item:
				self._insertChar = "."
			else:
				self._posBeforeCompList = self.GetCurrentPos() + 1
				self.codeComplete()


	def onListSelection(self, evt):
		txt = evt.GetText()
		if len(txt) > 0:
			insertChar = self._insertChar
			pos = self._posBeforeCompList
			self.SetTargetStart(pos)
			self.SetTargetEnd(self.GetCurrentPos())
			self.ReplaceTarget("")

			self.InsertText(pos, txt)
			self.GotoPos(pos + len(txt))

			if insertChar == "(":
				wx.CallAfter(self.callTip)
			elif insertChar == ".":
				self._posBeforeCompList = self.GetCurrentPos() + 1
				self.codeComplete()
			self._insertChar = ""
			
			
	def setInactive(self):
		"""Hides the auto-completion popup if one is open."""
		if self.AutoCompActive():
			self.AutoCompCancel()
			
		
	def toggleSyntaxColoring(self):
		"""Right now, just toggles between Python and none. In the future,
		we will need to save the current lexer and toggle between that and
		none.
		"""
		self._syntaxColoring = not self._syntaxColoring
		if self._syntaxColoring:
			self.setSyntaxColoring("Python")
		else:
			self.setSyntaxColoring(None)
	
	
	def setSyntaxColoring(self, typ=None):
		"""Sets the appropriate lexer for syntax coloring."""
		if typ is None:
			testTyp = "none"
		else:
			testTyp = typ.strip().lower()
		if testTyp == "python":
			self.SetLexer(stc.STC_LEX_PYTHON)		
			self.Colourise(-1, -1)
		elif testTyp == "none":
			self.ClearDocumentStyle()
			self.SetLexer(stc.STC_LEX_CONTAINER)		
		else:
			dabo.errorLog.write(_("Invalid syntax coloring type specified: %s") % typ)
	
	
	def toggleWordWrap(self):
		self.WordWrap = not self.WordWrap

		
	def OnModified(self, evt):
		if not self._syntaxColoring:
			return
		evt.Skip()
		self.setTitle()


	def OnUpdateUI(self, evt):
		if not self._syntaxColoring:
			return
		# check for matching braces
		braceAtCaret = -1
		braceOpposite = -1
		charBefore = None
		caretPos = self.GetCurrentPos()

		if caretPos > 0:
			charBefore = self.GetCharAt(caretPos - 1)
			styleBefore = self.GetStyleAt(caretPos - 1)

		# check before
		if charBefore and chr(charBefore) in "[]{}()" and styleBefore == stc.STC_P_OPERATOR:
			braceAtCaret = caretPos - 1

		# check after
		if braceAtCaret < 0:
			charAfter = self.GetCharAt(caretPos)
			styleAfter = self.GetStyleAt(caretPos)

			if charAfter and chr(charAfter) in "[]{}()" and styleAfter == stc.STC_P_OPERATOR:
				braceAtCaret = caretPos

		if braceAtCaret >= 0:
			braceOpposite = self.BraceMatch(braceAtCaret)

		if braceAtCaret != -1  and braceOpposite == -1:
			self.BraceBadLight(braceAtCaret)
		else:
			self.BraceHighlight(braceAtCaret, braceOpposite)
			#pt = self.PointFromPosition(braceOpposite)
			#self.Refresh(True, wxRect(pt.x, pt.y, 5,5))
			#print pt
			#self.Refresh(False)
			

	def OnMarginClick(self, evt):
		mg = evt.GetMargin()
		lineClicked = self.LineFromPosition(evt.GetPosition())
		if mg == 2:
			# Folding margin; fold and unfold as needed
			if evt.GetShift() and evt.GetControl():
				self.FoldAll()
			else:

				if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
					if evt.GetShift():
						self.SetFoldExpanded(lineClicked, True)
						self.Expand(lineClicked, True, True, 1)
					elif evt.GetControl():
						if self.GetFoldExpanded(lineClicked):
							self.SetFoldExpanded(lineClicked, False)
							self.Expand(lineClicked, False, True, 0)
						else:
							self.SetFoldExpanded(lineClicked, True)
							self.Expand(lineClicked, True, True, 100)
					else:
						self.ToggleFold(lineClicked)
		elif mg == 1:
			# Line number margin; hilite the line
			ln = self.LineFromPosition(evt.GetPosition())
			start = self.PositionFromLine(ln)
			end = self.PositionFromLine(ln+1)
			if evt.GetShift():
				# Need to extend from the current position
				currStart = self.GetSelectionStart()
				currEnd = self.GetSelectionEnd()
				start = min(start, currStart)
				end = max(end, currEnd)
			self.SetSelection(start, end)
				
	
	def callTip(self):
		"""Present the call tip for the current object, if any."""
		runtimeObjName = self._getRuntimeObjectName()
		obj = self._getRuntimeObject(runtimeObjName)
		pos = self.GetCurrentPos()

		if obj is not None:
			try:
				args = inspect.getargspec(obj)
				try:
					sarg = args[0][0]
				except IndexError:
					sarg = None
				if sarg is not None and sarg == "self":
					del args[0][0]
				args = inspect.formatargspec(args[0], args[1], args[2], args[3])
			except:
				args = ""

			try:
				if inspect.ismethod(obj):
					funcType = "Method"
				elif inspect.isfunction(obj):
					funcType = "Function"
				elif inspect.isclass(obj):
					funcType = "Class"
				elif inspect.ismodule(obj):
					funcType = "Module"
				elif inspect.isbuiltin():
					funcType = "Built-In"
				else:
					funcType = ""
			except:
				funcType = ""

			doc = ""
			try:
				docLines = obj.__doc__.splitlines()
				for line in docLines:
					doc += line.strip() + "\n"	 ## must be \n on all platforms
				doc = doc.strip()  ## Remove trailing blank line
			except:
				pass

			try:
				name = obj.__name__
			except:
				name = ""
				
			shortDoc = "%s %s%s" % (funcType,
				name,
				args)

			longDoc = "%s\n\n%s" % (shortDoc, doc)
			
			self.CallTipShow(pos, shortDoc)
			# Highlight the object name:
			self.CallTipSetHighlight(len(funcType) + 1, 
				len(funcType) + len(name) + 1)

			# Let someone else display the complete documentation:
			self.raiseEvent(dEvents.DocumentationHint, 
				shortDoc=shortDoc, longDoc=longDoc, object=obj)
				

	def codeComplete(self):
		"""Display the code completion list for the current object, if any."""
		# Get the name of object the user is pressing "." after.
		# This could be 'self', 'dabo', or a reference to any object
		# previously defined.
		obj = self._getRuntimeObject(self._getRuntimeObjectName())
		if obj is not None:
			kw = []
			pos = self.GetCurrentPos()
			for k in dir(obj):
				if k[0] != "_":
					kw.append(k)
					
			# Sort upper case:
			kw.sort(lambda a,b: cmp(a.upper(), b.upper()))

			# Images are specified with a appended "?type"
			for i in range(len(kw)):
				obj_ = eval("obj.%s" % kw[i])
				if type(obj_) == type(property()):
					kw[i] = kw[i] + "?2"
				elif inspect.isfunction(obj_) or inspect.ismethod(obj_):
					kw[i] = kw[i] + "?4"
				elif inspect.isclass(obj_) and issubclass(obj_, dEvents.Event):
					kw[i] = kw[i] + "?3"
				elif inspect.isclass(obj_):
					kw[i] = kw[i] + "?5"
				else:
					# Punt with the Dabo icon:
					kw[i] = kw[i] + "?1"
					
			if autoCompListType == "user":
				self.Bind(stc.EVT_STC_USERLISTSELECTION, self.onListSelection)
				wx.CallAfter(self.UserListShow, 1, " ".join(kw))
			else:
				wx.CallAfter(self.AutoCompShow,0, " ".join(kw))


	def FoldAll(self):
		lineCount = self.GetLineCount()
		expanding = True

		# find out if we are folding or unfolding
		for lineNum in range(lineCount):
			if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
				expanding = not self.GetFoldExpanded(lineNum)
				break;

		lineNum = 0
		while lineNum < lineCount:
			level = self.GetFoldLevel(lineNum)
			if level & stc.STC_FOLDLEVELHEADERFLAG and \
			(level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:
				if expanding:
					self.SetFoldExpanded(lineNum, True)
					lineNum = self.Expand(lineNum, True)
					lineNum = lineNum - 1
				else:
					lastChild = self.GetLastChild(lineNum, -1)
					self.SetFoldExpanded(lineNum, False)

					if lastChild > lineNum:
						self.HideLines(lineNum+1, lastChild)
			lineNum = lineNum + 1


	def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
		lastChild = self.GetLastChild(line, level)
		line = line + 1
		while line <= lastChild:
			if force:
				if visLevels > 0:
					self.Lines(line, line)
				else:
					self.HideLines(line, line)
			else:
				if doExpand:
					self.ShowLines(line, line)

			if level == -1:
				level = self.GetFoldLevel(line)

			if level & stc.STC_FOLDLEVELHEADERFLAG:
				if force:
					if visLevels > 1:
						self.SetFoldExpanded(line, True)
					else:
						self.SetFoldExpanded(line, False)

					line = self.Expand(line, doExpand, force, visLevels-1)
				else:
					if doExpand and self.GetFoldExpanded(line):
						line = self.Expand(line, True, force, visLevels-1)
					else:
						line = self.Expand(line, False, force, visLevels-1)
			else:
				line = line + 1;
		return line


	def promptToSave(self):
		try:
			fname = self._fileName
		except:
			fname = None
		if fname is None:
			s = "Do you want to save your changes?"
		else:
			s = "Do you want to save your changes to file '%s'?" % self._fileName
		return dabo.ui.areYouSure(s)

		
	def promptForFileName(self, prompt="Select a file", saveAs=False,
			path=None):
		"""Prompt the user for a file name."""
		if path is None:
			try:
				drct = self._curdir
			except:
				drct = ""
		else:
			drct = path
		
		if saveAs:
			func = dabo.ui.getSaveAs
		else:
			func = dabo.ui.getFile
		fname = func("py", "*", message=prompt, defaultPath=drct)
		return fname
	
		
	def promptForSaveAs(self):
		"""Prompt user for the filename to save the file as.
		
		If the file exists, confirm with the user that they really want to
		overwrite.
		"""
		while True:
			fname = self.promptForFileName(prompt="Save As", saveAs=True)
			if fname is None:
				break
			if os.path.exists(fname):
				r = dabo.ui.areYouSure("File '%s' already exists. "
					"Do you want to overwrite it?" % fname, defaultNo=True)
				if r == None:
					# user canceled.
					fname = None
					break
				elif r == False:
					# let user pick another file
					pass
				else:
					# User chose to overwrite fname
					break
			else:
				break
		return fname


	def saveFile(self, fname=None):
		if self._curdir:
			os.chdir(self._curdir)
		if fname == None:
			try:
				fname = self._fileName
			except:
				fname = self._newFileName
		
		if fname == self._newFileName:
			# We are being asked to save a new file that doesn't exist on disk yet.
			fname = self.promptForSaveAs()
			if fname is None:
				# user canceled in the prompt: don't continue
				return None
		
		open(fname, "wb").write(self.GetText())
		# set self._fileName, in case it was changed with a Save As
		self._fileName = fname
		self._clearDocument(clearText=False)

		# Save the bookmarks
		app = self.Application
		justFname = os.path.split(fname)[1]
		base = ".".join(("bookmark", justFname))
		# Clear any existing settings.
		app.deleteAllUserSettings(base)
		for nm, hnd in self._bookmarks.items():
			ln = self.MarkerLineFromHandle(hnd)
			setName = ".".join((base, nm))
			app.setUserSetting(setName, ln)
		# Save the appearance settings
		app.setUserSetting("editor.fontsize", self._fontSize)
		app.setUserSetting("editor.fontface", self._fontFace)
		
		
	def checkChangesAndContinue(self):
		"""Check to see if changes need to be saved, and if so prompt the user.
		
		Return False if saves were needed but not made.
		"""
		ret = True
		if self.GetModify():
			r = self.promptToSave()
			if r == None:
				# user canceled the prompt.
				ret = False
			elif r == True:
				# user wants changes saved.
				self.saveFile()
			else:
				# user doesn't want changes saved.
				pass
		return ret
		
		
	def _clearDocument(self, clearText=True):
		"""Do everything needed to start the doc as if new."""
		if clearText:
			self.SetText("")
		self.SetSavePoint()
		self.EmptyUndoBuffer()
		self.setTitle()
		self.setDocumentDefaults()

		
	def newFile(self):
		"""Create a new file and edit it."""
		if self.checkChangesAndContinue():
			self._fileName = self._newFileName
			self._curdir = os.getcwd()
			self._clearDocument()
			return True
		else:
			return False
	
	
	def openFile(self, fileSpec=None):
		"""Open a new file and edit it."""
		if self.checkChangesAndContinue():
			if fileSpec is None:
				fileSpec = self.promptForFileName("Open")
				if fileSpec is None:
					return False
			try:
				f = open(fileSpec, "rb")
				text = f.read()
				f.close()
			except:
				if dabo.ui.areYouSure("File '%s' does not exist."
						" Would you like to create it?" % fileSpec):
					text = ""
				else:
					return False
			self._fileName = fileSpec
			self._curdir = os.path.split(fileSpec)[0]
			self.SetText(text)
			self._clearDocument(clearText=False)
			ret = True
		else:
			ret = False
		
		# Restore the bookmarks
		app = self.Application
		fname = os.path.split(fileSpec)[1]
		keyspec = ".".join(("bookmark", fname)).lower()
		keys = app.getUserSettingKeys(keyspec)
		for key in keys:
			val = app.getUserSetting(".".join((keyspec, key)))
			self.setBookmark(key, val)
		# Restore the appearance
		self._fontFace = app.getUserSetting("editor.fontface")
		self._fontSize = app.getUserSetting("editor.fontsize")
		if self._fontFace:
			dabo.ui.callAfter(self.changeFontFace, self._fontFace)
		else:
			self._fontFace = self.GetFont().GetFaceName()
		if self._fontSize:
			dabo.ui.callAfter(self.changeFontSize, self._fontSize)
		else:
			self._fontSize = self.GetFont().GetPointSize()
		return ret


	def setTitle(self):
		"""Set the title of the editor"""
		try:
			_oldTitle = self._title
		except AttributeError:
			_oldTitle = ""
		try:
			fileName = os.path.split(self._fileName)
			fileName = fileName[len(fileName)-1]
		except AttributeError:
			fileName = ""
		if not fileName:
			fileName = self._newFileName
			
		if self.GetModify():
			modChar = "*"
		else:
			modChar = ""
		self._title = "%s %s" % (fileName, modChar)

		if self._title != _oldTitle:
			self.raiseEvent(dEvents.TitleChanged)
			

	def increaseTextSize(self, pts=1):
		self.ZoomLevel += pts
		
		
	def decreaseTextSize(self, pts=1):
		self.ZoomLevel -= pts
		
		
	def restoreTextSize(self):
		self.ZoomLevel = 0
	
	
	def moveToBeginning(self):
		self.SetSelection(0, 0)
		self.EnsureCaretVisible()
		
		
	def moveToEnd(self):
		self.SetSelection(-1, -1)
		self.EnsureCaretVisible()
		
		
	def _getRuntimeObjectName(self):
		"""Go backwards from the current position and get the runtime object name
		that the user is currently editing. For example, if they entered a '.' after
		'self', the runtime object name would be 'self'.
		"""
		end = self.GetCurrentPos()
		cur = end
		text = []
		while True:
			if cur < 1:
				break
			char = self.GetTextRange(cur-1, cur)
			if cur == end and char in (".", "("):
				# skip the char
				pass
			else:
				if ord(char) in (10,13,32,27,20) or char in (
					"()!@^%&*+="):
					break
				text.append(char)
			cur -= 1
		text.reverse()
		text = ''.join(text).strip()
		return text


	def _makeContainingClassIntoSelf(self):
		"""Make self refer to the class.
		
		For instance, in the following snippet:
			class MyClass(object):
				pass
				
		self would get bound to MyClass. This is to simulate the 
		runtime environment, for the purpose of getting auto-completion.
		"""
		classdef = None
		args = []
		for line in range(self.LineNumber - 1, -1, -1):
			text = self.GetLine(line).strip()
			if text[0:6] == "class ":
				# Now move forward, to get the entire classdef
				args = ""
				for line in range(line, self.LineNumber):
					text = self.GetLine(line).strip()
					if len(args) == 0 and "(" in text:
						args = text[text.index("("):]
						if "):" in args:
							args = args[0:args.index("):")]
							break
					if len(args) > 0 and "):" in text:
						args += text[0:text.index("):")]
						break
				# get rid of prepended (
				args = args[1:]
				break
		if args:
			classdef = "class self(%s): pass" % args
			exec classdef in self._namespaces

		
	def _getRuntimeObject(self, runtimeObjectName):
		"""Given a runtimeObjectName, get the object.

		For example, "self" should return the class object that self would
		be an instance of at runtime.
		"""
		# Short-circuit return if the objname is empty:
		if len(runtimeObjectName.strip()) == 0:
			return None
		self._fillNamespaces()
		s = runtimeObjectName.split(".")
		outerObjectName = s[0].strip()
		if len(outerObjectName) == 0:
			return None

		if outerObjectName == "self":
			## This is a HACK, but I don't see another way. Basically, if the 
			## object name is "self", we are going to mangle it to be the class
			## that at runtime self is an instance of. Then, the object will
			## exist in the _namespaces and hence we'll get autocompletion for 
			## it. --pkm 9/20/04
			self._makeContainingClassIntoSelf()
		# Different editor usages may require additional namespace
		# hacks, such as the above. This is a hook for adding such hacks.
		self._namespaceHacks()
		try:
			o = self._namespaces[outerObjectName]
		except KeyError:
			o = None
		if o is not None:
			innerObjectNames = '.'.join(s[1:])
			if len(innerObjectNames) > 0:
				try:
					o = eval("o.%s" % innerObjectNames)
				except:
					o = None
		return o
	
	
	def _namespaceHacks(self):
		"""Hook method for any additional namespace hacks"""
		pass
		
	
	def _fillNamespaces(self):
		"""Get the names that will exist at runtime into the _namespaces dict."""
		self._namespaces = {}
		# Execute the script line-by-line, into self._namespaces.
		# Ignore any errors. Note: if this editor gets slow, this
		# is likely the reason. It needs to be line by line, otherwise
		# if there are any errors the entire script will fail.

		# This whole process is really unsafe... the user code could, for
		# example, change the current working directory or some other "global"
		# effect.
		
		# Only execute the script up to the current line to save
		# unnecessary cycles.

		# Need to save and restore sys.stderr and sys.stdout, as
		# code.InteractiveConsole sends output there, cluttering up
		# my terminal during debug. Also made a subclass to override
		# the write() method for the same reason.
		stdErr, stdOut = sys.stderr, sys.stdout
		sys.stderr, sys.stdout = None, None
		
		class IC(code.InteractiveConsole):
			def write(self, string):
				pass
			
		ic = IC(self._namespaces)
		for lineNum in range(self.LineNumber + 1):
			line = self.GetLine(lineNum).rstrip()
			ic.push(line)
		sys.stderr, sys.stdout = stdErr, stdOut
		

	def _getFileName(self):
		return os.path.split(self._fileName)[1]


	def _getFilePath(self):
		return self._fileName


	def _getLineNumber(self):
		return self.GetCurrentLine()

	def _setLineNumber(self, val):
		self.GotoLine(val)


	def _getLineCount(self):
		return self.GetLineCount()


	def _getModified(self):
		return self.GetModify()


	def _getText(self):
		return self.GetText()

	def _setText(self, val):
		self.SetText(val)


	def _getWordWrap(self):
		return self.GetWrapMode()

	def _setWordWrap(self, val):
		self.SetWrapMode(val)


	def _getZoomLevel(self):
		return self.GetZoom()

	def _setZoomLevel(self, val):
		self.SetZoom(val)


	FileName = property(_getFileName, None, None,
			_("Name of the file being edited (without path info)  (str)"))
	
	FilePath = property(_getFilePath, None, None,
			_("Full path of the file being edited  (str)"))
	
	LineNumber = property(_getLineNumber, _setLineNumber, None,
			_("Returns the current line number being edited  (int)"))
	
	LineCount = property(_getLineCount, None, None,
			_("Total number of lines in the document  (int)"))
	
	Modified = property(_getModified, None, None,
			_("Has the content of this editor been modified?  (bool)"))
	
	Text = property(_getText, _setText, None,
			_("Current contents of the editor  (str)"))
	
	WordWrap = property(_getWordWrap, _setWordWrap, None,
			_("""Controls whether text lines that are wider than the window
			are soft-wrapped or clipped. (bool)"""))
	
	ZoomLevel = property(_getZoomLevel, _setZoomLevel, None,
			_("Point increase/decrease from normal viewing size  (int)"))
	
	
	
class _dEditor_test(dEditor): pass

if __name__ == '__main__':
	import test
	test.Test().runTest(_dEditor_test)
