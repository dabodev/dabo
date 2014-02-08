# -*- coding: utf-8 -*-
"""
3-Tier Desktop Database Business Application Framework

http://dabodev.com
"""
import sys
import os
import locale
import logging
import logging.handlers
from settings import *
from version import __version__

# dApp will change the following values upon its __init__:
dAppRef = None

def getEncoding():
	encoding = locale.getdefaultlocale()[1] or locale.getlocale()[1] or defaultEncoding

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
		fileLogHandler = logging.handlers.RotatingFileHandler(
				filename=mainLogFile,
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
		dbFileLogHandler = logging.handlers.RotatingFileHandler(
				filename=dbLogFile,
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
	import dabo
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
				maxBytes=maxLogFileSize, encoding=getEncoding())
		if level:
			dabo.fileLogHandler.setLevel(level)
		else:
			dabo.fileLogHandler.setLevel(mainLogFileLevel)
		dabo.fileFormatter = logging.Formatter(fileFormat)
		dabo.fileFormatter.datefmt = mainLogDateFormat
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
				maxBytes=maxLogFileSize, encoding=getEncoding())
		if level:
			dabo.dbFileLogHandler.setLevel(level)
		else:
			dabo.dbFileLogHandler.setLevel(mainLogFileLevel)
		dabo.dbFileFormatter = logging.Formatter(dbFileFormat)
		dabo.dbFileFormatter.datefmt = dbLogDateFormat
		dabo.dbFileLogHandler.setFormatter(dabo.dbFileFormatter)
		dabo.dbActivityLog.addHandler(dabo.dbFileLogHandler)

if localizeDabo:
	# Install localization service for dabo. dApp will install localization service
	# for the user application separately.
	import dLocalize
	dLocalize.install("dabo")

# On some platforms getfilesystemencoding() and even getdefaultlocale()
# can return None, so we make sure we always set a reasonable encoding:
fileSystemEncoding = (sys.getfilesystemencoding()
		or locale.getdefaultlocale()[1] or defaultEncoding)

if importDebugger:
	from dBug import logPoint
	try:
		import pudb as pdb
	except ImportError:
		import pdb
	trace = pdb.set_trace

	def debugout(*args):
		from lib.utils import ustr
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

if implicitImports:
	import dColors
	import dEvents
	import dabo.db
	import dabo.biz
	import dabo.ui
	from dApp import dApp
	from dPref import dPref

# Store the base path to the framework
frameworkPath = os.path.dirname(__file__)

# Subdirectories that make up a standard Dabo app
_standardDirs = ("biz", "cache", "db", "lib", "reports", "resources", "test", "ui")

# Method to create a standard Dabo directory structure layout
def makeDaboDirectories(homedir=None):
	"""If homedir is passed, the directories will be created off of that
	directory. Otherwise, it is assumed that they should be created
	in the current directory location.
	"""
	currLoc = os.getcwd()
	if homedir is not None:
		os.chdir(homedir)
	for d in _standardDirs:
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
import dabo.ui
dabo.ui.loadUI("wx")
from dabo.dApp import dApp

app = dApp()

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
	for dd in _standardDirs:
		fname = "%s/__init__.py" % dd
		txt = template % locals()
		open(fname, "w").write(txt)
	os.chmod("main.py", 0744)
	os.chdir(currLoc)
	print "Application '%s' has been created for you" % homedir

