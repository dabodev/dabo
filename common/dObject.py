import dabo
from doDefaultMixin import DoDefaultMixin
from propertyHelperMixin import PropertyHelperMixin

class dObject(DoDefaultMixin, PropertyHelperMixin):
	""" The basic ancestor of all dabo objects.
	"""
	
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

		
	def _getDApp(self):
		# dApp saves a ref to itself inside the dabo module object.
		return dabo.dAppRef
	
	
	def _getDForm(self):
		""" Return a reference to the containing dForm. 
		"""
		try:
			return self._dFormCached
		except AttributeError:
			import dabo.ui
			obj, frm = self, None
			while obj:
				parent = obj.GetParent()
				if isinstance(parent, dabo.ui.dForm):
					frm = parent
					break
				else:
					obj = parent
			if frm:
				self._dFormCached = frm   # Cache for next time
			return frm


	def _getClass(self):
		try:
			return self.__class__
		except AttributeError:
			return None


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


	dApp = property(_getDApp, None, None, 
 					'Object reference to the Dabo Application object. (read only).')
	dForm = property(_getDForm, None, None,
					'Object reference to the dForm containing the object. (read only).')
 	Name = property(_getName, _setName, None, 
 					'The name of the object. (str)')
	Class = property(_getClass, None, None,
					'The class the object is based on. Read-only. (class)')
 	BaseClass = property(_getBaseClass, None, None, 
 					'The base class of the object. Read-only. (class)')
	Parent = property(_getParent, _setParent, None,	
					'The containing object. (obj)')
 	SuperClass = property(_getSuperClass, None, None, 
 					'The parent class of the object. Read-only. (class)')

if __name__ == "__main__":
	d = D()
	print d.dApp
	app = dabo.dApp()
	print d.dApp
	
	print dir(d)
