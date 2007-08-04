# -*- coding: utf-8 -*-
import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dTextBoxMixin as tbm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.ui import makeDynamicProperty


# The EditBox is just a TextBox with some additional styles.

class dEditBox(tbm.dTextBoxMixinBase, wx.TextCtrl):
	"""Creates an editbox, which allows editing of string data of unlimited size.

	The editbox will create scrollbars as necessary, and can edit string or 
	unicode data.
	"""
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dEditBox
		
		preClass = wx.PreTextCtrl
		kwargs["style"] = wx.TE_MULTILINE
		tbm.dTextBoxMixinBase.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
	
	
	def _getInitPropertiesList(self):
		additional = ["WordWrap",]
		original = list(super(dEditBox, self)._getInitPropertiesList())
		return tuple(original + additional)

	def scrollToBeginning(self):
		"""Moves the insertion point to the beginning of the text"""
		self.SetInsertionPoint(0)
		self.ShowPosition(0)
		self.Refresh()
		
	
	def scrollToEnd(self):
		"""Moves the insertion point to the end of the text"""
		self.SetInsertionPointEnd()
		self.ShowPosition(self.GetLastPosition())
		self.Refresh()
	
	
	#Property getters and setters
	def _getWordWrap(self):
		return self._hasWindowStyleFlag(wx.TE_BESTWRAP)
	
	def _setWordWrap(self, val):
		if self._constructed():
			fontSize = self.GetFont().GetPointSize()
		self._delWindowStyleFlag(wx.TE_DONTWRAP)
		self._delWindowStyleFlag(wx.TE_WORDWRAP)
		self._delWindowStyleFlag(wx.TE_BESTWRAP)
		if val:
			self._addWindowStyleFlag(wx.TE_BESTWRAP)
		else:
			self._addWindowStyleFlag(wx.TE_DONTWRAP)
		if self._constructed():
			self.FontSize = fontSize
	
	# property definitions follow:
	WordWrap = property(_getWordWrap, _setWordWrap, None,
			_("""Specifies whether words get wrapped (the default). (bool)

			If False, a horizontal scrollbar will appear when a line is too long
			to fit in the horizontal space."""))



class _dEditBox_test(dEditBox):
	def initProperties(self):
		self.Size = (333, 175)
		self.Value = """Love, exciting and new
Come aboard, were expecting you
Love, lifes sweetest reward
Let it flow, it floats back to you

Love Boat soon will be making another run
The Love Boat promises something for everyone
Set a course for adventure
Your mind on a new romance

Love wont hurt anymore
Its an open smile on a friendly shore
Yes love...
Its love...

Love Boat soon will be making another run
The Love Boat promises something for everyone
Set a course for adventure
Your mind on a new romance

Love wont hurt anymore
Its an open smile on a friendly shore
Its love...
Its love...
Its love...
Its the Love Boat
Its the Love Boat 
"""
		self.TextLength = 50
		self.ForceCase = "u"


if __name__ == "__main__":
	import test
	test.Test().runTest(_dEditBox_test)
