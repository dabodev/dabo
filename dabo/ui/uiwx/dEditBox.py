import wx, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _

# The EditBox is just a TextBox with some additional styles.

class dEditBox(wx.TextCtrl, dcm.dDataControlMixin):
	""" Allows editing of string or unicode data of unlimited length.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dEditBox
		preClass = wx.PreTextCtrl
		kwargs["style"] = wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_LINEWRAP
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)


	def _initEvents(self):
		super(dEditBox, self)._initEvents()
		self.Bind(wx.EVT_TEXT, self._onWxHit)
		

	def selectAll(self):
		"""Each subclass must define their own selectAll method. This will 
		be called if SelectOnEntry is True when the control gets focus.
		"""
		self.SetSelection(-1, -1)
		
		
	# property get/set functions
	def _getAlignment(self):
		if self._hasWindowStyleFlag(wx.TE_RIGHT):
			return 'Right'
		elif self._hasWindowStyleFlag(wx.TE_CENTRE):
			return 'Center'
		else:
			return 'Left'

	def _setAlignment(self, value):
		self._delWindowStyleFlag(wx.TE_LEFT)
		self._delWindowStyleFlag(wx.TE_CENTRE)
		self._delWindowStyleFlag(wx.TE_RIGHT)

		value = str(value).lower()

		if value == 'left':
			self._addWindowStyleFlag(wx.TE_LEFT)
		elif value == 'center':
			self._addWindowStyleFlag(wx.TE_CENTRE)
		elif value == 'right':
			self._addWindowStyleFlag(wx.TE_RIGHT)
		else:
			raise ValueError, ("The only possible values are "
							"'Left', 'Center', and 'Right'.")


	def _getReadOnly(self):
		return not self.IsEditable()

	def _setReadOnly(self, value):
		if self._constructed():
			self.SetEditable(not value)
		else:
			self._properties["ReadOnly"] = value
	

	def _getSelectOnEntry(self):
		try:
			return self._SelectOnEntry
		except AttributeError:
			return False
	def _setSelectOnEntry(self, value):
		self._SelectOnEntry = bool(value)

	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
		"""Specifies the alignment of the text.
		
		Left (default)
		Center
		Right
		""")
	
	ReadOnly = property(_getReadOnly, _setReadOnly, None, 
		"""Specifies whether or not the text can be edited.""")
	
	SelectOnEntry = property(_getSelectOnEntry, _setSelectOnEntry, None, 
		"""Specifies whether all text gets selected upon receiving focus.""")


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

if __name__ == "__main__":
	import test
	test.Test().runTest(_dEditBox_test)
