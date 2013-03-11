# -*- coding: utf-8 -*-
import sys
import wx
try:
	import wx.lib.platebtn as platebtn
except ImportError:
	raise ImportError("Your version of wxPython is too old for dBorderlessButton")
import dabo
import dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
from dabo.dLocalize import _
import dabo.dColors as dColors
from dabo.ui import makeDynamicProperty


class dBorderlessButton(cm.dControlMixin, platebtn.PlateButton):
	"""
	Creates a button that can be pressed by the user to trigger an action.

	Example::

		class MyButton(dabo.ui.dBorderlessButton):
			def initProperties(self):
				self.Caption = "Press Me"

			def onHit(self, evt):
				self.Caption = "Press Me one more time"

	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dBorderlessButton
		preClass = platebtn.PlateButton

		self._backColorHover = (128, 128, 128)
		# Initialize the self._*picture attributes
		self._picture = self._hoverPicture = self._focusPicture = ""
		# These atts underlie the image sizing properties.
		self._imgScale = self._imgHt = self._imgWd = None
		# This controls whether the button automatically resizes
		# itself when its Picture changes.
		self._autoSize = False
		# On some platforms, we need to add some 'breathing room'
		# around the bitmap image in order for it to appear correctly
		self._bmpBorder = 10

		cm.dControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)


	def _initEvents(self):
		super(dBorderlessButton, self)._initEvents()
		#The EVT_BUTTON event for this control is fired
		#to the parent of the control rather than the control.
		#Binding to EVT_LEFT_UP fixes the problem. -nwl
		self.Bind(wx.EVT_LEFT_UP, self._onWxHit)


	def _getInitPropertiesList(self):
		return super(dBorderlessButton, self)._getInitPropertiesList() + \
			("ButtonShape",)


	# Property getters and setters
	def _getBackColorHover(self):
		return self._backColorHover

	def _setBackColorHover(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				val = dColors.colorTupleFromName(val)
			if isinstance(val, tuple):
				self._backColoHover = val
				self.SetPressColor(wx.Color(*val))
			else:
				raise ValueError("BackColorHover must be a valid color string or tuple")
		else:
			self._properties["BackColorHover"] = val


	def _getButtonShape(self):
		if self._hasWindowStyleFlag(platebtn.PB_STYLE_SQUARE):
			return "Square"
		else:
			return "Normal"

	def _setButtonShape(self, val):
		sst = val[:1].lower()
		if sst == "s":
			self._addWindowStyleFlag(platebtn.PB_STYLE_SQUARE)
		elif sst in ("n", "r"):
			self._delWindowStyleFlag(platebtn.PB_STYLE_SQUARE)
		else:
			nm = self.Name
			raise ValueError(_("Invalid value of %(nm)s.ButtonShape "
					"property: %(val)s") % locals())


	def _getCancelButton(self):
		# need to implement
		return False

	def _setCancelButton(self, val):
		warnings.warn(_("CancelButton isn't implemented yet."), Warning)


	def _getDefaultButton(self):
		if self.Parent is not None:
			return self.Parent.GetDefaultItem() == self
		else:
			return False

	def _setDefaultButton(self, val):
		if self._constructed():
			if val:
				if self.Parent is not None:
					self.Parent.SetDefaultItem(self._pemObject)
			else:
				if self._pemObject.GetParent().GetDefaultItem() == self._pemObject:
					# Only change the default item to None if it wasn't self: if another object
					# is the default item, setting self.DefaultButton = False shouldn't also set
					# that other object's DefaultButton to False.
					self.SetDefaultItem(None)
		else:
			self._properties["DefaultButton"] = val


	def _getNormalBitmap(self):
		return self.GetBitmapLabel()


	def _getNormalPicture(self):
		return self._picture

	def _setNormalPicture(self, val):
		self._picture = val
		if self._constructed():
			if isinstance(val, wx.Bitmap):
				bmp = val
			else:
				bmp = dabo.ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
			self.SetBitmapLabel(bmp)
		else:
			self._properties["Picture"] = val


	# Property definitions:
	BackColorHover = property(_getBackColorHover, _setBackColorHover, None,
		_("""Color of the button background when mouse is hovered over control (str or tuple)
		Default=(128, 128, 128)
		Changing this color with change the color of the control when pressed as well."""))

	Bitmap = property(_getNormalBitmap, None, None,
		_("""The bitmap normally displayed on the button.  (wx.Bitmap)"""))

	ButtonShape = property(_getButtonShape, _setButtonShape,
		_("""Shape of the button. (str)

		Normal/Rounded	:	button with rounded corners. (default)
		Square			:	button with square corners."""))

	Picture = property(_getNormalPicture, _setNormalPicture, None,
		_("""Specifies the image normally displayed on the button. (str)"""))



class _dBorderlessButton_test(dBorderlessButton):
	def initProperties(self):
		self.Caption = "You better not push me"
		self.FontSize = 8
		self.Width = 223
		self.Picture = "themes/tango/32x32/apps/accessories-text-editor.png"


	def onContextMenu(self, evt):
		print "context menu"

	def onMouseRightClick(self, evt):
		print "right click"

	def onHit(self, evt):
		self.ForeColor = "purple"
		self.FontBold = True
		self.FontItalic = True
		self.Caption = "Ok, you cross this line, and you die."
		self.Width = 333
		self.Form.layout()

if __name__ == "__main__":
	import test
	test.Test().runTest(_dBorderlessButton_test)
