# -*- coding: utf-8 -*-
import sys
import time
import types
import math
import wx
import dabo
from dabo.dLocalize import _
from dabo.lib.utils import ustr
from dabo.ui.dPemMixinBase import dPemMixinBase
import dabo.dEvents as dEvents
import dabo.dException as dException
import dabo.dColors as dColors
import dKeys
from dabo.dObject import dObject
from dabo.ui import makeDynamicProperty
from dabo.lib.utils import dictStringify



class dPemMixin(dPemMixinBase):
	"""
	Provides Property/Event/Method interfaces for dForms and dControls.

	Subclasses can extend the property sheet by defining their own get/set
	functions along with their own property() statements.
	"""
	_call_beforeInit, _call_afterInit, _call_initProperties = False, False, False
	_layout_on_set_caption = False

	def __init__(self, preClass=None, parent=None, properties=None,
			attProperties=None, srcCode=None, *args, **kwargs):
		# This is the major, common constructor code for all the dabo/ui/uiwx
		# classes. The __init__'s of each class are just thin wrappers to this
		# code.
		# Holds the properties passed in the constructor
		self._properties = {}
		# Holds the keyword event bindings passed in the constructor
		self._kwEvents = {}
		# Holds event binding expressed as strings to be eval'd after this object
		# has been constructed.
		self._delayedEventBindings = []
		# Transparency level
		self._transparency = 255
		# Time to change transparency
		self._transparencyDelay = 0.25
		# DataControl enabling/disabling helper attribute.
		self._uiDisabled = False

		# There are a few controls that don't yet support 3-way inits (grid, for
		# one). These controls will send the wx classref as the preClass argument,
		# and we'll call __init__ on it when ready. We can tell if we are in a
		# three-way init situation based on whether or not preClass is a function
		# type.
		threeWayInit = (type(preClass) == types.FunctionType)

		# Dictionary to keep track of Dynamic properties
		self._dynamic = {}
		if threeWayInit:
			# Instantiate the wx Pre object
			pre = preClass()
		else:
			pre = None

		if srcCode:
			self._addCodeAsMethod(srcCode)

		self._beforeInit(pre)
		# If the _EventTarget property is passed, extract it before any of the other
		# property-processing code runs.
		self._eventTarget = self._extractKey((properties, attProperties, kwargs), "_EventTarget",
				defaultVal=self)
		# Lots of useful wx props are actually only settable before the
		# object is fully constructed. The self._preInitProperties dict keeps
		# track of those during the pre-init phase, to finally send the
		# contents of it to the wx constructor. Our property setters know
		# if we are in pre-init or not, and instead of trying to modify
		# the prop will instead add the appropriate entry to the _preInitProperties
		# dict. Additionally, there are certain wx properties that are required,
		# and we include those in the _preInitProperties dict as well so they may
		# be modified by our pre-init method hooks if needed:
		self._preInitProperties = {"parent": parent}
		for arg, default in (("style", 0), ("id", -1)):
			try:
				self._preInitProperties[arg] = kwargs[arg]
				del kwargs[arg]
			except KeyError:
				self._preInitProperties[arg] = default

		self._initProperties()

		# Now that user code has had an opportunity to set the properties, we can
		# see if there are properties sent to the constructor which will augment
		# or override the properties as currently set.

		# The keyword properties can come from either, both, or none of:
		#    + the properties dict
		#    + the kwargs dict
		# Get them sanitized into one dict:
		if properties is not None:
			# Override the class values
			for k,v in properties.items():
				self._properties[k] = v
		properties = self._extractKeywordProperties(kwargs, self._properties)

		self._extractKeyWordEventBindings(kwargs, self._kwEvents)
		# Objects created from XML files will have their props passed
		# in the 'attProperties' parameter, in which all values are strings.
		# Convert these to the properties dict.

		try:
			builtinNames = __builtins__.keys()
		except AttributeError:
			# '__builtins__' is a module here
			builtinNames = dir(__builtins__)

		if attProperties:
			for prop, val in attProperties.items():
				if prop in properties:
					# attProperties has lower precedence, so skip it
					continue
				# Note: we may need to add more string props here.
				if (val in builtinNames) and (prop in ("Caption", "DataSource",
						"DataField", "FontFace", "Icon", "Picture", "RegID", "ToolTipText")):
					# It's a string that happens to be the same as a built-in name
					attVal = val
				else:
					try:
						attVal = eval(val)
					except (TypeError, SyntaxError, NameError, AttributeError):
						attVal = val
				properties[prop] = attVal
		properties = dictStringify(properties)

		# Hacks to fix up various things:
		import dMenuBar, dMenuItem, dMenu, dSlidePanelControl, dToggleButton
		if wx.VERSION >= (2, 8, 8):
			import dBorderlessButton
		if isinstance(self, (dMenuItem.dMenuItem, dMenuItem.dSeparatorMenuItem)):
			# Hack: wx.MenuItem doesn't take a style arg,
			# and the parent arg is parentMenu.
			del self._preInitProperties["style"]
			self._preInitProperties["parentMenu"] = parent
			del self._preInitProperties["parent"]
			if isinstance(self, dMenuItem.dSeparatorMenuItem):
				del(self._preInitProperties["id"])
				for remove in ("HelpText", "Icon", "kind"):
					self._extractKey((properties, self._properties, kwargs), remove)
		elif isinstance(self, (dMenu.dMenu, dMenuBar.dMenuBar)):
			# Hack: wx.Menu has no style, parent, or id arg.
			del(self._preInitProperties["style"])
			del(self._preInitProperties["id"])
			del(self._preInitProperties["parent"])
		elif isinstance(self, (wx.Timer, )):
			del(self._preInitProperties["style"])
			del(self._preInitProperties["id"])
			del(self._preInitProperties["parent"])
		elif isinstance(self, (dabo.ui.dSlidePanel, dabo.ui.dSlidePanelControl,
				dSlidePanelControl.dSlidePanel, dSlidePanelControl.dSlidePanelControl)):
			# Hack: the Slide Panel classes have no style arg.
			del self._preInitProperties["style"]
			# This is needed because these classes require a 'parent' param.
			kwargs["parent"] = parent
		elif wx.VERSION >= (2, 8, 8) and isinstance(self, (wx.lib.platebtn.PlateButton)):
			self._preInitProperties["id_"] = self._preInitProperties["id"]
			del self._preInitProperties["id"]
		# This is needed when running from a saved design file
		self._extractKey((properties, self._properties), "designerClass")
		# This attribute is used when saving code with a design file
		self._extractKey((properties, self._properties), "code-ID")
		# Remove the CxnFile property that is no longer used
		self._extractKey((properties, self._properties), "CxnFile")

		# The user's subclass code has had a chance to tweak the init properties.
		# Insert any of those into the arguments to send to the wx constructor:
		properties = self._setInitProperties(**properties)
		for prop in self._preInitProperties.keys():
			kwargs[prop] = self._preInitProperties[prop]
		# Allow the object a chance to add any required parms, such as OptionGroup
		# which needs a choices parm in order to instantiate.
		kwargs = self._preInitUI(kwargs)

		# Do the init:
		if threeWayInit:
			pre.Create(*args, **kwargs)
		elif preClass is None:
			pass
		else:
			preClass.__init__(self, *args, **kwargs)

		if threeWayInit:
			self.PostCreate(pre)

		self._pemObject = self

		if self._constructed():
			# (some objects could have overridden _constructed() and don't want
			# us to call _setNameAndProperties() here..)
			self._setNameAndProperties(properties, **kwargs)

		self._initEvents()
		self._afterInit()

		dPemMixinBase.__init__(self)  ## don't use super(), or wx init called 2x.

		if dabo.fastNameSet:
			# Event AutoBinding is set to happen when the Name property changes, but
			# with fastNameSet on, that never happened. Call it manually:
			self.autoBindEvents()

		# Create a method that gets called after all the other objects that are being
		# added have completed. A good use of this is when you want to call code in the
		# afterInit() of a form, but the controls it needs to work with haven't yet been
		# created. This method will be called after all the form objects have finished
		# instantiating. The framework-level _afterInitAll() will call the user-customizable
		# hook method afterInitAll().
		dabo.ui.callAfter(self._afterInitAll)

		# Finally, at the end of the init cycle, raise the Create event
		self.raiseEvent(dEvents.Create)


	def _setNameAndProperties(self, properties, **kwargs):
		"""
		If a Name isn't given, a default name will be used, and it'll
		autonegotiate by adding an integer until it is a unique name.
		If a Name is given explicitly, a NameError will be raised if
		the given Name isn't unique among siblings.
		"""
		if not dabo.fastNameSet:
			name, _explicitName = self._processName(kwargs, self.__class__.__name__)
			self._initName(name, _explicitName=_explicitName)

		# Add any properties that were re-set
		properties.update(self._properties)
		# Set the properties *before* calling the afterInit hook
		self._setProperties(properties)

		# Set any passed event bindings
		self._setKwEventBindings(self._kwEvents)


	def _setProperties(self, properties):
		"""Provides pre- and post- hooks for the setProperties() method."""
		## Typically used to remove Designer props that don't appear in
		## runtime classes.
		if self._beforeSetProperties(properties) is False:
			return
		self._properties = {}
		self.setProperties(properties)
		self._afterSetProperties()

	def _beforeSetProperties(self, properties):
		# By default, just call the hook
		return self.beforeSetProperties(properties)
	def _afterSetProperties(self):
		# By default, just call the hook
		self.afterSetProperties()
	def beforeSetProperties(self, properties): pass
	def afterSetProperties(self): pass


	def _constructed(self):
		"""Returns True if the ui object has been fully created yet, False otherwise."""
		try:
			return self is self._pemObject
		except Exception, e:
			return False


	def _beforeInit(self, pre):
		self._acceleratorTable = {}
		self._name = "?"
		self._pemObject = pre
		self._needRedraw = True
		self._inRedraw = False
		self._borderColor = (0, 0, 0)
		self._borderWidth = 0
		self._borderLineStyle = "Solid"
		self._minimumHeight = 10
		self._minimumWidth = 10
		self._maximumHeight = -1
		self._maximumWidth = -1

		# Do we need to clear the background before redrawing? Most cases will be
		# no, but if you have problems with drawings leaving behind unwanted
		# debris, set this to True
		self.autoClearDrawings = False

		# Reference to the border-drawing object
		self._border = None

		# Store the caption internally
		self._caption = ""

		# Flag that gets set to True when the object is being Destroyed
		self._finito = False

		# Dict to hold key bindings
		self._keyBindings = {}

		# Unique identifier attribute, if needed
		self._registryID = ""

		# List of all drawn objects
		self._drawnObjects = []

		# Mouse click events rely on these:
		self._mouseLeftDown = False
		self._mouseRightDown = False
		self._mouseMiddleDown = False

		# Does this control fire its onHover() method when the mouse enters?
		self._hover = False
		self._hoverTimer = None

		# Handlers for drag/drop
		self._droppedFileHandler = None
		self._droppedTextHandler = None
		self._dropTarget = None

		# Records the number of display lock calls on this object
		self._displayLockCount = 0

		# _beforeInit hook for Class Designer code
		self._beforeInitDesignerHook()

		# Call the user hook
		self.beforeInit()


	def _beforeInitDesignerHook(self): pass


	def _afterInit(self):
		if not wx.HelpProvider.Get():
			# The app hasn't set a help provider, and one is needed
			# to be able to save/restore help text.
			wx.HelpProvider.Set(wx.SimpleHelpProvider())
		self.afterInit()
		if self.Form and self.Form.SaveRestorePosition:
			self._restoreFontZoom()


	def _afterInitAll(self):
		"""This is the framework-level hook. It calls the developer-specific method."""
		if not self:
			return
		self.afterInitAll()
	def afterInitAll(self): pass


	def _preInitUI(self, kwargs):
		"""
		Subclass hook, for internal Dabo use.
		Some wx objects (RadioBox) need certain props forced if they hadn't been
		set by the user either as a parm or in beforeInit().
		"""
		return kwargs


	def _getInitPropertiesList(self):
		"""
		Subclass hook, for internal Dabo use.

		Some properties of wx objects are only settable by sending to the
		constructor. This tells Dabo which properties to specially handle.
		"""
		return ("Alignment", "BorderStyle", "ButtonClass", "MultipleSelect",
				"Orientation", "PasswordEntry", "ShowLabels", "SizerClass", "TabPosition",
				"CancelButton")


	def _setInitProperties(self, **_properties):
		# Called before the wx object is fully instantiated. Allows for sending
		# wx style properties to the constructor. This process will set all the
		# init properties in the dict, and remove them from the dict so that
		# when setProperties() is called after the wx object is instantiated,
		# the style props won't be set a second time.
		initProps = self._getInitPropertiesList()
		for prop in _properties.keys():
			if prop in initProps:
				self.setProperties({prop:_properties[prop]})
				del(_properties[prop])
		return _properties


	def _initEvents(self):
		# Bind wx events to handlers that re-raise the Dabo events:
		targ = self._EventTarget

		# Bind EVT_WINDOW_DESTROY twice: once to parent, and once to self. Binding
		# to the parent allows for attribute access of the child in the dEvents.Destroy
		# handler, in most cases. In some cases (panels at least), the self binding fires
		# first. We sort it out in __onWxDestroy, only reacting to the first destroy
		# event.
		parent = self.GetParent()
		if parent:
			parent.Bind(wx.EVT_WINDOW_DESTROY, self.__onWxDestroy)
		self.Bind(wx.EVT_WINDOW_DESTROY, self.__onWxDestroy)
		self.Bind(wx.EVT_IDLE, self.__onWxIdle)
		self.Bind(wx.EVT_MENU_OPEN, targ.__onWxMenuOpen)

		if isinstance(self, dabo.ui.dGrid):
			## Ugly workaround for grids not firing focus events from the keyboard
			## correctly.
			self._lastGridFocusTimestamp = 0.0
			self.GetGridCornerLabelWindow().Bind(wx.EVT_SET_FOCUS, self.__onWxGotFocus)
			self.GetGridColLabelWindow().Bind(wx.EVT_SET_FOCUS, self.__onWxGotFocus)
			self.GetGridRowLabelWindow().Bind(wx.EVT_SET_FOCUS, self.__onWxGotFocus)
			self.GetGridWindow().Bind(wx.EVT_SET_FOCUS, self.__onWxGotFocus)

		# These need to be applied to both
		self.Bind(wx.EVT_SET_FOCUS, targ.__onWxGotFocus)
		self.Bind(wx.EVT_KILL_FOCUS, targ.__onWxLostFocus)
		self.Bind(wx.EVT_MOVE, targ.__onWxMove)
		self.Bind(wx.EVT_ENTER_WINDOW, targ.__onWxMouseEnter)
		self.Bind(wx.EVT_LEAVE_WINDOW, targ.__onWxMouseLeave)
		self.Bind(wx.EVT_MOTION, targ.__onWxMouseMove)
		self.Bind(wx.EVT_MOUSEWHEEL, targ.__onWxMouseWheel)
		if targ is not self:
			self.Bind(wx.EVT_SET_FOCUS, self.__onWxGotFocus)
			self.Bind(wx.EVT_KILL_FOCUS, self.__onWxLostFocus)
			self.Bind(wx.EVT_MOVE, self.__onWxMove)
			self.Bind(wx.EVT_ENTER_WINDOW, self.__onWxMouseEnter)
			self.Bind(wx.EVT_LEAVE_WINDOW, self.__onWxMouseLeave)
			self.Bind(wx.EVT_MOTION, self.__onWxMouseMove)
			self.Bind(wx.EVT_MOUSEWHEEL, self.__onWxMouseWheel)

		self.Bind(wx.EVT_CHAR, targ.__onWxKeyChar)
		self.Bind(wx.EVT_KEY_DOWN, targ.__onWxKeyDown)
		self.Bind(wx.EVT_KEY_UP, targ.__onWxKeyUp)

		self.Bind(wx.EVT_LEFT_DOWN, targ.__onWxMouseLeftDown)
		self.Bind(wx.EVT_LEFT_UP, targ.__onWxMouseLeftUp)
		self.Bind(wx.EVT_LEFT_DCLICK, targ.__onWxMouseLeftDoubleClick)
		self.Bind(wx.EVT_RIGHT_DOWN, targ.__onWxMouseRightDown)
		self.Bind(wx.EVT_RIGHT_UP, targ.__onWxMouseRightUp)
		self.Bind(wx.EVT_RIGHT_DCLICK, targ.__onWxMouseRightDoubleClick)
		self.Bind(wx.EVT_MIDDLE_DOWN, targ.__onWxMouseMiddleDown)
		self.Bind(wx.EVT_MIDDLE_UP, targ.__onWxMouseMiddleUp)
		self.Bind(wx.EVT_MIDDLE_DCLICK, targ.__onWxMouseMiddleDoubleClick)

		self.Bind(wx.EVT_CONTEXT_MENU, targ.__onWxContextMenu)

		self.Bind(wx.EVT_PAINT, self.__onWxPaint)
		self.Bind(wx.EVT_ERASE_BACKGROUND, self.__onWxEraseBackground)
		self.Bind(wx.EVT_SIZE, self.__onWxResize)

		self.bindEvent(dEvents.Create, self.__onCreate)
		self.bindEvent(dEvents.ChildBorn, self.__onChildBorn)

		self.bindEvent(dEvents.MouseEnter, targ.__onMouseEnter)
		self.bindEvent(dEvents.MouseLeave, targ.__onMouseLeave)

		try:
			self.Parent.bindEvent(dEvents.Update, self.__onUpdate)
			self.Parent.bindEvent(dEvents.Resize, self.__onResize)
		except AttributeError:
			## pkm: I don't think we want to bind this to self, because then you
			##      will have recursion in the event handling. We are either a form
			##      or somehow our Parent isn't a Dabo object. Just do nothing...
			#self.bindEvent(dEvents.Update, self.__onUpdate)
			pass

		self.initEvents()

		# Handle delayed event bindings
		if self._delayedEventBindings:
			dabo.ui.callAfter(self._bindDelayed)


	def _bindDelayed(self):
		for evt, mthdString in self._delayedEventBindings:
			if not mthdString:
				# Empty method string; this is a sign of a bug in the UI code.
				# Log it and continue
				nm = self.Name
				dabo.log.error(_("Empty Event Binding: Object: %(nm)s; Event: %(evt)s") % locals())
				continue
			try:
				mthd = eval(mthdString)
			except (AttributeError, NameError), e:
				dabo.log.error(_("Could not evaluate method '%(mthdString)s': %(e)s") % locals())
				continue
			self.bindEvent(evt, mthd)

	def _popStatusText(self):
		if self.StatusText and self.Form is not None:
			self.Form.setStatusText("")

	def _pushStatusText(self):
		st = self.StatusText
		if st and self.Form is not None:
			self.Form.setStatusText(st)


	def __onMouseEnter(self, evt):
		if self._hover:
			if self._hoverTimer is None:
				self._hoverTimer = dabo.ui.callEvery(100, self._checkMouseOver)
			self._hoverTimer.start()
			self.onHover(evt)


	def __onMouseLeave(self, evt):
		if self._hover:
			if self._hoverTimer:
				self._hoverTimer.release()
				self._hoverTimer = None
			self.endHover(evt)


	# These are stub methods, to be coded in the classes that
	# need them.
	def onHover(self, evt=None): pass
	def endHover(self, evt=None): pass


	def _checkMouseOver(self):
		"""
		Called as part of the Hover mechanism for determining if the mouse
		is no longer over the object.
		"""
		if not self:
			# Object has been released
			self._hoverTimer = None
			return
		mx, my = self.Parent.ScreenToClient(wx.GetMousePosition())
		if not self.posIsWithin(mx, my):
			self.__onMouseLeave(None)


	def posIsWithin(self, xpos, ypos=None):
		if ypos is None:
			if isinstance(xpos, (tuple, list)):
				xpos, ypos = xpos
		ret = (self.Left <= xpos <= self.Right) and (self.Top <= ypos <= self.Bottom)
		return ret


	def __onCreate(self, evt):
		if self.Parent and hasattr(self.Parent, "raiseEvent"):
			self.Parent.raiseEvent(dEvents.ChildBorn, None, child=self)


	def __onChildBorn(self, evt):
		"""evt.Child will contain the reference to the new child."""
		pass


	def __onWxDestroy(self, evt):
		if getattr(self, "_destroyAlreadyFired", False):
			# we bind twice, once to parent and once to self, because some wxPython
			# objects are still accessible this way while others are not.
			return
		self._finito = (self is evt.GetEventObject())
		self._destroyAlreadyFired = True
		try:
			self.raiseEvent(dEvents.Destroy, evt)
		except dabo.ui.deadObjectException:
			pass

	def __onWxIdle(self, evt):
		if self._needRedraw:
			self._redraw()
		self.raiseEvent(dEvents.Idle, evt)


	def __onWxMenuOpen(self, evt):
		menu = evt.GetMenu()
		if menu and isinstance(menu, dabo.ui.dMenu):
			menu.raiseEvent(dEvents.MenuOpen, evt)
		evt.Skip()


	def __onWxGotFocus(self, evt):
		try:
			self.Form._controlGotFocus(self)
		except AttributeError:
			# 'Form' is None
			pass
		self._pushStatusText()
		if isinstance(self, dabo.ui.dGrid):
			## Continuation of ugly workaround for grid focus event. Only raise the
			## Dabo event if we are reasonably sure it isn't a repeat.
			prev = self._lastGridFocusTimestamp
			now = self._lastGridFocusTimestamp = time.time()
			if now-prev < .05:
				return
		self.raiseEvent(dEvents.GotFocus, evt)


	def __onWxKeyChar(self, evt):
		if not (isinstance(self, dabo.ui.dComboBox) and evt.KeyCode == 9):
			self.raiseEvent(dEvents.KeyChar, evt)


	def __onWxKeyUp(self, evt):
		self.raiseEvent(dEvents.KeyUp, evt)


	def __onWxKeyDown(self, evt):
		self.raiseEvent(dEvents.KeyDown, evt)


	def __onWxLostFocus(self, evt):
		if self._finito:
			return
		self._popStatusText()
		self.raiseEvent(dEvents.LostFocus, evt)


	def __onWxMove(self, evt):
		if self._finito:
			return
		self.raiseEvent(dEvents.Move, evt)


	def __onWxMouseEnter(self, evt):
		self._pushStatusText()
		self.raiseEvent(dEvents.MouseEnter, evt)


	def __onWxMouseLeave(self, evt):
		self._popStatusText()
		self._mouseLeftDown, self._mouseRightDown = False, False
		self.raiseEvent(dEvents.MouseLeave, evt)


	def __onWxMouseMove(self, evt):
		self.raiseEvent(dEvents.MouseMove, evt)


	def __onWxMouseWheel(self, evt):
		"""
		Some platforms do not properly determine the object that receives
		the scroll event. On Windows, for example, the event is raised by either
		a) the control that has focus, or b) the form. The code in this method
		ensures that the object below the mouse receives the event.
		"""
		pos = evt.GetPosition()
		obj = dabo.ui.getObjectAtPosition(self.absoluteCoordinates(pos))
		evt.SetEventObject(obj)
		if obj is not None:
			obj.raiseEvent(dEvents.MouseWheel, evt)


	def __onWxMouseLeftDown(self, evt):
		self.raiseEvent(dEvents.MouseLeftDown, evt)
		self._mouseLeftDown = True


	def __onWxMouseLeftUp(self, evt):
		self.raiseEvent(dEvents.MouseLeftUp, evt)
		if self._mouseLeftDown:
			# mouse went down and up in this control: send a click:
			self.raiseEvent(dEvents.MouseLeftClick, evt)
			self._mouseLeftDown = False


	def __onWxMouseLeftDoubleClick(self, evt):
		self.raiseEvent(dEvents.MouseLeftDoubleClick, evt)


	def __onWxMouseRightDown(self, evt):
		self._mouseRightDown = True
		self.raiseEvent(dEvents.MouseRightDown, evt)


	def __onWxMouseRightUp(self, evt):
		self.raiseEvent(dEvents.MouseRightUp, evt)
		if self._mouseRightDown:
			# mouse went down and up in this control: send a click:
			self.raiseEvent(dEvents.MouseRightClick, evt)
			self._mouseRightDown = False


	def __onWxMouseRightDoubleClick(self, evt):
		self.raiseEvent(dEvents.MouseRightDoubleClick, evt)


	def __onWxMouseMiddleDown(self, evt):
		self._mouseMiddleDown = True
		self.raiseEvent(dEvents.MouseMiddleDown, evt)


	def __onWxMouseMiddleUp(self, evt):
		self.raiseEvent(dEvents.MouseMiddleUp, evt)
		if self._mouseMiddleDown:
			# mouse went down and up in this control: send a click:
			self.raiseEvent(dEvents.MouseMiddleClick, evt)
			self._mouseMiddleDown = False


	def __onWxMouseMiddleDoubleClick(self, evt):
		self.raiseEvent(dEvents.MouseMiddleDoubleClick, evt)

	def __onWxContextMenu(self, evt):
		# Hide a problem on Windows where a single context event will
		# be raised twice.
		now = time.time()
		if (not hasattr(self, "_lastContextMenuTime") or
				(now - self._lastContextMenuTime) > .001):
			self._lastContextMenuTime = time.time()
			self.raiseEvent(dEvents.ContextMenu, evt)


	def __onWxPaint(self, evt):
		if self._finito:
			return
