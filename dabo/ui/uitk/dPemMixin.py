# -*- coding: utf-8 -*-
""" dPemMixin.py: Provide common PEM functionality """
import sys, types
import dabo
from dabo.dLocalize import _
import dabo.ui.dPemMixinBase
import dabo.dEvents as dEvents
from dabo.lib.utils import ustr



class dPemMixin(dabo.ui.dPemMixinBase.dPemMixinBase):
	""" Provide Property/Event/Method interfaces for dForms and dControls.

	Subclasses can extend the property sheet by defining their own get/set
	functions along with their own property() statements.
	"""
	def __init__(self, preClass, parent=None, properties=None, *args, **kwargs):
		# This is the major, common constructor code for all the dabo/ui/uitk
		# classes. The __init__'s of each class are just thin wrappers to this
		# code.

		# self.properties can be set in the userland beforeInit() hook.
		self._properties = {}

		# This will implicitly call the following user hooks:
		#    beforeInit()
		self._beforeInit()

		# The keyword properties can come from either, both, or none of:
		#    + self.properties (set by user code in self.beforeInit())
		#    + the properties dict
		#    + the kwargs dict
		# Get them sanitized into one dict:
		if properties is not None:
			# Override the class values
			for k,v in properties.items():
				self._properties[k] = v
		properties = self._extractKeywordProperties(kwargs, self._properties)

		# If a Name isn't given, a default name will be used, and it'll
		# autonegotiate by adding an integer until it is a unique name.
		# If a Name is given explicitly, a NameError will be raised if
		# the given Name isn't unique among siblings:
		name, _explicitName = self._processName(kwargs, self.__class__.__name__)

		# Do the init:
		preClass.__init__(self, *args, **kwargs)

		self._initName(name, _explicitName=_explicitName)

		self._afterInit()
		print properties
		try:
			self.setProperties(properties)
		except:
			pass


	def __getattr__(self, att):
		""" Try to resolve att to a child object reference.

		This allows accessing children with the style:
			self.mainPanel.txtName.Value = "test"
		"""

		children = self.winfo_children()

		ret = None
		for child in children:
			if child.winfo_name() == att:
				ret = child
				exit

		if not ret:
			raise AttributeError("%s object has no attribute %s" % (
				self._name, att))
		else:
			return ret


	def _beforeInit(self):
		self._name = '?'

		# Call the subclass hook:
		self.beforeInit()


	def _afterInit(self):
		self.debug = False

		self.initProperties()
		self.afterInit()

		self._mouseLeftDown, self._mouseRightDown = False, False

		self._initEvents()
		self.initEvents()

		self.raiseEvent(dEvents.Create)


	def _initEvents(self):
		# Bind tk events to handlers that re-raise the Dabo events:

		self.bind("<Destroy>", self._onTkDestroy)
		self.bind("<FocusIn>", self._onTkGotFocus)
		self.bind("<FocusOut>", self._onTkLostFocus)

		# Activate and Deactivate don't mean what we expect in Tk...
