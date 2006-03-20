import wx
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
	
		super(dFont, self).__init__(properties=properties, *args, **kwargs)


	def _propsChanged(self):
		self.raiseEvent(dabo.dEvents.FontPropertiesChanged)

	
	def _getBold(self):
		return (self._nativeFont.GetWeight() == wx.FONTWEIGHT_BOLD)

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
		return self._nativeFont.GetFaceName()

	def _setFace(self, val):
		self._nativeFont.SetFaceName(val)
		self._propsChanged()


	def _getItalic(self):
		return (self._nativeFont.GetStyle() == wx.FONTSTYLE_ITALIC)

	def _setItalic(self, val):
		if val:
			self._nativeFont.SetStyle(wx.FONTSTYLE_ITALIC)
		else:
			self._nativeFont.SetStyle(wx.FONTSTYLE_NORMAL)
		self._propsChanged()


	def _getSize(self):
		return self._nativeFont.GetPointSize()

	def _setSize(self, val):
		self._nativeFont.SetPointSize(val)
		self._propsChanged()


	def _getUnderline(self):
		return self._nativeFont.GetUnderlined()

	def _setUnderline(self, val):
		self._nativeFont.SetUnderlined(val)
		self._propsChanged()


	Bold = property(_getBold, _setBold, None,
			_("Bold setting for this font  (bool)"))
	
	Description = property(_getDescription, None, None,
			_("Read-only plain text description of the font  (str)"))
	
	Face = property(_getFace, _setFace, None,
			_("Name of the font face  (str)"))
	
	Italic = property(_getItalic, _setItalic, None,
			_("Italic setting for this font  (bool)"))
	
	Size = property(_getSize, _setSize, None,
			_("Size in points for this font  (int)"))
	
	Underline = property(_getUnderline, _setUnderline, None,
			_("Underline setting for this font  (bool)"))
	
