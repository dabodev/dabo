import wx, wx.grid, dabo, dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm

class dGrid(wx.grid.Grid, cm.dControlMixin):
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dGrid
		preClass = wx.grid.Grid
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)

	
	def _afterInit(self):
		super(dGrid, self)._afterInit()
		self.Size = (0,0)		

				
	def _getDataSource(self):
		try:
			return self._dataSource
		except AttributeError:
			return None
	def _setDataSource(self, value):
		self._dataSource = str(value)
	
	def _getHdr(self):
		return self.GetGridColLabelWindow()
		
		
	DataSource = property(_getDataSource, _setDataSource, None, 
			"The name of the data source for the grid.")

	Header = property(_getHdr, None, None,
			"Reference to the row of column labels across the top of the grid  (window)")
			