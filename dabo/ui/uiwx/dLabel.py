import wx
import dabo
from dabo.dLocalize import _

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.ui import makeDynamicProperty


class dLabel(wx.StaticText, cm.dControlMixin):
	"""Creates a static label, to make a caption for another control, for example."""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dLabel
		preClass = wx.PreStaticText
		cm.dControlMixin.__init__(self, preClass, parent, 
				properties, *args, **kwargs)


	# property get/set functions
	def _getAutoResize(self):
		return not self._hasWindowStyleFlag(wx.ST_NO_AUTORESIZE)
		
	def _setAutoResize(self, value):
		self._delWindowStyleFlag(wx.ST_NO_AUTORESIZE)
		if not value:
			self._addWindowStyleFlag(wx.ST_NO_AUTORESIZE)


	def _getAlignment(self):
		if self._hasWindowStyleFlag(wx.ALIGN_RIGHT):
			return "Right"
		elif self._hasWindowStyleFlag(wx.ALIGN_CENTRE):
			return "Center"
		else:
			return "Left"

	def _setAlignment(self, value):
		# Note: Alignment must be set before object created.
		self._delWindowStyleFlag(wx.ALIGN_LEFT)
		self._delWindowStyleFlag(wx.ALIGN_CENTRE)
		self._delWindowStyleFlag(wx.ALIGN_RIGHT)
		value = str(value)

		if value == "Left":
			self._addWindowStyleFlag(wx.ALIGN_LEFT)
		elif value == "Center":
			self._addWindowStyleFlag(wx.ALIGN_CENTRE)
		elif value == "Right":
			self._addWindowStyleFlag(wx.ALIGN_RIGHT)
		else:
			raise ValueError, ("The only possible values are "
							"'Left', 'Center', and 'Right'.")
							
	
	def _getFontBold(self):
		return super(dLabel, self)._getFontBold()
		
	def _setFontBold(self, val):
		super(dLabel, self)._setFontBold(val)
		if self._constructed():
			# This will force an auto-resize
			self.SetLabel(self.GetLabel())
			
		
	def _getFontFace(self):
		return super(dLabel, self)._getFontFace()
		
	def _setFontFace(self, val):
		super(dLabel, self)._setFontFace(val)
		if self._constructed():
			# This will force an auto-resize
			self.SetLabel(self.GetLabel())
			
		
	def _getFontItalic(self):
		return super(dLabel, self)._getFontItalic()
		
	def _setFontItalic(self, val):
		super(dLabel, self)._setFontItalic(val)
		if self._constructed():
			# This will force an auto-resize
			self.SetLabel(self.GetLabel())
		
		
	def _getFontSize(self):
		return super(dLabel, self)._getFontSize()
		
	def _setFontSize(self, val):
		super(dLabel, self)._setFontSize(val)
		if self._constructed():
			# This will force an auto-resize
			self.SetLabel(self.GetLabel())
		

	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
			_("""Specifies the alignment of the text. (str)
			Left (default)
			Center
			Right""") )
	DynamicAlignment = makeDynamicProperty(Alignment)
			
	AutoResize = property(_getAutoResize, _setAutoResize, None,
			_("""Specifies whether the length of the caption determines
			the size of the label. (bool)""") )
	
	FontBold = property(_getFontBold, _setFontBold, None,
			_("Sets the Bold of the Font (int)") )
	DynamicFontBold = makeDynamicProperty(FontBold)
			
	FontFace = property(_getFontFace, _setFontFace, None,
			_("Sets the face of the Font (int)") )
	DynamicFontFace = makeDynamicProperty(FontFace)
			
	FontItalic = property(_getFontItalic, _setFontItalic, None,
			_("Sets the Italic of the Font (int)") )
	DynamicFontItalic = makeDynamicProperty(FontItalic)
			
	FontSize = property(_getFontSize, _setFontSize, None,
			_("Sets the size of the Font (int)") )
	DynamicFontSize = makeDynamicProperty(FontSize)


class _dLabel_test(dLabel):
	def initProperties(self):
		self.FontBold = True
		self.Alignment = "Center"
		self.ForeColor = "Red"
		self.Width = 300
		self.Caption = "My God, it's full of stars!"


if __name__ == "__main__":
	import test
	test.Test().runTest(_dLabel_test)
