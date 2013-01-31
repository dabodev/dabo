# -*- coding: utf-8 -*-
import string
from dabo.dLocalize import _


class PropertyHelperMixin(object):
	"""Helper functions for getting information on class properties."""

	@staticmethod
	def _expandPropStringValue(value, propList):
		"""
		Called from various property setters: expand value into one of the
		accepted property values in propList. We allow properties to be set
		using case-insensitivity, and for properties with distinct first letters
		for user code to just set the property using the first letter.
		"""
		value = value.lower().strip()

		uniqueFirstLetter = True
		firstLetterCounts = {}
		firstLetters = {}
		lowerPropMap = {}
		for idx, prop in enumerate(propList):
			if prop is None:
				continue
			letter = prop[0:1].lower()
			firstLetterCounts[letter] = firstLetterCounts.get(letter, 0) + 1
			if firstLetterCounts[letter] > 1:
				uniqueFirstLetter = False
			firstLetters[letter] = propList[idx]
			lowerPropMap[prop.lower().strip()] = prop

		if uniqueFirstLetter:
			# just worry about the first letter in value:
			value = firstLetters.get(value[0:1])
		else:
			value = lowerPropMap.get(value)

		if value is None:
			if None not in propList:
				s = _("The only accepted values for this property are ")
				for idx, p in enumerate(propList):
					if idx == len(propList) - 1:
						s += """%s '%s'.""" % (_("and"), p)
					else:
						s += """'%s', """ % p
				raise ValueError(s)
		return value


	def _extractKeywordProperties(self, kwdict, propdict):
		"""
		Called from __init__: puts any property keyword arguments into
		the property dictionary, so that __init__ can pass that dict to
		setProperties() when appropriate (and so the property keywords are
		removed before sending **kwargs to the wx constructor).
		"""
		if propdict is None:
			propdict = {}
		props = self.getPropertyList()
		for arg in kwdict.keys():
			if arg in props:
				propdict[arg] = kwdict.pop(arg)
		return propdict


	@staticmethod
	def _extractKeyWordEventBindings(kwdict, evtdict):
		"""
		Called from __init__: puts any On* event keyword arguments into
		the event dictionary.
		"""
		if evtdict is None:
			evtdict = {}
		onKWs = [(kw, kw[2:]) for kw in kwdict if kw.startswith("On")]
		for kw, evtName in onKWs:
			evtdict[evtName] = kwdict.pop(kw)


	@staticmethod
	def _extractKey(kwdict, key, defaultVal=None):
		"""
		If the supplied key is present in the kwdict, the associated
		value is returned, and that key's element is deleted from the
		dict. If the key doesn't exist, the default value is returned. If
		kwdict is a tuple/list, it will look in each element until a value
		is found.
		"""
		if not isinstance(kwdict, (tuple, list)):
			kwdict = (kwdict,)
		ret = defaultVal
		found = False
		for dd in kwdict:
			if dd is None:
				continue
			try:
				if not found:
					ret = dd[key]
					found = True
				del dd[key]
			except KeyError:
				pass
		return ret


	def getProperties(self, propertySequence=(), propsToSkip=(),
			ignoreErrors=False, *propertyArguments):
		"""
		Returns a dictionary of property name/value pairs.

		If a sequence of properties is passed, just those property values
		will be returned. Otherwise, all property values will be returned.
		The sequence of properties can be a list, tuple, or plain string
		positional arguments. For instance, all of the following are
		equivilent::

			print self.getProperties("Caption", "FontInfo", "Form")
			print self.getProperties(["Caption", "FontInfo", "Form"])
			t = ("Caption", "FontInfo", "Form")
			print self.getProperties(t)
			print self.getProperties(\*t)

		An exception will be raised if any passed property names don't
		exist, aren't actual properties, or are not readable (do not have
		getter functions).

		However, if an exception is raised from the property getter function,
		the exception will get caught and used as the property value in the
		returned property dictionary. This allows the property list to be
		returned even if some properties can't be evaluated correctly by the
		object yet.
		"""
		propDict = {}

		def _fillPropDict(_propSequence):
			for prop in _propSequence:
				if prop in propsToSkip:
					continue
				propRef = eval("self.__class__.%s" % prop)
				if type(propRef) == property:
					getter = propRef.fget
					if getter is not None:
						try:
							propDict[prop] = getter(self)
						except Exception, e:
							propDict[prop] = e
					else:
						if not ignoreErrors:
							raise ValueError("Property '%s' is not readable." % prop)
						pass
				else:
					raise AttributeError("'%s' is not a property." % prop)

		if isinstance(propertySequence, (list, tuple)):
			_fillPropDict(propertySequence)
		else:
			if isinstance(propertySequence, basestring):
				# propertySequence is actually a string property name:
				# append to the propertyArguments tuple.
				propertyArguments = list(propertyArguments)
				propertyArguments.append(propertySequence)
				propertyArguments = tuple(propertyArguments)
		_fillPropDict(propertyArguments)

		if len(propertyArguments) == 0 and len(propertySequence) == 0:
			# User didn't send a list of properties, so return all properties:
			_fillPropDict(self.getPropertyList())

		return propDict


	def setProperties(self, propDict={}, ignoreErrors=False, **propKw):
		"""
		Sets a group of properties on the object all at once.

		You have the following options for sending the properties:

			1) Property/Value pair dictionary
			2) Keyword arguments
			3) Both

		The following examples all do the same thing::

			self.setProperties(FontBold=True, ForeColor="Red")
			self.setProperties({"FontBold": True, "ForeColor": "Red"})
			self.setProperties({"FontBold": True}, ForeColor="Red")

		"""
		def _setProps(_propDict):
			delayedSettings = {}
			for prop in _propDict:
				if prop in ("Name", "NameBase"):
					try:
						self._setName(_propDict[prop])
						continue
					except NameError:
						pass
				propRef = eval("self.__class__.%s" % prop)
				if type(propRef) == property:
					setter = propRef.fset
					if setter is not None:
						if prop in ("Value", "Picture"):
							# We need to delay setting this to last
							delayedSettings[setter] = _propDict[prop]
						else:
							setter(self, _propDict[prop])
					else:
						if not ignoreErrors:
							raise ValueError("Property '%s' is read-only." % prop)
				else:
					raise AttributeError("'%s' is not a property." % prop)
			if delayedSettings is not None:
				for setter, val in delayedSettings.items():
					setter(self, val)

		# Set the props specified in the passed propDict dictionary:
		_setProps(propDict)

		# Set the props specified in the keyword arguments:
		_setProps(propKw)


	def setPropertiesFromAtts(self, propDict={}, ignoreExtra=True, context=None):
		"""
		Sets a group of properties on the object all at once. This
		is different from the regular setProperties() method because
		it only accepts a dict containing prop:value pairs, and it
		assumes that the value is always a string. It will convert
		the value to the correct type for the property, and then set
		the property to that converted value. If the value needs to be evaluated
		in a specific namespace, pass that as the 'context' parameter.
		"""
		for prop, val in propDict.items():
			if not hasattr(self, prop):
				# Not a valid property
				if ignoreExtra:
					# ignore
					continue
				else:
					raise AttributeError("'%s' is not a property." % prop)
			try:
				valToSet = eval(val, context)
			except (TypeError, SyntaxError, NameError, AttributeError):
				valToSet = val
			setattr(self, prop, valToSet)


	def _setKwEventBindings(self, kwEvtDict):
		"""
		This method takes a dict of event names and method to which they are
		to be bound, and binds the corresponding event to that method.
		"""
		for evtName, mthd in kwEvtDict.items():
			from dabo import dEvents
			evt = dEvents.__dict__[evtName]
			if callable(mthd):
				self.bindEvent(evt, mthd)
			else:
				# A string that needs to be eval'd after construction was passed.
				self._delayedEventBindings.append((evt, mthd))


	def getPropertyList(cls, refresh=False, onlyDabo=False):
		"""
		Returns the list of properties for this object (class or instance).

		:param refresh: the cached property list (if any) will be rebuilt.
		:param onlyDabo: we won't list the properties underneath the
		__mro__ of dObject.
		:rtype: list of properties
		"""
		propLists = getattr(cls, "_propLists", {})
		propList = propLists.get((cls, onlyDabo), [])

		if refresh:
			propList = []

		if propList:
			## A prior call has already generated the propList
			return propList

		for c in cls.__mro__:
			if onlyDabo and c is PropertyHelperMixin:
				# Don't list properties lower down (e.g., from wxPython):
				break
			for item in dir(c):
				if item[0] in string.uppercase:
					if item in c.__dict__:
						if type(c.__dict__[item]) == property:
							if propList.count(item) == 0:
								propList.append(item)
		propList.sort()
		if not hasattr(cls, "_propLists"):
			cls._propLists = {}
		cls._propLists[(cls, onlyDabo)] = propList
		return propList
	getPropertyList = classmethod(getPropertyList)


	def getPropertyInfo(cls, name):
		"""Returns a dictionary of information about the passed property name."""
		# cls can be either a class or self
		classRef = cls
		try:
			issubclass(cls, object)
		except TypeError:
			classRef = cls.__class__

		propRef = getattr(classRef, name)

		if type(propRef) == property:
			if propRef.fget is None:
				# With no getter, the property's value cannot be determined
				propVal = None
			else:
				try:
					propVal = propRef.fget(cls)
				except StandardError:
					# There are many reasons the propval may not be determined for now,
					# such as not being a live instance.
					propVal = None

			d = {}
			d["name"] = name

			if propRef.fget:
				d["readable"] = True
			else:
				d["readable"] = False

			if propRef.fset:
				d["writable"] = True
			else:
				d["writable"] = False

			d["doc"] = propRef.__doc__
			d["type"] = type(propVal)
			d["definedIn"] = None
			for o in classRef.__mro__:
				if name in o.__dict__:
					d["definedIn"] = o

			return d
		else:
			raise AttributeError("%s is not a property." % name)
	getPropertyInfo = classmethod(getPropertyInfo)



