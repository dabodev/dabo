import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

	
class dCheckBox(wx.CheckBox, dcm.dDataControlMixin):
	""" Allows visual editing of boolean values.
	"""
	def __init__(self, parent, id=-1, name='dCheckBox', style=0, *args, **kwargs):
		
		self._baseClass = dCheckBox

		pre = wx.PreCheckBox()
		self._beforeInit(pre)
		pre.Create(parent, id, name=name, style=style|pre.GetWindowStyle(), *args, **kwargs)
		self.PostCreate(pre)
		
		dcm.dDataControlMixin.__init__(self, name)
		self._afterInit()


	def initEvents(self):
		dCheckBox.doDefault()

		# Respond to EVT_CHECKBOX and raise dEvents.Hit:
		self.Bind(wx.EVT_CHECKBOX, self._onWxHit)
		
				
	# property get/set functions
	def _getAlignment(self):
		if self.hasWindowStyleFlag(wx.ALIGN_RIGHT):
			return 'Right'
		else:
			return 'Left'

	def _getAlignmentEditorInfo(self):
		return {'editor': 'list', 'values': ['Left', 'Right']}

	def _setAlignment(self, value):
		self.delWindowStyleFlag(wx.ALIGN_RIGHT)
		if str(value) == 'Right':
			self.addWindowStyleFlag(wx.ALIGN_RIGHT)
		elif str(value) == 'Left':
			pass
		else:
			raise ValueError, "The only possible values are 'Left' and 'Right'."

	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
						'Specifies the alignment of the text. (int) \n'
						'   Left  : Checkbox to left of text (default) \n'
						'   Right : Checkbox to right of text')
if __name__ == "__main__":
	import test
	test.Test().runTest(dCheckBox)
