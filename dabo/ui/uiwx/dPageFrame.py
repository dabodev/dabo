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
import dabo.dColors as dColors

import wx.aui as aui

#The flatnotebook version we need is not avialable with wxPython < 2.8.4
_USE_FLAT = (wx.VERSION >= (2, 8, 4))
if _USE_FLAT:
	#The Editra flatnotebook module takes care of the Nav Buttons and Dropdown Tab List
	#overlap problem, so we try to import that module first.  If that doesn't
	#Why wxPython doesn't fold this flatnotebook module into the main one is beyond me...
	try:
		import wx.tools.Editra.src.extern.flatnotebook as fnb
		_USE_EDITRA = True
	except ImportError:
		if (wx.VERSION >= (2, 8, 9, 2)):
			import wx.lib.agw.flatnotebook as fnb
		else:
			import wx.lib.flatnotebook as fnb
		_USE_EDITRA = False


def readonly(value):
	""" Create a read-only property. """
	return property(lambda self: value)

class dPageFrame(dPageFrameMixin, wx.Notebook):
	"""Creates a pageframe, which can contain an unlimited number of pages,
	each of which should be a subclass/instance of the dPage class.
	"""
	_evtPageChanged = readonly(wx.EVT_NOTEBOOK_PAGE_CHANGED)
	_evtPageChanging = readonly(wx.EVT_NOTEBOOK_PAGE_CHANGING)
	_tabposTop = readonly(wx.NB_TOP)
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


class dPageToolBar(dPageFrameMixin, wx.Toolbook):
	_evtPageChanged = readonly(wx.EVT_TOOLBOOK_PAGE_CHANGED)
	_evtPageChanging = readonly(wx.EVT_TOOLBOOK_PAGE_CHANGING)
	_tabposTop = readonly(wx.BK_TOP)
	_tabposBottom = readonly(wx.BK_BOTTOM)
	_tabposRight = readonly(wx.BK_RIGHT)
	_tabposLeft = readonly(wx.BK_LEFT)

	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		self._baseClass = dPageToolBar
		preClass = wx.PreToolbook

		dPageFrameMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)

	def _afterInit(self):
		if sys.platform[:3] == "win":
			## This keeps Pages from being ugly on Windows:
			self.SetBackgroundColour(self.GetBackgroundColour())

		il = wx.ImageList(32, 32, initialCount=0)	#Need to set image list first or else we get and error...
		self.AssignImageList(il)
		super(dPageToolBar, self)._afterInit()


class dPageList(dPageFrameMixin, wx.Listbook):
	_evtPageChanged = readonly(wx.EVT_LISTBOOK_PAGE_CHANGED)
	_evtPageChanging = readonly(wx.EVT_LISTBOOK_PAGE_CHANGING)
	_tabposBottom = readonly(wx.LB_BOTTOM)
	_tabposTop = readonly(wx.LB_TOP)
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
				# Changed this to write to the info log to avoid error messages that
				#  unnecessarily exaggerate the problem.
				dabo.infoLog.write(_("ListSpacing is not supported in wxPython %s") % wx.__version__)
		else:
			self._properties["ListSpacing"] = val


	ListSpacing = property(_getListSpacing, _setListSpacing, None,
			_("Controls the spacing of the items in the controlling list  (int)"))



class dPageSelect(dPageFrameMixin, wx.Choicebook):
	_evtPageChanged = readonly(wx.EVT_CHOICEBOOK_PAGE_CHANGED)
	_evtPageChanging = readonly(wx.EVT_CHOICEBOOK_PAGE_CHANGING)
	_tabposTop = readonly(wx.CHB_TOP)
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


