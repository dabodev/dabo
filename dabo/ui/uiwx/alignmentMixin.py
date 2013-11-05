# -*- coding: utf-8 -*-
import wx
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.ui import makeDynamicProperty

class AlignmentMixin(object):
	def _getAlignment(self):
		if self._hasWindowStyleFlag(wx.ALIGN_RIGHT):
			return "Right"
		elif self._hasWindowStyleFlag(wx.ALIGN_CENTRE):
			return "Center"
		else:
			return "Left"

	def _setAlignment(self, value):
		# Note: Alignment must be set before object created.
		self._delWindowStyleFlag(wx.ALIGN_LEFT)
		self._delWindowStyleFlag(wx.ALIGN_CENTRE)
		self._delWindowStyleFlag(wx.ALIGN_RIGHT)
		value = ustr(value).lower()

		if value == "left":
			self._addWindowStyleFlag(wx.ALIGN_LEFT)
		elif value == "center":
			self._addWindowStyleFlag(wx.ALIGN_CENTRE)
		elif value == "right":
			self._addWindowStyleFlag(wx.ALIGN_RIGHT)
		else:
			raise ValueError("The only possible values are "
							"'Left', 'Center', and 'Right'.")

	Alignment = property(_getAlignment, _setAlignment, None,
			_("""Specifies the alignment of the text. (str)
			Left (default)
			Center
			Right""") )

	DynamicAlignment = makeDynamicProperty(Alignment)

