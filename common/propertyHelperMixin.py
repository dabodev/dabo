class PropertyHelperMixin(object):
	''' Helper functions for getting information on class properties.
	'''

	def getPropertyList(classOrInstance):
		''' Return the list of properties for this object (class or instance).
		'''
		propList = []
		for item in dir(classOrInstance):
			if type(eval('classOrInstance.%s' % item)) == property:
				propList.append(item)
		return propList
	getPropertyList = classmethod(getPropertyList)


	def getPropertyInfo(self, name):
		''' Return a dict of information about the passed property name.
		'''
		propRef = eval('self.__class__.%s' % name)
		propVal = eval('self.%s' % name)

		if type(propRef) == property:
			d = {}
			d['name'] = name

			if propRef.fget:
				d['showValueInDesigner'] = True
			else:
				d['showValueInDesigner'] = False

			if propRef.fset:
				d['editValueInDesigner'] = True
			else:
				d['editValueInDesigner'] = False

			d['doc'] = propRef.__doc__

			dataType = type(propVal)
			d['type'] = dataType

			try:
				d['editorInfo'] = eval('self._get%sEditorInfo()' % name)
			except:
				# There isn't an explicit editor setup, so let's derive it:
				if dataType in (type(str()), type(unicode())):
					d['editorInfo'] = {'editor': 'string', 'len': 256}
				elif dataType == type(bool()):
					d['editorInfo'] = {'editor': 'boolean'}
				elif dataType in (type(int()), type(long())):
					d['editorInfo'] = {'editor': 'integer', 'min': -65535, 'max': 65536}
			return d
		else:
			raise AttributeError, "%s is not a property." % name

	
