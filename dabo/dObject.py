# -*- coding: utf-8 -*-
import string
import types
import new
import dabo
from dabo.lib.propertyHelperMixin import PropertyHelperMixin
from dabo.lib.eventMixin import EventMixin
from dabo.dLocalize import _

NONE_TYPE = type(None)


class dObject(PropertyHelperMixin, EventMixin):
	"""The basic ancestor of all Dabo objects."""
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


	def __init__(self, properties=None, attProperties=None, *args, **kwargs):
		if not hasattr(self, "_properties"):
			self._properties = {}
		if self._call_beforeInit:
			self._beforeInit()
		if self._call_initProperties:
			self._initProperties()

		# Now that user code has had an opportunity to set the properties, we can
		# see if there are properties sent to the constructor which will augment
		# or override the properties set in beforeInit().

		# Some classes that are not inherited from the ui-layer PEM mixin classes
		# can have attProperties passed. Since these are all passed as strings, we
		# need to convert them to their proper type and add them to the properties
		# dict.
		if properties is None:
			properties = {}
		if attProperties:
			for prop, val in attProperties.items():
				if prop in ("designerClass", ):
					continue
				if prop in properties:
					# The properties value has precedence, so ignore.
					continue
				typ = type(getattr(self, prop))
				if not issubclass(typ, basestring):
					if issubclass(typ, bool):
						val = (val == "True")
					elif typ is NONE_TYPE:
						val = None
					else:
						try:
							val = typ(val)
						except ValueError, e:
							# Sometimes int values can be stored as floats
							if typ in (int, long):
								val = float(val)
							else:
								raise e
				properties[prop] = val

		# The keyword properties can come from either, both, or none of:
		#    + the properties dict
		#    + the kwargs dict
		# Get them sanitized into one dict:
		if properties is not None:
			# Override the class values
			for k,v in properties.items():
				self._properties[k] = v
		properties = self._extractKeywordProperties(kwargs, self._properties)
		if kwargs:
			# Some kwargs haven't been handled.
			bad = ", ".join(["'%s'" % kk for kk in kwargs])
			raise TypeError("Invalid keyword arguments passed to %s: %s" % (self.__repr__(), bad))

		if self._call_afterInit:
			self._afterInit()
		self.setProperties(properties)

		PropertyHelperMixin.__init__(self)
		EventMixin.__init__(self)


	def __repr__(self):
		bc = self.BaseClass
		if bc is None:
			bc = self.__class__
		strval = "%s" % bc
		classname = strval.split("'")[1]
		classparts = classname.split(".")
		if ".ui.ui" in classname:
			# Simplify the different UI toolkits
			pos = classparts.index("ui")
			classparts.pop(pos+1)
		# Remove the duplicate class name that happens
		# when the class name is the same as the file.
		while (len(classparts) > 1) and (classparts[-1] == classparts[-2]):
			classparts.pop()
		classname = ".".join(classparts)

		try:
			nm = self.Name
		except AttributeError:
			nm = ""

		regid = getattr(self, "RegID", "")
		if regid:
			nm = regid

		if (not nm) or (nm == "?"):
			# No name; use module.classname
			nm = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)
		_id = self._getID()
		return "<%(nm)s (baseclass %(classname)s, id:%(_id)s)>" % locals()


	def _getID(self):
		"""
		Defaults to the Python id() function. Objects in sub-modules, such as the various
		UI toolkits, can override to substitute something more relevant to them.
		"""
		return id(self)


	def beforeInit(self, *args, **kwargs):
		"""
		Subclass hook. Called before the object is fully instantiated.
		Usually, user code should override afterInit() instead, but there may be
		cases where you need to set an attribute before the init stage is fully
		underway.
		"""
		pass


	def afterInit(self):
		"""
		Subclass hook. Called after the object's __init__ has run fully.
		Subclasses should place their __init__ code here in this hook, instead of
		overriding __init__ directly, to avoid conflicting with base Dabo behavior.
		"""
		pass


	def initProperties(self):
		"""
		Hook for subclasses. User subclasses should set properties
		here, such as::

			self.Name = "MyTextBox"
			self.BackColor = (192,192,192)

		"""
		pass


	def initEvents(self):
		"""
		Hook for subclasses. User code should do custom event binding
		here, such as::

			self.bindEvent(dEvents.GotFocus, self.customGotFocusHandler)

		"""
		pass


	def _beforeInit(self):
		"""Framework subclass hook."""
		self.beforeInit()


	def _initProperties(self):
		"""Framework subclass hook."""
		self.initProperties()


	def _afterInit(self):
		"""Framework subclass hook."""
		self.afterInit()


	def getAbsoluteName(self):
		"""Return the fully qualified name of the object."""
		names = [self.Name, ]
		obj = self
		while True:
			try:
				parent = obj.Parent
			except AttributeError:
				# Parent not necessarily defined
				parent = None
			if parent:
				try:
					name = parent.Name
				except AttributeError:
					name = "?"
				names.append(name)
				obj = parent
			else:
				break
		names.reverse()
		return ".".join(names)


	def getMethodList(cls, refresh=False):
		"""Return the list of (Dabo) methods for this class or instance."""
		try:
			methodList = cls.__methodList
		except AttributeError:
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
					if item in c.__dict__:
						if type(c.__dict__[item]) in (types.MethodType, types.FunctionType):
							if methodList.count(item) == 0:
								methodList.append(item)
		methodList.sort()
		cls.__methodList = methodList
		return methodList
	getMethodList = classmethod(getMethodList)

	def super(self, *args, **kwargs):
		"""This method used to call superclass code, but it's been removed."""
		raise NotImplementedError(_(
				"Please change your self.super() call to super(cls, self)."))

	def _addCodeAsMethod(self, cd):
		"""
		This method takes a dictionary containing method names as
		keys, and the method code as the corresponding values, compiles
		it, and adds the methods to this object. If the method name begins
		with 'on', and dabo.autoBindEvents is True, an event binding will be
		made just as with normal auto-binding. If the code cannot be
		compiled successfully, an error message will be added
		to the Dabo ErrorLog, and the method will not be added.
		"""
		for nm, code in cd.items():
			try:
				code = code.replace("\n]", "]")
				compCode = compile(code, "", "exec")
			except SyntaxError, e:
				snm = self.Name
				dabo.log.error(_("Method '%(nm)s' of object '%(snm)s' has the following error: %(e)s") % locals())
				continue
			# OK, we have the compiled code. Add it to the class definition.
			# NOTE: if the method name and the name in the 'def' statement
			# are not the same, the results are undefined, and will probably crash.
			nmSpace = {}
			exec compCode in nmSpace
			mthd = nmSpace[nm]
			exec "self.%s = %s.__get__(self)" % (nm, nm)
			newMethod = new.instancemethod(mthd, self)
			setattr(self, nm, newMethod)


	# Property definitions begin here
	def _getApplication(self):
		# dApp saves a ref to itself inside the dabo module object.
		return dabo.dAppRef


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


	def _getBasePrefKey(self):
		try:
			ret = self._basePrefKey
		except AttributeError:
			ret = self._basePrefKey = ""
		return ret

	def _setBasePrefKey(self, val):
		if not isinstance(val, types.StringTypes):
			raise TypeError('BasePrefKey must be a string.')
		self._basePrefKey = val
		pm = self.PreferenceManager
		if pm is not None:
			if not pm._key:
				pm._key = val


	def _getClass(self):
		return self.__class__


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

	def _setName(self, val):
		if not isinstance(val, types.StringTypes):
			raise TypeError('Name must be a string.')
		if not len(val.split()) == 1:
			raise KeyError('Name must not contain any spaces')
		self._name = val


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


	def _getPreferenceManager(self):
		try:
			ret = self._preferenceManager
		except AttributeError:
			ret = None
			if self.Application is not self:
				try:
					ret = self._preferenceManager = self.Application.PreferenceManager
				except AttributeError: pass
			if ret is None:
				from dabo.dPref import dPref  ## here to avoid circular import
				ret = self._preferenceManager = dPref(key=self.BasePrefKey)
		return ret

	def _setPreferenceManager(self, val):
		from dabo.dPref import dPref  ## here to avoid circular import
		if not isinstance(val, dPref):
			raise TypeError('PreferenceManager must be a dPref object')
		self._preferenceManager = val


	Application = property(_getApplication, None, None,
			_("Read-only object reference to the Dabo Application object.  (dApp)."))

	BaseClass = property(_getBaseClass, None, None,
			_("The base Dabo class of the object. Read-only.  (class)"))

	BasePrefKey = property(_getBasePrefKey, _setBasePrefKey, None,
			_("Base key used when saving/restoring preferences  (str)"))

	Class = property(_getClass, None, None,
			_("The class the object is based on. Read-only.  (class)"))

	LogEvents = property(_getLogEvents, _setLogEvents, None,
			_("""
			Specifies which events to log.  (list of strings)

			If the first element is 'All', all events except the following listed events
			will be logged.
			Event logging is resource-intensive, so in addition to setting this LogEvents
			property, you also need to make the following call:

				>>> dabo.eventLogging = True

			"""))

	Name = property(_getName, _setName, None,
			_("The name of the object.  (str)"))

	Parent = property(_getParent, _setParent, None,
			_("The containing object.  (obj)"))

	PreferenceManager = property(_getPreferenceManager, _setPreferenceManager, None,
			_("Reference to the Preference Management object  (dPref)"))


if __name__ == "__main__":
	from dabo.dApp import dApp
	d = dObject()
	print d.Application
	app = dApp()
	print d.Application
