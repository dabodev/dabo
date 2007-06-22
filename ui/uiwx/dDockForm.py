# -*- coding: utf-8 -*-
import wx
import wx.aui as aui
PaneInfo = aui.AuiPaneInfo
import dabo
if __name__ == "__main__":
	dabo.ui.loadUI("wx")
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from dabo.ui import makeDynamicProperty


class _dDockManager(aui.AuiManager):
	def __init__(self, win):
		super(_dDockManager, self).__init__(win)


	def addPane(self, win, name=None, typ=None, caption=None):
		pi = PaneInfo()
		if name is not None:
			pi = pi.Name(name)
		if caption is not None:
			pi = pi.Caption(caption)
		if typ:
			lt = typ[0].lower()
			if lt == "c":
				# Center
				pi = pi.CenterPane()
			elif lt == "t":
				# Toolbar
				pi = pi.ToolbarPane()
		self.AddPane(win, pi)
		ret = self.GetAllPanes()[-1]
		dabo.ui.callAfterInterval(100, self.Update)
		return ret


	def runUpdate(self):
		win = self.GetManagedWindow()
		if not win or win._finito:
			return
		self.Update()



class _dDockPanel(dabo.ui.dPanel):
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		pname = self._extractKey(kwargs, "name", "")
		pcapUp = self._extractKey(kwargs, "Caption", "")
		pcap = self._extractKey(kwargs, "caption", "")
		ptype = self._extractKey(kwargs, "typ", "")
		kwargs["NameBase"] = pname
		if pcapUp:
			kwargs["Caption"] = pcapUp
		else:
			kwargs["Caption"] = pcap
		self._paramType = ptype

		# Initialize attributes that underly properties
		self._bottomDockable = True
		self._leftDockable = True
		self._rightDockable = True
		self._topDockable = True
		self._floatable = True
		self._floatingPosition = (0, 0)
		self._floatingSize = (100, 100)
		self._destroyOnClose = False
		self._movable = True
		self._resizable = True
		self._showBorder = True
		self._showCaption = True
		self._showCloseButton = True
		self._showGripper = False
		self._showMaximizeButton = False
		self._showMinimizeButton = False
		self._showPinButton = True
		super(_dDockPanel, self).__init__(parent, properties, attProperties, *args, **kwargs)
		if self.Floating:
			self._floatingPosition = self.GetParent().GetPosition().Get()
			self._floatingSize = self.GetParent().GetSize().Get()


	def float(self):
		"""Float the panel if it isn't already floating."""
		if self.Floating or not self.Floatable:
			return
		self.__pi.Float()
		self.Form._refreshState()


	def dock(self, side=None):
		"""Dock the panel. If side is specified, it is docked on that side of the
		form. If no side is specified, it is docked in its default location.
		"""
		if self.Docked or not self.Dockable:
			return
		inf = self.__pi
		if side is not None:
			s = side[0].lower()
			func = {"l": inf.Left, "r": inf.Right, "t": inf.Top, "b": inf.Bottom}.get(s, None)
			if func:
				func()
			else:
				dabo.logError(_("Invalid dock position: '%s'.") % side)
		inf.Dock()
		self.Form._refreshState()

    def SetFlag(self, flag, option):
        if flag == optionFloating and not option:
            raise dEvents.Pane_Docking
        elif flag == optionFloating and option:
            raise dEvents.Pane_Undocking

        super(_dDockPanel, self).SetFlag(flag, option)

	def _beforeSetProperties(self, props):
		"""Some properties of Floating panels cannot be set at the usual
		point in the process, since the panel will still be docked, and you
		can't change dimensions/location of a docked panel. So extract
		them now, and then set them afterwards.
		"""
		self._propDelayDict = {}
		for delayed in ("Left", "Right", "Top", "Bottom", "Width", "Height"):
			val = self._extractKey(props, delayed)
			if val:
				self._propDelayDict[delayed] = val
		return super(_dDockPanel, self)._beforeSetProperties(props)


	def _setProperties(self, props):
		frm = self.Form
		self.__pi = frm._mgr.addPane(self, name=props["NameBase"],
				typ=self._paramType, caption=props["Caption"])
		del self._paramType
		self.__pi.MinSize((50,50))
		super(_dDockPanel, self)._setProperties(props)


	def _afterSetProperties(self):
		if self._propDelayDict:
			self.setProperties(self._propDelayDict)
		del self._propDelayDict


	def __getPosition(self):
		if self.Floating:
			obj = self.GetParent()
		else:
			obj = self
		return obj.GetPosition().Get()


	def __getSize(self):
		if self.Floating:
			obj = self.GetParent()
		else:
			obj = self
		return obj.GetSize().Get()


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getBottom(self):
		return self.__getPosition()[1] + self.__getSize()[1]

	def _setBottom(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingBottom = val
			else:
				dabo.logError(_("Cannot set the position of a docked panel"))
		else:
			self._properties["Bottom"] = val


	def _getBottomDockable(self):
		return self._bottomDockable

	def _setBottomDockable(self, val):
		if self._constructed():
			self.__pi.BottomDockable(val)
			self.Form._refreshState()
		else:
			self._properties["BottomDockable"] = val


	def _getCaption(self):
		try:
			return self._caption
		except:
			self._caption = ""
			return self._caption

	def _setCaption(self, val):
		if self._constructed():
			self._caption = val
			self.__pi.Caption(val)
			self.Form._refreshState()
		else:
			self._properties["Caption"] = val


	def _getDestroyOnClose(self):
		return self._destroyOnClose

	def _setDestroyOnClose(self, val):
		if self._constructed():
			self._destroyOnClose = val
			self.__pi.DestroyOnClose(val)
			self.Form._refreshState()
		else:
			self._properties["DestroyOnClose"] = val


	def _getDockable(self):
		return self._bottomDockable or self._leftDockable or self._rightDockable or self._topDockable

	def _setDockable(self, val):
		if self._constructed():
			self._dockable = val
			self.__pi.Dockable(val)
			self.Form._refreshState()
		else:
			self._properties["Dockable"] = val


	def _getDocked(self):
		return self.__pi.IsDocked()

	def _setDocked(self, val):
		if self._constructed():
			curr = self.__pi.IsDocked()
			chg = False
			if val and not curr:
				self.__pi.Dock()
				chg = True
			elif not val and curr:
				self.__pi.Float()
				chg = True
			if chg:
				self.Form._refreshState()
		else:
			self._properties["Docked"] = val


	def _getDockSide(self):
		return {1: "Top", 2: "Right", 3: "Bottom", 4: "Left"}[self.__pi.dock_direction]

	def _setDockSide(self, val):
		if self._constructed():
			vUp = val[0].upper()
			self.__pi.dock_direction = {"T": 1, "R": 2, "B": 3, "L": 4}[vUp]
			self.Form._refreshState()
		else:
			self._properties["DockSide"] = val


	def _getFloatable(self):
		return self._floatable

	def _setFloatable(self, val):
		if self._constructed():
			self._floatable = val
			self.__pi.Floatable(val)
			self.Form._refreshState()
		else:
			self._properties["Floatable"] = val


	def _getFloating(self):
		return self.__pi.IsFloating()

	def _setFloating(self, val):
		if self._constructed():
			curr = self.__pi.IsFloating()
			chg = False
			if val and not curr:
				self.__pi.Float()
				chg = True
			elif not val and curr:
				self.__pi.Dock()
				chg = True
			if chg:
				self.Form._refreshState()
		else:
			print dir(self)
			self._properties["Floating"] = val


	def _getFloatingBottom(self):
		return self.FloatingPosition[1] + self.FloatingSize[1]

	def _setFloatingBottom(self, val):
		if self._constructed():
			ht = self.FloatingSize[1]
			self._floatingPosition = (self.FloatingPosition[0], val - ht)
			self.__pi.FloatingPosition(self._floatingPosition)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingBottom"] = val


	def _getFloatingHeight(self):
		return self.FloatingSize[1]

	def _setFloatingHeight(self, val):
		if self._constructed():
			self._floatingSize = (self.FloatingSize[0], val)
			if self.__pi.IsFloating():
				self.GetParent().SetSize(self._floatingSize)
			else:
				self.__pi.FloatingSize(self._floatingSize)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingHeight"] = val


	def _getFloatingLeft(self):
		return self.FloatingPosition[0]

	def _setFloatingLeft(self, val):
		if self._constructed():
			self._floatingPosition = (val, self.FloatingPosition[1])
			self.__pi.FloatingPosition(self._floatingPosition)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingLeft"] = val


	def _getFloatingPosition(self):
		return self.__pi.floating_pos.Get()

	def _setFloatingPosition(self, val):
		if self._constructed():
			self.__pi.FloatingPosition(val)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingPosition"] = val


	def _getFloatingRight(self):
		return self.FloatingPosition[0] + self.FloatingSize[0]

	def _setFloatingRight(self, val):
		if self._constructed():
			wd = self.FloatingSize[0]
			self._floatingPosition = (val - wd, self.FloatingPosition[1])
			self.__pi.FloatingPosition(self._floatingPosition)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingRight"] = val


	def _getFloatingSize(self):
		return self.__pi.floating_size.Get()

	def _setFloatingSize(self, val):
		if self._constructed():
			self.__pi.FloatingSize(val)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingSize"] = val


	def _getFloatingTop(self):
		return self.FloatingPosition[1]

	def _setFloatingTop(self, val):
		if self._constructed():
			self._floatingPosition = (self.FloatingPosition[0], val)
			self.__pi.FloatingPosition(self._floatingPosition)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingTop"] = val


	def _getFloatingWidth(self):
		return self.FloatingSize[0]

	def _setFloatingWidth(self, val):
		if self._constructed():
			self._floatingSize = (val, self.FloatingSize[1])
			if self.__pi.IsFloating():
				self.GetParent().SetSize(self._floatingSize)
			else:
				self.__pi.FloatingSize(self._floatingSize)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingWidth"] = val


	def _getHeight(self):
		return self.__getSize()[1]

	def _setHeight(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingHeight = val
			else:
				dabo.logError(_("Cannot set the Size of a docked panel"))
		else:
			self._properties["Height"] = val


	def _getLeft(self):
		return self.__getPosition()[0]

	def _setLeft(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingLeft = val
			else:
				dabo.logError(_("Cannot set the position of a docked panel"))
		else:
			self._properties["Left"] = val


	def _getLeftDockable(self):
		return self._leftDockable

	def _setLeftDockable(self, val):
		if self._constructed():
			self.__pi.LeftDockable(val)
			self.Form._refreshState()
		else:
			self._properties["LeftDockable"] = val


	def _getMovable(self):
		return self._movable

	def _setMovable(self, val):
		if self._constructed():
			self._movable = val
			self.__pi.Movable(val)
			self.Form._refreshState()
		else:
			self._properties["Movable"] = val


	def _getResizable(self):
		return self._resizable

	def _setResizable(self, val):
		if self._constructed():
			self._resizable = val
			self.__pi.Resizable(val)
			self.Form._refreshState()
		else:
			self._properties["Resizable"] = val


	def _getRight(self):
		return self.__getPosition()[0] + self.__getSize()[0]

	def _setRight(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingRight = val
			else:
				dabo.logError(_("Cannot set the position of a docked panel"))
		else:
			self._properties["Right"] = val


	def _getRightDockable(self):
		return self._rightDockable

	def _setRightDockable(self, val):
		if self._constructed():
			self.__pi.RightDockable(val)
			self.Form._refreshState()
		else:
			self._properties["RightDockable"] = val


	def _getShowBorder(self):
		return self._showBorder

	def _setShowBorder(self, val):
		if self._constructed():
			self._showBorder = val
			self.__pi.PaneBorder(val)
			self.Form._refreshState()
		else:
			self._properties["ShowBorder"] = val


	def _getShowCaption(self):
		return self._showCaption

	def _setShowCaption(self, val):
		if self._constructed():
			self._showCaption = val
			self.__pi.CaptionVisible(val)
			self.Form._refreshState()
		else:
			self._properties["ShowCaption"] = val


	def _getShowCloseButton(self):
		return self._showCloseButton

	def _setShowCloseButton(self, val):
		if self._constructed():
			self._showCloseButton = val
			self.__pi.CloseButton(val)
			self.Form._refreshState(0)
			self.Form.lockDisplay()
			self.Docked = not self.Docked
			dabo.ui.setAfterInterval(100, self, "Docked", not self.Docked)
			dabo.ui.callAfterInterval(150, self.Form.unlockDisplay)
		else:
			self._properties["ShowCloseButton"] = val


	def _getShowGripper(self):
		return self._showGripper

	def _setShowGripper(self, val):
		if self._constructed():
			self._showGripper = val
			self.__pi.Gripper(val)
			self.Form._refreshState()
		else:
			self._properties["ShowGripper"] = val


	def _getShowMaximizeButton(self):
		return self._showMaximizeButton

	def _setShowMaximizeButton(self, val):
		if self._constructed():
			self._showMaximizeButton = val
			self.__pi.MaximizeButton(val)
			self.Form._refreshState()
		else:
			self._properties["ShowMaximizeButton"] = val


	def _getShowMinimizeButton(self):
		return self._showMinimizeButton

	def _setShowMinimizeButton(self, val):
		if self._constructed():
			self._showMinimizeButton = val
			self.__pi.MinimizeButton(val)
			self.Form._refreshState()
		else:
			self._properties["ShowMinimizeButton"] = val


	def _getShowPinButton(self):
		return self._showPinButton

	def _setShowPinButton(self, val):
		if self._constructed():
			self._showPinButton = val
			self.__pi.PinButton(val)
			self.Form._refreshState()
		else:
			self._properties["ShowPinButton"] = val


	def _getTop(self):
		return self.__getPosition()[1]

	def _setTop(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingTop = val
			else:
				dabo.logError(_("Cannot set the position of a docked panel"))
		else:
			self._properties["Top"] = val


	def _getTopDockable(self):
		return self._topDockable

	def _setTopDockable(self, val):
		if self._constructed():
			self.__pi.TopDockable(val)
			self.Form._refreshState()
		else:
			self._properties["TopDockable"] = val


	def _getVisible(self):
		return self.__pi.IsShown()

	def _setVisible(self, val):
		if self._constructed():
			self.__pi.Show(val)
			self.Form._refreshState()
		else:
			self._properties["Visible"] = val


	def _getWidth(self):
		return self.__getSize()[0]

	def _setWidth(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingWidth = val
			else:
				dabo.logError(_("Cannot set the Size of a docked panel"))
		else:
			self._properties["Width"] = val


	Bottom = property(_getBottom, _setBottom, None,
			_("Position in pixels of the bottom side of the panel. Read-only when docked; read-write when floating  (int)"))

	BottomDockable = property(_getBottomDockable, _setBottomDockable, None,
			_("Can the panel be docked to the bottom edge of the form? Default=True  (bool)"))

	Caption = property(_getCaption, _setCaption, None,
			_("Text that appears in the title bar  (str)"))

	DestroyOnClose = property(_getDestroyOnClose, _setDestroyOnClose, None,
			_("When the panel's Close button is clicked, does the panel get destroyed (True) or just hidden (False, default)  (bool)"))

	Dockable = property(_getDockable, _setDockable, None,
			_("Can the panel be docked to the form? Default=True  (bool)"))

	Docked = property(_getDocked, _setDocked, None,
			_("Determines whether the pane is floating (False) or docked (True)  (bool)"))

	DockSide = property(_getDockSide, _setDockSide, None,
			_("""Side of the form that the panel is either currently docked to,
			or would be if dock() were to be called. Possible values are
			'Left', 'Right', 'Top' and 'Bottom'.  (str)"""))

	Floatable = property(_getFloatable, _setFloatable, None,
			_("Can the panel be undocked from the form and float independently? Default=True  (bool)"))

	Floating = property(_getFloating, _setFloating, None,
			_("Determines whether the pane is floating (True) or docked (False)  (bool)"))

	FloatingBottom = property(_getFloatingBottom, _setFloatingBottom, None,
			_("Bottom coordinate of the panel when floating  (int)"))

	FloatingHeight = property(_getFloatingHeight, _setFloatingHeight, None,
			_("Height of the panel when floating  (int)"))

	FloatingLeft = property(_getFloatingLeft, _setFloatingLeft, None,
			_("Left coordinate of the panel when floating  (int)"))

	FloatingPosition = property(_getFloatingPosition, _setFloatingPosition, None,
			_("Position of the panel when floating  (2-tuple of ints)"))

	FloatingRight = property(_getFloatingRight, _setFloatingRight, None,
			_("Right coordinate of the panel when floating  (int)"))

	FloatingSize = property(_getFloatingSize, _setFloatingSize, None,
			_("Size of the panel when floating  (2-tuple of ints)"))

	FloatingTop = property(_getFloatingTop, _setFloatingTop, None,
			_("Top coordinate of the panel when floating  (int)"))

	FloatingWidth = property(_getFloatingWidth, _setFloatingWidth, None,
			_("Width of the panel when floating  (int)"))

	Height = property(_getHeight, _setHeight, None,
			_("Position in pixels of the height of the panel. Read-only when docked; read-write when floating  (int)"))

	Left = property(_getLeft, _setLeft, None,
			_("Position in pixels of the left side of the panel. Read-only when docked; read-write when floating  (int)"))

	LeftDockable = property(_getLeftDockable, _setLeftDockable, None,
			_("Can the panel be docked to the left edge of the form? Default=True  (bool)"))

	Movable = property(_getMovable, _setMovable, None,
			_("Can the panel be moved (True, default), or is it in a fixed position (False).  (bool)"))

	Resizable = property(_getResizable, _setResizable, None,
			_("Can the panel be resized? Default=True  (bool)"))

	Right = property(_getRight, _setRight, None,
			_("Position in pixels of the right side of the panel. Read-only when docked; read-write when floating  (int)"))

	RightDockable = property(_getRightDockable, _setRightDockable, None,
			_("Can the panel be docked to the right edge of the form? Default=True  (bool)"))

	ShowBorder = property(_getShowBorder, _setShowBorder, None,
			_("Should the panel's border be shown when floating?  (bool)"))

	ShowCaption = property(_getShowCaption, _setShowCaption, None,
			_("Should the panel's Caption be shown when it is docked? Default=True  (bool)"))

	ShowCloseButton = property(_getShowCloseButton, _setShowCloseButton, None,
			_("Does the panel display a close button when floating? Default=True  (bool)"))

	ShowGripper = property(_getShowGripper, _setShowGripper, None,
			_("Does the panel display a draggable gripper? Default=False  (bool)"))

	ShowMaximizeButton = property(_getShowMaximizeButton, _setShowMaximizeButton, None,
			_("Does the panel display a maximize button when floating? Default=False  (bool)"))

	ShowMinimizeButton = property(_getShowMinimizeButton, _setShowMinimizeButton, None,
			_("Does the panel display a minimize button when floating? Default=False  (bool)"))

	ShowPinButton = property(_getShowPinButton, _setShowPinButton, None,
			_("Does the panel display a pin button when floating? Default=False  (bool)"))

	Top = property(_getTop, _setTop, None,
			_("Position in pixels of the top side of the panel. Read-only when docked; read-write when floating  (int)"))

	TopDockable = property(_getTopDockable, _setTopDockable, None,
			_("Can the panel be docked to the top edge of the form? Default=True  (bool)"))

	Visible = property(_getVisible, _setVisible, None,
			_("Is the panel shown?  (bool)"))

	Width = property(_getWidth, _setWidth, None,
			_("Position in pixels of the width of the panel. Read-only when docked; read-write when floating  (int)"))




class dDockForm(dabo.ui.dForm):
	def _afterInit(self):
		self._mgr = mgr = _dDockManager(self)
		pc = self.getBasePanelClass()
		self._centerPanel = pc(self, name="CenterPanel", typ="center")
		self._centerPanel.Sizer = dabo.ui.dSizer("v")
		super(dDockForm, self)._afterInit()
		self.bindEvent(dEvents.Destroy, self.__onDestroy)


	def __onDestroy(self, evt):
		if self._finito:
			self._mgr.UnInit()

	def getBasePanelClass(cls):
		return _dDockPanel
	getBasePanelClass = classmethod(getBasePanelClass)


	def onChildBorn(self, evt):
		ok = isinstance(evt.child, (_dDockPanel, dabo.ui.dStatusBar, dabo.ui.dShell.dShell))
		if not ok:
			print "BORN:", evt.child


	def addObject(self, classRef, Name=None, *args, **kwargs):
		self._centerPanel.addObject(classRef, Name=Name, *args, **kwargs)


	def addPanel(self, *args, **kwargs):
		pnl = _dDockPanel(self, *args, **kwargs)
		self._refreshState()
		return pnl


	def _refreshState(self, interval=None):
		if self._finito:
				return
		if interval is None:
			interval = 100
		if interval == 0:
			self._mgr.Update()
		else:
			dabo.ui.callAfterInterval(interval, self._mgr.runUpdate)


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getCenterPanel(self):
		return self._centerPanel


	CenterPanel = property(_getCenterPanel, None, None,
			_("Reference to the center (i.e., non-docking) panel. (read-only) (dPanel)"))





class _dDockForm_test(dDockForm):
	def afterInit(self):
		self.fp = _dDockPanel(self, Floating=True, BackColor="orange",
				Caption="I'm Floating!", Top=70, Left=100)
		self.dp = _dDockPanel(self, Floating=False, BackColor="slateblue",
				ShowCaption=False, ShowPinButton=True, ShowCloseButton=False,
				ShowGripper=True)
		btn = dabo.ui.dButton(self._centerPanel, Caption="Test Orange", OnHit=self.onTestFP)
		self._centerPanel.Sizer.append(btn)
		btn = dabo.ui.dButton(self._centerPanel, Caption="Test Blue", OnHit=self.onTestDP)
		self._centerPanel.Sizer.append(btn)
		self.fp.DynamicCaption = self.capForOrange


	def capForOrange(self):
		state = "Floating"
		if self.fp.Docked:
			state = "Docked"
		return "I'm %s!" % state


	def onTestFP(self, evt):
		self.printTest(self.fp)
	def onTestDP(self, evt):
		self.printTest(self.dp)
	def printTest(self, obj):
		nm = {self.fp: "OrangePanel", self.dp: "BluePanel"}[obj]
		print nm + ".BottomDockable:", obj.BottomDockable
		print nm + ".Caption:", obj.Caption
		print nm + ".DestroyOnClose:", obj.DestroyOnClose
		print nm + ".Dockable:", obj.Dockable
		print nm + ".Docked:", obj.Docked
		print nm + ".Floatable:", obj.Floatable
		print nm + ".Floating:", obj.Floating
		print nm + ".FloatingBottom:", obj.FloatingBottom
		print nm + ".FloatingHeight:", obj.FloatingHeight
		print nm + ".FloatingLeft:", obj.FloatingLeft
		print nm + ".FloatingPosition:", obj.FloatingPosition
		print nm + ".FloatingRight:", obj.FloatingRight
		print nm + ".FloatingSize:", obj.FloatingSize
		print nm + ".FloatingTop:", obj.FloatingTop
		print nm + ".FloatingWidth:", obj.FloatingWidth
		print nm + ".LeftDockable:", obj.LeftDockable
		print nm + ".Movable:", obj.Movable
		print nm + ".Resizable:", obj.Resizable
		print nm + ".RightDockable:", obj.RightDockable
		print nm + ".ShowBorder:", obj.ShowBorder
		print nm + ".ShowCaption:", obj.ShowCaption
		print nm + ".ShowCloseButton:", obj.ShowCloseButton
		print nm + ".ShowGripper:", obj.ShowGripper
		print nm + ".ShowMaximizeButton:", obj.ShowMaximizeButton
		print nm + ".ShowMinimizeButton:", obj.ShowMinimizeButton
		print nm + ".ShowPinButton:", obj.ShowPinButton
		print nm + ".TopDockable:", obj.TopDockable
		print nm + ".Visible:", obj.Visible



if __name__ == "__main__":
	import test
	test.Test().runTest(_dDockForm_test)
