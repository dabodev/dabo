import random
import wx
import dabo
dabo.ui.loadUI("wx")
import dForm
import dabo.dEvents as dEvents
from dabo.dLocalize import _
import dabo.dColors as dColors
import dControlMixin as cm


class SplitterPanel(dabo.ui.dPanel):
	def __init__(self, parent):
		super(SplitterPanel, self).__init__(parent)
		self.bindEvent(dEvents.MouseRightClick, self._onRClick)
	
	def _onRClick(self, evt):
		sm = dabo.ui.dMenu(self)
		sm.append("Split this pane", bindfunc=self.onSplit)
		if self.Parent.canRemove(self):
			sm.append("Remove this pane", bindfunc=self.onRemove)
		pos = evt.EventData["mousePosition"]
		self.PopupMenu(sm, pos)

	def onSplit(self, evt):
		self.split()
	def onRemove(self, evt):
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
		win = dSplitter(self, createPanes=True)
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
			style = kwargs["style"] | baseStyle
			del kwargs["style"]
		except KeyError:
			style = baseStyle
		
		self._createPanes = False
		try:
			self._createPanes = kwargs["createPanes"]
			del kwargs["createPanes"]
		except KeyError: pass
		
		self._splitOnInit = True
		try:
			self._splitOnInit = kwargs["splitOnInit"]
			del kwargs["splitOnInit"]
		except KeyError: pass
		
		self._colorizePanes = True
		try:
			self._colorizePanes = kwargs["colorizePanes"]
			del kwargs["colorizePanes"]
		except KeyError: pass
			
		preClass = wx.PreSplitterWindow
		cm.dControlMixin.__init__(self, preClass, parent, properties, 
				style=style, *args, **kwargs)
		
	
	def _initEvents(self):
		self.Bind(wx.EVT_SPLITTER_DCLICK, self._onSashDClick)
	

	def _afterInit(self):
		super(dSplitter, self)._afterInit()
		self.__p1 = None
		self.__p2 = None
		# Create the panes
		if self._createPanes:
			self.__p1 = SplitterPanel(self)
			self.__p2 = SplitterPanel(self)
			if self._colorizePanes:
				self.__p1.BackColor = random.choice(dColors.colorDict.values())
				self.__p2.BackColor = random.choice(dColors.colorDict.values())
		
		# Default to vertical split
		self._orientation = "v"
		self._sashPos = 100
		self.MinPanelSize = 100
		if self._splitOnInit:
			self.split()
	
	
	def initialize(self, p1):
		self.Initialize(p1)
	
	
	def _onSashDClick(self, evt):
		""" Handle the doubl-clicking of the sash. This will call
		the user-customizable onSashDClick() method.
		"""
		# Update the internal sash position attribute.
		self._getSashPosition()
		# Raise a dEvent for other code to bind to,
		self.raiseEvent(dEvents.SashDoubleClick, evt)
	
		
	def split(self, dir=None):
		if self.IsSplit():
			return
		if self.Panel1 is None or self.Panel2 is None:
			# No panels, so we can't split
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
	def _setPanel1(self, pnl):
		splt = self.IsSplit()
		if splt:
			self.unsplit(self.__p1)
		if self.__p1:
			self.__p1.Destroy()
		self.__p1 = pnl
		if splt:
			self.split()

	def _getPanel2(self):
		return self.__p2
	def _setPanel2(self, pnl):
		splt = self.IsSplit()
		if splt:
			self.unsplit(self.__p2)
		if self.__p2:
			self.__p2.Destroy()
		self.__p2 = pnl
		if splt:
			self.split()
	
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
	Panel1 = property(_getPanel1, _setPanel1, None,
			"Returns the Top/Left panel.  (SplitterPanel)" )
	Panel2 = property(_getPanel2, _setPanel2, None,
			"Returns the Bottom/Right panel.  (SplitterPanel)" )
	SashPosition = property(_getSashPosition, _setSashPosition, None,
			"Position of the sash when the window is split.  (int)")
			

if __name__ == "__main__":
	import test
	test.Test().runTest(dSplitter)
