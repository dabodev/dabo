# -*- coding: utf-8 -*-
import __builtin__
import wx
import wx.stc as stc
import wx.py
from wx.py import pseudo
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dSplitForm import dSplitForm
from dabo.ui import makeDynamicProperty
from dPemMixin import dPemMixin

dabo.ui.loadUI("wx")


class _Shell(dPemMixin, wx.py.shell.Shell):
	def __init__(self, parent, properties=None, attProperties=None,
				*args, **kwargs):
		self._isConstructed = False
		self._fontSize = 10
		self._fontFace = ""
		self._baseClass = _Shell
		preClass = wx.py.shell.Shell
		dPemMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
	
	
	def _afterInit(self):
		super(_Shell, self)._afterInit()
		# Set some font defaults
		plat = wx.Platform
		if plat == "__WXGTK__":
			self.FontFace = "Monospace"
			self.FontSize = 10
		elif plat == "__WXMAC__":
			self.FontFace = "Monaco"
			self.FontSize = 12
		if plat == "__WXMSW__":
			self.FontFace = "Courier New"
			self.FontSize = 10	


	def setDefaultFont(self, fontFace, fontSize):
		# Global default styles for all languages
		self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%s,size:%d" % (fontFace, fontSize))
		self.StyleClearAll()  # Reset all to be like the default

		# Global default styles for all languages
		self.StyleSetSpec(stc.STC_STYLE_DEFAULT,
			"face:%s,size:%d" % (self._fontFace, fontSize))
		self.StyleSetSpec(stc.STC_STYLE_LINENUMBER,
			"back:#C0C0C0,face:%s,size:%d" % (self._fontFace, 8))
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
	

	def _getFontSize(self):
		return self._fontSize

	def _setFontSize(self, val):
		if self._constructed():
			self._fontSize = val
			self.setDefaultFont(self._fontFace, self._fontSize)
			self.setPyFont(self._fontFace, self._fontSize)
			self.Application.setUserSetting("shell.fontsize", self._fontSize)
		else:
			self._properties["FontSize"] = val


	def _getFontFace(self):
		return self._fontFace

	def _setFontFace(self, val):
		if self._constructed():
			self._fontFace = val
			self.setDefaultFont(self._fontFace, self._fontSize)
			self.setPyFont(self._fontFace, self._fontSize)
			self.Application.setUserSetting("shell.fontface", self._fontFace)
		else:
			self._properties["FontFace"] = val


	FontFace = property(_getFontFace, _setFontFace, None,
			_("Name of the font face used in the shell  (str)"))
	
	FontSize = property(_getFontSize, _setFontSize, None,
			_("Size of the font used in the shell  (int)"))
	



