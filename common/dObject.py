import dabo
from dabo.common import PropertyHelperMixin
from dabo.common import DoDefaultMixin
from dabo.common import EventMixin
from dabo.dLocalize import _
#from dabo.lib import autosuper
	
class dObject(DoDefaultMixin,  PropertyHelperMixin, EventMixin):
	""" The basic ancestor of all dabo objects.
	"""
	
	def escapeQt(self, s):
		sl = "\\"
		qt = "\'"
		return s.replace(sl, sl+sl).replace(qt, sl+qt)

	def getAbsoluteName(self):
		""" Return the fully qualified name of the object.
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
 					'Object reference to the Dabo Application object. (read only).')
	
	BaseClass = property(_getBaseClass, None, None, 
 					'The base class of the object. Read-only. (class)')
	
	Class = property(_getClass, None, None,
					'The class the object is based on. Read-only. (class)')
 	
	LogEvents = property(_getLogEvents, _setLogEvents, None, 
					"Specifies which events to log. (list of strings)\n"
					"\n"
					"If the first element is 'All', all events except the following\n"
					"listed events will be logged.")
					
	Name = property(_getName, _setName, None, 
 					'The name of the object. (str)')
	
	Parent = property(_getParent, _setParent, None,	
					'The containing object. (obj)')
 	
	SuperClass = property(_getSuperClass, None, None, 
 					'The parent class of the object. Read-only. (class)')

if __name__ == "__main__":
	d = dObject()
	print d.Application
	app = dabo.dApp()
	print d.Application
