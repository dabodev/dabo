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
	def __init__(self, parent, id=-1, bitmap=None, name="dBitmapButton", 
				style=0, *args, **kwargs):
		
		self._baseClass = dBitmapButton

		pre = wx.PreBitmapButton()
		self._beforeInit(pre)
		
		if bitmap is None:
			# Default to the Dabo icon
			bitmap = getIconBitmap("daboIcon048")
		
		pre.Create(parent, id, bitmap, name=name, style=style|pre.GetWindowStyle(), *args, **kwargs)

		self.PostCreate(pre)
		
		cm.dControlMixin.__init__(self, name)
		self._afterInit()


	def initEvents(self):
		# init the common events:
		dBitmapButton.doDefault()

		# Respond to EVT_BUTTON and raise dEvents.Hit:
		self.Bind(wx.EVT_BUTTON, self._onWxHit)
		
		
	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getCancelButton(self):
		# need to implement
		return False
	def _setCancelButton(self, value):
		warnings.warn(Warning, "CancelButton isn't implemented yet.")	
	
	def _getDefaultButton(self):
		return self._pemObject.Parent.GetDefaultItem() == self
	def _setDefaultButton(self, value):
		if value:
			self._pemObject.Parent.SetDefaultItem(self)
			if wx.Platform == '__WXGTK__':
				warnings.warn(Warning, "DefaultButton doesn't seem to work on GTK.")
		else:
			self._pemObject.SetDefaultItem(None)

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
						_('Specifies whether this Bitmap button gets clicked on -Escape-. (bool)'))
						
	DefaultButton = property(_getDefaultButton, _setDefaultButton, None, 
						_('Specifies whether this Bitmap button gets clicked on -Enter-. (bool)'))

	Picture = property(_getNormalPicture, _setNormalPicture, None,
				_("The image normally displayed on the button. This is the default if none of the other Picture properties are specified. (bitmap)") )

	DownPicture = property(_getDownPicture, _setDownPicture, None,
				_("The image displayed on the button when it is depressed. (bitmap)") )

	FocusPicture = property(_getFocusPicture, _setFocusPicture, None,
				_("The image displayed on the button when it receives focus. (bitmap)") )


if __name__ == "__main__":
	import test
	class c(dBitmapButton):
		def afterInit(self):
			# Demonstrate that the Picture props are working.
			self.DownPicture = "daboIcon064"
			self.FocusPicture = "daboIcon016"
			
		def onButton(self, evt): 
			print "Bitmap Button!"
			evt.Skip()

	test.Test().runTest(c)
