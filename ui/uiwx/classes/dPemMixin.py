""" dPemMixin.py: Provide common PEM functionality """
import wx, sys, types, dabo.common

class dPemMixin(dabo.common.dObject):
	""" Provide Property/Event/Method interfaces for dForms and dControls.

	Subclasses can extend the property sheet by defining their own get/set
	functions along with their own property() statements.
	"""
	def __getattr__(self, att):
		""" Try to resolve att to a child object reference.

		This allows accessing children with the style:
			self.mainPanel.txtName.Value = "test"
		"""
		try:
			ret = self.FindWindowByName(att)
		except TypeError:
			ret = None
		if not ret:
			raise AttributeError, "%s object has no attribute %s" % (
				self._name, att)
		else:
			return ret

	
	def _beforeInit(self, pre):
		self._name = '?'
		self._pemObject = pre
		self.initStyleProperties()
		self._pemObject = self
		
		# Call the subclass hook:
		self.beforeInit(pre)
		
		
	def beforeInit(self, preCreateObject):
		""" Called before the wx object is fully instantiated.

		Allows things like extra style flags to be set or XRC resources to
		be loaded. Subclasses can override this as necessary.
		"""
		pass
		

	def __init__(self, *args, **kwargs):
		if self.Position == (-1, -1):
			# The object was instantiated with a default position,
			# which ended up being (-1,-1). Change this to (0,0). 
			# This is completely moot when sizers are employed.
			self.Position = (0, 0)

		if self.Size == (-1, -1):
			# The object was instantiated with a default position,
			# which ended up being (-1,-1). Change this to (0,0). 
			# This is completely moot when sizers are employed.
			self.Size = (0, 0)

		if not wx.HelpProvider.Get():
			# The app hasn't set a help provider, and one is needed
			# to be able to save/restore help text.
			wx.HelpProvider.Set(wx.SimpleHelpProvider())


	def _afterInit(self):
		self.initProperties()
		self.initChildObjects()
		self.afterInit()
		

	def afterInit(self):
		""" Called after the wx object's __init__ has run fully.

		Subclasses should place their __init__ code here in this hook,
		instead of overriding __init__ directly.
		"""
		pass
		

	def initProperties(self):
		""" Hook for subclasses.

		Dabo Designer will set properties here, such as:
			self.Name = "MyTextBox"
			self.BackColor = (192,192,192)
		"""
		pass
		
		
	def initStyleProperties(self):
		""" Hook for subclasses.

		Dabo Designer will set style properties here, such as:
			self.BorderStyle = "Sunken"
			self.Alignment = "Center"
		"""
		pass

		
	def initChildObjects(self):
		""" Hook for subclasses.
		
		Dabo Designer will set its addObject code here, such as:
			self.addObject(dTextBox, 'txtLastName')
		"""
		pass
		

	def getAbsoluteName(self):
		""" Get self's fully-qualified name, such as 'dFormRecipes.dPageFrame.Page1.txtName'
		"""
		names = [self.Name, ]
		object = self
		while True:
			parent = object.GetParent()
			if parent:
				names.append(parent.GetName())
				object = parent
			else:
				break
		names.reverse()
		return '.'.join(names)
		
		
	def getPropertyInfo(self, name):
		d = dPemMixin.doDefault(name)   # the property helper does most of the work
		
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

	
	def escapeQt(self, s):
		sl = "\\"
		qt = "\'"
		return s.replace(sl, sl+sl).replace(qt, sl+qt)
	

	def getPropValDict(self, obj):
		propValDict = {}
		propList = obj.getPropertyList()
		for prop in propList:
			propValDict[prop] = eval("obj.%s" % prop)
		return propValDict
	
	
	def applyPropValDict(self, obj, pvDict):
		ignoreProps = ["BaseClass", "Bottom", "Class", "Font", "FontFace", "FontInfo", 
				"MousePointer", "Parent", "Right", "SuperClass", "WindowHandle"]
		propList = obj.getPropertyList()
		name = obj.Name
		for prop in propList:
			if prop in ignoreProps:
				continue
			try:
				sep = ""	# Empty String
				val = pvDict[prop]
				if type(val) in (types.UnicodeType, types.StringType):
					sep = "'"	# Single Quote
				try:
					exp = "obj.%s = %s" % (prop, sep+self.escapeQt(str(val))+sep)
					exec(exp)
				except:
					#pass
					print "Could not set property:", exp
			except:
				pass
		# Font assignment can be complicated during the iteration of properties,
		# so assign it explicitly here at the end.
		if pvDict.has_key("Font"):
			obj.Font = pvDict["Font"]
			
	
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
		

	# The following 3 flag functions are used in some of the property
	# get/set functions.
	def hasWindowStyleFlag(self, flag):
		""" Return whether or not the flag is set. (bool)
		"""
		return (self._pemObject.GetWindowStyleFlag() & flag) == flag

	def addWindowStyleFlag(self, flag):
		""" Add the flag to the window style.
		"""
		self._pemObject.SetWindowStyleFlag(self._pemObject.GetWindowStyleFlag() | flag)

	def delWindowStyleFlag(self, flag):
		""" Remove the flag from the window style.
		"""
		self._pemObject.SetWindowStyleFlag(self._pemObject.GetWindowStyleFlag() & (~flag))


	# Scroll to the bottom to see the property definitions.

	# Property get/set/delete methods follow.

	def _getFont(self):
		return self._pemObject.GetFont()
	
	def _getFontEditorInfo(self):
		return {'editor': 'font'}
	
	def _setFont(self, font):
		self._pemObject.SetFont(font)

		
	def _getFontInfo(self):
		return self._pemObject.GetFont().GetNativeFontInfoDesc()

	def _getFontBold(self):
		return self._pemObject.GetFont().GetWeight() == wx.BOLD
	def _setFontBold(self, fontBold):
		font = self._pemObject.GetFont()
		if fontBold:
			font.SetWeight(wx.BOLD)
		else:
			font.SetWeight(wx.LIGHT)    # wx.NORMAL doesn't seem to work...
		self._pemObject.SetFont(font)

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


	def _getTop(self):
		return self._pemObject.GetPosition()[1]
	def _setTop(self, top):
		self.SetPosition((self._pemObject.Left, int(top)))

	def _getLeft(self):
		return self._pemObject.GetPosition()[0]
	def _setLeft(self, left):
		self._pemObject.SetPosition((int(left), self._pemObject.Top))

	def _getPosition(self):
		return self._pemObject.GetPosition()

	def _setPosition(self, position):
		self._pemObject.SetPosition(position)

	def _getBottom(self):
		return self._pemObject.Top + self._pemObject.Height
	def _setBottom(self, bottom):
		self._pemObject.Top = int(bottom) - self._pemObject.Height

	def _getRight(self):
		return self._pemObject.Left + self._pemObject.Width
	def _setRight(self, right):
		self._pemObject.Left = int(right) - self._pemObject.Width


	def _getWidth(self):
		return self._pemObject.GetSize()[0]

	def _getWidthEditorInfo(self):
		return {'editor': 'integer', 'min': 0, 'max': 8192}

	def _setWidth(self, width):
		self.SetSize((int(width), self._pemObject.Height))


	def _getHeight(self):
		return self._pemObject.GetSize()[1]

	def _getHeightEditorInfo(self):
		return {'editor': 'integer', 'min': 0, 'max': 8192}

	def _setHeight(self, height):
		self.SetSize((self._pemObject.Width, int(height)))


	def _getSize(self): 
		return self._pemObject.GetSize()

	def _setSize(self, size):
		self._pemObject.SetSize(size)


	def _getName(self):
		name = self._pemObject.GetName()
		self._name = name      # keeps name available even after C++ object is gone.
		return name
	
	def _setName(self, name):
		parent = self._pemObject.GetParent()
		if parent:
			if not self.dApp or self.dApp.AutoNegotiateUniqueNames:
				i = 0
				while True:
					nameError = False
					if i == 0:
						candidate = name
					else:
						candidate = '%s%s' % (name, i)

					for window in self._pemObject.GetParent().GetChildren():
						if window.GetName() == candidate and window != self:
							nameError = True
							break
					if nameError:
						i += 1
					else:
						name = candidate
						break
			else:
				raise NameError, "A unique object name is required."
				
		else:
			# Can't do the name check for siblings, so allow it for now.
			# This problem would only apply to top-level forms, so it really
			# wouldn't matter anyway in a practical sense.
			pass					

		self._pemObject.SetName(str(name))
		self._name = self._pemObject.GetName()

	def _getCaption(self):
		return self._pemObject.GetLabel()
	def _setCaption(self, caption):
		self._pemObject.SetLabel(str(caption))

		# Frames have a Title separate from Label, but I can't think
		# of a reason why that would be necessary... can you? 
		self._pemObject.SetTitle(str(caption))


	def _getEnabled(self):
		return self._pemObject.IsEnabled()
	def _setEnabled(self, value):
		self._pemObject.Enable(value)


	def _getBackColor(self):
		return self._pemObject.GetBackgroundColour()

	def _getBackColorEditorInfo(self):
		return {'editor': 'colour'}

	def _setBackColor(self, value):
		self._pemObject.SetBackgroundColour(value)
		if self._pemObject == self:
			# Background color changes don't seem to result in
			# an automatic refresh.
			self.Refresh()


	def _getForeColor(self):
		return self._pemObject.GetForegroundColour()

	def _getForeColorEditorInfo(self):
		return {'editor': 'colour'}

	def _setForeColor(self, value):
		self._pemObject.SetForegroundColour(value)


	def _getMousePointer(self):
		return self._pemObject.GetCursor()
	def _setMousePointer(self, value):
		self._pemObject.SetCursor(value)


	def _getToolTipText(self):
		t = self._pemObject.GetToolTip()
		if t:
			return t.GetTip()
		else:
			return ''

	def _getToolTipTextEditorInfo(self):
		return {'editor': 'string', 'len': 8192}

	def _setToolTipText(self, value):
		t = self._pemObject.GetToolTip()
		if t:
			t.SetTip(value)
		else:
			if value:
				t = wx.ToolTip(str(value))
				self._pemObject.SetToolTip(t)


	def _getHelpContextText(self):
		return self._pemObject.GetHelpText()
	def _setHelpContextText(self, value):
		self._pemObject.SetHelpText(str(value))


	def _getVisible(self):
		return self._pemObject.IsShown()
	def _setVisible(self, value):
		self._pemObject.Show(bool(value))

	def _getParent(self):
		return self._pemObject.GetParent()
	def _setParent(self, newParentObject):
		# Note that this isn't allowed in the property definition, however this
		# is how we'd do it *if* it were allowed <g>:
		self._pemObject.Reparent(newParentObject)

	def _getWindowHandle(self):
		return self._pemObject.GetHandle()

	def _getBorderStyle(self):
		if self.hasWindowStyleFlag(wx.RAISED_BORDER):
			return 'Raised'
		elif self.hasWindowStyleFlag(wx.SUNKEN_BORDER):
			return 'Sunken'
		elif self.hasWindowStyleFlag(wx.SIMPLE_BORDER):
			return 'Simple'
		elif self.hasWindowStyleFlag(wx.DOUBLE_BORDER):
			return 'Double'
		elif self.hasWindowStyleFlag(wx.STATIC_BORDER):
			return 'Static'
		elif self.hasWindowStyleFlag(wx.NO_BORDER):
			return 'None'
		else:
			return 'Default'

	def _getBorderStyleEditorInfo(self):
		return {'editor': 'list', 'values': ['Default', 'None', 'Simple', 'Sunken', 
						'Raised', 'Double', 'Static']}

	def _setBorderStyle(self, style):
		self.delWindowStyleFlag(wx.NO_BORDER)
		self.delWindowStyleFlag(wx.SIMPLE_BORDER)
		self.delWindowStyleFlag(wx.SUNKEN_BORDER)
		self.delWindowStyleFlag(wx.RAISED_BORDER)
		self.delWindowStyleFlag(wx.DOUBLE_BORDER)
		self.delWindowStyleFlag(wx.STATIC_BORDER)

		style = str(style)

		if style == 'None':
			self.addWindowStyleFlag(wx.NO_BORDER)
		elif style == 'Simple':
			self.addWindowStyleFlag(wx.SIMPLE_BORDER)
		elif style == 'Sunken':
			self.addWindowStyleFlag(wx.SUNKEN_BORDER)
		elif style == 'Raised':
			self.addWindowStyleFlag(wx.RAISED_BORDER)
		elif style == 'Double':
			self.addWindowStyleFlag(wx.DOUBLE_BORDER)
		elif style == 'Static':
			self.addWindowStyleFlag(wx.STATIC_BORDER)
		elif style == 'Default':
			pass
		else:
			raise ValueError, ("The only possible values are 'None', "
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
	Bottom = property(_getBottom, _setBottom, None,
					'The position of the bottom part of the object. (int)')
	Right = property(_getRight, _setRight, None,
					'The position of the right part of the object. (int)')
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
