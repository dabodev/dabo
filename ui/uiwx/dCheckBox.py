import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

	
class dCheckBox(wx.CheckBox, dcm.dDataControlMixin):
	""" Allows visual editing of boolean values.
	"""
	def __init__(self, parent, id=-1, style=0, properties=None, *args, **kwargs):
		
		self._baseClass = dCheckBox
		properties = self.extractKeywordProperties(kwargs, properties)
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)
		
		pre = wx.PreCheckBox()
		self._beforeInit(pre)
		pre.Create(parent, id, style=style|pre.GetWindowStyle(), *args, **kwargs)
		self.PostCreate(pre)
		
		dcm.dDataControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self.setProperties(properties)
		self._afterInit()


	def initEvents(self):
		#dCheckBox.doDefault()
		super(dCheckBox, self).initEvents()

		# Respond to EVT_CHECKBOX and raise dEvents.Hit:
		self.Bind(wx.EVT_CHECKBOX, self._onWxHit)
		
		if wx.Platform == "__WXMAC__":
			# On Mac, checkboxes don't receive the focus, so we need to flush the value
			# on every hit. (pkm: I'm thinking maybe we should do it this way for all platforms)
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

		
	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
			"Specifies the alignment of the text. (int) \n"
			"   Left  : Checkbox to left of text (default) \n"
			"   Right : Checkbox to right of text")

						
if __name__ == "__main__":
	import test
	test.Test().runTest(dCheckBox)
