# -*- coding: utf-8 -*-
""" This is Dabo's user interface layer which is the topmost layer.

There are submodules for all supported UI libraries. As of this writing,
the only supported UI library is wxPython (uiwx).

To use a given submodule at runtime, you need to call loadUI() with the
ui module you want as a parameter. For instance, to load wxPython, you
would issue:

	import dabo.ui
	dabo.ui.loadUI('wx')

"""
import os, traceback
import dabo
from dabo.dLocalize import _


def getUIType():
	""" Return the identifier of the currently loaded UI, or None.
	"""
	try:
		return uiType['shortName']
	except (AttributeError, NameError, KeyError):
		return None


def loadUI(uiType):
	""" Load the given UI into the global namespace.
	"""
	retVal = False
	currType = getUIType()
	mods = {"wx" : "dabo.ui.uiwx", "tk" : "dabo.ui.uitk"}
	if uiType.lower() in ("wx", "wxpython", "uiwx"):
		typ = "wx"
	elif uiType.lower() in ("tk", "tkinter", "uitk"):
		typ = "tk"
	else:
		raise ValueError, "Unknown UI type '%s' passed to loadUI()" % uiType

	if currType is None:
		try:
			exec("from %s import *" % mods[typ], globals())
			retVal = True
		except Exception, e:
			retVal = False
			# Record the actual problem
			#dabo.logError("Error Loading UI: %s" % e)
			traceback.print_exc()

	else:
		if currType == typ:
			# No problem; just a redundant call
			pass
		else:
			dabo.logInfo(_("Cannot change the uiType to '%s', because UI '%s' is already loaded."
				% (typ, currType)))

	return retVal


# Automatically load a default UI if the environmental variable exists.
# If the DABO_DEFAULT_UI exists, that ui will be loaded into the dabo.ui
# global namespace. This is really only meant as a convenience for the
# dabo developers when rolling single-file distributions - we don't want
# everyone setting this environment variable. To specify the UI for your
# app, you should instead set the UI property of the dApp object.
try:
	__defaultUI = os.environ['DABO_DEFAULT_UI']
except KeyError:
	__defaultUI = None

if __defaultUI:
	dabo.logInfo(_("Automatically loading default ui '%s'..." % __defaultUI))
	# For now, don't do the tempting option:
	#loadUI(defaultUI)
	# ...unless it will work with single-file installers. I think that
	# for single-file installers, it needs to see the import statement.
	# Therefore, do it explicitly:
	if __defaultUI in ('wx', 'wxPython', 'uiwx'):
		from uiwx import *

else:
	pass
	#dabo.logInfo(_("No default UI set. (DABO_DEFAULT_UI)"))



def getEventData(uiEvent):
	""" Given a UI-specific event object, return a UI-agnostic name/value dictionary.

	This function must be overridden in each ui library's __init__.py to function
	correctly.
	"""
	return {}


def makeDynamicProperty(prop, additionalDoc=None):
	"""Make a Dynamic property for the passed property.

	Call this in your class definition, after you've defined the property
	you'd like to make dynamic. For example:

	Caption = property(_getCaption, _setCaption, None, None)
	DynamicCaption = makeDynamicProperty(Caption)
	"""
	import inspect

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
			if self._dynamic.has_key(propName):
				del self._dynamic[propName]
		else:
			self._dynamic[propName] = func

	doc = _("""Dynamically determine the value of the %s property.

Specify a function and optional arguments that will get called from the
update() method. The return value of the function will get set to the
%s property. If Dynamic%s is set to None (the default), %s
will not be dynamically evaluated.
""" % (propName, propName, propName, propName))

	if additionalDoc:
		doc += "\n\n" + additionalDoc

	return property(fget, fset, None, doc)

