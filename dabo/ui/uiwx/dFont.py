import dabo
from dabo.dObject import dObject
from dabo.dLocalize import _


class dFont(dObject):
	"""This class wraps the various font properties into a single object."""
	def __init__(self, properties=None, *args, **kwargs):
		self._bold = None
		self._description = None
		self._face = None
		self._italic = None
		self._size = None
		self._underline = None
		# Some internal Dabo tools may need to access the platform-native
		# font object. This attribute holds that object, if any.
		self._baseObject = None
		super(dFont, self).__init__(properties=properties, *args, **kwargs)


	def _getBold(self):
		return self._bold

	def _setBold(self, val):
		self._bold = val


	def _getDescription(self):
		return self._description

	def _setDescription(self, val):
		self._description = val


	def _getFace(self):
		return self._face

	def _setFace(self, val):
		self._face = val


	def _getItalic(self):
		return self._italic

	def _setItalic(self, val):
		self._italic = val


	def _getSize(self):
		return self._size

	def _setSize(self, val):
		self._size = val


	def _getUnderline(self):
		return self._underline

	def _setUnderline(self, val):
		self._underline = val


	Bold = property(_getBold, _setBold, None,
			_("Bold setting for this font  (bool)"))
	
	Description = property(_getDescription, _setDescription, None,
			_("Read-only plain text description of the font  (str)"))
	
	Face = property(_getFace, _setFace, None,
			_("Name of the font face  (str)"))
	
	Italic = property(_getItalic, _setItalic, None,
			_("Italic setting for this font  (bool)"))
	
	Size = property(_getSize, _setSize, None,
			_("Size in points for this font  (int)"))
	
	Underline = property(_getUnderline, _setUnderline, None,
			_("Underline setting for this font  (bool)"))
	