import warnings
import wx, dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
import dPemMixin as pm
from dabo.dLocalize import _
from dIcons import getIconBitmap
from dabo.ui import makeDynamicProperty


class dBitmapButton(wx.BitmapButton, cm.dControlMixin):
	"""Creates a button with a picture.

	The button can have up to three pictures associated with it: 
		Picture: the normal picture shown on the button.
		DownPicture: the picture displayed when the button is depressed.
		FocusPicture: the picture displayed when the button has the focus.

	Otherwise, dBitmapButton behaves the same as a normal dButton.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dBitmapButton
		preClass = wx.PreBitmapButton
		# Initialize the self._*picture attributes
		self._picture = self._downPicture = self._focusPicture = ""
		# These atts underlie the image sizing properties.
		self._imgScale = self._imgHt = self._imgWd = None
		# This controls whether the button automatically resizes
		# itself when its Picture changes.
		self._autoSize = False
		# On some platforms, we need to add some 'breathing room'
		# around the bitmap image in order for it to appear correctly
		self._bmpBorder = 10
		
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		

	def _initEvents(self):
		super(dBitmapButton, self)._initEvents()
		self.Bind(wx.EVT_BUTTON, self._onWxHit)
		

	def __sizeToBitmap(self):
		if self.Picture:
			bmp = self.Bitmap
			self.Size = (bmp.GetWidth() + self._bmpBorder, 
					bmp.GetHeight() + self._bmpBorder)

		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	
	def _getAutoSize(self):
		return self._autoSize
		
	def _setAutoSize(self, val):
		self._autoSize = val
		
	
	def _getBmpBorder(self):
		return self._bmpBorder
		
	def _setBmpBorder(self, val):
		self._bmpBorder = val
		if self._autoSize:
			self.__sizeToBitmap()
			
		
	def _getCancelButton(self):
		# need to implement
		return False
		
	def _setCancelButton(self, val):
		warnings.warn("CancelButton isn't implemented yet.", Warning)	
	

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


	def _getDownBitmap(self):
		return self.GetBitmapSelected()
	
	
	def _getDownPicture(self):
		return self._downPicture
		
	def _setDownPicture(self, val):
		self._downPicture = val
		if self._constructed():
			if isinstance(val, wx.Bitmap):
				bmp = val
			else:
				bmp = dabo.ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
			self.SetBitmapSelected(bmp)
		else:
			self._properties["DownPicture"] = val


	def _getFocusBitmap(self):
		return self.GetBitmapFocus()

	
	def _getFocusPicture(self):
		return self._focusPicture

	def _setFocusPicture(self, val):
		self._focusPicture = val
		if self._constructed():
			if isinstance(val, wx.Bitmap):
				bmp = val
			else:
				bmp = dabo.ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
			self.SetBitmapFocus(bmp)
		else:
			self._properties["FocusPicture"] = val


	def _getImgHt(self):
		return self._imgHt

	def _setImgHt(self, val):
		self._imgHt = val
		if self._autoSize:
			self.Picture = self.Picture
			self.__sizeToBitmap()
	
	
	def _getImgScale(self):
		return self._imgScale
	
	def _setImgScale(self, val):
		self._imgScale = val
		if self._autoSize:
			pic = self.Picture
			if pic:
				self.Picture = pic
			self.__sizeToBitmap()
	
	
	def _getImgWd(self):
		return self._imgWd
	
	def _setImgWd(self, val):
		self._imgWd = val
		if self._autoSize:
			self.Picture = self.Picture
			self.__sizeToBitmap()
		
		
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
			# If the others haven't been specified, default them to the same
			if not self._downPicture:
				self.SetBitmapSelected(bmp)
			if not self._focusPicture:
				self.SetBitmapFocus(bmp)
			if self._autoSize:
				self.__sizeToBitmap()
		else:
			self._properties["Picture"] = val
	

	# Property definitions:
	AutoSize = property(_getAutoSize, _setAutoSize, None,
		_("Controls whether the button resizes when the Picture changes. (bool)") )
	DynamicAutoSize = makeDynamicProperty(AutoSize)
		
	Bitmap = property(_getNormalBitmap, None, None,
		_("""The bitmap normally displayed on the button.  (wx.Bitmap)"""))
	DynamicBitmap = makeDynamicProperty(Bitmap)

	BitmapBorder = property(_getBmpBorder, _setBmpBorder, None,
		_("""Extra space around the bitmap, used when auto-sizing.  (int)"""))
	DynamicBitmapBorder = makeDynamicProperty(BitmapBorder)

	CancelButton = property(_getCancelButton, _setCancelButton, None,
		_("Specifies whether this Bitmap button gets clicked on -Escape-."))
	DynamicCancelButton = makeDynamicProperty(CancelButton)
						
	DefaultButton = property(_getDefaultButton, _setDefaultButton, None, 
		_("Specifies whether this Bitmap button gets clicked on -Enter-."))
	DynamicDefaultButton = makeDynamicProperty(DefaultButton)

	DownBitmap = property(_getDownBitmap, None, None,
		_("The bitmap displayed on the button when it is depressed.  (wx.Bitmap)"))
	DynamicDownBitmap = makeDynamicProperty(DownBitmap)

	DownPicture = property(_getDownPicture, _setDownPicture, None,
		_("Specifies the image displayed on the button when it is depressed.  (str)"))
	DynamicDownPicture = makeDynamicProperty(DownPicture)

	FocusBitmap = property(_getFocusBitmap, None, None,
		_("The bitmap displayed on the button when it receives focus.  (wx.Bitmap)"))
	DynamicFocusBitmap = makeDynamicProperty(FocusBitmap)

	FocusPicture = property(_getFocusPicture, _setFocusPicture, None,
		_("Specifies the image displayed on the button when it receives focus.  (str)"))
	DynamicFocusPicture = makeDynamicProperty(FocusPicture)

	ImageHeight = property(_getImgHt, _setImgHt, None,
		_("""When set, sets the height of all images shown on this control. 
		Default=None, which performs no resizing.  (int)""") )
	DynamicImageHeight = makeDynamicProperty(ImageHeight)

	ImageScale = property(_getImgScale, _setImgScale, None,
		_("""When set, scales all images shown on this control. The value is
		a decimal, not a percent, so 1.0 is normal size, 0.5 is half size, etc.
		Default=None, which performs no scaling  (float)""") )
	DynamicImageScale = makeDynamicProperty(ImageScale)

	ImageWidth = property(_getImgWd, _setImgWd, None,
		_("""When set, sets the width of all images shown on this control. 
		Default=None, which performs no resizing.  (int)""") )
	DynamicImageWidth = makeDynamicProperty(ImageWidth)

	Picture = property(_getNormalPicture, _setNormalPicture, None,
		_("""Specifies the image normally displayed on the button.  This is the 
		default if none of the other Picture properties are 
		specified.  (str)"""))
	DynamicPicture = makeDynamicProperty(Picture)	


class _dBitmapButton_test(dBitmapButton):
	def afterInit(self):
		# Demonstrate that the Picture props are working.
		self.Picture = "save"
		self.DownPicture = "browse"
		self.FocusPicture = "edit"
		self.Width = 100
		self.Height = 25

if __name__ == "__main__":
	import test
	test.Test().runTest(_dBitmapButton_test)
