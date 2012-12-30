# -*- coding: utf-8 -*-
import wx
import wx.lib.buttons as wxb
import dabo

if __name__ == "__main__":
	import dabo.ui
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dImageMixin as dim
from dabo.dLocalize import _
import dabo.dEvents as dEvents

class dToggleButton(dcm.dDataControlMixin, dim.dImageMixin,
		wxb.GenBitmapTextToggleButton):
	"""
	Creates a button that toggles on and off, for editing boolean values.

	This is functionally equivilent to a dCheckbox, but visually much different.
	Also, it implies that pushing it will cause some sort of immediate action to
	take place, like you get with a normal button.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dabo.ui.dToggleButton
		preClass = wxb.GenBitmapTextToggleButton
		# These are required arguments
		kwargs["bitmap"] = None
		kwargs["label"] = ""
		self._downPicture = None
		bw = self._extractKey(attProperties, "BezelWidth", None)
		if bw is not None:
			bw = int(bw)
		else:
			bw = self._extractKey((properties, kwargs), "BezelWidth", 5)
		kwargs["BezelWidth"] = bw
		style = self._extractKey((properties, attProperties, kwargs), "style", 0) | wx.BORDER_NONE
		kwargs["style"] = style
		dim.dImageMixin.__init__(self)
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)
		self.Bind(wx.EVT_BUTTON, self.__onButton)


	def __onButton(self, evt):
		self.flushValue()
		self.raiseEvent(dEvents.Hit, evt)


	def getBlankValue(self):
		return False


	def _getBezelWidth(self):
		return self.GetBezelWidth()

	def _setBezelWidth(self, val):
		if self._constructed():
			self.SetBezelWidth(val)
			self.Refresh()
		else:
			self._properties["BezelWidth"] = val


	def _getDownPicture(self):
		return self._downPicture

	def _setDownPicture(self, val):
		if self._constructed():
			self._downPicture = val
			if isinstance(val, wx.Bitmap):
				bmp = val
			else:
				bmp = dabo.ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
			self.SetBitmapSelected(bmp)
			self.refresh()
		else:
			self._properties["DownPicture"] = val


	def _getPicture(self):
		return self._picture

	def _setPicture(self, val):
		if self._constructed():
			self._picture = val
			if isinstance(val, wx.Bitmap):
				bmp = val
			else:
				bmp = dabo.ui.strToBmp(val, self._imgScale, self._imgWd, self._imgHt)
			notdown = not self._downPicture
			self.SetBitmapLabel(bmp, notdown)
			self.refresh()
		else:
			self._properties["Picture"] = val


	BezelWidth = property(_getBezelWidth, _setBezelWidth, None,
			_("Width of the bezel on the sides of the button. Default=5  (int)"))

	DownPicture = property(_getDownPicture, _setDownPicture, None,
			_("Picture displayed when the button is pressed  (str)"))

	Picture = property(_getPicture, _setPicture, None,
			_("Picture used for the normal (unselected) state  (str)"))


class _dToggleButton_test(dToggleButton):
	def afterInit(self):
		self.Caption = "Toggle me!"
		self.Size = (100, 31)
		self.Picture = "themes/tango/22x22/apps/accessories-text-editor.png"
		self.DownPicture = "themes/tango/22x22/apps/help-browser.png"

	def onHit(self, evt):
		if self.Value:
			state = "down"
		else:
			state = "up"
		bval = self.Value
		self.Caption = _("State: %(state)s (Boolean: %(bval)s)") % locals()


if __name__ == "__main__":
	import test
	test.Test().runTest(_dToggleButton_test)
