import wx
import dControlMixin as cm

class dLabel(wx.StaticText, cm.dControlMixin):
	""" Create a static (not data-aware) label.
	"""
	def __init__(self, parent, id=-1, name='dLabel', style=0, *args, **kwargs):

		self._baseClass = dLabel

		pre = wx.PreStaticText()
		self.beforeInit(pre)                  # defined in dPemMixin

		pre.Create(parent, id, name, style=style | pre.GetWindowStyle(), *args, **kwargs)
		self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name)
		self.afterInit()                      # defined in dPemMixin


	def initEvents(self):
		# init the common events:
		cm.dControlMixin.initEvents(self)

		# init the widget's specialized event(s):

	# property get/set functions
	def _getAutoResize(self):
		return not self.hasWindowStyleFlag(wx.ST_NO_AUTORESIZE)
	def _setAutoResize(self, value):
		self.delWindowStyleFlag(wx.ST_NO_AUTORESIZE)
		if not value:
			self.addWindowStyleFlag(wx.ST_NO_AUTORESIZE)

	def _getAlignment(self):
		if self.hasWindowStyleFlag(wx.ALIGN_RIGHT):
			return 'Right'
		elif self.hasWindowStyleFlag(wx.ALIGN_CENTRE):
			return 'Center'
		else:
			return 'Left'

	def _getAlignmentEditorInfo(self):
		return {'editor': 'list', 'values': ['Left', 'Center', 'Right']}

	def _setAlignment(self, value):
		# Note: Alignment must be set before object created.
		self.delWindowStyleFlag(wx.ALIGN_LEFT)
		self.delWindowStyleFlag(wx.ALIGN_CENTRE)
		self.delWindowStyleFlag(wx.ALIGN_RIGHT)

		value = str(value)

		if value == 'Left':
			self.addWindowStyleFlag(wx.ALIGN_LEFT)
		elif value == 'Center':
			self.addWindowStyleFlag(wx.ALIGN_CENTRE)
		elif value == 'Right':
			self.addWindowStyleFlag(wx.ALIGN_RIGHT)
		else:
			raise ValueError, ("The only possible values are "
							"'Left', 'Center', and 'Right'.")

	# property definitions follow:
	AutoResize = property(_getAutoResize, _setAutoResize, None,
		'Specifies whether the length of the caption determines the size of the label. (bool)')
	Alignment = property(_getAlignment, _setAlignment, None,
						'Specifies the alignment of the text. (str) \n'
						'   Left (default) \n'
						'   Center \n'
						'   Right')

if __name__ == "__main__":
	import test
	test.Test().runTest(dLabel)
