""" dPemMixin.py: Provide common PEM functionality """
import sys, types
import dabo, dabo.common
from dabo.dLocalize import _

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
		
		# First, try to delegate to self._tkObject:
# 		try:
# 			return eval("self._tkObject.%s" % att)
# 		except AttributeError:
# 			pass
		
		children = self.winfo_children()

		print self, self.winfo_name(), children, att
				
		ret = None
		for child in children:
			if child.winfo_name() == att:
				ret = child
				exit
				
		if not ret:
			raise AttributeError, "%s object has no attribute %s" % (
				self._name, att)
		else:
			return ret

	
	def _beforeInit(self):
		self._name = '?'
		self.initStyleProperties()
		
		# Call the subclass hook:
		self.beforeInit()
		
		
	def beforeInit(self):
		""" Called before the object is fully instantiated.
		"""
		pass
		

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
			parent = object.nametowidget(object.winfo_parent())
			if parent:
				names.append(parent.winfo_name)
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

	
	def getPropValDict(self, obj):
		propValDict = {}
		propList = obj.getPropertyList()
		for prop in propList:
			if prop == "Form":
				# This property is not used.
				continue
			propValDict[prop] = eval("obj.%s" % prop)
		return propValDict
	
	
	def applyPropValDict(self, obj, pvDict):
		ignoreProps = ["Application", "BaseClass", "Bottom", "Class", "Font", 
				"FontFace", "FontInfo", "Form", "MousePointer", "Parent", 
				"Right", "SuperClass", "WindowHandle"]
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
					dabo.errorLog.write(_("Could not set property: %s"), exp)
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
		

	# Scroll to the bottom to see the property definitions.

	# Property get/set/delete methods follow.

	def _getForm(self):
		""" Return a reference to the containing Form. 
		"""
		try:
			return self._cachedForm
		except AttributeError:
			import dabo.ui
			obj, frm = self, None
			while obj:
				parent = obj.Parent
				if isinstance(parent, dabo.ui.dForm):
					frm = parent
					break
				else:
					obj = parent
			if frm:
				self._cachedForm = frm   # Cache for next time
			return frm


	def _getFont(self):
		return self.GetFont()
	
	def _getFontEditorInfo(self):
		return {'editor': 'font'}
	
	def _setFont(self, font):
		self.SetFont(font)

		
	def _getFontInfo(self):
		return self.GetFont().GetNativeFontInfoDesc()

	def _getFontBold(self):
		return self.GetFont().GetWeight() == wx.BOLD
	def _setFontBold(self, fontBold):
		font = self.GetFont()
		if fontBold:
			font.SetWeight(wx.BOLD)
		else:
			font.SetWeight(wx.LIGHT)    # wx.NORMAL doesn't seem to work...
		self.SetFont(font)

	def _getFontItalic(self):
		return self.Font.GetStyle() == wx.ITALIC
	def _setFontItalic(self, fontItalic):
		font = self.Font
		if fontItalic:
			font.SetStyle(wx.ITALIC)
		else:
			font.SetStyle(wx.NORMAL)
		self.Font = font

	def _getFontFace(self):
		return self.Font.GetFaceName()

	def _getFontSize(self):
		return self.Font.GetPointSize()
	def _setFontSize(self, fontSize):
		font = self.Font
		font.SetPointSize(int(fontSize))
		self.Font = font

	def _getFontUnderline(self):
		return self.Font.GetUnderlined()
	def _setFontUnderline(self, val):
		# underlining doesn't seem to be working...
		font = self.Font
		font.SetUnderlined(bool(val))
		self.Font = font


	def _getTop(self):
		return self.GetPosition()[1]
	def _setTop(self, top):
		self.SetPosition((self.Left, int(top)))

	def _getLeft(self):
		return self.GetPosition()[0]
	def _setLeft(self, left):
		self.SetPosition((int(left), self.Top))

	def _getPosition(self):
		return self.GetPosition()

	def _setPosition(self, position):
		self.SetPosition(position)

	def _getBottom(self):
		return self.Top + self.Height
	def _setBottom(self, bottom):
		self.Top = int(bottom) - self.Height

	def _getRight(self):
		return self.Left + self.Width
	def _setRight(self, right):
		self.Left = int(right) - self.Width


	def _getWidth(self):
		return self.GetSize()[0]

	def _getWidthEditorInfo(self):
		return {'editor': 'integer', 'min': 0, 'max': 8192}

	def _setWidth(self, width):
		self.SetSize((int(width), self.GetSize()[1]))
		self.SetMinSize(self.SetSize())


	def _getHeight(self):
		return self.GetSize()[1]

	def _getHeightEditorInfo(self):
		return {'editor': 'integer', 'min': 0, 'max': 8192}

	def _setHeight(self, height):
		self.SetSize((self.GetSize()[0], int(height)))
		self.SetMinSize(self.GetSize())


	def _getSize(self): 
		return self.GetSize()

	def _setSize(self, size):
		self.SetSize(size)
		self.SetMinSize(size)

	def _getName(self):
		name = self.winfo_name()
		self._name = name      # keeps name available even after C++ object is gone.
		return name
	
	def _setName(self, name):
		parent = self.GetParent()
		if parent:
			if not self.Application or self.Application.AutoNegotiateUniqueNames:
				i = 0
				while True:
					nameError = False
					if i == 0:
						candidate = name
					else:
						candidate = '%s%s' % (name, i)

					for window in self.GetParent().GetChildren():
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

		self.SetName(str(name))
		self._name = self.GetName()

	def _getCaption(self):
		return self.wm_title()
	def _setCaption(self, caption):
		self.wm_title(str(caption))

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
				t = wx.ToolTip(str(value))
				self.SetToolTip(t)


	def _getHelpContextText(self):
		return self.GetHelpText()
	def _setHelpContextText(self, value):
		self.SetHelpText(str(value))


	def _getVisible(self):
		return self.IsShown()
	def _setVisible(self, value):
		self.Show(bool(value))

	def _getParent(self):
		parent = self.nametowidget(self.winfo_parent())
		if isinstance(parent, dPemMixin):
			return parent
		else:
			return None
		
	def _setParent(self, obj):
		return None

	def _getWindowHandle(self):
		return self.GetHandle()

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
	Form = property(_getForm, None, None,
					'Object reference to the dForm containing the object. (read only).')
	
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
