import wx
import dControlMixin as cm
import dDataControlMixin as dcm

# The EditBox is just a TextBox with some additional styles.

class dEditBox(wx.TextCtrl, dcm.dDataControlMixin, cm.dControlMixin):
	''' Allows editing of string or unicode data of unlimited length.
	'''
	def __init__(self, parent, id=-1, name="dEditBox", style=0, *args, **kwargs):

		self._baseClass = dEditBox

		style = style | wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_LINEWRAP

		pre = wx.PreTextCtrl()
		self.beforeInit(pre)                  # defined in dPemMixin
		pre.Create(parent, id, name, style=style|pre.GetWindowStyleFlag(), *args, **kwargs)

		self.PostCreate(pre)
		
		cm.dControlMixin.__init__(self, name)
		dcm.dDataControlMixin.__init__(self)
		self.afterInit()                      # defined in dPemMixin


	def afterInit(self):
		self.SelectOnEntry = False
		dEditBox.doDefault()


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)
		dcm.dDataControlMixin.initEvents(self)

		# init the widget's specialized event(s):
		wx.EVT_TEXT(self, self.GetId(), self.OnText)

	# Event callback methods (override in subclasses):
	def OnText(self, event):
		event.Skip()


	# property get/set functions
	def _getAlignment(self):
		if self.hasWindowStyleFlag(wx.TE_RIGHT):
			return 'Right'
		elif self.hasWindowStyleFlag(wx.TE_CENTRE):
			return 'Center'
		else:
			return 'Left'

	def _getAlignmentEditorInfo(self):
		return {'editor': 'list', 'values': ['Left', 'Center', 'Right']}

	def _setAlignment(self, value):
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
			raise ValueError, ("The only possible values are "
							"'Left', 'Center', and 'Right'.")

	def _getReadOnly(self):
		return not self._pemObject.IsEditable()
	def _setReadOnly(self, value):
		self._pemObject.SetEditable(not value)
	
	def _getSelectOnEntry(self):
		try:
			return self._SelectOnEntry
		except AttributeError:
			return False
	def _setSelectOnEntry(self, value):
		self._SelectOnEntry = bool(value)

	# property definitions follow:
	Alignment = property(_getAlignment, _setAlignment, None,
						'Specifies the alignment of the text. (int) \n'
						'   Left (default) \n'
						'   Center \n'
						'   Right')
	
	ReadOnly = property(_getReadOnly, _setReadOnly, None, 
						'Specifies whether or not the text can be edited. (bool)')
	
	SelectOnEntry = property(_getSelectOnEntry, _setSelectOnEntry, None, 
						'Specifies whether all text gets selected upon receiving focus. (bool)')


if __name__ == "__main__":
	import test
	class c(dEditBox):
		def OnText(self, event): print "OnText!" 
	test.Test().runTest(c)
