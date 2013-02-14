# -*- coding: utf-8 -*-
import Tkinter, dabo, dabo.ui
from dabo.lib.utils import ustr

if __name__ == "__main__":
	dabo.ui.loadUI("tk")

import dControlMixin as cm

class dLabel(Tkinter.Label, cm.dControlMixin):
	""" Create a static (not data-aware) label.
	"""
	def __init__(self, master, cnf={}, name='dLabel', *args, **kwargs):

		self._baseClass = dLabel

		self._beforeInit()

		Tkinter.Label.__init__(self, master, cnf, name=name, *args, **kwargs)

		cm.dControlMixin.__init__(self, name)
		self._afterInit()

		self.pack()


	def initEvents(self):
		super(dLabel, self).initEvents()


# 	# property get/set functions
# 	def _getAutoResize(self):
# 		return not self._hasWindowStyleFlag(wx.ST_NO_AUTORESIZE)
# 	def _setAutoResize(self, value):
# 		self._delWindowStyleFlag(wx.ST_NO_AUTORESIZE)
# 		if not value:
# 			self._addWindowStyleFlag(wx.ST_NO_AUTORESIZE)
#
# 	def _getAlignment(self):
# 		if self._hasWindowStyleFlag(wx.ALIGN_RIGHT):
# 			return 'Right'
# 		elif self._hasWindowStyleFlag(wx.ALIGN_CENTRE):
# 			return 'Center'
# 		else:
# 			return 'Left'
#
# 	def _getAlignmentEditorInfo(self):
# 		return {'editor': 'list', 'values': ['Left', 'Center', 'Right']}
#
# 	def _setAlignment(self, value):
# 		# Note: Alignment must be set before object created.
# 		self._delWindowStyleFlag(wx.ALIGN_LEFT)
# 		self._delWindowStyleFlag(wx.ALIGN_CENTRE)
# 		self._delWindowStyleFlag(wx.ALIGN_RIGHT)
#
# 		value = ustr(value)
#
# 		if value == 'Left':
# 			self._addWindowStyleFlag(wx.ALIGN_LEFT)
# 		elif value == 'Center':
# 			self._addWindowStyleFlag(wx.ALIGN_CENTRE)
# 		elif value == 'Right':
# 			self._addWindowStyleFlag(wx.ALIGN_RIGHT)
# 		else:
# 			raise ValueError("The only possible values are "
# 							"'Left', 'Center', and 'Right'.")
#
# 	# property definitions follow:
# 	AutoResize = property(_getAutoResize, _setAutoResize, None,
# 		'Specifies whether the length of the caption determines the size of the label. (bool)')
# 	Alignment = property(_getAlignment, _setAlignment, None,
# 						'Specifies the alignment of the text. (str) \n'
# 						'   Left (default) \n'
# 						'   Center \n'
# 						'   Right')

if __name__ == "__main__":
	import test
	test.Test().runTest(dLabel)
