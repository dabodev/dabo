import warnings
import wx, dabo, dabo.ui
if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
import dPemMixin as pm
from dabo.dLocalize import _
from dIcons import getIconBitmap

class dBitmapButton(wx.BitmapButton, cm.dControlMixin):
	""" Allows the user to cause an action to occur by pushing a button.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dBitmapButton
		preClass = wx.PreBitmapButton
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

		if self.Picture == wx.NullBitmap:
			# Default to the dabo icon
			self.Picture = "daboIcon048"


	def _initEvents(self):
		super(dBitmapButton, self)._initEvents()
		self.Bind(wx.EVT_BUTTON, self._onWxHit)
		
		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getCancelButton(self):
		# need to implement
		return False
	def _setCancelButton(self, value):
		warnings.warn("CancelButton isn't implemented yet.", Warning)	
	
	def _getDefaultButton(self):
		return self._pemObject.GetParent().GetDefaultItem() == self._pemObject
	def _setDefaultButton(self, value):
		if value:
			self._pemObject.GetParent().SetDefaultItem(self._pemObject)
			if wx.Platform == '__WXGTK__':
				warnings.warn("DefaultButton doesn't seem to work on GTK.", Warning)
		else:
			if self._pemObject.GetParent().GetDefaultItem() == self._pemObject:
				# Only change the default item to None if it wasn't self: if another object
				# is the default item, setting self.DefaultButton = False shouldn't also set
				# that other object's DefaultButton to False.
				self.SetDefaultItem(None)

	def _getNormalPicture(self):
		return self.GetBitmapLabel()
	def _setNormalPicture(self, value):
		if type(value) == type(""):
			# Convert to bitmap
			value = getIconBitmap(value)
		self.SetBitmapLabel(value)
	
	def _getDownPicture(self):
		return self.GetBitmapSelected()
	def _setDownPicture(self, value):
		if type(value) == type(""):
			# Convert to bitmap
			value = getIconBitmap(value)
		self.SetBitmapSelected(value)
	
	def _getFocusPicture(self):
		return self.GetBitmapFocus()
	def _setFocusPicture(self, value):
		if type(value) == type(""):
			# Convert to bitmap
			value = getIconBitmap(value)
		self.SetBitmapFocus(value)
	

	# Property definitions:
	CancelButton = property(_getCancelButton, _setCancelButton, None,
		_("Specifies whether this Bitmap button gets clicked on -Escape-."))
						
	DefaultButton = property(_getDefaultButton, _setDefaultButton, None, 
		_("Specifies whether this Bitmap button gets clicked on -Enter-."))

	Picture = property(_getNormalPicture, _setNormalPicture, None,
		_("""Specifies the image normally displayed on the button. 
		
		This is the default if none of the other Picture properties are 
		specified.
		"""))

	DownPicture = property(_getDownPicture, _setDownPicture, None,
		_("Specifies the image displayed on the button when it is depressed."))

	FocusPicture = property(_getFocusPicture, _setFocusPicture, None,
		_("Specifies the image displayed on the button when it receives focus."))


if __name__ == "__main__":
	import test
	class c(dBitmapButton):
		def afterInit(self):
			# Demonstrate that the Picture props are working.
			self.Picture = "daboIcon048"
			self.DownPicture = "daboIcon064"
			self.FocusPicture = "daboIcon016"
	test.Test().runTest(c)
