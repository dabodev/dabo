import wx
import dabo
from dabo.dObject import dObject
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


class dFont(dObject):
	"""This class wraps the various font properties into a single object."""
	def __init__(self, properties=None, font=None, *args, **kwargs):
		if font is not None:
			self._nativeObject = font
		else:
			self._nativeObject = wx.Font(dabo.settings.defaultFontSize, 
					wx.DEFAULT, wx.NORMAL, wx.NORMAL)
	
		super(dFont, self).__init__(properties=properties, *args, **kwargs)

	
	def _getBold(self):
		return (self._nativeObject.GetWeight() == wx.BOLD)

	def _setBold(self, val):
		if val:
			self._nativeObject.SetWeight(wx.BOLD)
		else:
			self._nativeObject.SetWeight(wx.LIGHT)


	def _getDescription(self):
		ret = self.Face + " " + str(self.Size)
		if self.Bold:
			ret += " B"
		if self.Italic:
			ret += " I"
		return ret


	def _getFace(self):
		return self._nativeObject.GetFaceName()

	def _setFace(self, val):
		self._nativeObject.SetFaceName(val)


	def _getItalic(self):
		return (self._nativeObject.GetStyle() == wx.ITALIC)

	def _setItalic(self, val):
		if val:
			self._nativeObject.SetStyle(wx.ITALIC)
		else:
			self._nativeObject.SetStyle(wx.NORMAL)


	def _getNativeObject(self):
		return self._nativeObject

	def _setNativeObject(self, val):
		self._nativeObject = val


	def _getSize(self):
		return self._nativeObject.GetPointSize()

	def _setSize(self, val):
		self._nativeObject.SetPointSize(val)


	def _getUnderline(self):
		return self._nativeObject.GetUnderlined()

	def _setUnderline(self, val):
		self._nativeObject.SetUnderlined(val)


	Bold = property(_getBold, _setBold, None,
			_("Bold setting for this font  (bool)"))
	
	Description = property(_getDescription, None, None,
			_("Read-only plain text description of the font  (str)"))
	
	Face = property(_getFace, _setFace, None,
			_("Name of the font face  (str)"))
	
	Italic = property(_getItalic, _setItalic, None,
			_("Italic setting for this font  (bool)"))
	
	NativeObject = property(_getNativeObject, _setNativeObject, None,
			_("UI toolkit-specific font object  (wx.Font)"))
	
	Size = property(_getSize, _setSize, None,
			_("Size in points for this font  (int)"))
	
	Underline = property(_getUnderline, _setUnderline, None,
			_("Underline setting for this font  (bool)"))
	
