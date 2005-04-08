import wx, dabo, dabo.ui
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


class dPageList(wx.Listbook, dPageFrameMixin):
	_evtPageChanged = readonly(wx.EVT_LISTBOOK_PAGE_CHANGED)
	_tabposBottom = readonly(wx.LB_BOTTOM)
	_tabposRight = readonly(wx.LB_RIGHT)
	_tabposLeft = readonly(wx.LB_LEFT)
	
	def __init__(self, parent, properties=None, *args, **kwargs):
		self._baseClass = dPageList
		preClass = wx.PreListbook
		cm.dControlMixin.__init__(self, preClass, parent, properties, *args, **kwargs)
		# Dictionary for tracking images by key value
		self._imageList = {}


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
# 		
# class dPageFrame(dNotebookFrame, dPageFrameMixin):
# 	pass
