import wx
import dabo
import dabo.dEvents as dEvents
from dabo.dLocalize import _

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.ui import makeDynamicProperty


class dLabel(cm.dControlMixin, wx.StaticText):
	"""Creates a static label, to make a caption for another control, for example."""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dLabel
		self._wordWrap = False
		preClass = wx.PreStaticText
		cm.dControlMixin.__init__(self, preClass, parent, 
				properties, *args, **kwargs)
				
	
	def __onResize(self, evt):
		"""Event binding is set when Wrap=True. Tell the label
		to wrap to its current width.
		"""
		# We need to set the caption to the internally-saved caption, since 
		# WordWrap can introduce additional linefeeds.
		self.SetLabel(self._caption)
		self.Wrap(self.Width)


	# property get/set functions
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
		value = str(value).lower()

		if value == "left":
			self._addWindowStyleFlag(wx.ALIGN_LEFT)
		elif value == "center":
			self._addWindowStyleFlag(wx.ALIGN_CENTRE)
		elif value == "right":
			self._addWindowStyleFlag(wx.ALIGN_RIGHT)
		else:
			raise ValueError, ("The only possible values are "
							"'Left', 'Center', and 'Right'.")
							
	
	def _getAutoResize(self):
		return not self._hasWindowStyleFlag(wx.ST_NO_AUTORESIZE)
		
	def _setAutoResize(self, value):
		self._delWindowStyleFlag(wx.ST_NO_AUTORESIZE)
		if not value:
			self._addWindowStyleFlag(wx.ST_NO_AUTORESIZE)


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
		

	def _getWordWrap(self):
		return self._wordWrap

	def _setWordWrap(self, val):
		if self._constructed():
			self._wordWrap = val
			self.unbindEvent(dEvents.Resize)
			if val:
				# Make sure AutoResize is False.
				if self.AutoResize:
					#dabo.info.write(_("Setting AutoResize to False since WordWrap is True"))
					self.AutoResize = False
				self.bindEvent(dEvents.Resize, self.__onResize)				
		else:
			self._properties["Wrap"] = val


	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
			_("""Specifies the alignment of the text. (str)
			Left (default)
			Center
			Right""") )
			
	AutoResize = property(_getAutoResize, _setAutoResize, None,
			_("""Specifies whether the length of the caption determines
			the size of the label. This cannot be True if WordWrap is
			also set to True. Default=True.  (bool)""") )
	
	FontBold = property(_getFontBold, _setFontBold, None,
			_("Sets the Bold of the Font (int)") )
			
	FontFace = property(_getFontFace, _setFontFace, None,
			_("Sets the face of the Font (int)") )
			
	FontItalic = property(_getFontItalic, _setFontItalic, None,
			_("Sets the Italic of the Font (int)") )
			
	FontSize = property(_getFontSize, _setFontSize, None,
			_("Sets the size of the Font (int)") )

	WordWrap = property(_getWordWrap, _setWordWrap, None,
			_("""When True, the Caption is wrapped to the Width. 
			If this is set to True, AutoResize must be False.
			Default=False  (bool)"""))
	

	DynamicAlignment = makeDynamicProperty(Alignment)
	DynamicFontBold = makeDynamicProperty(FontBold)
	DynamicFontFace = makeDynamicProperty(FontFace)
	DynamicFontItalic = makeDynamicProperty(FontItalic)
	DynamicFontSize = makeDynamicProperty(FontSize)
	DynamicWordWrap = makeDynamicProperty(WordWrap)



class _dLabel_test(dLabel):
	def initProperties(self):
		self.FontBold = True
		self.Alignment = "Center"
		self.ForeColor = "Red"
		self.Width = 300
		self.Caption = "My God, it's full of stars!"
		self.Wrap = True

		
if __name__ == "__main__":
	import test
	test.Test().runTest(_dLabel_test)
