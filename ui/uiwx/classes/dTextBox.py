import wx
import dControlMixin as cm
import dDataControlMixin as dcm

class dTextBox(wx.TextCtrl, dcm.dDataControlMixin, cm.dControlMixin):
	""" Allows editing one line of string or unicode data.
	"""
	def __init__(self, parent, id=-1, name="dTextBox", style=0, *args, **kwargs):

		self._baseClass = dTextBox

		pre = wx.PreTextCtrl()
		self._beforeInit(pre)                  # defined in dPemMixin
		pre.Create(parent, id, name, style=style|pre.GetWindowStyleFlag(), *args, **kwargs)
		self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name)
		dcm.dDataControlMixin.__init__(self)
		self._afterInit()                      # defined in dPemMixin


	def afterInit(self):
		self.SelectOnEntry = True
		dTextBox.doDefault()


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)
		dcm.dDataControlMixin.initEvents(self)

		# init the widget's specialized event(s):
		wx.EVT_TEXT(self, self.GetId(), self.OnText)


	# Event callback method(s) (override in subclasses):
	def OnText(self, event):
		self.raiseValueChanged()
		event.Skip()


	# property get/set functions
	def _getAlignment(self):
		if self.hasWindowStyleFlag(wx.TE_RIGHT):
			return "Right"
		elif self.hasWindowStyleFlag(wx.TE_CENTRE):
			return "Center"
		else:
			return "Left"

	def _getAlignmentEditorInfo(self):
		return {'editor': 'list', 'values': ['Left', 'Center', 'Right']}

	def _setAlignment(self, value):
		# Note: alignment doesn't seem to work, at least on GTK2
		self.delWindowStyleFlag(wx.TE_LEFT)
		self.delWindowStyleFlag(wx.TE_CENTRE)
		self.delWindowStyleFlag(wx.TE_RIGHT)

		value = str(value)

		if value == 'Left':
			self.addWindowStyleFlag(wx.TE_LEFT)
		elif value == 'Center':
			self.addWindowStyleFlag(wx.TE_CENTRE)
		elif value == 'Right':
			self.addWindowStyleFlag(wx.TE_RIGHT)
		else:
			raise ValueError, "The only possible values are 'Left', 'Center', and 'Right'"

	def _getReadOnly(self):
		return not self._pemObject.IsEditable()
	def _setReadOnly(self, value):
		self._pemObject.SetEditable(not bool(value))

	def _getPasswordEntry(self):
		return self.hasWindowStyleFlag(wx.TE_PASSWORD)
	def _setPasswordEntry(self, value):
		self.delWindowStyleFlag(wx.TE_PASSWORD)
		if value:
			self.addWindowStyleFlag(wx.TE_PASSWORD)
		# Note: control needs to be recreated for this flag change
		#       to take effect.
	
	def _getSelectOnEntry(self):
		try:
			return self._SelectOnEntry
		except AttributeError:
			return False
	def _setSelectOnEntry(self, value):
		self._SelectOnEntry = bool(value)


	# Property definitions:
	Alignment = property(_getAlignment, _setAlignment, None,
						'Specifies the alignment of the text. (str) \n'
						'   Left (default) \n'
						'   Center \n'
						'   Right')
	ReadOnly = property(_getReadOnly, _setReadOnly, None, 
						'Specifies whether or not the text can be edited. (bool)')

	PasswordEntry = property(_getPasswordEntry, _setPasswordEntry, None,
						'Specifies whether plain-text or asterisks are echoed. (bool)')
	
	SelectOnEntry = property(_getSelectOnEntry, _setSelectOnEntry, None, 
						'Specifies whether all text gets selected upon receiving focus. (bool)')


if __name__ == "__main__":
	import test
	class c(dTextBox):
		def OnText(self, event): print "OnText!"
	test.Test().runTest(c)
