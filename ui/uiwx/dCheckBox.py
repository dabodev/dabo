import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

	
class dCheckBox(wx.CheckBox, dcm.dDataControlMixin):
	""" Allows visual editing of boolean values.
	"""
	def __init__(self, parent, id=-1, name="dCheckBox", style=0, *args, **kwargs):
		
		self._baseClass = dCheckBox

		pre = wx.PreCheckBox()
		self._beforeInit(pre)
		pre.Create(parent, id, name=name, style=style|pre.GetWindowStyle(), *args, **kwargs)
		self.PostCreate(pre)
		
		dcm.dDataControlMixin.__init__(self, name)
		self._afterInit()


	def initEvents(self):
		#dCheckBox.doDefault()
		super(dCheckBox, self).initEvents()

		# Respond to EVT_CHECKBOX and raise dEvents.Hit:
		self.Bind(wx.EVT_CHECKBOX, self._onWxHit)
		
		if wx.Platform == "__WXMAC__":
			self.bindEvent(dEvents.Hit, self._onHit )
	
	def _onHit(self, evt):
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

	def _getValue(self):
		#return dCheckBox.doDefault()
		return super(dCheckBox, self)._getValue()
		
	def _setValue(self, value):
		#dCheckBox.doDefault(value)
		super(dCheckBox, self)._setValue(value)

		
	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
			"Specifies the alignment of the text. (int) \n"
			"   Left  : Checkbox to left of text (default) \n"
			"   Right : Checkbox to right of text")

	Value = property(_getValue, _setValue, None,
			"Specifies the current state of the control (the value of the field). (varies)")
						
if __name__ == "__main__":
	import test
	test.Test().runTest(dCheckBox)
