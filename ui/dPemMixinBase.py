""" dPemMixin.py: Provide common PEM functionality """
import dabo, dabo.common
import types
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

		
	def initEvents(self):
		""" Hook for subclasses.
		
		User code can do custom event binding here, such as:
			self.bindEvent(dEvents.GotFocus, self.customGotFocusHandler)
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
		

	def getPropertyInfo(self, name):
		""" Abstract method: subclasses MUST override for UI-specifics.
		"""
		return super(dPemMixinBase, self).getPropertyInfo(name)
		
	
	def addObject(self, classRef, name=None, *args, **kwargs):
		""" Create an instance of classRef, and make it a child of self.
		
		Abstract method: subclasses MUST override for UI-specifics.
		"""
		pass
		

	def getProperties(self, propertySequence=(), *propertyArguments):
		""" Returns a dictionary of property name/value pairs.
		
		If a sequence of properties is passed, just those property values
		will be returned. Otherwise, all property values will be returned.
		The sequence of properties can be a list, tuple, or plain string
		positional arguments. For instance, all of the following are
		equivilent:
			
			print self.getProperties("Caption", "FontInfo", "Form")
			print self.getProperties(["Caption", "FontInfo", "Form"])
			t = ("Caption", "FontInfo", "Form")
			print self.getProperties(t)
			print self.getProperties(*t)
		"""
		propDict = {}
		
		def _fillPropDict(_propSequence):
			for property in _propSequence:
				getter = eval("self.__class__.%s.fget" % property)
				if getter is not None:
					propDict[property] = getter(self)
				else:
					# not sure what to do here
					dabo.infoLog.write("Property '%s' is not readable." % property)
		if type(propertySequence) in (list, tuple):
			_fillPropDict(propertySequence)
		else:
			if type(propertySequence) in (str, unicode):
				propertyArguments = list(propertyArguments)
				propertyArguments.append(propertySequence)
				propertyArguments = tuple(propertyArguments)
		_fillPropDict(propertyArguments)
		if len(propertyArguments) == 0 and len(propertySequence) == 0:
			# User didn't send a list of properties, so return all properties:
			_fillPropDict(self.getPropertyList())
		return propDict

	
	def setProperties(self, propDict={}, **propKw):
		""" Sets a group of properties on the object all at once.
			
		You have the following options for sending the properties:
			1) Property/Value pair dictionary
			2) Keyword arguments
			3) Both
	
		The following examples all do the same thing:
		self.setProperties(FontBold=True, ForeColor="Red")
		self.setProperties({"FontBold": True, "ForeColor": "Red")
		self.setProperties({"FontBold": True}, ForeColor="Red")
		"""
		def _setProps(_propDict):
			for property in _propDict.keys():
				setter = eval("self.__class__.%s.fset" % property)
				if setter is not None:
					setter(self, _propDict[property])
				else:
					# not sure what to do here
					dabo.infoLog.write("Property '%s' is read-only." % property)
					
		# Set the props specified in the passed propDict dictionary:
		_setProps(propDict)
	
		# Set the props specified in the keyword arguments:
		_setProps(propKw)

			
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
	Bottom = property(_getBottom, _setBottom, None,
					'The position of the bottom part of the object. (int)')
	
	Form = property(_getForm, None, None,
					'Object reference to the dForm containing the object. (read only).')
	
	Right = property(_getRight, _setRight, None,
					'The position of the right part of the object. (int)')


if __name__ == "__main__":
	o = dPemMixin()
	print o.BaseClass
	o.BaseClass = "dForm"
	print o.BaseClass
