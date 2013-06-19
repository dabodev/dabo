# -*- coding: utf-8 -*-
import wx
try:
	import wx.lib.agw.aui as aui
except ImportError:
	# wx versions prior to 2.8.9.2
	import wx.aui as aui
PaneInfo = aui.AuiPaneInfo
import dabo
if __name__ == "__main__":
	import dabo.ui
	dabo.ui.loadUI("wx")
from dabo.dLocalize import _
import dabo.dEvents as dEvents
from dabo.ui import makeDynamicProperty

flag_allow_float = aui.AUI_MGR_ALLOW_FLOATING
flag_show_active = aui.AUI_MGR_ALLOW_ACTIVE_PANE
flag_transparent_drag = aui.AUI_MGR_TRANSPARENT_DRAG
flag_rectangle_hint = aui.AUI_MGR_RECTANGLE_HINT
flag_transparent_hint = aui.AUI_MGR_TRANSPARENT_HINT
flag_venetian_blinds_hint = aui.AUI_MGR_VENETIAN_BLINDS_HINT
flag_no_venetian_blinds_fade = aui.AUI_MGR_NO_VENETIAN_BLINDS_FADE
flag_hint_fade = aui.AUI_MGR_HINT_FADE


class _dDockManager(aui.AuiManager):
	def __init__(self, win):
		self._managedWindow = win
		flags = flag_allow_float | flag_transparent_drag | flag_rectangle_hint | flag_transparent_hint
		try:
			super(_dDockManager, self).__init__(win, flags=flags)
		except TypeError:
			# Later AGW version
			super(_dDockManager, self).__init__(win, agwFlags=flags)
		self.Bind(aui.EVT_AUI_RENDER, self.aui_render)


	def aui_render(self, evt):
		evt.Skip()
		dabo.ui.callAfterInterval(100, self._managedWindow.update)


	def addPane(self, win, name=None, typ=None, caption=None, toolbar=None):
		pi = PaneInfo()
		if toolbar:
			pi.ToolbarPane()
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



