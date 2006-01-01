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


class dPageFrame(wx.Notebook, dPageFrameMixin):
	"""Creates a pageframe, which can contain an unlimited number of pages.

	Typically, your pages will descend from dPage, but they can in fact be any
	Dabo visual control, such as a dPanel, dEditBox, etc.
	"""
	_evtPageChanged = readonly(wx.EVT_NOTEBOOK_PAGE_CHANGED)
	_tabposBottom = readonly(wx.NB_BOTTOM)
	_tabposRight = readonly(wx.NB_RIGHT)
	_tabposLeft = readonly(wx.NB_LEFT)
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dPageFrame
		preClass = wx.PreNotebook
		
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		# Dictionary for tracking images by key value
		self._imageList = {}


	def _afterInit(self):
		if sys.platform[:3] == "win":
			## This keeps Pages from being ugly on Windows:
			self.SetBackgroundColour(self.GetBackgroundColour())
		super(dPageFrame, self)._afterInit()


class _dPageFrame_test(dPageFrame):
	def initProperties(self):
		self.Width = 400
		self.Height = 175
	
	def afterInit(self):
		self.appendPage(caption="Introduction")
		self.appendPage(caption="Chapter I")
	
	def onPageChanged(self, evt):
		print "Page number changed from %s to %s" % (evt.oldPageNum, evt.newPageNum)


class dPageList(wx.Listbook, dPageFrameMixin):
	_evtPageChanged = readonly(wx.EVT_LISTBOOK_PAGE_CHANGED)
	_tabposBottom = readonly(wx.LB_BOTTOM)
	_tabposRight = readonly(wx.LB_RIGHT)
	_tabposLeft = readonly(wx.LB_LEFT)
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dPageList
		preClass = wx.PreListbook
		# Dictionary for tracking images by key value
		self._imageList = {}
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)



class dPageSelect(wx.Choicebook, dPageFrameMixin):
	_evtPageChanged = readonly(wx.EVT_CHOICEBOOK_PAGE_CHANGED)
	_tabposBottom = readonly(wx.CHB_BOTTOM)
	_tabposRight = readonly(wx.CHB_RIGHT)
	_tabposLeft = readonly(wx.CHB_LEFT)
	
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dPageSelect
		preClass = wx.PreChoicebook
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
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
		
		
if __name__ == "__main__":
	import test
	test.Test().runTest(_dPageFrame_test)

