import dabo
import wx
import	wx.lib.mixins.listctrl	as ListMixin

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dDataControlMixin as dcm
import dabo.dEvents as dEvents
from dabo.dLocalize import _


class dListControl(wx.ListCtrl, dcm.dDataControlMixin, 
					ListMixin.ListCtrlAutoWidthMixin):
	""" Mostly copied from the wxDemo. The mixin allows the 
	rightmost column to expand as the control is resized.
	
	This class as it stands is pretty incomplete, but it works well enough
	for the property sheet in the designer. Before including it in the
	general Dabo set of controls, we will need to streamline the adding
	of items, sorting, etc. - all the things that this control can do.
	"""
	_IsContainer = False
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dListControl
		
		try:
			style = style | wx.LC_REPORT | wx.LC_SINGLE_SEL
		except:
			style = wx.LC_REPORT | wx.LC_SINGLE_SEL
		preClass = wx.PreListCtrl
		dcm.dDataControlMixin.__init__(self, preClass, parent, properties, style=style, *args, **kwargs)
		ListMixin.ListCtrlAutoWidthMixin.__init__(self)
		self._selIndex = 0


	def _initEvents(self):
		super(dListControl, self)._initEvents()
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.__onSelection)
		self.Bind(wx.EVT_LIST_KEY_DOWN, self.__onWxKeyDown)
		self.bindEvent(dEvents.Hit, self.onHit)
	
	
	def __onSelection(self, evt):
		self._selIndex = evt.GetIndex()
		# Call the default Hit code
		self._onWxHit(evt)
	
	def onHit(self, evt): pass
	
	def __onWxKeyDown(self, evt):
		self.raiseEvent(dEvents.KeyDown, evt)
		
	def _getSelected(self):
		ret = []
		pos = -1
		while True:
			indx = self.GetNextItem(pos, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
			if indx == -1:
				break
			pos = indx
			ret.append(indx)
		return ret
	def _setSelected(self, selList):
		for id in selList:
			self.SetItemState(id, wx.LIST_STATE_SELECTED, 
					wx.LIST_STATE_SELECTED)


	def _getValue(self):
		ret = None
		try:
			ret = self.GetItemText(self._selIndex)
		except: pass
		return ret
	def _setValue(self, val):
		if type(val) == int:
			self.Select(val)
		elif type(val) in (str, unicode):
			self.Select(self.FindItem(-1, val))

	SelectedIndices = property(_getSelected, _setSelected, None, 
			"Returns a list of selected row indices.  (list of int)")
			
	Value = property(_getValue, _setValue, None,
		"Returns current value (str)" )
		
		
			
if __name__ == "__main__":
	import test
	
	class TestListControl(dListControl):
		def afterInit(self):
			self.InsertColumn(0, "Main Column")
			self.InsertColumn(1, "Another Column")
			row = 0
			self.InsertStringItem(row, "First Line")
			self.SetStringItem(row, 1, "111")
			row += 1
			self.InsertStringItem(row, "Second Line")
			self.SetStringItem(row, 1, "222")
			row += 1
			self.InsertStringItem(row, "Third Line")
			self.SetStringItem(row, 1, "333")
			row += 1
			self.InsertStringItem(row, "Fourth Line")
			self.SetStringItem(row, 1, "444")
			row += 1
			self.InsertStringItem(row, "Fifth Line")
			self.SetStringItem(row, 1, "5.55")
			row += 1
			self.SetColumnWidth(0, 150)
			self.SetColumnWidth(1, wx.LIST_AUTOSIZE)
		
		def onHit(self, evt):
			print "HIT!", self.Value
		
	test.Test().runTest(TestListControl)
