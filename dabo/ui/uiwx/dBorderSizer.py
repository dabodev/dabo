# -*- coding: utf-8 -*-
import wx
import dabo
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


dabo.ui.loadUI("wx")


class dBorderSizer(dabo.ui.dSizerMixin, wx.StaticBoxSizer):
	"""
	A BorderSizer is a regular box sizer, but with a visible box around
	the perimiter. You must either create the box first and pass it to the
	dBorderSizer's constructor, or pass a parent object, and the box
	will be created for you in the constructor as a child object of the parent
	you passed.
	"""
	def __init__(self, box, orientation="h", properties=None, **kwargs):
		self._baseClass = dBorderSizer
		self._border = 0
		self._parent = None
		# Make sure that they got the params in the right order
		if isinstance(box, basestring):
			box, orientation = orientation, box
		if not isinstance(box, dabo.ui.dBox):
			prnt = box
			box = dabo.ui.dBox(prnt)
			box.sendToBack()
		# Convert Dabo orientation to wx orientation
		orient = self._extractKey((kwargs, properties), "Orientation", orientation)
		if orient[0].lower() == "v":
			orientation = wx.VERTICAL
		else:
			orientation = wx.HORIZONTAL
		wx.StaticBoxSizer.__init__(self, box, orientation)

		self._properties = {}
		# The keyword properties can come from either, both, or none of:
		#    + the properties dict
		#    + the kwargs dict
		# Get them sanitized into one dict:
		if properties is not None:
			# Override the class values
			for k,v in properties.items():
				self._properties[k] = v
		properties = self._extractKeywordProperties(kwargs, self._properties)
		self.setProperties(properties)

		if kwargs:
			# Some kwargs haven't been handled.
			bad = ", ".join(kwargs.keys())
			raise TypeError(("Invalid keyword arguments passed to dBorderSizer: %s") % kwargs)

		# Mark the box as part of the sizer
		self.Box._belongsToBorderSizer = True

		self._afterInit()


	def getNonBorderedClass(self):
		"""Return the class that is the non-border sizer version of this class."""
		return dabo.ui.dSizer


	def _getBackColor(self):
		return self.Box.BackColor

	def _setBackColor(self, val):
		self.Box.BackColor = val


	def _getBox(self):
		return self.GetStaticBox()


	def _getCaption(self):
		return self.Box.Caption

	def _setCaption(self, val):
		self.Box.Caption = val


	def _getFontBold(self):
		return self.Box.FontBold

	def _setFontBold(self, val):
		self.Box.FontBold = val


	def _getFontFace(self):
		return self.Box.FontFace

	def _setFontFace(self, val):
		self.Box.FontFace = val


	def _getFontItalic(self):
		return self.Box.FontItalic

	def _setFontItalic(self, val):
		self.Box.FontItalic = val


	def _getFontSize(self):
		return self.Box.FontSize

	def _setFontSize(self, val):
		self.Box.FontSize = val


	def _getFontUnderline(self):
		return self.Box.FontUnderline

	def _setFontUnderline(self, val):
		self.Box.FontUnderline = val


	BackColor = property(_getBackColor, _setBackColor, None,
			_("Color of the box background  (str or tuple)"))

	Box = property(_getBox, None, None,
			_("Reference to the box used in the sizer  (dBox)"))

	Caption = property(_getCaption, _setCaption, None,
			_("Caption for the box  (str)"))

	FontBold = property(_getFontBold, _setFontBold, None,
			_("Controls the bold setting of the box caption  (bool)"))

	FontFace = property(_getFontFace, _setFontFace, None,
			_("Controls the type face of the box caption  (str)"))

	FontItalic = property(_getFontItalic, _setFontItalic, None,
			_("Controls the italic setting of the box caption  (bool)"))

	FontSize = property(_getFontSize, _setFontSize, None,
			_("Size of the box caption font  (int)"))

	FontUnderline = property(_getFontUnderline, _setFontUnderline, None,
			_("Controls the underline setting of the box caption  (bool)"))


	# Dynamic property declarations
	DynamicBackColor = makeDynamicProperty(BackColor)
	DynamicCaption = makeDynamicProperty(Caption)
	DynamicFontBold = makeDynamicProperty(FontBold)
	DynamicFontFace = makeDynamicProperty(FontFace)
	DynamicFontItalic = makeDynamicProperty(FontItalic)
	DynamicFontSize = makeDynamicProperty(FontSize)
	DynamicFontUnderline = makeDynamicProperty(FontUnderline)



class TestForm(dabo.ui.dForm):
	def afterInit(self):
		self.Sizer = dabo.ui.dSizer("v", DefaultBorder=10)
		lbl = dabo.ui.dLabel(self, Caption="Button in BoxSizer Below", FontSize=16)
		self.Sizer.append(lbl, halign="center")
		sz = dBorderSizer(self, "v")
		self.Sizer.append1x(sz)
		btn = dabo.ui.dButton(self, Caption="Click")
		sz.append1x(btn)
		pnl = dabo.ui.dPanel(self, BackColor="seagreen")
		self.Sizer.append1x(pnl, border=18)

class _dBorderSizer_test(dBorderSizer):
	def __init__(self, bx=None, *args, **kwargs):
		super(_dBorderSizer_test, self).__init__(box=bx, orientation="h", *args, **kwargs)




if __name__ == "__main__":
	from dabo.dApp import dApp
	app = dApp()
	app.MainFormClass = TestForm
	app.start()