# 		self.bind("<Activate>", self._onTkActivate)
# 		self.bind("<Deactivate>", self._onTkDeactivate)

		self.bind("<KeyPress>", self._onTkKeyDown)
		self.bind("<KeyRelease>", self._onTkKeyUp)

		self.bind("<Enter>", self._onTkMouseEnter)
		self.bind("<Leave>", self._onTkMouseLeave)
		self.bind("<Button-1>", self._onTkMouseLeftDown)
		self.bind("<ButtonRelease-1>", self._onTkMouseLeftUp)
		self.bind("<Button-3>", self._onTkMouseRightDown)
		self.bind("<ButtonRelease-3>", self._onTkMouseRightUp)



	def _onTkDestroy(self, event):
		return self.raiseEvent(dEvents.Destroy, event)

	def _onTkGotFocus(self, event):
		return self.raiseEvent(dEvents.GotFocus, event)

	def _onTkLostFocus(self, event):
		return self.raiseEvent(dEvents.LostFocus, event)

	def _onTkActivate(self, event):
		return self.raiseEvent(dEvents.Activate, event)

	def _onTkDeactivate(self, event):
		return self.raiseEvent(dEvents.Deactivate, event)

	def _onTkKeyDown(self, event):
		r = self.raiseEvent(dEvents.KeyDown, event)
		if len(event.char) > 0:
			self.raiseEvent(dEvents.KeyChar, event)
		return r

	def _onTkKeyUp(self, event):
		return self.raiseEvent(dEvents.KeyUp, event)

	def _onTkMouseEnter(self, event):
		return self.raiseEvent(dEvents.MouseEnter, event)

	def _onTkMouseLeave(self, event):
		self._mouseLeftDown, self._mouseRightDown = False, False
		return self.raiseEvent(dEvents.MouseLeave, event)

	def _onTkMouseLeftDown(self, event):
		self._mouseLeftDown = True
		return self.raiseEvent(dEvents.MouseLeftDown, event)

	def _onTkMouseLeftUp(self, event):
		r = self.raiseEvent(dEvents.MouseLeftUp, event)
		if self._mouseLeftDown:
			# mouse went down and up in this control: send a click:
			self.raiseEvent(dEvents.MouseLeftClick, event)
			self._mouseLeftDown = False
		return r

	def _onTkMouseRightDown(self, event):
		self._mouseRightDown = True
		return self.raiseEvent(dEvents.MouseRightDown, event)

	def _onTkMouseRightUp(self, event):
		r = self.raiseEvent(dEvents.MouseRightUp, event)
		if self._mouseRightDown:
			# mouse went down and up in this control: send a click:
			self.raiseEvent(dEvents.MouseRightClick, event)
			self._mouseLeftDown = False
		return r


	def raiseEvent(self, eventClass, nativeEvent=None, *args, **kwargs):
		# Call the Dabo-native raiseEvent(), passing along the Tkinter after_idle
		# function, so that the Dabo events can be processed at next idle.
		super(dPemMixin, self).raiseEvent(eventClass, nativeEvent, callAfterFunc=self.after_idle,
				*args, **kwargs)


	def getPropertyInfo(self, name):
		d = super(dPemMixin, self).getPropertyInfo(name)   # the property helper does most of the work

		# Hide some wx-specific props in the designer:
		d['showInDesigner'] = not name in ('Size', 'Position', 'WindowHandle', 'TypeID')

		# Some wx-specific props need to be initialized early. Let the designer know:
		d['preInitProperty'] = name in ('Alignment', 'BorderStyle', 'PasswordEntry',
				'Orientation', 'ShowLabels', 'TabPosition')

		return d


	def addObject(self, classRef, name, *args, **kwargs):
		""" Instantiate object as a child of self.

		The class reference must be a Dabo object (must inherit dPemMixin).

		The name parameter will be used on the resulting instance, and additional
		arguments received will be passed on to the constructor of the object.
		"""
		object = classRef(self, name=name, *args, **kwargs)
		return object


	def reCreate(self, child=None):
		""" Recreate self.
		"""
		if child:
			propValDict = self.getPropValDict(child)
			style = child.GetWindowStyle()
			classRef = child.__class__
			name = child.Name
			child.Destroy()
			newObj = self.addObject(classRef, name, style=style)
			self.applyPropValDict(newObj, propValDict)
			return newObj
		else:
			return self.Parent.reCreate(self)


	def clone(self, obj, name=None):
		""" Create another object just like the passed object. It assumes that the
		calling object will be the container of the newly created object.
		"""
		propValDict = self.getPropValDict(obj)
		if name is None:
			name = obj.Name + "1"
		newObj = self.addObject(obj.__class__,
				name, style=obj.GetWindowStyle() )
		self.applyPropValDict(newObj, propValDict)
		return newObj


	# Scroll to the bottom to see the property definitions.

	# Property get/set/delete methods follow.

	def _getGeometryTuple(self):
		""" Convert Tkinter's 'widthXheight+left+top' format into a more usable
		set of 2-tuples. The first tuple is (width,height) and the second is
		(left,top). This is used by the various property getters/setters for
		left, top, height, width.
		"""
		# wm_geometry() for forms; winfo_geometry() for controls:
		try:
			g = self.wm_geometry()
		except AttributeError:
			g = self.winfo_geometry()
		size = tuple([int(k) for k in (g[0:g.find('+')].split('x'))])
		pos = tuple([int(k) for k in (g[g.find('+')+1:].split('+'))])
		return (size, pos)

	def _setGeometryTuple(self, geometryTuple):
		""" Given a geometry tuple, convert and send to Tkinter to be applied.
		"""
		size = geometryTuple[0]
		pos = geometryTuple[1]
		try:
			self.wm_geometry("%sx%s+%s+%s" % (size[0], size[1], pos[0], pos[1]))
		except AttributeError:
			self.width, self.height = size[0], size[1]
			#self.winfo_geometry("%sx%s+%s+%s" % (size[0], size[1], pos[0], pos[1]))



	def _getFont(self):
		return "Not implemented yet."

	def _getFontEditorInfo(self):
		return {'editor': 'font'}

	def _setFont(self, font):
		dabo.log.error("_setFont not implemented yet.")


	def _getFontInfo(self):
		return "Not implemented yet."

	def _getFontBold(self):
		return "Not implemented yet."
	def _setFontBold(self, fontBold):
		dabo.log.error("_setFontBold not implemented yet.")

	def _getFontItalic(self):
		return "Not implemented yet."
	def _setFontItalic(self, fontItalic):
		dabo.log.error("_setFontItalic not implemented yet.")

	def _getFontFace(self):
		return "Not implemented yet."

	def _getFontSize(self):
		return "Not implemented yet."
	def _setFontSize(self, fontSize):
		dabo.log.error("_setFontSize not implemented yet.")

	def _getFontUnderline(self):
		return "Not implemented yet."
	def _setFontUnderline(self, val):
		dabo.log.error("_setFontUnderline not implemented yet.")


	def _getTop(self):
		return self._getGeometryTuple()[1][1]
	def _setTop(self, top):
		size = self._getGeometryTuple()[0]
		pos = list(self._getGeometryTuple()[1])
		pos[1] = top
		pos = tuple(pos)
		self._setGeometryTuple((size, pos))

	def _getLeft(self):
		return self._getGeometryTuple()[1][0]
	def _setLeft(self, left):
		size = self._getGeometryTuple()[0]
		pos = list(self._getGeometryTuple()[1])
		pos[0] = left
		pos = tuple(pos)
		self._setGeometryTuple((size, pos))

	def _getPosition(self):
		return self._getGeometryTuple()[1]

	def _setPosition(self, position):
		size = self._getGeometryTuple()[0]
		pos = tuple(position)
		self._setGeometryTuple((size, pos))


	def _getWidth(self):
		return self._getGeometryTuple()[0][0]

	def _getWidthEditorInfo(self):
		return {'editor': 'integer', 'min': 0, 'max': 8192}

	def _setWidth(self, width):
		pos = self._getGeometryTuple()[1]
		size = list(self._getGeometryTuple()[0])
		size[0] = width
		size = tuple(size)
		self._setGeometryTuple((size, pos))


	def _getHeight(self):
		return self._getGeometryTuple()[0][1]

	def _getHeightEditorInfo(self):
		return {'editor': 'integer', 'min': 0, 'max': 8192}

	def _setHeight(self, height):
		pos = self._getGeometryTuple()[1]
		size = list(self._getGeometryTuple()[0])
		size[1] = height
		size = tuple(size)
		self._setGeometryTuple((size, pos))


	def _getSize(self):
		return self._getGeometryTuple()[0]

	def _setSize(self, size):
		pos = self._getGeometryTuple()[1]
		size = tuple(size)
		self._setGeometryTuple((size, pos))

	def _getName(self):
		name = self.winfo_name()
		self._name = name
		return name

	def _setName(self, val, _userExplicit=False):
		# Can't set tk name after initialized. However, we should try to implement
		# our own Dabo name which we can refer to and set/reset as we please.
		self._properties["name"] = val
		# Also, see ui/uiwx/dPemMixin._setName(), where we enforce a unique name
		# among siblings. That code should be refactored into dPemMixinBase...

	def _getCaption(self):
		# For forms: wm_title(), for controls: configure("text")
		try:
			return self.wm_title()
		except AttributeError:
			return self.cget("text")

	def _setCaption(self, caption):
		try:
			self.wm_title(ustr(caption))
		except AttributeError:
			self.configure(text=ustr(caption))

	def _getEnabled(self):
		return self.IsEnabled()
	def _setEnabled(self, value):
		self.Enable(value)


	def _getBackColor(self):
		return self.GetBackgroundColour()

	def _getBackColorEditorInfo(self):
		return {'editor': 'colour'}

	def _setBackColor(self, value):
		self.SetBackgroundColour(value)
		if self == self:
			# Background color changes don't seem to result in
			# an automatic refresh.
			self.Refresh()


	def _getForeColor(self):
		return self.GetForegroundColour()

	def _getForeColorEditorInfo(self):
		return {'editor': 'colour'}

	def _setForeColor(self, value):
		self.SetForegroundColour(value)


	def _getMousePointer(self):
		return self.GetCursor()
	def _setMousePointer(self, value):
		self.SetCursor(value)


	def _getToolTipText(self):
		t = self.GetToolTip()
		if t:
			return t.GetTip()
		else:
			return ''

	def _getToolTipTextEditorInfo(self):
		return {'editor': 'string', 'len': 8192}

	def _setToolTipText(self, value):
		t = self.GetToolTip()
		if t:
			t.SetTip(value)
		else:
			if value:
				t = wx.ToolTip(ustr(value))
				self.SetToolTip(t)


	def _getHelpContextText(self):
		return self.GetHelpText()
	def _setHelpContextText(self, value):
		self.SetHelpText(ustr(value))


	def _getVisible(self):
		return self.IsShown()
	def _setVisible(self, value):
		self.Show(bool(value))

	def _getParent(self):
		try:
			parent = self.nametowidget(self.winfo_parent())
		except:
			parent = None
		if isinstance(parent, dPemMixin):
			return parent
		else:
			return None

	def _setParent(self, obj):
		return None

	def _getWindowHandle(self):
		return self.GetHandle()

	def _getBorderStyle(self):
		if self._hasWindowStyleFlag(wx.RAISED_BORDER):
			return 'Raised'
		elif self._hasWindowStyleFlag(wx.SUNKEN_BORDER):
			return 'Sunken'
		elif self._hasWindowStyleFlag(wx.SIMPLE_BORDER):
			return 'Simple'
		elif self._hasWindowStyleFlag(wx.DOUBLE_BORDER):
			return 'Double'
		elif self._hasWindowStyleFlag(wx.STATIC_BORDER):
			return 'Static'
		elif self._hasWindowStyleFlag(wx.NO_BORDER):
			return 'None'
		else:
			return 'Default'

	def _getBorderStyleEditorInfo(self):
		return {'editor': 'list', 'values': ['Default', 'None', 'Simple', 'Sunken',
						'Raised', 'Double', 'Static']}

	def _setBorderStyle(self, style):
		self._delWindowStyleFlag(wx.NO_BORDER)
		self._delWindowStyleFlag(wx.SIMPLE_BORDER)
		self._delWindowStyleFlag(wx.SUNKEN_BORDER)
		self._delWindowStyleFlag(wx.RAISED_BORDER)
		self._delWindowStyleFlag(wx.DOUBLE_BORDER)
		self._delWindowStyleFlag(wx.STATIC_BORDER)

		style = ustr(style)

		if style == 'None':
			self._addWindowStyleFlag(wx.NO_BORDER)
		elif style == 'Simple':
			self._addWindowStyleFlag(wx.SIMPLE_BORDER)
		elif style == 'Sunken':
			self._addWindowStyleFlag(wx.SUNKEN_BORDER)
		elif style == 'Raised':
			self._addWindowStyleFlag(wx.RAISED_BORDER)
		elif style == 'Double':
			self._addWindowStyleFlag(wx.DOUBLE_BORDER)
		elif style == 'Static':
			self._addWindowStyleFlag(wx.STATIC_BORDER)
		elif style == 'Default':
			pass
		else:
			raise ValueError("The only possible values are 'None', "
							"'Simple', 'Sunken', and 'Raised.'")


	# Property definitions follow

	WindowHandle = property(_getWindowHandle, None, None,
			'The platform-specific handle for the window. Read-only. (long)')

	Font = property(_getFont, _setFont, None,
			'The font properties of the object. (obj)')
	FontInfo = property(_getFontInfo, None, None,
			'Specifies the platform-native font info string. Read-only. (str)')
	FontBold = property(_getFontBold, _setFontBold, None,
			'Specifies if the font is bold-faced. (bool)')
	FontItalic = property(_getFontItalic, _setFontItalic, None,
			'Specifies whether font is italicized. (bool)')
	FontFace = property(_getFontFace, None, None,
			'Specifies the font face. (str)')
	FontSize = property(_getFontSize, _setFontSize, None,
			'Specifies the point size of the font. (int)')
	FontUnderline = property(_getFontUnderline, _setFontUnderline, None,
			'Specifies whether text is underlined. (bool)')

	Top = property(_getTop, _setTop, None,
			'The top position of the object. (int)')
	Left = property(_getLeft, _setLeft, None,
			'The left position of the object. (int)')
	Position = property(_getPosition, _setPosition, None,
			'The (x,y) position of the object. (tuple)')

	Width = property(_getWidth, _setWidth, None,
			'The width of the object. (int)')
	Height = property(_getHeight, _setHeight, None,
			'The height of the object. (int)')
	Size = property(_getSize, _setSize, None,
			'The size of the object. (tuple)')


	Caption = property(_getCaption, _setCaption, None,
			'The caption of the object. (str)')

	Enabled = property(_getEnabled, _setEnabled, None,
			'Specifies whether the object (and its children) can get user input. (bool)')

	Visible = property(_getVisible, _setVisible, None,
			'Specifies whether the object is visible at runtime. (bool)')


	BackColor = property(_getBackColor, _setBackColor, None,
			'Specifies the background color of the object. (tuple)')

	ForeColor = property(_getForeColor, _setForeColor, None,
			'Specifies the foreground color of the object. (tuple)')

	MousePointer = property(_getMousePointer, _setMousePointer, None,
			'Specifies the shape of the mouse pointer when it enters this window. (obj)')

	Name = property(_getName, _setName, None,
			'The name of the object. (str)')

	Parent = property(_getParent, _setParent, None,
			'The containing object. (obj)')

	ToolTipText = property(_getToolTipText, _setToolTipText, None,
			'Specifies the tooltip text associated with this window. (str)')

	HelpContextText = property(_getHelpContextText, _setHelpContextText, None,
			'Specifies the context-sensitive help text associated with this window. (str)')

	BorderStyle = property(_getBorderStyle, _setBorderStyle, None,
			'Specifies the type of border for this window. (int). \n'
			'     None \n'
			'     Simple \n'
			'     Sunken \n'
			'     Raised')


if __name__ == "__main__":
	o = dPemMixin()
	print o.BaseClass
	o.BaseClass = "dForm"
	print o.BaseClass