class _DynamicList(list):
	"""
	Helper class for list-based properties, such as the 'Choices' property of
	list-type controls. This wraps the regular Python list object, but in addition
	also propagates changes to the control, so that code like this:

		control.Choices.append("Something")
			- or -
		control.Choices.sort()

	will modify the choices in the control, as most users would expect.
	"""
	def __init__(self, seq, obj, propname=None):
		self._object = obj
		if propname is None:
			propname = "Choices"
		self._setter = getattr(obj.__class__, propname).fset
		super(_DynamicList, self).__init__(seq)


	def _updateControl(self):
		self._setter(self._object, self)


	def __add__(self, val):
		ret = super(_DynamicList, self).__add__(val)
		self._updateControl()
		return ret


	def __delitem__(self, val):
		ret = super(_DynamicList, self).__delitem__(val)
		self._updateControl()
		return ret


	def __delslice__(self, i, j):
		ret = super(_DynamicList, self).__delslice__(i, j)
		self._updateControl()
		return ret


	def __iadd__(self, val):
		ret = super(_DynamicList, self).__iadd__(val)
		self._updateControl()
		return ret


	def __imul__(self, val):
		ret = super(_DynamicList, self).__imul__(val)
		self._updateControl()
		return ret


	def __setitem__(self, i, val):
		ret = super(_DynamicList, self).__setitem__(i, val)
		self._updateControl()
		return ret


	def __setslice__(self, i, j, val):
		ret = super(_DynamicList, self).__setslice__(i, j, val)
		self._updateControl()
		return ret


	def append(self, val):
		ret = super(_DynamicList, self).append(val)
		self._updateControl()
		return ret


	def extend(self, iterable):
		ret = super(_DynamicList, self).extend(iterable)
		self._updateControl()
		return ret


	def insert(self, i, val):
		ret = super(_DynamicList, self).insert(i, val)
		self._updateControl()
		return ret


	def pop(self, i=None):
		if i is None:
			i = len(self) - 1
		ret = super(_DynamicList, self).pop(i)
		self._updateControl()
		return ret


	def remove(self, val):
		ret = super(_DynamicList, self).remove(val)
		self._updateControl()
		return ret


	def reverse(self):
		ret = super(_DynamicList, self).reverse()
		self._updateControl()
		return ret


	def sort(self, cmp=None, key=None, reverse=False):
		ret = super(_DynamicList, self).sort(cmp, key, reverse)
		self._updateControl()
		return ret
