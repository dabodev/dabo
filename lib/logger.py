# -*- coding: utf-8 -*-
import sys, os, time
from dabo.dObject import dObject
from dabo.dLocalize import _

class Log(dObject):
	""" Generic logger object for Dabo.

	The main dabo module will instantiate singleton instances of this, which
	custom code can override to redirect the writing of informational and error
	messages.

	So, to display general informational messages, call:
		dabo.logInfo("message")

	For error messages, call:
		dabo.logError("message")

	By default,.logInfos to stdout and errorLog to stderr. But your code
	can redirect these messages however you please. Just set the LogObject property
	to an instance that has a write() method that will receive and act on the
	message. For example, you can redirect to a file:

		dabo.log.LogObject = open("/tmp/error.log", "w")
		dabo.log.LogObject = open("/dev/null", "w")

	You can set the logs to arbitrary objects. As long as the object has a write()
	method that receives a message parameter, it will work.
	"""
	def __init__(self, *args, **kwargs):
		self._logLevel = 7
		self._caption = None
		self._defaultType = 'Info'
		self._logToConsole = 7
		self._logTimeStamp = True
		self._logTypes = {'Database Activity':32, 'Debug':16, 'Info':8, 'Error':4, 'Exception':2, 'Critical':1}
		self._customTypes = {}
		self._nextLevel = 64

	def write(self, message, logType=self.DefaultType, toConsole=False):
		if self._logTypes.has_key(logType):
			logLevel = self._logTypes[logType]

		elif self._customTypes.has_key(logType):
			logLevel = self._customTypes[logType]

		else:
			self.LogObject = self.LogName
			logLevel = 1
			message = _('Invalid Log type specified!')

		if self.LogTimeStamp:
			timestamp = time.strftime('[%x %X] ', time.localtime(time.time()))
		else:
			timestamp = ""

		if self.Caption:
			caption = self.Caption + ': '
		else:
			caption = ''

		msg = caption + timestamp + '{' + logType + '} :: ' + message + os.linesep

		if logLevel & self.LogLevel:
			self.LogObject.write(msg)

		if toConsole or logLevel & self.LogToConsole or logType == 'Critical' and (self.LogObject != sys.stderr or self.LogObject != sys.stdout):
			sys.stderr.write(msg)

		# Flush the log entry to the file
		try:
			self.LogObject.flush()
		except (AttributeError, IOError):
			pass

	def addLogLevel(self, logLevel):
		if self._logTypes.has_key(logLevel):
			if not self._logLevel & self._logTypes[logLevel]:
				self._logLevel &= self._logTypes[logLevel]
			else:
				self.logInfo(_("Already Logging ") + logLevel)
		elif self._customTypes.has_key(logLevel):
			if not self.logLevel & self._customTypes[logLevel]:
				self.logLevel &= self._customTypes[logLevel]
			else:
				self.logInfo(_("Already Logging ") + logLevel)
		else:
			self.logError(_("Invalid Log Type"))

	def delLogLevel(self, logLevel):
		if logLevel == 'Critical':
			return

		if self._logTypes.has_key(logLevel):
			self._logLevel ~= self._logTypes[logLevel]
		elif self._customTypes.has_key(logLevel):
			self.logLevel ~= self._customTypes[logLevel]
		else:
			self.logError(_("Invalid Log Type"))

	def logDebug(self, message, toConsole=False):
		self.write(message, 'Debug', toConsole)

	def logInfo(self, message, toConsole=False):
		self.write(message, 'Info', toConsole)

	def logError(self, message, toConsole=False):
		self.write(message, 'Error', toConsole)

	def logException(self, message, toConsole=False):
		self.write(message, 'Exception', toConsole)

	def logCritical(self, message, toConsole=False):
		self.write(message, 'Critical', toConsole)

	def logDBActivity(self, message, toConsole=False):
		self.write(message, 'Database Activity', toConsole)

	def addCustomType(self, msgType):
		self._customTypes[msgType] = self._nextLevel
		self._nextLevel = self._nextLevel*2


	def _getCaption(self):
		try:
			return self._caption
		except AttributeError:
			return ""

	def _setCaption(self, val):
		self._caption = str(val)


	def _getDefaultType(self):
		try:
			return self._defaultType
		except AttributeError:
			return "Debug"

	def _setDefaultType(self, val):
		self._defaultType = str(val)


	def _getLogLevel(self):
		return self._logLevel

	def _setLogLevel(self, val):
		if val < 1:
			val = 1

		self._logLevel = val


	def _getLogObject(self):
		try:
			return self._logObject
		except AttributeError:
			return sys.stdout

	def _setLogObject(self, logObject):
		# assume that logObject is an object with a write() method...
		self._logObject = logObject


	def _getLogTimeStamp(self):
		try:
			return self._logTimeStamp
		except AttributeError:
			return True

	def _setLogTimeStamp(self, val):
		self._logTimeStamp = bool(val)


	def _getLogToConsole(self):
		return self._logToConsole

	def _setLogToConsole(self, val):
		if val < 1:
			val = 1

		self._logToConsole = val


	Caption = property(_getCaption, _setCaption, None,
		_("The log's label: will get prepended to the log entry"))

	DefaultType = property(_getDefaultType, _setDefaultType, None
		_("The log's default Type: used when you call write directly without specifying the type"))

	LogLevel = property(_getLogLevel, _setLogLevel, None,
		_("The log's level: Determins which messages are output to the log."))

	LogObject = property(_getLogObject, _setLogObject, None,
		_("The object that is to receive the log messages."))

	LogTimeStamp = property(_getLogTimeStamp, _setLogTimeStamp, None,
		_("Specifies whether a timestamp is logged with the message. Default: True"))

	LogToConsole = property(_getLogToConsole, _setLogToConsole, None,
		_("The log's console level: Determins which messages are output to the console."))

