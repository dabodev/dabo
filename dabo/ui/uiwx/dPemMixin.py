""" dPemMixin.py: Provide common PEM functionality """
import wx
import sys
import types
import dabo
from dabo.dLocalize import _
from dabo.ui.dPemMixinBase import dPemMixinBase
import dabo.dEvents as dEvents
import dabo.dColors as dColors
import dKeys
from dabo.dObject import dObject


class dPemMixin(dPemMixinBase):
	""" Provides Property/Event/Method interfaces for dForms and dControls.

	Subclasses can extend the property sheet by defining their own get/set
	functions along with their own property() statements.
	"""
	_call_beforeInit, _call_afterInit, _call_initProperties = False, False, False

	def __init__(self, preClass=None, parent=None, properties=None, 
			attProperties=None, *args, **kwargs):
		# This is the major, common constructor code for all the dabo/ui/uiwx 
		# classes. The __init__'s of each class are just thin wrappers to this
		# code.

		# NOTE: Do not call super(), there is similar code in propertyhelpermixin.__init__()
		#       that we override here.
		self._properties = {}
		
		# Lots of useful wx props are actually only settable before the
		# object is fully constructed. The self._preInitProperties dict keeps
		# track of those during the pre-init phase, to finally send the 
		# contents of it to the wx constructor. Our property setters know
		# if we are in pre-init or not, and instead of trying to modify 
		# the prop will instead add the appropriate entry to the _preInitProperties
		# dict. Additionally, there are certain wx properties that are required,
		# and we include those in the _preInitProperties dict as well so they may
		# be modified by our pre-init method hooks if needed:
		self._preInitProperties = {"style": 0}

		# There are a few controls that don't yet support 3-way inits (grid, for 
		# one). These controls will send the wx classref as the preClass argument, 
		# and we'll call __init__ on it when ready. We can tell if we are in a 
		# three-way init situation based on whether or not preClass is a function 
		# type.
		threeWayInit = (type(preClass) == types.FunctionType)
		
		if threeWayInit:
			# Instantiate the wx Pre object
			pre = preClass()
		else:
			pre = None

		# This will implicitly call the following user hooks:
		#    beforeInit()
		self._beforeInit(pre)
		self._initProperties()
		
		# Now that user code has had an opportunity to set the properties, we can 
		# see if there are properties sent to the constructor which will augment 
		# or override the properties set in beforeInit().
		
		# The keyword properties can come from either, both, or none of:
		#    + the properties dict
		#    + the kwargs dict
		# Get them sanitized into one dict:
		if properties is not None:
			# Override the class values
			for k,v in properties.items():
				self._properties[k] = v
		properties = self._extractKeywordProperties(kwargs, self._properties)
		
		if kwargs.has_key("style"):
			# If wx style parm sent, keep it as-is
			style = kwargs["style"]
		else:
			style = 0
		if kwargs.has_key("id"):
			# If wx id parm sent, keep it as-is
			id_ = kwargs["id"]
		else:
			id_ = -1

		if isinstance(self, dabo.ui.dMenuItem):
			# Hack: wx.MenuItem doesn't take a style arg,
			# and the parent arg is parentMenu
			del self._preInitProperties["style"]
			self._preInitProperties["parentMenu"] = parent
		elif isinstance(self, (dabo.ui.dMenu, dabo.ui.dMenuBar)):
			# Hack: wx.Menu has no style, parent, or id arg.
			del self._preInitProperties["style"]
		else:
			if self._preInitProperties.has_key("style"):
				self._preInitProperties["style"] = self._preInitProperties["style"] | style
			else:
				self._preInitProperties["style"] = style
			self._preInitProperties["parent"] = parent
			self._preInitProperties["id"] = id_
		
		# The user's subclass code has had a chance to tweak the style properties.
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
		else:
			preClass.__init__(self, *args, **kwargs)
		
		if threeWayInit:
			self.PostCreate(pre)

		self._pemObject = self

		# If a Name isn't given, a default name will be used, and it'll 
		# autonegotiate by adding an integer until it is a unique name.
		# If a Name is given explicitly, a NameError will be raised if
		# the given Name isn't unique among siblings:
		if not dabo.fastNameSet:
			name, _explicitName = self._processName(kwargs, self.__class__.__name__)
			self._initName(name, _explicitName=_explicitName)

		self._initEvents()
		self._afterInit()
		self.setProperties(properties)
		# 'attProperties' are properties restored from XML-like files where
		# all values are stored as strings.
		if attProperties:
			self.setPropertiesFromAtts(attProperties)

		super(dPemMixin, self).__init__(*args, **kwargs)

		# Finally, at the end of the init cycle, raise the Create event
		self.raiseEvent(dEvents.Create)


	def _constructed(self):
		"""Returns True if the ui object has been fully created yet, False otherwise."""
		try:
			return self == self._pemObject
		except Exception, e:
			print e
			return False

		
	def _beforeInit(self, pre):
		self._acceleratorTable = {}
		self._name = "?"
		self._pemObject = pre
		self._needRedraw = True
		self._borderColor = "black"
		self._borderWidth = 0
		self._borderLineStyle = "Solid"
		# Reference to the border-drawing object
		self._border = None
		# Flag that gets set to True when the object is being Destroyed
		self._finito = False
		# Dict to hold key bindings
		self._keyBindings = {}
		# Unique identifier attribute, if needed
		self._registryID = ""
		# List of all drawn objects
		self._drawnObjects = []
		self.beforeInit()
		
	
	def _afterInit(self):
		if False:
			## I don't think we need this code anymore, but if it turns out we do,
			## we have to not let it run if we are a dMenu*, because it'll cause
			## a segfault.
			try:
				if self.Position == (-1, -1):
					# The object was instantiated with a default position,
					# which ended up being (-1,-1). Change this to (0,0). 
					# This is completely moot when sizers are employed.
					self.Position = (0, 0)

			except:
				pass
	
		if not wx.HelpProvider.Get():
			# The app hasn't set a help provider, and one is needed
			# to be able to save/restore help text.
			wx.HelpProvider.Set(wx.SimpleHelpProvider())

		self._mouseLeftDown, self._mouseRightDown = False, False

		self.afterInit()

		
	def _preInitUI(self, kwargs):
		"""Subclass hook. Some wx objects (RadioBox) need certain props forced if
		they hadn't been set by the user either as a parm or in beforeInit()
		"""
		return kwargs
		
	def _getInitPropertiesList(self):
		return ("Alignment", "BorderStyle", "PasswordEntry", "Orientation", 
			"ShowLabels", "TabPosition")

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
		self.Bind(wx.EVT_WINDOW_DESTROY, self.__onWxDestroy)
		
		self.Bind(wx.EVT_SET_FOCUS, self.__onWxGotFocus)
		self.Bind(wx.EVT_IDLE, self.__onWxIdle)
		self.Bind(wx.EVT_KILL_FOCUS, self.__onWxLostFocus)
			
		self.Bind(wx.EVT_CHAR, self.__onWxKeyChar)
		self.Bind(wx.EVT_KEY_DOWN, self.__onWxKeyDown)
		self.Bind(wx.EVT_KEY_UP, self.__onWxKeyUp)

		self.Bind(wx.EVT_MOVE, self.__onWxMove)
				
		self.Bind(wx.EVT_LEFT_DOWN, self.__onWxMouseLeftDown)
		self.Bind(wx.EVT_LEFT_UP, self.__onWxMouseLeftUp)
		self.Bind(wx.EVT_RIGHT_DOWN, self.__onWxMouseRightDown)
		self.Bind(wx.EVT_RIGHT_UP, self.__onWxMouseRightUp)
		self.Bind(wx.EVT_ENTER_WINDOW, self.__onWxMouseEnter)
		self.Bind(wx.EVT_LEAVE_WINDOW, self.__onWxMouseLeave)
		self.Bind(wx.EVT_LEFT_DCLICK, self.__onWxMouseLeftDoubleClick)
		self.Bind(wx.EVT_MOTION, self.__onWxMouseMove)

		self.Bind(wx.EVT_CONTEXT_MENU, self.__onWxContextMenu)
		
		self.Bind(wx.EVT_PAINT, self.__onWxPaint)
		self.Bind(wx.EVT_SIZE, self.__onWxResize)
		
		self.bindEvent(dEvents.Create, self.__onCreate)
		self.bindEvent(dEvents.ChildBorn, self.__onChildBorn)
		
		self.initEvents()


	def __onCreate(self, evt):
		if self.Parent and hasattr(self.Parent, "raiseEvent"):
			self.Parent.raiseEvent(dEvents.ChildBorn, None, child=self)
	
	def __onChildBorn(self, evt):
		""" evt.Child will contain the reference to the new child. """
		pass
		
		
	def __onWxDestroy(self, evt):
		self._finito = (self == evt.GetEventObject() )
		self.raiseEvent(dEvents.Destroy, evt)
		
	def __onWxIdle(self, evt):
		if self._needRedraw:
			self._redraw()
		self.raiseEvent(dEvents.Idle, evt)
		
	def __onWxGotFocus(self, evt):
		self.raiseEvent(dEvents.GotFocus, evt)
		
	def __onWxKeyChar(self, evt):
		self.raiseEvent(dEvents.KeyChar, evt)
		## pkm 3/14/05: not sure about the ResumePropagation(), 
		## but I noticed on Windows that it is needed for the keypresses
		## to get noticed by anything but the focused control.
		## 2005.8.14 - ed - This is what is preventing keystrokes from working
		## under Linux. We may need to bracket the code and only
		## make this call if we are running on Windows.
