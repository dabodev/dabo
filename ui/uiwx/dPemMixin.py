""" dPemMixin.py: Provide common PEM functionality """
import wx, sys, types
import dabo, dabo.common
from dabo.dLocalize import _
from dabo.ui.dPemMixinBase import dPemMixinBase
import dabo.dEvents as dEvents
import dabo.common.dColors as dColors


class dPemMixin(dPemMixinBase):
	""" Provides Property/Event/Method interfaces for dForms and dControls.

	Subclasses can extend the property sheet by defining their own get/set
	functions along with their own property() statements.
	"""
	def __init__(self, preClass=None, parent=None, properties=None, *args, **kwargs):
		# This is the major, common constructor code for all the dabo/ui/uiwx 
		# classes. The __init__'s of each class are just thin wrappers to this
		# code.

		# self.properties can be set in the userland beforeInit() hook.
		self.properties = {}
		
		# Lots of useful wx props are actually only settable before the
		# object is fully constructed. The self._initProperties dict keeps
		# track of those during the pre-init phase, to finally send the 
		# contents of it to the wx constructor. Our property setters know
		# if we are in pre-init or not, and instead of trying to modify 
		# the prop will instead add the appropriate entry to the _initProperties
		# dict. Additionally, there are certain wx properties that are required,
		# and we include those in the _initProperties dict as well so they may
		# be modified by our pre-init method hooks if needed:
		self._initProperties = {"style": 0}

		# There are a few controls that don't yet support 3-way inits (grid, for one).
		# These controls will send the wx classref as the preClass argument, and we'll
		# call __init__ on it when ready. We can tell if we are in a three-way init
		# situation based on whether or not preClass is a function type.
		threeWayInit = (type(preClass) == types.FunctionType)
		
		if threeWayInit:
			# Instantiate the wx Pre object
			pre = preClass()
		else:
			pre = None
		
		# This will implicitly call the following user hooks:
		#    beforeInit()
		#    initStyleProperties()
		self._beforeInit(pre)
		
		# Now that user code has had an opportunity to set the properties, we can see
		# if there are properties sent to the constructor which will augment or override
		# and properties set in beforeInit()
		
		# The keyword properties can come from either, both, or none of:
		#    + self.properties (set by user code in self.beforeInit())
		#    + the properties dict
		#    + the kwargs dict
		# Get them sanitized into one dict:
		if properties is not None:
			# Override the class values
			for k,v in properties.items():
				self.properties[k] = v
		properties = self.extractKeywordProperties(kwargs, self.properties)
		
		# If a Name isn't given, a default name will be used, and it'll 
		# autonegotiate by adding an integer until it is a unique name.
		# If a Name is given explicitly, a NameError will be raised if
		# the given Name isn't unique among siblings:
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)

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
			del self._initProperties["style"]
			self._initProperties["parentMenu"] = parent
		elif isinstance(self, (dabo.ui.dMenu, dabo.ui.dMenuBar)):
			# Hack: wx.Menu has no style, parent, or id arg.
			del self._initProperties["style"]
		else:
			self._initProperties["style"] = style
			self._initProperties["parent"] = parent
			self._initProperties["id"] = id_
		
		
		# The user's subclass code has had a chance to tweak the style properties.
		# Insert any of those into the arguments to send to the wx constructor:
		properties = self._setInitProperties(**properties)
		for prop in self._initProperties.keys():
			kwargs[prop] = self._initProperties[prop]
		
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
		
		self._initName(name, _explicitName=_explicitName)
		
		self._afterInit()
		self.setProperties(properties)
	
	def __getattr__(self, att):
		""" Try to resolve att to a child object reference.

		This allows accessing children with the style:
			self.mainPanel.txtName.Value = "test"
		"""
		ret = None
		if self._IsContainer:
			# Only objects that can contain other objects can use this method.
			try:
				ret = self.FindWindowByName(att)
			except:
				pass
		if ret is None:
			raise AttributeError, "%s object has no attribute %s" % (
				self._name, att)
		else:
			return ret

			
	def _initName(self, name=None, _explicitName=True):
		if name is None:
			name = self.Name
		
		try:
			self._setName(name, _userExplicit=_explicitName)
		except AttributeError:
			# Some toolkits (Tkinter) don't let objects change their
			# names after instantiation.
			pass

			
	def _beforeInit(self, pre):
		self.acceleratorTable = []
		self._name = "?"
		self._pemObject = pre
		self.initStyleProperties()
		
		# Call the subclass hook:
		self.beforeInit()
		
		
	def _afterInit(self):
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
		
		self._pemObject = self
		self.initProperties()
		self.initChildObjects()
		self.afterInit()
		
		try:
			self.SetAcceleratorTable(wx.AcceleratorTable(self.acceleratorTable))
		except:
			pass
		self._initEvents()
		self.initEvents()
		self.raiseEvent(dEvents.Create)

		
	def _preInitUI(self, kwargs):
		"""Subclass hook. Some wx objects (RadioBox) need certain props forced if
		they hadn't been set by the user either as a parm or in initStyleProperties"""
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
		
		self.Bind(wx.EVT_PAINT, self.__onWxPaint)
		self.Bind(wx.EVT_SIZE, self.__onWxResize)
		
	
	def __onWxDestroy(self, evt):
		self.raiseEvent(dEvents.Destroy, evt)
		
	def __onWxIdle(self, evt):
		self.raiseEvent(dEvents.Idle, evt)
		
	def __onWxGotFocus(self, evt):
		self.raiseEvent(dEvents.GotFocus, evt)
		
	def __onWxKeyChar(self, evt):
		self.raiseEvent(dEvents.KeyChar, evt)
		
	def __onWxKeyUp(self, evt):
		self.raiseEvent(dEvents.KeyUp, evt)
		
	def __onWxKeyDown(self, evt):
		self.raiseEvent(dEvents.KeyDown, evt)
	
	def __onWxLostFocus(self, evt):
		self.raiseEvent(dEvents.LostFocus, evt)
	
	def __onWxMove(self, evt):
		self.raiseEvent(dEvents.Move, evt)
	
	def __onWxMouseEnter(self, evt):
		self.raiseEvent(dEvents.MouseEnter, evt)
		
	def __onWxMouseLeave(self, evt):
		self._mouseLeftDown, self._mouseRightDown = False, False
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
	
	
	def __onWxPaint(self, evt):
		self.raiseEvent(dEvents.Paint, evt)
	
	def __onWxResize(self, evt):
		self.raiseEvent(dEvents.Resize, evt)
		
		
	def getPropertyInfo(self, name):
		#d = dPemMixin.doDefault(name)   # the property helper does most of the work
		d = super(dPemMixin, self).getPropertyInfo(name)

		# List of all props we ever want to show in the Designer
		d["showInDesigner"] = name in dabo.ui.propsToShowInDesigner

		# Some wx-specific props need to be initialized early. Let the designer know:
		d["preInitProperty"] = name in self._initProperties.values()
		
		# Finally, override the default editable state. The base behavior
		# is to make any prop with a setter method editable, but some simply
		# should not be edited in the Designer.
		d["editValueInDesigner"] = name in dabo.ui.propsToEditInDesigner

		return d
		
	
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
	
			
	def _processName(self, kwargs, defaultName):
		# Called by the constructors of the dObjects, to properly set the
		# name of the object based on whether the user set it explicitly
		# or Dabo is to provide it implicitly.
		if "Name" in kwargs.keys():
			if "_explicitName" in kwargs.keys():
				_explicitName = kwargs["_explicitName"]
				del kwargs["_explicitName"]
			else:
				_explicitName = True
			name = kwargs["Name"]
		else:
			_explicitName = False
			name = defaultName
		return name, _explicitName
		

	def reCreate(self, child=None):
		""" Recreate self.
		"""
		if child is not None:
			propValDict = child.getProperties()
			style = child.GetWindowStyle()
			classRef = child.__class__
			name = child.Name
			child.Destroy()
			newObj = self.addObject(classRef, name, style=style)
			newObj.setProperties(propValDict)
			return newObj
		else:
			return self.Parent.reCreate(self)
	
	
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
	def hasWindowStyleFlag(self, flag):
		""" Return whether or not the flag is set. (bool)
		"""
		if self._pemObject == self:
			return (self.GetWindowStyleFlag() & flag) == flag
		else:
			return (self._initProperties["style"] & flag) == flag

	def addWindowStyleFlag(self, flag):
		""" Add the flag to the window style.
		"""
		if self._pemObject == self:
			self.SetWindowStyleFlag(self.GetWindowStyleFlag() | flag)
		else:
			self._initProperties["style"] = self._initProperties["style"] | flag

	def delWindowStyleFlag(self, flag):
		""" Remove the flag from the window style.
		"""
		if self._pemObject == self:
			self.SetWindowStyleFlag(self.GetWindowStyleFlag() & (~flag))
		else:
			self._initProperties["style"] = self._initProperties["style"] & (~flag)

	def getColorTupleFromName(self, color):
		"""Given a color name, such as "Blue" or "Aquamarine", return a color tuple.
		
		This is used internally in the ForeColor and BackColor property setters. The
		color name is not case-sensitive. If the color name doesn't exist, an exception
		is raised.
		"""
		try:
			return dColors.colorDict[color.lower().strip()]
		except KeyError:
			raise KeyError, "Color '%s' is not defined." % color

	# Scroll to the bottom to see the property definitions.

	# Property get/set/delete methods follow.

	def _getBackColor(self):
		return self._pemObject.GetBackgroundColour()

	def _getBackColorEditorInfo(self):
		return {"editor": "colour"}

	def _setBackColor(self, value):
		if type(value) == str:
			try:
				value = self.getColorTupleFromName(value)
			except: pass
		self._pemObject.SetBackgroundColour(value)
		if self._pemObject == self:
			# Background color changes don't seem to result in
			# an automatic refresh.
			self.Refresh()


	def _getBorderStyle(self):
		if self.hasWindowStyleFlag(wx.RAISED_BORDER):
			return "Raised"
		elif self.hasWindowStyleFlag(wx.SUNKEN_BORDER):
			return "Sunken"
		elif self.hasWindowStyleFlag(wx.SIMPLE_BORDER):
			return "Simple"
		elif self.hasWindowStyleFlag(wx.DOUBLE_BORDER):
			return "Double"
		elif self.hasWindowStyleFlag(wx.STATIC_BORDER):
			return "Static"
		elif self.hasWindowStyleFlag(wx.NO_BORDER):
			return "None"
		else:
			return "Default"

	def _getBorderStyleEditorInfo(self):
		return {"editor": "list", "values": ["Default", "None", "Simple", "Sunken", 
						"Raised", "Double", "Static"]}

	def _setBorderStyle(self, style):
		self.delWindowStyleFlag(wx.NO_BORDER)
		self.delWindowStyleFlag(wx.SIMPLE_BORDER)
		self.delWindowStyleFlag(wx.SUNKEN_BORDER)
		self.delWindowStyleFlag(wx.RAISED_BORDER)
		self.delWindowStyleFlag(wx.DOUBLE_BORDER)
		self.delWindowStyleFlag(wx.STATIC_BORDER)

		style = str(style)

		if style == "None":
			self.addWindowStyleFlag(wx.NO_BORDER)
		elif style == "Simple":
			self.addWindowStyleFlag(wx.SIMPLE_BORDER)
		elif style == "Sunken":
			self.addWindowStyleFlag(wx.SUNKEN_BORDER)
		elif style == "Raised":
			self.addWindowStyleFlag(wx.RAISED_BORDER)
		elif style == "Double":
			self.addWindowStyleFlag(wx.DOUBLE_BORDER)
		elif style == "Static":
			self.addWindowStyleFlag(wx.STATIC_BORDER)
		elif style == "Default":
			pass
		else:
			raise ValueError, ("The only possible values are 'None', "
							"'Simple', 'Sunken', and 'Raised.'")
	
	
	def _getCaption(self):
		return self._pemObject.GetLabel()
	
	def _setCaption(self, caption):
		self._pemObject.SetLabel(str(caption))

		# Frames have a Title separate from Label, but I can't think
		# of a reason why that would be necessary... can you? 
		self._pemObject.SetTitle(str(caption))


	def _getChildren(self):
		children = []
		for child in self.GetChildren():
			if isinstance(child, dabo.common.dObject):
				children.append(child)
		return children
		
		
	def _getEnabled(self):
		return self._pemObject.IsEnabled()
	
	def _setEnabled(self, value):
		self._pemObject.Enable(value)


	def _getFont(self):
		return self._pemObject.GetFont()
	
	def _getFontEditorInfo(self):
		return {"editor": "font"}
	
	def _setFont(self, font):
		self._pemObject.SetFont(font)

	
	def _getFontBold(self):
		return self._pemObject.GetFont().GetWeight() == wx.BOLD
	
	def _setFontBold(self, fontBold):
		font = self._pemObject.GetFont()
		if fontBold:
			font.SetWeight(wx.BOLD)
		else:
			font.SetWeight(wx.LIGHT)    # wx.NORMAL doesn't seem to work...
		self._pemObject.SetFont(font)

	def _getFontDescription(self):
		f = self._pemObject.GetFont()
		ret = f.GetFaceName() + " " + str(f.GetPointSize())
		if f.GetWeight() == wx.BOLD:
			ret += " B"
		if f.GetStyle() == wx.ITALIC:
			ret += " I"
		return ret
	
	def _getFontInfo(self):
		return self._pemObject.GetFont().GetNativeFontInfoDesc()

		
	def _getFontItalic(self):
		return self._pemObject.Font.GetStyle() == wx.ITALIC
	
	def _setFontItalic(self, fontItalic):
		font = self._pemObject.Font
		if fontItalic:
			font.SetStyle(wx.ITALIC)
		else:
			font.SetStyle(wx.NORMAL)
		self._pemObject.Font = font

	
	def _getFontFace(self):
		return self._pemObject.Font.GetFaceName()
	def _setFontFace(self, val):
		f = self._pemObject.Font
		f.SetFaceName(val)
		self._pemObject.Font = f

	
	def _getFontSize(self):
		return self._pemObject.Font.GetPointSize()
	
	def _setFontSize(self, fontSize):
		font = self._pemObject.Font
		font.SetPointSize(int(fontSize))
		self._pemObject.Font = font

	
	def _getFontUnderline(self):
		return self._pemObject.Font.GetUnderlined()
	
	def _setFontUnderline(self, val):
		# underlining doesn't seem to be working...
		font = self._pemObject.Font
		font.SetUnderlined(bool(val))
		self._pemObject.Font = font


	def _getForeColor(self):
		return self._pemObject.GetForegroundColour()

	def _getForeColorEditorInfo(self):
		return {"editor": "colour"}

	def _setForeColor(self, value):
		if type(value) == str:
			try:
				value = self.getColorTupleFromName(value)
			except: pass
		self._pemObject.SetForegroundColour(value)

	
	def _getHeight(self):
		return self._pemObject.GetSize()[1]

	def _getHeightEditorInfo(self):
		return {"editor": "integer", "min": 0, "max": 8192}

	def _setHeight(self, height):
		newSize = self._pemObject.GetSize()[0], int(height)
		if isinstance(self, (wx.Frame, wx.Dialog) ):
			self._pemObject.SetSize(newSize)
		else:
			self._pemObject.SetBestFittingSize(newSize)


	def _getHelpContextText(self):
		return self._pemObject.GetHelpText()
	
	def _setHelpContextText(self, value):
		self._pemObject.SetHelpText(str(value))


	def _getLeft(self):
		return self._pemObject.GetPosition()[0]
	
	def _setLeft(self, left):
		self._pemObject.SetPosition((int(left), self._pemObject.Top))

		
	def _getMousePointer(self):
		return self._pemObject.GetCursor()
	
	def _setMousePointer(self, value):
		self._pemObject.SetCursor(value)


	def _getName(self):
		try:
			name = self._pemObject.GetName()
		except AttributeError:
			# Some objects that inherit from dPemMixin (dMenu*) don't have GetNam()
			# or SetName() methods.
			name = self._name
		self._name = name      # keeps name available even after C++ object is gone.
		return name
	
	def _setName(self, name, _userExplicit=True):
		parent = self._pemObject.GetParent()
		if parent:
			if not _userExplicit:
				# Dabo is setting the name implicitly, in which case we want to mangle
				# the name if necessary to make it unique (we don't want a NameError).
				i = 0
				while True:
					nameError = False
					if i == 0:
						candidate = name
					else:
						candidate = "%s%s" % (name, i)

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
				for window in parent.GetChildren():
					if str(window.GetName()) == str(name) and window != self:
						raise NameError, "Name '%s' is already in use." % name
				
		else:
			# Can't do the name check for siblings, so allow it for now.
			# This problem would only apply to top-level forms, so it really
			# wouldn't matter anyway in a practical sense.
			name = name

		try:
			self._pemObject.SetName(str(name))
		except AttributeError:
			# Some objects that inherit from dPemMixin do not implement SetName().
			pass
		self._name = self._pemObject.GetName()

	
	def _setNameBase(self, val):
		self._setName(val, False)
		
		
	def _getParent(self):
		return self._pemObject.GetParent()
	
	def _setParent(self, newParentObject):
		# Note that this isn't allowed in the property definition, however this
		# is how we'd do it *if* it were allowed <g>:
		self._pemObject.Reparent(newParentObject)

		
	def _getPosition(self):
		return self._pemObject.GetPosition()

	def _setPosition(self, position):
		self._pemObject.SetPosition(position)

	
	def _getSize(self): 
		return self._pemObject.GetSize()

	def _setSize(self, size):
		if isinstance(self, (wx.Frame, wx.Dialog) ):
			self._pemObject.SetSize(size)
		else:
			self._pemObject.SetBestFittingSize(size)

	
	def _getSizer(self):
		return self.GetSizer()
		
	def _setSizer(self, val):
		self.SetSizer(val)
			
		
	def _getToolTipText(self):
		t = self._pemObject.GetToolTip()
		if t:
			return t.GetTip()
		else:
			return ""

	def _getToolTipTextEditorInfo(self):
		return {"editor": "string", "len": 8192}

	def _setToolTipText(self, value):
		t = self._pemObject.GetToolTip()
		if t:
			t.SetTip(value)
		else:
			if value:
				t = wx.ToolTip(str(value))
				self._pemObject.SetToolTip(t)


	def _getTop(self):
		return self._pemObject.GetPosition()[1]
	
	def _setTop(self, top):
		self.SetPosition((self._pemObject.Left, int(top)))

	
	def _getVisible(self):
		return self._pemObject.IsShown()
	
	def _setVisible(self, value):
		self._pemObject.Show(bool(value))

		
	def _getWidth(self):
		return self._pemObject.GetSize()[0]

	def _getWidthEditorInfo(self):
		return {"editor": "integer", "min": 0, "max": 8192}

	def _setWidth(self, width):
		newSize = int(width), self._pemObject.GetSize()[1]
		if isinstance(self, (wx.Frame, wx.Dialog) ):
			self._pemObject.SetSize(newSize)
		else:
			self._pemObject.SetBestFittingSize(newSize)

	def _getWindowHandle(self):
		return self._pemObject.GetHandle()



	# Property definitions follow
	BackColor = property(_getBackColor, _setBackColor, None,
			_("Specifies the background color of the object. (tuple)"))

	BorderStyle = property(_getBorderStyle, _setBorderStyle, None,
			"Specifies the type of border for this window. (int). \n"
			"     None \n"
			"     Simple \n"
			"     Sunken \n"
			"     Raised")
	
	Caption = property(_getCaption, _setCaption, None, 
			"The caption of the object. (str)")

	Children = property(_getChildren, None, None, 
		_("Returns a list of object references to the children of this object."))
		
	Enabled = property(_getEnabled, _setEnabled, None,
			"Specifies whether the object (and its children) can get user input. (bool)")

	Font = property(_getFont, _setFont, None,
			"The font properties of the object. (obj)")
	
	FontBold = property(_getFontBold, _setFontBold, None,
			"Specifies if the font is bold-faced. (bool)")
	
	FontDescription = property(_getFontDescription, None, None, 
			"Human-readable description of the current font settings. (str)")
	
	FontFace = property(_getFontFace, _setFontFace, None,
			"Specifies the font face. (str)")
	
	FontInfo = property(_getFontInfo, None, None,
			"Specifies the platform-native font info string. Read-only. (str)")
	
	FontItalic = property(_getFontItalic, _setFontItalic, None,
			"Specifies whether font is italicized. (bool)")
	
	FontSize = property(_getFontSize, _setFontSize, None,
			"Specifies the point size of the font. (int)")
	
	FontUnderline = property(_getFontUnderline, _setFontUnderline, None,
			"Specifies whether text is underlined. (bool)")

	ForeColor = property(_getForeColor, _setForeColor, None,
			"Specifies the foreground color of the object. (tuple)")

	Height = property(_getHeight, _setHeight, None,
			"The height of the object. (int)")
	
	HelpContextText = property(_getHelpContextText, _setHelpContextText, None,
			"Specifies the context-sensitive help text associated with this window. (str)")
	
	Left = property(_getLeft, _setLeft, None,
			"The left position of the object. (int)")
	
	MousePointer = property(_getMousePointer, _setMousePointer, None,
			"Specifies the shape of the mouse pointer when it enters this window. (obj)")
	
 	Name = property(_getName, _setName, None, 
			"""Specifies the name of the object, which must be unique among siblings.
			
			If the specified name isn't unique, an exception will be raised. See also
			NameBase, which let's you set a base name and Dabo will automatically append
			integers to make it unique.
			""")
	
	NameBase = property(None, _setNameBase, None,
			"""Specifies the base name of the object.
			
			The base name specified will become the object's Name, unless another sibling
			already has that name, in which case Dabo will find the next unique name by
			adding integers to the end of the base name. For example, if your code says:
			
				self.NameBase = "txtAddress" 
				
			and there is already a sibling object with that name, your object will end up
			with Name = "txtAddress1".
			
			This property is write-only at runtime.
			""")
		
	Parent = property(_getParent, _setParent, None,	
			"The containing object. (obj)")

	Position = property(_getPosition, _setPosition, None, 
			"The (x,y) position of the object. (tuple)")

	Size = property(_getSize, _setSize, None,
			"The size of the object. (tuple)")

	Sizer = property(_getSizer, _setSizer, None, 
			"The sizer for the object.")
		
	ToolTipText = property(_getToolTipText, _setToolTipText, None,
			"Specifies the tooltip text associated with this window. (str)")

	Top = property(_getTop, _setTop, None, 
			"The top position of the object. (int)")
	
	Visible = property(_getVisible, _setVisible, None,
			"Specifies whether the object is visible at runtime. (bool)")                    

	Width = property(_getWidth, _setWidth, None,
			"The width of the object. (int)")
	
	WindowHandle = property(_getWindowHandle, None, None,
			"The platform-specific handle for the window. Read-only. (long)")




if __name__ == "__main__":
	o = dPemMixin()
	print o.BaseClass
	o.BaseClass = "dForm"
	print o.BaseClass
