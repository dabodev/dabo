# -*- coding: utf-8 -*-
import os
import sys
import wx
import dabo
import dPemMixin as pm
import dMenu
import dabo.icons
from dabo.dLocalize import _
from dabo.lib.utils import ustr
import dabo.dEvents as dEvents
import dabo.dException as dException
from dabo.lib.xmltodict import xmltodict as XTD
from dabo.lib.utils import cleanMenuCaption
from dabo.ui import makeDynamicProperty


class dFormMixin(pm.dPemMixin):
	def __init__(self, preClass, parent=None, properties=None, attProperties=None,
			src=None, *args, **kwargs):
		self._cxnName = ""
		self._connection = None
		self._floatingPanel = None
		self._sizersToOutline = []
		self._recurseOutlinedSizers = True
		self._alwaysDrawSizerOutlines = False
		self._idleRefreshInterval = 1000
		self._drawSizerChildren = False
		self._statusBarClass = dabo.ui.dStatusBar

		# Extract the menu definition file, if any
		self._menuBarFile = self._extractKey((properties, attProperties, kwargs),
				"MenuBarFile", "")
		if self._menuBarFile:
			self._menuBarClass = self._menuBarFile

		if False and parent:
			## pkm 3/10/05: I like it better now without the float on parent option
			##              and think it is a better default to stick with the wx
			##              default frame style. You can still override the style
			##              by passing it to the constructor.
			style = wx.DEFAULT_FRAME_STYLE|wx.FRAME_FLOAT_ON_PARENT
		else:
			style = self._extractKey(kwargs, "style", 0)
			if not style:
				# No style was explicitly set
				style = wx.DEFAULT_FRAME_STYLE
		kwargs["style"] = style

		# Manages RegID values and their controls
		self._objectRegistry = {}

		# Flag to skip updates when they aren't needed
		self._isClosed = False
		# Flag that indicates if the form was shown modally
		self._isModal = False
		# Sizer outline drawing flag
		self.__needOutlineRedraw = False
		# When in designer mode, we need to turn off various behaviors.
		self._designerMode = False
		# Default behavior used to be for the form to set the status bar text with the
		# current record position. Now we only turn it on for data apps.
		self._autoUpdateStatusText = False
		# Flag to denote temporary forms
		self._tempForm = False
		# Defaults for window sizing
		self._defaultLeft = 50
		self._defaultTop = 50
		self._defaultWidth = 600
		self._defaultHeight = 500
		self._defaultState = "Normal"
		# Flag to prevent infinite loops when doing field-level validation
		self._fieldValidationControl = None

		super(dFormMixin, self).__init__(preClass, parent, properties=properties,
				attProperties=attProperties, *args, **kwargs)

		dabo.ui.callAfter(self._createStatusBar)
		self._createToolBar()


	def _getInitPropertiesList(self):
		additional = ["BorderResizable", "FloatOnParent", "ShowCloseButton", "ShowInTaskBar",
				"ShowMaxButton", "ShowMinButton", "ShowSystemMenu", "StayOnTop", "TinyTitleBar"]
		original = list(super(dFormMixin, self)._getInitPropertiesList())
		return tuple(original + additional)


	def _afterInit(self):
		app = self.Application
		mbc = self.MenuBarClass
		if app and mbc and self.ShowMenuBar:
			if isinstance(mbc, basestring):
				self.MenuBar = dabo.ui.createMenuBar(mbc, self)
			else:
				self.MenuBar = mbc()
			self.afterSetMenuBar()

		if not self.Icon:
			if app:
				self.Icon = app.Icon
			else:
				self.Icon = "daboIcon.ico"

		self.debugText = ""
		self.useOldDebugDialog = False
		self._statusStack = []
		if app is not None:
			app.uiForms.add(self)

		# Centering information
		self._normLeft = self.Left
		self._normTop = self.Top

		if self._cxnName:
			try:
				self.Connection = app.getConnectionByName(self._cxnName)
			except dException.ConnectionNotFoundException:
				self.Connection = None
			if self.Connection is None:
				dabo.log.info(_("Could not establish connection '%s'") %
						self._cxnName)
		# If code to create bizobjs is present, run it.
		self.createBizobjs()
		# If there are custom menu hotkey bindings, re-set them
		wx.CallAfter(self._restoreMenuPrefs)

		super(dFormMixin, self)._afterInit()

		## pkm 2010-08-03: The below results in smoother, nicer forms (no menu flickering or
		##                 other weird artifacts like page tabs partially disappearing),
		##                 however there are reports of python.exe maxing out the CPU and the
		##                 process needing to be killed by the user. My testing was with
		##                 Python 2.5.4 / wx 2.8.11.0 / Windows Vista. Perhaps we just need to
		##                 play around with where we make this call, or set double buffered off
		##                 every now and then with a timer or something...
		##self.SetDoubleBuffered(True)


	def _initEvents(self):
		super(dFormMixin, self)._initEvents()
		self.Bind(wx.EVT_ACTIVATE, self.__onWxActivate)
		self.Bind(wx.EVT_CLOSE, self.__onWxClose)
		self.bindEvent(dEvents.Deactivate, self.__onDeactivate)
		self.bindEvent(dEvents.Close, self.__onClose)
		self.bindEvent(dEvents.Paint, self.__onPaint)
		self.bindEvent(dEvents.Idle, self.__onIdle)


	def __onWxClose(self, evt):
		self.raiseEvent(dEvents.Close, evt)
		if evt.CanVeto():
			evt.Veto()


	def __onWxActivate(self, evt):
		"""Raise the Dabo Activate or Deactivate appropriately."""
		if bool(evt.GetActive()):
			self.raiseEvent(dEvents.Activate, evt)
			app = self.Application
			if app is not None:
				if app.Platform != "Win":
					app.ActiveForm = self
			mb = self.MenuBar
			if mb:
				pref_id = getattr(mb, "_mac_pref_menu_item_id", None)
				if pref_id:
					wx.App_SetMacPreferencesMenuItemId(pref_id)
		else:
			self.raiseEvent(dEvents.Deactivate, evt)
		evt.Skip()


	def _controlGotFocus(self, ctrl):
		if self._fieldValidationControl is ctrl:
			# Clear it
			self._fieldValidationControl = None


	def Maximize(self, maximize=True, *args, **kwargs):
		"""On Mac MDI Child Frames, Maximize(False) erroneously maximizes. Not sure
		how to restore a maximized frame in this case, but at least we can catch
		the case where the window isn't maximized already.
		"""
		if (self.MDI and sys.platform.startswith("darwin") and not maximize
				and not self.IsMaximized()):
			return
		super(dFormMixin, self).Maximize(maximize, *args, **kwargs)


	def SetPosition(self, val):
		# On Windows MDI Child frames when the main form has a toolbar, setting the
		# top position results in a position too low by the height of the toolbar.
		left, top = val
		tb = None
		if self.Form:
			tb = self.Form.ToolBar
		if sys.platform.startswith("win") and self.MDI and tb:
			top -= tb.Height
		super(dFormMixin, self).SetPosition((left, top))


	def _createToolBar(self):
		if self.ShowToolBar and self.ToolBar is None:
			try:
				self.ToolBar = dabo.ui.dToolBar(self)
			except (AttributeError, TypeError):
				# We are a dialog, an MDI Child, or some other toolbar-unworthy form
				pass


	def _createStatusBar(self):
		modal = getattr(self, "Modal", False)
		if (self and self.ShowStatusBar
				and self.StatusBar is None
				and not isinstance (self, wx.Dialog)
				and not modal
				and (sys.platform.startswith("darwin") or not isinstance(self, wx.MDIChildFrame))):
			SBC = self.StatusBarClass
			self.StatusBar = SBC(self)


	def __onDeactivate(self, evt):
		if self.Application is not None and self.Application.ActiveForm == self:
			self.Application.clearActiveForm(self)


	def __onPaint(self, evt):
		if self.Application:
			self.__needOutlineRedraw = self.Application.DrawSizerOutlines
		else:
			self.__needOutlineRedraw = False


	def __onIdle(self, evt):
		if self.__needOutlineRedraw or self._alwaysDrawSizerOutlines:
			dabo.ui.callAfterInterval(self.IdleRefreshInterval, self._idleRedraw)


	def _idleRedraw(self):
		self.refresh()
		for sz in self.SizersToOutline:
			win = sz.getContainingWindow()
			try:
				sz.drawOutline(win, recurse=self._recurseOutlinedSizers,
						drawChildren=self._drawSizerChildren)
			except AttributeError:
				# Will happen if sz is None
				self.removeFromOutlinedSizers(sz)


	def __onClose(self, evt):
		app = self.Application

		if not self._designerMode:
			self.saveSizeAndPosition()

		force = evt.EventData.get("force", False)
		if not force:
			if self._beforeClose(evt) == False:
				evt.stop()
				return
			# Run the cleanup code.
			self.closing()

		self._isClosed = True
		if self._isModal:
			self.MakeModal(False)

		# On the Mac, this next line prevents Bus Errors when closing a form.
		self.Visible = False

		if app is not None:
			app.uiForms.remove(self)


	def forceSizerOutline(self):
		self.__needOutlineRedraw = True


	def activeControlValid(self):
		"""
		Force the control-with-focus to fire its KillFocus code.

		The bizobj will only get its field updated during the control's
		KillFocus code. This function effectively commands that update to
		happen before it would have otherwise occurred.
		"""
		ac = self.ActiveControl
		if ac is not None and isinstance(ac, dabo.ui.dDataControlMixinBase.dDataControlMixinBase):
			if not hasattr(ac, "_oldVal") or (not ac._oldVal) or (ac._oldVal != ac.Value):
				return ac.flushValue()
		return True


	def refresh(self, interval=None):
		"""
		Repaints the form and all contained objects.

		This method is called repeatedly from many different places during
		a single change in the UI, so by default the actual execution is cached
		using callAfterInterval(). The default interval is 100 milliseconds. You
		can change that to suit your app needs by passing a different interval
		in milliseconds.

		Sometimes, though, you want to force immediate execution of the
		refresh. In these cases, pass an interval of 0 to this method, which
		means don't wait; execute now.
		"""
		if interval is None:
			interval = 100
		if interval == 0:
			self.__refresh()
		else:
			dabo.ui.callAfterInterval(interval, self.__refresh)


	@dabo.ui.deadCheck
	def __refresh(self):
		super(dFormMixin, self).refresh()


	def reload(self):
		"""
		Tells the application to check for a newer version of the form, and if there is,
		to replace this instance with an instance of the newer class.
		"""
		# First, create a dummy event object
		class DummyEvent(object): pass
		evt = DummyEvent()
		evt.EventObject = self
		dabo.ui.callAfter(self.Application.onReloadForm, evt)


	def createBizobjs(self):
		"""
		Can be overridden in instances to create the bizobjs this form needs.
		It is provided so that tools such as the Class Designer can create skeleton
		code that the user can later enhance.
		"""
		pass


	def addToOutlinedSizers(self, val):
		self._sizersToOutline.append(val)


	def removeFromOutlinedSizers(self, val):
		try:
			self._sizersToOutline.remove(val)
		except ValueError:
			# already removed
			pass


	def _restoreMenuPrefs(self):
		if not self:
			# Form has already been released
			return
		pm = self.PreferenceManager
		mb = self.MenuBar
		if mb is None or not pm.hasKey("menu"):
			return
		menus = mb.Children
		pmMenu = pm.menu
		menuPath = pmMenu.FullPath + "."
		prefs = pmMenu.getPrefs(returnNested=True)
		for itmPath, hk in prefs.items():
			relPath, setting = itmPath.replace(menuPath, "").rsplit(".", 1)
			menuItem = mb
			for pth in relPath.split("."):
				try:
					menuItem = [ch for ch in menuItem.Children
							if hasattr(ch, "Caption")
							and cleanMenuCaption(ch.Caption) == pth][0]
				except IndexError:
					# No such menu; skip it
					menuItem = None
					break
			if menuItem is not None:
				if setting == "hotkey":
					menuItem.HotKey = hk


	def restoreSizeAndPositionIfNeeded(self):
		if not getattr(self, "_firstShown", False):
			self.restoreSizeAndPosition()
			self._firstShown = True


	def Show(self, *args, **kwargs):
		self.restoreSizeAndPositionIfNeeded()
		super(dFormMixin, self).Show(*args, **kwargs)


	def showModal(self):
		"""
		Shows the form in a modal fashion. Other forms can still be
		activated, but all controls are disabled.

		.. note::
			wxPython does not currently support this. DO NOT USE this method.

		"""
		raise dException.FeatureNotSupportedException(
				_("The underlying UI toolkit does not support modal forms. Use a dDialog instead."))


	def release(self):
		"""
		Instead of just destroying the object, make sure that
		we close it properly and clean up any references to it.
		"""
		self.close(True)


	def close(self, force=False):
		"""
		This method will close the form. If force = False (default)
		the beforeClose methods will be called, and these will have
		an opportunity to conditionally block the form from closing.
		If force=True, the form is closed without any chance of
		preventing it.
		"""
		if not force:
			if self._beforeClose() == False:
				return False
		# Run any cleanup code
		self.closing()
		pd = getattr(self, "_prefDialog", None)
		if pd:
			pd.release()
		# Kill the form
		self.Close(force=True)
		# pkm: I've found that modal dialogs need Destroy():
		dabo.ui.callAfter(self.safeDestroy)


	def safeDestroy(self):
		"""
		Since the callAfter to close() was added, I'm getting a lot
		of dead object warnings. This should fix that.
		"""
		if self:
			self.Destroy()


	def _beforeClose(self, evt=None):
		"""
		See if there are any pending changes in the form, if the
		form is set for checking for this. If everything's OK, call the
		hook method.
		"""
		## By the time subforms get closed, the app object can be gone,
		## resulting in not saving the window geometry. Do it here
		## to be safe.
		for child in self.Children:
			if isinstance(child, dFormMixin):
				child.saveSizeAndPosition()
		if self._floatingPanel:
			self._floatingPanel.release()
		ret = self.beforeClose(evt)
		return ret


	def beforeClose(self, evt):
		"""
		Hook method. Returning False will prevent the form from
		closing. Gives you a chance to determine the status of the form
		to see if changes need to be saved, etc.
		"""
		return True


	def closing(self):
		"""
		Stub method to be customized in subclasses. At this point,
		the form is going to close. If you need to do something that might
		prevent the form from closing, code it in the beforeClose()
		method instead.
		"""
		pass


	def afterSetMenuBar(self):
		"""Subclasses can extend the menu bar here."""
		pass


	def getMenu(self):
		"""
		Get the navigation menu for this form.

		Every form maintains an internal menu of actions appropriate to itself.
		For instance, a dForm with a primary bizobj will maintain a menu with
		'requery', 'save', 'next', etc. choices.

		This function sets up the internal menu, which can optionally be
		inserted into the mainForm's menu bar during SetFocus.
		"""
		menu = dMenu.dMenu()
		return menu


	def onEditUndo(self, evt):
		"""
		If you want your form to respond to the Undo menu item in
		the Edit menu that is installed in the Dabo base menu, override
		this method, and either return nothing, or return something other
		than False.
		"""
		return False


	def onEditRedo(self, evt):
		"""
		If you want your form to respond to the Redo menu item in
		the Edit menu that is installed in the Dabo base menu, override
		this method, and either return nothing, or return something other
		than False.
		"""
		return False


	def restoreSizeAndPosition(self):
		"""
		Restore the saved window geometry for this form.

		Ask dApp for the last saved setting of height, width, left, and top,
		and set those properties on this form.
		"""
		if not self.Application or not self.SaveRestorePosition:
			return

		name = self.getAbsoluteName()
		state = self.Application.getUserSetting("%s.windowstate" % name, self._defaultState)
		width = self.Application.getUserSetting("%s.width" % name, self._defaultWidth)
		height = self.Application.getUserSetting("%s.height" % name, self._defaultHeight)
		left = self.Application.getUserSetting("%s.left" % name, self._defaultLeft)
		top = self.Application.getUserSetting("%s.top" % name, self._defaultTop)

		if not isinstance(width, int) or not isinstance(height, int) \
				or not isinstance(left, int) or not isinstance(top, int):
			# size/position unsaved from before
			return

		if state not in ("Minimized", "Maximized", "Normal", "FullScreen"):
			state = self.WindowState

		if state == "Minimized":
			state = "Normal"

		if self.BorderResizable:
			self.Size = (width, height)

		if not self.Centered:
			# Make sure that the frame is on the visible display:
			self.Position = (left, top)
			if self.Application.Platform == "Mac":
				# Need to account for the menu bar
				minTop = 23
			else:
				minTop = 0
			dispWd, dispHt = dabo.ui.getDisplaySize()
			self.Right = min(dispWd, self.Right)
			self.Bottom = min(dispHt, self.Bottom)
			self.Left = max(0, self.Left)
			self.Top = max(minTop, self.Top)

		self.WindowState = state


	def saveSizeAndPosition(self):
		"""Save the current size and position of this form."""
		app = self.Application
		if app:
			if self.SaveRestorePosition and not self.TempForm:
				name = self.getAbsoluteName()
				state = self.WindowState
				app.setUserSetting("%s.windowstate" % name, state)

				if state == "Normal":
					# Don't save size and position when the window
					# is minimized, maximized or fullscreen because
					# windows doesn't supply correct value if the window
					# is in one of these states.
					left, top = self.Position
					width, height = self.Size
					app.setUserSetting("%s.left" % name, left)
					app.setUserSetting("%s.top" % name, top)
					app.setUserSetting("%s.width" % name, width)
					app.setUserSetting("%s.height" % name, height)


	def setStatusText(self, val, immediate=False):
		"""Set the status text to val."""
		self._setStatusText(val, not immediate)


	def layout(self):
		"""Wrap the wx sizer layout call."""
		self.Layout()
		try:
			# Call the Dabo version, if present
			self.Sizer.layout()
		except AttributeError:
			pass
		if self.Application.Platform == "Win":
			self.refresh()


	def registerObject(self, obj):
		"""
		Stores a reference to the passed object using the RegID key
		property of the object for later retrieval. You may reference the
		object as if it were a child object of this form; i.e., by using simple
		dot notation, with the RegID as the 'name' of the object.
		"""
		if hasattr(obj, "RegID"):
			id = obj.RegID
			if id in self._objectRegistry:
				if not isinstance(self._objectRegistry[id], dabo.ui.deadObject):
					raise KeyError(_("Duplicate RegID '%s' found") % id)
				else:
					del self.__dict__[id]
			self._objectRegistry[id] = obj
			if hasattr(self, id) or id in self.__dict__:
				dabo.log.error(_("RegID '%s' conflicts with existing name") % id)
			else:
				self.__dict__[id] = obj


	def getObjectByRegID(self, id):
		"""
		Given a RegID value, this will return a reference to the
		associated object, if any. If not, returns None.
		"""
		if id in self._objectRegistry:
			return self._objectRegistry[id]
		else:
			return None


	def _appendToMenu(self, menu, caption, function, bitmap=wx.NullBitmap, menuId=-1):
		return menu.append(caption, OnHit=function, bmp=bitmap)


	def appendToolBarButton(self, name, pic, toggle=False, tip="", help="",
			*args, **kwargs):
		return self.ToolBar.appendButton(name, pic, toggle=toggle, tip=tip,
				help=help, *args, **kwargs)


	def fillPreferenceDialog(self, dlg):
		"""
		This method is called with a reference to the pref dialog. It can be overridden
		in subclasses to add application-specific content to the pref dialog. To add a
		new page to the dialog, call the dialog's addCategory() method, passing the caption
		for that page. It will return a reference to the newly-created page, to which you
		then add your controls.
		"""
		pass


	def _setAbsoluteFontZoom(self, amt):
		"""
		Let the default behavior run, but then save the font zoom level to
		the user preferences file. The loading of the saved pref happens in
		the individual control (dPemMixinBase) so that the restoration of the
		control's font zoom isn't dependent on the control being created at
		form load time.
		"""
		super(dFormMixin, self)._setAbsoluteFontZoom(amt)
		if self.Application and self.SaveRestorePosition:
			self.Application.setUserSetting("%s.fontzoom"
					% self.getAbsoluteName(), self._currFontZoom)

	def _restoreFontZoom(self):
		if self.Application:
			self._currFontZoom = self.Application.getUserSetting("%s.fontzoom"
					% self.getAbsoluteName(), 0)


	def pushStatusText(self, txt, duration=None):
		"""Stores the current text of the StatusBar on a LIFO stack for later retrieval."""
		self._statusStack.append(self.StatusText)
		self.StatusText = txt
		if duration is not None:
			# Pop it after 'duration' seconds
			dabo.ui.callAfterInterval(1000*duration, self.popStatusText)


	def popStatusText(self):
		"""
		Restores the StatusText to the last value pushed on the stack. If there
		are no values in the stack, nothing is changed.
		"""
		txt = self._statusStack.pop()
		if txt:
			self.StatusText = txt
		else:
			self.StatusText = ""


	################################
	# property get/set/del functions follow:
	def _getActiveControl(self):
		# Can't use FindFocus: it returns whatever control has the keyboard focus,
		# whether or not it is a member of this form.
		return getattr(self, "_activeControl", None)

	def _setActiveControl(self, val):
		val.setFocus()


	def _getAutoUpdateStatusText(self):
		return self._autoUpdateStatusText

	def _setAutoUpdateStatusText(self, val):
		self._autoUpdateStatusText = val


	def _getBorderResizable(self):
		return (self.MDI or self._hasWindowStyleFlag(wx.RESIZE_BORDER))

	def _setBorderResizable(self, value):
		self._delWindowStyleFlag(wx.RESIZE_BORDER)
		if value:
			self._addWindowStyleFlag(wx.RESIZE_BORDER)


	def _getCentered(self):
		if hasattr(self, "_centered"):
			v = self._centered
		else:
			v = self._centered = False
		return v

	def _setCentered(self, val):
		if self._constructed():
			oldCentered = self.Centered
			self._centered = val
			if val:
				if not oldCentered:
					# Save the old position
					self._normLeft = self.Left
					self._normTop = self.Top
				# Center it!
				self.CenterOnScreen(wx.BOTH)
			else:
				# restore the old position
				self.Left = self._normLeft
				self.Top = self._normTop
		else:
			self._properties["Centered"] = val


	def _getConnection(self):
		return self._connection

	def _setConnection(self, val):
		self._connection = val


	def _getCxnName(self):
		return self._cxnName

	def _setCxnName(self, val):
		self._cxnName = val


	def _getFloatingPanel(self):
		if not self._floatingPanel:
			# Have to import it here, as it requires that dFormMixin be defined.
			from dDialog import _FloatDialog
			self._floatingPanel = _FloatDialog(owner=None, parent=self)
		return self._floatingPanel


	def _getFloatOnParent(self):
		return self._hasWindowStyleFlag(wx.FRAME_FLOAT_ON_PARENT)

	def _setFloatOnParent(self, value):
		self._delWindowStyleFlag(wx.FRAME_FLOAT_ON_PARENT)
		if value:
			self._addWindowStyleFlag(wx.FRAME_FLOAT_ON_PARENT)


	def _getIcon(self):
		try:
			return self._icon
		except AttributeError:
			return None

	def _setIcon(self, val):
		if self._constructed():
			setIconFunc = self.SetIcon
			if val is None:
				ico = wx.NullIcon
			elif isinstance(val, wx.Icon):
				ico = val
			else:
				setIconFunc = self.SetIcons
				if isinstance(val, basestring):
					icon_strs = (val,)
				else:
					icon_strs = val
				ico = wx.IconBundle()
				for icon_str in icon_strs:
					iconPath = dabo.icons.getIconFileName(icon_str)
					if iconPath and os.path.exists(iconPath):
						ext = os.path.splitext(iconPath)[1].lower()
						if ext == ".png":
							bitmapType = wx.BITMAP_TYPE_PNG
						elif ext == ".ico":
							bitmapType = wx.BITMAP_TYPE_ICO
						else:
							# punt:
							bitmapType = wx.BITMAP_TYPE_ANY
						single_ico = wx.Icon(iconPath, bitmapType)
					else:
						single_ico = wx.NullIcon
					ico.AddIcon(single_ico)
			# wx doesn't provide GetIcon()
			self._icon = val
			setIconFunc(ico)

		else:
			self._properties["Icon"] = val


	def _getIdleRefreshInterval(self):
		return self._idleRefreshInterval

	def _setIdleRefreshInterval(self, val):
		self._setIdleRefreshInterval = val


	def _getMDI(self):
		## self._mdi defined in dForm.py/dFormMain.py:
		try:
			return self._mdi
		except AttributeError:
			# dDialog, for instance
			return False


	def _getMenuBar(self):
		try:
			return self.GetMenuBar()
		except (TypeError, AttributeError):
			# dDialogs don't have menu bars
			return None

	def _setMenuBar(self, val):
		if self._constructed():
			try:
				self.SetMenuBar(val)
			except (TypeError, AttributeError):
				# dDialogs don't have menu bars
				pass
		else:
			self._properties["MenuBar"] = val


	def _getMenuBarClass(self):
		try:
			mb = self._menuBarClass
		except AttributeError:
			mb = self._menuBarClass = self.Application.DefaultMenuBarClass
		return mb

	def _setMenuBarClass(self, val):
		self._menuBarClass = val


	def _getMenuBarFile(self):
		return self._menuBarFile

	def _setMenuBarFile(self, val):
		if self._constructed():
			self._menuBarFile = self._menuBarClass = val
		else:
			self._properties["MenuBarFile"] = val


	def _getSaveRestorePosition(self):
		try:
			val = self._saveRestorePosition
		except AttributeError:
			val = self._saveRestorePosition = not isinstance(self, dabo.ui.dDialog)
		return val

	def _setSaveRestorePosition(self, val):
		self._saveRestorePosition = val


	def _getShowCaption(self):
		return self._hasWindowStyleFlag(wx.CAPTION)

	def _setShowCaption(self, value):
		self._delWindowStyleFlag(wx.CAPTION)
		if value:
			self._addWindowStyleFlag(wx.CAPTION)


	def _getShowCloseButton(self):
		return self._hasWindowStyleFlag(wx.CLOSE_BOX)

	def _setShowCloseButton(self, value):
		self._delWindowStyleFlag(wx.CLOSE_BOX)
		if value:
			self._addWindowStyleFlag(wx.CLOSE_BOX)


	def _getShowInTaskBar(self):
		return not self._hasWindowStyleFlag(wx.FRAME_NO_TASKBAR)

	def _setShowInTaskBar(self, value):
		self._delWindowStyleFlag(wx.FRAME_NO_TASKBAR)
		if not value:
			self._addWindowStyleFlag(wx.FRAME_NO_TASKBAR)


	def _getShowMaxButton(self):
		return self._hasWindowStyleFlag(wx.MAXIMIZE_BOX)

	def _setShowMaxButton(self, value):
		self._delWindowStyleFlag(wx.MAXIMIZE_BOX)
		if value:
			self._addWindowStyleFlag(wx.MAXIMIZE_BOX)


	def _getShowMenuBar(self):
		if hasattr(self, "_showMenuBar"):
			val = self._showMenuBar
		else:
			val = self._showMenuBar = True
		return val

	def _setShowMenuBar(self, val):
		self._showMenuBar = bool(val)


	def _getShowMinButton(self):
		return self._hasWindowStyleFlag(wx.MINIMIZE_BOX)

	def _setShowMinButton(self, value):
		self._delWindowStyleFlag(wx.MINIMIZE_BOX)
		if value:
			self._addWindowStyleFlag(wx.MINIMIZE_BOX)


	def _getShowStatusBar(self):
		try:
			ret = self._showStatusBar
		except AttributeError:
			ret = self._showStatusBar = True
		return ret

	def _setShowStatusBar(self, val):
		self._showStatusBar = bool(val)


	def _getShowSystemMenu(self):
		return self._hasWindowStyleFlag(wx.SYSTEM_MENU)

	def _setShowSystemMenu(self, value):
		self._delWindowStyleFlag(wx.SYSTEM_MENU)
		if value:
			self._addWindowStyleFlag(wx.SYSTEM_MENU)


	def _getShowToolBar(self):
		try:
			ret = self._showToolBar
		except AttributeError:
			# Default to no toolbar
			ret = self._showToolBar = False
		return ret

	def _setShowToolBar(self, val):
		self._showToolBar = bool(val)


	def _getSizersToOutline(self):
		if self._alwaysDrawSizerOutlines:
			return self._sizersToOutline
		else:
			ret = self._sizersToOutline or self.Sizer
			if not isinstance(ret, list):
				if ret:
					ret = [ret]
				else:
					ret = []
			return ret

	def _setSizersToOutline(self, val):
		self._sizersToOutline = val


	def _getStatusBar(self):
		try:
			return self.GetStatusBar()
		except (TypeError, AttributeError):
			# dialogs don't have status bars
			return None

	def _setStatusBar(self, val):
		try:
			self.SetStatusBar(val)
		except (TypeError, AttributeError):
			# dialogs don't have status bars
			pass


	def _getStatusBarClass(self):
		return self._statusBarClass

	def _setStatusBarClass(self, val):
		if self._constructed():
			self._statusBarClass = val
		else:
			self._properties["StatusBarClass"] = val


	def _getStatusText(self):
		ret = ""
		if sys.platform.startswith("win") and isinstance(self, wx.MDIChildFrame):
			controllingFrame = self.Application.MainForm
		else:
			controllingFrame = self
		try:
			sb = controllingFrame.GetStatusBar()
		except (AttributeError, TypeError):
			# certain dialogs don't have status bars
			sb = None
		if sb:
			ret = sb.GetStatusText()
		return ret

	@dabo.ui.deadCheck
	def _setStatusText(self, val, _callAfter=True):
		"""
		Set the text of the status bar. Dabo will decide whether to
		send the text to the main frame or this frame. This matters with MDI
		versus non-MDI forms.
		"""
		if _callAfter:
			dabo.ui.callAfterInterval(250, self._setStatusText, val, _callAfter=False)
			return
		if sys.platform.startswith("win") and isinstance(self, wx.MDIChildFrame):
			controllingFrame = self.Application.MainForm
		else:
			controllingFrame = self

		try:
			statusBar = controllingFrame.GetStatusBar()
		except (AttributeError, TypeError):
			statusBar = None

		if statusBar:
			sb = controllingFrame.GetStatusBar()
			sb.SetStatusText(val)
			statusBar.Update()


	def _getStayOnTop(self):
		return self._hasWindowStyleFlag(wx.STAY_ON_TOP)

	def _setStayOnTop(self, value):
		self._delWindowStyleFlag(wx.STAY_ON_TOP)
		if value:
			self._addWindowStyleFlag(wx.STAY_ON_TOP)


	def _getTempForm(self):
		return self._tempForm

	def _setTempForm(self, val):
		if self._constructed():
			self._tempForm = val
		else:
			self._properties["TempForm"] = val


	def _getTinyTitleBar(self):
		return self._hasWindowStyleFlag(wx.FRAME_TOOL_WINDOW)

	def _setTinyTitleBar(self, value):
		self._delWindowStyleFlag(wx.FRAME_TOOL_WINDOW)
		if value:
			self._addWindowStyleFlag(wx.FRAME_TOOL_WINDOW)


	def _getToolBar(self):
		try:
			return self.GetToolBar()
		except (AttributeError, TypeError):
			# We are probably a dialog or some other form that doesn't support ToolBars.
			return None

	def _setToolBar(self, val):
		self.SetToolBar(val)

	def _getWindowState(self):
		try:
			if self.IsFullScreen():
				return "FullScreen"
			elif self.IsMaximized():
				return "Maximized"
			elif self.IsIconized():
				return "Minimized"
			else:
				return "Normal"
		except AttributeError:
			# These only work on Windows, I fear
			return "Normal"

	def _setWindowState(self, value):
		if self._constructed():
			lowvalue = ustr(value).lower().strip()
			vis = self.Visible
			if lowvalue == "normal":
				if self.IsFullScreen():
					self.ShowFullScreen(False)
				elif self.IsMaximized():
					self.Maximize(False)
				elif self.IsIconized():
					self.Iconize(False)
				else:
					# window already normal, but just in case:
					self.Maximize(False)
			elif lowvalue == "minimized":
				self.Iconize()
			elif lowvalue == "maximized":
				self.Maximize()
			elif lowvalue == "fullscreen":
				self.ShowFullScreen(True)
			else:
				self.unlockDisplay()
				raise ValueError("The only possible values are "
								"'Normal', 'Minimized', 'Maximized', and 'FullScreen'")
		else:
			self._properties["WindowState"] = value


	# property definitions follow:
	ActiveControl = property(_getActiveControl, _setActiveControl, None,
			_("Contains a reference to the active control on the form, or None."))

	AutoUpdateStatusText = property(_getAutoUpdateStatusText, _setAutoUpdateStatusText, None,
			_("Does this form update the status text with the current record position?  (bool)"))

	BorderResizable = property(_getBorderResizable, _setBorderResizable, None,
			_("""Specifies whether the user can resize this form.  (bool).

			The default is True for dForm and False for dDialog."""))

	Centered = property(_getCentered, _setCentered, None,
			_("Centers the form on the screen when set to True.  (bool)"))

	Connection = property(_getConnection, _setConnection, None,
			_("The connection to the database used by this form  (dConnection)"))

	CxnName = property(_getCxnName, _setCxnName, None,
			_("Name of the connection used for data access  (str)"))

	FloatingPanel = property(_getFloatingPanel, None, None,
			_("""Small modal dialog that is designed to be used for temporary displays,
			similar to context menus, but which can contain any controls.
			(read-only) (dDialog)"""))

	FloatOnParent = property(_getFloatOnParent, _setFloatOnParent, None,
			_("Specifies whether the form stays on top of the parent or not."))

	Icon = property(_getIcon, _setIcon, None,
			_("""Specifies the icon for the form.

			The value passed can be a binary icon bitmap, a filename, or a
			sequence of filenames. Providing a sequence of filenames pointing to
			icons at expected dimensions like 16, 22, and 32 px means that the
			system will not have to scale the icon, resulting in a much better
			appearance."""))

	IdleRefreshInterval = property(_getIdleRefreshInterval, _setIdleRefreshInterval, None,
			_("""Controls how often the form is refreshed when idle.

			If you notice a lot of flicker when a form is 'doing nothing', increase
			this value. Likewise, if you notice that changes are not reflected as
			readily as you wish, decrease it. The value is in milliseconds; the
			default is 1000.  (int)"""))

	MDI = property(_getMDI, None, None,
			_("""Returns True if this is a MDI (Multiple Document Interface) form.  (bool)

			Otherwise, returns False if this is a SDI (Single Document Interface) form.
			Users on Microsoft Windows seem to expect MDI, while on other platforms SDI is
			preferred.

			See also: the dabo.MDI global setting.  (bool)"""))

	MenuBar = property(_getMenuBar, _setMenuBar, None,
			_("Specifies the menu bar instance for the form."))

	MenuBarClass = property(_getMenuBarClass, _setMenuBarClass, None,
			_("Specifies the menu bar class to use for the form, or None."))

	MenuBarFile = property(_getMenuBarFile, _setMenuBarFile, None,
			_("Path to the .mnxml file that defines this form's menu bar  (str)"))

	SaveRestorePosition = property(_getSaveRestorePosition,
			_setSaveRestorePosition, None,
			_("""Specifies whether the form's position and size as set by the user
				will get saved and restored in the next session. Default is True for
				forms and False for dialogs."""))

	ShowCaption = property(_getShowCaption, _setShowCaption, None,
			_("Specifies whether the caption is displayed in the title bar. (bool)."))

	ShowCloseButton = property(_getShowCloseButton, _setShowCloseButton, None,
			_("Specifies whether a close button is displayed in the title bar. (bool)."))

	ShowInTaskBar = property(_getShowInTaskBar, _setShowInTaskBar, None,
			_("Specifies whether the form is shown in the taskbar.  (bool)."))

	ShowMaxButton = property(_getShowMaxButton, _setShowMaxButton, None,
			_("Specifies whether a maximize button is displayed in the title bar. (bool)."))

	ShowMenuBar = property(_getShowMenuBar, _setShowMenuBar, None,
			_("Specifies whether a menubar is created and shown automatically."))

	ShowMinButton = property(_getShowMinButton, _setShowMinButton, None,
			_("Specifies whether a minimize button is displayed in the title bar. (bool)."))

	ShowStatusBar = property(_getShowStatusBar, _setShowStatusBar, None,
			_("Specifies whether the status bar gets automatically created."))

	ShowSystemMenu = property(_getShowSystemMenu, _setShowSystemMenu, None,
			_("Specifies whether a system menu is displayed in the title bar. (bool)."))

	ShowToolBar = property(_getShowToolBar, _setShowToolBar, None,
			_("Specifies whether the Tool bar gets automatically created."))

	SizersToOutline = property(_getSizersToOutline, _setSizersToOutline, None,
			_("""When drawing the outline of sizers, the sizer(s) to draw.
			Default=self.Sizer  (dSizer)"""))

	StatusBar = property(_getStatusBar, _setStatusBar, None,
			_("Status bar for this form. (dStatusBar)"))

	StatusBarClass = property(_getStatusBarClass, _setStatusBarClass, None,
			_("Class to be used for this form's status bar. Default=dStatusBar (dStatusBar)"))

	StatusText = property(_getStatusText, _setStatusText, None,
			_("Text displayed in the form's status bar. (string)"))

	StayOnTop = property(_getStayOnTop, _setStayOnTop, None,
			_("Keeps the form on top of all other forms. (bool)"))

	TempForm = property(_getTempForm, _setTempForm, None,
			_("""Used to indicate that this is a temporary form, and that its settings
			should not be persisted. Default=False  (bool)"""))

	TinyTitleBar = property(_getTinyTitleBar, _setTinyTitleBar, None,
			_("Specifies whether the title bar is small, like a tool window. (bool)."))

	ToolBar = property(_getToolBar, _setToolBar, None,
			_("Tool bar for this form. (dToolBar)"))

	WindowState = property(_getWindowState, _setWindowState, None,
			_("""Specifies the current state of the form. (int)

					Normal
					Minimized
					Maximized
					FullScreen"""))


	DynamicAutoUpdateStatusText = makeDynamicProperty(AutoUpdateStatusText)
	DynamicBorderResizable = makeDynamicProperty(BorderResizable)
	DynamicCentered = makeDynamicProperty(Centered)
	DynamicConnection = makeDynamicProperty(Connection)
	DynamicFloatOnParent = makeDynamicProperty(FloatOnParent)
	DynamicIcon = makeDynamicProperty(Icon)
	DynamicMenuBar = makeDynamicProperty(MenuBar)
	DynamicShowCaption = makeDynamicProperty(ShowCaption)
	DynamicShowStatusBar = makeDynamicProperty(ShowStatusBar)
	DynamicStatusBar = makeDynamicProperty(StatusBar)
	DynamicStatusText = makeDynamicProperty(StatusText)
	DynamicToolBar = makeDynamicProperty(ToolBar)
	DynamicWindowState = makeDynamicProperty(WindowState)