if _USE_FLAT:
	class dPageStyled(dPageFrameMixin, fnb.FlatNotebook):
		"""Creates a pageframe, which can contain an unlimited number of pages,
		each of which should be a subclass/instance of the dPage class.
		"""
		_evtPageChanged = readonly(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED)
		_evtPageChanging = readonly(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING)
		_tabposBottom = readonly(fnb.FNB_BOTTOM)

		def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
			self._baseClass = dPageStyled
			preClass = fnb.FlatNotebook

			self._inactiveTabTextColor = None
			self._menuBackColor = None
			self._showDropdownTabList = False
			self._showMenuCloseButton = True
			self._showMenuOnSingleTab = True
			self._showNavButtons = True
			self._showPageCloseButtons = False
			self._tabSideIncline = 0
			self._tabStyle = "Default"

			dPageFrameMixin.__init__(self, preClass, parent, properties, attProperties, *args, **kwargs)

		def _initEvents(self):
			super(dPageStyled, self)._initEvents()
			self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.__onPageClosing)
			self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSED, self.__onPageClosed)
			self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CONTEXT_MENU, self.__onPageContextMenu)

		def _afterInit(self):
			if sys.platform[:3] == "win":
				## This keeps Pages from being ugly on Windows:
				self.SetBackgroundColour(self.GetBackgroundColour())
			super(dPageStyled, self)._afterInit()

		def __onPageClosing(self, evt):
			"""The page has not yet been closed, so we can veto it if conditions call for it."""
			pageNum = evt.GetSelection()
			if self._beforePageClose(pageNum) is False:
				evt.Veto()
			else:
				evt.Skip()
			self.raiseEvent(dEvents.PageClosing, pageNum=pageNum)

		def _beforePageClose(self, page):
			return self.beforePageClose(page)

		def insertPage(self, *args, **kwargs):
			page = super(dPageStyled, self).insertPage(*args, **kwargs)
			self.SetAllPagesShapeAngle(self._tabSideIncline)	#incline isn't autoset on new page add so set it
			return page


		def beforePageClose(self, page):
			"""Return False from this method to prevent the page from closing."""
			pass

		def __onPageClosed(self, evt):
			self.raiseEvent(dEvents.PageClosed)

		def __onPageContextMenu(self, evt):
			self.GetPage(self.GetSelection()).raiseEvent(dEvents.PageContextMenu)

		#Property getters and setters
		def _getActiveTabTextColor(self):
			return self._activeTabTextColor

		def _setActiveTabTextColor(self, val):
			if self._constructed():
				self._activeTabTextColor = val
				if isinstance(val, basestring):
					val = dColors.colorTupleFromName(val)
				if isinstance(val, tuple):
					self.SetActiveTabTextColour(wx.Colour(*val))
					self.Refresh()
				else:
					raise ValueError(_("'%s' can not be translated into a color" % val))
			else:
				self._properties["ActiveTabTextColor"] = val


		def _getInactiveTabTextColor(self):
			return self._inactiveTabTextColor

		def _setInactiveTabTextColor(self, val):
			if self._constructed():
				self._inactiveTabTextColor = val
				if isinstance(val, basestring):
					val = dColors.colorTupleFromName(val)
				if isinstance(val, tuple):
					self.SetNonActiveTabTextColour(wx.Colour(*val))
					self.Refresh()
				else:
					raise ValueError(_("'%s' can not be translated into a color" % val))
			else:
				self._properties["InactiveTabTextColor"] = val


		def _getMenuBackColor(self):
			return self._menuBackColor

		def _setMenuBackColor(self, val):
			if self._constructed():
				self._menuBackColor = val
				if isinstance(val, basestring):
					val = dColors.colorTupleFromName(val)
				if isinstance(val, tuple):
					self.SetTabAreaColour(wx.Colour(*val))
					self.Refresh()
				else:
					raise ValueError(_("'%s' can not be translated into a color" % val))
			else:
				self._properties["MenuBackColor"] = val


		def _getShowDropdownTabList(self):
			return self._showDropdownTabList

		def _setShowDropdownTabList(self, val):
			val = bool(val)
			if val:
				self._addWindowStyleFlag(fnb.FNB_DROPDOWN_TABS_LIST)
				if not _USE_EDITRA:
					self._addWindowStyleFlag(fnb.FNB_NO_NAV_BUTTONS)
					self._showNavButtons = False
			else:
				self._delWindowStyleFlag(fnb.FNB_DROPDOWN_TABS_LIST)

			self._showDropdownTabList = val


		def _getShowMenuCloseButton(self):
			return self._showMenuCloseButton

		def _setShowMenuCloseButton(self, val):
			val = bool(val)
			if val:
				self._delWindowStyleFlag(fnb.FNB_NO_X_BUTTON)
			else:
				self._addWindowStyleFlag(fnb.FNB_NO_X_BUTTON)
			self._showMenuCloseButton = val


		def _getShowMenuOnSingleTab(self):
			return self._showMenuOnSingleTab

		def _setShowMenuOnSingleTab(self, val):
			val = bool(val)
			if val:
				self._delWindowStyleFlag(fnb.FNB_HIDE_ON_SINGLE_TAB)
			else:
				self._addWindowStyleFlag(fnb.FNB_HIDE_ON_SINGLE_TAB)
			self._showMenuOnSingleTab = val


		def _getShowNavButtons(self):
			return self._showNavButtons

		def _setShowNavButtons(self, val):
			val = bool(val)
			if val:
				self._delWindowStyleFlag(fnb.FNB_NO_NAV_BUTTONS)
				if not _USE_EDITRA:
					self._delWindowStyleFlag(fnb.FNB_DROPDOWN_TABS_LIST)
					self._showDropdownTabList = False
			else:
				self._addWindowStyleFlag(fnb.FNB_NO_NAV_BUTTONS)
			self._showNavButtons = val


		def _getShowPageCloseButtons(self):
			return self._showPageCloseButtons

		def _setShowPageCloseButtons(self, val):
			val = bool(val)
			if val:
				self._addWindowStyleFlag(fnb.FNB_X_ON_TAB)
			else:
				self._delWindowStyleFlag(fnb.FNB_X_ON_TAB)
			self._showPageCloseButtons = val


		def _getTabPosition(self):
			if self._hasWindowStyleFlag(self._tabposBottom):
				return "Bottom"
			else:
				return "Top"

		def _setTabPosition(self, val):
			val = str(val)
			self._delWindowStyleFlag(self._tabposBottom)

			if val == "Top":
				pass
			elif val == "Bottom":
				self._addWindowStyleFlag(self._tabposBottom)
			else:
				raise ValueError(_("The only possible values are 'Top' and 'Bottom'"))


		def _getTabSideIncline(self):
			return self._tabSideIncline

		def _setTabSideIncline(self, val):
			val = int(val)
			if val<0 or val>15:
				raise ValueError(_("Value must be 0 through 15"))

			self._tabSideIncline = val
			self.SetAllPagesShapeAngle(val)


		def _getTabStyle(self):
			return self._tabStyle

		def _setTabStyle(self, val):
			self._delWindowStyleFlag(fnb.FNB_VC8)
			self._delWindowStyleFlag(fnb.FNB_VC71)
			self._delWindowStyleFlag(fnb.FNB_FANCY_TABS)
			self._delWindowStyleFlag(fnb.FNB_FF2)

			if val == "Default":
				pass
			elif val == "VC8":
				self._addWindowStyleFlag(fnb.FNB_VC8)
			elif val == "VC71":
				self._addWindowStyleFlag(fnb.FNB_VC71)
			elif val == "Fancy":
				self._addWindowStyleFlag(fnb.FNB_FANCY_TABS)
			elif val == "Firefox":
				self._addWindowStyleFlag(fnb.FNB_FF2)
			else:
				raise ValueError(_("The only possible values are 'Default' and 'VC8', 'VC71', 'Fancy', or 'Firefox'"))

			self._tabStyle = val


		#Property definitions
		ActiveTabTextColor = property(_getActiveTabTextColor, _setActiveTabTextColor, None,
			_("""Specifies the color of the text of the active tab (str or 3-tuple) (Default=None)
				Note, is not visible with the 'VC8' TabStyle"""))

		InactiveTabTextColor = property(_getInactiveTabTextColor, _setInactiveTabTextColor, None,
			_("""Specifies the color of the text of non active tabs (str or 3-tuple) (Default=None)
				Note, is not visible with the 'VC8' TabStyle"""))

		MenuBackColor = property(_getMenuBackColor, _setMenuBackColor, None,
			_("""Specifies the background color of the menu (str or 3-tuple) (Default=None)
				Note, is not visible with 'VC71' TabStyle."""))

		ShowDropdownTabList = property(_getShowDropdownTabList, _setShowDropdownTabList, None,
				_("""Specifies whether the dropdown tab list button is visible in the menu (bool) (Default=False)
				Setting this property to True will set ShowNavButtons to False"""))

		ShowMenuCloseButton = property(_getShowMenuCloseButton, _setShowMenuCloseButton, None,
				_("Specifies whether the close button is visible in the menu (bool) (Default=True)"))

		ShowMenuOnSingleTab = property(_getShowMenuOnSingleTab, _setShowMenuOnSingleTab, None,
				_("Specifies whether the tab thumbs and nav buttons are shown when there is a single tab. (bool) (Default=True)"))

		ShowPageCloseButtons = property(_getShowPageCloseButtons, _setShowPageCloseButtons, None,
				_("Specifies whether the close button is visible on the page tab (bool) (Default=False)"))

		ShowNavButtons = property(_getShowNavButtons, _setShowNavButtons, None,
				_("""Specifies whether the left and right nav buttons are visible in the menu (bool) (Default=True)
				Setting this property to True will set ShowDropdownTabList to False"""))

		TabPosition = property(_getTabPosition, _setTabPosition, None,
				_("""Specifies where the page tabs are located. (string)
					Top (default)
					Bottom""") )

		TabSideIncline = property(_getTabSideIncline, _setTabSideIncline, None,
				_("""Specifies the incline of the sides of the tab in degrees (int) (Default=0)
					Acceptable values are 0  - 15.
					Note this property will have no effect on TabStyles other than Default.
					"""))

		TabStyle = property(_getTabStyle, _setTabStyle, None,
				_("""Specifies the style of the display tabs. (string)
					"Default" (default)
					"VC8"
					"VC71"
					"Fancy"
					"Firefox\""""))


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

