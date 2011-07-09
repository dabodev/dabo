# -*- coding: utf-8 -*-

"""
Dabo: A Framework for developing data-driven business applications

Dabo is for developing multi-platform database business applications -
you know, applications that need to connect to a database server (MySQL,
Oracle, MS-SQL, whatever), get recordsets of data based on criteria
set by the user, provide easy ways to edit and commit changes to the
data, and to report on the data.

You either program using Python, importing the dabo library, or you
use the Dabo Class Designer to create xml files to define your classes.
These xml files can contain embedded python code for the best of all worlds.

So, the basic idea is that you have a functional, working, albeit basic
application up and running very quickly, and you can then spend time
getting all the fancy bells and whistles implemented. Keep things as
simple as possible though, while still fulfilling your customer's
specifications. Simplicity is the better part of elegance.

Beyond the wizards and xml definition files, Dabo exposes a nice
API in Python for manually creating your own class definitions. IOW,
we let you have as much control as you need. You aren't required to
take advantage of our xml definition formats at all.

Dabo has three main submodules, representing the three tiers common
in modern database application design:

	dabo.db  : database
	dabo.biz : business objects
	dabo.ui  : user interface

dabo.db and dabo.biz are completely ui-free, while dabo.ui (currently)
requires wxPython. We have allowed for possible future support for other
ui libraries, such as PyQt, tk, and curses.

The Dabo framework will have to be distributed to your client's machine(s),
along with your project-specific data definitions and (if applicable), your
subclasses of the Dabo classes and additional Python scripts, if any. There
are ways to do runtime deployment via installers that take the complexity
out of this, but that is outside the scope of Dabo itself, and you'll use
a different method for each target platform.

To run Dabo, and apps based on Dabo, you need:
	+ Python 2.4 or higher (2.5 or higher recommended)
	+ wxPython 2.8 or higher (2.8.8 or higher highly recommended)
      (only necessary for apps with a ui: because of the modular
	  nature of Dabo's design, it is possible to use just the
	  db layer, or the db layer in conjunction with the biz
	  layer, with no ui at all.)
	+ pysqlite2: The Python dbapi module for SQLite. (Not needed in
	  Python 2.5 and higher)
	+ Windows 98SE or higher
	+ Macintosh OSX 10.2 or higher (*much* nicer in Tiger - 10.4)
	+ Linux 2.4 with X11 running and Gtk2
	+ Access to some sort of database server, along with the
	  appropriate Python driver(s) installed. For example, for
	  MySQL you'll need to have the MySQL client libraries
	  installed, as well as the MySQLDb Python module. (Dabo
	  does not use ODBC: it connects directly using the Python
	  DB API coupled with the individual database drivers. This
	  is, at the same time, less flexible, tougher to get started
	  with, but more capable, more multi-platform, and better
	  performing, than ODBC is.) (we recommend starting with MySQL
	  installed, because all of the demo code has the best support
	  for MySQL).

How you get started is pretty much up to you. Run DaboDemo.py which
is in demo/DaboDemo. Run AppWizard.py which is in ide/wizards.
Run ClassDesigner.py or ReportDesigner.py in the ide directory.

For some quick eye-candy, once you've installed Dabo using the standard
'python setup.py install' method, do this from your Python interpreter::

	import dabo
	dabo.dApp().start()

press Ctrl+D and type the following into the command window that appears::

	tb = dabo.ui.dTextBox(self)

Notice the textbox in the upper left hand corner? ::

	tb.Value = "yippee!"
	tb.FontBold = True
	print tb.Value

Now, use the ui to change the value in the textbox, and switch back to
the command window. ::

	print tb.Value

Have fun in your exploration of Dabo!
"""

import sys
import os
import locale
import logging
import logging.handlers
try:
	import pysqlite2
