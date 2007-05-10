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
		kwargs["style"] = wx.TE_MULTILINE | wx.TE_WORDWRAP
		tbm.dTextBoxMixinBase.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
	
	
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
