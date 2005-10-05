import string
import types
import dabo
from dabo.common import PropertyHelperMixin
from dabo.common import DoDefaultMixin
from dabo.common import EventMixin
from dabo.dLocalize import _
	
class dObject(DoDefaultMixin, PropertyHelperMixin, EventMixin):
	""" The basic ancestor of all dabo objects.
	"""
	# Subclasses can set these to False, in which case they are responsible
	# for maintaining the following call order:
	#   self._beforeInit()
	#   # optional stuff
	#   super().__init__()
	#   # optional stuff
	#   self._afterInit()
	# or, not calling super() at all, but remember to call _initProperties() and
	# the call to setProperties() at the end!
	_call_beforeInit, _call_afterInit, _call_initProperties = True, True, True

	def __init__(self, properties=None, *args, **kwargs):
		self._properties = {}
		if self._call_beforeInit:
			self._beforeInit()
		if self._call_initProperties:
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
		properties = self.extractKeywordProperties(kwargs, self._properties)
		if self._call_afterInit:
			self._afterInit()
		self.setProperties(properties)

		DoDefaultMixin.__init__(self)		
		PropertyHelperMixin.__init__(self)		
		EventMixin.__init__(self)		


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
		
			
	def _beforeInit(self):
		"""Framework subclass hook.
		"""
		self.beforeInit()

	def _initProperties(self):
		"""Framework subclass hook.
		"""
		self.initProperties()

	def _afterInit(self):
		"""Framework subclass hook.
		"""
		self.afterInit()


	def getAbsoluteName(self):
		"""Return the fully qualified name of the object.
		"""
		names = [self.Name, ]
		object = self
		while True:
			try:
				parent = object.Parent
			except AttributeError:
				# Parent not necessarily defined
				parent = None
			if parent:
				try:
					name = parent.Name
				except AttributeError:
					name = "?"
				names.append(name)
				object = parent
			else:
				break
		names.reverse()
		return '.'.join(names)

		
	def getMethodList(cls, refresh=False):
		"""Return the list of (Dabo) methods for this class or instance."""
		try:
			methodList = cls.__methodList
		except:
			methodList = None

		if refresh:
			methodList = None

		if isinstance(methodList, list):
			## A prior call has already generated the methodList
			return methodList

		methodList = []
		for c in cls.__mro__:
			for item in dir(c):
				if item[0] in string.lowercase:
					if c.__dict__.has_key(item):
						if type(c.__dict__[item]) in (types.MethodType, types.FunctionType):
							if methodList.count(item) == 0:
								methodList.append(item)
		methodList.sort()
		cls.__methodList = methodList
		return methodList
	getMethodList = classmethod(getMethodList)


	def _getBaseClass(self):
		# Every Dabo baseclass must set self._baseClass explicitly, to itself. For instance:
		# 	class dBackend(object)
		#		def __init__(self):
		#			self._baseClass = dBackend
		# IOW, BaseClass isn't the actual Python base class of the object, but the Dabo-
		# relative base class.
		try:
			return self._baseClass
		except AttributeError:
			return None

		
	def _getApplication(self):
		# dApp saves a ref to itself inside the dabo module object.
		return dabo.dAppRef
	
	
	def _getClass(self):
		try:
			return self.__class__
		except AttributeError:
			return None


	def _getLogEvents(self):
		# This is expensive, as it is semi-recursive upwards in the containership 
		# until some parent object finally reports a LogEvents property. In normal 
		# use, this will be the Application object.
		try:
			le = self._logEvents
		except AttributeError:
			# Try to get the value from the parent object, or the Application if
			# no Parent.
			if self.Parent is not None:
				parent = self.Parent
			else:
				if self == self.Application:
					parent = None
				else:
					parent = self.Application
				
			try:
				le = parent.LogEvents
			except AttributeError:
				le = []
				
		return le
		
			
	def _setLogEvents(self, val):
		self._logEvents = list(val)

		
	def _getName(self):
		try:
			return self._name
		except AttributeError:
			return "?"
			
	
	def _setName(self, value):
		self._name = str(value)
		
		
	def _getParent(self):
		# Subclasses must override as necessary. Parent/child relationships 
		# don't exist for all nonvisual objects, and implementation of parent/child
		# relationships will vary. This implementation is the simplest.
		try:
			return self._parent
		except AttributeError:
			return None
		
		
	def _setParent(self, obj):
		# Subclasses must override as necessary.
		self._parent = obj
					
		
	def _getSuperClass(self):
		if self.BaseClass == self.Class:
			# The superclass is lower down than Dabo, and useless to the user.
			return None
		else:
			return self.__class__.__base__
	

	Application = property(_getApplication, None, None, 
 		_("""Object reference to the Dabo Application object. (read only)."""))
	
	BaseClass = property(_getBaseClass, None, None, 
 		_("""The base Dabo class of the object. Read-only. (class)"""))
	
	Class = property(_getClass, None, None,
		_("""The class the object is based on. Read-only. (class)"""))
 	
	LogEvents = property(_getLogEvents, _setLogEvents, None, 
		_("""Specifies which events to log. (list of strings)

		If the first element is 'All', all events except the following listed events 
		will be logged. 

		Event logging is resource-intensive, so in addition to setting this LogEvents
		property, you also need to make the following call:

		>>> dabo.eventLogging = True
		"""))
					
	Name = property(_getName, _setName, None, 
 		_("""The name of the object. (str)"""))
	
	Parent = property(_getParent, _setParent, None,	
		_("""The containing object. (obj)"""))
 	
	SuperClass = property(_getSuperClass, None, None, 
 		_("""The parent class of the object. Read-only. (class)"""))


if __name__ == "__main__":
	d = dObject()
	print d.Application
	app = dabo.dApp()
	print d.Application