class dDockPanel(dabo.ui.dPanel):
	def __init__(self, parent, properties=None, attProperties=None, *args, **kwargs):
		nmU = self._extractKey((properties, kwargs), "Name", "")
		nb = self._extractKey((properties, kwargs), "NameBase", "")
		nmL = self._extractKey((properties, kwargs), "name", "")
		kwargs["NameBase"] = [txt for txt in (nmU, nb, nmL, "dDockPanel") if txt][0]
		pcapUp = self._extractKey(kwargs, "Caption", "")
		pcap = self._extractKey(kwargs, "caption", "")
		ptype = self._extractKey(kwargs, "typ", "")
		if pcapUp:
			kwargs["Caption"] = pcapUp
		else:
			kwargs["Caption"] = pcap
		self._paramType = ptype
		self._toolbar = self._extractKey(kwargs, "Toolbar", False)

		# Initialize attributes that underly properties
		self._bottomDockable = True
		self._leftDockable = True
		self._rightDockable = True
		self._topDockable = True
		self._floatable = True
		self._floatingPosition = (0, 0)
		self._floatingSize = (100, 100)
		self._gripperPosition = "Left"
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
		super(dDockPanel, self).__init__(parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)
		if self.Floating:
			self._floatingPosition = self.GetParent().GetPosition().Get()
			self._floatingSize = self.GetParent().GetSize().Get()


	def _uniqueNameForParent(self, name, parent=None):
		"""
		We need to check the AUI manager's PaneInfo name value, too, as that has to be unique
		there as well as the form.
		"""
		changed = True
		try:
			mgr = parent._mgr
		except AttributeError:
			mgr = self._Manager
		while changed:
			i = 0
			auiOK = False
			while not auiOK:
				auiOK = True
				candidate = name
				if i:
					candidate = "%s%s" % (name, i)
				mtch = [pi.name for pi in mgr.GetAllPanes()
						if pi.name == candidate]
				if mtch:
					auiOK = False
					i += 1
			changed = changed and (candidate != name)
			name = candidate

			candidate = super(dDockPanel, self)._uniqueNameForParent(name, parent)
			changed = changed and (candidate != name)
			name = candidate
		return name


	def float(self):
		"""Float the panel if it isn't already floating."""
		if self.Floating or not self.Floatable:
			return
		self._PaneInfo.Float()
		self._updateAUI()


	def dock(self, side=None):
		"""
		Dock the panel. If side is specified, it is docked on that side of the
		form. If no side is specified, it is docked in its default location.
		"""
		if self.Docked or not self.Dockable:
			return
		inf = self._PaneInfo
		if side is not None:
			s = side[0].lower()
			func = {"l": inf.Left, "r": inf.Right, "t": inf.Top, "b": inf.Bottom}.get(s, None)
			if func:
				func()
			else:
				dabo.log.error(_("Invalid dock position: '%s'.") % side)
		inf.Dock()
		self._updateAUI()


	def _beforeSetProperties(self, props):
		"""
		Some properties of Floating panels cannot be set at the usual
		point in the process, since the panel will still be docked, and you
		can't change dimensions/location of a docked panel. So extract
		them now, and then set them afterwards.
		"""
		self._propDelayDict = {}
		props2Delay = ("Bottom", "BottomDockable", "Caption", "DestroyOnClose", "Dockable", "Docked",
				"DockSide", "Floatable", "Floating", "FloatingBottom", "FloatingHeight", "FloatingLeft",
				"FloatingPosition", "FloatingRight", "FloatingSize", "FloatingTop", "FloatingWidth", "GripperPosition",
				"Height", "Left", "LeftDockable", "Movable", "Resizable", "Right", "RightDockable", "ShowBorder",
				"ShowCaption", "ShowCloseButton", "ShowGripper", "ShowMaximizeButton", "ShowMinimizeButton",
				"ShowPinButton", "Top", "TopDockable", "Visible", "Width")
		for delayed in props2Delay:
			val = self._extractKey(props, delayed, None)
			if val is not None:
				self._propDelayDict[delayed] = val
		return super(dDockPanel, self)._beforeSetProperties(props)


	def _afterSetProperties(self):
		nm = self.Name
		frm = self.Form
		self._Manager.addPane(self, name=nm,
				typ=self._paramType, caption=self._propDelayDict.get("Caption", "dDockPanel"))
		del self._paramType
		self._PaneInfo.MinSize((50,50))
		if self._propDelayDict:
			self.setProperties(self._propDelayDict)
		del self._propDelayDict


	def getState(self):
		"""Returns the local name and a string that can be used to restore the state of this pane."""
		inf = self._Manager.SavePaneInfo(self._PaneInfo)
		try:
			infPairs = (qq.split("=") for qq in inf.split(";"))
			nm = dict(infPairs)["name"]
		except KeyError:
			# For some reason a name was not returned
			return ""
		return (nm, inf.replace("name=%s;" % nm, ""))


	def _updateAUI(self):
		frm = self.Form
		if frm is not None:
			frm._refreshState()
		else:
			try:
				self._Manager.runUpdate()
			except AttributeError:
				pass


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
				dabo.log.error(_("Cannot set the position of a docked panel"))
		else:
			self._properties["Bottom"] = val


	def _getBottomDockable(self):
		return self._bottomDockable

	def _setBottomDockable(self, val):
		if self._constructed():
			self._PaneInfo.BottomDockable(val)
			self._updateAUI()
		else:
			self._properties["BottomDockable"] = val

	def _getCaption(self):
		try:
			return self._caption
		except AttributeError:
			self._caption = ""
			return self._caption

	def _setCaption(self, val):
		if self._constructed():
			self._caption = val
			self._PaneInfo.Caption(val)
			self._updateAUI()
		else:
			self._properties["Caption"] = val


	def _getDestroyOnClose(self):
		return self._destroyOnClose

	def _setDestroyOnClose(self, val):
		if self._constructed():
			self._destroyOnClose = val
			self._PaneInfo.DestroyOnClose(val)
			self._updateAUI()
		else:
			self._properties["DestroyOnClose"] = val


	def _getDockable(self):
		return self._bottomDockable or self._leftDockable or self._rightDockable or self._topDockable

	def _setDockable(self, val):
		if self._constructed():
			self._dockable = self._bottomDockable = self._leftDockable = self._rightDockable = self._topDockable = val
			self._PaneInfo.Dockable(val)
			if self.Docked:
				self.Docked = val
			self._updateAUI()
		else:
			self._properties["Dockable"] = val


	def _getDocked(self):
		return self._PaneInfo.IsDocked()

	def _setDocked(self, val):
		if self._constructed():
			curr = self._PaneInfo.IsDocked()
			chg = False
			if val and not curr:
				self._PaneInfo.Dock()
				chg = True
			elif not val and curr:
				self._PaneInfo.Float()
				chg = True
			if chg:
				self._updateAUI()
		else:
			self._properties["Docked"] = val


	def _getDockSide(self):
		return {1: "Top", 2: "Right", 3: "Bottom", 4: "Left"}[self._PaneInfo.dock_direction]

	def _setDockSide(self, val):
		if self._constructed():
			vUp = val[0].upper()
			self._PaneInfo.dock_direction = {"T": 1, "R": 2, "B": 3, "L": 4}[vUp]
			self._updateAUI()
		else:
			self._properties["DockSide"] = val


	def _getFloatable(self):
		return self._floatable

	def _setFloatable(self, val):
		if self._constructed():
			self._floatable = val
			self._PaneInfo.Floatable(val)
			self._updateAUI()
		else:
			self._properties["Floatable"] = val


	def _getFloating(self):
		return self._PaneInfo.IsFloating()

	def _setFloating(self, val):
		if self._constructed():
			curr = self._PaneInfo.IsFloating()
			chg = False
			if val and not curr:
				self._PaneInfo.Float()
				chg = True
			elif not val and curr:
				self._PaneInfo.Dock()
				chg = True
			if chg:
				self._updateAUI()
		else:
			self._properties["Floating"] = val


	def _getFloatingBottom(self):
		return self.FloatingPosition[1] + self.FloatingSize[1]

	def _setFloatingBottom(self, val):
		if self._constructed():
			ht = self.FloatingSize[1]
			self._floatingPosition = (self.FloatingPosition[0], val - ht)
			self._PaneInfo.FloatingPosition(self._floatingPosition)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingBottom"] = val


	def _getFloatingHeight(self):
		return self.FloatingSize[1]

	def _setFloatingHeight(self, val):
		if self._constructed():
			self._floatingSize = (self.FloatingSize[0], val)
			if self._PaneInfo.IsFloating():
				self.GetParent().SetSize(self._floatingSize)
			else:
				self._PaneInfo.FloatingSize(self._floatingSize)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingHeight"] = val


	def _getFloatingLeft(self):
		return self.FloatingPosition[0]

	def _setFloatingLeft(self, val):
		if self._constructed():
			self._floatingPosition = (val, self.FloatingPosition[1])
			self._PaneInfo.FloatingPosition(self._floatingPosition)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingLeft"] = val


	def _getFloatingPosition(self):
		return self._PaneInfo.floating_pos.Get()

	def _setFloatingPosition(self, val):
		if self._constructed():
			self._PaneInfo.FloatingPosition(val)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingPosition"] = val


	def _getFloatingRight(self):
		return self.FloatingPosition[0] + self.FloatingSize[0]

	def _setFloatingRight(self, val):
		if self._constructed():
			wd = self.FloatingSize[0]
			self._floatingPosition = (val - wd, self.FloatingPosition[1])
			self._PaneInfo.FloatingPosition(self._floatingPosition)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingRight"] = val


	def _getFloatingSize(self):
		return self._PaneInfo.floating_size.Get()

	def _setFloatingSize(self, val):
		if self._constructed():
			self._PaneInfo.FloatingSize(val)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingSize"] = val


	def _getFloatingTop(self):
		return self.FloatingPosition[1]

	def _setFloatingTop(self, val):
		if self._constructed():
			self._floatingPosition = (self.FloatingPosition[0], val)
			self._PaneInfo.FloatingPosition(self._floatingPosition)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingTop"] = val


	def _getFloatingWidth(self):
		return self.FloatingSize[0]

	def _setFloatingWidth(self, val):
		if self._constructed():
			self._floatingSize = (val, self.FloatingSize[1])
			if self._PaneInfo.IsFloating():
				self.GetParent().SetSize(self._floatingSize)
			else:
				self._PaneInfo.FloatingSize(self._floatingSize)
			self.Form._refreshState(0)
		else:
			self._properties["FloatingWidth"] = val


	def _getGripperPosition(self):
		return self._gripperPosition

	def _setGripperPosition(self, val):
		if self._constructed():
			val = val[0].lower()
			if not val in ("l", "t"):
				raise ValueError(_("Only valid GripperPosition values are 'Top' or 'Left'."))
			self._gripperPosition = {"l": "Left", "t": "Top"}[val]
			self._PaneInfo.GripperTop(val == "t")
			self._updateAUI()
		else:
			self._properties["GripperPosition"] = val


	def _getHeight(self):
		return self.__getSize()[1]

	def _setHeight(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingHeight = val
			else:
				dabo.log.error(_("Cannot set the Size of a docked panel"))
		else:
			self._properties["Height"] = val


	def _getLeft(self):
		return self.__getPosition()[0]

	def _setLeft(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingLeft = val
			else:
				dabo.log.error(_("Cannot set the position of a docked panel"))
		else:
			self._properties["Left"] = val


	def _getLeftDockable(self):
		return self._leftDockable

	def _setLeftDockable(self, val):
		if self._constructed():
			self._PaneInfo.LeftDockable(val)
			self._updateAUI()
		else:
			self._properties["LeftDockable"] = val


	def _getManager(self):
		try:
			mgr = self._mgr
		except AttributeError:
			mgr = self._mgr = self.Form._mgr
		return mgr


	def _getMovable(self):
		return self._movable

	def _setMovable(self, val):
		if self._constructed():
			self._movable = val
			self._PaneInfo.Movable(val)
			self._updateAUI()
		else:
			self._properties["Movable"] = val


	def _getPaneInfo(self):
		try:
			mgr = self._mgr
		except AttributeError:
			mgr = self._mgr = self.Form._mgr
		return mgr.GetPane(self)


	def _getResizable(self):
		return self._resizable

	def _setResizable(self, val):
		if self._constructed():
			self._resizable = val
			self._PaneInfo.Resizable(val)
			self._updateAUI()
		else:
			self._properties["Resizable"] = val


	def _getRight(self):
		return self.__getPosition()[0] + self.__getSize()[0]

	def _setRight(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingRight = val
			else:
				dabo.log.error(_("Cannot set the position of a docked panel"))
		else:
			self._properties["Right"] = val


	def _getRightDockable(self):
		return self._rightDockable

	def _setRightDockable(self, val):
		if self._constructed():
			self._PaneInfo.RightDockable(val)
			self._updateAUI()
		else:
			self._properties["RightDockable"] = val


	def _getShowBorder(self):
		return self._showBorder

	def _setShowBorder(self, val):
		if self._constructed():
			self._showBorder = val
			self._PaneInfo.PaneBorder(val)
			self._updateAUI()
		else:
			self._properties["ShowBorder"] = val


	def _getShowCaption(self):
		return self._showCaption

	def _setShowCaption(self, val):
		if self._constructed():
			self._showCaption = val
			self._PaneInfo.CaptionVisible(val)
			self._updateAUI()
		else:
			self._properties["ShowCaption"] = val


	def _getShowCloseButton(self):
		return self._showCloseButton

	def _setShowCloseButton(self, val):
		if self._constructed():
			self._showCloseButton = val
			self._PaneInfo.CloseButton(val)
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
			if val == self._showGripper:
				return
			self._showGripper = val
			self._PaneInfo.Gripper(val)
			self._updateAUI()
		else:
			self._properties["ShowGripper"] = val


	def _getShowMaximizeButton(self):
		return self._showMaximizeButton

	def _setShowMaximizeButton(self, val):
		if self._constructed():
			self._showMaximizeButton = val
			self._PaneInfo.MaximizeButton(val)
			self._updateAUI()
		else:
			self._properties["ShowMaximizeButton"] = val


	def _getShowMinimizeButton(self):
		return self._showMinimizeButton

	def _setShowMinimizeButton(self, val):
		if self._constructed():
			self._showMinimizeButton = val
			self._PaneInfo.MinimizeButton(val)
			self._updateAUI()
		else:
			self._properties["ShowMinimizeButton"] = val


	def _getShowPinButton(self):
		return self._showPinButton

	def _setShowPinButton(self, val):
		if self._constructed():
			self._showPinButton = val
			self._PaneInfo.PinButton(val)
			self._updateAUI()
		else:
			self._properties["ShowPinButton"] = val



	def _getToolbar(self):
		return self._toolbar


	def _getTop(self):
		return self.__getPosition()[1]

	def _setTop(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingTop = val
			else:
				dabo.log.error(_("Cannot set the position of a docked panel"))
		else:
			self._properties["Top"] = val


	def _getTopDockable(self):
		return self._topDockable

	def _setTopDockable(self, val):
		if self._constructed():
			self._PaneInfo.TopDockable(val)
			self._updateAUI()
		else:
			self._properties["TopDockable"] = val


	def _getVisible(self):
		return self._PaneInfo.IsShown()

	def _setVisible(self, val):
		if self._constructed():
			self._PaneInfo.Show(val)
			self._updateAUI()
		else:
			self._properties["Visible"] = val


	def _getWidth(self):
		return self.__getSize()[0]

	def _setWidth(self, val):
		if self._constructed():
			if self.Floating:
				self.FloatingWidth = val
			else:
				dabo.log.error(_("Cannot set the Size of a docked panel"))
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

	GripperPosition = property(_getGripperPosition, _setGripperPosition, None,
			_("If a gripper is shown, is it on the Top or Left side? Default = 'Left'  ('Top' or 'Left')"))

	Height = property(_getHeight, _setHeight, None,
			_("Position in pixels of the height of the panel. Read-only when docked; read-write when floating  (int)"))

	Left = property(_getLeft, _setLeft, None,
			_("Position in pixels of the left side of the panel. Read-only when docked; read-write when floating  (int)"))

	LeftDockable = property(_getLeftDockable, _setLeftDockable, None,
			_("Can the panel be docked to the left edge of the form? Default=True  (bool)"))

	_Manager = property(_getManager, None, None,
			_("Reference to the AUI manager (for internal use only).  (_dDockManager)"))

	Movable = property(_getMovable, _setMovable, None,
			_("Can the panel be moved (True, default), or is it in a fixed position (False).  (bool)"))

	_PaneInfo = property(_getPaneInfo, None, None,
			_("Reference to the AUI PaneInfo object (for internal use only).  (wx.aui.PaneInfo)"))

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

	Toolbar = property(_getToolbar, None, None,
			_("Returns True if this is a Toolbar pane. Default=False  (bool)"))

	Top = property(_getTop, _setTop, None,
			_("Position in pixels of the top side of the panel. Read-only when docked; read-write when floating  (int)"))

	TopDockable = property(_getTopDockable, _setTopDockable, None,
			_("Can the panel be docked to the top edge of the form? Default=True  (bool)"))

	Visible = property(_getVisible, _setVisible, None,
			_("Is the panel shown?  (bool)"))

	Width = property(_getWidth, _setWidth, None,
			_("Position in pixels of the width of the panel. Read-only when docked; read-write when floating  (int)"))


	DynamicCaption = makeDynamicProperty(Caption)



class dDockForm(dabo.ui.dForm):
	def _afterInit(self):
		self._inUpdate = False
		self._mgr = mgr = _dDockManager(self)
		pc = self.getBasePanelClass()
		self._centerPanel = pc(self, name="CenterPanel", typ="center")
		self._centerPanel.Sizer = dabo.ui.dSizer("v")
		self._panels = {}
		super(dDockForm, self)._afterInit()
		self.bindEvent(dEvents.Destroy, self.__onDestroy)


	def __onDestroy(self, evt):
		if self._finito:
			# Need to save this here, since we can't respond to all layout changes.
			self.saveSizeAndPosition()
			self._mgr.UnInit()


	def getBasePanelClass(cls):
		return dDockPanel
	getBasePanelClass = classmethod(getBasePanelClass)


	def onChildBorn(self, evt):
		ok = isinstance(evt.child, (dDockPanel, dabo.ui.dStatusBar, dabo.ui.dShellForm))
		if not ok:
			# This should never happen; if so, log the error
			dabo.log.error(_("Unmanaged object added to a Dock Form: %s") %evt.child)


	def addObject(self, classRef, Name=None, *args, **kwargs):
		"""
		To support the old addObject() syntax, we need to re-direct the request
		to the center panel.
		"""
		self._centerPanel.addObject(classRef, Name=Name, *args, **kwargs)


	def addPanel(self, *args, **kwargs):
		"""Adds a dockable panel to the form."""
		pnl = dDockPanel(self, *args, **kwargs)
		self._refreshState()
		# Store the pane info
		nm = pnl.getState()[0]
		self._panels[pnl] = nm
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
		if not self._inUpdate:
			dabo.ui.callAfter(self.update)


	def update(self, interval=None):
		if not self._inUpdate:
			self._inUpdate = True
			super(dDockForm, self).update(interval=interval)
			# Update the panels
			for pnl in self._panels.keys():
				pnl.update()
			dabo.ui.callAfterInterval(500, self._clearInUpdate)


	def _clearInUpdate(self):
		self._inUpdate = False


	def saveSizeAndPosition(self):
		"""Save the panel layout info, then call the default behavior."""
		if self.Application:
			if self.SaveRestorePosition and not self.TempForm:
				self.Application.setUserSetting("perspective", self._mgr.SavePerspective())
				if not self._finito:
					super(dDockForm, self).saveSizeAndPosition()


	def restoreSizeAndPosition(self):
		"""Restore the panel layout, if possible, then call the default behavior."""
		if self.Application and self.SaveRestorePosition:
			super(dDockForm, self).restoreSizeAndPosition()
			ps = self.Application.getUserSetting("perspective", "")
			if ps:
				self._mgr.LoadPerspective(ps)


	# Property get/set/del methods follow. Scroll to bottom to see the property
	# definitions themselves.
	def _getCenterPanel(self):
		return self._centerPanel


	def _getShowActivePanel(self):
		return bool(self._mgr.GetFlags() & flag_show_active)

	def _setShowActivePanel(self, val):
		if self._constructed():
			self._transparentDrag = val
			flags = self._mgr.GetFlags()
			if val:
				newFlags = flags | flag_show_active
			else:
				newFlags = flags & ~flag_show_active
			self._mgr.SetFlags(newFlags)
		else:
			self._properties["ShowActivePanel"] = val


	def _getTransparentDrag(self):
		return bool(self._mgr.GetFlags() & flag_transparent_drag)

	def _setTransparentDrag(self, val):
		if self._constructed():
			self._transparentDrag = val
			flags = self._mgr.GetFlags()
			if val:
				newFlags = flags | flag_transparent_drag
			else:
				newFlags = flags & ~flag_transparent_drag
			self._mgr.SetFlags(newFlags)
		else:
			self._properties["TransparentDrag"] = val


	CenterPanel = property(_getCenterPanel, None, None,
			_("Reference to the center (i.e., non-docking) panel. (read-only) (dPanel)"))

	ShowActivePanel = property(_getShowActivePanel, _setShowActivePanel, None,
			_("When True, the title bar of the active pane is highlighted. Default=False  (bool)"))

	TransparentDrag = property(_getTransparentDrag, _setTransparentDrag, None,
			_("When dragging panes, do they appear transparent? Default=True  (bool)"))



class _dDockForm_test(dDockForm):
	def initProperties(self):
		self.SaveRestorePosition = False
		self.Size = (700, 500)

	def afterInit(self):
		self.fp = self.addPanel(Floating=True, BackColor="orange",
				Caption="Initially Floating", Top=70, Left=200, Size=(144, 100))
		self.dp = self.addPanel(Floating=False, Caption="Initially Docked", BackColor="slateblue",
				ShowCaption=False, ShowPinButton=True, ShowCloseButton=False,
				ShowGripper=True, Size=(144, 100))
		btn = dabo.ui.dButton(self.CenterPanel, Caption="Test Orange", OnHit=self.onTestFP)
		self.CenterPanel.Sizer.append(btn)
		btn = dabo.ui.dButton(self.CenterPanel, Caption="Test Blue", OnHit=self.onTestDP)
		self.CenterPanel.Sizer.append(btn)
		chk = dabo.ui.dCheckBox(self.CenterPanel, Caption="Orange Dockable", DataSource=self.fp,
				DataField="Dockable")
		self.CenterPanel.Sizer.append(chk)
		self.fp.DynamicCaption = self.capForOrange

	def capForOrange(self):
		print "ORNG CAP", self.fp.Docked
		state = "Floating"
		if self.fp.Docked:
			state = "Docked"
		print "STATE", state
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
		print nm + ".GripperPosition:", obj.GripperPosition
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
