import wx, dControlMixin

class dPageFrame(wx.Notebook, dControlMixin.dControlMixin):

	def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
			size=wx.DefaultSize, style=0, name='dPageFrame'):

		self._baseClass = dPageFrame

		pre = wx.PreNotebook()
		self.beforeInit(pre)                  # defined in dPemMixin
		style = style | pre.GetWindowStyle()
		pre.Create(parent, id, pos, size, style, name)

		self.this = pre.this
		self._setOORInfo(self)

		dControlMixin.dControlMixin.__init__(self, name)
		self.afterInit()                      # defined in dPemMixin


	def afterInit(self):
		self.lastSelection = 0
		dPageFrame.doDefault()


	def initEvents(self):
		dControlMixin.dControlMixin.initEvents(self)
		self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)


	def OnPageChanged(self, event):
		ls = self.lastSelection
		cs = event.GetSelection()

		event.Skip()    # This must happen before onLeave/EnterPage below

		newPage = self.GetPage(cs)
		oldPage = self.GetPage(ls)    

		oldPage.onLeavePage()
		newPage.onEnterPage()

		self.lastSelection = cs

	# property get/set functions:
	def _getTabPosition(self):
		if self.hasWindowStyleFlag(wx.NB_BOTTOM):
			return 'Bottom'
		elif self.hasWindowStyleFlag(wx.NB_RIGHT):
			return 'Right'
		elif self.hasWindowStyleFlag(wx.NB_LEFT):
			return 'Left'
		else:
			return 'Top'

	def _getTabPositionEditorInfo(self):
		return {'editor': 'list', 'values': ['Top', 'Left', 'Right', 'Bottom']}

	def _setTabPosition(self, value):
		value = str(value)

		self.delWindowStyleFlag(wx.NB_BOTTOM)
		self.delWindowStyleFlag(wx.NB_RIGHT)
		self.delWindowStyleFlag(wx.NB_LEFT)

		if value == 'Top':
			pass
		elif value == 'Left':
			self.addWindowStyleFlag(wx.NB_LEFT)
		elif value == 'Right':
			self.addWindowStyleFlag(wx.NB_RIGHT)
		elif value == 'Bottom':
			self.addWindowStyleFlag(wx.NB_BOTTOM)
		else:
			raise ValueError, ("The only possible values are "
						"'Top', 'Left', 'Right', and 'Bottom'")

	# Property definitions:
	TabPosition = property(_getTabPosition, _setTabPosition, None, 
						'Specifies where the page tabs are located. (int) \n'
						'    Top (default) \n'
						'    Left \n'
						'    Right \n'
						'    Bottom')