# 		def __setNeedRedraw():
# 			try:
# 				self._needRedraw = bool(self._drawnObjects)
# 			except dabo.ui.deadObjectException:
# 				pass
# 		dabo.ui.callAfterInterval(50, __setNeedRedraw)
		self._needRedraw = (not self._inRedraw) and bool(self._drawnObjects)
		self.raiseEvent(dEvents.Paint, evt)


	def __onWxEraseBackground(self, evt):
		if self._finito:
			return
		self.raiseEvent(dEvents.BackgroundErased, evt)


	def __onWxResize(self, evt):
		if self._finito:
			return
		self._needRedraw = bool(self._drawnObjects)
		if sys.platform.startswith("win") and isinstance(self, (dabo.ui.dFormMixin,)):
			dabo.ui.callAfterInterval(200, self.update)
		self.raiseEvent(dEvents.Resize, evt)


	def bindKey(self, keyCombo, callback, **kwargs):
		"""
		Bind a key combination such as "ctrl+c" to a callback function.

		See dKeys.keyStrings for the valid string key codes.
		See dKeys.modifierStrings for the valid modifier codes.

		Examples::

			# When user presses <esc>, close the form:
			form.bindKey("esc", form.Close)

			# When user presses <ctrl><alt><w>, close the form:
			form.bindKey("ctrl+alt+w", form.Close)

		"""
		mods, key, flags = dabo.ui.dKeys.resolveKeyCombo(keyCombo, True)
		upMods = [mm.upper() for mm in mods]
		try:
			keyCode = dKeys.keyStrings[key.lower()]
		except KeyError:
			# It isn't a special key. Get the code from the ascii table:
			keyCode = ord(key)

		# If the key combo was previously registered, we need to make sure the
		# event binding for the old id is removed:
		self.unbindKey(keyCombo)

		# Now, set up the accelerator table with this new entry:
		anId = wx.NewId()
		table = self._acceleratorTable
		table[keyCombo] = (flags, keyCode, anId)
		self.SetAcceleratorTable(wx.AcceleratorTable(table.values()))
		# Store the modifier keys that will have been pressed to trigger
		# this key event. They will be included in the Dabo event that is
		# passed to the callback function.
		ed = {}
		ed["keyCode"] = keyCode
		ed["rawKeyCode"] = keyCode
		ed["rawKeyFlags"] = flags
		ed["hasModifiers"] = bool(mods)
		ed["altDown"] = "ALT" in upMods
		ed["commandDown"] = "CMD" in upMods
		ed["controlDown"] = "CTRL" in upMods
		ed["metaDown"] = "META" in upMods
		ed["shiftDown"] = "SHIFT" in upMods
		ed.update(kwargs)
		bnd = {"callback" : callback, "eventData" : ed}
		self._keyBindings[anId] = bnd
		self.Bind(wx.EVT_MENU, self._keyCallback, id=anId)


	def _keyCallback(self, evt):
		bnd = self._keyBindings[evt.GetId()]
		keyEvent = dEvents.KeyEvent(None)
		keyEvent.EventData = bnd["eventData"]
		try:
			callback = bnd["callback"]
		except KeyError:
			# binding doesn't exist
			return
		callback(keyEvent)


	def Show(self, show=True):
		ret = super(dPemMixin, self).Show(show)
		if show and ret:
			# updates were potentially suppressed while the object
			# wasn't visible, so update now.
			self.update()
		return ret


	def unbindKey(self, keyCombo):
		"""
		Unbind a previously bound key combination.

		Fail silently if the key combination didn't exist already.
		"""
		table = self._acceleratorTable
		try:
			self.Unbind(wx.EVT_MENU, id=table[keyCombo][2])
			del table[keyCombo]
			self.SetAcceleratorTable(wx.AcceleratorTable(table.values()))
		except KeyError:
			pass


	def _getID(self):
		"""Override the default behavior to return the wxPython ID."""
		try:
			ret = self.GetId()
		except (TypeError, AttributeError):
			# Object doesn't support GetID(), which includes trying
			# to get the id of a not-yet-fully-instantiated wxPython
			# object.
			ret = wx.NewId()
		return ret


	def fitToSizer(self, extraWidth=0, extraHeight=0):
		"""Resize the control to fit the size required by its sizer."""
		self.layout()
		self.Fit()
		self.Width += extraWidth
		self.Height += extraHeight
		self.layout()


	def getSizerProp(self, prop):
		"""
		Gets the current setting for the given property from the object's
		ControllingSizer. Returns None if object is not in a sizer.
		"""
		ret = None
		if self.ControllingSizer:
			ret = self.ControllingSizer.getItemProp(self, prop)
		return ret


	def getSizerProps(self):
		"""
		Returns a dict containing the object's sizer property info. The
		keys are the property names, and the values are the current
		values for those props.
		"""
		ret = None
		if self.ControllingSizer:
			ret = self.ControllingSizer.getItemProps(self)
		return ret


	def setSizerProp(self, prop, val):
		"""Tells the object's ControllingSizer to adjust the requested property."""
		if self.ControllingSizer:
			self.ControllingSizer.setItemProp(self, prop, val)


	def setSizerProps(self, propDict):
		"""
		Convenience method for setting multiple sizer item properties at once. The
		dict should have the property name as the key and the desired new value
		as the associated value.
		"""
		if self.ControllingSizer:
			for prop, val in propDict.iteritems():
				self.ControllingSizer.setItemProp(self, prop, val)


	def moveTabOrderBefore(self, obj):
		"""Moves this object's tab order before the passed obj."""
		self.MoveBeforeInTabOrder(obj)


	def moveTabOrderAfter(self, obj):
		"""Moves this object's tab order after the passed obj."""
		self.MoveAfterInTabOrder(obj)


	def processDroppedFiles(self, filelist, x, y):
		"""
		Handler for files dropped on the control. Override in your
		subclass/instance for your needs .
		"""
		pass


	def processDroppedText(self, txt, x, y):
		"""
		Handler for text dropped on the control. Override in your
		subclass/instance for your needs .
		"""
		pass


	def getPropertyInfo(cls, name):
		return super(dPemMixin, cls).getPropertyInfo(name)
	getPropertyInfo = classmethod(getPropertyInfo)


	def lockDisplay(self):
		"""
		Locks the visual updates to the control.

		This can significantly improve performance when many items are being
		updated at once.

		IMPORTANT: you must call unlockDisplay() when you are done, or your
		object will never draw. unlockDisplay() must be called once for every
		time lockDisplay() is called in order to resume repainting of the
		control. Alternatively, you can call lockDisplay() many times, and
		then call unlockDisplayAll() once when you are done.

		Note that lockDisplay currently doesn't do anything on GTK.
		"""
		if self._displayLockCount:
			self._displayLockCount += 1
		else:
			self._displayLockCount = 1
			self.Freeze()


	def unlockDisplay(self):
		"""
		Unlocks the visual updates to the control.

		Use in conjunction with lockDisplay(), when you are doing lots of things
		that would result in lengthy screen updates.

		Since lockDisplay() may be called several times on an object, calling
		unlockDisplay() will "undo" one locking call. When all locks have been
		removed, repainting of the display will resume.
		"""
		self._displayLockCount -= 1
		if not self._displayLockCount:
			try:
				self.Thaw()
			except dabo.ui.assertionException:
				# Too many 'unlockDisplay' calls to the same object were made. Log
				# the mistake, but don't throw a Python error.
				dabo.log.error(_("Extra call to unlockDisplay() for object %s") % self)


	def unlockDisplayAll(self):
		"""
		Immediately unlocks the display, no matter how many previous
		lockDisplay calls have been made. Useful in a callAfterInterval()
		construction to avoid flicker.
		"""
		if not self._displayLockCount:
			return
		self._displayLockCount = 1
		self.unlockDisplay()


	def getDisplayLocker(self):
		"""
		Returns an object that locks the current display when created, and
		unlocks it when destroyed. This is generally safer than calling lockDisplay()
		and unlockDisplay(), especially when used with callAfterInterval(), when
		the unlockDisplay() calls may not all happen.
		"""
		class DisplayLocker(object):
			def __init__(self, obj):
				self._obj = obj
				obj.Freeze()

			def __del__(self):
				if not self._obj:
					return
				try:
					self._obj.Thaw()
				except StandardError, e:
					# Create an error log message. We can't record the obj reference,
					# since it is most likely deleted, but the presence of these messages
					# will ensure that possible problems will not be silenced.
					dabo.log.error(_("Failed to unlock display: %s") % e)
			release = __del__
		return DisplayLocker(self)


	def bringToFront(self):
		"""Makes this object topmost"""
		self.Raise()


	def sendToBack(self):
		"""Places this object behind all others."""
		self.Lower()


	def showContainingPage(self):
		"""
		If this object is inside of any paged control, it will force all containing
		paged controls to switch to the page that contains this object.
		"""
		import dabo.ui.dialogs
		cntnr = self.getContainingPage()
		if isinstance(cntnr, dabo.ui.dialogs.WizardPage):
			self.Form.CurrentPage = cntnr
		else:
			cntnr.Parent.SelectedPage = cntnr


	def getContainingPage(self):
		"""
		Return the dPage or WizardPage that contains self.
		"""
		import dabo.ui.dialogs
		try:
			frm = self.Form
		except AttributeError:
			frm = None
		cntnr = self
		iswiz = isinstance(frm, dabo.ui.dialogs.Wizard)
		mtch = {True: dabo.ui.dialogs.WizardPage, False: dabo.ui.dPage}[iswiz]
		while cntnr and not isinstance(cntnr, dabo.ui.dForm):
			if isinstance(cntnr, mtch):
				return cntnr
			cntnr = cntnr.Parent


	def addObject(self, classRef, Name=None, *args, **kwargs):
		"""
		Instantiate object as a child of self.

		The classRef argument must be a Dabo UI class definition. (it must inherit
		dPemMixin). Alternatively, it can be a saved class definition in XML format,
		as created by the Class Designer.

		The name argument, if passed, will be sent along to the object's
		constructor, which will attempt to set its Name accordingly. If the name
		argument is not passed (or None), the object will get a default Name as
		defined in the object's class definition.

		Additional positional and/or keyword arguments will be sent along to the
		object's constructor.
		"""
		# See if the 'classRef' is either some XML or the path of an XML file
		if isinstance(classRef, basestring):
			xml = classRef
			from dabo.lib.DesignerClassConverter import DesignerClassConverter
			conv = DesignerClassConverter()
			classRef = conv.classFromText(xml)
		# Note that we could have just given addObject() a signature of:
		#   addObject(self, classRef, *args, **kwargs)
		# Which would simplify the implementation somewhat. However, we want
		# to enforce name as the second argument to avoid breaking old code.
		if Name is None:
			obj = classRef(self, *args, **kwargs)
		else:
			obj = classRef(self, Name=Name, *args, **kwargs)
		return obj


	def raiseEvent(self, eventClass, nativeEvent=None, *args, **kwargs):
		"""Raise the passed Dabo event."""
		# Call the Dabo-native raiseEvent(), passing along the wx.CallAfter
		# function, so that the Dabo events can be processed at next idle.

		if not self:
			# Continuing isn't possible, as the wxPython object is already gone.
			# Perhaps we should log this too?
			return

		# Call immediately in this callstack so the object isn't completely
		# gone by the time the callback is called.
		super(dPemMixin, self).raiseEvent(eventClass, nativeEvent, *args, **kwargs)


	def formCoordinates(self, pos=None):
		"""
		Given a position relative to this control, return a position relative
		to the containing form. If no position is passed, returns the position
		of this control relative to the form.
		"""
		if isinstance(self, dabo.ui.dFormMixin):
			frm = self.Parent
		else:
			frm = self.Form
		if frm is None:
			return None
		return self.containerCoordinates(frm, pos)


	def containerCoordinates(self, cnt, pos=None):
		"""
		Given a position relative to this control, return a position relative
		to the specified container. If no position is passed, returns the position
		of this control relative to the container.
		"""
		selfX, selfY = self.absoluteCoordinates()
		if self.Application.Platform == "Win" and isinstance(cnt, dabo.ui.dFormMixin):
			# On Windows, absoluteCoordinates() returns the position of the
			# interior of the form, ignoring the menus, borders, etc. On Mac, it
			# properly returns position of the entire window frame
			# NOTE: Need to check this on Gtk
			cntX, cntY = cnt.Position
		else:
			cntX, cntY = cnt.absoluteCoordinates()
		return (selfX-cntX, selfY-cntY)


	def objectCoordinates(self, pos=None):
		"""
		Given a position relative to the form, return a position relative
		to this object. If no position is passed, returns the position
		of this control relative to the form.
		"""
		if pos is None:
			pos = self.absoluteCoordinates()
		if isinstance(self, dabo.ui.dFormMixin):
			return pos
		x, y = pos
		formX, formY = self.Form.absoluteCoordinates()
		return (x-formX, y-formY)


	def absoluteCoordinates(self, pos=None):
		"""Translates a position value for a control to absolute screen position."""
		if pos is None:
			if isinstance(self, dabo.ui.dFormMixin):
				pos = (0, 0)
			else:
				pos = self.Position
		if self.Parent:
			src = self.Parent
		else:
			src = self
		return src.ClientToScreen(pos)


	def relativeCoordinates(self, pos=None):
		"""Translates an absolute screen position to position value for a control."""
		if pos is None:
			pos = self.Position
		return self.ScreenToClient(pos)


	def isContainedBy(self, obj):
		"""
		Returns True if the containership hierarchy for this control
		includes the passed object reference.
		"""
		ret = False
		p = self.Parent
		while p is not None:
			if p is obj:
				ret = True
				break
			else:
				p = p.Parent
		return ret


	def showContextMenu(self, menu, pos=None, release=True):
		"""
		Display a context menu (popup) at the specified position.

		If no position is specified, the menu will be displayed at the current
		mouse position.

		If release is True (the default), the menu will be released after the user
		has dismissed it.
		"""
		if pos is None:
			pos = self.ScreenToClient(wx.GetMousePosition())
		self.PopupMenu(menu, pos)

		if release:
			menu.release()


	def _getSizerInfo(self, prop):
		"""
		Returns True or False based on whether the property passed is contained
		in the sizer item's flags.
		"""
		prop = prop.lower().strip()
		flag = self.ControllingSizerItem.GetFlag()
		propDict = {"left" : wx.ALIGN_LEFT,
			"right" : wx.ALIGN_RIGHT,
			"center" : wx.ALIGN_CENTER,
			"centre" : wx.ALIGN_CENTER,
			"top" : wx.ALIGN_TOP,
			"bottom" : wx.ALIGN_BOTTOM,
			"middle" : wx.ALIGN_CENTER_VERTICAL,
			"borderbottom" : wx.BOTTOM,
			"borderleft" : wx.LEFT,
			"borderright" : wx.RIGHT,
			"bordertop" : wx.TOP,
			"borderall" : wx.ALL,
			"expand" : wx.EXPAND,
			"grow" : wx.EXPAND,
			"fixed" : wx.FIXED_MINSIZE }
		ret = None
		if prop in propDict:
			val = propDict[prop]
			if flag & val:
				ret = True
			else:
				ret = False
		return ret


	def getPositionInSizer(self):
		"""Convenience method to let you call this directly on the object."""
		return dabo.ui.getPositionInSizer(self)


	def setPositionInSizer(self, pos):
		"""Convenience method to let you call this directly on the object."""
		return dabo.ui.setPositionInSizer(self, pos)


	def setAll(self, prop, val, recurse=True, filt=None, instancesOf=None):
		"""
		Set all child object properties to the passed value.

		No bad effects will happen if the property doesn't apply to a child - only
		children with the property will have their property updated.

		If 'recurse' is True, setAll() will be called on each child as well.

		If 'filt' is not empty, only children that match the expression in 'filt'
		will be affected. The expression will be evaluated assuming the child
		object is prefixed to the expression. For example, if you want to only
		affect objects that are instances of dButton, you'd call::

			form.setAll("FontBold", True, filt="BaseClass == dabo.ui.dButton")

		If the instancesOf sequence is passed, the property will only be set if
		the child object is an instance of one of the passed classes.
		"""
		if isinstance(self, dabo.ui.dGrid):
			kids = self.Columns
		elif isinstance(self, (dabo.ui.dPageFrameMixin, dabo.ui.dPageFrameNoTabs)):
			kids = self.Pages
		else:
			kids = self.Children
		if not kids:
			return
		if isinstance(filt, basestring):
			filt = (filt, )

		if isinstance(instancesOf, basestring):
			instancesOf = (instancesOf,)
		if instancesOf is None:
			instancesOf = tuple()

		def setProp(obj, prop, val):
			try:
				setattr(obj, prop, val)
			except AttributeError:
				# okay, just skip it
				pass

		for kid in kids:
			ok = hasattr(kid, prop) and (not instancesOf or isinstance(kid, instancesOf))
			if ok:
				if filt:
					for ff in filt:
						try:
							ok = eval("kid.%s" % ff)
						except AttributeError:
							ok = False
						if not ok:
							break
			if ok:
				setProp(kid, prop, val)
				if isinstance(kid, dabo.ui.dColumn):
					setProp(kid, "Header%s" % prop, val)
			if recurse:
				if hasattr(kid, "setAll"):
					kid.setAll(prop, val, recurse=recurse, filt=filt, instancesOf=instancesOf)


	def recreate(self, child=None):
		"""
		Recreate the object.

		Warning: this is experimental and is known to cause hair loss.
		"""
		if child is not None:
			propValDict = child.getProperties(ignoreErrors=True,
					propsToSkip=("Parent", "NameBase", "SuperClass"))
			style = child.GetWindowStyle()
			classRef = child.__class__
			name = child.Name
			child.Destroy()
			newObj = self.addObject(classRef, name, style=style)
			newObj.setProperties(propValDict, ignoreErrors=True)
			return newObj
		else:
			return self.Parent.recreate(self)


	def _changeParent(self, newParent):
		"""The native wx method doesn't work on Macs."""
		try:
			return newParent._adopt(self)
		except AttributeError:
			# None parent, perhaps
			self.Reparent(None)


	def _adopt(self, obj):
		"""Moves an object to a new parent container."""
		if self.Application.Platform != "Mac":
			# Reparent() doesn't work on Macs
			obj.Reparent(self)
		else:
			# Re-create the object in the new parent, and then
			# destroy this instance. Note that any previous references
			# to this object will now be invalid.
			obj = self.recreate(obj)
		return obj


	def release(self):
		"""Destroys the object."""
		if self:
			# Make sure something else hasn't already destroyed it.
			self.Destroy()


	def setFocus(self):
		"""Sets focus to the object."""
		## Up until r6816, the following was wrapped in a callAfter(), which made for
		## lousy performance, especially on Windows.
		self.SetFocus()


	def __onUpdate(self, evt):
		"""Update any dynamic properties, and then call the update() hook."""
		if isinstance(self, dabo.ui.deadObject) or not self._constructed():
			return
		# Check paged controls event propagation to inactive pages.
		try:
			isPage = isinstance(self.Parent, dabo.ui.dPageFrameMixin)
		except AttributeError:
			isPage = False
		if isPage:
			try:
				updateInactive = self.Parent.UpdateInactivePages
			except AttributeError:
				updateInactive = None
			if updateInactive == False and self.Parent.SelectedPage != self:
				return
			if not updateInactive and not self.Visible:
				# (some platforms have inactive pages not visible)
				return
		if isinstance(self, dabo.ui.dFormMixin) and not self.Visible:
			return
		self.update()


	def __onResize(self, evt):
		"""Update any dynamic properties."""
		if not self or not self._constructed():
			return
		self.__updateDynamicProps()


	def update(self):
		"""Update the properties of this object and all contained objects."""
		if isinstance(self, dabo.ui.deadObject):
			# This can happen if an object is released when there is a
			# pending callAfter() refresh.
			return
		if isinstance(self, dabo.ui.dForm) and self.AutoUpdateStatusText \
				and self.Visible:
			self.setStatusText(self.getCurrentRecordText(), immediate=True)
		if self.Children:
			self.raiseEvent(dEvents.Update)
		dabo.ui.callAfter(self.__updateDynamicProps)


	def __updateDynamicProps(self):
		"""Updates the object's dynamic properties."""
		if not self:
			return
		self.__updateObjectDynamicProps(self)
		for obj in self._drawnObjects:
			self.__updateObjectDynamicProps(obj)


	def __updateObjectDynamicProps(self, obj):
		for prop, func in obj._dynamic.items():
			if isinstance(func, tuple):
				args = func[1:]
				func = func[0]
			else:
				args = ()
			setattr(obj, prop, func(*args))


	def refresh(self, fromRefresh=False):
		"""Repaints this control and all contained objects."""
		try:
			self.Refresh()
		except dabo.ui.deadObjectException:
			# This can happen if an object is released when there is a
			# pending callAfter() refresh.
			pass
		except AttributeError:
			# Menus don't have a Refresh() method.
			pass


	def show(self):
		"""Make the object visible."""
		self.Visible = True


	def hide(self):
		"""Make the object invisible."""
		self.Visible = False


	def _getWxColour(self, val):
		"""Convert Dabo colors to wx.Colour objects"""
		ret = None
		if isinstance(val, basestring):
			val = dColors.colorTupleFromName(val)
		if isinstance(val, tuple):
			ret = wx.Colour(*val)
		return ret


	def getMousePosition(self):
		"""
		Returns the current mouse position on the entire screen
		relative to this object.
		"""
		return self.ScreenToClient(wx.GetMousePosition()).Get()


	def getCaptureBitmap(self):
		"""Return a bitmap snapshot of self as it appears in the UI at this moment."""
		obj = self.Parent
		if self.Parent is None:
			obj = self
		offset = 0
		htReduction = 0
		cltTop = self.absoluteCoordinates(self.GetClientAreaOrigin())[1]
		if isinstance(self, (dabo.ui.dForm, dabo.ui.dDialog, dabo.ui.dPanel)):
			dc = wx.WindowDC(self)
			if self.Application.Platform == "Mac":
				# Need to adjust for the title bar
				offset = self.Top - cltTop
		else:
			dc = wx.ClientDC(obj)
		# Make sure that the elements are all current
		obj.iterateCall("_redraw", dc)

		# Suggested as an alternative for OS X
		if wx.Platform == "__WXMAC__":
			return dc.GetAsBitmap()

		rect = self.GetRect()
		bmp = wx.EmptyBitmap(rect.width, rect.height, -1)  ## -1: use same color depth
		memdc = wx.MemoryDC()
		memdc.SelectObject(bmp)

		memdc.Blit(0, 0, rect.width, rect.height, dc, 0, offset)
		memdc.SelectObject(wx.NullBitmap)
		memdc.Destroy()
		return bmp


	def drawCircle(self, xPos, yPos, rad, penColor="black", penWidth=1,
			fillColor=None, lineStyle=None, hatchStyle=None, mode=None,
			persist=True, visible=True, dc=None, useDefaults=False):
		"""
		Draws a circle of the specified radius around the specified point.

		You can set the color and thickness of the line, as well as the
		color and hatching style of the fill. Normally, when persist=True,
		the circle will be re-drawn on paint events, but if you pass False,
		it will be drawn once only.

		A drawing object is returned, or None if persist=False. You can
		'remove' the drawing by setting the Visible property of the
		returned object to False. You can also manipulate the position, size,
		color, and fill by changing the various properties of the object.
		"""
		obj = DrawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, Radius=rad, LineStyle=lineStyle,
				HatchStyle=hatchStyle, Shape="circle", Xpos=xPos, Ypos=yPos,
				DrawMode=mode, Visible=visible, dc=dc, useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawArc(self, xPos, yPos, rad, startAngle, endAngle, penColor="black",
			penWidth=1, fillColor=None, lineStyle=None, hatchStyle=None,
			mode=None, persist=True, visible=True, dc=None, useDefaults=False):
		"""
		Draws an arc (pie slice) of a circle centered around the specified point,
		starting from 'startAngle' degrees, and sweeping counter-clockwise
		until 'endAngle' is reached.

		See the 'drawCircle()' method above for more details.
		"""
		obj = DrawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, Radius=rad, StartAngle=startAngle,
				EndAngle=endAngle, LineStyle=lineStyle, HatchStyle=hatchStyle,
				Shape="arc", Xpos=xPos, Ypos=yPos, DrawMode=mode,
				Visible=visible, dc=dc, useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawEllipse(self, xPos, yPos, width, height, penColor="black",
			penWidth=1, fillColor=None, lineStyle=None, hatchStyle=None,
			mode=None, persist=True, visible=True, dc=None, useDefaults=False):
		"""
		Draws an ellipse contained within the rectangular space defined by
		the position and size coordinates

		See the 'drawCircle()' method above for more details.
		"""
		obj = DrawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, LineStyle=lineStyle, HatchStyle=hatchStyle,
				Shape="ellipse", Xpos=xPos, Ypos=yPos, Width=width, Height=height,
				DrawMode=mode, Visible=visible, dc=dc, useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawEllipticArc(self, xPos, yPos, width, height, startAngle, endAngle,
			penColor="black", penWidth=1, fillColor=None, lineStyle=None,
			hatchStyle=None, mode=None, persist=True, visible=True,
			dc=None, useDefaults=False):
		"""
		Draws an arc (pie slice) of a ellipse contained by the specified
		dimensions, starting from 'startAngle' degrees, and sweeping
		counter-clockwise until 'endAngle' is reached.

		See the 'drawCircle()' method above for more details.
		"""
		obj = DrawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, StartAngle=startAngle,
				EndAngle=endAngle, LineStyle=lineStyle, HatchStyle=hatchStyle,
				Shape="ellipticarc", Xpos=xPos, Ypos=yPos, Width=width,
				Height=height, DrawMode=mode, Visible=visible, dc=dc,
				useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawRectangle(self, xPos, yPos, width, height, penColor="black",
			penWidth=1, fillColor=None, lineStyle=None, hatchStyle=None,
			mode=None, persist=True, visible=True, dc=None, useDefaults=False):
		"""
		Draws a rectangle of the specified size beginning at the specified
		point.

		See the 'drawCircle()' method above for more details.
		"""
		obj = DrawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, LineStyle=lineStyle, HatchStyle=hatchStyle,
				Shape="rect", Xpos=xPos, Ypos=yPos, Width=width, Height=height,
				DrawMode=mode, Visible=visible, dc=dc, useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawRoundedRectangle(self, xPos, yPos, width, height, radius, penColor="black",
			penWidth=1, fillColor=None, lineStyle=None, hatchStyle=None,
			mode=None, persist=True, visible=True, dc=None, useDefaults=False):
		"""
		Draws a rounded rectangle of the specified size beginning at the specified
		point, with the specified corner radius.

		See the 'drawCircle()' method above for more details.
		"""
		obj = DrawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, LineStyle=lineStyle, HatchStyle=hatchStyle,
				Shape="roundrect", Xpos=xPos, Ypos=yPos, Width=width, Height=height,
				Radius=radius, DrawMode=mode, Visible=visible, dc=dc, useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawPolygon(self, points, penColor="black", penWidth=1,
			fillColor=None, lineStyle=None, hatchStyle=None, mode=None,
			persist=True, visible=True, dc=None, useDefaults=False):
		"""
		Draws a polygon defined by the specified points.

		The 'points' parameter should be a tuple of (x,y) pairs defining the
		polygon.

		See the 'drawCircle()' method above for more details.
		"""
		obj = DrawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, LineStyle=lineStyle, HatchStyle=hatchStyle,
				Shape="polygon", Points=points, DrawMode=mode,
				Visible=visible, dc=dc, useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawPolyLines(self, points, penColor="black", penWidth=1,
			lineStyle=None, mode=None, persist=True, visible=True,
			dc=None, useDefaults=False):
		"""
		Draws a series of connected line segments defined by the specified points.

		The 'points' parameter should be a tuple of (x,y) pairs defining the shape. Lines
		are drawn connecting the points sequentially, but a segment from the last
		point to the first is not drawn, leaving an 'open' polygon. As a result, there is no
		FillColor or HatchStyle defined for this.

		See the 'drawCircle()' method above for more details.
		"""
		obj = DrawObject(self, PenColor=penColor, PenWidth=penWidth,
				LineStyle=lineStyle, Shape="polylines", Points=points,
				DrawMode=mode, Visible=visible, dc=dc, useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawLine(self, x1, y1, x2, y2, penColor="black", penWidth=1,
			fillColor=None, lineStyle=None, mode=None, persist=True,
			visible=True, dc=None, useDefaults=False):
		"""
		Draws a line between (x1,y1) and (x2, y2).

		See the 'drawCircle()' method above for more details.
		"""
		obj = DrawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, LineStyle=lineStyle, DrawMode=mode,
				Shape="line", Points=((x1,y1), (x2,y2)), Visible=visible, dc=dc,
				useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawBitmap(self, bmp, x=0, y=0, mode=None, persist=True,
			transparent=True, visible=True, dc=None, useDefaults=False):
		"""Draws a bitmap on the object at the specified position."""
		if isinstance(bmp, basestring):
			bmp = dabo.ui.strToBmp(bmp)
		obj = DrawObject(self, Bitmap=bmp, Shape="bmp",
				Xpos=x, Ypos=y, Transparent=transparent, DrawMode=mode,
				Visible=visible, dc=dc, useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawText(self, text, x=0, y=0, angle=0, fontFace=None,
			fontSize=None, fontBold=None, fontItalic=None,
			fontUnderline=None, foreColor=None, backColor=None,
			mode=None, persist=True, visible=True, dc=None, useDefaults=False):
		"""
		Draws text on the object at the specified position
		using the specified characteristics. Any characteristics
		not specified will be set to the system default.
		"""
		obj = DrawObject(self, Shape="text", Text=text, Xpos=x, Ypos=y,
				Angle=angle, FontFace=fontFace, FontSize=fontSize,
				FontBold=fontBold, FontItalic=fontItalic,
				FontUnderline=fontUnderline, ForeColor=foreColor,
				BackColor=backColor, DrawMode=mode, Visible=visible,
				dc=dc, useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawGradient(self, orientation, x=0, y=0, width=None, height=None,
			color1=None, color2=None, mode=None, persist=True, visible=True,
			dc=None, useDefaults=False):
		"""
		Draws a horizontal or vertical gradient on the control. Default
		is to cover the entire control, although you can specify positions.
		The gradient is drawn with 'color1' as the top/left color, and 'color2'
		as the bottom/right color.
		"""
		obj = DrawObject(self, Shape="gradient", Orientation=orientation,
				Xpos=x, Ypos=y, Width=width, Height=height,
				GradientColor1=color1, GradientColor2=color2, DrawMode=mode,
				Visible=visible, dc=dc, useDefaults=useDefaults)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def clear(self):
		"""Clears the background of custom-drawn objects."""
		self.ClearBackground()


	def _addToDrawnObjects(self, obj, persist):
		self._drawnObjects.append(obj)
		self._redraw()
		if not persist:
			self._drawnObjects.remove(obj)
			obj = None
		return obj


	def removeDrawnObject(self, obj):
		self._drawnObjects.remove(obj)


	def _redraw(self, dc=None):
		"""
		If the object has drawing routines that affect its appearance, this
		method is where they go. Subclasses should place code in the
		redraw() hook method.
		"""
		if self._inRedraw:
			return
		self._inRedraw = True
		# Clear the idle flag.
		self._needRedraw = False
		if dc is None:
			# First, clear any old drawing if requested
			if self.autoClearDrawings:
				self.ClearBackground()

		# Draw any shapes
		for obj in self._drawnObjects:
			obj.draw(dc)
		# Call the hook
		self.redraw(dc)
		# Make sure this is really cleared.
		self._needRedraw = False
		# Clear the process flag
		self._inRedraw = False


	def redraw(self, dc):
		"""
		Called when the object is (re)drawn.

		This is a user subclass hook, where you should put any drawing routines
		to affect the object appearance.
		"""
		pass


	def _bringDrawObjectToFront(self, obj):
		"""Put the drawing object on top of other drawing objects."""
		self._drawnObjects.remove(obj)
		self._drawnObjects.append(obj)
		self._needRedraw = True


	def _sendDrawObjectToBack(self, obj):
		"""Put the drawing object below other drawing objects."""
		self._drawnObjects.remove(obj)
		self._drawnObjects.insert(0, obj)
		self._needRedraw = True


	def _moveDrawObjectUp(self, obj, levels=1):
		"""
		Move the drawing object higher in the stack of drawing objects.

		The optional levels argument specifies how much higher to move the drawing
		object.
		"""
		# Moving a drawing object up means moving it down	in position in the list.
		pos = self._drawnObjects.index(obj)
		newPos = pos + levels
		self._drawnObjects.remove(obj)
		self._drawnObjects.insert(newPos, obj)
		self._needRedraw = True


	def _moveDrawObjectDown(self, obj, levels=1):
		"""
		Move the drawing object lower in the stack of drawing objects.

		The optional levels argument specifies how much lower to move the drawing
		object.
		"""
		# Moving a drawing object down means moving it up	in position in the list.
		pos = self._drawnObjects.index(obj)
		newPos = max(0, pos - levels)
		self._drawnObjects.remove(obj)
		self._drawnObjects.insert(newPos, obj)
		self._needRedraw = True


	def _onResizeBorder(self, evt):
		"""
		Called when the user has defined a border for the control, and	the
		control is resized.
		"""
		brd = self._border
		brd.Width, brd.Height = self.Width, self.Height


	def clone(self, obj, name=None):
		"""
		Create another object just like the passed object. It assumes that the
		calling object will be the container of the newly created object.
		"""
		propValDict = obj.getProperties()
		if name is None:
			name = obj.Name + "1"
		newObj = self.addObject(obj.__class__,
				name, style=obj.GetWindowStyle())
		newObj.setProperties(propValDict)
		return newObj


	def copy(self):
		"""
		Called by uiApp when the user requests a copy operation.

		Return None (the default) and uiApp will try a default copy operation.
		Return anything other than None and uiApp will assume that the copy
		operation has been handled.
		"""
		return None


	def cut(self):
		"""
		Called by uiApp when the user requests a cut operation.

		Return None (the default) and uiApp will try a default cut operation.
		Return anything other than None and uiApp will assume that the cut
		operation has been handled.
		"""
		return None


	def paste(self):
		"""
		Called by uiApp when the user requests a paste operation.

		Return None (the default) and uiApp will try a default paste operation.
		Return anything other than None and uiApp will assume that the paste
		operation has been handled.
		"""
		return None


	def _jiggleFontSize(self):
		"""Force refresh the control by tweaking the font size."""
		self.Freeze()
		self.FontSize += 1
		self.FontSize -= 1
		self.Thaw()


	def _onFontPropsChanged(self, evt):
		# Sent by the dFont object when any props changed. Wx needs to be notified:
		if self.Application.Platform == "Mac":
			# Mac bug: need to clear the font from the control first
			# (Thanks Peter Damoc):
			self.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL))
		self.SetFont(self.Font._nativeFont)
		# Re-raise it so that the object can respond to the event.
		self.raiseEvent(dEvents.FontPropertiesChanged)


	def _uniqueNameForParent(self, name, parent=None):
		"""
		Takes a given name and ensures that it is unique among the existing child
		objects of the specified parent container. If no parent is specified, self.Parent
		is assumed. Returns either the original name, if it is unique, or the name with
		a numeric suffix that will make it unique.
		"""
		if parent is None:
			parent = self.Parent
		i = 0
		nameError = True
		candidate = name
		while nameError:
			if i:
				candidate = "%s%s" % (name, i)
			nameError = hasattr(parent, candidate) \
					and type(getattr(parent, candidate)) != wx._core._wxPyDeadObject \
					and getattr(parent, candidate) != self \
					and [win for win in parent.GetChildren()
						if win != self and win.GetName() == candidate]
			i += 1
		return candidate


	# The following 3 flag functions are used in some of the property
	# get/set functions.
	def _getWindowStyleMechanics(self, advanced):
		"""Returns tuple of window style parameter and style manipulation
		method references for ordinary or AGW windows.
		"""
		if advanced:
			return ("agwStyle", self.GetAGWWindowStyleFlag, self.SetAGWWindowStyleFlag)
		else:
			return ("style", self.GetWindowStyleFlag, self.SetWindowStyleFlag)

	def _hasWindowStyleFlag(self, flag, advanced=False):
		"""Return whether or not the flag is set. (bool)"""
		mechanics = self._getWindowStyleMechanics(advanced)
		if self._constructed():
			return (mechanics[1]() & flag) == flag
		else:
			return (self._preInitProperties[mechanics[0]] & flag) == flag

	def _addWindowStyleFlag(self, flag, advanced=False):
		"""Add the flag to the window style."""
		mechanics = self._getWindowStyleMechanics(advanced)
		if self._constructed():
			mechanics[2](mechanics[1]() | flag)
		else:
			self._preInitProperties[mechanics[0]] = self._preInitProperties[mechanics[0]] | flag

	def _delWindowStyleFlag(self, flag, advanced=False):
		"""Remove the flag from the window style."""
		mechanics = self._getWindowStyleMechanics(advanced)
		if self._constructed():
			mechanics[2](mechanics[1]() & (~flag))
		else:
			self._preInitProperties[mechanics[0]] = self._preInitProperties[mechanics[0]] & (~flag)


	def _getBackColor(self):
		return self.GetBackgroundColour().Get()

	def _setBackColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				val = dColors.colorTupleFromName(val)
			if val is None:
				self.SetBackgroundColour(wx.NullColour)
			elif val != self.GetBackgroundColour().Get():
				self.SetBackgroundColour(val)
				# Background color changes don't result in an automatic refresh.
				self.refresh()
		else:
			self._properties["BackColor"] = val


	def _getBorderColor(self):
		return self._borderColor

	def _setBorderColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				val = dColors.colorTupleFromName(val)
			self._borderColor = val
			if self._border:
				self._border.PenColor = val
			self._needRedraw = True
		else:
			self._properties["BorderColor"] = val


	def _getBorderLineStyle(self):
		return self._borderLineStyle

	def _setBorderLineStyle(self, val):
		val = self._expandPropStringValue(val, ("Solid", "Dash", "Dashed", "Dot",
				"Dotted", "DotDash", "DashDot"))
		self._borderLineStyle = val
		if self._border:
			self._border.LineStyle = val
		self._needRedraw = True


	def _getBorderWidth(self):
		return self._borderWidth

	def _setBorderWidth(self, val):
		if self._constructed():
			self._borderWidth = val
			if self._border and (self._border in self._drawnObjects):
				if val == 0:
					self._drawnObjects.remove(self._border)
				else:
					self._border.PenWidth = val
			else:
				if val > 0:
					self._border = self.drawRectangle(0, 0, self.Width,
							self.Height, penColor=self.BorderColor, penWidth=val)
			if self._border:
				# Tie it to resizing
				self.bindEvent(dEvents.Resize, self._onResizeBorder)
			else:
				self.unbindEvent(dEvents.Resize, self._onResizeBorder)
		else:
			self._properties["BorderWidth"] = val


	def _getBorderStyle(self):
		if self._hasWindowStyleFlag(wx.RAISED_BORDER):
			return "Raised"
		elif self._hasWindowStyleFlag(wx.SUNKEN_BORDER):
			return "Sunken"
		elif self._hasWindowStyleFlag(wx.SIMPLE_BORDER):
			return "Simple"
		elif self._hasWindowStyleFlag(wx.DOUBLE_BORDER):
			return "Double"
		elif self._hasWindowStyleFlag(wx.STATIC_BORDER):
			return "Static"
		elif self._hasWindowStyleFlag(wx.NO_BORDER):
			return "None"
		else:
			return "Default"


	def _setBorderStyle(self, val):
		if val is None:
			# XML stores the string and null 'None' identically
			val = "None"
		style = self._expandPropStringValue(val, ("None", "Simple", "Sunken",
				"Raised", "Double", "Static", "Default"))
		self._delWindowStyleFlag(wx.NO_BORDER)
		self._delWindowStyleFlag(wx.SIMPLE_BORDER)
		self._delWindowStyleFlag(wx.SUNKEN_BORDER)
		self._delWindowStyleFlag(wx.RAISED_BORDER)
		self._delWindowStyleFlag(wx.DOUBLE_BORDER)
		self._delWindowStyleFlag(wx.STATIC_BORDER)

		if style == "None":
			self._addWindowStyleFlag(wx.NO_BORDER)
		elif style == "Simple":
			self._addWindowStyleFlag(wx.SIMPLE_BORDER)
		elif style == "Sunken":
			self._addWindowStyleFlag(wx.SUNKEN_BORDER)
		elif style == "Raised":
			self._addWindowStyleFlag(wx.RAISED_BORDER)
		elif style == "Double":
			self._addWindowStyleFlag(wx.DOUBLE_BORDER)
		elif style == "Static":
			self._addWindowStyleFlag(wx.STATIC_BORDER)
		elif style == "Default":
			pass


	def _getCaption(self):
		return getattr(self, "_caption", self.GetLabel())

	def _setCaption(self, val):
		# Force the value to string
		val = "%s" % val
		def __captionSet(val):
			"""Windows textboxes change their value when SetLabel() is called; this
			avoids that problem.
			"""
			if not isinstance(self, (dabo.ui.dTextBox, dabo.ui.dEditBox)):
				self._caption = val
				uval = ustr(val)
				## 2/23/2005: there is a bug in wxGTK that resets the font when the
				##            caption changes. So this is a workaround:
				font = self.Font
				self.SetLabel(uval)
				self.Font = font
				self.refresh()

				# Frames have a Title separate from Label, but I can't think
				# of a reason why that would be necessary... can you?
				try:
					self.SetTitle(uval)
				except AttributeError:
					# wxPython 2.7.x started not having this attribute for labels
					# at least.
					pass

				if getattr(self, "_layout_on_set_caption", False):
					try:
						self.Parent.layout()
					except AttributeError:
						# no parent?
						pass

		if self._constructed():
			try:
				if self.WordWrap or self._properties["WordWrap"]:
					# Word wrapping doesn't always work correctly when
					# the Caption is set initially, so set it afterwards as well.
					dabo.ui.callAfter(__captionSet, val)
					return
			except (AttributeError, KeyError):
				pass
			__captionSet(val)
		else:
			self._properties["Caption"] = val


	def _getChildren(self):
		if hasattr(self, "GetChildren"):
			return list(self.GetChildren())
		else:
			return None


	def _getCntrlSizer(self):
		try:
			ret = self._controllingSizer
		except AttributeError:
			ret = self._controllingSizer = None
		return ret


	def _getCntrlSzItem(self):
		try:
			ret = self._controllingSizerItem
		except AttributeError:
			ret = self._controllingSizerItem = None
		return ret


	def _getDroppedFileHandler(self):
		return self._droppedFileHandler

	def _setDroppedFileHandler(self, val):
		if self._constructed():
			self._droppedFileHandler = val
			if self._dropTarget == None:
				self._dropTarget = _DropTarget()
				if isinstance(self, dabo.ui.dGrid):
					wxObj = self.GetGridWindow()
				else:
					wxObj = self
				wxObj.SetDropTarget(self._dropTarget)
			self._dropTarget.FileHandler = val
		else:
			self._properties["DroppedFileHandler"] = val


	def _getDroppedTextHandler(self):
		return self._droppedTextHandler

	def _setDroppedTextHandler(self, val):
		if self._constructed():
			self._droppedTextHandler = val
			# EGL: 2009-09-22 - is this needed? The name 'target' is never used.
			#target = self.GetDropTarget()
			if self._dropTarget == None:
				self._dropTarget = _DropTarget()
				if isinstance(self, dabo.ui.dGrid):
					wxObj = self.GetGridWindow()
				else:
					wxObj = self
				wxObj.SetDropTarget(self._dropTarget)
			self._dropTarget.TextHandler = val
		else:
			self._properties["DroppedTextHandler"] = val


	def _getEnabled(self):
		return self.IsEnabled()

	def _setEnabled(self, val):
		if self._constructed():
			# Handle DataControl disabling on empty data source.
			try:
				inDataUpdate = self._inDataUpdate
			except AttributeError:
				inDataUpdate = False
			if inDataUpdate:
				if self._uiDisabled:
					val = False
			else:
				self._uiDisabled = not val
				try:
					dsDisabled = self._dsDisabled
				except AttributeError:
					dsDisabled = False
				if dsDisabled:
					val = False
			self.Enable(val)
		else:
			self._properties["Enabled"] = False


	def _getEventTarget(self):
		return self._eventTarget


	def _getDaboFont(self):
		if hasattr(self, "_font") and isinstance(self._font, dabo.ui.dFont):
			v = self._font
		else:
			v = self.Font = dabo.ui.dFont(_nativeFont=self.GetFont())
		return v

	def _setDaboFont(self, val):
		#PVG: also accep wxFont parameter
		if isinstance(val, (wx.Font, wx._gdi.Font)):
			val = dabo.ui.dFont(_nativeFont=val)
		if self._constructed():
			self._font = val
			try:
				self.SetFont(val._nativeFont)
			except AttributeError:
				dabo.log.error(_("Error setting font for %s") % self.Name)
			val.bindEvent(dEvents.FontPropertiesChanged, self._onFontPropsChanged)
		else:
			self._properties["Font"] = val


	def _getFontBold(self):
		return self.Font.Bold

	def _setFontBold(self, val):
		if self._constructed():
			self.Font.Bold = bool(val)
		else:
			self._properties["FontBold"] = val


	def _getFontDescription(self):
		return self.Font.Description


	def _getFontInfo(self):
		return self.Font._nativeFont.GetNativeFontInfoDesc()


	def _getFontItalic(self):
		return self.Font.Italic

	def _setFontItalic(self, val):
		if self._constructed():
			self.Font.Italic = bool(val)
		else:
			self._properties["FontItalic"] = val


	def _getFontFace(self):
		return self.Font.Face

	def _setFontFace(self, val):
		if self._constructed():
			self.Font.Face = val
		else:
			self._properties["FontFace"] = val


	def _getFontSize(self):
		return self.Font.Size

	def _setFontSize(self, val):
		if self._constructed():
			self.Font.Size = val
		else:
			self._properties["FontSize"] = val


	def _getFontUnderline(self):
		return self.Font.Underline

	def _setFontUnderline(self, val):
		if self._constructed():
			# underlining doesn't seem to be working...
			self.Font.Underline = bool(val)
		else:
			self._properties["FontUnderline"] = val


	def _getForeColor(self):
		return self.GetForegroundColour().Get()

	def _setForeColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				val = dColors.colorTupleFromName(val)
			if val != self.GetForegroundColour().Get():
				self.SetForegroundColour(val)
				# Need to jiggle the font size to force the color change to take
				# effect, at least for dEditBox on Gtk.
				dabo.ui.callAfterInterval(100, self._jiggleFontSize)
		else:
			self._properties["ForeColor"] = val


	def _getHeight(self):
		return self.GetSize()[1]

	def _setHeight(self, val):
		if self._constructed():
			if getattr(self, "_widthAlreadySet", False):
				width = self.Width
			else:
				width = -1
			newSize = (width, int(val))
			self._setSize(newSize)
			if isinstance(self, dabo.ui.dFormMixin):
				self._defaultHeight = val
		else:
			self._properties["Height"] = val


	def _getHelpContextText(self):
		return self.GetHelpText()

	def _setHelpContextText(self, val):
		if self._constructed():
			self.SetHelpText(val)
		else:
			self._properties["HelpContextText"] = val


	def _getHover(self):
		return self._hover

	def _setHover(self, val):
		self._hover = val


	def _getLeft(self):
		return self.GetPosition()[0]

	def _setLeft(self, val):
		if self._constructed():
			self.SetPosition((int(val), self.Top))
		if isinstance(self, dabo.ui.dFormMixin):
			self._defaultLeft = val
		else:
			self._properties["Left"] = val


	def _getMaximumHeight(self):
		return self._maximumHeight

	def _setMaximumHeight(self, val):
		if self._constructed():
			if val is None:
				val = -1
			self._maximumHeight = val
			self.SetMaxSize((self._maximumWidth, self._maximumHeight))
		else:
			self._properties["MaximumHeight"] = val


	def _getMaximumSize(self):
		return (self._maximumWidth, self._maximumHeight)

	def _setMaximumSize(self, val):
		if self._constructed():
			if val is None:
				self._maximumWidth = self._maximumHeight = -1
			self._maximumWidth, self._maximumHeight = val
			if self._maximumWidth is None:
				self._maximumWidth = -1
			if self._maximumHeight is None:
				self._maximumHeight = -1
			self.SetMaxSize((self._maximumWidth, self._maximumHeight))
		else:
			self._properties["MaximumSize"] = val


	def _getMaximumWidth(self):
		return self._maximumWidth

	def _setMaximumWidth(self, val):
		if self._constructed():
			if val is None:
				val = -1
			self._maximumWidth = val
			self.SetMaxSize((self._maximumWidth, self._maximumHeight))
		else:
			self._properties["MaximumWidth"] = val


	def _getMinimumHeight(self):
		return self._minimumHeight

	def _setMinimumHeight(self, val):
		if self._constructed():
			self._minimumHeight = val
			self.SetMinSize((self._minimumWidth, val))
		else:
			self._properties["MinimumHeight"] = val


	def _getMinimumSize(self):
		return (self._minimumWidth, self._minimumHeight)

	def _setMinimumSize(self, val):
		if self._constructed():
			self._minimumWidth, self._minimumHeight = val
			self.SetMinSize(val)
		else:
			self._properties["MinimumSize"] = val


	def _getMinimumWidth(self):
		return self._minimumWidth

	def _setMinimumWidth(self, val):
		if self._constructed():
			self._minimumWidth = val
			self.SetMinSize((val, self._minimumHeight))
		else:
			self._properties["MinimumWidth"] = val


	def _getMousePointer(self):
		return self.GetCursor()

	def _setMousePointer(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				# Name of a cursor. This can be either the full names, such
				# as 'Cursor_Bullseye', or just 'Bullseye'. It could also be a sizing
				# direction, such as 'NWSE'.
				uic = dabo.ui.dUICursors
				try:
					crsName = eval("uic.%s" % val)
				except AttributeError:
					# Try prepending the appropriate string
					if val.upper() in ("NWSE", "NESW", "NS", "WE"):
						prfx = "Cursor_Size_"
					else:
						prfx = "Cursor_"
					try:
						crsName = eval("uic.%s%s" % (prfx, val))
					except AttributeError:
						# Try munging the case
						valTitle = "_".join([pt.title() for pt in val.split("_")])
						try:
							crsName = eval("uic.%s%s" % (prfx, valTitle))
						except AttributeError:
							dabo.log.error(_("Invalid MousePointer value: '%s'") % val)
							return
				crs = uic.getStockCursor(crsName)
			else:
				crs = val
			self.SetCursor(crs)
		else:
			self._properties["MousePointer"] = val


	def _getName(self):
		try:
			name = self.GetName()
		except (TypeError, AttributeError):
			# Some objects that inherit from dPemMixin (dMenu*) don't have GetName()
			# or SetName() methods. Or, the wxPython object isn't fully
			# instantiated yet.
			name = self._name
		# keep name available even after C++ object is gone:
		self._name = name
		return name

	def _setName(self, name, _userExplicit=True):
		if not self._constructed():
			if _userExplicit:
				self._properties["Name"] = name
			else:
				self._properties["NameBase"] = name
		else:
			currentName = self._getName()
			if dabo.fastNameSet:
				# The user is responsible for setting and unsetting the global fastNameSet
				# flag. It means that they are initializing a bunch of objects and want good
				# performance, and that they are taking responsibility for making sure the
				# names are unique. Just set the name and return, without all the checking.
				self._name = name
				try:
					self.SetName(name)
				except AttributeError:
					# Some objects that inherit from dPemMixin do not implement SetName().
					pass
				try:
					del self.Parent.__dict__[currentName]
				except (AttributeError, KeyError):
					# Parent could be None, or currentName wasn't bound yet (init)
					pass

				# Make sure that the name isn't already used
				if self.Parent:
					if hasattr(self.Parent, name) \
							and type(getattr(self.Parent, name)) != wx._core._wxPyDeadObject \
							and getattr(self.Parent, name) != self:
						raise NameError("Name '%s' is already in use." % name)
				try:
					self.Parent.__dict__[name] = self
				except AttributeError:
					# Parent could be None
					pass
				return

			parent = self.Parent
			if parent is not None:
				if not _userExplicit:
					# Dabo is setting the name implicitly, in which case we want to mangle
					# the name if necessary to make it unique (we don't want a NameError).
					name = self._uniqueNameForParent(name)
				else:
					# the user is explicitly setting the Name. If another object already
					# has the name, we must raise an exception immediately.
					if hasattr(parent, name) \
							and type(getattr(parent, name)) != wx._core._wxPyDeadObject \
							and getattr(parent, name) != self:
						raise NameError("Name '%s' is already in use." % name)
					else:
						for window in parent.GetChildren():
							if window is self:
								continue
							try:
								winname = window.GetName()
							except AttributeError:
								try:
									winname = window._name
								except AttributeError:
									# Not an object with a Name, so ignore
									continue
							if ustr(winname) == ustr(name):
								raise NameError("Name '%s' is already in use." % name)

			else:
				# Can't do the name check for siblings, so allow it for now.
				# This problem would only apply to top-level forms, so it really
				# wouldn't matter anyway in a practical sense.
				pass


			name = ustr(name)
			self._name = name
			try:
				self.SetName(name)
			except AttributeError:
				# Some objects that inherit from dPemMixin do not implement SetName().
				pass

			try:
				del self.Parent.__dict__[currentName]
			except (AttributeError, KeyError):
				# Parent could be None, or currentName wasn't bound yet (init)
				pass

			try:
				self.Parent.__dict__[name] = self
			except AttributeError:
				# Parent could be None
				pass

			## When the name changes, we need to autobind again:
			self.autoBindEvents(force=False)


	def _setNameBase(self, val):
		if self._constructed():
			self._setName(val, False)
		else:
			self._properties["NameBase"] = val


	def _getParent(self):
		try:
			return self.GetParent()
		except TypeError:
			return None

	def _setParent(self, val):
		if self._constructed():
			self._changeParent(val)
			## When the object's parent changes, we need to autobind again:
			self.autoBindEvents(force=False)
		else:
			self._properties["Parent"] = val



	def _getPosition(self):
		return self.GetPosition().Get()

	def _setPosition(self, val):
		if self._constructed():
			left, top = val
			if isinstance(self, dabo.ui.dFormMixin):
				self._defaultLeft, self._defaultTop = (left, top)
			self.SetPosition((left, top))
		else:
			self._properties["Position"] = val


	def _getRegID(self):
		return self._registryID

	def _setRegID(self, val):
		if not self._constructed():
			self._properties["RegID"] = val
			return
		if self._registryID:
			# These should be immutable once set
			raise AttributeError(_("RegIDs cannot be changed once they are set"))
		self._registryID = val
		try:
			self.Form.registerObject(self)
		except KeyError:
			err = _("Attempt in object '%(self)s' to set duplicate RegID: '%(val)s'") % locals()
			dabo.log.error(err)
			raise KeyError(err)

		# When the object's RegID is set, we need to autobind again:
		self.autoBindEvents(force=False)


	def _getSize(self):
		return self.GetSize().Get()

	def _setSize(self, val):
		if self._constructed():
			self._widthAlreadySet = (val[0] >= 0)
			self._heightAlreadySet = (val[1] >= 0)
			if isinstance(self, (wx.Frame, wx.Dialog)):
				self.SetSize(val)
			else:
				if isinstance(self, wx.Panel):
					self.SetMinSize(val)
				if hasattr(self, "SetInitialSize"):
					# wxPython 2.7.x:
					self.SetInitialSize(val)
				else:
					# prior to wxPython 2.7.s:
					self.SetBestFittingSize(val)
			if isinstance(self, dabo.ui.dFormMixin):
				self._defaultWidth, self._defaultHeight = val
		else:
			self._properties["Size"] = val


	def _getSizer(self):
		return self.GetSizer()

	def _setSizer(self, val):
		if self._constructed():
			if val is None:
				# Unset the sizer, but don't destroy it
				self.SetSizer(val, False)
			else:
				self.SetSizer(val, True)
			try:
				val.Parent = self
			except AttributeError:
				pass
		else:
			self._properties["Sizer"] = val


	def _getStatusText(self):
		try:
			v = self._statusText
		except AttributeError:
			v = self._statusText = None
		return v

	def _setStatusText(self, val):
		self._statusText = val


	def _getTag(self):
		try:
			v = self._tag
		except AttributeError:
			v = self._tag = None
		return v

	def _setTag(self, val):
		self._tag = val


	def _getToolTipText(self):
		return getattr(self, "_toolTipText", None)

	def _setToolTipText(self, val):
		if not self._constructed():
			self._properties["ToolTipText"] = val
			return
		if not val and not self.ToolTipText:
			# Don't keep setting blank tooltip repeatedly.
			pass
		else:
			if not val:
				## Note that this currently doesn't work, at least on Gtk2. Robin
				## appears to think it should, though, so let's hope... to be safe,
				## I first set the tooltip to a blank string.
				self.SetToolTip(wx.ToolTip(""))
				self.SetToolTip(None)
			else:
				curr = self.GetToolTip()
				if curr is not None:
					currTip = curr.GetTip()
				else:
					currTip = ""
				if currTip != val:
					newtip = wx.ToolTip(val)
					self.SetToolTip(None)
					self.SetToolTip(newtip)
		self._toolTipText = val


	def _getTop(self):
		return self.GetPosition()[1]

	def _setTop(self, val):
		if self._constructed():
			if isinstance(self, dabo.ui.dFormMixin):
				self._defaultTop = val
			self.SetPosition((self.Left, int(val)))
		else:
			self._properties["Top"] = val


	def _getTransparency(self):
		return self._transparency

	def _setTransparency(self, val):
		if self._constructed():
			val = min(max(val, 0), 255)
			delay = self.TransparencyDelay
			if delay:
				sleeptime = delay / 10.0
				oldVal = self._transparency
				self._transparency = val
				incr = (val - oldVal) / 10
				newVal = oldVal
				for i in xrange(10):
					newVal = int(round(newVal + incr, 0))
					newVal = min(max(newVal, 0), 255)
					self.SetTransparent(newVal)
					self.refresh()
					time.sleep(sleeptime)
				# Make sure that there is no rounding error
				self.SetTransparent(val)
			else:
				self.SetTransparent(val)
		else:
			self._properties["Transparency"] = val


	def _getTransparencyDelay(self):
		return self._transparencyDelay

	def _setTransparencyDelay(self, val):
		if self._constructed():
			self._transparencyDelay = val
		else:
			self._properties["TransparencyDelay"] = val


	def _getVisible(self):
		try:
			return self.IsShown()
		except AttributeError:
			dabo.log.error(_("The object %s does not support the Visible property.") % self)
			return None

	def _setVisible(self, val):
		if self._constructed():
			try:
				self.Show(bool(val))
			except AttributeError:
				dabo.log.error(_("The object %s does not support the Visible property.") % self)
			try:
				dabo.ui.callAfterInterval(100, self.Parent.layout)
			except AttributeError:
				pass
		else:
			self._properties["Visible"] = val


	def _getVisibleOnScreen(self):
		return self.IsShownOnScreen()


	def _getWidth(self):
		return self.GetSize()[0]

	def _setWidth(self, val):
		if self._constructed():
			if getattr(self, "_heightAlreadySet", False):
				height = self.Height
			else:
				height = -1
			newSize = (int(val), height)
			self._setSize(newSize)
			if isinstance(self, dabo.ui.dFormMixin):
				self._defaultWidth = val
		else:
			self._properties["Width"] = val


	def _getWindowHandle(self):
		return self.GetHandle()


	# Property definitions follow
	BackColor = property(_getBackColor, _setBackColor, None,
			_("Specifies the background color of the object. (str, 3-tuple, or wx.Colour)"))

	BorderColor = property(_getBorderColor, _setBorderColor, None,
			_("""Specifies the color of the border drawn around the control, if any.

			Default='black'  (str, 3-tuple, or wx.Colour)"""))

	BorderLineStyle = property(_getBorderLineStyle, _setBorderLineStyle, None,
			_("""Style of line for the border drawn around the control.

			Possible choices are:
				"Solid"  (default)
				"Dash"
				"Dot"
				"DotDash"
				"DashDot"
			"""))

	BorderStyle = property(_getBorderStyle, _setBorderStyle, None,
			_("""Specifies the type of border for this window. (str).

				Possible choices are:
					"None"
					"Simple"
					"Sunken"
					"Raised"
			"""))

	BorderWidth = property(_getBorderWidth, _setBorderWidth, None,
			_("""Width of the border drawn around the control, if any. (int)

				Default=0 (no border)
			"""))

	Caption = property(_getCaption, _setCaption, None,
			_("The caption of the object. (str)"))

	Children = property(_getChildren, None, None,
			_("""Returns a list of object references to the children of
			this object. Only applies to containers. Children will be None for
			non-containers.  (list or None)
			"""))

	ControllingSizer = property(_getCntrlSizer, None, None,
			_("""Reference to the sizer that controls this control's layout.  (dSizer)"""))

	ControllingSizerItem = property(_getCntrlSzItem, None, None,
			_("""Reference to the sizer item that control's this control's layout.

				This is useful for getting information about how the item is being
				sized, and for changing those settings.  (SizerItem)
			"""))

	DroppedFileHandler = property(_getDroppedFileHandler, _setDroppedFileHandler, None,
			_("""Reference to the object that will handle files dropped on this control.
			When files are dropped, a list of them will be passed to this object's
			'processDroppedFiles()' method. Default=None  (object or None)
			"""))

	DroppedTextHandler = property(_getDroppedTextHandler, _setDroppedTextHandler, None,
			_("""Reference to the object that will handle text dropped on this control.
			When text is dropped, that text will be passed to this object's
			'processDroppedText()' method. Default=None  (object or None)
			"""))

	Enabled = property(_getEnabled, _setEnabled, None,
			_("""Specifies whether the object and children can get user input. (bool)"""))

	_EventTarget = property(_getEventTarget, None, None,
			_("""The object that receives events. In all but a few particular cases, it will be
			the object itself. This must be passed to the constructor so that it can be set
			before event binding occurs; it cannot be changed after the object is created.
			DO NOT USE UNLESS YOU KNOW WHAT YOU ARE DOING and can handle the
			resulting behavior changes. Usually used to pass events to the container in a
			composite control. Default=self  (object)
			"""))

	Font = property(_getDaboFont, _setDaboFont, None,
			_("Specifies font object for this control. (dFont)"))

	FontBold = property(_getFontBold, _setFontBold, None,
			_("Specifies if the font is bold-faced. (bool)"))

	FontDescription = property(_getFontDescription, None, None,
			_("Human-readable description of the current font settings. (str)"))

	FontFace = property(_getFontFace, _setFontFace, None,
			_("Specifies the font face. (str)"))

	FontInfo = property(_getFontInfo, None, None,
			_("Specifies the platform-native font info string. Read-only. (str)"))

	FontItalic = property(_getFontItalic, _setFontItalic, None,
			_("Specifies whether font is italicized. (bool)"))

	FontSize = property(_getFontSize, _setFontSize, None,
			_("Specifies the point size of the font. (int)"))

	FontUnderline = property(_getFontUnderline, _setFontUnderline, None,
			_("Specifies whether text is underlined. (bool)"))

	ForeColor = property(_getForeColor, _setForeColor, None,
			_("Specifies the foreground color of the object. (str, 3-tuple, or wx.Colour)"))

	Height = property(_getHeight, _setHeight, None,
			_("Specifies the height of the object. (int)"))

	HelpContextText = property(_getHelpContextText, _setHelpContextText, None,
			_("""Specifies the context-sensitive help text associated with this
				window. (str)
			"""))

	Hover = property(_getHover, _setHover, None,
			_("""When True, Mouse Enter events fire the onHover method, and
			MouseLeave events fire the endHover method  (bool)
			"""))

	Left = property(_getLeft, _setLeft, None,
			_("Specifies the left position of the object. (int)"))

	MaximumHeight = property(_getMaximumHeight, _setMaximumHeight, None,
			_("Maximum allowable height for the control in pixels.  (int)"))

	MaximumSize = property(_getMaximumSize, _setMaximumSize, None,
			_("Maximum allowable size for the control in pixels.  (2-tuple of int)"))

	MaximumWidth = property(_getMaximumWidth, _setMaximumWidth, None,
			_("Maximum allowable width for the control in pixels.  (int)"))

	MinimumHeight = property(_getMinimumHeight, _setMinimumHeight, None,
			_("Minimum allowable height for the control in pixels.  (int)"))

	MinimumSize = property(_getMinimumSize, _setMinimumSize, None,
			_("Minimum allowable size for the control in pixels.  (2-tuple of int)"))

	MinimumWidth = property(_getMinimumWidth, _setMinimumWidth, None,
			_("Minimum allowable width for the control in pixels.  (int)"))

	MousePointer = property(_getMousePointer, _setMousePointer, None,
			_("Specifies the shape of the mouse pointer when it enters this window. (obj)"))

	Name = property(_getName, _setName, None,
			_("""Specifies the name of the object, which must be unique among siblings.

			If the specified name isn't unique, an exception will be raised. See also
			NameBase, which let's you set a base name and Dabo will automatically append
			integers to make it unique.
			"""))

	NameBase = property(None, _setNameBase, None,
			_("""Specifies the base name of the object.

			The base name specified will become the object's Name, unless another sibling
			already has that name, in which case Dabo will find the next unique name by
			adding integers to the end of the base name. For example, if your code says:

				self.NameBase = "txtAddress"

			and there is already a sibling object with that name, your object will end up
			with Name = "txtAddress1".

			This property is write-only at runtime.
			"""))

	Parent = property(_getParent, _setParent, None,
			_("The containing object. (obj)"))

	Position = property(_getPosition, _setPosition, None,
			_("The (x,y) position of the object. (tuple)"))

	RegID = property(_getRegID, _setRegID, None,
			_("A unique identifier used for referencing by other objects. (str)"))

	Size = property(_getSize, _setSize, None,
			_("The size of the object. (tuple)"))

	Sizer = property(_getSizer, _setSizer, None,
			_("The sizer for the object."))

	StatusText = property(_getStatusText, _setStatusText, None,
			_("""Specifies the text that displays in the form's status bar, if any.

			The text will appear when the control gets the focus, or when the
			mouse hovers over the control, and will clear when the control loses
			the focus, or when the mouse is no longer hovering.

			For forms, set StatusText whenever you want to display a message.
			"""))

	Tag = property(_getTag, _setTag, None,
			_("A property that user code can safely use for specific purposes."))

	ToolTipText = property(_getToolTipText, _setToolTipText, None,
			_("Specifies the tooltip text associated with this window. (str)"))

	Top = property(_getTop, _setTop, None,
			_("The top position of the object. (int)"))

	Transparency = property(_getTransparency, _setTransparency, None,
			_("""Transparency level of the control; ranges from 0 (transparent) to 255 (opaque).
			Default=0. Does not currently work on Gtk/Linux.  (int)
			"""))

	TransparencyDelay = property(_getTransparencyDelay, _setTransparencyDelay, None,
			_("""Time in seconds to change transparency. Set it to zero to see instant changes.
			Default=0.25 (float)
			"""))

	Visible = property(_getVisible, _setVisible, None,
			_("Specifies whether the object is visible at runtime.  (bool)"))

	VisibleOnScreen = property(_getVisibleOnScreen, None, None,
			_("""Specifies whether the object is physically visible at runtime.  (bool)

			The Visible property could return True even if the object isn't actually
			shown on screen, due to a parent object or sizer being invisible.

			The VisibleOnScreen property will return True only if the object and all
			parents are visible.
			"""))

	Width = property(_getWidth, _setWidth, None,
			_("The width of the object. (int)"))

	WindowHandle = property(_getWindowHandle, None, None,
			_("The platform-specific handle for the window. Read-only. (long)"))


	# Dynamic property declarations
	DynamicBackColor = makeDynamicProperty(BackColor)
	DynamicBorderColor = makeDynamicProperty(BorderColor)
	DynamicBorderLineStyle = makeDynamicProperty(BorderLineStyle)
	DynamicBorderStyle = makeDynamicProperty(BorderStyle)
	DynamicBorderWidth = makeDynamicProperty(BorderWidth)
	DynamicCaption = makeDynamicProperty(Caption)
	DynamicEnabled = makeDynamicProperty(Enabled)
	DynamicFont = makeDynamicProperty(Font)
	DynamicFontBold = makeDynamicProperty(FontBold)
	DynamicFontFace = makeDynamicProperty(FontFace)
	DynamicFontItalic = makeDynamicProperty(FontItalic)
	DynamicFontSize = makeDynamicProperty(FontSize)
	DynamicFontUnderline = makeDynamicProperty(FontUnderline)
	DynamicForeColor = makeDynamicProperty(ForeColor)
	DynamicHeight = makeDynamicProperty(Height)
	DynamicLeft = makeDynamicProperty(Left)
	DynamicMousePointer = makeDynamicProperty(MousePointer)
	DynamicPosition = makeDynamicProperty(Position)
	DynamicSize = makeDynamicProperty(Size)
	DynamicStatusText = makeDynamicProperty(StatusText)
	DynamicTag = makeDynamicProperty(Tag)
	DynamicToolTipText = makeDynamicProperty(ToolTipText)
	DynamicTop = makeDynamicProperty(Top)
	DynamicTransparency = makeDynamicProperty(Transparency)
	DynamicVisible = makeDynamicProperty(Visible)
	DynamicWidth = makeDynamicProperty(Width)



class DrawObject(dObject):
	"""
	Class to handle drawing on an object.

	It is not meant to be used directly; instead, it is returned after a drawing
	instruction is called on the object.
	"""
	def __init__(self, parent, dc=None, useDefaults=False, *args, **kwargs):
		self._inInit = True
		self._dc = dc
		self._useDefaults = useDefaults
		self._dynamic = {}
		# Initialize property atts
		self._parent = parent
		self._bitmap = None
		self._fillColor = None
		self._height = None
		self._lineStyle = None
		self._hatchStyle = None
		self._penColor = None
		self._penWidth = None
		self._points = None
		self._radius = None
		self._startAngle = None
		self._endAngle = None
		self._shape = None
		self._visible = True
		self._width = 0
		self._xPos = None
		self._yPos = None
		self._fontFace = None
		self._fontSize = None
		self._fontBold = None
		self._fontItalic = None
		self._fontUnderline = None
		self._foreColor = None
		self._backColor = None
		self._text = None
		self._angle = 0
		self._gradientColor1 = None
		self._gradientColor2 = None
		self._orientation = None
		self._transparent = True
		self._drawMode = None
		self._hatchStyleDict = {"transparent": wx.TRANSPARENT, "solid": wx.SOLID,
				"cross": wx.CROSS_HATCH, "reversediagonal": wx.BDIAGONAL_HATCH,
				"crossdiagonal": wx.CROSSDIAG_HATCH, "diagonal": wx.FDIAGONAL_HATCH,
				"horizontal": wx.HORIZONTAL_HATCH, "vertical": wx.VERTICAL_HATCH}
		super(DrawObject, self).__init__(*args, **kwargs)
		self._inInit = False


	def update(self):
		self.Parent._needRedraw = True


	def release(self):
		self._parent.removeDrawnObject(self)


	def draw(self, dc=None):
		"""
		Does the actual drawing.

		NOTE: it does not clear any old drawings of the shape, so this shouldn't be
		called except as part of a method of the parent that first clears the
		background.
		"""
		if not self.Visible or self._inInit:
			return
		srcObj = self.Parent
		if isinstance(srcObj, dabo.ui.dFormMixin):
			frm = srcObj
		else:
			frm = srcObj.Form
		x, y = self.Xpos, self.Ypos

		if dc is None:
			dc = self._dc or wx.WindowDC(srcObj)
		if self.Shape == "bmp":
			dc.DrawBitmap(self._bitmap, x, y, self._transparent)
			self._width = self._bitmap.GetWidth()
			self._height = self._bitmap.GetHeight()
			return

		if not self._useDefaults:
			self._penSettings(dc)
			self._brushSettings(dc)
			self._modeSettings(dc)

# 		if self.Application.Platform == "GTK" and \
# 				not (isinstance(srcObj, (dabo.ui.dPanel, dabo.ui.dPage, dabo.ui.dGrid))):
# 			if isinstance(srcObj, dabo.ui.dForm):
# 				x, y = srcObj.containerCoordinates(srcObj, (self.Xpos, self.Ypos))
# 			else:
# 				x, y = self.Parent.containerCoordinates(srcObj.Parent, (self.Xpos, self.Ypos))
# 		else:
# 			x, y = self.Xpos, self.Ypos
#
		if self.Shape == "circle":
			dc.DrawCircle(x, y, self.Radius)
			self._width = self._height = self.Radius * 2
		elif self.Shape == "arc":
			xc, yc = self.Xpos, self.Ypos
			x1 = xc + (math.cos(math.radians(self.StartAngle)) * self.Radius)
			y1 = yc - (math.sin(math.radians(self.StartAngle)) * self.Radius)
			x2 = xc + (math.cos(math.radians(self.EndAngle)) * self.Radius)
			y2 = yc - (math.sin(math.radians(self.EndAngle)) * self.Radius)
			dc.DrawArc(x1, y1, x2, y2, xc, yc)
		elif self.Shape == "ellipticarc":
			dc.DrawEllipticArc(self.Xpos, self.Ypos, self.Width, self.Height, self.StartAngle, self.EndAngle)
		elif self.Shape in ("rect", "roundrect", "ellipse"):
			w, h = self.Width, self.Height
			# If any of these values is -1, use the parent object's size
			if w < 0:
				w = self.Parent.Width
			if h < 0:
				h = self.Parent.Height
			if self.Shape == "rect":
				dc.DrawRectangle(x, y, w, h)
			elif self.Shape == "roundrect":
				dc.DrawRoundedRectangle(x, y, w, h, self.Radius)
			else:
				dc.DrawEllipse(x, y, w, h)
		elif self.Shape in ("polygon", "polylines"):
			if self.Shape == "polygon":
				dc.DrawPolygon(self.Points)
			else:
				dc.DrawLines(self.Points)
			xs = [pt[0] for pt in self.Points]
			ys = [pt[1] for pt in self.Points]
			self._xPos = min(xs)
			self._yPos = min(ys)
			self._width = max(xs) - self._xPos
			self._height = max(ys) - self._yPos
		elif self.Shape == "line":
			x1, y1 = self.Points[0]
			x2, y2 = self.Points[1]
			dc.DrawLine(x1, y1, x2, y2)
			self._xPos = min(x1, x2)
			self._yPos = min(y1, y2)
			self._width = abs(x1 - x2)
			self._height = abs(y1 - y2)
		elif self.Shape == "gradient":
			self._drawGradient(dc, x, y)
		elif self.Shape == "text":
			txt = self._text
			if not txt:
				return

			if not self._useDefaults:
				self._fontSettings(dc)
			if self._angle == 0:
				dc.DrawText(txt, x, y)
			else:
				dc.DrawRotatedText(txt, x, y, self._angle)
			w, h = dabo.ui.fontMetricFromDC(dc, txt)
			angle = self._angle % 360
			if angle % 90 == 0:
				if angle % 180 == 0:
					self._width, self._height = w, h
				else:
					# 90 degree variant; switch the values.
					self._width, self._height = h, w
			else:
				rad = math.radians(angle)
				self._width = abs(math.cos(rad) * w) + abs(math.sin(rad) * h)
				self._height = abs(math.sin(rad) * w) + abs(math.cos(rad) * h)


	def _drawGradient(self, dc, xpos, ypos):
		if self.GradientColor1 is None or self.GradientColor2 is None:
			return
		if self.Orientation is None:
			return
		if self.Width is None:
			wd = self.Parent.Width
		else:
			wd = self.Width
		if xpos is None:
			x1 = 0
			x2 = wd
		else:
			x1 = xpos
			x2 = x1 + wd
		if self.Height is None:
			ht = self.Parent.Height
		else:
			ht = self.Height
		if ypos is None:
			y1 = 0
			y2 = ht
		else:
			y1 = ypos
			y2 = y1 + ht

		dc.SetPen(wx.TRANSPARENT_PEN)
		r1, g1, b1 = self.GradientColor1
		r2, g2, b2 = self.GradientColor2

		if self.Orientation == "h":
			flrect = float(wd)
		else:
			flrect = float(ht)
		flrect = max(1, flrect)
		rstep = float((r2 - r1)) / flrect
		gstep = float((g2 - g1)) / flrect
		bstep = float((b2 - b1)) / flrect

		rf, gf, bf = 0, 0, 0
		if self.Orientation == "h":
			for x in range(x1, x1 + wd):
				currRow = (r1 + rf, g1 + gf, b1 + bf)
				dc.SetBrush(wx.Brush(currRow, wx.SOLID))
				dc.DrawRectangle(x1 + (x - x1), y1, 1, ht)
				rf = rf + rstep
				gf = gf + gstep
				bf = bf + bstep
		else:
			for y in range(y1, y1 + ht):
				currCol = (r1 + rf, g1 + gf, b1 + bf)
				dc.SetBrush(wx.Brush(currCol, wx.SOLID))
				dc.DrawRectangle(x1, y1 + (y - y1), wd, ht)
				rf = rf + rstep
				gf = gf + gstep
				bf = bf + bstep


	def bringToFront(self):
		self.Parent._bringDrawObjectToFront(self)


	def sendToBack(self):
		self.Parent._sendDrawObjectToBack(self)


	def moveUp(self, levels=1):
		self.Parent._moveDrawObjectUp(self, levels)


	def moveDown(self, levels=1):
		self.Parent._moveDrawObjectDown(self, levels)


	def _penSettings(self, dc):
		pw = self.PenWidth
		if not pw:
			# No pen
			pen = wx.TRANSPARENT_PEN
		else:
			if self.PenColor is None:
				pc = dColors.colorTupleFromName("black")
			else:
				if isinstance(self.PenColor, basestring):
					pc = dColors.colorTupleFromName(self.PenColor)
				else:
					pc = self.PenColor
			sty = self._lineStyle
			lnStyle = wx.SOLID
			if sty in ("dash", "dashed"):
				lnStyle = wx.SHORT_DASH
			elif sty in ("dot", "dotted"):
				lnStyle = wx.DOT
			elif sty in ("dotdash", "dashdot"):
				lnStyle = wx.DOT_DASH
			pen = wx.Pen(pc, pw, lnStyle)
		dc.SetPen(pen)


	def _brushSettings(self, dc):
		fill = self.FillColor
		hatch = self.HatchStyle
		if hatch is None:
			sty = wx.SOLID
		else:
			sty = self._hatchStyleDict.get(hatch.lower(), wx.SOLID)
		if fill is None:
			brush = wx.TRANSPARENT_BRUSH
		else:
			if isinstance(fill, basestring):
				fill = dColors.colorTupleFromName(fill)
			brush = wx.Brush(fill, style=sty)
		dc.SetBrush(brush)


	def _modeSettings(self, dc):
		mode = self.DrawMode
		if mode is None:
			logic = wx.COPY
		elif mode == "invert":
			logic = wx.INVERT
		elif mode == "and":
			logic = wx.AND
		elif mode == "and_invert":
			logic = wx.AND_INVERT
		elif mode == "and_reverse":
			logic = wx.AND_REVERSE
		elif mode == "clear":
			logic = wx.CLEAR
		elif mode == "equiv":
			logic = wx.EQUIV
		elif mode == "nand":
			logic = wx.NAND
		elif mode == "nor":
			logic = wx.NOR
		elif mode == "no_op":
			logic = wx.NO_OP
		elif mode == "or":
			logic = wx.OR
		elif mode == "or_invert":
			logic = wx.OR_INVERT
		elif mode == "or_reverse":
			logic = wx.OR_REVERSE
		elif mode == "set":
			logic = wx.SET
		elif mode == "src_invert":
			logic = wx.SRC_INVERT
		elif mode == "xor":
			logic = wx.XOR
		dc.SetLogicalFunction(logic)


	def _fontSettings(self, dc):
		fnt = dc.GetFont()
		# If the following call fails, the font has not been initialized, and can look
		# pretty ugly. In this case, initialize it to the system-default font.
		if self.FontFace:
			try:
				fnt.GetFaceName()
			except AttributeError:
				fnt = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
		else:
			fnt = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
		if self._fontFace is not None:
			fnt.SetFaceName(self._fontFace)
		if self._fontSize is not None:
			fnt.SetPointSize(self._fontSize)
		if self._fontBold is not None:
			if self._fontBold:
				fnt.SetWeight(wx.BOLD)
			else:
				fnt.SetWeight(wx.NORMAL)
		if self._fontItalic is not None:
			if self._fontItalic:
				fnt.SetStyle(wx.ITALIC)
			else:
				fnt.SetStyle(wx.NORMAL)
		if self._fontUnderline is not None:
			fnt.SetUnderlined(self._fontUnderline)
		if self._foreColor is not None:
			dc.SetTextForeground(self._foreColor)
		if self._backColor is not None:
			dc.SetTextBackground(self._backColor)
		dc.SetFont(fnt)
		self.update()


	# Property get/set methods
	def _getAngle(self):
		return self._angle

	def _setAngle(self, val):
		if self._angle != val:
			self._angle = val
			self.update()


	def _getBackColor(self):
		return self._backColor

	def _setBackColor(self, val):
		if self._backColor != val:
			self._backColor = val
			self.update()


	def _getBitmap(self):
		return self._bitmap

	def _setBitmap(self, val):
		if self._bitmap != val:
			self._bitmap = val
			self.update()


	def _getDrawMode(self):
		return self._drawMode

	def _setDrawMode(self, val):
		if val is None:
			self._drawMode = None
		else:
			val = val.lower()
			if val != self._drawMode:
				self._drawMode = val
				self.update()


	def _getEndAngle(self):
		return self._endAngle

	def _setEndAngle(self, val):
		if self._endAngle != val:
			self._endAngle = val
			self.update()


	def _getFillColor(self):
		return self._fillColor

	def _setFillColor(self, val):
		if self._fillColor != val:
			self._fillColor = val
			self.update()


	def _getFontBold(self):
		return self._fontBold

	def _setFontBold(self, val):
		if self._fontBold != val:
			self._fontBold = val
			self.update()


	def _getFontFace(self):
		return self._fontFace

	def _setFontFace(self, val):
		if self._fontFace != val:
			self._fontFace = val
			self.update()


	def _getFontItalic(self):
		return self._fontItalic

	def _setFontItalic(self, val):
		if self._fontItalic != val:
			self._fontItalic = val
			self.update()


	def _getFontSize(self):
		return self._fontSize

	def _setFontSize(self, val):
		if self._fontSize != val:
			self._fontSize = val
			self.update()


	def _getFontUnderline(self):
		return self._fontUnderline

	def _setFontUnderline(self, val):
		if self._fontUnderline != val:
			self._fontUnderline = val
			self.update()


	def _getForeColor(self):
		return self._foreColor

	def _setForeColor(self, val):
		if self._foreColor != val:
			self._foreColor = val
			self.update()


	def _getGradientColor1(self):
		return self._gradientColor1

	def _setGradientColor1(self, val):
		if isinstance(val, basestring):
			val = dColors.colorTupleFromName(val)
		if self._gradientColor1 != val:
			self._gradientColor1 = val
			self.update()


	def _getGradientColor2(self):
		return self._gradientColor2

	def _setGradientColor2(self, val):
		if isinstance(val, basestring):
			val = dColors.colorTupleFromName(val)
		if self._gradientColor2 != val:
			self._gradientColor2 = val
			self.update()


	def _getHatchStyle(self):
		return self._hatchStyle

	def _setHatchStyle(self, val):
		if isinstance(val, basestring):
			val = val.lower()
		if self._hatchStyle != val:
			self._hatchStyle = val
			self.update()


	def _getHeight(self):
		return self._height

	def _setHeight(self, val):
		if self._height != val:
			self._height = val
			self.update()


	def _getLineStyle(self):
		return self._lineStyle

	def _setLineStyle(self, val):
		if isinstance(val, basestring):
			val = val.lower()
		if self._lineStyle != val:
			self._lineStyle = val
			self.update()


	def _getOrientation(self):
		return self._orientation

	def _setOrientation(self, val):
		val = val[0].lower()
		if self._orientation != val:
			self._orientation = val
			self.update()


	def _getParent(self):
		return self._parent

	def _setParent(self, val):
		self._parent = val


	def _getPenColor(self):
		return self._penColor

	def _setPenColor(self, val):
		if self._penColor != val:
			self._penColor = val
			self.update()


	def _getPenWidth(self):
		return self._penWidth

	def _setPenWidth(self, val):
		if self._penWidth != val:
			self._penWidth = val
			self.update()


	def _getPoints(self):
		return self._points

	def _setPoints(self, val):
		if self._points != val:
			self._points = val
			self.update()


	def _getPosition(self):
		return (self._xPos, self._yPos)

	def _setPosition(self, val):
		if (self._xPos, self._yPos) != val:
			self._xPos, self._yPos = val
			self.update()


	def _getRadius(self):
		return self._radius

	def _setRadius(self, val):
		if self._radius != val:
			self._radius = val
			self.update()


	def _getRect(self):
		x, y, w, h = self._xPos, self._yPos, self._width, self._height
		if self._shape == "circle":
			# x and y are the center, so correct for that.
			x = x - self._radius
			y = y - self._radius
		elif (self._shape == "text") and (self._angle % 360 != 0):
			tw, th = dabo.ui.fontMetricFromDrawObject(self)
			angle = self._angle % 360
			if 0 < angle <= 90:
				rad = math.radians(angle)
				cos = math.cos(rad)
				y -= (h - cos*th)
			elif 90 < angle <= 180:
				rad = math.radians(90 - angle)
				cos = math.cos(rad)
				y -= h
				x -= (w - cos*th)
			elif 180 < angle <= 270:
				rad = math.radians(180 - angle)
				cos = math.cos(rad)
				y -= cos*th
				x -= w
			else:
				rad = math.radians(270 - angle)
				cos = math.cos(rad)
				x -= cos*th
		return wx.Rect(x, y, w, h)


	def _getSize(self):
		return (self._width, self._height)

	def _setSize(self, val):
		if (self._width, self._height) != val:
			self._width, self._height = val
			self.update()


	def _getShape(self):
		return self._shape

	def _setShape(self, val):
		self._shape = val


	def _getStartAngle(self):
		return self._startAngle

	def _setStartAngle(self, val):
		if self._startAngle != val:
			self._startAngle = val
			self.update()


	def _getText(self):
		return self._text

	def _setText(self, val):
		self._text = val


	def _getTransparent(self):
		return self._transparent

	def _setTransparent(self, val):
		self._transparent = val


	def _getVisible(self):
		return self._visible

	def _setVisible(self, val):
		if self._visible != val:
			self._visible = val
			self.update()


	def _getWidth(self):
		return self._width

	def _setWidth(self, val):
		if self._width != val:
			self._width = val
			self.update()


	def _getXpos(self):
		return self._xPos

	def _setXpos(self, val):
		if self._xPos != val:
			self._xPos = val
			self.update()


	def _getYpos(self):
		return self._yPos

	def _setYpos(self, val):
		if self._yPos != val:
			self._yPos = val
			self.update()


	Angle = property(_getAngle, _setAngle, None,
			_("Angle (in degrees) to draw text  (int)"))

	BackColor = property(_getBackColor, _setBackColor, None,
			_("Background color of text when using text objects  (str or tuple)"))

	Bitmap = property(_getBitmap, _setBitmap, None,
			_("Bitmap to be drawn on the object  (dBitmap)"))

	DrawMode = property(_getDrawMode, _setDrawMode, None,
			_("""Logical operation for how the drawing is done. Can be one of:  (str)

				copy (or None) - default
				invert
				and
				and_invert
				and_reverse
				clear
				equiv
				nand
				nor
				no_op
				or
				or_invert
				or_reverse
				set
				src_invert
				xor

			"""))

	EndAngle = property(_getEndAngle, _setEndAngle, None,
			_("Angle (in degrees) used to end drawing a circular or elliptic arc  (int)"))

	FillColor = property(_getFillColor, _setFillColor, None,
			_("Background color for the shape  (color)"))

	FontBold = property(_getFontBold, _setFontBold, None,
			_("Bold setting for text objects  (bool)"))

	FontFace = property(_getFontFace, _setFontFace, None,
			_("Face of the font used for text objects  (str)"))

	FontItalic = property(_getFontItalic, _setFontItalic, None,
			_("Italic setting for text objects  (bool)"))

	FontSize = property(_getFontSize, _setFontSize, None,
			_("Size of the font used for text objects  (int)"))

	FontUnderline = property(_getFontUnderline, _setFontUnderline, None,
			_("Underline setting for text objects  (bool)"))

	ForeColor = property(_getForeColor, _setForeColor, None,
			_("Color of text when using text objects  (str or tuple)"))

	GradientColor1 = property(_getGradientColor1, _setGradientColor1, None,
			_("Top/Left color for the gradient  (color: str or tuple)"))

	GradientColor2 = property(_getGradientColor2, _setGradientColor2, None,
			_("Bottom/Right color for the gradient  (color: str or tuple)"))

	HatchStyle = property(_getHatchStyle, _setHatchStyle, None,
			_("""Hatching style for the fill.  (str)
					Options are:

						Solid (default)
						Transparent
						Cross
						Horizontal
						Vertical
						Diagonal
						ReverseDiagonal
						CrossDiagonal

			"""))

	Height = property(_getHeight, _setHeight, None,
			_("For rectangles, the height of the shape  (int)"))

	LineStyle = property(_getLineStyle, _setLineStyle, None,
			_("Line style (solid, dash, dot) drawn  (str)"))

	Orientation = property(_getOrientation, _setOrientation, None,
			_("Direction of the drawn gradient ('v' or 'h')  (str)"))

	Parent = property(_getParent, _setParent, None,
			_("Reference to the object being drawn upon.  (object)"))

	PenColor = property(_getPenColor, _setPenColor, None,
			_("ForeColor of the shape's lines  (color)"))

	PenWidth = property(_getPenWidth, _setPenWidth, None,
			_("Width of the shape's lines  (int)"))

	Points = property(_getPoints, _setPoints, None,
			_("Tuple of (x,y) pairs defining a polygon.  (tuple)"))

	Position = property(_getPosition, _setPosition, None,
			_("Shorthand for (Xpos, Ypos).  (2-tuple)"))

	Radius = property(_getRadius, _setRadius, None,
			_("""For circles, the radius of the shape. For Rounded Rectangles,
			the radius of the rounded corner. (int)"""))

	Rect = property(_getRect, None, None,
			_("Reference to a wx.Rect that encompasses the drawn object (read-only) (wx.Rect)"))

	Size = property(_getSize, _setSize, None,
			_("Convenience property, equivalent to (Width, Height)  (2-tuple)"))

	Shape = property(_getShape, _setShape, None,
			_("Type of shape to draw  (str)"))

	StartAngle = property(_getStartAngle, _setStartAngle, None,
			_("Angle (in degrees) used to start drawing a circular or elliptic arc  (int)"))

	Text = property(_getText, _setText, None,
			_("Text to be drawn  (str)"))

	Transparent = property(_getTransparent, _setTransparent, None,
			_("Should the bitmap be drawn transparently?  (bool)"))

	Visible = property(_getVisible, _setVisible, None,
			_("Controls whether the shape is drawn.  (bool)"))

	Width = property(_getWidth, _setWidth, None,
			_("For rectangles, the width of the shape  (int)"))

	Xpos = property(_getXpos, _setXpos, None,
			_("""For circles, the x position of the center. For rectangles,
			the x position of the top left corner. (int)"""))

	Ypos = property(_getYpos, _setYpos, None,
			_("""For circles, the y position of the center. For rectangles,
			the y position of the top left corner. (int)"""))


	DynamicAngle = makeDynamicProperty(Angle)
	DynamicBackColor = makeDynamicProperty(BackColor)
	DynamicBitmap = makeDynamicProperty(Bitmap)
	DynamicDrawMode = makeDynamicProperty(DrawMode)
	DynamicFillColor = makeDynamicProperty(FillColor)
	DynamicFontBold = makeDynamicProperty(FontBold)
	DynamicFontFace = makeDynamicProperty(FontFace)
	DynamicFontItalic = makeDynamicProperty(FontItalic)
	DynamicFontSize = makeDynamicProperty(FontSize)
	DynamicFontUnderline = makeDynamicProperty(FontUnderline)
	DynamicForeColor = makeDynamicProperty(ForeColor)
	DynamicGradientColor1 = makeDynamicProperty(GradientColor1)
	DynamicGradientColor2 = makeDynamicProperty(GradientColor2)
	DynamicHeight = makeDynamicProperty(Height)
	DynamicLineStyle = makeDynamicProperty(LineStyle)
	DynamicOrientation = makeDynamicProperty(Orientation)
	DynamicParent = makeDynamicProperty(Parent)
	DynamicPenColor = makeDynamicProperty(PenColor)
	DynamicPenWidth = makeDynamicProperty(PenWidth)
	DynamicPoints = makeDynamicProperty(Points)
	DynamicRadius = makeDynamicProperty(Radius)
	DynamicShape = makeDynamicProperty(Shape)
	DynamicText = makeDynamicProperty(Text)
	DynamicTransparent = makeDynamicProperty(Transparent)
	DynamicVisible = makeDynamicProperty(Visible)
	DynamicWidth = makeDynamicProperty(Width)
	DynamicXpos = makeDynamicProperty(Xpos)
	DynamicYpos = makeDynamicProperty(Ypos)



class _DropTarget(wx.DropTarget):
	"""Class that handles drag/drop items of any type."""
	def __init__(self):
		wx.DropTarget.__init__(self)

		self._fileHandle  = self._textHandle = None
		self.compositeDataObject = wx.DataObjectComposite()
		self.fileData = wx.FileDataObject()
		self.compositeDataObject.Add(self.fileData)
		self.textData = wx.TextDataObject()
		self.compositeDataObject.Add(self.textData)
		self.SetDataObject(self.compositeDataObject)


	def OnData(self, x, y, defResult):
		if self.GetData():
			format = self.compositeDataObject.ReceivedFormat.GetType()
			mthd = param = None
			if format == wx.DF_FILENAME:
				if self._fileHandle:
					mthd = self._fileHandle.processDroppedFiles
					param = self.fileData.Filenames
			elif format == wx.DF_TEXT or wx.DF_HTML:
				if self._textHandle:
					mthd = self._textHandle.processDroppedText
					param = self.textData.Text
			if mthd:
				try:
					mthd(param, x, y)
				except TypeError, e:
					# Older implementation that doesn't accept x, y
					mthd(param)
		return defResult


	def OnDragOver(self, xpos, ypos, result):
		return wx.DragLink


	#Property getters and setters
	def _getFileHandler(self):
		return self._fileHandle

	def _setFileHandler(self, val):
		self._fileHandle = val


	def _getTextHandler(self):
		return self._textHandle

	def _setTextHandler(self, val):
		self._textHandle = val


	#PropertyDefinitions
	FileHandler = property(_getFileHandler, _setFileHandler, None,
			_("""Reference to the object that will handle files dropped on this control.
			When files are dropped, a list of them will be passed to this object's
			'processDroppedFiles()' method. Default=None  (object or None)"""))

	TextHandler = property(_getTextHandler, _setTextHandler, None,
			_("""Reference to the object that will handle text dropped on this control.
			When text is dropped, that text will be passed to this object's
			'processDroppedText()' method. Default=None  (object or None)"""))


if __name__ == "__main__":
	# Instantiating the mixin directly creates circular imports
	# o = dPemMixin()
	# print o.BaseClass
	# o.BaseClass = "dForm"
	# print o.BaseClass
	print "OK"
