import wx
import dabo
dabo.ui.loadUI("wx")
import dForm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dabo.common import dColors
import random
import dControlMixin as cm


class SplitMenu(dabo.ui.dMenu):
	def __init__(self, frm=None, useRemoveOpt=True):
		super(SplitMenu, self).__init__(frm)
		self.idSplit = wx.NewId()
		self.idRemove = wx.NewId()
		self.Append(self.idSplit, "Split this pane")
		if useRemoveOpt:
			self.Append(self.idRemove, "Remove this pane")


class SplitterPanel(dabo.ui.dPanel):
	def __init__(self, parent):
		super(SplitterPanel, self).__init__(parent)
		self.Bind(wx.EVT_MENU, self.onMenu)
		self.bindEvent(dEvents.MouseRightClick, self.onRClick)
	
	def onRClick(self, evt):
		rem = self.Parent.canRemove(self) 
		menu = SplitMenu(useRemoveOpt=rem)
		pos = evt.EventData["mousePosition"]
		self.PopupMenu(menu, pos)
	
	def onMenu(self, evt):
		menu = evt.GetEventObject()
		id = evt.GetId()
		if id == menu.idSplit:
			self.split()
		elif id == menu.idRemove:
			self.remove()
	
	
	def remove(self):
		self.Parent.remove(self)

		
	def split(self, dir=None):
		if not self.Parent.IsSplit():
			# Re-show the hidden split panel
			self.Parent.split()
			return
		orientation = self.Parent.Orientation[0].lower()
		# Default to the opposite of the current orientation
		if orientation == "h":
			newDir = "v"
		else:
			newDir = "h"
		if self.Sizer is None:
			self.Sizer = dabo.ui.dSizer(newDir)
		if dir is None:
			dir = newDir
		win = dSplitter(self)
		win.Orientation = dir
		win.unsplit()
		win.split()
		self.Sizer.append(win, 1, "expand")
		self.splitter = win
		self.Layout()
	
	def unsplit(self, win=None):
		self.splitter.unsplit(win)
		
		

class dSplitter(wx.SplitterWindow, cm.dControlMixin):
	""" Main class for handling split windows. It will contain two
	panels (subclass of SplitterPanel), each of which can further 
	split itself in two.
	"""
	def __init__(self, parent, properties=None, *args, **kwargs):
			
		self._baseClass = dSplitter
		
		baseStyle = wx.SP_3D | wx.SP_PERMIT_UNSPLIT
		try:
			style = style | baseStyle
		except UnboundLocalError:
			style = baseStyle
			
		preClass = wx.PreSplitterWindow
		cm.dControlMixin.__init__(self, preClass, parent, properties, 
				style=style, *args, **kwargs)
		
	
	def _initEvents(self):
		self.Bind(wx.EVT_SPLITTER_DCLICK, self._onSashDClick)
	

	def _afterInit(self):
		super(dSplitter, self)._afterInit()
		# Create the panes
		self.__p1 = SplitterPanel(self)
		self.__p1.BackColor = random.choice(dColors.colorDict.values())
		self.__p2 = SplitterPanel(self)
		self.__p2.BackColor = random.choice(dColors.colorDict.values())
		
		# Default to vertical split
		self._orientation = "v"
		self._sashPos = 100
		self.MinPanelSize = 100
# 		self.initialize(p1)
		self.split()
	
	
	def initialize(self, p1):
		self.Initialize(p1)
	
	
	def _onSashDClick(self, evt):
		""" Handle the doubl-clicking of the sash. This will call
		the user-customizable onSashDClick() method.
		"""
		# Update the internal sash position attribute.
		self._getSashPosition()
		self.onSashDClick(evt)
	def onSashDClick(self, evt): pass
	
		
	def split(self, dir=None):
		if self.IsSplit():
			return
		if dir:
			self.Orientation = dir

		# Since unsplitting hides the panes, make sure that they are visible
		self.Panel1.Visible = True
		self.Panel2.Visible = True
		# Get the position
		pos = self.SashPosition
		if self.Orientation == "Horizontal":
			self.SplitHorizontally(self.Panel1, self.Panel2, pos)
		else:
			self.SplitVertically(self.Panel1, self.Panel2, pos)
		self.Layout()
	
	
	def unsplit(self, win=None):
		if self.IsSplit():
			# Save the sash position
			self._getSashPosition()
			self.Unsplit(win)
			self.Layout()
			
	
	def canRemove(self, pnl):
		ret = self.IsSplit()
		if not ret:
			# Make sure that there is at least one level of splitting somewhere
			obj = self
			while obj.Parent and not ret:
				obj = obj.Parent
				if isinstance(obj, dSplitter):
					ret = self.IsSplit()
		return ret
		
		
	def remove(self, pnl):
		if self.IsSplit():
			self.unsplit(pnl)
		else:
			# If the parent of this is a SplitterPanel, tell it to hide
			prnt = self.Parent
			if isinstance(prnt, SplitterPanel):
				prnt.remove()
			else:
				self.Destroy()				
	
	
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
	
	def _getPanel1(self):
		return self.__p1
	def _getPanel2(self):
		return self.__p2
	
	def _getSashPosition(self):
		if self.IsSplit():
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
	Panel1 = property(_getPanel1, None, None,
			"Returns the Top/Left panel.  (SplitterPanel)" )
	Panel2 = property(_getPanel2, None, None,
			"Returns the Bottom/Right panel.  (SplitterPanel)" )
	SashPosition = property(_getSashPosition, _setSashPosition, None,
			"Position of the sash when the window is split.  (int)")
			

if __name__ == "__main__":
	import test
	test.Test().runTest(dSplitter)
