""" dPemMixin.py: Provide common PEM functionality """
import dabo, dabo.common
from dabo.dLocalize import _

class dPemMixinBase(dabo.common.dObject):
	""" Provide Property/Event/Method interfaces for dForms and dControls.

	Subclasses can extend the property sheet by defining their own get/set
	functions along with their own property() statements.
	"""
	
	def __getattr__(self, att):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
	
	def _beforeInit(self):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
		
	def _afterInit(self):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
	
	def beforeInit(self, *args, **kwargs):
		""" Subclass hook.
		
		Called before the object is fully instantiated.
		"""
		pass
		

	def afterInit(self):
		""" Subclass hook.
		
		Called after the object's __init__ has run fully.

		Subclasses should place their __init__ code here in this hook,
		instead of overriding __init__ directly, to avoid conflicting
		with base Dabo behavior.
		"""
		pass
		

	def initProperties(self):
		""" Hook for subclasses.

		User code can set properties here, such as:
			self.Name = "MyTextBox"
			self.BackColor = (192,192,192)
		"""
		pass
		
		
	def initStyleProperties(self):
		""" Hook for subclasses.

		User code can set style properties here, such as:
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
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
		
		
	def getPropertyInfo(self, name):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
		
	
	def addObject(self, classRef, name, *args, **kwargs):
		""" Create an instance of classRef, and make it a child of self.
		
		Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
		

	def bindEvent(self, event, function, eventObject=None):
		""" Bind a Dabo event raised by eventObject (or self) to the given function.
		
		Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
		
	
	def unBindEvent(self, event, function, eventObject=None):
		""" Unbind a previously bound event/function.
		
		Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
		
		
	def raiseEvent(self, event):
		""" Raise the specified event.
		
		Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
		
			
	def getPropValDict(self, obj=None):
		""" Return a dictionary of property name/value pairs.
		"""
		if obj is None:
			obj = self
		propValDict = {}
		propList = obj.getPropertyList()
		for prop in propList:
			if prop == "Form":
				# This property is not used.
				continue
			propValDict[prop] = eval("obj.%s" % prop)
		return propValDict
	
	
	def applyPropValDict(self, obj=None, pvDict={}):
		""" Apply the passed dictionary of prop/val pairs to the passed object.
		"""
		if obj is None:
			obj=self
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
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
	
	def clone(self, obj, name=None):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		

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


	def _getBottom(self):
		return self.Top + self.Height
	def _setBottom(self, bottom):
		self.Top = int(bottom) - self.Height

	def _getRight(self):
		return self.Left + self.Width
	def _setRight(self, right):
		self.Left = int(right) - self.Width




	# Property definitions follow
	Form = property(_getForm, None, None,
					'Object reference to the dForm containing the object. (read only).')
	
	Bottom = property(_getBottom, _setBottom, None,
					'The position of the bottom part of the object. (int)')
	Right = property(_getRight, _setRight, None,
					'The position of the right part of the object. (int)')


if __name__ == "__main__":
	o = dPemMixin()
	print o.BaseClass
	o.BaseClass = "dForm"
	print o.BaseClass