except ImportError:
	try:
		import sqlite3
	except ImportError:
		msg = """

Dabo requires SQLite 3 and the pysqlite2 module. You will have to install these
free products before running Dabo. You can get them from the following locations:

SQLite: http://www.sqlite.org/download.html
pysqlite2: http://initd.org/tracker/pysqlite

"""
		sys.exit(msg)

# dApp will change the following values upon its __init__:
dAppRef = None

# Import global settings (do this first, as other imports may rely on it):
# NOTE: Yeah, it's namespace pollution, but in this case it is deliberate:
# we want to make them part of the dabo namespace.
from settings import *

def getEncoding():
	encoding = locale.getlocale()[1] or locale.getdefaultlocale()[1] or defaultEncoding

	def _getEncodingName():
		if encoding.isdigit():
			# Fix for missing encoding aliases e.g. '874'.
			yield  "cp%s" % encoding
		yield encoding
		prefEncoding = locale.getpreferredencoding()
		if not encoding == prefEncoding:
			yield prefEncoding
		if not encoding == defaultEncoding:
			yield defaultEncoding
		raise ValueError, "Unknown encoding: %s" % encoding

	for encoding in _getEncodingName():
		try:
			"".encode(encoding)
		except LookupError:
			pass
		else:
			break
	return encoding

def getXMLEncoding():
	ret = getEncoding()
	if ret.lower().strip().replace("-", "") == "utf8":
		return "utf-8"
	if "1252" in ret:
		return "windows-1252"
	return ret


# These are the various standard log handlers.
consoleLogHandler = fileLogHandler = None
dbConsoleLogHandler = dbFileLogHandler = None
# See if a logging.conf file exists in either the current directory or
# the base directory for the dabo module. If such a file is found, use
# it to configure logging. Otherwise, use the values gotten from
# dabo.settings.
_logConfFileName = "logging.conf"
_hasConfFile = False
_logConfFile = os.path.join(os.getcwd(), _logConfFileName)
if not os.path.exists(_logConfFile):
	_daboloc = os.path.dirname(__file__)
	_logConfFile = os.path.join(_daboloc, _logConfFileName)
if os.path.exists(_logConfFile):
	# If a 'logging.conf' file exists, use it instead of dabo.settings.
	import logging.config
	logging.config.fileConfig(_logConfFile)
	# Populate the module namespace with the appropriate loggers
	log = logging.getLogger(mainLogQualName)
	dbActivityLog = logging.getLogger(dbLogQualName)
	for _handler in log.handlers:
		try:
			_handler.baseFilename
			fileLogHandler = _handler
		except AttributeError:
			consoleLogHandler = _handler
	for _handler in dbActivityLog.handlers:
		try:
			_handler.baseFilename
			dbFileLogHandler = _handler
			break
		except AttributeError:
			dbConsoleLogHandler = _handler
else:
	# Use dabo.settings values to configure the logs
	enc = getEncoding()
	consoleLogHandler = logging.StreamHandler()
	consoleLogHandler.setLevel(mainLogConsoleLevel)
	consoleFormatter = logging.Formatter(consoleFormat)
	consoleFormatter.datefmt = mainLogDateFormat
	consoleLogHandler.setFormatter(consoleFormatter)
	log = logging.getLogger(mainLogQualName)
	log.setLevel(logging.DEBUG)
	log.addHandler(consoleLogHandler)
	if mainLogFile is not None:
		fileLogHandler = logging.handlers.RotatingFileHandler(filename=mainLogFile,
				maxBytes=maxLogFileSize, encoding=enc)
		fileLogHandler.setLevel(mainLogFileLevel)
		fileFormatter = logging.Formatter(fileFormat)
		fileFormatter.datefmt = mainLogDateFormat
		fileLogHandler.setFormatter(fileFormatter)
		log.addHandler(fileLogHandler)

	dbConsoleLogHandler = logging.StreamHandler()
	dbConsoleLogHandler.setLevel(dbLogConsoleLevel)
	dbConsoleFormatter = logging.Formatter(dbConsoleFormat)
	dbConsoleFormatter.datefmt = dbLogDateFormat
	dbConsoleLogHandler.setFormatter(dbConsoleFormatter)
	dbActivityLog = logging.getLogger(dbLogQualName)
	dbActivityLog.setLevel(dbLogLevel)
	dbActivityLog.addHandler(dbConsoleLogHandler)
	if dbLogFile is not None:
		dbFileLogHandler = logging.handlers.RotatingFileHandler(filename=dbLogFile,
				maxBytes=maxLogFileSize, encoding=enc)
		dbFileLogHandler.setLevel(dbLogFileLevel)
		dbFileFormatter = logging.Formatter(dbFileFormat)
		dbFileFormatter.datefmt = dbLogDateFormat
		dbFileLogHandler.setFormatter(dbFileFormatter)
		dbActivityLog.addHandler(dbFileLogHandler)


