# -*- coding: utf-8 -*-
import sys
import wx
import dabo
import dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")

import dControlMixin as cm
import dPage
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dPageFrameMixin import dPageFrameMixin


def readonly(value):
	""" Create a read-only property. """
	return property(lambda self: value)


class dPageFrame(dPageFrameMixin, wx.Notebook):
	"""Creates a pageframe, which can contain an unlimited number of pages.

	Typically, your pages will descend from dPage, but they can in fact be any
	Dabo visual control, such as a dPanel, dEditBox, etc.
	"""
	_evtPageChanged = readonly(wx.EVT_NOTEBOOK_PAGE_CHANGED)
	_evtPageChanging = readonly(wx.EVT_NOTEBOOK_PAGE_CHANGING)
	_tabposBottom = readonly(wx.NB_BOTTOM)
	_tabposRight = readonly(wx.NB_RIGHT)
	_tabposLeft = readonly(wx.NB_LEFT)
	
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dPageFrame
		preClass = wx.PreNotebook
		
		cm.dControlMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
		# Dictionary for tracking images by key value
		self._imageList = {}


	def _afterInit(self):
		if sys.platform[:3] == "win":
			## This keeps Pages from being ugly on Windows:
			self.SetBackgroundColour(self.GetBackgroundColour())
		super(dPageFrame, self)._afterInit()



class dPageList(dPageFrameMixin, wx.Listbook):
	_evtPageChanged = readonly(wx.EVT_LISTBOOK_PAGE_CHANGED)
	_evtPageChanging = readonly(wx.EVT_LISTBOOK_PAGE_CHANGING)
	_tabposBottom = readonly(wx.LB_BOTTOM)
	_tabposRight = readonly(wx.LB_RIGHT)
	_tabposLeft = readonly(wx.LB_LEFT)
	
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dPageList
		preClass = wx.PreListbook
		# Dictionary for tracking images by key value
		self._imageList = {}
		cm.dControlMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
		self.Bind(wx.EVT_LIST_ITEM_MIDDLE_CLICK, self.__onWxMiddleClick)
		self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.__onWxRightClick)

	
	def __onWxMiddleClick(self, evt):
		self.raiseEvent(dEvents.MouseMiddleClick, evt)
	

	def __onWxRightClick(self, evt):
		self.raiseEvent(dEvents.MouseRightClick, evt)


	def SetPageText(self, pos, val):
		super(dPageList, self).SetPageText(pos, val)
		# Force the list to re-align the spacing
		self.ListSpacing = self.ListSpacing
		
		
	def _getListSpacing(self):
		return self.GetChildren()[0].GetItemSpacing()[0]

	def _setListSpacing(self, val):
		if self._constructed():
			self.GetChildren()[0].SetItemSpacing(val)
		else:
			self._properties["ListSpacing"] = val


	ListSpacing = property(_getListSpacing, _setListSpacing, None,
			_("Controls the spacing of the items in the controlling list  (int)"))
	


class dPageSelect(dPageFrameMixin, wx.Choicebook):
	_evtPageChanged = readonly(wx.EVT_CHOICEBOOK_PAGE_CHANGED)
	_evtPageChanging = readonly(wx.EVT_CHOICEBOOK_PAGE_CHANGING)
	_tabposBottom = readonly(wx.CHB_BOTTOM)
	_tabposRight = readonly(wx.CHB_RIGHT)
	_tabposLeft = readonly(wx.CHB_LEFT)
	
	
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dPageSelect
		preClass = wx.PreChoicebook
		cm.dControlMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
		# Dictionary for tracking images by key value
		self._imageList = {}


	def SetPageText(self, pg, tx):
		"""Need to override this because this is not implemented yet
		on the Mac, at least as of wxPython 2.5.5.1
		"""
		# Get a reference to the Choice control
		dd = self.GetChildren()[0]
		# Save the current position
		pos = dd.GetSelection()
		# Get the current contents
		choices = [dd.GetString(n) for n in range(dd.GetCount()) ]
		choices[pg] = tx
		dd.Clear()
		dd.AppendItems(choices)
		dd.SetSelection(pos)
		

import random
class _dPageFrame_test(dPageFrame):
	def initProperties(self):
		self.Width = 400
		self.Height = 175
		self.TabPosition = random.choice(("Top", "Bottom", "Left", "Right"))
	
	def afterInit(self):
		self.appendPage(caption="Introduction")
		self.appendPage(caption="Chapter I")
		self.Pages[0].BackColor = "darkred"
		self.Pages[1].BackColor = "darkblue"
	
	def onPageChanged(self, evt):
		print "Page number changed from %s to %s" % (evt.oldPageNum, evt.newPageNum)


class _dPageList_test(dPageList):
	def initProperties(self):
		self.Width = 400
		self.Height = 175
		self.TabPosition = random.choice(("Top", "Bottom", "Left", "Right"))
	
	def afterInit(self):
		self.appendPage(caption="Introduction")
		self.appendPage(caption="Chapter I")
		self.Pages[0].BackColor = "darkred"
		self.Pages[1].BackColor = "darkblue"
	
	def onPageChanged(self, evt):
		print "Page number changed from %s to %s" % (evt.oldPageNum, evt.newPageNum)


class _dPageSelect_test(dPageSelect):
	def initProperties(self):
		self.Width = 400
		self.Height = 175
		self.TabPosition = random.choice(("Top", "Bottom", "Left", "Right"))
	
	def afterInit(self):
		self.appendPage(caption="Introduction")
		self.appendPage(caption="Chapter I")
		self.Pages[0].BackColor = "darkred"
		self.Pages[1].BackColor = "darkblue"
	
	def onPageChanged(self, evt):
		print "Page number changed from %s to %s" % (evt.oldPageNum, evt.newPageNum)


		
if __name__ == "__main__":
	import test
	test.Test().runTest(_dPageFrame_test)
	test.Test().runTest(_dPageList_test)
	test.Test().runTest(_dPageSelect_test)

