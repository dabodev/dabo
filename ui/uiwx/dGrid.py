import wx, wx.grid
import dabo.ui.dControlMixin as cm

class dGrid(wx.grid.Grid, cm.dControlMixin):
	def __init__(self, parent, id=-1, name='dGrid', style=0, *args, **kwargs):

		self._baseClass = dGrid

		# no 3-stage create for grids
		#pre = wx.PreGrid()
		self._beforeInit(None)

		wx.grid.Grid.__init__(self, parent, id, name=name, style=style, *args, **kwargs)
		#pre.Create(parent, id, name, style=style | pre.GetWindowStyle(), *args, **kwargs)
		#self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name)
		
		# The grid's default MinSize is pretty big, resulting in weird sizer issues
		# starting with wxPython 2.5.2.3. Setting size to 0 here resolves the
		# problem (because there is code in the Size property to also set MinSize).
		self.Size = ((0,0))
		
		self._afterInit()

		
	def _getDataSource(self):
		try:
			return self._dataSource
		except AttributeError:
			return None
			
	def _setDataSource(self, value):
		self._dataSource = str(value)
		
		
	DataSource = property(_getDataSource, _setDataSource, None, 
					'The name of the data source for the grid.')