def setMainLogFile(fname, level=None):
	"""Create the main file-based logger for the framework, and optionally
	set the log level. If the passed 'fname' is None, any existing file-based
	logger will be closed.
	"""
	if fname is None:
		if dabo.fileLogHandler:
			# Remove the existing handler
			dabo.log.removeHandler(dabo.fileLogHandler)
			dabo.fileLogHandler.close()
			dabo.fileLogHandler = None
	else:
		if dabo.fileLogHandler:
			# Close the existing handler first
			dabo.log.removeHandler(dabo.fileLogHandler)
			dabo.fileLogHandler.close()
			dabo.fileLogHandler = None
		dabo.fileLogHandler = logging.handlers.RotatingFileHandler(filename=fname,
				maxBytes=dabo.maxLogFileSize, encoding=getEncoding())
		if level:
			dabo.fileLogHandler.setLevel(level)
		else:
			dabo.fileLogHandler.setLevel(dabo.mainLogFileLevel)
		dabo.fileFormatter = logging.Formatter(dabo.fileFormat)
		dabo.fileFormatter.datefmt = dabo.mainLogDateFormat
		dabo.fileLogHandler.setFormatter(dabo.fileFormatter)
		dabo.log.addHandler(dabo.fileLogHandler)


def setDbLogFile(fname, level=None):
	"""Create the dbActivity file-based logger for the framework, and optionally
	set the log level. If the passed 'fname' is None, any existing file-based
	logger will be closed.
	"""
	if fname is None:
		if dabo.dbFileLogHandler:
			# Remove the existing handler
			dabo.dbActivityLog.removeHandler(dabo.dbFileLogHandler)
			dabo.dbFileLogHandler.close()
			dabo.dbFileLogHandler = None
	else:
		if dabo.dbFileLogHandler:
			# Close the existing handler first
			dabo.dbActivityLog.removeHandler(dabo.dbFileLogHandler)
			dabo.dbFileLogHandler.close()
			dabo.dbFileLogHandler = None
		dabo.dbFileLogHandler = logging.handlers.RotatingFileHandler(filename=fname,
				maxBytes=dabo.maxLogFileSize, encoding=getEncoding())
		if level:
			dabo.dbFileLogHandler.setLevel(level)
		else:
			dabo.dbFileLogHandler.setLevel(dabo.mainLogFileLevel)
		dabo.dbFileFormatter = logging.Formatter(dabo.dbFileFormat)
		dabo.dbFileFormatter.datefmt = dabo.dbLogDateFormat
		dabo.dbFileLogHandler.setFormatter(dabo.dbFileFormatter)
		dabo.dbActivityLog.addHandler(dabo.dbFileLogHandler)

# Install localization service for dabo. dApp will install localization service
# for the user application separately.
import dLocalize
dLocalize.install("dabo")
# On some platforms getfilesystemencoding() and even getdefaultlocale()
# can return None, so we make sure we always set a reasonable encoding:
# NOTE: 'defaultEncoding' is imported from 'from settings import *' line above.
fileSystemEncoding = (sys.getfilesystemencoding()
    or locale.getdefaultlocale()[1] or defaultEncoding)


