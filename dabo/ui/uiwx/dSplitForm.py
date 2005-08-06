import wx
import dabo
dabo.ui.loadUI("wx")
import dForm
import dSplitter
import dabo.dEvents as dEvents
from dabo.dLocalize import _

class dSplitForm(dForm.dForm):
	def _afterInit(self):
		super(dSplitForm, self)._afterInit()
		win = dSplitter.dSplitter(self, createPanes=1)
		self.Sizer.append(win, 1, "expand")
		win.Show(True)
		# Store the references
		self.splitter = win
		self.layout()

	def unsplit(self):
		self.splitter.unsplit()
	
	def split(self, dir=None):
		self.splitter.split(dir)
	
	def _getMinPanelSize(self):
		return self.splitter.MinPanelSize
	def _setMinPanelSize(self, val):
		self.splitter.MinPanelSize = val
	
	def _getOrientation(self):
		return self.splitter.Orientation
	def _setOrientation(self, val):
		self.splitter.Orientation = val
	
	def _getSashPosition(self):
		return self.splitter.SashPosition
	def _setSashPosition(self, val):
		self.splitter.SashPosition = val
	
	MinPanelSize = property(_getMinPanelSize, _setMinPanelSize, None,
			"Controls the minimum width/height of the panels.  (int)")
	Orientation = property(_getOrientation, _setOrientation, None,
			"Determines if the window splits Horizontally or Vertically.  (string)")
	SashPosition = property(_getSashPosition, _setSashPosition, None,
			"Position of the sash when the window is split.  (int)")


if __name__ == "__main__":
	import test
	test.Test().runTest(dSplitForm)

