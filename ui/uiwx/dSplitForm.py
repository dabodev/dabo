import wx
import dabo
dabo.ui.loadUI("wx")
from dSplitter import dSplitter
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class dSplitForm(dabo.ui.dForm):
	def _afterInit(self):
		win = self.splitter = dSplitter(self, createPanes=True, RegID="MainSplitter")
		super(dSplitForm, self)._afterInit()
		self.Sizer.append1x(win)
		win.Visible = True
		self.layout()


	def unsplit(self):
		self.splitter.unsplit()
		
	
	def split(self, dir=None):
		self.splitter.split(dir)
		

	def _getMinPanelSize(self):
		return self.splitter.MinPanelSize
		
	def _setMinPanelSize(self, val):
		if self._constructed():
			self.splitter.MinPanelSize = val
		else:
			self._properties["MinPanelSize"] = val
	
	
	def _getOrientation(self):
		return self.splitter.Orientation
		
	def _setOrientation(self, val):
		if self._constructed():
			self.splitter.Orientation = val
		else:
			self._properties["MinPanelSize"] = val
	
	
	def _getPanel1(self):
		return self.splitter.Panel1
		
	def _setPanel1(self, pnl):
		if self._constructed():
			self.splitter.Panel1 = pnl
		else:
			self._properties["Panel1"] = pnl
			

	def _getPanel2(self):
		return self.splitter.Panel2
		
	def _setPanel2(self, pnl):
		if self._constructed():
			self.splitter.Panel2 = pnl
		else:
			self._properties["Panel2"] = pnl
	
	
	def _getSashPosition(self):
		return self.splitter.SashPosition
		
	def _setSashPosition(self, val):
		if self._constructed():
			self.splitter.SashPosition = val
		else:
			self._properties["SashPosition"] = val
		
	

	MinPanelSize = property(_getMinPanelSize, _setMinPanelSize, None,
			_("Controls the minimum width/height of the panels.  (int)"))
			
	Orientation = property(_getOrientation, _setOrientation, None,
			_("Determines if the window splits Horizontally or Vertically.  (str)"))
			
	Panel1 = property(_getPanel1, _setPanel1, None,
			_("Returns the Top/Left panel.  (SplitterPanel)"))

	Panel2 = property(_getPanel2, _setPanel2, None,
			_("Returns the Bottom/Right panel.  (SplitterPanel)"))

	SashPosition = property(_getSashPosition, _setSashPosition, None,
			_("Position of the sash when the window is split.  (int)"))



class _dSplitForm_test(dSplitForm):
	def initProperties(self):
		self.Caption = "Splitter Demo"

	def afterInit(self):
		self.splitter.Panel1.BackColor = dabo.dColors.randomColor()
		self.splitter.Panel2.BackColor = dabo.dColors.randomColor()
		
				
if __name__ == "__main__":
	import test
	test.Test().runTest(_dSplitForm_test)
