import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

	
class dCheckBox(wx.CheckBox, dcm.dDataControlMixin):
	""" Allows visual editing of boolean values.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dCheckBox
		preClass = wx.PreCheckBox
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	
	def _initEvents(self):
		super(dCheckBox, self)._initEvents()
		self.Bind(wx.EVT_CHECKBOX, self._onWxHit)
		
		if wx.Platform == "__WXMAC__":
			# On Mac, checkboxes don't receive the focus, so we need to flush the 
			# value on every hit. (pkm: I'm thinking maybe we should do it this 
			# way for all platforms, for all non-textentry data controls.)
			self.bindEvent(dEvents.Hit, self.__onHit )
	
			
	def __onHit(self, evt):
		self.flushValue()

		
	# property get/set functions
	def _getAlignment(self):
		if self.hasWindowStyleFlag(wx.ALIGN_RIGHT):
			return "Right"
		else:
			return "Left"

	def _getAlignmentEditorInfo(self):
		return {"editor": "list", "values": ["Left", "Right"]}

	def _setAlignment(self, value):
		self.delWindowStyleFlag(wx.ALIGN_RIGHT)
		if str(value) == "Right":
			self.addWindowStyleFlag(wx.ALIGN_RIGHT)
		elif str(value) == "Left":
			pass
		else:
			raise ValueError, "The only possible values are 'Left' and 'Right'."

		
	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
		"""Specifies the alignment of the text.
			
		Left  : Checkbox to left of text (default)
		Right : Checkbox to right of text
		""")

						
if __name__ == "__main__":
	import test
	test.Test().runTest(dCheckBox)
