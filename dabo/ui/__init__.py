# -*- coding: utf-8 -*-
"""
This is Dabo's user interface layer which is the topmost layer.

There are submodules for all supported UI libraries. As of this writing,
the only supported UI library is wxPython (uiwx).

To use a given submodule at runtime, you need to call loadUI() with the
ui module you want as a parameter. For instance, to load wxPython, you
would issue::

	import dabo.ui
	dabo.ui.loadUI("wx")

"""
import os
import traceback
import inspect
import dabo
from dabo.dLocalize import _

lastCallAfterStack = ""  ## see uiwx/__init__.py in callAfter and callAfterInterval

def getUIType():
	"""Return the identifier of the currently loaded UI, or None."""
	try:
		return uiType["shortName"]
	except (AttributeError, NameError, KeyError):
		return None


def deadCheck(fn, *args, **kwargs):
	"""
	This decorator is intended to detect dead objects (objects in the process of being
	destroyed) from attempts to call their methods. Currently this only supports wxPython,
	but if needed in other toolkits, different functionality will need to be coded.
	"""
	def deadCheckFunc(self, *args, **kwargs):
		if not self:
			# For testing, uncomment the print line below:
# 			print "FOUND DEAD OBJECT"
			return
		return fn(self, *args, **kwargs)
	return deadCheckFunc


def loadUI(uiType):
	"""Load the given UI into the global namespace."""
	retVal = False
	currType = getUIType()
	mods = {"wx" : "dabo.ui.uiwx", "tk" : "dabo.ui.uitk"}
	if uiType.lower() in ("wx", "wxpython", "uiwx"):
		typ = "wx"
	elif uiType.lower() in ("tk", "tkinter", "uitk"):
		typ = "tk"
	else:
		raise ValueError("Unknown UI type '%s' passed to loadUI()" % uiType)

	if currType is None:
		try:
			exec("from %s import *" % mods[typ], globals())
			retVal = True
		except Exception, e:
			retVal = False
			# Record the actual problem
			print _("ui.loadUI failed: %s") % e
			traceback.print_exc()
	else:
		if currType == typ:
			# No problem; just a redundant call
			pass
		else:
			dabo.log.info(_("Cannot change the uiType to '%(typ)s', because UI '%(currType)s' is already loaded.")
					% locals())
	return retVal


def getEventData(uiEvent):
	"""
	Given a UI-specific event object, return a UI-agnostic name/value dictionary.

	This function must be overridden in each ui library's __init__.py to function
	correctly.
	"""
	return {}


def makeDynamicProperty(prop, additionalDoc=None):
	"""
	Make a Dynamic property for the passed property.

	Call this in your class definition, after you've defined the property
	you'd like to make dynamic. For example:"

	Caption = property(_getCaption, _setCaption, None, None)
	DynamicCaption = makeDynamicProperty(Caption)

	"""
	propName = None
	frame = inspect.currentframe(1)
	for k, v in frame.f_locals.items():
		if v is prop:
			propName = k
			break
	if not propName:
		raise ValueError

	def fget(self):
		return self._dynamic.get(propName)

	def fset(self, func):
		if func is None:
			# For safety and housekeeping, delete the dynamic prop completely,
			# instead of just setting to None.
			if propName in self._dynamic:
				del self._dynamic[propName]
		else:
			self._dynamic[propName] = func

	doc = _("""Dynamically determine the value of the %(propName)s property.

Specify a function and optional arguments that will get called from the
update() method. The return value of the function will get set to the
%(propName)s property. If Dynamic%(propName)s is set to None (the default), %(propName)s
will not be dynamically evaluated.
""") % locals()

	if additionalDoc:
		doc += "\n\n" + additionalDoc

	return property(fget, fset, None, doc)


def makeProxyProperty(dct, nm, proxyAtts):
	"""
	When creating composite controls, it is necessary to be able to pass through
	property get/set calls to an object or objects within the composite control. For
	example, if a class based on dPanel contains a textbox and a label, I might want
	to proxy the class's Caption to the label's Caption, the Value to the textbox, and
	the FontSize to both. In order to do this, the object(s) to be proxied must be
	stored in the custom class as references in attributes of the custom class, and
	passed in the 'proxyAtts' parameter. In addition, passing 'self' as one of the
	proxyAtts will apply the property to the custom class itself; a good example
	would be a property like 'Height': the outer panel needs to grow as well as the
	inner controls. In this case, assuming you store a reference to the textbox and
	label in attributes named '_textbox' and '_label', respectively, the code in your
	custom composite class would look like::

		_proxyDict = {}
		Caption = makeProxyProperty(_proxyDict, "Caption", "_label")
		FontSize = makeProxyProperty(_proxyDict, "FontSize", ("_textbox", "_label"))
		Height = makeProxyProperty(_proxyDict, "Value", ("self", "_textbox"))
		Value = makeProxyProperty(_proxyDict, "Value", "_textbox")

	For setter operations, if the 'proxyAtts' is a sequence of more than one object, the
	setting will be applied to all. For the getter, only the first object in the sequence
	with that property will be used.

	You must declare an attribute named '_proxyDict' in the class definition before you
	call this method; '_proxyDict' should be an empty dictionary. This dict needs to be
	passed to this method, since there is no 'self' reference at the time that properties
	are declared in a class definition.

	'nm' is the name of the property to be proxied. 'proxyAtts' is either a single string
	with the name of the attribute that will hold the reference to the inner control, or
	it should be a tuple of strings, each of which is the name of an attribute that contains
	the reference to an inner control.
	"""
	def _resolveGet(self, nm):
		ret = None
		for att in self.__class__._proxyDict[nm]:
			if att == "self":
				base = getattr(self, "_baseClass", self.__class__)
				obj = base.__bases__[0]
				prop = getattr(obj, nm)
				ret = prop.fget(self)
			else:
				obj = getattr(self, att)
				ret = getattr(obj, nm)
			break
		return ret

	def _resolveSet(self, nm, val):
		if not self._constructed():
			return
		resolveProps = getattr(self, "_set_resolve_props", [])
		if nm in resolveProps:
			return
		resolveProps.append(nm)
		for att in self.__class__._proxyDict[nm]:
			if att == "self":
				base = getattr(self, "_baseClass", self.__class__)
				obj = base.__bases__[0]
				prop = getattr(obj, nm)
				prop.fset(self, val)
			else:
				obj = getattr(self, att)
				if obj is None:
					# Instantiation has not completed yet
					continue
				elif not isinstance(obj, (list, tuple)):
					setattr(obj, nm, val)
				else:
					for expandedObj in obj:
						if expandedObj is None:
							# Instantiation has not completed yet
							continue
						setattr(expandedObj, nm, val)
		resolveProps.remove(nm)
		# This may not be needed, but helps in many cases...
		try:
			self.layout()
		except AttributeError:
			pass


	if not isinstance(proxyAtts, (list, tuple)):
		proxyAtts = (proxyAtts, )
	dct[nm] = proxyAtts
	def fget(self):
		return _resolveGet(self, nm)
	def fset(self, val):
		return _resolveSet(self, nm, val)
	try:
		doc = getattr(dabo.ui.dPemMixin, nm).__doc__
	except AttributeError:
		doc = None
	return property(fget, fset, None, doc)


# Because some of IDEs uses lexical analysis (Wing) instead of the dynamic
# analysis (PyDev), the following code should make them happy.
if False:
	from uiwx import *
