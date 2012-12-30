# -*- coding: utf-8 -*-
import wx
import dabo
from dabo.ui import makeDynamicProperty
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dSplitter import dSplitter
import dabo.dColors as dColors
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class dSplitForm(dabo.ui.dForm):
	def __init__(self, *args, **kwargs):
		self._splitter = None
		super(dSplitForm, self).__init__(*args, **kwargs)


	def unsplit(self):
		self.Splitter.unsplit()


	def split(self, dir=None):
		self.Splitter.split(dir)


	def _getMinPanelSize(self):
		return self.Splitter.MinPanelSize

	def _setMinPanelSize(self, val):
		if self._constructed():
			self.Splitter.MinPanelSize = val
		else:
			self._properties["MinPanelSize"] = val


	def _getOrientation(self):
		return self.Splitter.Orientation

	def _setOrientation(self, val):
		if self._constructed():
			self.Splitter.Orientation = val
		else:
			self._properties["MinPanelSize"] = val


	def _getPanel1(self):
		return self.Splitter.Panel1

	def _setPanel1(self, pnl):
		if self._constructed():
			self.Splitter.Panel1 = pnl
		else:
			self._properties["Panel1"] = pnl


	def _getPanel2(self):
		return self.Splitter.Panel2

	def _setPanel2(self, pnl):
		if self._constructed():
			self.Splitter.Panel2 = pnl
		else:
			self._properties["Panel2"] = pnl


	def _getSashPosition(self):
		return self.Splitter.SashPosition

	def _setSashPosition(self, val):
		if self._constructed():
			self.Splitter.SashPosition = val
		else:
			self._properties["SashPosition"] = val


	def _getSplitter(self):
		if self._splitter is None:
			win = self._splitter = dSplitter(self, createPanes=True, createSizers=True,
					RegID="MainSplitter")
			def addToSizer(frm, itm):
				if not frm.Sizer:
					dabo.ui.callAfter(addToSizer, frm, itm)
				else:
					frm.Sizer.append1x(itm)
					frm.layout()
			win.Visible = True
			dabo.ui.callAfter(addToSizer, self, win)
		return self._splitter



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

	Splitter = property(_getSplitter, None, None,
			_("Reference to the main splitter in the form  (dSplitter"))



	DynamicMinPanelSize = makeDynamicProperty(MinPanelSize)
	DynamicOrientation = makeDynamicProperty(Orientation)
	DynamicSashPosition = makeDynamicProperty(SashPosition)


class _dSplitForm_test(dSplitForm):
	def initProperties(self):
		self.Caption = "Splitter Demo"

	def afterInit(self):
		self.Splitter.Panel1.BackColor = dColors.randomColor()
		self.Splitter.Panel2.BackColor = dColors.randomColor()


if __name__ == "__main__":
	import test
	test.Test().runTest(_dSplitForm_test)
