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
from dActionList import dActionList
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
	module = None
	
	if getUIType() is None:
		if uiType.lower() in ('wx', 'wxpython', 'uiwx'):
			module = "dabo.ui.uiwx"
		elif uiType.lower() in ('tk', 'tkinter', 'uitk'):
			module = "dabo.ui.uitk"
			
		if module:
			try:
				exec("from %s import *" % module, globals())
				retVal = True
			except ImportError, e:
				retVal = False
				# Record the actual problem
				#dabo.errorLog.write("Error Loading UI: %s" % e)
				traceback.print_exc()
				
	else:
		dabo.infoLog.write(_("Cannot change the uiType to '%s', because UI '%s' is already loaded."
			% (uiType, getUIType())))
			
	return retVal

	
# Automatically load a default UI if the environmental variable exists.
# If the DABO_DEFAULT_UI exists, that ui will be loaded into the dabo.ui
# global namespace. This is really only meant as a convenience for the 
# dabo developers when rolling single-file distributions - we don't want
# everyone setting this environment variable. To specify the UI for your
# app, you should instead set the UserInterface property of the dApp 
# object.
try:
	__defaultUI = os.environ['DABO_DEFAULT_UI']
except KeyError:
	__defaultUI = None

if __defaultUI:
	dabo.infoLog.write(_("Automatically loading default ui '%s'..." % __defaultUI))
	# For now, don't do the tempting option:
	#loadUI(defaultUI)
	# ...unless it will work with single-file installers. I think that
	# for single-file installers, it needs to see the import statement.
	# Therefore, do it explicitly:
	if __defaultUI in ('wx', 'wxPython', 'uiwx'):
		from uiwx import *
	
else:
	dabo.infoLog.write(_("No default UI set. (DABO_DEFAULT_UI)"))

	
	
def getEventData(uiEvent):
	""" Given a UI-specific event object, return a UI-agnostic name/value dictionary.
	
	This function must be overridden in each ui library's __init__.py to function
	correctly.
	"""
	return {}
	