class _dPageToolBar_test(TestMixin, dPageToolBar):
	def afterInit(self):
		self.addImage("themes/tango/32x32/actions/go-previous.png", "Left")
		self.addImage("themes/tango/32x32/actions/go-next.png", "Right")
		self.addImage("themes/tango/32x32/actions/go-up.png", "Up")
		self.addImage("themes/tango/32x32/actions/go-down.png", "Down")
		self.appendPage(caption="Introduction", imgKey="Left")
		self.appendPage(caption="Chapter I", imgKey="Right")
		self.appendPage(caption="Chapter 2", imgKey="Up")
		self.appendPage(caption="Chapter 3", imgKey="Down")
		self.Pages[0].BackColor = "darkred"
		self.Pages[1].BackColor = "darkblue"
		self.Pages[2].BackColor = "green"
		self.Pages[3].BackColor = "yellow"

class _dPageFrame_test(TestMixin, dPageFrame): pass
class _dPageList_test(TestMixin, dPageList): pass
class _dPageSelect_test(TestMixin, dPageSelect): pass
class _dDockTabs_test(TestMixin, dDockTabs): pass
if _USE_FLAT:
	class _dPageStyled_test(TestMixin, dPageStyled):
		def initProperties(self):
			self.Width = 400
			self.Height = 175
			self.TabStyle = random.choice(("Default", "VC8", "VC71", "Fancy", "Firefox"))
			self.TabPosition = random.choice(("Top", "Bottom"))
			self.ShowPageCloseButtons = random.choice(("True", "False"))
			self.ShowDropdownTabList = random.choice(("True", "False"))
			self.ShowMenuClose = random.choice(("True", "False"))
			self.ShowMenuOnSingleTab = random.choice(("True", "False"))
			self.MenuBackColor = random.choice(dColors.colors)
			self.InactiveTabTextColor = random.choice(dColors.colors)
			self.ActiveTabTextColor = random.choice(dColors.colors)



if __name__ == "__main__":
	import test
	test.Test().runTest(_dPageFrame_test)
	test.Test().runTest(_dPageToolBar_test)
	test.Test().runTest(_dPageList_test)
	test.Test().runTest(_dPageSelect_test)
	test.Test().runTest(_dDockTabs_test)
	if _USE_FLAT:
		test.Test().runTest(_dPageStyled_test)