from __version__ import version
import dColors
import dEvents
from lib.utils import ustr

from dBug import logPoint
if importDebugger:
	try:
		import pudb as pdb
	except ImportError:
		import pdb
	trace = pdb.set_trace
else:
	def trace():
		raise NotImplementedError

from dApp import dApp
from dPref import dPref

def debugout(*args):
	txtargs = [ustr(arg) for arg in args]
	txt = " ".join(txtargs)
	log = logging.getLogger("Debug")
	log.debug(txt)
# Mangle the namespace so that developers can add lines like:
# 		debugo("Some Message")
# or
# 		debugout("Another Message", self.Caption)
# to their code for debugging.
# (I added 'debugo' as an homage to Whil Hentzen!)
import __builtin__
__builtin__.debugo = __builtin__.debugout = debugout

# Make sure dabo.db, dabo.biz, and dabo.ui are imported:
import dabo.db
import dabo.biz
import dabo.ui

# Store the base path to the framework
frameworkPath = os.path.dirname(__file__)


# Define the standard Dabo subdirectory stucture for apps.
def _getAppDirectoryNames():
	return ("biz", "cache", "db", "lib", "reports", "resources", "test", "ui")


# Method to create a standard Dabo directory structure layout
def makeDaboDirectories(homedir=None):
	"""If homedir is passed, the directories will be created off of that
	directory. Otherwise, it is assumed that they should be created
	in the current directory location.
	"""
	currLoc = os.getcwd()
	if homedir is not None:
		os.chdir(homedir)
	for d in _getAppDirectoryNames():
		if not os.path.exists(d):
			os.mkdir(d)
	os.chdir(currLoc)


def quickStart(homedir=None):
	"""This creates a bare-bones application in either the specified
	directory, or the current one if none is specified.
	"""
	currLoc = os.getcwd()
	if homedir is None:
		homedir = raw_input("Enter the name for your application: ")
	if not homedir:
		return

	if not os.path.exists(homedir):
		os.makedirs(homedir)
	os.chdir(homedir)
	makeDaboDirectories()
	open("main.py", "w").write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dabo
dabo.ui.loadUI("wx")

app = dabo.dApp()

# IMPORTANT! Change app.MainFormClass value to the name
# of the form class that you want to run when your
# application starts up.
app.MainFormClass = dabo.ui.dFormMain

app.start()
""")

	template = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
######
# In order for Dabo to 'see' classes in your %(dd)s directory, add an
# import statement here for each class. E.g., if you have a file named
# 'MyClasses.py' in this directory, and it defines two classes named 'FirstClass'
# and 'SecondClass', add these lines:
#
# from MyClasses import FirstClass
# from MyClasses import SecondClass
#
# Now you can refer to these classes as: self.Application.%(dd)s.FirstClass and
# self.Application.%(dd)s.SecondClass
######

"""
	for dd in dabo._getAppDirectoryNames():
		fname = "%s/__init__.py" % dd
		txt = template % locals()
		open(fname, "w").write(txt)
	os.chmod("main.py", 0744)
	os.chdir(currLoc)
	print "Application '%s' has been created for you" % homedir


# Automatically load a default UI if the environmental variable exists.
# If the DABO_DEFAULT_UI exists, that ui will be loaded into the dabo.ui
# global namespace. This is really only meant as a convenience for the
# dabo developers when rolling single-file distributions - we don't want
# everyone setting this environment variable. To specify the UI for your
# app, you should instead set the UI property of the dApp object.
# We can't do this from within the ui package because of the corss references.
try:
	__defaultUI = os.environ["DABO_DEFAULT_UI"]
except KeyError:
	__defaultUI = None
else:
	dabo.log.info("Automatically loading default ui '%s'..." % __defaultUI)
	dabo.ui.loadUI(__defaultUI)
