# -*- coding: utf-8 -*-
import sys
import wx
import dabo
import dabo.ui

if __name__ == "__main__":
	dabo.ui.loadUI("wx")
import dabo.dEvents as dEvents
from dabo.dLocalize import _
from dPageFrameMixin import dPageFrameMixin

# dDockForm is not available with wxPython < 2.7
_USE_DOCK = (wx.VERSION >= (2, 7))
if _USE_DOCK:
	import wx.aui as aui


def readonly(value):
	""" Create a read-only property. """
	return property(lambda self: value)


class dPageFrame(dPageFrameMixin, wx.Notebook):
	"""Creates a pageframe, which can contain an unlimited number of pages,
	each of which should be a subclass/instance of the dPage class.
	"""
	_evtPageChanged = readonly(wx.EVT_NOTEBOOK_PAGE_CHANGED)
	_evtPageChanging = readonly(wx.EVT_NOTEBOOK_PAGE_CHANGING)
	_tabposBottom = readonly(wx.NB_BOTTOM)
	_tabposRight = readonly(wx.NB_RIGHT)
	_tabposLeft = readonly(wx.NB_LEFT)
	
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dPageFrame
		preClass = wx.PreNotebook
		
		dPageFrameMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)


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
		dPageFrameMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)

		self.Bind(wx.EVT_LIST_ITEM_MIDDLE_CLICK, self.__onWxMiddleClick)
		self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.__onWxRightClick)

	
	def __onWxMiddleClick(self, evt):
		self.raiseEvent(dEvents.MouseMiddleClick, evt)
	

	def __onWxRightClick(self, evt):
		self.raiseEvent(dEvents.MouseRightClick, evt)


	def layout(self):
		"""We need to force the control to adjust the list size."""
		self.GetChildren()[0].InvalidateBestSize()
		self.Layout()
		

	def SetPageText(self, pos, val):
		super(dPageList, self).SetPageText(pos, val)
		# Force the list to re-align the spacing
		self.layout()
		
		
	def _getListSpacing(self):
		return self.GetChildren()[0].GetItemSpacing()[0]

	def _setListSpacing(self, val):
		if self._constructed():
			try:
				self.GetChildren()[0].SetItemSpacing(val)
			except AttributeError:
				dabo.errorLog.write(_("ListSpacing is not supported in wxPython %s") % wx.__version__)
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
		dPageFrameMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
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


if _USE_DOCK:
	class dDockTabs(dPageFrameMixin, aui.AuiNotebook):
		_evtPageChanged = readonly(aui.EVT_AUINOTEBOOK_PAGE_CHANGED)
		_evtPageChanging = readonly(aui.EVT_AUINOTEBOOK_PAGE_CHANGING)
		_tabposBottom = readonly(aui.AUI_NB_BOTTOM)
		_tabposRight = readonly(aui.AUI_NB_RIGHT)
		_tabposLeft = readonly(aui.AUI_NB_LEFT)
		_tabposTop = readonly(aui.AUI_NB_TOP)
	
		def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
			self._baseClass = dDockTabs
			preClass = aui.AuiNotebook
			
			newStyle = (aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT | aui.AUI_NB_TAB_MOVE
					| aui.AUI_NB_SCROLL_BUTTONS | aui.AUI_NB_CLOSE_ON_ALL_TABS)
			if "style" in kwargs:
				newStyle = kwargs["style"] | newStyle
			kwargs["style"] = newStyle
			dPageFrameMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)
	
	
		def insertPage(self, pos, pgCls=None, caption="", imgKey=None,
				ignoreOverride=False):
			""" Insert the page into the pageframe at the specified position, 
			and optionally sets the page caption and image. The image 
			should have already been added to the pageframe if it is 
			going to be set here.
			"""
			# Allow subclasses to potentially override this behavior. This will
			# enable them to handle page creation in their own way. If overridden,
			# the method will return the new page.
			ret = None
			if not ignoreOverride:
				ret = self._insertPageOverride(pos, pgCls, caption, imgKey)
			if ret:
				return ret			
			if pgCls is None:
				pgCls = self.PageClass
			if isinstance(pgCls, dabo.ui.dPage):
				pg = pgCls
			else:
				# See if the 'pgCls' is either some XML or the path of an XML file
				if isinstance(pgCls, basestring):
					xml = pgCls
					from dabo.lib.DesignerXmlConverter import DesignerXmlConverter
					conv = DesignerXmlConverter()
					pgCls = conv.classFromXml(xml)
				pg = pgCls(self)
			if not caption:
				# Page could have its own default caption
				caption = pg._caption
			if imgKey:
				idx = self._imageList[imgKey]
				bmp = self.GetImageList().GetBitmap(idx)
				self.InsertPage(pos, pg, caption=caption, bitmap=bmp)
			else:
				self.InsertPage(pos, pg, caption=caption)
			self.layout()
			return self.Pages[pos]
		def _insertPageOverride(self, pos, pgCls, caption, imgKey): pass
else:
	dDockTabs = dPageFrame
		

import random

class TestMixin(object):
	def initProperties(self):
		self.Width = 400
		self.Height = 175
		self.TabPosition = random.choice(("Top", "Bottom", "Left", "Right"))
	
	def afterInit(self):
		self.appendPage(caption="Introduction")
		self.appendPage(caption="Chapter I")
		self.appendPage(caption="Chapter 2")
		self.appendPage(caption="Chapter 3")
		self.Pages[0].BackColor = "darkred"
		self.Pages[1].BackColor = "darkblue"
		self.Pages[2].BackColor = "green"
		self.Pages[3].BackColor = "yellow"
	
	def onPageChanged(self, evt):
		print "Page number changed from %s to %s" % (evt.oldPageNum, evt.newPageNum)

class _dPageFrame_test(TestMixin, dPageFrame): pass
class _dPageList_test(TestMixin, dPageList): pass
class _dPageSelect_test(TestMixin, dPageSelect): pass
class _dDockTabs_test(TestMixin, dDockTabs): pass


		
if __name__ == "__main__":
	import test
	test.Test().runTest(_dPageFrame_test)
	test.Test().runTest(_dPageList_test)
	test.Test().runTest(_dPageSelect_test)
	test.Test().runTest(_dDockTabs_test)