#		evt.ResumePropagation(1)
		
	def __onWxKeyUp(self, evt):
		self.raiseEvent(dEvents.KeyUp, evt)
#		evt.ResumePropagation(1)
		
	def __onWxKeyDown(self, evt):
		self.raiseEvent(dEvents.KeyDown, evt)
#		evt.ResumePropagation(1)
	
	def __onWxLostFocus(self, evt):
		if self._finito: return
		self.raiseEvent(dEvents.LostFocus, evt)
	
	def __onWxMove(self, evt):
		if self._finito: return
		self.raiseEvent(dEvents.Move, evt)
	
	def __onWxMouseEnter(self, evt):
		st = self.StatusText
		if st is not None and self.Form is not None:
			self.Form.setStatusText(st)
		self.raiseEvent(dEvents.MouseEnter, evt)
		
	def __onWxMouseLeave(self, evt):
		self._mouseLeftDown, self._mouseRightDown = False, False
		st = self.StatusText
		if st is not None and self.Form is not None:
			self.Form.setStatusText("")
		self.raiseEvent(dEvents.MouseLeave, evt)
		
	def __onWxMouseLeftDoubleClick(self, evt):
		self.raiseEvent(dEvents.MouseLeftDoubleClick, evt)

	def __onWxMouseLeftDown(self, evt):
		self.raiseEvent(dEvents.MouseLeftDown, evt)
		self._mouseLeftDown = True
		
	def __onWxMouseLeftUp(self, evt):
		self.raiseEvent(dEvents.MouseLeftUp, evt)
		if self._mouseLeftDown:
			# mouse went down and up in this control: send a click:
			self.raiseEvent(dEvents.MouseLeftClick, evt)
			self._mouseLeftDown = False
		
	def __onWxMouseMove(self, evt):
		self.raiseEvent(dEvents.MouseMove, evt)
		
	def __onWxMouseRightDown(self, evt):
		self._mouseRightDown = True
		self.raiseEvent(dEvents.MouseRightDown, evt)
		
	def __onWxMouseRightUp(self, evt):
		self.raiseEvent(dEvents.MouseRightUp, evt)
		if self._mouseRightDown:
			# mouse went down and up in this control: send a click:
			self.raiseEvent(dEvents.MouseRightClick, evt)
			self._mouseRightDown = False
	
	def __onWxContextMenu(self, evt):
		self.raiseEvent(dEvents.ContextMenu, evt)

	def __onWxPaint(self, evt):
		if self._finito: return
		elif len(self._drawnObjects) > 0:
			self._needRedraw = True
		self.raiseEvent(dEvents.Paint, evt)
	
	def __onWxResize(self, evt):
		if self._finito: return
		elif len(self._drawnObjects) > 0:
			self._needRedraw = True
		self.raiseEvent(dEvents.Resize, evt)


	def bindKey(self, keyCombo, callback):
		"""Bind a key combination such as "ctrl+c" to a callback function.

		See dKeys.keyStrings for the valid string key codes.
		See dKeys.modifierStrings for the valid modifier codes.

		Examples:
			# When user presses <esc>, close the form:
			form.bindKey("esc", form.Close)

			# When user presses <ctrl><alt><w>, close the form:
			form.bindKey("ctrl+alt+w", form.Close)
		"""
		keys = keyCombo.split("+")
		# The modifier keys, if any, comprise all but the last key in keys
		mods = keys[:-1]
		key = keys[-1]
		upMods = [mm.upper() for mm in mods]

		# Convert the string mods and key into the correct parms for wx:
		flags = dKeys.mod_Normal
		for mod in mods:
			flags = flags | dKeys.modifierStrings[mod]

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
		bnd = {"callback" : callback, "eventData" : ed}
		self._keyBindings[anId] = bnd
		self.Bind(wx.EVT_MENU, self._keyCallback, id=anId)

				
	def _keyCallback(self, evt):
		bnd = self._keyBindings[evt.GetId()]
		keyEvent = dabo.dEvents.KeyEvent(None)
		keyEvent.EventData = bnd["eventData"]
		try:
			callback = bnd["callback"]
		except:
			# binding doesn't exist
			return
		callback(keyEvent)
			
	
	def unbindKey(self, keyCombo):
		"""Unbind a previously bound key combination.
		Fail silently if the key combination didn't exist already.
		"""
		table = self._acceleratorTable
		if table.has_key(keyCombo):
			self.Unbind(wx.EVT_MENU, id=table[keyCombo][2])
			del table[keyCombo]
			self.SetAcceleratorTable(wx.AcceleratorTable(table.values()))


	def getPropertyInfo(cls, name):
		return super(dPemMixin, cls).getPropertyInfo(name)
	getPropertyInfo = classmethod(getPropertyInfo)

	
	def lockDisplay(self):
		"""Locks the visual updates to the control to improve performance
		when many items are being updated at once.
		IMPORTANT: you must call unlockDisplay() when you are done,
		or your form (or parts of it) will look like it isn't responding.
		"""
		self.Freeze()
	
	
	def unlockDisplay(self):
		"""Unlocks the screen so that visual updates can be made. Must
		be called after a call to lockDisplay().
		"""
		self.Thaw()
	
	
	def addObject(self, classRef, Name=None, *args, **kwargs):
		""" Instantiate object as a child of self.
		
		The classRef argument must be a Dabo UI class definition. (it must inherit 
		dPemMixin).
		
		The name argument, if passed, will be sent along to the object's 
		constructor, which will attempt to set its Name accordingly. If the name
		argument is not passed (or None), the object will get a default Name as 
		defined in the object's class definition.

		Additional positional and/or keyword arguments will be sent along to the
		object's constructor.
		"""
		# Note that we could have just given addObject() a signature of:
		#   addObject(self, classRef, *args, **kwargs)
		# Which would simplify the implementation somewhat. However, we want
		# to enforce name as the second argument to avoid breaking old code.
		if Name is None:
			object = classRef(self, *args, **kwargs)
		else:
			object = classRef(self, Name=Name, *args, **kwargs)
		return object

	
	def raiseEvent(self, eventClass, nativeEvent=None, *args, **kwargs):
		# Call the Dabo-native raiseEvent(), passing along the wx.CallAfter
		# function, so that the Dabo events can be processed at next idle.
		
		##- 2004/01/07: Problems with segfaults and illegal instructions in some cases
		##-             with the wx.CallAfter. Revert back for now to calling in the
		##-             callstack.
		if True or eventClass is dabo.dEvents.Destroy:
			# Call immediately in this callstack so the object isn't completely
			# gone by the time the callback is called.
			super(dPemMixin, self).raiseEvent(eventClass, nativeEvent, *args, **kwargs)
		else:
			# Call with wx.CallAfter in the next Idle.
			super(dPemMixin, self).raiseEvent(eventClass, nativeEvent,
				uiCallAfterFunc=wx.CallAfter, *args, **kwargs)
	
	
	def formCoordinates(self, pos):
		"""A mouse click will report coordinates relative to the window
		which was clicked. For a control in a form, it is sometimes 
		necessary to translate this point to a position relative to the 
		containing form.
		"""
		ret = self.absoluteCoordinates(pos)
		if hasattr(self, "Form") and self.Form is not None:
			ret = self.Form.ScreenToClient(ret)
		return ret
	
	
	def absoluteCoordinates(self, pos):
		"""Translates a position value for a control to absolute screen position."""
		return self.ClientToScreen(pos)
	
	
	def showContextMenu(self, menu, pos=None):
		"""Display a context menu (popup) at the specified position.
		If no position is specified, the menu will be displayed at the 
		current mouse position.
		"""
		if pos is None:
			pos = wx.GetMousePosition()
		self.PopupMenu(menu, pos)
		
	
	def _getSizerInfo(self, prop):
		"""Returns True or False based on whether the property
		passed is contained in the sizer item's flags.
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
		""" Returns the current position of this control in its containing
		sizer. This is useful for when a control needs to be re-created in
		place.
		If the containing sizer is a box sizer, the integer position will
		be returned. If it is a grid sizer, a row,col tuple will be returned.
		If the object is not contained in a sizer, None will be returned.
		"""
		sz = self.GetContainingSizer()
		if not sz:
			return None
		if isinstance(sz, wx.BoxSizer):
			chil = sz.GetChildren()
			for pos in range(len(chil)):
				# Yeah, normally we'd just iterate over the children, but
				# we want the position, so...
				szitem = chil[pos]
				if szitem.IsWindow():
					if szitem.GetWindow() == self:
						return pos
			# If we reached here, something's wrong!
			dabo.errorLog.write(_("Containing sizer did not match item %s") % self.Name)
			return None
		elif isinstance(sz, wx.GridBagSizer):
			# Return a row,col tuple
			row, col = sz.GetItemPosition(self)
			return (row, col)
		else:
			return None
	
	
	def setAll(self, prop, val, recurse=True, filt=None):
		"""Iterates through all child objects, and attempts to set the
		value of the specified property to the specified value. If this
		object has no child objects, nothing happens. If any child object
		does not have the specified attribute/property, no attempt
		is made to add it. 
		If 'recurse' is True, setAll will be called on each child.
		If 'filt' is not empty, only children that matcg the expression in 'filt' 
		will be affected. The expression will be evaluated assuming
		the child object is prefixed to the expression. For example, if
		you want to only affect objects whose value of their 'foo' attribute
		equals 42, you'd pass:  filt="foo == 42", which would result in the 
		following being evaluated: eval("chld.%s" % filt). If that eval returns 
		True, the object will be affected.
		"""
		for chld in self.Children:
			ok = hasattr(chld, prop)
			if ok:
				if filt:
					ok = eval("chld.%s" % filt)
			if ok:
				if isinstance(val, basestring):
					# Wrap the value in single quotes
					exec("chld.%s = '%s'" % (prop, val))
				else:
					exec("chld.%s = %s" % (prop, val))
			if recurse:
				if hasattr(chld, "setAll"):
					chld.setAll(prop, val, recurse=recurse, filt=filt)

			
	def reCreate(self, child=None):
		""" Recreate an object. """
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
			return self.Parent.reCreate(self)
	
	
	def changeParent(self, newParent):
		"""The native wx method doesn't work on Macs."""
		return newParent.adopt(self)
		
	
	def adopt(self, obj):
		"""Moves an object to a new parent container."""
		if self.Application.Platform != "Mac":
			# Reparent() doesn't work on Macs
			obj.Reparent(self)
		else:
			# Re-create the object in the new parent, and then
			# destroy this instance. Note that any previous references
			# to this object will now be invalid.
			obj = self.reCreate(obj)
		return obj

	
	def release(self):
		""" Calls the object's destructor. """
		self.Destroy()
	
	
	def setFocus(self):
		"""Wrapper to the wx method."""
		self.SetFocus()
		
	
	def refresh(self):
		"""Wrapper to the wx method."""
		self.Refresh()
	
	
	def fitToSizer(self):
		"""If the object has a sizer, this will fit the object to 
		the size of the contained objects.
		"""
		if self.Sizer:
			self.Fit()
	
	
	def drawCircle(self, xPos, yPos, rad, penColor="black", penWidth=1,
			fillColor=None, lineStyle=None, persist=True):
		"""Draws a circle of the specified radius around the specified point.
		You can set the color and thickness of the line, as well as the 
		color of the fill. Normally, when persist=True, the circle will be 
		re-drawn on paint events, but if you pass False, it will be drawn 
		once only. 
		
		A drawing object is returned, or None if persist=False. You can 
		'remove' the drawing by setting the Visible property of the 
		returned object to False. You can also manipulate the position, size,
		color, and fill by changing the various properties of the object.
		"""
		obj = _drawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, Radius=rad, LineStyle=lineStyle, 
				Shape="circle", Xpos=xPos, Ypos=yPos)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj
	
	
	def drawRectangle(self, xPos, yPos, width, height, penColor="black", 
			penWidth=1, fillColor=None, lineStyle=None, persist=True):
		"""Draws a rectangle of the specified width and height beginning
		at the specified point. See the 'drawCircle()' method above for more
		details.
		"""
		obj = _drawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, LineStyle=lineStyle, Shape="rect", 
				Xpos=xPos, Ypos=yPos, Width=width, Height=height)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawPolygon(self, points, penColor="black", penWidth=1, 
				fillColor=None, lineStyle=None, persist=True):
		"""Draws a polygon defined by the specified points. The 'points'
		parameter should be a tuple of (x,y) pairs defining the polygon.
		See the 'drawCircle()' method above for more details.
		"""
		obj = _drawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, LineStyle=lineStyle, 
				Shape="polygon", Points=points)
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def drawLine(self, x1, y1, x2, y2, penColor="black", penWidth=1, 
				fillColor=None, lineStyle=None, persist=True):
		"""Draws a line between (x1,y1) and (x2, y2). 
		See the 'drawCircle()' method above for more details.
		"""
		obj = _drawObject(self, FillColor=fillColor, PenColor=penColor,
				PenWidth=penWidth, LineStyle=lineStyle, 
				Shape="line", Points=((x1,y1), (x2,y2)) )
		# Add it to the list of drawing objects
		obj = self._addToDrawnObjects(obj, persist)
		return obj


	def _addToDrawnObjects(self, obj, persist):
		self._drawnObjects.append(obj)
		self._redraw()
		if not persist:
			self._drawnObjects.remove(obj)
			obj = None
		return obj
		
		
	def _redraw(self):
		"""If the object has drawing routines that affect its appearance, this
		method is where they go. Subclasses should place code in the 
		redraw() hook method.
		"""
		# First, clear any old drawing
		self.ClearBackground()
		# Draw any shapes
		for obj in self._drawnObjects:
			obj.draw()
		# Call the hook
		self.redraw()
		# Clear the idle flag.
		self._needRedraw = False
	def redraw(self): pass
	
	
	def _bringDrawObjectToFront(self, obj):
		"""Given a drawing object, moves it to the end of the 
		list, so that it is drawn last.
		"""
		self._drawnObjects.remove(obj)
		self._drawnObjects.append(obj)
		self._needRedraw = True

		
	def _sendDrawObjectToBack(self, obj):
		"""Given a drawing object, moves it to the beginning of the 
		list, so that it is drawn first.
		"""
		self._drawnObjects.remove(obj)
		self._drawnObjects.insert(0, obj)
		self._needRedraw = True


	def _onResizeBorder(self, evt):
		"""Called when the user has defined a border for the control, and
		the control is resized.
		"""
		brd = self._border
		brd.Width, brd.Height = self.Width, self.Height

		
	def clone(self, obj, name=None):
		""" Create another object just like the passed object. It assumes that the 
		calling object will be the container of the newly created object.
		"""
		propValDict = obj.getProperties()
		if name is None:
			name = obj.Name + "1"
		newObj = self.addObject(obj.__class__, 
				name, style=obj.GetWindowStyle() )
		newObj.setProperties(propValDict)
		return newObj
		

	# The following 3 flag functions are used in some of the property
	# get/set functions.
	def _hasWindowStyleFlag(self, flag):
		""" Return whether or not the flag is set. (bool)"""
		if self._constructed():
			return (self.GetWindowStyleFlag() & flag) == flag
		else:
			return (self._preInitProperties["style"] & flag) == flag

	def _addWindowStyleFlag(self, flag):
		""" Add the flag to the window style."""
		if self._constructed():
			self.SetWindowStyleFlag(self.GetWindowStyleFlag() | flag)
		else:
			self._preInitProperties["style"] = self._preInitProperties["style"] | flag

	def _delWindowStyleFlag(self, flag):
		""" Remove the flag from the window style."""
		if self._constructed():
			self.SetWindowStyleFlag(self.GetWindowStyleFlag() & (~flag))
		else:
			self._preInitProperties["style"] = self._preInitProperties["style"] & (~flag)


	def _getBackColor(self):
		return self.GetBackgroundColour().Get()

	def _setBackColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				try:
					val = dColors.colorTupleFromName(val)
				except: pass
			if isinstance(val, tuple):
				self.SetBackgroundColour(val)
				# Background color changes don't result in an automatic refresh.
				self.Refresh()
		else:
			self._properties["BackColor"] = val


	def _getBorderColor(self):
		return self._borderColor

	def _setBorderColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				try:
					val = dColors.colorTupleFromName(val)
				except: pass
			self._borderColor = val
			if self._border:
				self._border.PenColor = val
			self._needRedraw = True
		else:
			self._properties["BorderColor"] = val
	
	def _getBorderLineStyle(self):
		return self._borderLineStyle
	
	def _setBorderLineStyle(self, val):
		val = self._expandPropStringValue(val, ("Solid", "Dash", "Dashed", "Dot", "Dotted", "DotDash", "DashDot"))
		self._borderLineStyle = val
		if self._border:
			self._border.LineStyle = val
		self._needRedraw = True

	def _getBorderWidth(self):
		return self._borderWidth

	def _setBorderWidth(self, val):
		if self._constructed():
			self._borderWidth = val
			if self._border:
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
		style = self._expandPropStringValue(val, ("None", "Simple", "Sunken", "Raised", "Double", "Static", "Default"))
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
		return self.GetLabel()
	
	def _setCaption(self, val):
		# Force the value to string
		val = "%s" % val
		if self._constructed():
			## 2/23/2005: there is a bug in wxGTK that resets the font when the 
			##            caption changes. So this is a workaround:
			font = self.Font
			self.SetLabel(val)
			self.Font = font

			# Frames have a Title separate from Label, but I can't think
			# of a reason why that would be necessary... can you? 
			self.SetTitle(val)
		else:
			self._properties["Caption"] = val


	def _getChildren(self):
		if hasattr(self, "GetChildren"):
			return self.GetChildren()
		else:
			return None
	
	
	def _getCntrlSizer(self):
		return self.GetContainingSizer()
		
	def _getCntrlSzItem(self):
		sz = self.GetContainingSizer()
		if isinstance(sz, wx.GridBagSizer):
			return sz.FindItem(self)
		else:
			pos = self.getPositionInSizer()
			if pos is None:
				# Nothing to do here...
				return None
			return sz.GetChildren()[pos]
		
	def _getEnabled(self):
		return self.IsEnabled()
	
	def _setEnabled(self, val):
		if self._constructed():
			self.Enable(val)
		else:
			self._properties["Enabled"] = False


	def _getFont(self):
		return self.GetFont()
	
	def _setFont(self, val):
		if self._constructed():
			self.SetFont(val)
		else:
			self._properties["Font"] = val

	
	def _getFontBold(self):
		return self.Font.GetWeight() == wx.BOLD
	
	def _setFontBold(self, val):
		if self._constructed():
			font = self.Font
			if val:
				font.SetWeight(wx.BOLD)
			else:
				font.SetWeight(wx.LIGHT)    # wx.NORMAL doesn't seem to work...
			self.Font = font
		else:
			self._properties["FontBold"] = val

	def _getFontDescription(self):
		f = self.Font
		ret = f.GetFaceName() + " " + str(f.GetPointSize())
		if f.GetWeight() == wx.BOLD:
			ret += " B"
		if f.GetStyle() == wx.ITALIC:
			ret += " I"
		return ret
	
	def _getFontInfo(self):
		return self.Font.GetNativeFontInfoDesc()

		
	def _getFontItalic(self):
		return self.Font.GetStyle() == wx.ITALIC
	
	def _setFontItalic(self, val):
		if self._constructed():
			font = self.Font
			if val:
				font.SetStyle(wx.ITALIC)
			else:
				font.SetStyle(wx.NORMAL)
			self.Font = font
		else:
			self._properties["FontItalic"] = val

	
	def _getFontFace(self):
		return self.Font.GetFaceName()

	def _setFontFace(self, val):
		if self._constructed():
			f = self.Font
			f.SetFaceName(val)
			self.Font = f
		else:
			self._properties["FontFace"] = val

	
	def _getFontSize(self):
		return self.Font.GetPointSize()
	
	def _setFontSize(self, val):
		if self._constructed():
			font = self.Font
			font.SetPointSize(int(val))
			self.Font = font
		else:
			self._properties["FontSize"] = val
	
	def _getFontUnderline(self):
		return self.Font.GetUnderlined()
	
	def _setFontUnderline(self, val):
		if self._constructed():
			# underlining doesn't seem to be working...
			font = self.Font
			font.SetUnderlined(bool(val))
			self.Font = font
		else:
			self._properties["FontUnderline"] = val


	def _getForeColor(self):
		return self.GetForegroundColour().Get()

	def _setForeColor(self, val):
		if self._constructed():
			if isinstance(val, basestring):
				try:
					val = dColors.colorTupleFromName(val)
				except: pass
			self.SetForegroundColour(val)
		else:
			self._properties["ForeColor"] = val

	
	def _getHeight(self):
		return self.GetSize()[1]

	def _setHeight(self, val):
		if self._constructed():
			newSize = self.GetSize()[0], int(val)
			if isinstance(self, (wx.Frame, wx.Dialog) ):
				self.SetSize(newSize)
			else:
				self.SetBestFittingSize(newSize)
		else:
			self._properties["Height"] = val


	def _getHelpContextText(self):
		return self.GetHelpText()
	
	def _setHelpContextText(self, val):
		if self._constructed():
			self.SetHelpText(val)
		else:
			self._properties["HelpContextText"] = val


	def _getLeft(self):
		return self.GetPosition()[0]
	
	def _setLeft(self, val):
		if self._constructed():
			self.SetPosition((int(val), self.Top))
		else:
			self._properties["Left"] = val

		
	def _getMousePointer(self):
		return self.GetCursor()
	
	def _setMousePointer(self, val):
		if self._constructed():
			self.SetCursor(val)
		else:
			self._properties["MousePointer"] = val


	def _getName(self):
		try:
			name = self.GetName()
		except AttributeError:
			# Some objects that inherit from dPemMixin (dMenu*) don't have GetName()
			# or SetName() methods.
			name = self._name
		self._name = name      # keeps name available even after C++ object is gone.
		return name
	
	def _setName(self, name, _userExplicit=True):
		if self._constructed():
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
					if hasattr(self.Parent, name) and type(getattr(self.Parent, name)) != wx._core._wxPyDeadObject \
						and getattr(self.Parent, name) != self:
						raise NameError, "Name '%s' is already in use." % name
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
					i = 0
					while True:
						if i == 0:
							candidate = name
						else:
							candidate = "%s%s" % (name, i)
						nameError = hasattr(parent, candidate) and type(getattr(parent, candidate)) != wx._core._wxPyDeadObject \
							and getattr(parent, candidate) != self
						if not nameError:
							for window in parent.GetChildren():
								if window.GetName() == candidate and window != self:
									nameError = True
									break
						if nameError:
							i += 1
						else:
							name = candidate
							break
				else:
					# the user is explicitly setting the Name. If another object already
					# has the name, we must raise an exception immediately.
					if hasattr(parent, name) and type(getattr(parent, name)) != wx._core._wxPyDeadObject \
						and getattr(parent, name) != self:
						raise NameError, "Name '%s' is already in use." % name
					else:
						for window in parent.GetChildren():
							if str(window.GetName()) == str(name) and window != self:
								raise NameError, "Name '%s' is already in use." % name
					
			else:
				# Can't do the name check for siblings, so allow it for now.
				# This problem would only apply to top-level forms, so it really
				# wouldn't matter anyway in a practical sense.
				name = name
	
			name = str(name)
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

		else:
			self._properties["Name"] = name
	

	def _setNameBase(self, val):
		if self._constructed():
			self._setName(val, False)
		else:
			self._properties["NameBase"] = val
		
		
	def _getParent(self):
		return self.GetParent()
	
	def _setParent(self, val):
		if self._constructed():
			self.changeParent(val)
		else:
			self._properties["Parent"] = val

		
	def _getPosition(self):
		return self.GetPosition()

	def _setPosition(self, val):
		if self._constructed():
			self.SetPosition(val)
		else:
			self._properties["Position"] = val


	def _getRegID(self):
		return self._registryID
	def _setRegID(self, val):
		if self._registryID:
			# These should be immutable once set
			raise AttributeError, _("RegIDs cannot be changed once they are set")
		self._registryID = val
		try:
			self.Form.registerObject(self)
			# If the Form defines event callbacks for the object, bind them:
			self._autoBindEvents(context=self.Form)
		except:
			dabo.errorLog.write(_("Failed to register RegID '%s'") % val)
	
	
	def _getSize(self): 
		return self.GetSize()

	def _setSize(self, val):
		if self._constructed():
			if isinstance(self, (wx.Frame, wx.Dialog) ):
				self.SetSize(val)
			else:
				self.SetBestFittingSize(val)
		else:
			self._properties["Size"] = val
	
	def _getSizer(self):
		return self.GetSizer()
		
	def _setSizer(self, val):
		if self._constructed():
			self.SetSizer(val, True)
			try:
				val.Parent = self
			except: pass
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
		t = self.GetToolTip()
		if t:
			return t.GetTip()
		else:
			return ""

	def _setToolTipText(self, val):
		if self._constructed():
			t = self.GetToolTip()
			if t:
				t.SetTip(val)
			else:
				if val:
					t = wx.ToolTip(val)
					self.SetToolTip(t)
		else:
			self._properties["ToolTipText"] = val

	def _getTop(self):
		return self.GetPosition()[1]
	
	def _setTop(self, val):
		if self._constructed():
			self.SetPosition((self.Left, int(val)))
		else:
			self._properties["Top"] = val

	
	def _getVisible(self):
		return self.IsShown()
	
	def _setVisible(self, val):
		if self._constructed():
			self.Show(bool(val))
		else:
			self._properties["Visible"] = val

		
	def _getWidth(self):
		return self.GetSize()[0]

	def _setWidth(self, val):
		if self._constructed():
			newSize = int(val), self.GetSize()[1]
			if isinstance(self, (wx.Frame, wx.Dialog) ):
				self.SetSize(newSize)
			else:
				self.SetBestFittingSize(newSize)
		else:
			self._properties["Width"] = val

	def _getWindowHandle(self):
		return self.GetHandle()



	# Property definitions follow
	BackColor = property(_getBackColor, _setBackColor, None,
			_("Specifies the background color of the object. (tuple)"))

	BorderColor = property(_getBorderColor, _setBorderColor, None,
			_("""Color of the border drawn around the control, if any. 

			Default='black'  (str or color tuple)"""))
	
	BorderLineStyle = property(_getBorderLineStyle, _setBorderLineStyle, None,
			_("""Style of line for the border drawn around the control. Possible
			choices are:
				'Solid'  (default)
				'Dash'
				'Dot' 
				'DotDash'
				'DashDot'
			"""))

	BorderStyle = property(_getBorderStyle, _setBorderStyle, None,
			_("""Specifies the type of border for this window. (int).
			     None
			     Simple
			     Sunken 
			     Raised""") )
	
	BorderWidth = property(_getBorderWidth, _setBorderWidth, None,
			_("""Width of the border drawn around the control, if any. 
			
Default=0 (no border)  (int)"""))

	Caption = property(_getCaption, _setCaption, None, 
			_("The caption of the object. (str)") )

	Children = property(_getChildren, None, None, 
			_("""Returns a list of object references to the children of this object.
			Only applies to containers. Children will be None for non-containers."""))
	
	ControllingSizer = property(_getCntrlSizer, None, None,
			_("Reference to the sizer that controls this control's layout.  (dSizer)") )

	ControllingSizerItem = property(_getCntrlSzItem, None, None,
			_("""Returns the sizer item (or None if not in a sizer) that controls the 
		sizing of this control. It is useful for getting information about how the 
		item is being sized, and for changing those settings. (wx.SizerItem)"""))
		
	Enabled = property(_getEnabled, _setEnabled, None,
			_("Specifies whether the object (and its children) can get user input. (bool)") )

	Font = property(_getFont, _setFont, None,
			_("The font properties of the object. (obj)") )
	
	FontBold = property(_getFontBold, _setFontBold, None,
			_("Specifies if the font is bold-faced. (bool)") )
	
	FontDescription = property(_getFontDescription, None, None, 
			_("Human-readable description of the current font settings. (str)") )
	
	FontFace = property(_getFontFace, _setFontFace, None,
			_("Specifies the font face. (str)") )
	
	FontInfo = property(_getFontInfo, None, None,
			_("Specifies the platform-native font info string. Read-only. (str)") )
	
	FontItalic = property(_getFontItalic, _setFontItalic, None,
			_("Specifies whether font is italicized. (bool)") )
	
	FontSize = property(_getFontSize, _setFontSize, None,
			_("Specifies the point size of the font. (int)") )
	
	FontUnderline = property(_getFontUnderline, _setFontUnderline, None,
			_("Specifies whether text is underlined. (bool)") )

	ForeColor = property(_getForeColor, _setForeColor, None,
			_("Specifies the foreground color of the object. (tuple)") )

	Height = property(_getHeight, _setHeight, None,
			_("The height of the object. (int)") )
	
	HelpContextText = property(_getHelpContextText, _setHelpContextText, None,
			_("Specifies the context-sensitive help text associated with this window. (str)") )
	
	Left = property(_getLeft, _setLeft, None,
			_("The left position of the object. (int)") )
	
	MousePointer = property(_getMousePointer, _setMousePointer, None,
			_("Specifies the shape of the mouse pointer when it enters this window. (obj)") )
	
	Name = property(_getName, _setName, None, 
			_("""Specifies the name of the object, which must be unique among siblings.
			
			If the specified name isn't unique, an exception will be raised. See also
			NameBase, which let's you set a base name and Dabo will automatically append
			integers to make it unique.
			""") )
	
	NameBase = property(None, _setNameBase, None,
			_("""Specifies the base name of the object.
			
			The base name specified will become the object's Name, unless another sibling
			already has that name, in which case Dabo will find the next unique name by
			adding integers to the end of the base name. For example, if your code says:
			
				self.NameBase = "txtAddress" 
				
			and there is already a sibling object with that name, your object will end up
			with Name = "txtAddress1".
			
			This property is write-only at runtime.
			""") )
		
	Parent = property(_getParent, _setParent, None,	
			_("The containing object. (obj)") )

	Position = property(_getPosition, _setPosition, None, 
			_("The (x,y) position of the object. (tuple)") )

	RegID = property(_getRegID, _setRegID, None, 
			_("A unique identifier used for referencing by other objects. (str)") )

	Size = property(_getSize, _setSize, None,
			_("The size of the object. (tuple)") )

	Sizer = property(_getSizer, _setSizer, None, 
			_("The sizer for the object.") )

	StatusText = property(_getStatusText, _setStatusText, None,
			_("Specifies the text that displays in the form's status bar, if any."))

	Tag = property(_getTag, _setTag, None,
			_("A property that user code can safely use for specific purposes.") )
		
	ToolTipText = property(_getToolTipText, _setToolTipText, None,
			_("Specifies the tooltip text associated with this window. (str)") )

	Top = property(_getTop, _setTop, None, 
			_("The top position of the object. (int)") )
	
	Visible = property(_getVisible, _setVisible, None,
			_("Specifies whether the object is visible at runtime. (bool)") )                    

	Width = property(_getWidth, _setWidth, None,
			_("The width of the object. (int)") )
	
	WindowHandle = property(_getWindowHandle, None, None,
			_("The platform-specific handle for the window. Read-only. (long)") )



