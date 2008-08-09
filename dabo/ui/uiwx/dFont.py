# -*- coding: utf-8 -*-
import wx
import decimal
import dabo
from dabo.dObject import dObject
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dFont(dObject):
	"""This class wraps the various font properties into a single object."""
	def __init__(self, properties=None, _nativeFont=None, *args, **kwargs):
		if _nativeFont is not None:
			self._nativeFont = _nativeFont
		else:
			self._nativeFont = wx.Font(dabo.settings.defaultFontSize, 
					wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, 
					wx.FONTWEIGHT_NORMAL)
		self._macNonScaledSize = 0
	
		super(dFont, self).__init__(properties=properties, *args, **kwargs)


	def _propsChanged(self):
		self.raiseEvent(dabo.dEvents.FontPropertiesChanged)

	
	def _getBold(self):
		if self._nativeFont:
			return (self._nativeFont.GetWeight() == wx.FONTWEIGHT_BOLD)
		return False

	def _setBold(self, val):
		if val:
			self._nativeFont.SetWeight(wx.FONTWEIGHT_BOLD)
		else:
			self._nativeFont.SetWeight(wx.FONTWEIGHT_NORMAL)
		self._propsChanged()


	def _getDescription(self):
		ret = self.Face + " " + str(self.Size)
		if self.Bold:
			ret += " B"
		if self.Italic:
			ret += " I"
		return ret


	def _getFace(self):
		if self._nativeFont:
			return self._nativeFont.GetFaceName()
		return ""

	def _setFace(self, val):
		if not val:
			return
		availableFonts = dabo.ui.getAvailableFonts()
		def trySetFont(val):
			if val in availableFonts:
				try:
					return self._nativeFont.SetFaceName(val)
				except AttributeError:
					return False
			return False
				
		if not trySetFont(val):
			# The font wasn't found on the user's system. Try to set it
			# automatically based on some common-case mappings.
			automatic_face = None
			if val.lower() in ("courier", "courier new", "monospace", "mono"):
				for trial in ("Courier New", "Courier", "Monaco", "Monospace", "Mono"):
					if trySetFont(trial):
						automatic_face = trial
						break
			elif val.lower() in ("arial", "helvetica", "geneva", "sans"):
				for trial in ("Arial", "Helvetica", "Geneva", "Sans Serif", "Sans"):
					if trySetFont(trial):
						automatic_face = trial
						break
			elif val.lower() in ("times", "times new roman", "Georgia", "serif"):
				for trial in ("Times New Roman", "Times", "Georgia", "Serif"):
					if trySetFont(trial):
						automatic_face = trial
						break

			if not automatic_face:
				raise dabo.dException.FontNotFoundException, _("The font '%s' doesn't exist on this system.") % val
 
		self._propsChanged()


	def _getItalic(self):
		if self._nativeFont:
			return (self._nativeFont.GetStyle() == wx.FONTSTYLE_ITALIC)
		return False

	def _setItalic(self, val):
		if val:
			self._nativeFont.SetStyle(wx.FONTSTYLE_ITALIC)
		else:
			self._nativeFont.SetStyle(wx.FONTSTYLE_NORMAL)
		self._propsChanged()


	def _getSize(self):
		ret = None
		if self._useMacFontScaling():
			ret = self._macNonScaledSize
		if not ret:
			# Could be zero if it is the first time referenced when using Mac font scaling
			if self._nativeFont:
				return self._nativeFont.GetPointSize()
			else:
				# No native font yet; return a reasonable default.
				return 9
		else:	
			return ret

	def _setSize(self, val):
		try:
			val = int(val)
		except ValueError:
			# Could be fractional. Try casting to float. If that fails,
			# let the ValueError be raised.
			val = float(val)
		if self._useMacFontScaling():
			# Make sure that the difference is less than float rounding errors.
			if abs(float(val) - float(self._macNonScaledSize)) < 0.1:
				self._macNonScaledSize = val
				val = round(val/.75, 0)
		try:
			self._nativeFont.SetPointSize(val)
		except ValueError:
			dabo.errorLog.write(_("Setting FontSize to %s failed") % val)
		self._propsChanged()


	def _useMacFontScaling(self):
		return wx.Platform == "__WXMAC__" and dabo.settings.macFontScaling


	def _getUnderline(self):
		if self._nativeFont:
			return self._nativeFont.GetUnderlined()
		return False

	def _setUnderline(self, val):
		self._nativeFont.SetUnderlined(val)
		self._propsChanged()


	Bold = property(_getBold, _setBold, None,
			_("Bold setting for this font  (bool)"))
	FontBold = Bold
	
	Description = property(_getDescription, None, None,
			_("Read-only plain text description of the font  (str)"))
	
	Face = property(_getFace, _setFace, None,
			_("Name of the font face  (str)"))
	FontFace = Face
	
	Italic = property(_getItalic, _setItalic, None,
			_("Italic setting for this font  (bool)"))
	FontItalic = Italic
	
	Size = property(_getSize, _setSize, None,
			_("Size in points for this font  (int)"))
	FontSize = Size
	
	Underline = property(_getUnderline, _setUnderline, None,
			_("Underline setting for this font  (bool)"))
	FontUnderline = Underline
