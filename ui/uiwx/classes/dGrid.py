import wx, wx.grid
import dControlMixin as cm

class dGrid(wx.grid.Grid, cm.dControlMixin):
	def __init__(self, parent, id=-1, name='dGrid', style=0, *args, **kwargs):

		self._baseClass = dGrid

		# no 3-stage create for grids
		#pre = wx.PreGrid()
		self._beforeInit(None)                  # defined in dPemMixin

		wx.grid.Grid.__init__(self, parent, id, name=name, style=style, *args, **kwargs)
		#pre.Create(parent, id, name, style=style | pre.GetWindowStyle(), *args, **kwargs)
		#self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name)
		self._afterInit()                      # defined in dPemMixin

		
	def _getDataSource(self):
		try:
			return self._dataSource
		except AttributeError:
			return None
			
	def _setDataSource(self, value):
		self._dataSource = str(value)
		
		
	DataSource = property(_getDataSource, _setDataSource, None, 
					'The name of the data source for the grid.')