class dShell(dSplitForm):
	def _onDestroy(self, evt):
		__builtin__.raw_input = self._oldRawInput

	
	def _beforeInit(self, pre):
		# Set the sash
		self._sashPct = 0.6
		super(dShell, self)._beforeInit(pre)
		

	def _afterInit(self):
		super(dShell, self)._afterInit()

		# PyShell sets the raw_input function to a function of PyShell,
		# but doesn't set it back on destroy, resulting in errors later
		# on if something other than PyShell asks for raw_input (pdb, for
		# example).
		self._oldRawInput = __builtin__.raw_input
		self.bindEvent(dabo.dEvents.Destroy, self._onDestroy)

		splt = self.splitter
		splt.MinimumPanelSize = 80
		splt.unbindEvent()
		self.Orientation = "H"
		self.unsplit()
		self._splitState = False
		self.MainSplitter.bindEvent(dEvents.SashDoubleClick, 
				self.sashDoubleClick)
		self.MainSplitter.bindEvent(dEvents.SashPositionChanged, 
				self.sashPosChanged)
		
		cp = self.CmdPanel = self.Panel1
		op = self.OutPanel = self.Panel2
		cp.unbindEvent(dEvents.ContextMenu)
		op.unbindEvent(dEvents.ContextMenu)
		
		cp.Sizer = dabo.ui.dSizer()
		op.Sizer = dabo.ui.dSizer()
		self.shell = _Shell(self.CmdPanel)
		# Configure the shell's behavior
		self.shell.AutoCompSetIgnoreCase(True)
		self.shell.AutoCompSetAutoHide(False)	 ## don't hide when the typed string no longer matches
		self.shell.AutoCompStops(" ")  ## characters that will stop the autocomplete
		self.shell.AutoCompSetFillUps(".(")
		# This lets you go all the way back to the '.' without losing the AutoComplete
		self.shell.AutoCompSetCancelAtStart(False)
		
		cp.Sizer.append1x(self.shell)
		self.shell.Bind(wx.EVT_RIGHT_UP, self.shellRight)

		# create the output control
		outControl = dabo.ui.dEditBox(op, RegID="edtOut", 
				ReadOnly = True)
		op.Sizer.append1x(outControl)
		outControl.bindEvent(dEvents.MouseRightDown, 
				self.outputRightDown)
		
		self._stdOut = self.shell.interp.stdout
		self._stdErr = self.shell.interp.stderr
		self._pseudoOut = pseudo.PseudoFileOut(write=self.appendOut)
		self._pseudoErr = pseudo.PseudoFileOut(write=self.appendOut)
		self.SplitState = True
		
		# Make 'self' refer to the calling form, or this form if no calling form.
		if self.Parent is None:
			ns = self
		else:
			ns = self.Parent
		self.shell.interp.locals['self'] = ns

		self.Caption = _("dShell: self is %s") % ns.Name
		self.setStatusText(_("Use this shell to interact with the runtime environment"))
		self.fillMenu()
		self.shell.SetFocus()
		
	
	def appendOut(self, tx):
		ed = self.edtOut
		ed.Value += tx
		endpos = ed.GetLastPosition()
		# Either of these commands should scroll the edit box
		# to the bottom, but neither do (at least on OS X) when 
		# called directly or via callAfter().
		dabo.ui.callAfter(ed.ShowPosition, endpos)
		dabo.ui.callAfter(ed.SetSelection, endpos, endpos)


	def outputRightDown(self, evt):
		pop = dabo.ui.dMenu()
		pop.append(_("Clear"), OnHit=self.onClearOutput)
		self.showContextMenu(pop)
		evt.stop()
	
	
	def onClearOutput(self, evt):
		self.edtOut.Value = ""
	
	
	def shellRight(self, evt):
		pop = dabo.ui.dMenu()
		if self.SplitState:
			pmpt = _("Unsplit")
		else:
			pmpt = _("Split")
		pop.append(pmpt, OnHit=self.onSplitContext)
		self.showContextMenu(pop)
		evt.StopPropagation()
		

	def onSplitContext(self, evt):
		self.SplitState = (evt.EventObject.Caption == _("Split"))
		evt.stop()
		
		
	def onResize(self, evt):
		self.SashPosition = self._sashPct * self.Height
	

	def sashDoubleClick(self, evt):
		# We don't want the window to unsplit
		evt.stop()
		
		
	def sashPosChanged(self, evt):
		self._sashPct = float(self.SashPosition) / self.Height
		
		
	def fillMenu(self):
		viewMenu = self.MenuBar.getMenu(_("View"))
		if viewMenu.Children:
			viewMenu.appendSeparator()
		viewMenu.append(_("Zoom &In\tCtrl+="), OnHit=self.onViewZoomIn, 
				bmp="zoomIn", help=_("Zoom In"))
		viewMenu.append(_("&Normal Zoom\tCtrl+/"), OnHit=self.onViewZoomNormal, 
				bmp="zoomNormal", help=_("Normal Zoom"))
		viewMenu.append(_("Zoom &Out\tCtrl+-"), OnHit=self.onViewZoomOut, 
				bmp="zoomOut", help=_("Zoom Out"))
		editMenu = self.MenuBar.getMenu(_("Edit"))
		if editMenu.Children:
			editMenu.appendSeparator()
		editMenu.append(_("Clear O&utput\tCtrl+Back"), 
				OnHit=self.onClearOutput, help=_("Clear Output Window"))
		
		
	def onViewZoomIn(self, evt):
		self.shell.SetZoom(self.shell.GetZoom()+1)


	def onViewZoomNormal(self, evt):
		self.shell.SetZoom(0)


	def onViewZoomOut(self, evt):
		self.shell.SetZoom(self.shell.GetZoom()-1)


	def _getSplitState(self):
		return self._splitState

	def _setSplitState(self, val):
		if self._splitState != val:
			self._splitState = val
			if val:
				self.split()
				self.shell.interp.stdout = self._pseudoOut
				self.shell.interp.stderr = self._pseudoErr
			else:
				self.unsplit()
				self.shell.interp.stdout = self._stdOut
				self.shell.interp.stderr = self._stdErr
			

	def _getFontSize(self):
		return self.shell.FontSize

	def _setFontSize(self, val):
		if self._constructed():
			self.shell.FontSize = val
		else:
			self._properties["FontSize"] = val


	def _getFontFace(self):
		return self.shell.FontFace

	def _setFontFace(self, val):
		if self._constructed():
			self.shell.FontFace = val
		else:
			self._properties["FontFace"] = val


	FontFace = property(_getFontFace, _setFontFace, None,
			_("Name of the font face used in the shell  (str)"))
	
	FontSize = property(_getFontSize, _setFontSize, None,
			_("Size of the font used in the shell  (int)"))

	SplitState = property(_getSplitState, _setSplitState, None,
			_("""Controls whether the output is in a separate pane (default) 
			or intermixed with the commands.  (bool)"""))
			
			
	DynamicSplitState = makeDynamicProperty(SplitState)
	
		

def main():
	app = dabo.dApp(BasePrefKey="dabo.ui.dShell")
	app.MainFormClass = dShell
	app.setup()
	app.start()

if __name__ == "__main__":
	main()