class _drawObject(dObject):
	"""Class to handle drawing in Dabo. It is not meant to be used directly;
	instead, it is returned after a drawing instruction is called.
	"""
	def __init__(self, parent, *args, **kwargs):
		self._inInit = True
		# Initialize property atts
		self._parent = parent
		self._fillColor = None
		self._height = None
		self._lineStyle = None
		self._penColor = None
		self._penWidth = None
		self._points = None
		self._radius = None
		self._shape = None
		self._visible = True
		self._width = None
		self._xPos = None
		self._yPos = None
		super(_drawObject, self).__init__(*args, **kwargs)
		self._inInit = False
	
	
	def update(self):
		self.Parent._needRedraw = True
		
		
	def draw(self):
		"""Does the actual drawing. NOTE: it does not clear any old 
		drawings of the shape, so this shouldn't be called except as 
		part of a method of the parent that first clears the background.
		"""
		if not self.Visible or self._inInit:
			return
		dc = wx.ClientDC(self.Parent)
		pw = self.PenWidth
		if self.PenColor is None:
			pc = dColors.colorTupleFromName("black")
		else:
			pc = dColors.colorTupleFromName(self.PenColor)

		sty = self._lineStyle
		lnStyle = wx.SOLID
		if sty in ("dash", "dashed"):
