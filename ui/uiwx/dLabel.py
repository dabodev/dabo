import wx, dabo, dabo.ui
from dabo.dLocalize import _

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm

class dLabel(wx.StaticText, cm.dControlMixin):
	""" Create a static (not data-aware) label.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dLabel
		preClass = wx.PreStaticText
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _initEvents(self):
		super(dLabel, self)._initEvents()


	# property get/set functions
	def _getAutoResize(self):
		return not self.hasWindowStyleFlag(wx.ST_NO_AUTORESIZE)
	def _setAutoResize(self, value):
		self.delWindowStyleFlag(wx.ST_NO_AUTORESIZE)
		if not value:
			self.addWindowStyleFlag(wx.ST_NO_AUTORESIZE)

	def _getAlignment(self):
		if self.hasWindowStyleFlag(wx.ALIGN_RIGHT):
			return "Right"
		elif self.hasWindowStyleFlag(wx.ALIGN_CENTRE):
			return "Center"
		else:
			return "Left"

	def _getAlignmentEditorInfo(self):
		return {"editor": "list", "values": ["Left", "Center", "Right"]}

	def _setAlignment(self, value):
		# Note: Alignment must be set before object created.
		self.delWindowStyleFlag(wx.ALIGN_LEFT)
		self.delWindowStyleFlag(wx.ALIGN_CENTRE)
		self.delWindowStyleFlag(wx.ALIGN_RIGHT)

		value = str(value)

		if value == "Left":
			self.addWindowStyleFlag(wx.ALIGN_LEFT)
		elif value == "Center":
			self.addWindowStyleFlag(wx.ALIGN_CENTRE)
		elif value == "Right":
			self.addWindowStyleFlag(wx.ALIGN_RIGHT)
		else:
			raise ValueError, ("The only possible values are "
							"'Left', 'Center', and 'Right'.")
	
	def _getFontBold(self):
		return super(dLabel, self)._getFontBold()
	def _setFontBold(self, val):
		super(dLabel, self)._setFontBold(val)
		# This will force an auto-resize
		self.SetLabel(self.GetLabel())
		
	def _getFontFace(self):
		return super(dLabel, self)._getFontFace()
	def _setFontFace(self, val):
		super(dLabel, self)._setFontFace(val)
		# This will force an auto-resize
		self.SetLabel(self.GetLabel())
		
	def _getFontItalic(self):
		return super(dLabel, self)._getFontItalic()
	def _setFontItalic(self, val):
		super(dLabel, self)._setFontItalic(val)
		# This will force an auto-resize
		self.SetLabel(self.GetLabel())
		
	def _getFontSize(self):
		return super(dLabel, self)._getFontSize()
	def _setFontSize(self, val):
		super(dLabel, self)._setFontSize(val)
		# This will force an auto-resize
		self.SetLabel(self.GetLabel())
		

	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
			_("""Specifies the alignment of the text. (str)
	   Left (default)
	   Center
	   Right""") )
	AutoResize = property(_getAutoResize, _setAutoResize, None,
			_("Specifies whether the length of the caption determines "
			"the size of the label. (bool)") )
	
	FontBold = property(_getFontBold, _setFontBold, None,
			_("Sets the Bold of the Font (int)") )
	FontFace = property(_getFontFace, _setFontFace, None,
			_("Sets the face of the Font (int)") )
	FontItalic = property(_getFontItalic, _setFontItalic, None,
			_("Sets the Italic of the Font (int)") )
	FontSize = property(_getFontSize, _setFontSize, None,
			_("Sets the size of the Font (int)") )


if __name__ == "__main__":
	import test
	testProps = {"FontBold": True, "Alignment": "Center", "ForeColor": "Red"}
	test.Test().runTest(dLabel, Width=150, Caption="Hello", 
			properties=testProps)
