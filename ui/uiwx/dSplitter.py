import wx
import dabo
dabo.ui.loadUI("wx")
import dForm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dControlMixin as cm

class dSplitter(wx.SplitterWindow, cm.dControlMixin):
	""" Don't know if we need this class, since the form will handle all the
	spllitter events, but just in case...
	"""
	def __init__(self, parent, id=-1, style=wx.SP_3D | wx.SP_PERMIT_UNSPLIT, 
			properties=None, *args, **kwargs):
		
		self._baseClass = dSplitter
		properties = self.extractKeywordProperties(kwargs, properties)
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)

		pre = wx.PreSplitterWindow()
		self._beforeInit(pre)
		
		pre.Create(parent, id, style=style | pre.GetWindowStyle(), *args, **kwargs)
		self.PostCreate(pre)

		cm.dControlMixin.__init__(self, name, _explicitName=_explicitName)
		
		self.setProperties(properties)
		self._afterInit()
		
		# Create the panes
		p1 = dabo.ui.dPanel(self)
		p1.BackColor = "red"
		p2 = dabo.ui.dPanel(self)
		p2.BackColor = "blue"
		self.p1 = p1
		self.p2 = p2
		
		# Default to vertical split
		self._orientation = "v"
		self._sashPos = 100
		self.split()
	
	
	def initialize(self, p1, p2):
		self.Initialize(p1, p2)
		
		
	def split(self, dir=None):
		if self.IsSplit():
			return
		if dir:
			self.Orientation = dir

		# Since unsplitting hides the panes, make sure that they are visible
		self.p1.Visible = True
		self.p2.Visible = True
		
		if self.Orientation == "Horizontal":
			self.SplitHorizontally(self.p1, self.p2, self.SashPosition)
		else:
			self.SplitVertically(self.p1, self.p2, self.SashPosition)
		self.Layout()
	
	def unsplit(self):
		if self.IsSplit():
			self.Unsplit()
			self.Layout()
	
	def _getMinPanelSize(self):
		return self.GetMinimumPaneSize()
	def _setMinPanelSize(self, val):
		self.SetMinimumPaneSize(val)
	
	def _getOrientation(self):
		if self._orientation == "v":
			return "Vertical"
		else:
			return "Horizontal"
	def _setOrientation(self, val):
		orient = val.lower()[0]
		if orient in ("h", "v"):
			self._orientation = orient
		else:
			raise ValueError, "Orientation can only be 'Horizontal' or 'Vertical'"
	
	def _getSashPosition(self):
		self._sashPos = self.GetSashPosition()
		return self._sashPos
	def _setSashPosition(self, val):
		self.SetSashPosition(val)
		# Set the internal prop from the wx Prop
		self._sashPos = self.GetSashPosition()
	
	MinPanelSize = property(_getMinPanelSize, _setMinPanelSize, None,
			"Controls the minimum width/height of the panels.  (int)")
	Orientation = property(_getOrientation, _setOrientation, None,
			"Determines if the window splits Horizontally or Vertically.  (string)")
	SashPosition = property(_getSashPosition, _setSashPosition, None,
			"Position of the sash when the window is split.  (int)")


if __name__ == "__main__":
	import test
	test.Test().runTest(dSplitter)