#				lnStyle = wx.LONG_DASH		#wx.SHORT_DASH
			lnStyle = wx.SHORT_DASH
		elif sty in ("dot", "dotted"):
			lnStyle = wx.DOT
		elif sty in ("dotdash", "dashdot"):
			lnStyle = wx.DOT_DASH

		dc.SetPen(wx.Pen(pc, pw, lnStyle))
		fill = self.FillColor
		if fill is None:
			brush = wx.Brush(fill, style=wx.TRANSPARENT)
		else:
			brush = wx.Brush(dColors.colorTupleFromName(fill))
		dc.SetBrush(brush)
		if self.Shape == "circle":
			dc.DrawCircle(self.Xpos, self.Ypos, self.Radius)
		elif self.Shape == "rect":
			dc.DrawLines([(0,0), (self.Width-pw, 0), (self.Width-pw, self.Height-pw), 
					(0, self.Height-pw), (0,0)])
		elif self.Shape == "polygon":
			dc.DrawPolygon(self.Points)
		elif self.Shape == "line":
			x1, y1 = self.Points[0]
			x2, y2 = self.Points[1]
			dc.DrawLine(x1, y1, x2, y2)

	
	def bringToFront(self):
		self.Parent._bringDrawObjectToFront(self)
		
	
	def sendToBack(self):
		self.Parent._sendDrawObjectToBack(self)
		

	# Property get/set methods
	def _getFillColor(self):
		return self._fillColor
		
	def _setFillColor(self, val):
		self._fillColor = val
		self.update()

	def _getHeight(self):
		return self._height
		
	def _setHeight(self, val):
		self._height = val
		self.update()
	
	def _getLineStyle(self):
		return self._lineStyle
	
	def _setLineStyle(self, val):
		if isinstance(val, basestring):
			val = val.lower()
		self._lineStyle = val
		self.update()

	def _getParent(self):
		return self._parent
		
	def _setParent(self, val):
		self._parent = val

	def _getPenColor(self):
		return self._penColor
		
	def _setPenColor(self, val):
		self._penColor = val
		self.update()

	def _getPenWidth(self):
		return self._penWidth
		
	def _setPenWidth(self, val):
		self._penWidth = val
		self.update()

	def _getPoints(self):
		return self._points
		
	def _setPoints(self, val):
		self._points = val
		self.update()

	def _getRadius(self):
		return self._radius
		
	def _setRadius(self, val):
		self._radius = val
		self.update()
		
	def _getShape(self):
		return self._shape
		
	def _setShape(self, val):
		self._shape = val
		
	def _getVisible(self):
		return self._visible
		
	def _setVisible(self, val):
		self._visible = val
		self.update()

	def _getWidth(self):
		return self._width
		
	def _setWidth(self, val):
		self._width = val
		self.update()

	def _getXpos(self):
		return self._xPos
		
	def _setXpos(self, val):
		self._xPos = val
		self.update()
		
	def _getYpos(self):
		return self._yPos
		
	def _setYpos(self, val):
		self._yPos = val
		self.update()
		
		
	FillColor = property(_getFillColor, _setFillColor, None,
			_("Background color for the shape  (color)"))

	Height = property(_getHeight, _setHeight, None,
			_("For rectangles, the height of the shape  (int)"))

	LineStyle = property(_getLineStyle, _setLineStyle, None,
			_("Line style (solid, dash, dot) drawn  (str)"))

	Parent = property(_getParent, _setParent, None,
			_("Reference to the object being drawn upon.  (object)"))

	PenColor = property(_getPenColor, _setPenColor, None,
			_("ForeColor of the shape's lines  (color)"))

	PenWidth = property(_getPenWidth, _setPenWidth, None,
			_("Width of the shape's lines  (int)"))
	
	Points = property(_getPoints, _setPoints, None,
			_("Tuple of (x,y) pairs defining a polygon.  (tuple)"))

	Radius = property(_getRadius, _setRadius, None,
			_("For circles, the radius of the shape  (int)"))

	Shape = property(_getShape, _setShape, None,
			_("Type of shape to draw  (str)"))

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

	


if __name__ == "__main__":
	o = dPemMixin()
	print o.BaseClass
	o.BaseClass = "dForm"
	print o.BaseClass
