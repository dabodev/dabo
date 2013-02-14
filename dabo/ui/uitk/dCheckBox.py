# -*- coding: utf-8 -*-
import Tkinter, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("tk")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.lib.utils import ustr


class dCheckBox(Tkinter.Checkbutton, dcm.dDataControlMixin):
	""" Allows visual editing of boolean values.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dCheckBox
		preClass = Tkinter.Checkbutton
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties,
				*args, **kwargs)

		self.pack()


	def initEvents(self):
		super(dCheckBox, self).initEvents()

		self.bindEvent(dEvents.MouseLeftClick, self._onTkHit)
		self.bindEvent(dEvents.KeyDown, self._onKeyDown)


	def _onKeyDown(self, event):
		char = event.EventData["keyChar"]
		if char is not None and ord(char) in (10,13,32):
			self._onTkHit(event)

	def _getValue(self):
		try:
			v = self._value
		except AttributeError:
			v, self._value = False, False
			self.deselect()
		return v

	def _setValue(self, value):
		self._value = bool(value)
		if self._value:
			self.select()
		else:
			self.deselect()


	Value = property(_getValue, _setValue, None,
		'Specifies the current state of the control (the value of the field). (varies)')


	# property get/set functions
# 	def _getAlignment(self):
# 		if self._hasWindowStyleFlag(wx.ALIGN_RIGHT):
# 			return 'Right'
# 		else:
# 			return 'Left'
#
# 	def _getAlignmentEditorInfo(self):
# 		return {'editor': 'list', 'values': ['Left', 'Right']}
#
# 	def _setAlignment(self, value):
# 		self._delWindowStyleFlag(wx.ALIGN_RIGHT)
# 		if ustr(value) == 'Right':
# 			self._addWindowStyleFlag(wx.ALIGN_RIGHT)
# 		elif ustr(value) == 'Left':
# 			pass
# 		else:
# 			raise ValueError("The only possible values are 'Left' and 'Right'.")
#
# 	# property definitions follow:
# 	Alignment = property(_getAlignment, _setAlignment, None,
# 						'Specifies the alignment of the text. (int) \n'
# 						'   Left  : Checkbox to left of text (default) \n'
# 						'   Right : Checkbox to right of text')


if __name__ == "__main__":
	class C(dCheckBox):
		def initEvents(self):
			super(C, self).initEvents()
			self.bindEvent(dEvents.Hit, self.onHit)

		def onHit(self, evt):
			self.Caption = self.Caption + "hit!"


	import test
	test.Test().runTest(C)
